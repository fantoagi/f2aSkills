#!/usr/bin/env python3
"""Check whether an article fulfils the v2 Editorial Brief and reader-value rubric.

The checker scores nine dimensions mechanically (0-2 each).  It is designed
to expose missing editorial inputs and obvious promise/ending gaps; it does not
replace an editor's judgment about originality or usefulness.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

PLACEHOLDER = re.compile(r"^(?:待补充|无|暂无|待确认|N/?A|\.{2,})$", re.I)
GENERIC_AUDIENCE = re.compile(r"AI\s*(爱好者|用户)|对\s*AI\s*感兴趣|所有人|泛用户|职场人$")
FIELD_RE = re.compile(r"^-[ \t]*([^\r\n：:]+)[：:][ \t]*(.*)$", re.M)
ACTION_RE = re.compile(r"(先|可以|应该|建议|检查|建立|记录|验证|试用|比较|复核|补充|观察|采取|下一步|不要|避免)")
CONCLUSION_RE = re.compile(r"(因此|所以|最后|结论|回到|对你来说|下一步|建议|如果你)")
TENSION_RE = re.compile(r"(为什么|却|反而|意外|反直觉|问题在于|原以为|没想到|直到|代价|瓶颈|落差|冲突|悬念|不是一回事|不等于|并不意味着|看似.{0,12}(实际|却)|之间存在|[？?])")
HOOK_TYPES = {"反常识", "反差", "场景", "金句", "数据", "悬念", "无"}
INFO_H_MODES = {"B-news", "C-faithful", "C-retelling"}
H_REQUIRED_MODES = {"A-explainer", "B-analysis", "C-commentary"}


@dataclass
class Finding:
    level: str
    code: str
    message: str


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


def fields(text: str) -> dict[str, str]:
    return {k.strip(): v.strip() for k, v in FIELD_RE.findall(text)}


def good(value: str | None) -> bool:
    return bool(value and value.strip() and not PLACEHOLDER.match(value.strip()))


def meaningful_tokens(text: str) -> set[str]:
    tokens = set(re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,}", text))
    # Chinese phrases are often rewritten, so include overlapping bigrams as a
    # tolerant mechanical signal rather than requiring exact thesis wording.
    for phrase in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        tokens.update(phrase[i : i + 2] for i in range(len(phrase) - 1))
    return tokens


def overlap_score(a: str, b: str) -> float:
    left = meaningful_tokens(a)
    right = meaningful_tokens(b)
    if not left or not right:
        return 0.0
    return len(left & right) / max(1, min(len(left), len(right)))


def article_parts(article: str) -> tuple[str, str, str, str]:
    content = strip_frontmatter_and_code(article)
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    headings = [re.sub(r"^#+\s*", "", line) for line in lines if line.startswith("#")]
    title = headings[0] if headings else ""
    body = [line for line in lines if not line.startswith("#") and not line.startswith(">")]
    first = body[0] if body else ""
    ending = " ".join(body[-5:]) if body else ""
    return title, first, ending, " ".join(lines[:8])


def score_brief(brief: dict[str, str], article: str, mode: str | None = None) -> tuple[int, list[Finding], dict[str, int]]:
    findings: list[Finding] = []
    dimensions: dict[str, int] = {}

    audience = brief.get("目标读者", "")
    if good(audience) and not GENERIC_AUDIENCE.search(audience) and len(audience) >= 6:
        dimensions["reader_specificity"] = 2
    else:
        dimensions["reader_specificity"] = 0
        findings.append(Finding("BLOCKER", "AUDIENCE_UNCLEAR", "目标读者必须具体到角色和场景，不能只写泛人群"))

    if good(brief.get("读者为什么现在需要这篇文章")):
        dimensions["problem_urgency"] = 2
    else:
        dimensions["problem_urgency"] = 0
        findings.append(Finding("BLOCKER", "WHY_NOW_MISSING", "缺少或未填写：为什么现在需要"))

    thesis = brief.get("本文核心命题", "")
    reader_judgment = brief.get("读者读完后应该形成的一个判断", "")
    title, first, ending, opening_surface = article_parts(article)
    if not good(thesis):
        dimensions["new_judgment"] = 0
        findings.append(Finding("BLOCKER", "THESIS_MISSING", "缺少或未填写：核心命题"))
    elif not good(reader_judgment):
        dimensions["new_judgment"] = 0
        findings.append(Finding("BLOCKER", "JUDGMENT_MISSING", "缺少或未填写：读者判断"))
    else:
        thesis_overlap = overlap_score(thesis, article)
        dimensions["new_judgment"] = 2 if thesis_overlap >= 0.2 else 1
        if thesis_overlap < 0.2:
            findings.append(Finding("WARNING", "THESIS_NOT_VISIBLE", "正文没有明显回应 Brief 的核心命题，需要人工检查标题、开头和结尾"))

    action = brief.get("读者读完后可以采取的一个行动", "")
    if good(action):
        dimensions["actionability"] = 2 if ACTION_RE.search(article) else 1
        if dimensions["actionability"] == 1:
            findings.append(Finding("WARNING", "ACTION_NOT_VISIBLE", "Brief 有行动，但正文没有明显的下一步或操作表达"))
    else:
        dimensions["actionability"] = 0
        findings.append(Finding("BLOCKER", "ACTION_MISSING", "缺少或未填写：读者行动"))

    evidence = brief.get("支撑命题的关键证据", "")
    if good(evidence):
        dimensions["evidence_density"] = 2
    else:
        dimensions["evidence_density"] = 0
        findings.append(Finding("WARNING", "EVIDENCE_THIN", "Brief 没有提供关键证据，Standard/High-risk 需要补充"))

    limitation = brief.get("主要反方观点或限制", "")
    if good(limitation):
        dimensions["boundary_clarity"] = 2
    else:
        dimensions["boundary_clarity"] = 0
        findings.append(Finding("WARNING", "LIMITATION_MISSING", "没有记录主要限制或反方观点"))

    author_judgment = brief.get("作者自己的判断", "")
    if good(author_judgment) and ("作者" in article or ACTION_RE.search(article) or "判断" in article):
        dimensions["originality"] = 2
    elif good(author_judgment):
        dimensions["originality"] = 1
        findings.append(Finding("WARNING", "AUTHOR_JUDGMENT_THIN", "Brief 有作者判断，但正文中的独立判断或信息增量不明显"))
    else:
        dimensions["originality"] = 1
        findings.append(Finding("WARNING", "AUTHOR_JUDGMENT_MISSING", "没有记录作者判断；转述类文章需确认这是有意保持中性"))

    scan_signals = sum(bool(part) for part in (title, first, ending))
    if scan_signals == 3 and (overlap_score(thesis, title + " " + first + " " + ending) >= 0.15 or ACTION_RE.search(ending)):
        dimensions["scan_value"] = 2
    elif scan_signals >= 2:
        dimensions["scan_value"] = 1
        findings.append(Finding("WARNING", "SCAN_VALUE_WEAK", "标题、开头或结尾对读者承诺的回应不够明显"))
    else:
        dimensions["scan_value"] = 0
        findings.append(Finding("WARNING", "SCAN_VALUE_MISSING", "文章缺少可供扫读的标题、开头或结尾信息"))

    # H: curiosity/tension is a separate check from promise clarity. It must
    # be grounded in the brief and visible in the article; a generic word such
    # as “但” alone is not enough to earn the point.
    tension = brief.get("文章核心认知张力 / 开篇问题", "")
    hook_type = brief.get("传播钩子类型", "")
    info_policy = mode in INFO_H_MODES and ("无新增悬念" in tension or "信息型标题" in tension or hook_type.strip() == "无")
    if not good(hook_type):
        findings.append(Finding("WARNING", "HOOK_TYPE_MISSING", "Brief 缺少传播钩子类型；没有可靠 H 时应明确填写“无”并采用信息型标题"))
    elif hook_type.strip() not in HOOK_TYPES and not any(item in hook_type for item in HOOK_TYPES - {"无"}):
        findings.append(Finding("WARNING", "HOOK_TYPE_UNKNOWN", f"传播钩子类型不在约定枚举内：{hook_type}"))

    if good(tension):
        visible_surface = title + " " + first + " " + opening_surface + " " + ending
        tension_overlap = overlap_score(tension, visible_surface)
        explicit_question = "？" in visible_surface or "?" in visible_surface
        signal = TENSION_RE.search(visible_surface)
        if info_policy or (signal and (explicit_question or tension_overlap >= 0.15)):
            dimensions["curiosity_tension"] = 2
        elif tension_overlap >= 0.15 or signal:
            dimensions["curiosity_tension"] = 1
            findings.append(Finding("WARNING", "TENSION_WEAK", "文章有认知张力线索，但未形成清晰的继续阅读理由；需要人工检查开头和标题"))
        else:
            dimensions["curiosity_tension"] = 0
            findings.append(Finding("WARNING", "TENSION_NOT_VISIBLE", "Brief 已记录认知张力，但标题、开头、正文前段或结尾没有明显呈现"))
    elif info_policy:
        dimensions["curiosity_tension"] = 2
    else:
        dimensions["curiosity_tension"] = 0
        findings.append(Finding("WARNING", "TENSION_MISSING", "没有记录文章核心认知张力/开篇问题；若采用信息型文章，应明确说明原因"))

    # The ending must return to the reader's problem, not only add a generic
    # uplift sentence.  Keep this a warning because the signal is heuristic.
    if ending and not (ACTION_RE.search(ending) or CONCLUSION_RE.search(ending)):
        findings.append(Finding("WARNING", "ENDING_NOT_READER_FOCUSED", "结尾没有明显回到读者问题、判断或下一步"))

    score = sum(dimensions.values())
    return min(score, 18), findings, dimensions


def main() -> int:
    parser = argparse.ArgumentParser(description="Check v2 reader value")
    parser.add_argument("article", type=Path)
    parser.add_argument("--brief", required=True, type=Path)
    parser.add_argument("--workflow", choices=["Lite", "Standard", "High-risk"], default="Standard")
    parser.add_argument("--mode", choices=["A-explainer", "B-news", "B-analysis", "C-faithful", "C-retelling", "C-commentary", "D-reading", "D-learning", "D-practice", "R1", "R2", "R3", "R4"], default=None, help="v2 子模式；用于信息型 H 豁免和审计记录")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.article.exists() or not args.brief.exists():
        print("[ERROR] article or brief file does not exist", file=sys.stderr)
        return 2

    article = read(args.article)
    brief = fields(read(args.brief))
    score, findings, dimensions = score_brief(brief, article, args.mode)
    thresholds = {"Lite": 10, "Standard": 13, "High-risk": 15}
    threshold = thresholds[args.workflow]
    if score < threshold:
        findings.append(Finding("BLOCKER" if args.workflow != "Lite" else "WARNING", "SCORE_LOW", f"reader-value score {score}/18 is below {args.workflow} threshold {threshold}/18"))

    required_dimensions = {"reader_specificity", "new_judgment", "actionability", "evidence_density"}
    # H is a hard G4 requirement for the public-facing modes that promise an
    # angle, interpretation, or decision tension. Omitting --mode must not be
    # a bypass, so Standard conservatively treats an unspecified mode as H-required.
    if args.workflow == "Standard" and (args.mode is None or args.mode in H_REQUIRED_MODES):
        required_dimensions.add("curiosity_tension")
    if args.workflow == "High-risk":
        zero_dimensions = [key for key, value in dimensions.items() if value == 0]
    else:
        zero_dimensions = [key for key in required_dimensions if dimensions.get(key) == 0]
    for key in zero_dimensions:
        # Avoid duplicating the explicit missing-field blocker, but make the
        # rubric rule visible in machine output for downstream audit reports.
        if not any(f.code == "RUBRIC_ZERO_DIMENSION" and key in f.message for f in findings):
            findings.append(Finding("BLOCKER" if args.workflow != "Lite" else "WARNING", "RUBRIC_ZERO_DIMENSION", f"rubric dimension is 0: {key}"))

    blockers = sum(x.level == "BLOCKER" for x in findings)
    warnings = sum(x.level == "WARNING" for x in findings)
    result = {
        "article": str(args.article),
        "brief": str(args.brief),
        "workflow": args.workflow,
        "mode": args.mode,
        "h_policy": "required" if args.mode is None or args.mode in H_REQUIRED_MODES else "information/source-hook" if args.mode in INFO_H_MODES else "review",
        "score": score,
        "threshold": threshold,
        "dimensions": dimensions,
        "blockers": blockers,
        "warnings": warnings,
        "findings": [asdict(x) for x in findings],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("## Reader value check v2")
        print(f"文章：{args.article}")
        print(f"工作流：{args.workflow} | 模式：{args.mode or '未指定'} | 得分：{score}/18 | 门槛：{threshold}/18")
        print("维度：" + "，".join(f"{key}={value}" for key, value in dimensions.items()))
        for finding in findings:
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
