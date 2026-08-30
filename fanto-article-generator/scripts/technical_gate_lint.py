#!/usr/bin/env python3
"""Mechanical preflight for the v2 Editor Technical Gate.

The script verifies that the human/editorial gate was recorded and catches
obvious rendering or logic-risk signals. It cannot determine product behavior
or resolve pronouns by itself; those remain explicit human checks.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

FIELD_RE = re.compile(r"^\s*(?:-[ \t]*|[①②③④⑤⑥⑦]\s*)?([^：:\r\n]+)[：:][ \t]*(.*)$", re.M)
REQUIRED_FIELDS = ["指代与逻辑", "技术机制", "渲染等价性", "概念与术语", "品牌与大小写", "正文口语词", "聚合结果"]
BLOCKING_VALUE_RE = re.compile(r"(BLOCKER|未通过|待修|未核验|❌)", re.I)
LATEX_RE = re.compile(r"(?<!\\)\$\$?[^\n$]+\$\$?|\\(?:sigma|alpha|beta|gamma|frac|text|mathrm)\b")
HTML_RE = re.compile(r"<(?:div|span|iframe|math|script|style|br\s*/?)(?:\s|>|/)", re.I)
PRONOUN_RISK_RE = re.compile(r"(^|[。！？；]\s*)(它|这|那|这些|这种|该对象|该机制)(?:会|将|可以|负责|用于|先|再|根据)")
LOGIC_RISK_RE = re.compile(r"(变回|恢复成|重新回到|从[^。！？\n]{1,30}变回)")
ABSOLUTE_MECHANISM_RE = re.compile(r"(完全自动|自动完成所有|一定会|保证不会|绝对不会|不能改文件)")


@dataclass
class Finding:
    level: str
    code: str
    message: str
    line: int | None = None


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate v2 Editor Technical Gate audit")
    parser.add_argument("article", type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.article.exists() or not args.audit.exists():
        print("[ERROR] article or audit file does not exist", file=sys.stderr)
        return 2

    article = read(args.article)
    audit = read(args.audit)
    audit_fields = {k.strip(): v.strip() for k, v in FIELD_RE.findall(audit)}
    findings: list[Finding] = []

    for field in REQUIRED_FIELDS:
        value = audit_fields.get(field, "")
        if not value:
            findings.append(Finding("BLOCKER", "TECH_AUDIT_FIELD_MISSING", f"stage-06 audit missing technical-gate field: {field}"))
        elif BLOCKING_VALUE_RE.search(value):
            findings.append(Finding("BLOCKER", "TECH_AUDIT_UNRESOLVED", f"technical-gate field is unresolved: {field}={value}"))

    if article.count("```") % 2:
        findings.append(Finding("BLOCKER", "CODE_FENCE_UNPAIRED", "Markdown code fence is not paired"))
    for pattern, code, message in [
        (LATEX_RE, "RENDER_LATEX", "LaTeX may not render in the target publishing environment"),
        (HTML_RE, "RENDER_HTML", "raw HTML/MathML may not render in the target publishing environment"),
    ]:
        for match in pattern.finditer(article):
            findings.append(Finding("BLOCKER", code, message, line_number(article, match.start())))

    for pattern, code, message in [
        (PRONOUN_RISK_RE, "REFERENCE_REVIEW", "pronoun/reference may be ambiguous; verify a unique antecedent"),
        (LOGIC_RISK_RE, "TRANSITION_LOGIC_REVIEW", "'变回/恢复成' implies a prior state; verify the starting-state logic"),
        (ABSOLUTE_MECHANISM_RE, "MECHANISM_ABSOLUTE_REVIEW", "absolute product/mechanism wording requires source verification"),
    ]:
        for match in pattern.finditer(article):
            findings.append(Finding("WARNING", code, message, line_number(article, match.start())))

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
        "article": str(args.article), "audit": str(args.audit),
        "blockers": blockers, "warnings": warnings,
        "findings": [asdict(f) for f in unique],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("## Editor Technical Gate lint v2")
        print(f"文章：{args.article}\n审计：{args.audit} | BLOCKER：{blockers} | WARNING：{warnings}")
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
