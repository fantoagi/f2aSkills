#!/usr/bin/env python3
"""链接完整性检查 — URL 源材料翻译的链接丢失检测。

为什么存在：
  2026-08-04 Lilian Weng harness 文章翻译：45 个正文内嵌链接 + 39 条参考文献
  链接全部静默丢失，交付闸门"嵌入链接对齐"未能检出——因为源对比文本是
  从 HTML 提取后的纯文本（<a href> 已被 re.sub 剥掉），源侧计数恒为 0，
  对比恒等通过。本脚本直接读 HTML 原文的 <a href> 计数做真源对比。

用法：
  python scripts/check_links.py <source.html> <translated_zh.md>
  python scripts/check_links.py <source.html> <translated_zh.md> --details

输出：
  原文外部链接总数/唯一数、译文 URL 总数/唯一数、保真判定。
  exit 0 = 链接保真；exit 1 = 疑似丢失（译文唯一 URL < 原文唯一外部链接 × 0.85）

判定逻辑：
  - 译文唯一 URL 数 ≥ 原文唯一外部链接数 × 0.85 且差值 ≤ 2 → PASS
  - 否则 FAIL，列出原文中未在译文出现的 URL 前 20 条
  - 唯一数对比（而非总数）避免"同一 URL 重复引用"造成的假警报
"""

import re
import sys
from pathlib import Path


def extract_source_links(html: str) -> tuple[list[str], list[str]]:
    """Return (external_hrefs, anchor_hrefs) from the article/main body.

    Share-button URLs (twitter intent, facebook sharer, etc.) are excluded —
    they are page chrome, not content links, and should not appear in a
    translation.
    """
    m = re.search(r"<article[^>]*>(.*?)</article>", html, re.S)
    if not m:
        m = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    body = m.group(1) if m else html
    hrefs = re.findall(r'<a[^>]*href="([^"]+)"', body)
    share_markers = (
        "sharer", "submit", "intent/", "shareArticle", "share/url",
        "send?text=", "whatsapp", "/tags/",  # 页脚标签也是页面 chrome
    )
    external = [
        h for h in hrefs
        if h.startswith("http") and not any(mk in h for mk in share_markers)
    ]
    anchors = [h for h in hrefs if h.startswith("#")]
    return external, anchors


def extract_translation_urls(zh: str) -> list[str]:
    """Return URLs found in translation: <URL> autolink + [text](url) formats.

    NOTE: the autolink regex MUST use a capture group. `re.findall` on a
    pattern without one returns the full match including the angle brackets,
    so `<https://...>` would not equal the source's `https://...` and the
    sets would be disjoint (2026-08-04: caused a false FAIL of all 65 URLs).
    """
    autolinks = re.findall(r"<(https?://[^>]+)>", zh)
    markdown = re.findall(r"\[[^\]]+\]\((https?://[^)]+)\)", zh)
    bare = re.findall(r"(?<![<\w])(https?://[^\s<>()]+)", zh)
    return autolinks + markdown + bare


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    html_path = Path(sys.argv[1])
    zh_path = Path(sys.argv[2])
    details = "--details" in sys.argv

    html = html_path.read_text(encoding="utf-8", errors="replace")
    zh = zh_path.read_text(encoding="utf-8", errors="replace")

    external, anchors = extract_source_links(html)
    zh_urls = extract_translation_urls(zh)

    src_unique = set(external)
    zh_unique = set(zh_urls)

    ratio_threshold = 0.85
    missing = src_unique - zh_unique
    fail = len(zh_unique) < max(2, int(len(src_unique) * ratio_threshold)) or len(missing) > 2

    print("## 链接完整性检查报告")
    print("")
    print(f"源文件：`{html_path.name}`｜译文：`{zh_path.name}`")
    print("")
    print("### 统计")
    print("")
    print("| 项 | 原文 | 译文 |")
    print("|----|------|------|")
    print(f"| 外部链接（含重复） | {len(external)} | {len(zh_urls)} |")
    print(f"| 唯一 URL | {len(src_unique)} | {len(zh_unique)} |")
    print(f"| 站内锚点（#，不计入保真） | {len(anchors)} | — |")
    print("")
    print("### 判定")
    print("")
    if fail:
        print(f"**FAIL：疑似链接丢失。** 译文唯一 URL（{len(zh_unique)}）显著少于原文唯一外部链接（{len(src_unique)}）。")
        if missing:
            print("")
            print("原文有、译文缺失的 URL（前 20 条）：")
            for u in sorted(missing)[:20]:
                print(f"- <{u}>")
    else:
        print(f"**PASS：链接保真。** 译文唯一 URL {len(zh_unique)} ≥ 原文唯一外部链接 {len(src_unique)} 的 {int(ratio_threshold * 100)}% 且差值 ≤ 2。")
    if details:
        print("")
        print("### 译文全部 URL")
        for u in sorted(zh_unique):
            print(f"- <{u}>")
    print("")
    return 1 if fail else 0


if __name__ == "__main__":
    import io
    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.exit(main())
