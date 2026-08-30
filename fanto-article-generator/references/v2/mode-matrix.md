# Mode Matrix v2

## Compatibility

Keep A/B/C/D/R as public entry modes. v2 adds subtypes internally; an explicit `v1`, `legacy`, or “按旧版流程” request uses the snapshot under `legacy/` and the original reference files.

## Routing matrix

| Public mode | v2 subtype | Primary reader job | Required value | Personal stance | H / 传播张力 |
|---|---|---|---|---|---|
| A | A-explainer | Understand and decide whether to care/use | Definition + boundary + decision card | Required via C4 | Required for Standard; use a real contrast or decision tension |
| B | B-news | Know what happened quickly | Facts + availability + impact | No independent stance required | Information hook; no invented suspense |
| B | B-analysis | Understand why it matters | Evidence + competing interpretations + judgment | Required via C4 and labeled | Required when supported by evidence |
| C | C-faithful | Read a faithful Chinese version | Source fidelity | Forbidden | Preserve source hook only; no invented H |
| C | C-retelling | Save time on a source | Selection + context + accurate paraphrase | Editorial notes only | Use source tension or an explicit information angle |
| C | C-commentary | Understand a source and its implications | Source summary + author judgment | Required via C4 and labeled | Required; source-backed only |
| D | D-reading | Organize reading thoughts | New understanding + limitations | Required only if user supplied it | User observation may supply the hook |
| D | D-learning | See a real learning transition | Old belief → new belief + personal observations | Required via C4 | The surprise must come from the learning change |
| D | D-practice | Reproduce a hands-on result | Version + steps + evidence + failure details | Required via C4; never invent | Use observed result or failure as tension |
| R | R1/R2/R3/R4 | Change an existing draft safely | Scoped diff + regression check | Preserve unless requested | Preserve existing hook unless scope changes it |

## C routing keywords

- “忠实翻译 / 不改写 / 保留原文结构” → C-faithful.
- “内部研究 / 工作参考 / 只整理重点” → C-retelling.
- “公众号改编 / 观点文章 / 加入我的判断” → C-commentary.
- Ambiguous public-facing requests default to C-commentary only when the user has provided a stance; otherwise default to C-retelling and ask for one judgment.

## D routing rules

- Pure link with no personal input → suggest C-retelling, do not fabricate first-person experience.
- Personal observations but no reproducible test → D-reading or D-learning.
- Version, steps, error, measurement, or before/after comparison → D-practice.

## C4 and H routing

C4 and H are separate checks: C4 asks “作者站在哪里”，H asks “读者为什么继续读”。一篇文章可以有 H 而没有新增作者立场（B-news/C-faithful），也可以有作者立场但采用信息型标题（当材料没有可靠悬念时）。

## Mode-specific minimum deliverables

### A

- One-sentence definition.
- Applicability and boundary.
- Decision card with suitable users, prerequisites, first step, failure signal, and metric.

### B-news

- What happened, when, who is affected, how to access/use it, and what remains unknown.

### B-analysis

- Fact/source view, competing interests or interpretations, author judgment, and uncertainty.

### C

- Source locator for every direct quote.
- Explicit boundary between source content and editorial content.

### D

- Evidence of the user's actual learning or an explicit no-test declaration.

### R

- Scope, affected sections, whether the core thesis is affected, whether context regression is required, upgrade decision, and post-edit validation result. Full schema: `references/v2/revision-gate.md`.
