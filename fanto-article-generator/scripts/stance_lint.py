#!/usr/bin/env python3
"""Validate the v2 C4 stance gate.

This checker verifies the mechanical part of C4: required seed fields, an
explicit non-generic author position, and evidence that the position reached
the article.  It does not decide whether the opinion is intellectually good;
that remains an editorial judgment.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

FIELD_RE = re.compile(r"^\s*(?:\d+[.、)]\s*)?([^：:\r\n]+)[：:][ \t]*(.*)$", re.M)
FIRST_PERSON_RE = re.compile(r"(我|我们|我的|我们的|我不认同|我倾向于)")
GENERIC_STANCE_RE = re.compile(r"^(?:(?:我的判断是|我认为|我倾向于|在我看来|我的建议是)[，,: ]*)?(?:这件事|这个变化|该功能|它)?(?:确实|非常|很)?(?:重要|值得关注|值得重视|意义重大|影响深远|很有启发|值得思考)[。！!，, ]*$")
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?%?|\d+(?:倍|万|亿)")
REQUIRED_MODES = {"A-explainer", "B-analysis", "C-commentary", "D-learning", "D-practice"}
NO_STANCE_MODES = {"B-news", "C-faithful", "C-retelling", "R1", "R2", "R4"}
STANCE_BLOCK_OVERLAP = 0.10
STANCE_REVIEW_OVERLAP = 0.15
FORBIDDEN_AUTHOR_MARKER_MODES = {"B-news", "C-faithful", "C-retelling"}
AUTHOR_MARKER_RE = re.compile(r"(我的判断是|我认为|我倾向于|在我看来|我的建议是)")
STANCE_SURFACE_RE = re.compile(r"(判断|倾向|更愿意|优先|不建议|不要|应该|应当|保留|反对|同意|值得|更稳妥|先.{0,20}再)")
D_READING_EXPERIENCE_RE = re.compile(r"(我试了|我用过|我跑通|我测试|我发现|我体验|我实际|昨天|上周|前几天).{0,40}")


@dataclass
class Finding:
    level: str
    code: str
    message: str
    line: int | None = None


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_frontmatter_and_code(text: str) -> str:
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


def normalized(text: str) -> str:
    return re.sub(r"\s+", "", text).replace("“", "").replace("”", "").replace('"', "")


def meaningful_tokens(text: str) -> set[str]:
    tokens = set(re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,}", text))
    for phrase in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        tokens.update(phrase[i : i + 2] for i in range(len(phrase) - 1))
    return tokens


def overlap(a: str, b: str) -> float:
    left, right = meaningful_tokens(a), meaningful_tokens(b)
    return len(left & right) / max(1, min(len(left), len(right))) if left and right else 0.0


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def parse_seed(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for key, value in FIELD_RE.findall(text):
        key = key.strip()
        if "原文" in key and "结论" in key:
            values["source_conclusion"] = value.strip()
        elif "补充" in key or "反对" in key or "原创判断" in key or "意外" in key:
            values["author_position"] = value.strip()
        elif "目标读者" in key or "关系" in key or "so what" in key.lower():
            values["reader_relevance"] = value.strip()
        elif "落点" in key:
            values["placement"] = value.strip()
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate v2 C4 stance seed and article integration")
    parser.add_argument("article", type=Path)
    parser.add_argument("--stance", type=Path, default=None, help="Stance Seed markdown; required for modes with C4")
    parser.add_argument("--mode", required=True, choices=["A-explainer", "B-news", "B-analysis", "C-faithful", "C-retelling", "C-commentary", "D-reading", "D-learning", "D-practice", "R1", "R2", "R3", "R4"])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.article.exists() or (args.stance is not None and not args.stance.exists()):
        print("[ERROR] article or stance file does not exist", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    article_raw = read(args.article)
    article = strip_frontmatter_and_code(article_raw)
    required = args.mode in REQUIRED_MODES
    exempt = args.mode in NO_STANCE_MODES

    if args.mode in FORBIDDEN_AUTHOR_MARKER_MODES:
        for match in AUTHOR_MARKER_RE.finditer(article):
            findings.append(Finding("BLOCKER", "AUTHOR_STANCE_FORBIDDEN", f"{args.mode} contains an unrequested independent author stance", line_number(article_raw, match.start())))

    if args.mode == "D-reading" and args.stance is None:
        for match in D_READING_EXPERIENCE_RE.finditer(article):
            findings.append(Finding("BLOCKER", "D_READING_UNSUPPORTED_EXPERIENCE", "D-reading contains first-person or time-anchored experience without a supplied user observation", line_number(article_raw, match.start())))

    if args.stance is None:
        if required:
            findings.append(Finding("BLOCKER", "STANCE_MISSING", f"{args.mode} requires a C4 Stance Seed"))
        elif args.mode == "D-reading":
            findings.append(Finding("WARNING", "STANCE_CONDITIONAL", "D-reading has no supplied stance; verify that the article only uses user-provided observations"))
    else:
        seed_raw = read(args.stance)
        seed = parse_seed(seed_raw)
        fields = ["source_conclusion", "author_position", "reader_relevance", "placement"]
        for field in fields:
            if not seed.get(field):
                level = "BLOCKER" if required else "WARNING"
                findings.append(Finding(level, "STANCE_FIELD_MISSING", f"Stance Seed missing field: {field}"))

        position = seed.get("author_position", "")
        if position and not FIRST_PERSON_RE.search(position):
            findings.append(Finding("BLOCKER" if required else "WARNING", "STANCE_NOT_PERSONAL", "author position must show an explicit first-person stance"))
        if position and GENERIC_STANCE_RE.match(position.strip()):
            findings.append(Finding("WARNING", "STANCE_GENERIC", "author position is generic; add a concrete trade-off, reservation, disagreement, or surprise"))
        if position and NUMBER_RE.search(position) and not all(token in article for token in NUMBER_RE.findall(position)):
            findings.append(Finding("WARNING", "STANCE_NUMBER_REVIEW", "stance contains numeric detail not visibly present in the article; verify against claims ledger"))
        if position:
            stance_overlap = overlap(position, article)
            if stance_overlap < STANCE_BLOCK_OVERLAP:
                # A sharpened or synonym-rewritten stance may have near-zero
                # lexical overlap. Require visible first-person judgment
                # language, then defer semantic preservation to an editor.
                if FIRST_PERSON_RE.search(article) and STANCE_SURFACE_RE.search(article):
                    findings.append(Finding("WARNING", "STANCE_INTEGRATION_REVIEW", f"author position was substantially rephrased; manually confirm semantic preservation (token overlap={stance_overlap:.3f})"))
                else:
                    findings.append(Finding("BLOCKER" if required else "WARNING", "STANCE_NOT_IN_ARTICLE", f"author position does not visibly reach the article (token overlap={stance_overlap:.3f})"))
            elif stance_overlap < STANCE_REVIEW_OVERLAP:
                findings.append(Finding("WARNING", "STANCE_INTEGRATION_REVIEW", f"author position was substantially rephrased; manually confirm semantic preservation (token overlap={stance_overlap:.3f})"))

    if exempt and args.stance is not None:
        findings.append(Finding("WARNING", "STANCE_NOT_APPLICABLE", f"{args.mode} should not add independent author stance; confirm the supplied seed is only for internal reference"))

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
        "stance": str(args.stance) if args.stance else None,
        "mode": args.mode,
        "c4": "required" if required else "conditional" if args.mode == "D-reading" else "not-applicable" if exempt else "review",
        "blockers": blockers,
        "warnings": warnings,
        "findings": [asdict(f) for f in unique],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("## Stance lint v2")
        print(f"文章：{args.article}\n模式：{args.mode} | C4：{result['c4']} | BLOCKER：{blockers} | WARNING：{warnings}")
        for finding in unique:
            print(f"- [{finding.level}] {finding.code}: {finding.message}")
        print("结论：" + ("未通过" if blockers else ("通过但有警告" if warnings else "通过")))
    return 1 if blockers else 0


if __name__ == "__main__":
    import io
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in {"utf-8", "utf8"}:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if sys.stderr.encoding and sys.stderr.encoding.lower() not in {"utf-8", "utf8"}:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    sys.exit(main())
