"""
Auto-sync guizang-social-card-skill output to the article directory.

Why this exists:
  Previously, after guizang-social-card-skill generated covers into its `output/`
  directory, the user had to manually `cp` them into the article directory. This
  step was easy to forget — and SKILL.md delivery gate #8 (cover.png exists and
  >0 bytes) would then fail. This script makes the sync automatic.

Behavior:
  - Reads the article path → resolves article directory
  - Searches the guizang output directory for the latest `wechat-21x9-cover.png`
    and `wechat-1x1-cover.png` (or uses the explicit `--21x9` / `--1x1` paths)
  - Copies them to `<article-dir>/cover.png` and `<article-dir>/cover_square.png`
  - Updates the article's frontmatter `cover:` field to `./cover.png` if missing
    or pointing to a different relative path. Leaves the `cover:` field alone
    if it already points to `./cover.png` (idempotent).
  - Prints a clear status line; exits non-zero on any failure.

Depends on: Python stdlib only.

Usage:
  python scripts/sync_cover.py <article.md>
  python scripts/sync_cover.py <article.md> --guizang-output output/
  python scripts/sync_cover.py <article.md> --21x9 path/to/21x9.png --1x1 path/to/square.png
"""

import argparse
import os
import re
import shutil
import sys


def find_cover(output_dir, ratio):
    """Find the latest cover file matching the given ratio in output_dir.

    ratio: "21x9" or "1x1"

    Looks for exact name first, then falls back to glob pattern. Returns
    the file with the most recent mtime if multiple matches.
    """
    if not os.path.isdir(output_dir):
        return None
    exact = os.path.join(output_dir, f"wechat-{ratio}-cover.png")
    if os.path.isfile(exact):
        return exact
    # Fallback: glob pattern (some guizang versions may use slightly different names)
    pattern = re.compile(rf"wechat.*{re.escape(ratio)}.*\.png$", re.IGNORECASE)
    matches = []
    for fname in os.listdir(output_dir):
        if pattern.match(fname):
            matches.append(os.path.join(output_dir, fname))
    if not matches:
        return None
    # Pick the most recently modified file
    matches.sort(key=os.path.getmtime, reverse=True)
    return matches[0]


def update_frontmatter_cover(article_path, relative_cover="./cover.png"):
    """Ensure the article's frontmatter has `cover: <relative_cover>`.

    - If frontmatter is missing → no-op (caller can prepend a default block).
    - If `cover:` line exists → leave alone if it already equals relative_cover,
      otherwise replace the path (keep the rest of the line intact).
    - If `cover:` line is missing → insert it right after `title:` (or at end of
      frontmatter if `title:` is also missing).
    """
    with open(article_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match the frontmatter block (between the first pair of ---)
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not fm_match:
        return False, "no frontmatter found (skipped)"

    fm_block = fm_match.group(1)
    rest = content[fm_match.end():]

    cover_re = re.compile(r"^(\s*cover\s*:\s*).*$", re.MULTILINE)
    cover_match = cover_re.search(fm_block)

    if cover_match:
        current = cover_match.group(0)
        if relative_cover in current:
            return False, f"cover already set to {relative_cover}"
        new_fm = cover_re.sub(f"\\g<1>{relative_cover}", fm_block, count=1)
        action = f"updated cover → {relative_cover}"
    else:
        # Insert after `title:` if present, else at end of frontmatter
        title_re = re.compile(r"^(\s*title\s*:.*)$", re.MULTILINE)
        title_match = title_re.search(fm_block)
        insert_line = f"cover: {relative_cover}"
        if title_match:
            new_fm = fm_block[: title_match.end()] + "\n" + insert_line + fm_block[title_match.end():]
        else:
            new_fm = fm_block.rstrip() + "\n" + insert_line
        action = f"inserted cover: {relative_cover}"

    new_content = f"---\n{new_fm}\n---\n{rest}"
    if new_content != content:
        with open(article_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    return True, action


def read_png_size(path):
    """Read PNG dimensions from the IHDR chunk (no Pillow dependency).

    Returns (width, height) or None if the file is not a valid PNG."""
    with open(path, "rb") as f:
        head = f.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w = int.from_bytes(head[16:20], "big")
    h = int.from_bytes(head[20:24], "big")
    return w, h


def check_title_h1(article_path):
    """Verify frontmatter title matches the first H1 heading.

    Returns (ok, title, h1). ok=False only when both exist and differ.
    A mismatched title/H1 is a delivery-gate violation (frontmatter.title
    and the body # heading must be identical per SKILL.md)."""
    with open(article_path, "r", encoding="utf-8") as f:
        content = f.read()
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    body_start = fm_match.end() if fm_match else 0
    title = None
    if fm_match:
        tm = re.search(r"^title\s*:\s*(.+?)\s*$", fm_match.group(1), re.MULTILINE)
        if tm:
            title = tm.group(1).strip().strip('"\'')
    h1 = None
    hm = re.search(r"^#\s+(.+?)\s*$", content[body_start:], re.MULTILINE)
    if hm:
        h1 = hm.group(1).strip()
    if title and h1 and title != h1:
        return False, title, h1
    return True, title, h1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("article", help="path to article .md file")
    parser.add_argument("--guizang-output", default="output/",
                        help="guizang-social-card-skill output directory (default: output/)")
    parser.add_argument("--21x9", dest="cover_21x9", help="explicit path to 21:9 cover (overrides --guizang-output)")
    parser.add_argument("--1x1", dest="cover_1x1", help="explicit path to 1:1 cover (overrides --guizang-output)")
    parser.add_argument("--name-21x9", dest="name_21x9", default="cover.png",
                        help="target filename for 21:9 cover in article dir (default: cover.png)")
    parser.add_argument("--name-1x1", dest="name_1x1", default="cover_square.png",
                        help="target filename for 1:1 cover in article dir (default: cover_square.png)")
    parser.add_argument("--no-frontmatter", action="store_true",
                        help="skip frontmatter cover: field update")
    args = parser.parse_args()

    article_path = os.path.abspath(args.article)
    if not os.path.isfile(article_path):
        print(f"ERROR: article not found: {article_path}", file=sys.stderr)
        sys.exit(1)

    article_dir = os.path.dirname(article_path)
    guizang_output = os.path.abspath(args.guizang_output) if not os.path.isabs(args.guizang_output) else args.guizang_output

    # Resolve source covers
    cover_21x9_src = args.cover_21x9 if args.cover_21x9 else find_cover(guizang_output, "21x9")
    cover_1x1_src = args.cover_1x1 if args.cover_1x1 else find_cover(guizang_output, "1x1")

    if not cover_21x9_src:
        print(
            f"ERROR: no 21:9 cover found in {guizang_output}\n"
            f"  expected: {guizang_output}/wechat-21x9-cover.png\n"
            f"  hint: run /guizang-social-card-skill first to generate the cover",
            file=sys.stderr,
        )
        sys.exit(2)

    # Copy 21:9 (mandatory)
    cover_21x9_dst = os.path.join(article_dir, args.name_21x9)
    shutil.copy2(cover_21x9_src, cover_21x9_dst)
    size_21x9 = os.path.getsize(cover_21x9_dst)
    print(f"[OK] 21:9 cover: {cover_21x9_src} -> {cover_21x9_dst} ({size_21x9} bytes)")

    # Copy 1:1 (optional, informational)
    if cover_1x1_src:
        cover_1x1_dst = os.path.join(article_dir, args.name_1x1)
        shutil.copy2(cover_1x1_src, cover_1x1_dst)
        size_1x1 = os.path.getsize(cover_1x1_dst)
        print(f"[OK] 1:1 cover:  {cover_1x1_src} -> {cover_1x1_dst} ({size_1x1} bytes)")
    else:
        print(f"[--] 1:1 cover:  not found in {guizang_output}, skipped")

    # Update frontmatter (unless disabled)
    if not args.no_frontmatter:
        changed, action = update_frontmatter_cover(article_path, f"./{args.name_21x9}")
        print(f"[OK] frontmatter: {action}")

    # Verification: title/H1 consistency + cover dimensions
    ok, title, h1 = check_title_h1(article_path)
    if not ok:
        print(f"[WARN] frontmatter title != first H1:\n"
              f"  frontmatter title: {title}\n"
              f"  first H1:          {h1}")
    else:
        print(f"[OK] frontmatter title == first H1")

    for label, dst in (("21:9", os.path.join(article_dir, args.name_21x9)),
                       ("1:1", os.path.join(article_dir, args.name_1x1))):
        if not os.path.isfile(dst):
            continue
        size = read_png_size(dst)
        if size is None:
            print(f"[WARN] {label} cover is not a valid PNG: {dst}")
            continue
        w, h = size
        ratio = w / h if h else 0
        expected = 7 / 3 if label == "21:9" else 1.0
        if abs(ratio - expected) > 0.05:
            print(f"[WARN] {label} cover ratio {ratio:.3f} (expected ~{expected:.3f}): "
                  f"{w}x{h} — {dst}")
        else:
            print(f"[OK] {label} cover ratio {ratio:.3f}: {w}x{h}")

    print(f"\nDone. Article: {article_path}")


if __name__ == "__main__":
    main()
