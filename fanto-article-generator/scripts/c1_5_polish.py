# -*- coding: utf-8 -*-
"""
C1.5 母语化深度润色 — 4 人格对抗审校的可执行工具。

v2 变更（vs v1 5-rule subagent）:
  不再按"错误类别"拆分（译制腔/句法/动宾/长句/体量感），改用 4 个立场不同的审校人格:
    A. 投资人视角 — 商业判断、竞争定位、数据上下文
    B. 工程师视角 — 技术准确性、架构逻辑、Benchmark 描述
    C. 媒体编辑视角 — 开篇钩子、信息密度、节奏、动词力度
    D. 双语译者视角 — 语义漂移、翻译腔、术语一致性、隐喻对等

  四个人格对同一段文字会发现完全不同类型的问题 —— 这是真正的视角多样性。

用法（典型流程）:

  # 第 1 步：生成 4 个 persona subagent prompts
  python scripts/c1_5_polish.py <article.md> --gen-prompts --out-dir c1_5_run/

  # 第 2 步：main agent 用 Agent 工具跑 4 个 subagent，把每个的 JSON 输出存到
  #          c1_5_run/findings/persona_A.json ... persona_D.json

  # 第 3 步：聚合 + 应用修改 + 输出
  python scripts/c1_5_polish.py <article.md> --apply --findings-dir c1_5_run/findings/

依赖:
  - Python 3.8+ stdlib only
  - polish-prompt.md 必须存在于 references/
  - c1_5_subagent_schema.json 必须存在于 references/
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ===== 路径常量 =====
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
REFERENCES_DIR = SKILL_ROOT / "references"
POLISH_PROMPT_PATH = REFERENCES_DIR / "polish-prompt.md"
SCHEMA_PATH = REFERENCES_DIR / "c1_5_subagent_schema.json"

# ===== 4 人格元数据（与 polish-prompt.md 对齐）=====
PERSONAS = [
    ("A", "投资人视角",   "### 人格 A：💰 投资人视角"),
    ("B", "工程师视角",   "### 人格 B：🔧 工程师视角"),
    ("C", "媒体编辑视角", "### 人格 C：✍️ 媒体编辑视角"),
    ("D", "双语译者视角", "### 人格 D：🌐 双语译者视角"),
]

# ===== 不可改清单（与 polish-prompt.md "前置约束" 段对齐）=====
IMMUTABLE_LIST = """
1. 事实断言不可改（数字、百分比、时间、金额、产品名、公司名、人名）
2. 术语译法不可改（已确定的术语映射清单）
3. 因果逻辑不可改
4. 代码块不可改（fenced code block / inline code / CLI 命令原样保留）
5. 点名批评/道德判断不可弱化或删除
6. 引语归属不可混淆（多个引语紧密排列时逐句核对归属）
"""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_markdown_fences(text: str) -> str:
    """Strip markdown code fences from LLM output before JSON parsing."""
    stripped = text.strip()

    fence_pattern = re.compile(
        r'^```(?:json)?\s*\n?(.*?)\n?\s*```$',
        re.DOTALL
    )
    m = fence_pattern.match(stripped)
    if m:
        return m.group(1).strip()

    if '```' in stripped:
        lines = stripped.split('\n')
        first_fence = -1
        last_fence = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                if first_fence == -1:
                    first_fence = i
                last_fence = i
        if first_fence >= 0 and last_fence > first_fence:
            inner = '\n'.join(lines[first_fence + 1:last_fence])
            return inner.strip()

    return stripped


def extract_persona_section(polish_md: str, marker: str) -> str:
    """从 polish-prompt.md 提取某个人格的完整审校标准。

    范围：从 marker 行起，到下一个 '### 人格' 或 '## 主 Agent 聚合规则' 或文件结尾为止。
    """
    start = polish_md.find(marker)
    if start < 0:
        return f"[ERROR] 找不到人格段 {marker} in polish-prompt.md"

    # 找结束位置：下一个 ### 人格 / ## 主 Agent / ## Subagent
    end = len(polish_md)
    stop_markers = [
        "\n### 人格 ",
        "\n## 主 Agent 聚合规则",
        "\n## Subagent 调用契约",
    ]
    for stop in stop_markers:
        idx = polish_md.find(stop, start + len(marker))
        if idx > 0 and idx < end:
            end = idx

    return polish_md[start:end].strip()


def build_persona_prompt(
    persona_id: str,
    persona_name: str,
    persona_section: str,
    article_text: str,
    schema_json_text: str,
    original_en_text: str = "",
    target_media: str = "WeChat",
) -> str:
    """构造 1 个 persona subagent 的完整审校 prompt。"""
    en_context = ""
    if original_en_text:
        en_context = f"""
## 【英文原文（对照参考）】

```text
{original_en_text[:8000]}
```
"""
        if len(original_en_text) > 8000:
            en_context += f"\n> ⚠️ 原文较长（{len(original_en_text)} chars），以上为前 8000 字符。全文已由主 agent 持有，如需要可请求补充段落。"

    return f"""# C1.5 Persona Subagent — {persona_id}：{persona_name}

## 角色与边界

你是 fanto-article-generator 的审校人格 **{persona_id}：{persona_name}**。
**你的任务：以{persona_name}的立场审校全文，只报告本视角关注的问题，不越界评估其他维度。**

## 【{persona_name} 审校标准】（从 references/polish-prompt.md 摘出）

{persona_section}

## 【不可改清单】（必须保留，不允许修改）

{IMMUTABLE_LIST}

## 【目标媒体】

{target_media}
{en_context}
## 【待审校文章】

```markdown
{article_text}
```

## 【输出要求】

请按 JSON schema 输出 findings。**0 触发也要输出 trigger_count=0 + no_finding_reason**。

JSON schema 路径：`references/c1_5_subagent_schema.json`

Schema 全文：

```json
{schema_json_text}
```

**输出格式**：你的最终回复必须是**一个完整的 JSON 对象**，形如：

```json
{{
  "persona_id": "{persona_id}",
  "persona_name": "{persona_name}",
  "trigger_count": <整数>,
  "findings": [
    {{
      "finding_id": 1,
      "original_sentence": "必须是【待审校文章】中逐字复制的精确子串（从原文复制粘贴，禁止添加位置前缀如'第3段：'、禁止用引号/方括号包裹、禁止改写压缩）。脚本将用它做全文精确匹配以自动应用修改，带前缀或改写的摘录会导致 NOT_FOUND 无法自动应用",
      "english_reference": "对应的英文原文（人格 D 必填）",
      "issue_category": "issue_category 枚举值之一",
      "issue": "一句话说明问题（不超过 40 字）",
      "modified_sentence": "建议改句 / DELETE / NEEDS_CONTEXT: ...",
      "confidence": "high | medium | low"
    }}
  ],
  "no_finding_reason": "（trigger_count=0 时必填）扫描结果简述",
  "severity_summary": {{
    "hard_error": <整数>,
    "soft_error": <整数>,
    "polish": <整数>
  }}
}}
```

**完成后只输出这一个 JSON 对象**。不要添加解释、前言、结束语。
"""


def cmd_gen_prompts(
    article_path: Path,
    out_dir: Path,
    original_en: str = "",
    target_media: str = "WeChat",
) -> int:
    """生成 4 个 persona subagent prompt 文件 + schema 副本。"""
    article_text = read_text(article_path)
    polish_md = read_text(POLISH_PROMPT_PATH)
    schema_json = read_text(SCHEMA_PATH)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "article_text.md").write_text(article_text, encoding="utf-8")
    (out_dir / "schema.json").write_text(schema_json, encoding="utf-8")

    print(f"=== C1.5 四人格 prompt 生成 ===")
    print(f"  article: {article_path} ({len(article_text)} chars)")
    print(f"  target_media: {target_media}")
    if original_en:
        print(f"  original_en: {len(original_en)} chars")
    print(f"  out_dir: {out_dir}")
    print()

    for persona_id, persona_name, marker in PERSONAS:
        section = extract_persona_section(polish_md, marker)
        prompt = build_persona_prompt(
            persona_id, persona_name, section, article_text, schema_json,
            original_en_text=original_en, target_media=target_media,
        )
        out_path = out_dir / f"persona_{persona_id}.md"
        out_path.write_text(prompt, encoding="utf-8")
        print(f"  [{persona_id}/D] persona_{persona_id}.md: {len(prompt)} chars")

    # 写 runner hint
    runner_hint = f"""# C1.5 四人格 Runner Hint

已生成 4 个 persona subagent prompt 文件。接下来的执行流程：

## 步骤 1：主 agent 用 Agent 工具启 4 个 subagent

对每个 `persona_*.md` 文件，用 Agent 工具（agentType: `general-purpose`）调用，
prompt 内容 = 该文件全文。
每个 subagent 物理隔离：独立 context，看不到主对话历史和前 subagent 的输出。

返回 4 份 JSON findings，每份对应一个 persona。

## 步骤 2：保存 4 份 JSON 到 findings/

每份 JSON 命名为 `findings/persona_A.json` ... `persona_D.json`，
内容是 subagent 输出的 JSON 对象。

## 步骤 3：调用本脚本的 apply 模式

```bash
python scripts/c1_5_polish.py {article_path} \\
  --apply --findings-dir {out_dir}/findings/ \\
  --out-dir {out_dir}/
```

输出：
- `c1_5_diagnosis.md`：4 份 findings 聚合的 Diagnosis 报告
- `c1_5_post_polish.md`：应用所有修改后的润色后全文
- `c1_5_change_table.md`：原句 vs 改句对照表
"""
    (out_dir / "RUNNER_HINT.md").write_text(runner_hint, encoding="utf-8")

    print()
    print(f"  RUNNER_HINT.md: 已写入执行指南")
    print()
    print(f"=== 接下来 ===")
    print(f"  1. 用 Agent 工具跑 4 次（每次 prompt = persona_*.md 全文）")
    print(f"  2. 4 份 JSON 保存到 {out_dir}/findings/persona_A.json ... persona_D.json")
    print(f"  3. 跑 --apply 模式聚合 + 应用")
    return 0


# --- Schema validation ---

REQUIRED_TOP_FIELDS = {"persona_id", "persona_name", "trigger_count", "findings"}
REQUIRED_FINDING_FIELDS = {"finding_id", "issue_category", "issue", "modified_sentence", "confidence"}
VALID_CONFIDENCES = {"high", "medium", "low"}
VALID_PERSONA_IDS = {"A", "B", "C", "D"}


def _validate_finding_schema(data: dict, path: str) -> list:
    """Validate a single finding JSON against the expected schema.

    Returns a list of warning strings. Empty list = all checks passed.
    """
    warnings = []

    missing_top = REQUIRED_TOP_FIELDS - set(data.keys())
    if missing_top:
        warnings.append(f"{path}: 缺必填字段 {missing_top}")

    persona_id = data.get("persona_id", "")
    if persona_id not in VALID_PERSONA_IDS:
        warnings.append(f"{path}: persona_id '{persona_id}' 不在 {VALID_PERSONA_IDS}")

    tc = data.get("trigger_count")
    if tc is not None and not isinstance(tc, int):
        warnings.append(f"{path}: trigger_count={tc} 不是整数")

    findings_arr = data.get("findings")
    if findings_arr is not None and not isinstance(findings_arr, list):
        warnings.append(f"{path}: findings 不是数组")
    elif isinstance(findings_arr, list):
        if isinstance(tc, int) and tc != len(findings_arr):
            warnings.append(
                f"{path}: trigger_count={tc} ≠ len(findings)={len(findings_arr)}"
            )
        for i, item in enumerate(findings_arr):
            if not isinstance(item, dict):
                warnings.append(f"{path}: findings[{i}] 不是对象")
                continue
            missing_item = REQUIRED_FINDING_FIELDS - set(item.keys())
            if missing_item:
                warnings.append(f"{path}: findings[{i}] 缺字段 {missing_item}")
            conf = item.get("confidence", "")
            if conf and conf not in VALID_CONFIDENCES:
                warnings.append(
                    f"{path}: findings[{i}].confidence='{conf}' 不在 {VALID_CONFIDENCES}"
                )

    if data.get("trigger_count") == 0 and not data.get("no_finding_reason"):
        warnings.append(f"{path}: trigger_count=0 但缺 no_finding_reason")

    return warnings


def load_findings(findings_dir: Path) -> tuple:
    """加载 4 份 persona findings JSON，校验 schema。

    返回: (valid_findings, validation_warnings)
    """
    findings = []
    validation_warnings = []

    for persona_id in ["A", "B", "C", "D"]:
        path = findings_dir / f"persona_{persona_id}.json"
        if not path.exists():
            validation_warnings.append(f"缺失: {path}")
            print(f"  [!] 缺 {path}", file=sys.stderr)
            continue
        try:
            raw = read_text(path)
            cleaned = _strip_markdown_fences(raw)
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            validation_warnings.append(f"{path}: JSON 解析失败: {e}")
            print(f"  [!] {path} JSON 解析失败: {e}", file=sys.stderr)
            continue

        schema_warnings = _validate_finding_schema(data, str(path))
        validation_warnings.extend(schema_warnings)
        for w in schema_warnings:
            print(f"  [WARN] {w}", file=sys.stderr)

        findings.append(data)

    return findings, validation_warnings


def _count_non_overlapping(text: str, sub: str) -> int:
    """Count non-overlapping occurrences of sub in text."""
    if not sub:
        return 0
    count = 0
    start = 0
    while True:
        idx = text.find(sub, start)
        if idx == -1:
            break
        count += 1
        start = idx + len(sub)
    return count


def apply_findings(article_text: str, findings: list) -> tuple:
    """聚合 4 份 persona findings，按 A→B→C→D 顺序应用修改。

    返回: (post_polish_text, change_table_rows, warnings)
    """
    # 按 persona_id 顺序 A→B→C→D
    id_order = {"A": 0, "B": 1, "C": 2, "D": 3}
    sorted_findings = sorted(
        findings,
        key=lambda f: id_order.get(f.get("persona_id", "Z"), 99),
    )

    text = article_text
    change_table = []  # (原句, 改句, persona, issue_category, conf)
    warnings = []

    for finding_block in sorted_findings:
        persona_id = finding_block.get("persona_id", "?")
        persona_name = finding_block.get("persona_name", "?")
        block_changes = []
        for f in finding_block.get("findings", []):
            orig = f.get("original_sentence", "")
            modified = f.get("modified_sentence", "")
            category = f.get("issue_category", "?")
            conf = f.get("confidence", "?")

            if not orig:
                continue

            # Handle special modified values
            if modified == "DELETE":
                if orig in text:
                    text = text.replace(orig, "", 1)
                    block_changes.append((orig, "[已删除]", persona_id, category, conf))
                else:
                    block_changes.append((orig, "[未找到，无法删除]", persona_id, category, f"{conf} (NOT_FOUND)"))
                continue

            if modified and modified.startswith("NEEDS_CONTEXT:"):
                block_changes.append((orig, f"[需补充: {modified[14:]}]", persona_id, category, f"{conf} (NEEDS_CONTEXT)"))
                continue

            if not modified:
                continue

            count = _count_non_overlapping(text, orig)

            if count == 0:
                tag = f"{conf} (NOT_FOUND)"
                block_changes.append((orig, "[未在文中找到，未应用]", persona_id, category, tag))
                short = orig[:50] + "..." if len(orig) > 50 else orig
                warnings.append(f"[{persona_id}/{category}] 未找到匹配: '{short}'")

            elif count == 1:
                text = text.replace(orig, modified, 1)
                block_changes.append((orig, modified, persona_id, category, conf))

            else:
                first_idx = text.find(orig)
                ctx_start = max(0, first_idx - 30)
                context_before = text[ctx_start:first_idx]
                context_key = context_before + orig
                context_count = _count_non_overlapping(text, context_key)

                if context_count == 1:
                    replace_start = ctx_start + len(context_before)
                    text = text[:replace_start] + modified + text[replace_start + len(orig):]
                    tag = f"{conf} (context-resolved, {count} bare matches)"
                    block_changes.append((orig, modified, persona_id, category, tag))
                else:
                    tag = f"{conf} (AMBIGUOUS×{count})"
                    block_changes.append((orig, f"[{count}处匹配，未应用]", persona_id, category, tag))
                    short = orig[:50] + "..." if len(orig) > 50 else orig
                    warnings.append(
                        f"[{persona_id}/{category}] 歧义: '{short}' 在文中出现 {count} 次"
                    )

        change_table.extend(block_changes)

    return text, change_table, warnings


def cmd_apply(article_path: Path, findings_dir: Path, out_dir: Path, dry_run: bool = False) -> int:
    article_text = read_text(article_path)
    findings, validation_warnings = load_findings(findings_dir)

    if len(findings) < 4:
        print(f"  [!] 只找到 {len(findings)}/4 份 findings，部分 persona 缺失", file=sys.stderr)

    if validation_warnings:
        print(f"\n  === Schema 校验告警 ({len(validation_warnings)} 条) ===")
        for w in validation_warnings:
            print(f"  [WARN] {w}")
        print()

    out_dir.mkdir(parents=True, exist_ok=True)

    post_polish, change_table, apply_warnings = apply_findings(article_text, findings)

    if apply_warnings:
        print(f"\n  === 应用告警 ({len(apply_warnings)} 条) ===")
        for w in apply_warnings:
            print(f"  [WARN] {w}")
        print()

    if dry_run:
        total_triggers = sum(f.get("trigger_count", 0) for f in findings)
        print(f"=== DRY RUN 模式（未写入文件） ===")
        print(f"  总触发: {total_triggers} 处")
        applied = sum(1 for c in change_table if "未应用" not in str(c[1]) and "未找到" not in str(c[1]))
        print(f"  可应用: {applied} 处")
        print(f"  未匹配/歧义: {len(change_table) - applied} 处")
        print(f"  Schema 告警: {len(validation_warnings)} 条")
        return 0

    # 写润色后全文
    (out_dir / "c1_5_post_polish.md").write_text(post_polish, encoding="utf-8")

    # 写变更对照表
    change_table_md = "# C1.5 变更对照表\n\n"
    total_triggers = sum(f.get("trigger_count", 0) for f in findings)
    change_table_md += f"共 {len(change_table)} 处修改（trigger_count 总计：{total_triggers}）\n\n"
    change_table_md += "| # | 原句 | 改句 | Persona | 问题类别 | 置信度 |\n"
    change_table_md += "|---|------|------|---------|---------|--------|\n"
    for i, (orig, modified, persona, category, conf) in enumerate(change_table, start=1):
        orig_short = orig[:60] + "..." if len(orig) > 60 else orig
        mod_short = modified[:60] + "..." if len(modified) > 60 else modified
        orig_short = orig_short.replace("|", "\\|")
        mod_short = mod_short.replace("|", "\\|")
        change_table_md += f"| {i} | {orig_short} | {mod_short} | {persona} | {category} | {conf} |\n"
    (out_dir / "c1_5_change_table.md").write_text(change_table_md, encoding="utf-8")

    # 写 Diagnosis
    diagnosis_md = "# C1.5 四人格审校报告\n\n"
    diagnosis_md += f"源文件：`{article_path}` ({len(article_text)} chars)\n"
    diagnosis_md += f"输出目录：`{out_dir}`\n\n"

    if validation_warnings:
        diagnosis_md += "## Schema 校验告警\n\n"
        for w in validation_warnings:
            diagnosis_md += f"- ⚠ {w}\n"
        diagnosis_md += "\n"

    if apply_warnings:
        diagnosis_md += "## 应用告警（未应用的修改）\n\n"
        for w in apply_warnings:
            diagnosis_md += f"- ⚠ {w}\n"
        diagnosis_md += "\n"

    diagnosis_md += "## 4 Persona Findings 汇总\n\n"
    total_triggers = 0
    total_hard = 0
    total_soft = 0
    total_polish = 0
    for f_item in findings:
        persona_id = f_item.get("persona_id", "?")
        persona_name = f_item.get("persona_name", "?")
        trigger_count = f_item.get("trigger_count", 0)
        total_triggers += trigger_count
        sev = f_item.get("severity_summary", {})
        total_hard += sev.get("hard_error", 0)
        total_soft += sev.get("soft_error", 0)
        total_polish += sev.get("polish", 0)

        diagnosis_md += f"### {persona_id}：{persona_name}（触发 {trigger_count} 处）\n\n"
        if sev:
            diagnosis_md += f"  - 硬错 {sev.get('hard_error', 0)} / 软错 {sev.get('soft_error', 0)} / 润色 {sev.get('polish', 0)}\n\n"
        findings_list = f_item.get("findings", [])
        if not findings_list:
            diagnosis_md += f"  - {f_item.get('no_finding_reason', '（无 findings）')}\n\n"
        else:
            for item in findings_list:
                orig = item.get("original_sentence", "?")[:50]
                category = item.get("issue_category", "?")
                issue = item.get("issue", "?")
                conf = item.get("confidence", "?")
                diagnosis_md += f"  - **{category}**（{conf}）：{issue} → 定位: `{orig}...`\n"
            diagnosis_md += "\n"

    diagnosis_md += f"\n**总触发：{total_triggers} 处**（硬错 {total_hard} / 软错 {total_soft} / 润色 {total_polish}）\n"
    (out_dir / "c1_5_diagnosis.md").write_text(diagnosis_md, encoding="utf-8")

    applied = sum(1 for c in change_table if "未应用" not in str(c[1]) and "未找到" not in str(c[1]))
    print(f"=== C1.5 apply 完成 ===")
    print(f"  总触发: {total_triggers} 处（硬错 {total_hard} / 软错 {total_soft} / 润色 {total_polish}）")
    print(f"  实际应用: {applied} 处")
    print(f"  未匹配/歧义: {len(change_table) - applied} 处")
    print(f"  Schema 告警: {len(validation_warnings)} 条")
    print()
    print(f"  输出文件:")
    print(f"    {out_dir / 'c1_5_post_polish.md'}")
    print(f"    {out_dir / 'c1_5_diagnosis.md'}")
    print(f"    {out_dir / 'c1_5_change_table.md'}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="C1.5 母语化深度润色 — 4 人格对抗审校执行入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("article", type=Path, help="待审校的 Markdown 文章路径")
    sub = parser.add_mutually_exclusive_group(required=True)
    sub.add_argument("--gen-prompts", action="store_true",
                     help="生成 4 个 persona subagent prompt 文件 + schema 副本")
    sub.add_argument("--apply", action="store_true",
                     help="聚合 4 份 JSON findings 并应用修改（A→B→C→D 顺序）")
    parser.add_argument("--out-dir", type=Path, default=None,
                     help="输出目录（--gen-prompts 默认 ./c1_5_run/，--apply 默认 ./c1_5_out/）")
    parser.add_argument("--findings-dir", type=Path, default=None,
                     help="findings JSON 所在目录（仅 --apply 模式必填）")
    parser.add_argument("--original-en", type=Path, default=None,
                     help="英文原文路径（--gen-prompts 模式可选，注入人格 D 的 prompt）")
    parser.add_argument("--target-media", type=str, default="WeChat",
                     choices=["WeChat", "GeekPark", "36Kr", "Juejin", "Zhihu"],
                     help="目标媒体（默认 WeChat，影响人格 C 的判断尺度）")
    parser.add_argument("--dry-run", action="store_true",
                     help="预览变更但不写入文件（仅 --apply 模式有效）")

    args = parser.parse_args()

    if not args.article.exists():
        print(f"[ERROR] 文章文件不存在: {args.article}", file=sys.stderr)
        return 2

    if not POLISH_PROMPT_PATH.exists():
        print(f"[ERROR] 找不到 references/polish-prompt.md: {POLISH_PROMPT_PATH}", file=sys.stderr)
        return 2
    if not SCHEMA_PATH.exists():
        print(f"[ERROR] 找不到 references/c1_5_subagent_schema.json: {SCHEMA_PATH}", file=sys.stderr)
        return 2

    if args.gen_prompts:
        out_dir = args.out_dir or Path("c1_5_run")
        original_en = ""
        if args.original_en and args.original_en.exists():
            original_en = read_text(args.original_en)
        return cmd_gen_prompts(args.article, out_dir,
                               original_en=original_en,
                               target_media=args.target_media)
    elif args.apply:
        if not args.findings_dir:
            print(f"[ERROR] --apply 模式必填 --findings-dir", file=sys.stderr)
            return 2
        if not args.findings_dir.exists():
            print(f"[ERROR] findings 目录不存在: {args.findings_dir}", file=sys.stderr)
            return 2
        out_dir = args.out_dir or Path("c1_5_out")
        return cmd_apply(args.article, args.findings_dir, out_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
