# AI 翻译术语表 (Glossary)

> **使用方式**：翻译时遇术语 → 先查本表 → 按对应子类规则处理。不确定时默认保留英文+首次加注。
> **维护**：每次翻译遇新术语即时登记至下方“待定区”（CI/CD 模式），每月初团队对齐固化译法，避免高频概念滞后。

---

## 1. 直接保留英文（泛读者已熟知）

全文统一保留，不加注，除非原文首次出现时已有解释。

| 术语 | 说明 |
|:---|:---|
| `LLM` | 大语言模型，中文圈已完全通用 |
| `RAG` | 检索增强生成，保留缩写更简洁专业 |
| `Agent` | 智能体/代理，保留英文最符合行业习惯 |
| `Memory` | 对话记忆/长期记忆/向量存储，依语境理解 |
| `Skills` | Agent 技能/工具调用能力 |
| `Prompt` | 提示词/指令，保留英文更自然 |
| `Context / Context Window` | 上下文/上下文窗口，技术语境保留 |
| `Token` | 计费/长度单位，不译 |
| `MCP` | Model Context Protocol，协议名保留 |
| `API / GUI / CLI` | 标准技术缩写，保留 |
| `Zero-shot / Few-shot` | 提示工程标准术语 |
| `Fine-tuning` | 可保留或译为"微调"，首次出现建议中英对照 |
| `MoE` | 专家混合模型，架构名保留英文更简洁 |
| `PPO` | 近端策略优化，强化学习标准术语 |
| `HBM` | 高带宽内存，硬件术语中文圈通用 |
| `SSD / NAND / LPDDR` | 存储/内存类型，保留英文更专业 |
| `FLOPs` | 浮点运算次数，算力计量单位 |
| `EUV` | 极紫外光刻，半导体工艺术语 |
| `AGI / ASI` | 通用/超级人工智能，行业通用缩写 |
| `CUDA` | NVIDIA 并行计算平台，保留英文 |

## 2. 首次中英对照，后续简化

首次出现标注，后文按需使用最简形式。

| 英文 | 建议格式 | 后续用法 |
|:---|:---|:---|
| `Alignment` | `Alignment（对齐）` | 对齐 |
| `Orchestration` | `Orchestration（编排）` | 编排 |
| `Grounding` | `Grounding（事实锚定）` | 事实锚定 |
| `Hallucination` | `Hallucination（幻觉）` | 幻觉 |
| `Pipeline` | `Pipeline（流水线）` | 流水线/工作流 |
| `Checkpoint` | `Checkpoint（检查点）` | 检查点 |
| `Foundation model` | `基础模型（Foundation model）` | 基础模型 |
| `Temperature` | `Temperature（温度值/生成随机性）` | 作为参数设置时保留英文 |
| `Attention` | `Attention（注意力机制）` | Transformer 架构语境中，大写保留英文+首次加注 |
| `weight` | `weight（权重）` | 权重 | 技术术语可中文前置，便于快速识别核心概念；非技术语境用"英文（中文）" |
| `GRPO` | `GRPO（DeepSeek 新强化学习算法）` | GRPO | 替代 PPO 的新算法，首次需解释 |
| `RLVR` | `RLVR（基于验证奖励的强化学习）` | RLVR | DeepSeek 推理能力核心策略 |
| `Speculative Decoding` | `推测解码（Speculative Decoding）` | 推测解码 | 推理加速技术 |
| `KV Cache` | `KV Cache（键值缓存）` | KV Cache | 长上下文核心优化点，技术语境保留英文 |
| `Engram` | `Engram（条件记忆模块）` | Engram | DeepSeek 特有"内存换计算"机制 |
| `mHC` | `mHC（流形约束超连接）` | mHC | DeepSeek 宏观架构创新 |
| `TileLang` | `TileLang（跨平台内核编译工具）` | TileLang | 解决 CUDA 护城河的关键工具 |
| `Muon optimizer` | `Muon 优化器（Muon optimizer）` | Muon 优化器 | 大规模训练优化器 |
| `RSI` | `RSI（递归自我改进）` | RSI | AGI 演进关键路径，指"AI 自主设计并执行实验以迭代自身能力" |
| `FDE (Forward Deployed Engineer)` | `FDE（驻场部署工程师）` | FDE / 驻场工程师 | 职位头衔类术语；技术读者保留英文，泛读者可用中文释义 |
| `Charter` | `指令宪章（Charter）` | 宪章 | Agent 工程中给 Agent 下发的完整任务定义文档，包含目标、工作范围、自检规则、记忆方式、停止条件。不要译为"任务章程"——气场偏企业管理，不匹配 Agent 工程语境 |
| `Loop` | `循环（Loop）` | 循环 | 自动反复 Prompt Agent 的小系统。与 cron job 的区别：内部有决策者（模型），不是固定脚本 |
| `Loop Engineering` | `循环工程（Loop Engineering）` | 循环工程 | 设计、构建和管理 Loop 的工程实践。Boris Cherny / Addy Osmani 2026 年提出的范式 |
| `Cron Job` | `定时任务（Cron Job）` | 定时任务 | 固定脚本的周期执行。与 Loop 的核心区别：无决策能力 |
| `Loop State` | `循环状态（Loop State）` | 循环状态 | 记录 Loop 执行进度的持久化文件（通常 LOOP-STATE.md），使 Loop 能在中断后精准续跑 |
| `Harness Engineering` | `运行框架工程（Harness Engineering）` | 运行框架工程 | 为长运行 Agent 搭建校验、重试、状态管理基建的工程实践。Loop Engineering 的前置阶段 |
| `Expected Reward` | `期望奖励（Expected Reward）` | 期望奖励 | 强化学习标准术语——Agent 执行动作后期望获得的累积奖励信号的数学期望。注意与 `Return`（回报，即实际累积奖励）区分：Reward 是单步信号，Return 是多步累积量 |
| `CapEx` | `资本支出（CapEx）` | CapEx / 资本支出 | 企业用于购买、升级、维护固定资产（如数据中心、GPU 集群）的支出。首次出现建议 `CapEx（资本支出）`，后文统一用大写 `CapEx` 或中文，**禁止小写 `capex`** |
| `Quadratic` | `二次复杂度（Quadratic）` | 二次复杂度 | 算法复杂度术语 O(n²)。中文字面"二次"存在"第二次"歧义，首次出现必须补"复杂度"或 bilingual 标注；后文可用"二次复杂度" |

## 3. 强制标准中文（有明确行业共识）

统一采用中文技术社区译法，避免歧义。

| 英文 | 标准译法 | 备注 |
|:---|:---|:---|
| `Training / Inference` | 训练 / 推理 | 固定搭配 |
| `Embedding` | 嵌入 / 向量表示 | 依语境选择 |
| `Retrieval` | 检索 | 不译"召回"除非特指召回率 |
| `Generation` | 生成 | 不译"产生" |
| `Reasoning` | 推理 / 逻辑推导 | 依语境选择 |
| `Planning` | 规划 / 任务规划 | Agent 语境用"规划" |
| `Tool Calling` | 工具调用 | 不译"函数调用"除非特指 Function Calling |
| `landing page layouts` | `落地页布局（landing page layouts）` | 营销/产品/设计领域标准表述；首次加注，后续用"落地页布局"；UI 专业场景可用"着陆页版式" |
| `brand voice guidelines` | `品牌调性指南` | 统一用`品牌调性指南`；泛受众首次加注`品牌语调（调性）指南` |
| `sparring partner` | `思维陪练（sparring partner）` | 首次加注，后续用"思维陪练"；强调"认知对抗+建设性反馈"的双重属性 |
| `thinking partner` | `个人思考伙伴（thinking partner）` | 首次加注，后续用"思考伙伴"；避免"伴侣"的情感暗示 |
| `mental models` | `核心思维框架` | 泛读者科普首选；专业认知科学文档可用“心智模型” |
| `edge` | `竞争优势` | 商业/战略语境；禁用“边缘/刀刃”直译 |
| `hack` | `取巧的捷径` | 口语化贬义语境；技术语境保留英文 |
| `Expert Load Balancer` | `专家负载均衡器` | MoE 架构核心组件，中文技术圈已有共识 |
| `Multi Token Prediction` | `多 Token 预测` | 推测解码的子技术，直译准确 |
| `ZERO bubble pipeline` | `零气泡流水线并行（ZERO bubble pipeline）` | 首次加注，后续可简化为"零气泡流水线"；"气泡"为并行训练领域标准隐喻，指流水线空闲时间 |
| `Wide Expert Parallel` | `宽专家并行（Wide Expert Parallel）` | NVIDIA TensorRT-LLM 专有 MoE 推理策略，首次加注，后续可简化为"宽专家并行"或`Wide-EP` |
| `cold` / `warm` | `冷启动` / `预热` | 缓存/上下文/会话语境；禁用“冷的/热的”生活化直译 |
| `flip` / `toggle` | `切到` / `设为` / `切换` | 配置/代码/布尔值修改语境；物理开关语境才用“翻转/拨动” |
| `bursts` / `spikes` | `突发流量` / `瞬时高并发` | API 限流/服务器负载语境；禁用“脉冲/尖峰”物理隐喻 |
| `make the cut` | `入选` / `落选配置项` | 方案筛选/配置审计语境；需压缩为“状态词+实体”，反同义反复 |
| `kill` / `die` | `强制结束` / `宕机` | 进程/Hook/服务状态语境；开发者日常交流常用“挂掉/杀进程” |
| `habit tracker` | `习惯追踪器` / `习惯记录器` | 产品功能术语；禁用“打卡器”（中文无此搭配） |
| `stress-testing` | `压力测试` / `极限推演` | AI 推理语境优先用”极限推演”；后端/系统语境用”压力测试” |
| `shipped (software context)` | `推送` / `发布` / `自带` | 软件/配置语境标准表述；禁用”发货”（硬件/电商词误植） |
| `agentic coding` | `Agentic 编程` | 国内 AI 研发圈已形成共识，使用 `Agentic 编程` 而非 `Agent 型编程`（拼凑感强）或 `智能体驱动开发`（过长）。同理：`agentic workflow`→`Agentic 工作流` |
| `conditioned on`（ML/DL 语境） | `受…驱动` / `以…为条件` | `action-conditioned`→`受动作驱动的`，禁用"行动可调节的"（"可调节"是 adjustable 而非 conditioned）。`conditioned on X`=模型的输出以 X 为输入条件 |
| `content nouns` / `meta-words` | `具体关键词` / `模糊指代` | 搜索/查询语境；禁用"内容名词/元词"直译（中文无此日常搭配） |
| `per-conversation toggle` | `对话级开关` | 配置指南标准表述；禁用"每对话"（非中文标准搭配） |
| `citation behavior` | `引用格式` / `引用展示方式` | 产品语境；禁用"引用行为"（偏学术抽象） |
| `binary (executable)` | `二进制文件` / `可执行文件` | 技术文档标准表述；禁用单独"二进制"（易歧义指数制） |
| `context bloat` | `上下文占用` / `上下文冗余` | AI/工程语境；禁用"膨胀"（物理/经济词误植） |
| `data residency tax` | `数据驻留溢价` / `驻留附加费` | 商业成本语境；禁用"税"（政府征收语境误植） |
| `Gaussian Splatting (3DGS)` | `3D 高斯溅射` | 计算机图形学/CV 领域标准译法。禁用"高斯泼溅"（机翻）。`Gaussian Splats`→`高斯溅射` |
| `Meta-Evaluation` | `元评测（Meta-Evaluation）` | 评价"评测本身"的质量，非评价模型/系统。禁译"评价你的评测"（2026-08-25） |
| `predefined sequence` | `预定义调用序列（Pre-specified Sequence）` | 区别"预定序"（predetermined）：`a predefined sequence of LLM calls`→"预定义调用序列的 LLM 工作流"（2026-08-25） |
| `rapidly evolving`（技术演进语境） | `前沿演进极其迅速` | 禁"变得极快"（口语）。`Agentic workflows are evolving rapidly`→"Agentic 前沿演进极其迅速"（2026-08-25） |

## 4. 多义词按语境区分

结合上下文选择精确译法，避免一刀切。

### 4.0 多义词裁决决策树（先走流程，再查下表）

**问题**：当一个英文词同时适配 §4 下表的 2-3 个语境时，LLM 容易随机选择或偏好默认语境，导致译法漂移。

**裁决流程**（按顺序执行，任一步骤终止时即得答案）：

```
1. 问一句："这个中文译法在目标读者脑中的第一反应是什么？"
   ↓
2. 第一反应 ≠ 原文想表达的意思？
   → 是：跳过该候选，回到本表查其他语境候选，重复步骤 1
   → 否：进入步骤 3
   ↓
3. 表内所有候选都不匹配？
   → 是：保留英文 + 首次加注（参考 §5 加注格式）
   → 否：进入步骤 4
   ↓
4. 多个候选都匹配第一反应？→ 按以下优先级裁决：
   a) 模式 C/D（转述/学习视角）→ 优先选"读者已知"的中文（如"应用"、"工具"），不选术语
   b) 模式 A（系列文章）→ 优先选"具象/具画面感"的中文，配合主比喻
   c) 模式 B（行业快讯）→ 优先选"专业克制"的中文，保留技术语域
   d) 同一文章内一致性 > 选哪个译法 → 首次确定后不漂移
```

**常见陷阱**（决策树不能解决时查此表）：

| 词 | 易错 | 真实应选 | 原因 |
|:---|:---|:---|:---|
| `labs` | "实验室" | "大实验室" / "巨头" | 中文第一反应是物理房间，丧失商业实体感 |
| `pipeline`（商业）| "销售管线/管道" | "销售线索" | 第一反应是水管，与销售场景脱钩 |
| `control plane`（泛商业）| "控制面" | "管控层" / "治理层" | 控制面是 K8s 术语，泛读者不熟 |
| `moat`（战术级）| "护城河" | "命门" / "核心壁垒" | 护城河锚定巴菲特战略层面，描述技术环节越界 |
| `production`（软件）| "生产" | "生产环境" / "真实业务" | 中文生产=工厂，软件语境必须补"环境/业务" |
| `horizontal`（商业战略）| "横向" | "通用型" | 横向无对应商业含义，读者无感 |
| `signal`（AI 训练）| "信号" | "训练素材" / "学习数据" | 信号=电信号，与训练语义脱钩 |
| `cost`（资源）| "成本" | "开销" / "代价" | 成本锚定财务，资源消耗应避歧义 |
| `feature`（产研黑话）| "功能" | "需求" | 产研内部说"ship a feature"="交付一个需求" |
| `judgment / verdict`（商业）| "判词" | "判断" / "结论" | 判词是法官术语，商业场景用判断 |
| `discipline`（技术实践）| "自律" | "纪律" / "习惯" | 自律带道德色彩，技术实践不用 |

| 英文 | 语境 1 | 语境 2 | 语境 3 |
|:---|:---|:---|:---|
| `Context` | 对话/提示词上下文 | 业务语境/市场环境 | 技术上下文窗口 |
| `Model` | AI 模型 | 架构范式/方法论 | 商业模型（需谨慎区分） |
| `Workflow` | Agent 执行链 | 业务流程/审批流 | 数据处理流水线 |
| `State` | 模型状态/对话状态 | 系统状态/应用状态 | 州（地理，需区分） |
| `Performance` | 模型表现 / 跑分性能 | 系统性能（延迟/吞吐量等） | 执行情况 |
| `Scale` | 参数规模（如 Scale of models） | 扩展性 / 扩容（Scale up/out）| 行业/市场规模 |
| `Policy` | 策略网络（强化学习语境） | 访问控制策略（安全/合规语境） | 政策（监管语境） |
| `Weights` | 模型权重 / 参数 | 占比 / 权重分配（评估维度） | / |
| `Harness` | AI 应用编排框架（如 Claude Harness） | 马具/控制装置（非技术语境） | / |
| `Pipeline` | 技术流水线/工作流（工程语境） | 销售线索/商机（商业语境）。禁用"销售管线"（第一反应是水管）或"销售管道"（偏直译）；中文销售领域标准说法是"销售线索" | / |
| `Hero's Journey` | 叙事范式/故事结构（商业战略隐喻） | 英雄之旅（电影/文学语境） | / |
| `signal` | 训练素材 / 学习数据 / 有效信息 | AI 训练/学习语境；禁用"信号"（易与电信号混淆） |
| `cost (disk/resource)` | 占用 / 开销 / 代价 | 资源消耗语境；禁用"成本"（财务语境歧义） |
| `argument` | 论点/论据（学术辩论语境） | **论证** / **分析**（商业/投资语境）。"整篇文章的论点"太学术，改"文章的分析/论证" | / |
| `verdict / judgment` | 裁决/判词（法律语境） | 商业分析→**判断** / **结论**；代码审查/CI/CD→**审查报告** / **验收结果**。"判词"是法官术语，商业文章用"判断"；"审查裁决"在中文代码审查语境不说——日常说"看审查报告/看验收结果"。`read the review verdict`→"看验收报告"，不写"读审查裁决" | / |
| `feature`（产品/研发语境） | 功能（通用译法） | 国内产研日常→**需求**。"ship a feature"→"交付一个需求"（产研黑话，"功能"是用户视角，"需求"是研发视角）。`kick off a feature`→"启动一个需求"。但面向终端用户/产品介绍文章保留"功能" | / |
| `acknowledge / admit` | 承认（认错/认罪色彩） | **表明** / **印证** / **释放信号**（商业语境）。"用行动承认"暗示此前在抵赖；原文只是"effectively telling the market" | / |
| `horizontal`（商业战略语境） | 横向的（平台/工具） | **通用型**（如"通用型工具"）。"横向"在中文商业语境无对应含义，读者无法理解 | / |
| `labs`（指 AI 公司） | 实验室 | **大实验室** / **巨头**。"实验室"在中文第一反应是物理房间；指 OpenAI/Anthropic 等公司时必须加"大"前缀或直接用"巨头" | / |
| `incumbents`（商业语境） | 现有巨头 / 在位者 | **既有厂商**。"现有巨头"将"existing"和"giant"混为一谈，且"在位者"太学术；中文商业报道标准说法是"既有厂商/既有企业" | / |
| `surface`（应用层/产品语境） | 表面 / 地盘 | ① "application surface"→应用层版图；② "surface where work executes"→操作界面/工作层面。"界面"在中文=UI，但企软语境中"surface"指承载业务运行的平台层，不能一概译为"界面" | / |
| `moat`（隐喻强度分级） | ① 企业级战略壁垒（如"微信的护城河是社交链"）；② 技术机制/战术环节（如"交接是护城河"） | ① **护城河** ✅（公司/产品层面的结构性壁垒，巴菲特的原始含义）；② **命门** / **核心壁垒** / **关键差距** ✅（战术级技术环节禁止用"护城河"）。"交接才是护城河"→"交接才是命门所在"——流水线的一个交接机制是战术实现细节，不是企业战略壁垒，用"护城河"是隐喻膨胀。"护城河"在中文商业语境锚定在巴菲特/战略层面，描述技术环节时读者会困惑"这也能算护城河？" | / |
| `configuration / capabilities`（战略/竞争语境，如"闭源模型的专属配置"） | 配置（产品规格/参数） | **专属领地** / **核心壁垒** / **标配能力**。"配置"在中文锚定产品参数表（如"高配/低配/标配"），战略竞争语境中"闭源模型的专属配置"听起来像在评测汽车——读者第一反应是"什么配置？GPU 配置还是内存配置？"。改用"专属领地"或"核心壁垒"。"闭源模型的专属配置"→"闭源巨头的专属领地" | / |
| `technique`（软件/方法论语境，如"specific techniques"） | 技术（technology） | **方法** / **模式** / **技巧**。"技术"在中文锚定科学技术/工程实现，"technique"在编程方法论文中指的是具体的操作手法（如锦标赛模式、扇出模式）。`specific techniques`→"特定模式（如锦标赛、扇出）"，不写"特定技术" | / |
| `overloaded`（CS 术语，如"the term is overloaded"） | 被滥用（abused） | **承载杂糅含义** / **含义过载**。"overloaded"是 CS 术语（函数重载），引申为"一个词被塞进了太多不同含义"——这是描述性判断，不是道德批判。`the term is overloaded`→"这个词承载了太多杂糅含义"，不写"被滥用" | / |
| `projection`（数学/抽象语境，如"projection of a loop"） | 投影（几何/光学概念） | **映射** / **切面**。"投影"在中文锚定光学/几何成像（投影仪、地图投影），描述"循环的不同投影"时读者脑中会出现一束光——"循环"是动态过程，"投影"是静态光学结果，两者无法搭配。学术写作中用"映射"（保数学含义）或"切面"（保维度含义）。 | / |
| `secondary (sale)`（私募市场语境） | 老股转让 / 二手份额 | **看语境**：① 创始人/早期股东卖老股套现（"卖公司"讨论中的中间选项）→ **老股转让**；② LP 转让基金份额 → **二手份额**。2026-08-10 失误：用"二手份额"（LP 语境）译了创始人卖老股场景。先确认主语是创始人还是 LP | / |
| `Neolabs` / `Neo-labs`（AI 行业） | 直译/大写为实体公司 | **新锐实验室（Neo-labs）**。Elad Gil 等投资人口中的行业统称，指 OpenAI/Anthropic 等新一代 AI 实验室，不是叫 "Neo Labs" 的公司。源文形态判据：单个小写词或连字符 `Neolabs`/`Neo-labs` → 统称；若源文为专有名词形态（大写拆词/首发链接）再考虑实体 | / |
| `margin call`（金融） | 追加保证金 | **追加保证金**（唯一译法）。"margin call"= 券商要求补足保证金；中文金融报道标准说法"追加保证金" | / |
| `revenue stream`（商业/投资） | 收入流 | **收入流**（通用译法）。是否加注按 §2 / cross-cultural-terms 读者分层处理 | / |

## 5. 专有名词加注规范（强制执行 + 拦截清单）

首次出现必须加注，降低非通用术语的理解门槛。

| 类型 | 示例 | 加注格式 | 说明 |
|:---|:---|:---|:---|
| **基准/评测** | `TerminalBench 2.0` | `TerminalBench 2.0（Agent 任务基准测试）` | 非行业通用基准，需解释用途 |
| **专有模式/循环** | `Ralph Loop` | `Ralph Loop（Anthropic 两阶段初始化模式）` | 厂商特有架构模式 |
| **研究/论文缩写** | `ACON` | `ACON（上下文优化研究）` | 缩写首次出现需展开 |
| **框架特有概念** | `Magentic` | `Magentic（动态任务账本协调模式）` | AutoGen 特有编排模式 |
| **技术概念/隐喻** | `context bleed` | `上下文渗透（Context Bleed）` | Agent 上下文管理核心概念 |
| **隐喻/习语** | `context rot` | `上下文劣化（Context Rot）` | 行业已接受此隐喻，保留+加注 |
| **公司/产品** | `GLM` / `MoonShot` / `MiniMax` | `GLM（智谱 AI 大模型系列）` | 中国大模型厂商，首次出现建议加注 |
| **硬件厂商** | `YMTC` / `CXMT` | `YMTC（长江存储）` / `CXMT（长鑫存储）` | 中国存储芯片龙头，泛读者可能不熟悉 |
| **评测基准** | `BIG-Bench Hard` / `GSM8K` / `MMLU` | `BIG-Bench Hard（复杂推理基准）` | 学术评测集，首次出现需解释用途 |
| **技术隐喻** | `CUDA moat` | `CUDA 护城河（CUDA moat）` | 商业竞争隐喻，保留+加注 |
| **历史人物** | `Adam Smith`、`Alan Turing` 等 | `亚当·斯密（Adam Smith）`、`艾伦·图灵（Alan Turing）` | 中文圈已有固定译名的著名历史人物，用中译名+英文原名加注。科技/商业/学术界在世人物保留英文原名（如 `Dario Amodei`），不强行中文化 |
| **易混术语** | `hyper trained` vs `overfitted` | `hyper trained` = 超大规模训练（中性）| `overfitted` = 过拟合（负面）。不可互译 |
| **易混术语** | `inversion` | 倒置 / 反过来（非"镜像"） | `X is an inversion of Y` = X 本质就是 Y 方向反了；`mirror image` 才是"镜像"。不可混淆 |
| **领域术语** | `data room` | 虚拟资料室（data room） | M&A/尽调/审计场景的安全文档共享空间，非 `data warehouse`（数据仓库），非普通"数据室" |

## 6. 禁止强行翻译

若中文表述会引发歧义、冗长或偏离原意，保留英文。

| 原文 | ❌ 错误译法 | ✅ 推荐处理 |
|:---|:---|:---|
| `Agentic workflow` | "智能体代理工作流" | `Agentic 工作流` 或保留英文 |
| `Computer-use Agent` | "计算机使用智能体" | `Computer-use Agent` 或 `界面操作型 Agent` |
| `Data exhaust` | "数据尾气" | `执行痕迹数据` 或保留英文+加注 |
| `System of Record` | "系统记录" | `权威业务系统（System of Record）` |
| `System of Action` | "行动系统" | `执行系统（System of Action）`。企软术语，"system of action"=业务实际跑在上面的执行层，区别于"system of record"（仅记录数据）。"行动系统"在中文有军事感，用"执行系统" |
| `System of Work` | "工作系统" | **保留英文 System of Work**。全文核心概念（奥兹国公司的护城河所在），类似 Agent/Token/Prompt 等级别，不强行汉化。首次出现可加中文解释："即企业实际执行工作、并捕获由此产生数据的操作界面" |
| `Headless` | "无头" | `接口化暴露（Headless）` 或保留+加注 |
| `control plane` | "控制面" | 泛商业读者→**管控层** / **治理层**。"控制面"是 Kubernetes/网络术语，面向泛读者不适用 |
| `CUDA moat` | "CUDA 护城河"直译无解释 | `CUDA 护城河（CUDA moat）` + 简短说明"指 NVIDIA 生态壁垒" |
| `just-in-time fashion` | "及时时尚" | `即时流式传输（just-in-time）` 或保留英文+加注 |
| `Cowork` | 归属 OpenAI | `Cowork（Anthropic 的 AI 同事产品）`，**归属 Anthropic 非 OpenAI** |
| `Codex` | 归属 Anthropic | `Codex（OpenAI 的编码 Agent 产品）`，**归属 OpenAI 非 Anthropic** |
| `thread`（Twitter/X 平台，指系列推文/长推文） | 裸用 "thread" | **长推文（Thread）**。公众号/泛读者语境中，`thread` 是 Twitter 圈内黑话，大部分中文读者不知道指什么。首次出现必须写"长推文（Thread）"，后续可用"长推文"。禁止裸用"thread"或"推文串"。"他发了一篇爆款 thread"→"他发了一篇爆款长推文（Thread）" |

## 7. 术语待定区 (Staging Area)
*说明：遇到 unsure 的新词（如 Vibe Coding, Context Engineering），首次出现采用 `英文（中文直译/意译）` 格式，并记录在此处。当月内重复出现 3 次以上，月初复盘时移入正式术语表。*

首次出现格式示例：
- `Vibe Coding（氛围编程）`
- `Context Engineering（上下文工程）`

[待定] `Vibe Coding`：氛围编程 / 直觉式编程
[待定] `Context Engineering`：上下文工程

## 8. 术语争议历史（已裁决）
| 术语 | 争议点 | 最终决议 | 裁决日期 | 提案人 |
|:---|:---|:---|:---|:---|
| `brand voice guidelines` | "语调"vs"调性"场景适用 | 统一用`品牌调性指南` | 2026-05-24 | @译者 A |
| `sparring partner` | "搏击"vs"思维" | 统一用`思维陪练（sparring partner）`，强调认知对抗属性 | 2026-05-24 | @译者 B |
| `recursive milestone` | "递归式"vs"自举" | 编译器/AI 自写自的语境下，用`自举（Bootstrapping）`而非"递归式"。"递归"是数学/算法概念，"自举"是工程概念——系统自己构建自己 | 2026-06-29 | 首席译审 |
| `Orchestration` | "编排者"vs"编排" | Orchestration = 编排（机制/行为），Orchestrator = 编排者（角色）。原文 "one of orchestration rather than execution" 对比的是两种机制而非角色 | 2026-06-29 | 首席译审 |
| `Harness Engineering` | "调度框架"vs"运行框架" | Harness = 运行/测试脚手架（Test Harness），非调度。"调度"= Scheduling，会与 cron 调度器撞车 | 2026-06-29 | 首席译审 |

## 9. 开发者工具域：保留英文优先

> **适用场景**：源材料涉及 Git、IDE、CI/CD、Agent 编排等开发者工具链。目标读者为开发者或 AI 从业者时，以下术语保留英文（首次可加注），不强行汉化。

| 英文 | 处理 | 理由 |
|:---|:---|:---|
| `Worktree` | 保留 Worktree | Git 标准术语，中美开发者通用；"工作树"需额外解释，反而阻碍阅读 |
| `Commit` | 保留 Commit（提交） | 首次加注，后续裸用 Commit |
| `Pull Request` | 保留 Pull Request | 不译为"拉取请求" |
| `CI/CD` | 保留 CI/CD | 首次写"CI（持续集成）"，后续裸用 |
| `Bootstrap / Bootstrapping` | 自举（Bootstrapping） | 编译器/AI 自写自语境的标准黑话；不要译为"递归式"或"引导式" |
| `Hook` | 保留 Hook | Git/Agent 语境中的事件钩子，不译为"钩子" |
| `Routine` | 保留 Routine（例行任务） | Anthropic Claude Code 特指的功能名 |

**判断原则**：该术语在中文开发者社区的日常交流中是否直接用英文？如果是 → 保留英文。Worktree、Commit、Hook 在中文开发者对话中不会说"工作树""提交""钩子"，而是直接说 worktree、commit、hook。

## 10. 易混淆术语对（词性/语义边界）

| 英文 | ✅ 正确译法 | ❌ 错误译法 | 理由 |
|:---|:---|:---|:---|
| `Orchestration` | 编排（机制/行为） | 编排者 | Orchestration = 编排这个行为/机制；Orchestrator = 编排者（执行者）。原文对比的是两种机制（orchestration vs execution），不是两种角色 |
| `Harness Engineering` | 运行框架工程 | 调度框架工程 | Harness = 运行/测试脚手架（如 Test Harness），不是调度。"调度"对应 Scheduling，会与后文 cron 调度器概念撞车 |
| `Scheduler` | 调度器 | 运行器 | 与 Harness 区分：Scheduler 才是"调度"，Harness 是"运行框架" |

## 11. 中文排版规范

> **适用场景**：所有面向公众号/媒体发布的中文译文。

| 规则 | 说明 |
|:---|:---|
| 引号 | 使用全角中文双引号 `""`，不使用半角 `""`。半角引号在中文媒体后台被视为"未排版的生肉"。单引号同理：`''`（全角）而非 `''`（半角）。英文缩写（如 don't）中的撇号保留半角 |
| 括号 | 中文语境用全角 `（）`，英文/代码语境保留半角 `()` |
| 破折号 | 使用 `——`（两个全角破折号），不使用 `--` 或 `—` |
| 货币格式 | 英文 `$20` / `€15` → 中文 `20 美元` / `15 欧元`。不保留 `$` 符号——中文排版中 `$` 视觉突兀，微信公众号渲染器可能误识别为 LaTeX 公式标记。格式：`金额 + 货币名`，如 `每月 20 美元`、`按年付每月 17 美元` |
| 产品定价术语 | `tier`（定价档）→ `版 / 计划 / 套餐`，不译"层"。`free tier` → `免费版`，`pro tier` → `Pro 版 / 专业版`。`plan` → `计划 / 套餐`。`subscription` → `订阅`。`billing` → `计费 / 付费方式` |
| 专有名词大小写 | 产品名/公司名/协议名首字母必须大写：`Git`（非 git）、`GitHub`（非 github）、`Claude Code`（非 claude code）、`Token`（AI 计费语境，非 token）、`Pull Request`（非 pull request）。代码/CLI 命令中的小写保留原样 |
| 指示词正式度 | 工程/技术语境优先用书面指示词：`这一` > `这个`，`该` > `那个`。"这一设定"优于"这个安排"，"该机制"优于"这个东西" |

> **核心底线**：翻译是为了降低理解门槛，不是改变行业语言习惯。当英文术语已成为中文 AI 圈日常表达时，**保留即是最精准的翻译**。
