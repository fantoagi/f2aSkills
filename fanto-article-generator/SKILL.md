---
name: fanto-article-generator
description: 面向微信公众号和中文自媒体的 AI 内容生产 skill。支持 A 系列科普、B 行业快讯、C 一线内容转述、D 认知重构和 R 已成稿修订；默认使用 v2 的读者价值、证据账本、分级质控和发布兼容流程，也可用 v1/legacy 复现旧流程。
---

# fanto-article-generator v2

## 目标

先确定读者价值，再组织证据、观点和结构，最后做分级质控。默认优先级：

1. 事实可信度
2. 读者实用价值
3. 论证完整性
4. 中文自然度
5. 传播力
6. 生产速度

正文默认输出到 `output/<topic>/index.md`，内部审计产物默认输出到 `runlog/<topic>/`。保留现有 Markdown frontmatter：`title`、`cover`。

## 版本与兼容

- 默认工作流：`v2`。
- 用户明确说“按旧版流程”“v1”“legacy”“保持原来的完整阶段输出”时，读取 `legacy/SKILL.v1.md`，并使用原有参考文件。
- 不要为了迁移而改写历史 `output/` 文件。
- 新任务在内部产物中记录 `workflow_version: v2`。

## 总流程

```text
源材料准备
  ↓
读者与发布目标
  ↓
Editorial Brief
  ↓
模式与子模式
  ↓
C4 立场预热（适用子模式）
  ↓
源材料清单、主张账本和必要核验
  ↓
文章角度与大纲
  ↓
正文初稿
  ↓
最终标题
  ↓
读者价值审查
  ↓
事实、引用、逻辑、语言、渲染质控
  ↓
正文和内部审计产物落盘
```

最终标题不得在正文初稿前锁死。写作前只确定一个临时角度标题。

## 复杂度分流

### Lite

适用于无外部事实、无英文源材料、无时间敏感内容、预计不超过 1500 字且不涉及价格/政策/版本/行业数据的任务。

执行：Brief → 模式判断 →（适用时）C4 立场预热 → 大纲 → 正文 → H/读者价值检查 → 基础语言和渲染检查。Lite 的 C4 结果并入 `stage-01-brief.md`，不额外创建阶段文件。

### Standard

默认流程。执行 Brief、源材料清单、模式子类型、（适用时）C4 立场预热、主张账本、大纲、正文、最终标题、五道质控；Standard 必须执行 Editor Technical Gate，并将其结果聚合进 G2/G3/G5。

### High-risk

出现以下任一情况即触发：最新新闻或人物动态、版本/价格/性能数据、政策监管、投资商业数据、医疗安全法律判断、英文长文/长访谈/论文、两个以上来源相互引用、五条以上外部事实主张。

增加：原始来源核验、逐条事实主张登记、引用回溯、数字日期双检、因果关系审查和不确定性标注。

## 源材料准备

- 用户直接粘贴的文本可直接作为源材料，但主动确认是否有图、链接、代码或附件。
- 本地 Markdown/文本/PDF：读取全文，保留图片、链接、代码块和章节结构；图片复制到 `images_<topic>/`。
- URL：优先使用 CDP 浏览器读取渲染后的正文和图片清单；不要只依赖纯文本抓取。现有 SVG、X/Twitter 和图片处理细节参见原有脚本与 v1 参考文件。
- 英文源材料：根据源材料体裁选择翻译规范；C-faithful/C-retelling/C-commentary 先完成必要翻译，再做改写。不要把未完成的翻译直接当作中文成稿。

## Editorial Brief

Standard/High-risk 必须在 `runlog/<topic>/stage-01-brief.md` 落盘；Lite 至少保存简版 Brief。按 `references/v2/editorial-brief.md` 填写：

- 目标发布场景
- 具体目标读者（角色 + 场景）
- 读者当前问题
- 为什么现在需要
- 一句话核心命题
- 读者读完应形成的判断
- 读者读完可以采取的行动
- 关键证据
- 反方观点或限制
- 作者判断
- 明确不讨论的内容
- 预期文章类型和篇幅
- 临时角度标题
- 文章核心认知张力 / 开篇问题
- 传播钩子类型：反常识 / 反差 / 场景 / 金句 / 数据 / 悬念 / 无

如果核心命题、读者收益或传播张力无法填写，先降级为材料整理，不直接生成发布稿。C-faithful/B-news 可明确记录“无新增作者立场”或“无额外悬念”，但仍需说明如何保持源材料的事实张力。

## C4 立场预热

按 `references/v2/stance-gate.md` 执行。A-explainer、B-analysis、C-commentary、D-learning、D-practice 必须在大纲前生成 Stance Seed；D-reading 只能使用用户提供的观察。C-faithful、B-news、R1/R2/R4 不新增作者立场，C-retelling 只做编辑选择。

适用 C4 的任务优先使用独立 stance subagent，明确授权可以不同意源材料；立场只能评价已有事实，不能新增事实、数字、因果或用户没有提供的经历。立场必须落进正文，否则 G3 阻塞。

机械检查：

```bash
python scripts/stance_lint.py <article.md> --stance <stance.md> --mode C-commentary
```

## 主张账本与事实核验

Standard/High-risk 在 `runlog/<topic>/claims.md` 建立机器可检查的主张账本；需要阶段快照时同步保存 `stage-03-claims.md`。C 类任务按需增加 `quotes.md`，High-risk C 任务另保存 `stage-03-quotes.md`。格式参见 `references/v2/claims-ledger.md`。

必须登记的内容：外部数字、日期、人物发言、产品功能、版本、价格、公司历史、benchmark、政策、因果关系和直接引语。

高风险事实必须核对原始来源或可信一手来源。无法核验时，降低确定性并明确写“据该材料称”“目前尚无独立来源确认”等。合成句不得放入引号。直接引语找不到来源定位时阻塞交付。

必要脚本：

```bash
python scripts/claims_lint.py <article.md> --ledger <claims.md>
```

## 模式路由

### A：系列科普 / 番外篇

保留大白话、强比喻、痛点引入、概念类型判断、比喻边界和系列连续性。核心目标是帮助读者理解并决定是否关心/采用。

必须包含：

- 一句话定义
- 核心机制或工作方式
- 适用边界和代价
- 决策卡：适合、不适合、前置条件、第一步、失败信号、指标

职业/角色类主题讲岗位解决的组织问题、相邻岗位分工、适用阶段和成本；应用/工具类主题讲采用时机和不采用时机；方法论类主题按实际环节灵活组织，不机械凑固定章节。

主比喻、术语预算和 Mermaid 是指导性规则，不是无条件硬限制。只有确实能降低理解成本时才使用 Mermaid。

### B：行业快讯

保留 B 入口，内部区分：

- `B-news`：事实快讯，回答发生了什么、什么时候、影响谁、如何使用、什么尚不确定。
- `B-analysis`：行业解读，区分事实、源材料观点、编辑判断和不确定性，补充利益关系、竞品位置和可能影响。

产品/模型发布优先检查发布时间、主体、版本、核心变化、地区、入口/API、价格、限制、benchmark 口径和来源。没有数据时不得强行写“拐点级变化”；行动建议必须有事实支撑。

### C：AI 一线内容转述

C 保留旧入口，按以下关键词分流：

- `C-faithful`：忠实翻译；不加入个人立场，不新增外部背景或因果推论。
- `C-retelling`：编辑转述；可重组和补少量读者背景，但不增加独立事实判断。
- `C-commentary`：观点改编；允许作者判断，但必须明确区分源材料、编辑推断和作者立场。

“忠实翻译/不改写”进入 C-faithful；“内部研究/工作参考”进入 C-retelling；“公众号改编/观点文章/加入我的判断”进入 C-commentary。所有直接引语需在 quotes 账本中可追溯。

### D：认知重构

内部区分：

- `D-reading`：有阅读观察、没有实测；明确声明无个人实测。
- `D-learning`：有认知变化、困惑或判断，但没有完整可复现实测。
- `D-practice`：有版本、步骤、报错、数据、时间或前后对比。

纯链接不再直接拒绝：默认建议 C-retelling，并询问 1-2 个个人观察。没有用户提供的经历、时间和结果，不得编造第一人称实测。

### R：已成稿修订

内部区分：

- `R1`：句子/段落级修改
- `R2`：章节顺序和衔接
- `R3`：观点、证据和立场
- `R4`：事实、引用和数字纠错

每次 R 任务都要记录：用户要求、受影响位置、是否影响核心命题、是否需要重新检查前后文、是否升级 Standard、修改后的验证结果。格式参见 `references/v2/revision-gate.md`。若修改触及核心命题、事实方向、引语含义或整体结构，升级到 Standard，而不是继续按轻量微调处理。

## 标题

正文初稿完成后，读取 `references/shared/title-workflow.md`，生成 3-5 个候选标题。最终标题除准确性和读者利益外，还必须检查是否存在基于真实材料的认知张力或开放问题；没有张力时可以明确选择信息型标题，不得用虚构冲突补 H。最终标题必须检查：

1. 信息是否准确
2. 是否兑现读者利益
3. 是否有必要的传播张力
4. 是否适合公众号移动端扫读
5. 是否夸大、标题党或超出证据

标题可以保留既有模式风格，但不能用反常识、数字和情绪词掩盖证据不足。

## 五道质控闸门

### G1 源材料完整性：BLOCKER

正文所需的源材料、图片、链接、代码块、章节和来源定位必须完整。

### G2 事实、引用与归因：BLOCKER

不能有未登记的高风险主张、无来源直接引语、数字/日期/专名错误或把作者判断写成源材料事实。

### G3 命题与结构：BLOCKER

核心命题必须清楚；标题承诺必须被正文兑现；每一节必须提供证据、背景、反方、方法、行动或必要过渡；结尾必须回到读者问题。

### G4 读者价值与传播张力：Standard/High-risk 为 BLOCKER，Lite 为 WARNING

按 `references/v2/reader-value-rubric.md` 评分，包含 `curiosity_tension` 维度。除目标读者、现在为什么需要、读者新增判断、行动/方法、边界、证据密度和可转发性外，检查是否有真实的反差、悬念、意外或问题推进。H 不等于标题党：A-explainer、B-analysis、C-commentary 在 Standard 中必须有可见的认知张力；B-news/C-faithful/C-retelling 可以采用信息型或源材料原有钩子，但没有新增张力时必须在 Brief 中明确记录原因，不得凭空制造冲突。

```bash
python scripts/reader_value_check.py <article.md> --brief <brief.md> --mode <v2-subtype>
```

### G5 语言、技术与渲染：按问题等级处理

Standard/High-risk 必须读取 `references/v2/editor-technical-gate.md`，并将其逐项裁决写入 `runlog/<topic>/stage-06-audit.md`；Lite 若涉及技术机制或目标渲染，也应按需执行基础版技术预检。指代逻辑和技术机制错误归入 G3/G2 BLOCKER；渲染、概念一致性和同语境品牌大小写错误归入 G5 BLOCKER。

```bash
python scripts/technical_gate_lint.py <article.md> --audit <stage-06-audit.md>
```

Markdown、图片路径、代码围栏、关键术语和技术机制错误为 BLOCKER。破折号、三连排比、加粗、模板化过渡、节奏均匀和“AI 味”只做 WARNING，必须人工判断，不因数量单独阻塞。`c2_scan.py` 的 scan-16 使用 `references/ai-humanize-gates.md` 中的 H2-H5 命名；H2-H5 是去 AI 味的风格子门禁，不得与 v2 的 G1-G5 事实/结构/读者/渲染闸门混用。

现有 `translation_lint.py`、`check_links.py`、`rotation_check.py`、`c1_5_polish.py` 继续使用，但其结果必须映射到 G1-G5，不能把所有风格提示都视为失败。

R 修订记录可并入 `stage-06-audit.md`；复杂 R3/R4 任务应额外保留 `stage-04-revision.md`。

## 内部落盘协议

### Lite

```text
runlog/<topic>/
├── stage-01-brief.md
└── stage-06-audit.md
```

### Standard

```text
runlog/<topic>/
├── stage-00-intake.md
├── stage-01-brief.md
├── stage-02-source-inventory.md
├── stage-03-stance.md（适用 C4 的任务；Lite 除外，Lite 并入 stage-01-brief.md）
├── claims.md
├── stage-03-claims.md
├── stage-04-outline.md
├── stage-05-title.md
└── stage-06-audit.md
```

### High-risk 额外文件

```text
stage-03-verification.md
stage-03-quotes.md
stage-05-translation-audit.md
```

对话中默认只输出简短交付报告：工作流、模式、核心命题、目标读者、主要读者价值、事实/引用状态、语言/渲染状态和待确认项。

## 交付报告

```markdown
## 交付

- 工作流：v2 / Lite / Standard / High-risk
- 模式：A / B-news / B-analysis / C-faithful / C-retelling / C-commentary / D-reading / D-learning / D-practice / R1-R4
- 核心命题：
- 目标读者：
- 主要读者价值：
- 传播张力：通过 / 信息型标题 / 有待确认
- 作者立场：通过 / N/A / 有待确认
- 事实核验：通过 / 有待确认
- 引用核验：通过 / 有待确认 / 不适用
- 语言与渲染：通过 / 有警告
- 待确认项：
```

## 调用示例

- “写一篇解释 Agent 适用边界的番外篇” → A-explainer。
- “基于发布稿写行业快讯” → B-news；“分析这次发布对行业的意义” → B-analysis。
- “忠实翻译这段访谈” → C-faithful；“整理成内部研究” → C-retelling；“改成公众号观点文章” → C-commentary。
- “我读完这篇文章后的学习分享”且有个人观察 → D-reading/D-learning；有版本、步骤和结果 → D-practice；只有链接 → 先建议 C-retelling。
- “把这段改得更自然” → R1；“调整这两节顺序” → R2；“补强我的判断” → R3；“修正这个数字” → R4。
