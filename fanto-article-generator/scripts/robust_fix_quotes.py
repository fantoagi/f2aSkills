#!/usr/bin/env python3
"""Robust quote fixer: collapse-then-rebuild protocol (full-text aware).

Why this exists: the Write/Edit tools sometimes convert full-width Chinese
quotes into ASCII double quotes. The previous heuristic (context-based
left/right decision) produced wrong-direction quotes ("X" style) whenever a
quote sat between two CJK chars (the most common case for Chinese quotes).

Algorithm (verified 2026-08-10 on 41/41 and 43/43 pairs; 2026-08-30 fix):
  1. Collapse every curly quote (" " ' ' " ) into a placeholder.
  2. Scan left-to-right, alternately rebuilding " and " (open/close), with
     the left/right alternation carried ACROSS lines (full-text), not reset
     per line.
  3. Skip markdown fenced code blocks AND inline `code` spans — quotes inside
     them are literal (a literal '"' used to explain the quote character must
     never be rebuilt).
  4. Report balance; warn if odd count (unpaired quote = source problem).

2026-08-30 bugfix: previously (a) inline `code` spans were not skipped, so a
literal '"' inside a code span (e.g. SKILL.md L945/L947 explaining the quote
char) was rebuilt as a stray full-width quote; and (b) the left/right
alternation reset at every line, so an odd literal quote in one line pushed
the whole file's balance off by one. Both are now fixed via inline-code
masking + full-text alternation, verified to yield 191/191 balance on
SKILL.md (376 body ASCII quotes -> full-width, 15 fence + 42 inline-code
ASCII quotes legitimately preserved).

Usage:
  python robust_fix_quotes.py <file.md>            # rebuild in place
  python robust_fix_quotes.py <file.md> --dry-run  # report only, no write
"""
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

LEFT = '“'    # "
RIGHT = '”'   # "
SLEFT = '‘'   # '
SRIGHT = '’'  # '
PLACEHOLDER_DQ = '\x01'
PLACEHOLDER_SQ = '\x02'
MASK_INLINE = '\x03'
INLINE_CODE = re.compile(r'`[^`]*`')  # single-line inline code span


class QuoteState:
    """Carries the left/right alternation across the whole file (full-text),
    so one stray literal quote can no longer desync every later line."""
    def __init__(self):
        self.dq_left = True
        self.sq_left = True
        self.total = 0


def fix_line(line: str, state: QuoteState) -> str:
    """Collapse quote variants, then rebuild each kind with its own
    alternating sequence carried in `state`.

    Inline `code` spans are masked out first, so a literal '"' inside a code
    span (used to explain the quote character itself) stays untouched; then
    restored verbatim after rebuilding surrounding quotes. ASCII apostrophe
    (') is deliberately excluded from the single-quote alternation — in
    English text it is an apostrophe (Dell'Acqua, don't, performers'), not a
    quote delimiter. Only the curly single quotes (' ') participate."""
    masks = []

    def shield(match):
        masks.append(match.group(0))
        return MASK_INLINE

    shielded = INLINE_CODE.sub(shield, line)

    collapsed = []
    for ch in shielded:
        if ch in '"“”':
            collapsed.append(PLACEHOLDER_DQ)
        elif ch in '‘’':
            collapsed.append(PLACEHOLDER_SQ)
        else:
            collapsed.append(ch)

    out = []
    n = 0
    for ch in collapsed:
        if ch == PLACEHOLDER_DQ:
            out.append(LEFT if state.dq_left else RIGHT)
            state.dq_left = not state.dq_left
            n += 1
        elif ch == PLACEHOLDER_SQ:
            out.append(SLEFT if state.sq_left else SRIGHT)
            state.sq_left = not state.sq_left
            n += 1
        else:
            out.append(ch)

    rebuilt = ''.join(out)
    for mask in masks:
        rebuilt = rebuilt.replace(MASK_INLINE, mask, 1)
    state.total += n
    return rebuilt


def _report(left: int, right: int, sleft: int, sright: int) -> int:
    """Print balance summary; return 0 if balanced, 2 if not."""
    if left != right or sleft != sright:
        print('WARNING: unbalanced quotes — an odd count in a line means a '
              'quote was meant as nested/one-sided; fix manually.')
        return 2
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python robust_fix_quotes.py <file.md> [--dry-run]')
        sys.exit(1)

    filepath = sys.argv[1]
    dry_run = '--dry-run' in sys.argv[2:]
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    in_code = False
    state = QuoteState()
    out_lines = []
    for line in lines:
        if line.strip().startswith('```'):
            in_code = not in_code
            out_lines.append(line)
            continue
        if in_code:
            out_lines.append(line)
            continue
        out_lines.append(fix_line(line, state))

    new_content = '\n'.join(out_lines)
    left = new_content.count(LEFT)
    right = new_content.count(RIGHT)
    ascii_dq = new_content.count('"')
    sleft = new_content.count(SLEFT)
    sright = new_content.count(SRIGHT)

    if dry_run:
        changed = sum(1 for a, b in zip(content.split('\n'), out_lines) if a != b)
        print('DRY-RUN: %d line(s) would change. total %d pairs '
              '(curly-dq=%d/%d, curly-sq=%d/%d, ascii-dq=%d)'
              % (changed, state.total // 2, left, right, sleft, sright, ascii_dq))
        sys.exit(_report(left, right, sleft, sright))

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print('Rebuilt quotes: %d pairs (curly-dq=%d/%d, curly-sq=%d/%d, ascii-dq=%d)'
          % (state.total // 2, left, right, sleft, sright, ascii_dq))
    sys.exit(_report(left, right, sleft, sright))
