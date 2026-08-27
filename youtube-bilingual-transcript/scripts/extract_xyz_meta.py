#!/usr/bin/env python3
"""
Extract reusable metadata from a saved xiaoyuzhou (小宇宙) episode page, so a
DashScope transcription + final transcript can be driven by the page's own
structured fields instead of hand-typed names.

Reads the __NEXT_DATA__ JSON out of the saved episode HTML and writes three files
into the output dir:
  meta.json            - title / channel / author / duration / description /
                         shownotes_md (HTML shownotes -> Markdown, keeps bold/links/images)
                         host / guest / chapters[] / fde_expansion
  shownotes.md         - the converted Markdown shownotes (same as meta.shownotes_md)
  auto_vocab.json      - instant-hotwords for dashscope_asr_transcribe.py
                         (--vocabulary-file). Only STRUCTURALLY RELIABLE Chinese
                         proper nouns (publisher / guest / host-if-Chinese), because
                         a romanized host (e.g. "Yaxian") or a product name buried
                         in a marketing line cannot be guessed reliably.
  english_lexicon.json - Latin proper-noun tokens seen in the episode's own narrative
                         (e.g. FDE, OpenAI, Anthropic). REFERENCE ONLY: pass to a
                         light proofread step as a correction lexicon. Do NOT feed
                         these into the ASR vocabulary, or weight-5 English hotwords
                         split proper nouns into fragments (see SKILL.md known-gotcha).

Usage:
  python extract_xyz_meta.py --page D:/CC/_xyz_page.html --out-dir D:/CC/.cc-connect/_xyz_audio
  python dashscope_asr_transcribe.py --... --vocabulary-file OUT/auto_vocab.json --vocabulary '{"雅贤":5,"雷鸟":5}'
"""
import argparse
import json
import os
import re
from html.parser import HTMLParser

# Lines that end the narrative intro and start the boilerplate/metadata block.
SECTION_MARKERS = ("本期人物", "时间轴", "延伸阅读", "收听", "幕后制作",
                   "关于", "商业合作", "加入", "欢迎扫码")

# Latin tokens that are boilerplate / URLs / staff names / marketing noise, not brands.
LEXICON_STOP = {
    "com", "cn", "http", "https", "docx", "feishu", "shengfm", "sheng",
    "copylink", "nBh", "rdcl", "xmAMoc", "aGoI", "ting", "business", "from",
    "Guest", "Special", "Untitled", "WHY", "Yaxian", "George", "mono", "MP3",
}


def load_page(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        html = f.read()
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        raise SystemExit(f"No __NEXT_DATA__ in {path}")
    return json.loads(m.group(1))


def cjk_runs(s):
    """Contiguous runs of >=2 CJK chars."""
    return re.findall(r'[\u4e00-\u9fff]{2,}', s)


def name_token(s):
    """Person-name token from a person field.

    Take the substring before the first comma / CJK bracket / newline, so a
    romanized host followed by a channel name (e.g. "Yaxian，「科技早知道」主播")
    yields "Yaxian", not the channel name. A Chinese host ("雅贤，...") yields "雅贤".
    The caller decides whether the result is usable as a Chinese hotword (cjk_runs).
    """
    head = re.split(r"[，,、「\n]", s.strip())[0]
    return head.strip().rstrip("。，,.")


def format_duration(sec):
    if sec is None:
        return ""
    sec = int(sec)
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


class _ShownotesToMD(HTMLParser):
    """Convert the xiaoyuzhou shownotes HTML to Markdown, preserving bold / links /
    images / timestamp anchors so Obsidian renders it faithfully instead of as a
    flattened blob.

    Handles the observed nesting (strong<->anchor), timestamp anchors
    (<a class="timestamp">03:36</a> -> bold marker), <img> -> ![..](..),
    <br> -> newline, and strips the empty <span></span> break artifacts.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []          # flat list of text/formatting segments
        self.stack = []          # open frames: {'kind': 'B'|'A'|'T', 'idx': int, 'href': str}

    def emit(self, s):
        self.parts.append(s)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("strong", "b"):
            self.stack.append({"kind": "B", "idx": len(self.parts), "href": ""})
        elif tag == "a":
            cls = a.get("class", "")
            if "timestamp" in cls:
                self.stack.append({"kind": "T", "idx": len(self.parts), "href": ""})
            else:
                self.stack.append({"kind": "A", "idx": len(self.parts), "href": a.get("href", "")})
        elif tag == "img":
            self.emit("![%s](%s)" % (a.get("alt", ""), a.get("src", "")))
        elif tag == "br":
            self.emit("\n")
        elif tag == "p":
            # Preserve paragraph breaks so the shownotes doesn't collapse into one blob.
            if self.parts:
                self.emit("\n\n")
        # <span> carries no markdown of its own; its text passes through.

    def handle_endtag(self, tag):
        if tag in ("strong", "b"):
            self._close("B")
        elif tag == "p":
            self.emit("\n\n")
        elif tag == "a":
            # timestamp anchors are re-wrapped as A first if mismatched; close innermost
            self._close("A")
            self._close("T")

    def _close(self, kind):
        for i in range(len(self.stack) - 1, -1, -1):
            fr = self.stack[i]
            if fr["kind"] == kind:
                inner = "".join(self.parts[fr["idx"]:])
                self.parts = self.parts[:fr["idx"]]
                if not inner:
                    inner = ""
                if kind == "B":
                    self.emit("**%s**" % inner)
                elif kind == "T":
                    self.emit("**%s**" % inner)
                else:
                    self.emit("[%s](%s)" % (inner, fr["href"]))
                del self.stack[i]
                return

    def handle_data(self, data):
        if data:
            self.emit(data)

    def result(self):
        return "".join(self.parts)


def html_shownotes_to_md(html):
    """Convert assumed-xiaoyuzhou shownotes HTML to clean Markdown."""
    if not html:
        return ""
    p = _ShownotesToMD()
    try:
        p.feed(html)
        p.close()
    except Exception:
        # Fail-open: fall back to the description text if the HTML is malformed.
        return _strip_html(html)
    md = p.result()
    # Normalize a marking-up artifact the producer leaves behind: a literal
    # "[text](" immediately followed by a real "[inner](href)". Collapse the
    # double bracket to a single "[text](href)" instead of nesting two links.
    md = re.sub(r"(\[[^\]]+\]\()\[[^\]]*\]\(([^)]*)\)\)", r"\1\2)", md)
    lines = []
    for ln in md.split("\n"):
        s = ln.strip()
        if not s:
            if not lines or lines[-1] != "":
                lines.append("")
            continue
        lines.append(s)
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _strip_html(s):
    return re.sub(r"<[^>]+>", "", re.sub(r"<[^>]*/\s*>", "", s)).strip()


def main():
    ap = argparse.ArgumentParser(description="Extract xiaoyuzhou episode metadata into reuse-ready JSON.")
    ap.add_argument("--page", required=True, help="saved xiaoyuzhou episode HTML (with __NEXT_DATA__)")
    ap.add_argument("--out-dir", default=".", help="directory to write meta.json / auto_vocab.json / english_lexicon.json")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    d = load_page(args.page)
    ep = d["props"]["pageProps"]["episode"]
    podcast = ep.get("podcast", {})
    desc = ep.get("description", "")

    title = ep.get("title", "")
    channel = podcast.get("title", "")
    author = podcast.get("author", "")
    duration_sec = ep.get("duration")

    # --- chapters: lines like [MM:SS] title -------------------------------
    chapters = []
    for line in desc.split("\n"):
        mm = re.match(r"\s*\[(\d{1,2}:\d{2})\]\s*(.+)$", line)
        if mm:
            chapters.append({"t": mm.group(1), "title": mm.group(2).strip()})

    # --- hosts / guests ----------------------------------------------------
    host = guest = ""
    for line in desc.split("\n"):
        s = line.strip()
        g = re.search(r"^Special Guest:\s*(.+)$", s)
        if g and not guest:
            guest = name_token(g.group(1))
        if "主播" in s and not host:
            host = name_token(s)
        if ("嘉宾" in s or "顾问" in s or "培训讲师" in s) and not guest and "主播" not in s:
            guest = name_token(s)

    # --- narrative body (before boilerplate) for Latin lexicon -------------
    body_lines, stop_check = [], False
    for line in desc.split("\n"):
        stripped = line.strip()
        if any(stripped == m or stripped.startswith(m) for m in SECTION_MARKERS):
            stop_check = True
            if stripped == "本期人物" or stripped == "时间轴":
                continue
            break
        if not stop_check:
            body_lines.append(line)
    body = "\n".join(body_lines)

    latin = set()
    for src in (body, title, "\n".join(c["title"] for c in chapters)):
        for tok in re.findall(r"[A-Za-z][A-Za-z]{2,}", src):
            if tok in LEXICON_STOP or tok.islower():
                continue
            if tok.endswith("s") and re.sub(r"s$", "", tok).islower():
                continue
            latin.add(tok)

    fde_exp = ""
    mfe = re.search(r"FDE（([^（）]+)）", desc)
    if mfe:
        fde_exp = mfe.group(1).strip()

    # Full shownotes live in episode.shownotes as HTML (bold/links/images/timestamps);
    # convert to Markdown so the final wiki preserves the original layout.
    shownotes_md = html_shownotes_to_md(ep.get("shownotes", ""))

    meta = {
        "title": title,
        "channel": channel,
        "author": author,
        "duration_sec": duration_sec,
        "duration_ts": format_duration(duration_sec),
        "description": desc,
        "shownotes_md": shownotes_md,
        "host": host,
        "guest": guest,
        "chapters": chapters,
        "fde_expansion": fde_exp,
    }
    with open(os.path.join(args.out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # auto_vocab: ONLY reliable Chinese proper nouns (author + non-romanized host/guest).
    vocab = {}
    for name in (author, host, guest):
        if name and cjk_runs(name):  # romanized host "Yaxian" has no CJK -> skipped
            vocab[name] = 5
    with open(os.path.join(args.out_dir, "auto_vocab.json"), "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=2)

    with open(os.path.join(args.out_dir, "english_lexicon.json"), "w", encoding="utf-8") as f:
        json.dump(sorted(latin), f, ensure_ascii=False, indent=2)

    with open(os.path.join(args.out_dir, "shownotes.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(shownotes_md)

    print("meta.json       :", meta["title"], "|", meta["channel"], "| dur", meta["duration_ts"])
    print("  host=", host, " guest=", guest, " chapters=", len(chapters))
    print("auto_vocab.json :", vocab)
    print("english_lexicon :", sorted(latin))
    print("shownotes.md    : %d chars" % len(shownotes_md))


if __name__ == "__main__":
    main()
