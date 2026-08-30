#!/usr/bin/env python3
"""Structure-rotation check (近文轮换检测).

Scans output/*/index.md bodies (frontmatter has only title/cover, so the
structure signature is extracted heuristically from the body):
  - structure signature  -> mapped to a skeleton id (structure-rotation.md)
  - opening sentence     -> first real body paragraph's first sentence
  - closing sentence     -> last real sentence, source-attribution stripped

Flags conflicts when the current/latest article repeats an opening/closing
sentence against a recent one (>80% similarity), reuses a banned signature
phrase, or stacks the same skeleton id too many times in a row.

Uses only the Python stdlib (difflib). Deterministic, heuristic, and meant to
prompt a human decision — near matches print, they don't block.

Usage:
  python rotation_check.py                      # scan all articles, new->old
  python rotation_check.py --near 6             # compare against last N (default 6)
  python rotation_check.py --target output/fde-intro/index.md   # one vs others
  python rotation_check.py --json               # machine-readable output
"""
import difflib
import glob
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_GLOB = os.path.join(ROOT, 'output', '*', 'index.md')

# Banned "signature phrase" templates (structure-rotation.md section 3).
# Regex on purpose: a bare substring like `这就是` fires on nearly every
# article (noise), so only meaningful 升华/口头禅 forms are targeted.
BANNED_PATTERNS = [
    r'你可能(见过(这个场景|这个场面|这种)|觉得|遇到过这种)',   # 开头口头禅
    r'先看(一个)?问题', r'你有没有想过', r'当下(的)?AI[圈界]最热',   # 开头钩子套话
    r'一句话总结', r'总的来说', r'归根结底', r'综上,?\s*$',        # 结尾自述预告
    r'这就是.{0,8}(意义|价值|全部|未来|一切|开始)',                # 结尾升华
    r'未来已来', r'我们有理由相信', r'这次事件告诉我们', r'它启示我们',  # 结尾升华
    r'值得注意的是', r'尴尬的是', r'更有意思的是', r'说到底',       # 过渡评论腔
    r'在当今这个.{0,6}时代',                                       # G5 泛化时代定语
]


def find_banned(body: str):
    """Return the banned patterns matched in a body. Only regex, stdlib only."""
    return [p for p in BANNED_PATTERNS if re.search(p, body)]

SOURCE_LINE_RE = re.compile(r'^[> ]*\*.*(本文|来源|改写自|内容.*来源|参考).*[*：:]?.*$')
HEADING_RE = re.compile(r'^\*\*\s*(.+?)\s*\*\*$')


def _strip_frontmatter(content: str) -> str:
    """Return body text with the leading YAML frontmatter removed."""
    lines = content.split('\n')
    if lines and lines[0].strip() == '---':
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                return '\n'.join(lines[i + 1:])
    return content


def _sentences(text: str):
    """Split CJK text into sentences on 。/！/？/； (keep plain)."""
    return [s for s in re.split(r'[。！？；]', text) if s.strip()]


def _first_real_para(paras):
    """First paragraph that has real prose (not heading, not cite link)."""
    for p in paras:
        s = p.strip()
        if not s:
            continue
        if s.startswith('#') or s.startswith('![') or s.startswith('<'):
            continue
        # drop blockquote lead marker `> `
        s = re.sub(r'^>\s*', '', s)
        if not s:
            continue
        for sent in _sentences(s):
            return sent.strip()
    return ''


def _last_real_para(paras):
    """Last paragraph with a real closing judgement, source attribution stripped."""
    cands = [p.strip() for p in paras if p.strip() and not p.strip().startswith('#')]
    # source attribution usually in the final 1-2 lines; walk back to skip them
    for p in reversed(cands):
        if SOURCE_LINE_RE.match(p):
            continue
        s = re.sub(r'^>\s*', '', p)
        sents = _sentences(s)
        # prefer the sentence that carries a judgement, not a URL
        if sents and not re.search(r'https?://', sents[-1]):
            return sents[-1].strip()
    return ''


def skeleton_id(heading: str, h2s, body: str, opening: str) -> str:
    """Heuristic skeleton-id mapping (structure-rotation.md section 2).

    Rules are ordered by how discriminating each signal is. This is heuristic,
    aimed at flagging "same-skeleton stacking", not perfect classification.
    """
    full = '\n'.join(h2s) + '\n' + heading
    n = len(h2s)

    if '番外篇' in heading or '谈谈专业概念' in heading or '谈谈' in heading:
        # mode-A series heading
        if any(k in full for k in ('岗位画像', '制度', '门槛', '几个面孔', '时代', '团队', '职业', '角色')):
            return 'A2'
        if any(k in full for k in ('病象', '方法论', '工作流', '方法全貌', '落地', '注意事项', '弹性')):
            return 'A3'
        return 'A1'

    # mode-D: cognitive reconstruction — opposite start + numbered sections + closing takeaway
    if '我以为' in body and '直到' in body and '认知' in full or ('带走的认知' in full):
        return 'D'
    if re.search(r'我以为.*?，?直到', body[:200]):
        return 'D'

    # mode-C-tutorial: `## N. 步骤标题` style
    if any(re.match(r'^\d+[\.、]', h2.lstrip('#')) for h2 in h2s):
        return 'C-tut'
    if any('步骤' in h for h in h2s):
        return 'C-tut'

    if n == 4:
        return 'B'
    if n >= 7:
        return 'C-di'
    return 'C-essay'


def parse_article(path: str) -> dict:
    content = open(path, encoding='utf-8').read()
    body = _strip_frontmatter(content)
    lines = body.split('\n')
    paras = lines  # treat lines as paragraphs; indentation-based paragraphs are single-newline

    h2s = [re.sub(r'^##\s*', '', l) for l in lines if l.strip().startswith('## ')]
    heading = re.sub(r'^#\s*', '', next((l for l in lines if l.strip().startswith('# ')), ''))

    non_empty = [l for l in lines if l.strip()]
    opening = _first_real_para(non_empty)
    closing = _last_real_para(non_empty)

    sk = skeleton_id(heading, h2s, body, opening)
    banned = find_banned(body)

    return {
        'path': os.path.relpath(path, ROOT),
        'heading': heading,
        'h2s': h2s,
        'skeleton': sk,
        'opening': opening,
        'closing': closing,
        'banned': banned,
    }


def folder(relpath: str) -> str:
    """Return the article directory name from a ROOT-relative path, OS-agnostic."""
    return relpath.replace('\\', '/').split('/')[-2]


def sim(a: str, b: str) -> float:
    if len(a) < 5 or len(b) < 5:
        return 0.0
    # ignore pure-punctuation ties
    if not re.search(r'[一-鿿]', a) or not re.search(r'[一-鿿]', b):
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def main():
    import argparse
    ap = argparse.ArgumentParser(description='Structure-rotation check (near-article repetition).')
    ap.add_argument('--near', type=int, default=6, help='compare vs last N articles')
    ap.add_argument('--target', help='compare this one article against the others')
    ap.add_argument('--json', action='store_true', help='machine-readable output')
    ap.add_argument('--threshold', type=float, default=0.8, help='similarity threshold')
    args = ap.parse_args()

    files = sorted(glob.glob(OUTPUT_GLOB), key=os.path.getmtime, reverse=True)
    arts = [parse_article(f) for f in files]

    conflicts = []
    for idx, cur in enumerate(arts):
        # only compare against older (published-earlier => listed later in reversed order)
        window = arts[max(0, idx + (1 if args.target else 0)): idx + 1 + args.near]
        # when --target, compare that one file against ALL others
        if args.target:
            target_abs = os.path.normpath(os.path.join(ROOT, args.target))
            if os.path.abspath(files[idx]) != os.path.abspath(target_abs):
                continue
            window = arts[:idx] + arts[idx + 1:]
        for prev in window:
            if prev is cur:
                continue
            if sim(cur['opening'], prev['opening']) >= args.threshold and cur['opening'] and prev['opening']:
                conflicts.append({
                    'kind': 'opening', 'cur': cur['path'], 'prev': prev['path'],
                    'snippet': cur['opening'][:28], 'score': round(sim(cur['opening'], prev['opening']), 2),
                })
            if sim(cur['closing'], prev['closing']) >= args.threshold and cur['closing'] and prev['closing']:
                conflicts.append({
                    'kind': 'closing', 'cur': cur['path'], 'prev': prev['path'],
                    'snippet': cur['closing'][:28], 'score': round(sim(cur['closing'], prev['closing']), 2),
                })

    # same-skeleton stacking: count runs of identical skeleton id on the sorted-recency list
    stack_warn = []
    run = 1
    for i in range(1, len(arts)):
        if arts[i]['skeleton'] == arts[i - 1]['skeleton']:
            run += 1
            if run == 4:
                stack_warn.append(arts[i]['skeleton'])
        else:
            run = 1
    if stack_warn:
        conflicts.append({'kind': 'skeleton-stack', 'cur': ', '.join(stack_warn),
                          'prev': '最近文章', 'snippet': '骨架 %s 连续 ≥3 篇' % stack_warn[0], 'score': 1})

    # banned signature phrases present anywhere in a published article
    banned_hits = []
    for cur in arts:
        if cur['banned']:
            banned_hits.append({'path': cur['path'], 'phrases': cur['banned']})
    if banned_hits:
        conflicts.append({'kind': 'banned-phrase',
                          'cur': '；'.join(folder(b['path']) + ':' + ','.join(b['phrases']) for b in banned_hits),
                          'prev': '正文', 'snippet': '检测到套话模板', 'score': 1})

    if args.json:
        print(json.dumps({'articles': [{'path': a['path'], 'skeleton': a['skeleton'],
                                        'opening': a['opening'][:20], 'closing': a['closing'][:20]}
                                       for a in arts],
                          'conflicts': conflicts}, ensure_ascii=False, indent=2))
    else:
        print('== 检测 %d 篇近文（按发布时间新→旧） ==' % len(arts))
        print('%-24s %-6s %s' % ('文章', '骨架', '开头句(前20字)'))
        for a in arts:
            print('%-24s %-6s %s' % (folder(a['path']), a['skeleton'], a['opening'][:20]))
        print()
        if not conflicts:
            print('✅ 无近文结构/开头/结尾重复，无套话模板残留。')
        else:
            print('⚠️ 发现 %d 项冲突，需人工复核：' % len(conflicts))
            for c in conflicts:
                print('  [%s] %s <- %s  (sim %.2f)  %s'
                      % (c['kind'], c['cur'], c['prev'], c.get('score', 0), c.get('snippet', '')))
        return 0 if not conflicts else 1


if __name__ == '__main__':
    sys.exit(main())
