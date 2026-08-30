#!/usr/bin/env python3
"""Mechanical lint for AI translation from English to Chinese.

SSOT (Single Source of Truth):
  - Rule definitions: references/translation-principles.md (principles A-E)
  - Terminology: references/glossary-ai.md (§11 for typography)
  - Collocation traps: COLLOCATION_TRAPS list below (keep synced with principles §10)
  - This file: mechanical enforcement only. Does NOT define rules.

Usage:
    python translation_lint.py <original_en.md> <translated_zh.md>

Outputs a structured report to stdout. Exit code 0 means no errors found,
exit code 1 means errors or warnings were found.

Checks are purely regex/mechanical — they complement, not replace,
human final-read review for tone, fidelity, and naturalness.
"""

import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Finding:
    severity: str  # "error" | "warning" | "info"
    line: int
    category: str
    detail: str


@dataclass
class LintReport:
    en_path: str
    zh_path: str
    findings: list[Finding] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    @property
    def errors(self) -> int:
        return sum(1 for f in self.findings if f.severity == "error")

    @property
    def warnings(self) -> int:
        return sum(1 for f in self.findings if f.severity == "warning")

    def add(self, severity: str, line: int, category: str, detail: str) -> None:
        self.findings.append(Finding(severity, line, category, detail))


# ── Helpers ──────────────────────────────────────────────────────────────────

def _strip_markdown_code_blocks(text: str) -> list[tuple[int, str, bool]]:
    """Split text into (line_number, content, is_inside_code_block)."""
    lines = text.split("\n")
    result: list[tuple[int, str, bool]] = []
    in_block = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_block = not in_block
            result.append((i, line, True))
            continue
        result.append((i, line, in_block))
    return result


def _zh_lines_outside_blocks(text: str) -> list[tuple[int, str]]:
    """Return (line_number, content) for lines that are NOT inside code blocks."""
    parsed = _strip_markdown_code_blocks(text)
    return [(ln, content) for ln, content, in_block in parsed if not in_block]


def _extract_numbers(text: str) -> list[str]:
    """Extract numeric tokens: integers, floats, percentages, ranges."""
    return re.findall(r"\b\d[\d,.]*(?:\s*%|\s*[-–]\s*\d[\d,.]*\s*%)?", text)


# ── Check functions ──────────────────────────────────────────────────────────

def check_number_parity(report: LintReport, en_text: str, zh_text: str) -> None:
    """Check that numeric token counts are similar between EN and ZH."""
    en_nums = _extract_numbers(en_text)
    zh_nums = _extract_numbers(zh_text)
    report.stats["en_number_count"] = len(en_nums)
    report.stats["zh_number_count"] = len(zh_nums)

    # Allow ±5% tolerance for numbers converted to Chinese text (e.g. "hundreds")
    diff = abs(len(en_nums) - len(zh_nums))
    if diff > max(2, len(en_nums) * 0.05):
        # Try to find specific missing numbers by comparing sets
        en_set = set(en_nums)
        zh_set = set(zh_nums)
        missing = en_set - zh_set
        report.add(
            "error", 0,
            "数字完整性",
            f"原文 {len(en_nums)} 个数字，译文 {len(zh_nums)} 个数字，差值 {diff}。"
            f"疑似缺失: {sorted(missing)[:8]}" if missing else ""
        )


def check_backtick_pairs(report: LintReport, zh_text: str) -> None:
    """Check for unmatched single or triple backtick groups."""
    lines = zh_text.split("\n")
    single_count = 0
    in_fence = False
    for i, line in enumerate(lines, 1):
        # Track ``` fences
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # Count backticks outside code blocks
        singles = line.count("`") - line.count("``") * 2
        single_count += singles
    if single_count % 2 != 0:
        report.add("error", 0, "反引号成对", "反引号(`) 不成对，总数 " + str(single_count) + "（应为偶数）")


def check_forbidden_phrases(report: LintReport, zh_text: str) -> None:
    """Detect high-frequency translation-tone phrases."""
    patterns: list[tuple[str, str]] = [
        ("这就是为什么", "高频翻译腔——This is why 的语法直译"),
        ("这一事实", "高频翻译腔——the fact that 的语法直译"),
        ("事实证明", "高频翻译腔——It turns out that 的语气过重直译"),
        ("关键的洞察", "高频翻译腔——key insight 的直译"),
        ("不仅是关于", "高频翻译腔——not just about X 的 about 直译"),
        ("之间的桥", "高频翻译腔——X is the bridge between A and B 的结构隐喻直译"),
        ("之间的纽带", "高频翻译腔——X is the link between A and B 的结构隐喻直译"),
        ("之间的铰链", "高频翻译腔——X is the hinge between A and B 的结构隐喻直译"),
        ("发货", "软件语境禁用词——应译为'推送/发布'"),
    ]
    lines = zh_text.split("\n")
    for i, line in enumerate(lines, 1):
        for phrase, explanation in patterns:
            if phrase in line:
                report.add(
                    "error" if phrase in ("发货",) else "warning",
                    i,
                    "翻译腔/禁用词",
                    f"'{phrase}' — {explanation}",
                )


def check_pronoun_abuse(report: LintReport, zh_text: str) -> None:
    """Detect consecutive 其/该/此 abuse in sentences."""
    zh_lines = _zh_lines_outside_blocks(zh_text)
    # Split each line into sentences (roughly, by Chinese punctuation)
    sentence_end = re.compile(r"[。！？；]")
    for ln, line in zh_lines:
        sentences = sentence_end.split(line)
        for sent in sentences:
            count = len(re.findall(r"[其该此]", sent))
            if count >= 2:
                report.add(
                    "warning", ln,
                    "书面代词滥用",
                    "单句内'其/该/此'出现 " + str(count) + " 次 — 需改写",
                )


def check_de_chain(report: LintReport, zh_text: str) -> None:
    """Detect 的 appearing 3+ times in a single sentence.

    Rule from polish-prompt.md: 单句内'的'≥3 次必须拆分。
    Uses count threshold (not density) to match the spec.
    """
    zh_lines = _zh_lines_outside_blocks(zh_text)
    sentence_end = re.compile(r"[。！？；\n]")
    for ln, line in zh_lines:
        sentences = sentence_end.split(line)
        for sent in sentences:
            de_count = len(re.findall(r"的", sent))
            if de_count >= 3:
                report.add(
                    "warning", ln,
                    "的-chain",
                    "单句内'的'出现 " + str(de_count) + " 次（≥3）— 需拆分长定语",
                )


def check_bei_de_chain(report: LintReport, zh_text: str) -> None:
    """Detect '被...的' modifier chains — a high-signal translation-ese pattern.

    Pattern: 被 + [adverb] + [adjective] + 的 + [noun]
    Example: 被严重低估的最大价值 → should be split into two clauses.
    This pattern often flies under the 的≥3 radar when only one 的 is present.
    """
    zh_lines = _zh_lines_outside_blocks(zh_text)
    # Match: 被 + (any non-的 chars) + 的 — within a sentence context
    pattern = re.compile(r"被[^。！？；\n]{1,30}的")
    for ln, line in zh_lines:
        for match in pattern.finditer(line):
            report.add(
                "warning", ln,
                "被...的修饰链",
                f"'被...的' 嵌套修饰 — 考虑拆分为独立短句: '...{match.group()[:40]}...'",
            )


def check_passive_redundancy(report: LintReport, zh_text: str) -> None:
    """Detect redundant passive/formal words."""
    redundant = ["被", "进行", "作出", "加以"]
    zh_lines = _zh_lines_outside_blocks(zh_text)
    for ln, line in zh_lines:
        for word in redundant:
            if word in line:
                # "被" is allowed in certain contexts but flag if appears frequently
                count = line.count(word)
                if word == "被" and count >= 2:
                    report.add(
                        "info", ln,
                        "冗余被动",
                        f"'{word}' 出现 {count} 次 — 考虑转主动语态",
                    )
                    break
                elif word != "被" and count >= 1:
                    report.add(
                        "info", ln,
                        "冗余书面词",
                        f"'{word}' — 可用更直接的动词替代",
                    )


def check_pangu_spacing(report: LintReport, zh_text: str) -> None:
    """Check Chinese+English/digit spacing (pangu rule).

    Rule: Chinese char adjacent to ASCII letter/digit MUST have
    a half-width space between them. Exception: Chinese full-width
    punctuation (，。！？；：）】》） already handles spacing.
    """
    zh_lines = _zh_lines_outside_blocks(zh_text)
    # Chinese char followed by ASCII letter/digit without space
    cn_then_en = re.compile(r"[一-鿿㐀-䶿](?=[A-Za-z0-9])")
    en_then_cn = re.compile(r"(?<=[A-Za-z0-9])[一-鿿㐀-䶿]")

    for ln, line in zh_lines:
        # Skip lines that are purely markdown syntax
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(">"):
            continue
        if stripped.startswith("|") or stripped.startswith("-"):
            continue

        for match in cn_then_en.finditer(line):
            report.add("warning", ln, "盘古之白", f"中→英缺空格: '...{line[max(0,match.start()-4):match.end()+4]}...'")
        for match in en_then_cn.finditer(line):
            report.add("warning", ln, "盘古之白", f"英→中缺空格: '...{line[max(0,match.start()-4):match.end()+4]}...'")


def check_codeblock_lang_labels(report: LintReport, zh_text: str) -> None:
    """Flag ``` fences opening code blocks without language labels."""
    lines = zh_text.split("\n")
    in_block = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_block:
                in_block = False  # closing fence — no label needed
            else:
                in_block = True  # opening fence
                if stripped == "```":
                    report.add(
                        "warning", i,
                        "代码块语言标签",
                        "代码块起始 ``` 缺少语言标签（如 ```text / ```json / ```bash）",
                    )


# ── Known collocation violations (principle B mechanical intercept) ────────────

# Verb → abstract object pairs that are known to violate Chinese collocation.
# Format: (verb_substring, abstract_object_substring, suggestion)
# These only cover KNOWN cases — they don't exhaust the space of possible violations.
# They serve as a mechanical backstop for patterns discovered in prior translations.
KNOWN_COLLOCATION_VIOLATIONS: list[tuple[str, str, str]] = [
    ("穿过", "研究", "贯穿 / 梳理"),
    ("穿过", "实验", "贯穿 / 梳理"),
    ("穿过", "论文", "贯穿 / 梳理"),
    ("穿过", "论证", "贯穿 / 梳理"),
    ("穿过", "文章", "贯穿 / 梳理"),
    ("花掉", "注意力", "耗费 / 投入"),
    ("花掉", "精力", "耗费 / 投入"),
    ("花掉", "心力", "耗费 / 投入"),
    ("花", "注意力", "耗费 / 投入"),
    ("卸载", "任务", "交由 / 外包"),
    ("卸载", "认知", "交由 / 外包"),
    ("卸载", "工作", "交由 / 外包"),
    ("部分卸载", "", "交由…处理 / 外包给"),
    ("等量的", "理解", "相应的 / 对等的"),
    ("等量的", "收获", "相应的 / 对等的"),
    ("等量的", "价值", "相应的 / 对等的"),
    ("走进", "对话", "面对 / 陷入"),
    ("走进", "处境", "陷入 / 面对"),
    ("走进", "陷阱", "陷入（陷阱可以'踏进'，对话不能'走进'）"),
    ("踏进", "对话", "面对"),
    ("桥", "之间", "串起 / 贯穿（'X是A和B之间的桥'改为'X把A和B串了起来'）"),
    ("铰链", "之间", "串起 / 贯穿"),
    ("纽带", "之间", "连接 / 串联"),
    ("的花", "注意力", "耗费 / 投入"),
    ("部分删除", "", "动词本身含粒度？二值动词'删除'天然排斥'部分'修饰"),
    ("部分关闭", "", "动词本身含粒度？二值动词'关闭'天然排斥'部分'修饰"),
    ("引擎盖", "", "底层机制（under the hood）"),
    ("发货", "", "推送/发布（软件语境）"),
    ("头条功能", "", "主打功能/核心功能（'头条'限于新闻域，不能修饰技术'功能'）"),
    ("动了", "数据", "也有变化/有提升（'动了'太口语，不适合书面主语'数据'）"),
    ("动了", "评测", "也有变化/有提升（同上）"),
]


def check_known_collocations(report: LintReport, zh_text: str) -> None:
    """Flag known verb-noun collocation violations in Chinese text.

    This is a mechanical backstop for principle B. It only catches patterns
    we've already discovered and encoded. New violations still need human
    review (the native-speaker read-aloud step).
    """
    zh_lines = _zh_lines_outside_blocks(zh_text)
    for ln, line in zh_lines:
        for verb_pat, obj_pat, suggestion in KNOWN_COLLOCATION_VIOLATIONS:
            if obj_pat:
                # Check if both verb and object appear in proximity (within 10 chars)
                if verb_pat in line and obj_pat in line:
                    # Check they're reasonably close (not in completely separate clauses)
                    v_pos = line.find(verb_pat)
                    o_pos = line.find(obj_pat)
                    if abs(v_pos - o_pos) <= 15:
                        report.add(
                            "warning", ln,
                            "搭配越界",
                            f"'{verb_pat}+{obj_pat}' — 建议: {suggestion}",
                        )
            else:
                # obj_pat is empty — match verb alone (e.g., "部分卸载" anywhere)
                if verb_pat in line:
                    report.add(
                        "warning", ln,
                        "搭配越界",
                        f"'{verb_pat}' — 建议: {suggestion}",
                    )


def check_ascii_quotes(report: LintReport, zh_text: str) -> None:
    """Flag half-width ASCII double quotes in Chinese text outside code blocks.

    Chinese typography requires full-width quotes "" (U+201C/U+201D).
    Half-width ASCII quotes " (U+0022) should only appear inside code blocks,
    in purely English lines (e.g., source citations), or in headings.
    English quotes embedded in Chinese sentences also need full-width wrapping.
    """
    zh_lines = _zh_lines_outside_blocks(zh_text)
    for ln, line in zh_lines:
        stripped = line.strip()
        if stripped.startswith("*") and "http" in stripped:
            continue  # Source citation line
        if stripped.startswith("---"):
            continue  # YAML delimiter
        if stripped.startswith("#"):
            continue  # Heading line
        chinese_chars = len(re.findall(r'[一-鿿]', line))
        if chinese_chars < 3:
            continue  # Mostly English line, skip
        # Check for ASCII double quotes — flag all in Chinese-dominant lines
        if '"' in line:
            idx = line.index('"')
            context = line[max(0, idx-10):idx+10].strip()
            report.add(
                "error", ln,
                "半角引号",
                f"正文残留半角双引号 -> 应替换为全角引号。上下文: ...{context}...",
            )


def check_quote_pairing(report: LintReport, zh_text: str) -> None:
    """Flag mismatched full-width quote pairs (e.g., RIGHT used as LEFT).

    Valid pairs: "..." (U+201C ... U+201D).
    Invalid: "..." (U+201D ... U+201D) or "..." (U+201C ... U+201C).
    """
    # Extract all full-width quotes with positions
    quotes = []
    for i, ch in enumerate(zh_text):
        if ch in '“”':
            quotes.append((i, ch))

    # Check pairs: should alternate LEFT, RIGHT, LEFT, RIGHT...
    # But allow consecutive RIGHT+LEFT at pair boundaries (e.g., "A""B")
    for j in range(0, len(quotes) - 1):
        pos, ch = quotes[j]
        next_pos, next_ch = quotes[j + 1]

        # Determine line number
        line_num = zh_text[:pos].count('\n') + 1

        if ch == '”' and next_ch == '”':
            # Two consecutive RIGHT quotes — first one is wrong
            context = zh_text[max(0, pos-10):pos+10].replace('\n', ' ')
            report.add(
                "error", line_num,
                "引号配对",
                f"右引号 U+201D 被用作左引号。上下文: ...{context}...",
            )
        elif ch == '“' and next_ch == '“':
            # Two consecutive LEFT quotes — second one is wrong
            context = zh_text[max(0, next_pos-10):next_pos+10].replace('\n', ' ')
            report.add(
                "error", line_num,
                "引号配对",
                f"左引号 U+201C 被用作右引号。上下文: ...{context}...",
            )


def check_delivery_alignment(report: LintReport, en_text: str, zh_text: str) -> None:
    """Check that code blocks, images, headings counts match between EN and ZH.

    Smart detection: if the source file is plain text (no markdown fences/heading
    markers), skip structural comparisons that would produce false positives.
    """
    def count_pattern(text, pattern, flags=0):
        return len(re.findall(pattern, text, flags))

    # Count code block fences (``` lines)
    en_cb = count_pattern(en_text, r'^```', re.MULTILINE)
    zh_cb = count_pattern(zh_text, r'^```', re.MULTILINE)

    # Only flag code block mismatch if BOTH files have fences.
    # If source has 0 fences (plain text extraction), translation adding fences is correct.
    if en_cb > 0 and zh_cb > 0 and en_cb != zh_cb:
        report.add(
            "error", 0,
            "交付物对齐",
            f"代码块数量不一致: 原文 {en_cb // 2} 个, 译文 {zh_cb // 2} 个",
        )
    elif en_cb > 0 and zh_cb == 0:
        report.add(
            "error", 0,
            "交付物对齐",
            f"原文有 {en_cb // 2} 个代码块但译文无代码块",
        )

    # Count image references
    en_img = count_pattern(en_text, r'!\[.*?\]\(.*?\)')
    zh_img = count_pattern(zh_text, r'!\[.*?\]\(.*?\)')
    # Also count bare image URLs in source (e.g., pbs.twimg.com/media/...)
    en_bare_img = len(re.findall(r'https?://\S+\.(?:jpg|jpeg|png|gif|webp)(?:\?\S*)?', en_text, re.IGNORECASE))
    en_img_total = max(en_img, en_bare_img)  # Use whichever is larger
    if en_img_total != zh_img and en_img_total > 0 and zh_img > 0:
        report.add(
            "warning", 0,
            "交付物对齐",
            f"图片引用数量不一致: 原文 {en_img_total} 张(含裸URL), 译文 {zh_img} 张(![]()格式)",
        )
    elif en_img_total > 0 and zh_img == 0:
        report.add(
            "error", 0,
            "交付物对齐",
            f"原文有 {en_img_total} 张图片但译文无图片引用",
        )

    # Count section headings (##)
    en_h2 = count_pattern(en_text, r'^## ', re.MULTILINE)
    zh_h2 = count_pattern(zh_text, r'^## ', re.MULTILINE)

    # Only flag heading mismatch if BOTH files have ## headings.
    # If source is plain text (0 headings), translation adding structure is correct.
    if en_h2 > 0 and zh_h2 > 0 and abs(en_h2 - zh_h2) > 1:
        report.add(
            "warning", 0,
            "交付物对齐",
            f"章节标题数量差异较大: 原文 {en_h2} 个, 译文 {zh_h2} 个",
        )
    elif en_h2 > 0 and zh_h2 == 0:
        report.add(
            "warning", 0,
            "交付物对齐",
            f"原文有 {en_h2} 个章节标题但译文无标题结构",
        )

    # Store counts in stats for display
    report.stats["en_codeblocks"] = en_cb // 2
    report.stats["zh_codeblocks"] = zh_cb // 2
    report.stats["en_images"] = en_img
    report.stats["zh_images"] = zh_img
    report.stats["en_headings"] = en_h2
    report.stats["zh_headings"] = zh_h2


def check_cli_inline_code(report: LintReport, zh_text: str) -> None:
    """Flag CLI/slash commands not wrapped in inline code backticks.

    Commands like /goal, /loop should appear as `/goal`, `/loop` in body text.
    Only checks lines outside code blocks.
    """
    # Common CLI/slash commands to check
    cli_patterns = [
        (r'(?<!`)/goal(?![`\w])', '/goal', '`/goal`'),
        (r'(?<!`)/loop(?![`\w])', '/loop', '`/loop`'),
    ]
    zh_lines = _zh_lines_outside_blocks(zh_text)
    for ln, line in zh_lines:
        # Skip headings (they're handled separately and often have different formatting)
        if line.strip().startswith("#"):
            continue
        for pattern, cmd, suggestion in cli_patterns:
            if re.search(pattern, line):
                report.add(
                    "info", ln,
                    "行内代码格式",
                    f"命令 {cmd} 未用行内代码包裹，建议改为 {suggestion}",
                )


# ── Register drift detection (principle D mechanical intercept) ─────────────

# Colloquial/slang words that are too informal for Mode C (L2 register).
# These are fine in casual chat but cross the line in "科技记者整理稿" tone.
# Format: (word, suggested_formal_alternative)
REGISTER_DRIFT_WORDS: list[tuple[str, str]] = [
    ("坑你", "误导你"),
    ("坑了", "误导了"),
    ("烧钱", "消耗更多 Token / 成本更高"),
    ("活儿", "任务"),
    ("大活儿", "复杂任务"),
    ("小活", "简单任务"),
    ("挂了", "失败了"),
    ("保姆", "手动兜底"),
    ("当保姆", "手动兜底"),
    ("敲 Prompt", "输入 Prompt"),
    ("敲代码", "编写代码"),
    ("打一段", "输入一段"),
    ("零碎", "步骤细碎"),
    ("跑一次就完", "一次执行即可完成"),
    ("信得过", "确认可靠"),
    ("搞定", "完成"),
    ("整一个", "创建一个"),
    ("整件事", "整个流程"),
    ("牛逼", "出色"),
    ("牛逼", "强大"),
    ("拉胯", "表现不佳"),
    ("翻车", "出错"),
    ("踩坑", "遇到问题"),
    ("擦屁股", "收拾残局"),
    ("硬杠杠", "硬性指标"),
]

# Collocation traps: literal translations where verb+object don't form
# natural Chinese pairs. These are specific to tech translation.
#
# SSOT: The principle behind these traps is defined in
#   references/translation-principles.md → 原则 E (隐喻对等映射)
#   references/ai-translation-guide.md → 基座禁忌 #10 例外 → 常见搭配陷阱
# This list is the mechanical enforcement layer. When adding new traps here,
# also update the principles file and ai-translation-guide.md.
#
# Format: (bad_phrase, good_alternative, trap_type)
COLLOCATION_TRAPS: list[tuple[str, str, str]] = [
    ("免费层", "免费版 / 免费计划", "tier 不译'层'"),
    ("把生活粘贴进", "反复向 AI 复述", "paste+life 不可迁移"),
    ("不会被锁定", "不被平台绑死 / 不受供应商锁定", "locked in 隐喻不对等"),
    ("被锁定在", "被绑定在 / 受制于", "locked in 隐喻不对等"),
    ("Obsidian 方言", "Obsidian 语法 / Obsidian 的写法", "dialect 语义偏移"),
    ("粘贴你的", "复述你的 / 录入你的", "paste 不可迁移到抽象宾语"),
    ("断裂的链接", "死链 / 失效链接", "broken links 非标准术语"),
    # "打磨" + abstract noun collocation traps
    ("打磨.*可扩展性", "打磨架构、提升可扩展性", "打磨不能搭配可扩展性"),
    ("打磨.*创造力", "打磨架构、注入创造力", "打磨不能搭配创造力"),
    # "是关于" machine translation patterns (complement check_is_about_pattern)
    ("是关于", "核心在于 / 本质上是 / 关键是", "'is about' 直译机翻味"),
]


def check_register_drift(report: LintReport, zh_text: str) -> None:
    """Flag colloquial/slang words that exceed Mode C's L2 register ceiling.

    Mode C target: "科技记者整理稿" — colloquial but formal (L2).
    Words below L2 (street slang, internet jargon) should be flagged.
    """
    zh_lines = _zh_lines_outside_blocks(zh_text)
    for ln, line in zh_lines:
        for word, suggestion in REGISTER_DRIFT_WORDS:
            if word in line:
                idx = line.index(word)
                context = line[max(0, idx-8):idx+len(word)+8].strip()
                report.add(
                    "warning", ln,
                    "语域漂移",
                    f"'{word}' 口语化超标 → 建议: {suggestion}。上下文: ...{context}...",
                )


def check_collocation_traps(report: LintReport, zh_text: str) -> None:
    """Flag literal translation traps where verb+object don't form natural Chinese pairs.

    These are specific to tech translation: English metaphors/collocations that
    break when translated literally (e.g., "paste your life", "free tier", "locked in").
    """
    zh_lines = _zh_lines_outside_blocks(zh_text)
    for ln, line in zh_lines:
        for bad, good, trap_type in COLLOCATION_TRAPS:
            if bad in line:
                idx = line.index(bad)
                context = line[max(0, idx-8):idx+len(bad)+8].strip()
                report.add(
                    "warning", ln,
                    "搭配陷阱",
                    f"'{bad}' — {trap_type} → 建议: {good}。上下文: ...{context}...",
                )


def check_currency_format(report: LintReport, zh_text: str) -> None:
    """Flag raw $ symbol in Chinese text (should be 美元/欧元)."""
    zh_lines = _zh_lines_outside_blocks(zh_text)
    for ln, line in zh_lines:
        # Skip code blocks
        stripped = line.strip()
        if stripped.startswith("```"):
            continue
        # Check for $ followed by digits (currency pattern)
        matches = re.finditer(r'\$\d', line)
        for m in matches:
            context = line[max(0, m.start()-8):m.end()+8].strip()
            report.add(
                "warning", ln,
                "货币格式",
                f"$ 符号应替换为'美元/欧元'。上下文: ...{context}...",
            )


# Words that should remain in English in Chinese tech articles.
# Anything else appearing as a standalone English word in Chinese context
# is likely an untranslated verb/adjective that slipped through.
ALLOWED_ENGLISH_IN_CHINESE = {
    # Tech products/platforms
    'Claude', 'ChatGPT', 'GPT', 'Obsidian', 'Notion', 'Slack', 'GitHub',
    'GitLab', 'VSCode', 'Cursor', 'Anthropic', 'OpenAI', 'Google', 'DeepMind',
    'Modal', 'Gemini', 'Codex', 'Twitter', 'LinkedIn', 'Reddit',
    # Tech terms (glossary §1)
    'LLM', 'RAG', 'Agent', 'Memory', 'Skills', 'Prompt', 'Token', 'MCP',
    'API', 'GUI', 'CLI', 'AGI', 'ASI', 'CUDA', 'MoE', 'PPO', 'HBM',
    'SSD', 'NAND', 'LPDDR', 'FLOPs', 'EUV', 'FDE', 'GRPO', 'RLVR',
    # AI concepts / named frameworks
    'Loss', 'Function', 'Expected', 'Goals', 'Bitter', 'Lesson',
    'The', 'LeetCode', 'Article',
    # Named concepts
    'Vibe', 'Coding', 'xG',
    # File/path names
    'CLAUDE', 'TODO', 'LOOP', 'STATE', 'raw', 'wiki',
    # Commands
    'goal', 'loop',
    # Social media / misc
    'xD', 'AI',
    # Common people names in AI industry (expand as needed)
    'Phil', 'Chen', 'Scale', 'Helm', 'Alfred', 'Lin', 'Michael',
    'Aman', 'Vlad', 'Boris', 'Cherny', 'Dario', 'Amodei', 'Daniela',
    'Andrej', 'Karpathy', 'Steph', 'Ango',
    # GitHub usernames / handles
    'kellerjordan',
}


def check_untranslated_english(report: LintReport, zh_text: str) -> None:
    """Flag English words in Chinese text that should have been translated.

    Catches cases like '这家公司在 tackling 其问题' where an English verb
    was left untranslated. Ignores known terms (product names, tech acronyms,
    person names, parenthetical annotations like '损失函数（Loss Function）').
    """
    zh_lines = _zh_lines_outside_blocks(zh_text)
    for ln, line in zh_lines:
        stripped = line.strip()
        # Skip frontmatter (title:, cover:, etc.)
        if stripped.startswith(('title:', 'cover:', '---')):
            continue
        # Skip image references ![...](...)
        if '![' in stripped:
            continue
        # Skip citation lines (source URLs at bottom)
        if stripped.startswith('*') and ('来源' in stripped or 'http' in stripped):
            continue
        # Skip headings (may contain English commands)
        if stripped.startswith('#'):
            continue
        # Skip lines that are purely URLs
        if stripped.startswith('http'):
            continue

        # Find all English word sequences (2+ chars)
        matches = re.finditer(r'[A-Za-z]{2,}', line)
        for m in matches:
            word = m.group()
            # Skip if it's an allowed term
            if word in ALLOWED_ENGLISH_IN_CHINESE:
                continue
            # Skip if inside parentheses (annotation pattern like 损失函数（Loss Function）)
            before = line[:m.start()]
            if '（' in before and before.rfind('（') > before.rfind('）'):
                continue
            if '(' in before and before.rfind('(') > before.rfind(')'):
                continue
            # Skip if inside backticks (inline code)
            if before.count('`') % 2 == 1:
                continue
            # Skip if it looks like a filename/path
            context_after = line[m.end():m.end()+3]
            if '.' in context_after and context_after.index('.') <= 2:
                continue
            if '/' in line[max(0,m.start()-3):m.end()+3]:
                continue
            # This is likely an untranslated word
            context = line[max(0, m.start()-10):m.end()+10].strip()
            report.add(
                "warning", ln,
                "英文夹杂",
                f"'{word}' 在中文行文中未翻译。上下文: ...{context}...",
            )


def check_preposition_chain(report: LintReport, zh_text: str) -> None:
    """Flag redundant preposition chains like '在...在...在' in the same clause.

    Catches grammar errors like '主动在多花一点时间在打磨' where the same
    preposition appears 3+ times in one sentence, causing clear redundancy.
    Threshold is set to 3 to avoid false positives on natural 2-occurrence usage.
    """
    zh_lines = _zh_lines_outside_blocks(zh_text)
    for ln, line in zh_lines:
        # Only check '在' (most common chain error)
        count = line.count('在')
        if count >= 3:
            context = line.strip()[:80]
            report.add(
                "info", ln,
                "介词链冗余",
                f"'在' 出现 {count} 次，可能存在语法冗余。上下文: ...{context}...",
            )


def check_is_about_pattern(report: LintReport, zh_text: str) -> None:
    """Flag 'X 是关于 Y' machine-translation patterns.

    'A is about B' is a classic English sentence structure. When translated
    literally as 'A 是关于 B', it reads like a machine translation.
    Chinese prefers conclusive statements: 'A 的核心是 B' / 'A 本质上是 B'.

    Also catches similar patterns: '问题是关于' / '关键是关于' / '重点是关于'.
    """
    # Patterns that indicate "is about" literal translation
    is_about_patterns = [
        r'是关于',          # "X 是关于 Y"
        r'问题是关于',      # "The problem is about"
        r'关键是关于',      # "The key is about"
        r'重点是关于',      # "The focus is about"
        r'核心是关于',      # "The core is about"
        r'本质是关于',      # "The essence is about"
        r'生活是关于',      # "Life is about" (specific case from review)
        r'目标是关于',      # "The goal is about"
        r'意义是关于',      # "The meaning is about"
    ]
    zh_lines = _zh_lines_outside_blocks(zh_text)
    for ln, line in zh_lines:
        for pattern in is_about_patterns:
            if re.search(pattern, line):
                context = line.strip()[:80]
                report.add(
                    "warning", ln,
                    "机翻句式",
                    f"'{pattern}' 是英文 'is about' 直译，建议改为结论性表述。上下文: ...{context}...",
                )
                break  # One flag per line is enough


def check_term_consistency(report: LintReport, zh_text: str) -> None:
    """Flag inconsistent translations of the same English term.

    When the same English word appears multiple times in the translation with
    different Chinese renderings (e.g., 'ambitious' → both '雄心' and '野心'),
    it indicates a consistency bug.

    Uses a curated list of terms that are commonly mistranslated inconsistently.
    """
    # Terms that have multiple valid translations but should be consistent per article
    # Format: {english_term: [accepted_translations]}
    # If multiple variants from the same group appear, flag it
    CONSISTENCY_GROUPS = {
        'ambitious': ['雄心', '野心', '有抱负'],
        'bitter lesson': ['苦涩教训', '苦涩的教训', '惨痛教训'],
        'alignment': ['对齐', '一致', '对齐机制'],
        'scaling': ['扩展', '规模化', '缩放'],
        'frontier': ['前沿', '前线'],
        'leverage': ['杠杆', '借力', '利用'],
        'trade-off': ['权衡', '取舍', '折中'],
        'bootstrap': ['自举', '引导', '启动'],
    }

    zh_lines = _zh_lines_outside_blocks(zh_text)
    for eng_term, variants in CONSISTENCY_GROUPS.items():
        found_variants = set()
        for ln, line in zh_lines:
            for variant in variants:
                if variant in line:
                    found_variants.add((variant, ln))

        # If multiple variants found, flag inconsistency
        unique_variants = set(v for v, _ in found_variants)
        if len(unique_variants) > 1:
            lines_str = ', '.join(f"L{ln}='{v}'" for v, ln in sorted(found_variants, key=lambda x: x[1]))
            report.add(
                "warning", 0,
                "术语不一致",
                f"'{eng_term}' 在译文中出现多种译法: {lines_str}。建议统一为一种",
            )


# ── Main ─────────────────────────────────────────────────────────────────────

def lint(original_text: str, translated_text: str, en_path: str = "<stdin>", zh_path: str = "<stdin>") -> LintReport:
    report = LintReport(en_path=en_path, zh_path=zh_path)

    check_number_parity(report, original_text, translated_text)
    check_backtick_pairs(report, translated_text)
    check_forbidden_phrases(report, translated_text)
    check_pronoun_abuse(report, translated_text)
    check_de_chain(report, translated_text)
    check_bei_de_chain(report, translated_text)
    check_passive_redundancy(report, translated_text)
    check_pangu_spacing(report, translated_text)
    check_codeblock_lang_labels(report, translated_text)
    check_known_collocations(report, translated_text)
    check_ascii_quotes(report, translated_text)
    check_quote_pairing(report, translated_text)
    check_delivery_alignment(report, original_text, translated_text)
    check_cli_inline_code(report, translated_text)
    check_register_drift(report, translated_text)
    check_collocation_traps(report, translated_text)
    check_currency_format(report, translated_text)
    check_untranslated_english(report, translated_text)
    check_preposition_chain(report, translated_text)
    check_is_about_pattern(report, translated_text)
    check_term_consistency(report, translated_text)

    return report


def format_report(report: LintReport) -> str:
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("Translation Lint Report")
    lines.append(f"  EN: {report.en_path}")
    lines.append(f"  ZH: {report.zh_path}")
    lines.append("=" * 60)

    # Stats
    lines.append(f"\nStats:")
    for k, v in report.stats.items():
        lines.append(f"  {k}: {v}")

    # Findings by severity
    by_sev: dict[str, list[Finding]] = {"error": [], "warning": [], "info": []}
    for f in report.findings:
        by_sev[f.severity].append(f)

    for sev, label, prefix in [("error", "ERRORS", "ERR"), ("warning", "WARNINGS", "WARN"), ("info", "INFO", "INFO")]:
        items = by_sev[sev]
        if not items:
            continue
        lines.append(f"\n[{prefix}] {label} ({len(items)}):")
        for f in items:
            loc = f"L{f.line}" if f.line else "—"
            lines.append(f"  [{f.category}] {loc}: {f.detail}")

    lines.append(f"\n{'=' * 60}")
    total = len(report.findings)
    if total == 0:
        lines.append("[OK] All checks passed.")
    else:
        lines.append(f"Total: {report.errors} errors, {report.warnings} warnings, "
                     f"{len(by_sev['info'])} info notes")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    args = sys.argv[1:]

    # File mode
    non_flag = [a for a in args if not a.startswith("--")]
    if len(non_flag) != 2:
        print(f"Usage: python {Path(__file__).name} <original_en.md> <translated_zh.md>", file=sys.stderr)
        sys.exit(2)

    en_path, zh_path = non_flag[0], non_flag[1]

    try:
        en_text = Path(en_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: file not found: {en_path}", file=sys.stderr)
        sys.exit(2)

    try:
        zh_text = Path(zh_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: file not found: {zh_path}", file=sys.stderr)
        sys.exit(2)

    report = lint(en_text, zh_text, en_path, zh_path)
    print(format_report(report))
    sys.exit(1 if report.errors > 0 else 0)


if __name__ == "__main__":
    main()
