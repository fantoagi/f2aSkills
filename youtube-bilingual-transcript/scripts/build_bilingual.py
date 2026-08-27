#!/usr/bin/env python3
"""
Build a clean transcript markdown from one or more yt-dlp-fetched SRT subtitle tracks.
Platform-general: works for YouTube (en+zh), bilibili (often a single Chinese CC track),
or any platform/subtitle set that yt-dlp can export.

The SRTs are "rolling captions": each caption's time window overlaps the next, so
inter-cue GAP-based paragraphing does not work (gaps are mostly negative). This script
paragraphizes on the FIRST (primary) track by sentence-final punctuation (English or CJK),
keeps a monotonic pointer into each secondary track, and assigns each secondary cue to
exactly one paragraph by "start-time falls in the paragraph window" so no text is duplicated.

A single track -> mono transcript. Two (or more) tracks -> bilingual side-by-side.
The FIRST track is used for segmentation (the "anchor"); subsequent tracks are aligned
into each segment. Column order follows the order you pass tracks.

Usage (general, repeatable --subs lang:path):
    python build_bilingual.py --subs "en:path.en.srt" --subs "zh-Hans:path.zh-Hans.srt" --out out.md ...
    python build_bilingual.py --subs "zh-CN:path.zh.srt" --out out.md ...     # mono

Usage (legacy YouTube-compatible):
    python build_bilingual.py --en path.en.srt --zh path.zh-Hans.srt --out out.md ...
"""
import argparse
import os
import re


def parse_srt(path):
    """Parse an .srt file into [[start_ms, end_ms, text], ...]."""
    with open(path, encoding="utf-8-sig") as f:
        raw = f.read()
    cues = []
    for block in raw.strip().split("\n\n"):
        lines = block.split("\n")
        if len(lines) < 3:
            continue
        m = re.match(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", lines[1])
        if not m:
            continue
        start = int(m[1]) * 3600000 + int(m[2]) * 60000 + int(m[3]) * 1000 + int(m[4])
        end = int(m[5]) * 3600000 + int(m[6]) * 60000 + int(m[7]) * 1000 + int(m[8])
        text = re.sub(r"\s+", " ", " ".join(line.strip() for line in lines[2:])).strip()
        cues.append([start, end, text])
    cues.sort(key=lambda c: c[0])
    return cues


# Strong sentence-ending punctuation (English + CJK). Used as the paragraph break.
TERMINAL = re.compile(r"[.?!…。？！]+$")
# Stray whitespace between two CJK characters (subtitle line-breaks).
CJK_JOIN = re.compile(r"(?<=[一-鿿])\s+(?=[一-鿿])")

# Human-facing column labels for known language codes.
LABEL = {
    "en": "EN", "en-us": "EN", "en-gb": "EN", "英": "EN", "英文": "EN",
    "zh": "ZH", "zh-hans": "ZH", "zh-hant": "ZH", "zh-cn": "ZH", "cmn": "ZH",
    "中文": "ZH", "中": "ZH",
}


def clean(text):
    """Strip YouTube speaker-turn arrows and normalize whitespace / CJK spacing."""
    text = re.sub(r"^>>\s*", "", text).strip()          # leading ">>" speaker marker
    text = re.sub(r"\s+", " ", text)                    # collapse runs
    return CJK_JOIN.sub("", text).strip()               # de-space between CJK chars


def fmt_ms(ms):
    s = ms // 1000
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def column_label(lang):
    key = lang.strip().lower()
    if key in LABEL:
        return LABEL[key]
    return key.upper() if len(key) <= 6 else lang


# Fallback paragraph break for punctuation-free tracks (e.g. bilibili AI subtitles,
# which carry no 。！？ or any terminal punctuation): break on a silence gap instead.
GAP_BREAK_MS = 1500


def _paragraphize_punct(cues):
    """Group cues into paragraphs, breaking only at sentence-final punctuation."""
    paras = []
    cur, cstart, cend = [], None, None
    for start, end, text in cues:
        if cstart is None:
            cstart = start
        cend = max(cend or end, end)
        cur.append(clean(text))
        if TERMINAL.search(text):
            paras.append([cstart, cend, " ".join(cur)])
            cur, cstart, cend = [], None, None
    if cur:
        paras.append([cstart, cend, " ".join(cur)])
    return paras


def _paragraphize_gap(cues, gap_ms=GAP_BREAK_MS):
    """Group cues into paragraphs, breaking when the silence before a cue >= gap_ms."""
    paras = []
    cur, cstart, cend = [], None, None
    for start, end, text in cues:
        if cur and cend is not None and (start - cend) >= gap_ms:
            paras.append([cstart, cend, " ".join(cur)])
            cur, cstart, cend = [], None, None
        if cstart is None:
            cstart = start
        cend = max(cend or end, end)
        cur.append(clean(text))
    if cur:
        paras.append([cstart, cend, " ".join(cur)])
    return paras


def paragraphize(cues):
    """Group cues into paragraphs.

    Prefer sentence-final punctuation; fall back to silence-gap breaking for
    punctuation-free subtitle tracks (bilibili AI subtitles have no terminal
    punctuation, so punctuation-only logic would collapse the whole video).
    """
    if any(TERMINAL.search(t) for _s, _e, t in cues):
        return _paragraphize_punct(cues)
    return _paragraphize_gap(cues)


def assign_secondary(paras, sec):
    """Assign each secondary cue to the single paragraph whose window contains its start."""
    out = []
    zidx = 0
    for ps, pe, txt in paras:
        parts = []
        while zidx < len(sec):
            za, _zb, zt = sec[zidx]
            if za >= pe:
                break
            if za >= ps:
                parts.append(clean(zt))
            zidx += 1
        out.append((ps, txt, " ".join(parts)))
    return out


def emit(rows, labels, has_secondary, meta):
    """Render final markdown; rows are 2-tuples (ts, primary) or 3-tuples (ts, primary, secondary)."""
    lines = ["---"]
    for k, v in meta.items():
        lines.append(f"{k}: {v}")
    lines += ["---", "", "# 中英对照逐字稿", ""]
    for row in rows:
        ts, primary = row[0], row[1]
        lines.append(f"> **{fmt_ms(ts)}**")
        lines.append(">")
        lines.append(f"> {labels[0]}：{primary}")
        if has_secondary:
            lines.append(f"> {labels[1]}：{row[2]}")
        lines.append(">")
    return "\n".join(lines).replace("\n>\n>\n", "\n>\n")


def main():
    ap = argparse.ArgumentParser(description="Build transcript markdown from SRT subtitle tracks.")
    ap.add_argument("--subs", action="append", metavar="LANG:PATH",
                    help="subtitle track as 'lang:/path/to.srt'; repeatable, order = display order. Track 0 is the paragraph anchor.")
    ap.add_argument("--en", help="(legacy) English .srt -> track 0")
    ap.add_argument("--zh", help="(legacy) Chinese .srt -> track 1")
    ap.add_argument("--out", required=True, help="output markdown path")
    ap.add_argument("--title", default="Transcript", help="title for frontmatter")
    ap.add_argument("--source-url", default="", help="source URL")
    ap.add_argument("--duration", default="", help="duration string")
    ap.add_argument("--channel", default="", help="channel name")
    ap.add_argument("--video-id", default="", help="platform video id")
    ap.add_argument("--note", default="", help="extra frontmatter note")
    args = ap.parse_args()

    # Normalize to ordered [(lang, path), ...]
    subs = []
    if args.subs:
        for s in args.subs:
            lang, path = s.split(":", 1)
            subs.append((lang, path))
    if args.en and args.zh:
        if not subs:
            subs = [("en", args.en), ("zh-Hans", args.zh)]
    if args.en and not subs:
        subs = [("en", args.en)]
    if not subs:
        raise SystemExit("Need --subs 'lang:path' (repeatable), or --en/--zh. Got nothing.")

    for lang, path in subs:
        if not os.path.exists(path):
            raise SystemExit(f"Missing subtitle file: {path}")

    meta = {"title": f'"{args.title}"', "source-type": "transcript", "status": "unprocessed"}
    for key, val in (("source-url", args.source_url), ("duration", args.duration),
                     ("channel", args.channel), ("video-id", args.video_id),
                     ("date-added", "2026-08-26")):
        if val:
            meta[key] = val
    if args.note:
        meta["note"] = args.note

    tracks = [(lang, parse_srt(path)) for lang, path in subs]
    labels = [column_label(lang) for lang, _ in tracks]
    has_secondary = len(tracks) >= 2
    rows = paragraphize(tracks[0][1])       # each row = [start_ms, end_ms, text]
    if has_secondary:
        rows = assign_secondary(rows, tracks[1][1])   # each row = (start_ms, primary_text, secondary_text)
    else:
        rows = [(r[0], r[2]) for r in rows]           # normalize to (start_ms, text)

    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(emit(rows, labels, has_secondary, meta))
    with_secondary = sum(1 for r in rows if has_secondary and len(r) > 2 and r[2])
    print(f"paragraphs: {len(rows)}  tracks: {len(tracks)}  secondary-filled: {with_secondary}  wrote: {args.out}")


if __name__ == "__main__":
    main()
