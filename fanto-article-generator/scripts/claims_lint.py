#!/usr/bin/env python3
"""Validate an article against a v2 claims/quotes ledger.

This is a deterministic traceability check, not a source-quality judge.  It
catches missing ledger coverage, incomplete quote records, unverified
high-risk claims, and a few attribution hazards before an editor signs off.

Usage:
    python scripts/claims_lint.py article.md --ledger runlog/topic/claims.md
    python scripts/claims_lint.py article.md --ledger claims.md --high-risk
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

UNVERIFIED = {"", "未核验", "部分核验", "待核验"}
CLAIM_ID_RE = re.compile(r"^##[ \t]+(?:(?:Claim|Quote)[ \t]+)?([FfQq]-\d+)\b", re.M)
FIELD_RE = re.compile(r"^-[ \t]*([^：:\r\n]+)[：:][ \t]*(.*)$", re.M)
QUOTE_RE = re.compile(r'[“"]([^“”"\n]{2,240})[”"]')
QUOTE_ID_RE = re.compile(r"(?:Q|q)-\d+")
URL_RE = re.compile(r"https?://[^)\s>]+")
NUMBER_RE = re.compile(
    r"(?<![A-Za-z])(?:"
    r"\d{4}年\d{1,2}月\d{1,2}(?:日)?|"
    r"\d{4}[-/]\d{1,2}(?:[-/]\d{1,2})?|"
    r"\d+(?:\.\d+)?%?|\d+(?:倍|万|亿|万人|亿元|万元)"
    r")(?![A-Za-z])"
)


@dataclass
class Finding:
    level: str
    code: str
    message: str
    line: int | None = None


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_frontmatter_and_code(text: str) -> str:
    """Remove YAML frontmatter and fenced code from article-level checks."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + len("\n---") :]
    out: list[str] = []
    in_code = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            out.append(line)
    return "\n".join(out)


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def parse_entries(ledger: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    matches = list(CLAIM_ID_RE.finditer(ledger))
    entries: dict[str, dict[str, str]] = {}
    duplicates: list[str] = []
    for i, match in enumerate(matches):
        ident = match.group(1).upper()
        if ident in entries:
            duplicates.append(ident)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(ledger)
        block = ledger[match.end() : end]
        fields = {k.strip(): v.strip() for k, v in FIELD_RE.findall(block)}
        fields["_raw"] = block
        entries[ident] = fields
    return entries, duplicates


def normalized(value: str) -> str:
    return re.sub(r"\s+", "", value).replace("“", "").replace("”", "").replace('"', "")


def quote_is_covered(quote: str, entries: dict[str, dict[str, str]]) -> tuple[bool, str | None]:
    q = normalized(quote)
    if not q:
        return True, None
    for ident, entry in entries.items():
        if not ident.startswith("Q-"):
            continue
        # Prefer the recorded original/translation/body quote fields, while
        # retaining a tolerant substring match for edited Chinese punctuation.
        hay = normalized(" ".join(entry.values()))
        if q in hay or hay in q:
            return True, ident
    return False, None


def token_is_covered(token: str, entries: dict[str, dict[str, str]]) -> bool:
    return any(token in entry.get("_raw", "") for entry in entries.values())


def has_value(entry: dict[str, str], field: str) -> bool:
    value = entry.get(field, "").strip()
    return bool(value and value not in {"待补充", "暂无", "无", "N/A"})


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate v2 claims and quote coverage")
    parser.add_argument("article", type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--high-risk", action="store_true", help="Require verified status for time-sensitive claims")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.article.exists() or not args.ledger.exists():
        print("[ERROR] article or ledger file does not exist", file=sys.stderr)
        return 2

    article_raw = read(args.article)
    ledger_raw = read(args.ledger)
    article = strip_frontmatter_and_code(article_raw)
    entries, duplicates = parse_entries(ledger_raw)
    findings: list[Finding] = []

    if not entries:
        findings.append(Finding("BLOCKER", "LEDGER_EMPTY", "claims ledger contains no Claim/Quote entries"))
    for ident in duplicates:
        findings.append(Finding("BLOCKER", "DUPLICATE_ID", f"ledger contains duplicate entry id: {ident}"))

    # Every direct quote must be traceable to a Q entry.  Explicit inline IDs
    # are accepted and validated, but published prose need not expose them.
    for match in QUOTE_RE.finditer(article):
        quote = match.group(1).strip()
        if quote.startswith("http") or len(quote) < 4:
            continue
        covered, ident = quote_is_covered(quote, entries)
        if not covered:
            findings.append(Finding("BLOCKER", "QUOTE_UNTRACKED", f"direct quote has no matching Q-* ledger entry: {quote[:80]}", line_number(article_raw, match.start())))
        elif ident:
            q_entry = entries[ident]
            exact = q_entry.get("是否逐字对应", "")
            merged = q_entry.get("是否存在合并", "")
            if exact.startswith("否") or "合成" in q_entry.get("备注", ""):
                findings.append(Finding("BLOCKER", "QUOTE_SYNTHETIC", f"{ident} is marked non-verbatim but appears as a direct quote", line_number(article_raw, match.start())))
            if merged.startswith("是") and "编辑" not in q_entry.get("归属方式", ""):
                findings.append(Finding("BLOCKER", "QUOTE_MERGED_UNMARKED", f"{ident} combines source passages without an editorial marker", line_number(article_raw, match.start())))

    # If a document deliberately exposes a Q-* marker, make sure it exists.
    for marker in sorted({m.upper() for m in QUOTE_ID_RE.findall(article)}):
        if marker not in entries:
            findings.append(Finding("BLOCKER", "QUOTE_ID_UNKNOWN", f"article references {marker}, but the ledger has no such entry"))

    # Numeric/date coverage is a mechanical proxy for external-fact coverage.
    # Standard warns; High-risk blocks until the author records the source.
    for match in NUMBER_RE.finditer(article):
        token = match.group(0)
        if not token_is_covered(token, entries):
            level = "BLOCKER" if args.high_risk else "WARNING"
            findings.append(Finding(level, "NUMBER_UNTRACKED", f"numeric/date token is absent from ledger: {token}", line_number(article_raw, match.start())))

    # URLs in published prose should have a corresponding source record.
    for match in URL_RE.finditer(article):
        url = match.group(0).rstrip("。，；、")
        if url not in ledger_raw:
            level = "BLOCKER" if args.high_risk else "WARNING"
            findings.append(Finding(level, "URL_UNTRACKED", f"source URL is absent from ledger: {url[:120]}", line_number(article_raw, match.start())))

    required_claim_fields = ["文中主张", "主张类型", "来源", "来源定位", "核验状态", "可信度", "是否时间敏感", "允许的改写范围", "正文落点"]
    required_quote_fields = ["Speaker", "来源定位", "原文", "中文译文", "正文引用", "是否逐字对应", "是否存在删节", "是否存在合并", "归属方式"]
    for ident, entry in entries.items():
        fields = required_quote_fields if ident.startswith("Q-") else required_claim_fields if ident.startswith("F-") else []
        for field in fields:
            if not has_value(entry, field):
                level = "BLOCKER" if args.high_risk or ident.startswith("Q-") else "WARNING"
                findings.append(Finding(level, "LEDGER_FIELD_MISSING", f"{ident} missing field: {field}"))
        if ident.startswith("F-") and args.high_risk:
            sensitive = entry.get("是否时间敏感", "")
            status = entry.get("核验状态", "")
            claim_type = entry.get("主张类型", "")
            fact_like = any(label in claim_type for label in ("事实", "引语", "作者推断"))
            if fact_like and status in UNVERIFIED:
                findings.append(Finding("BLOCKER", "HIGH_RISK_UNVERIFIED", f"{ident} is a fact-like claim but not verified"))
            if "是" in sensitive and entry.get("来源定位", "").strip() in {"", "待补充", "暂无"}:
                findings.append(Finding("BLOCKER", "HIGH_RISK_NO_LOCATOR", f"{ident} is time-sensitive but has no source locator"))

    # A common attribution failure: source attribution and an unmarked first-
    # person judgement in one sentence.  This remains a warning for editors.
    for i, line in enumerate(article.splitlines(), 1):
        if re.search(r"(官方|原文|材料|报告|研究|发布方).*(我认为|我的判断|我倾向于)|(我认为|我的判断|我倾向于).*(官方|原文|材料|报告|研究|发布方)", line):
            findings.append(Finding("WARNING", "ATTRIBUTION_MIXED", "source attribution and author judgment appear in the same sentence; separate them", i))

    # De-duplicate equivalent findings while preserving order.
    seen: set[tuple[str, str, str, int | None]] = set()
    unique: list[Finding] = []
    for finding in findings:
        key = (finding.level, finding.code, finding.message, finding.line)
        if key not in seen:
            seen.add(key)
            unique.append(finding)

    blockers = sum(f.level == "BLOCKER" for f in unique)
    warnings = sum(f.level == "WARNING" for f in unique)
    result = {
        "article": str(args.article),
        "ledger": str(args.ledger),
        "workflow": "High-risk" if args.high_risk else "Standard",
        "entries": len(entries),
        "blockers": blockers,
        "warnings": warnings,
        "findings": [asdict(f) for f in unique],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("## Claims lint v2")
        print(f"文章：{args.article}")
        print(f"账本：{args.ledger}")
        print(f"条目：{len(entries)} | BLOCKER：{blockers} | WARNING：{warnings}")
        for finding in unique:
            loc = f"L{finding.line}: " if finding.line else ""
            print(f"- [{finding.level}] {finding.code} {loc}{finding.message}")
        print("结论：" + ("未通过" if blockers else ("通过但有警告" if warnings else "通过")))
    return 1 if blockers else 0


if __name__ == "__main__":
    import io
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in {"utf-8", "utf8"}:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if sys.stderr.encoding and sys.stderr.encoding.lower() not in {"utf-8", "utf8"}:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    sys.exit(main())
