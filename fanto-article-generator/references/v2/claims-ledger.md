# Claims Ledger v2

## Purpose

The claims ledger separates source facts, source opinions, direct quotes, author inferences, and author judgments. It is the audit source for factuality and attribution; it is not part of the published article unless the user asks for it.

## Files

- `runlog/<topic>/claims.md`: canonical article-level ledger consumed by `claims_lint.py`.
- `runlog/<topic>/stage-03-claims.md`: optional stage snapshot of the same ledger for audit trails.
- `runlog/<topic>/quotes.md`: optional quote-level ledger for Standard C tasks.
- `runlog/<topic>/stage-03-quotes.md`: required quote audit artifact for High-risk C tasks.

## Claim schema

```markdown
## Claim F-001

- 文中主张：
- 主张类型：事实 / 引语 / 源材料观点 / 作者推断 / 作者判断 / 假设
- 来源：
- 来源定位：URL、页码、段落、时间戳、推文序号或文件行号
- 核验状态：已核验 / 部分核验 / 未核验 / 不适用
- 可信度：高 / 中 / 低
- 是否时间敏感：是 / 否
- 允许的改写范围：直译 / 可重组 / 可概括 / 只能作为观点归因
- 正文落点：章节或行号
- 备注：
```

## Quote schema

```markdown
## Quote Q-001

- Speaker：
- 原文：
- 中文译文：
- 正文引用：
- 来源定位：
- 是否逐字对应：是 / 否
- 是否存在删节：
- 是否存在合并：
- 归属方式：直接引语 / 间接转述 / 编辑整理
- 备注：
```

## Required rules

- Every external number, date, named product, company-history statement, benchmark, price, policy statement, and causal claim must have a claim entry in Standard/High-risk workflows.
- High-risk claims require a first-party or otherwise authoritative source whenever one exists. If independent verification is unavailable, mark the claim as unverified and lower the article's certainty.
- A direct quote without a source locator blocks delivery.
- A synthesized sentence must not be wrapped in quotation marks. If a quote is edited for length, use an ellipsis or explicitly mark it as an edited translation.
- Author judgment may be unsupported by a source, but it must be labeled as judgment and may not introduce new facts.
- Claims lint checks coverage and attribution; it does not decide whether a source is trustworthy. Human review remains required for borderline claims.

## Evidence labels for prose

Use one of the following when the distinction matters:

- `据官方材料……`
- `原文认为……`
- `从这些材料可以推断……`
- `我的判断是……`
- `目前尚不能确认……`

Do not use a confident factual sentence when the ledger status is `未核验`.
