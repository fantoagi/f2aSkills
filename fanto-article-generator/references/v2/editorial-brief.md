# Editorial Brief v2

## Purpose

Editorial Brief is the minimum editorial contract for a generated article. It is created before the outline and final title. It answers who the article serves, what decision it supports, and what evidence can carry the argument.

## Required fields

```markdown
## Editorial Brief

- 工作流版本：v2
- 复杂度：Lite / Standard / High-risk
- 发布场景：公众号 / 知乎 / 掘金 / Newsletter / 内部研究 / 其他
- 目标读者：角色 + 具体场景
- 读者当前遇到的问题：
- 读者为什么现在需要这篇文章：
- 本文核心命题：一句话
- 读者读完后应该形成的一个判断：
- 读者读完后可以采取的一个行动：
- 支撑命题的关键证据：至少 1 条；Standard/High-risk 至少 3 条或明确说明不足
- 主要反方观点或限制：
- 作者自己的判断：无 / 一句话写出
- 本文明确不讨论：
- 预期文章类型：解释 / 快讯 / 转述 / 评论 / 学习分享 / 微调
- 预计篇幅：
- 临时角度标题：
- 文章核心认知张力 / 开篇问题：
- 传播钩子类型：反常识 / 反差 / 场景 / 金句 / 数据 / 悬念 / 无
- C4 立场状态：强制 / 条件强制 / 不适用；Stance Seed 文件：
```

## Quality rules

- “目标读者”必须包含角色和场景，例如“正在评估 Agent 的企业产品负责人”，禁止只写“AI 爱好者”。
- “核心命题”必须能被复述为一句完整判断，不能只是主题名。
- “读者价值”至少选一项：形成判断、采取行动、带走方法、节省阅读时间、理解一个争议。
- “文章核心认知张力 / 开篇问题”必须来自源材料、用户观察或作者明确判断；没有合适张力时填写“无新增悬念，采用信息型标题”，不得用夸张词代替张力。
- C4 适用时，Brief 的作者判断不能只写“值得关注/很重要”，至少要包含一个取舍、保留、反对或意外。
- 没有实测时不得写成实测复盘；没有可靠来源时不得把推断写成事实。
- 如果无法填写核心命题或读者收益，先降级为材料整理，不得直接生成发布稿。

## Route rules

- Lite：Brief 简短填写，允许证据只有用户提供的具体观察。
- Standard：所有字段填写；证据字段必须可链接到 source inventory 或 claims ledger。
- High-risk：所有字段填写，并增加事实核验、引用核验和不确定性说明。

## Title timing

Brief 中只保留“临时角度标题”。最终标题在正文初稿完成后生成，必须重新检查是否超出证据或夸大读者收益。
