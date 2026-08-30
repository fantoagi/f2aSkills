# 示例：英文基础句式 → 中文自然语感转换

> 以下案例全部来自同一次翻译——逐段对齐但语感照搬英文结构，导致"信息在但像翻译的"。问题不在术语，在最基础的英文句式被直译成了中文。

---

## 案例 1：连词、动词、句尾语感——开篇段

**原文**：
> Everyone uses AI.
> Almost nobody understands how it actually works.
> People throw around words like transformers, embeddings, RAG, agents, RLHF…
> …as if everyone already knows.
> Most don't.
> And honestly?
> AI is not that complicated once you see the mental models.

**❌ 易错（连词照搬 + 动词浅译 + 语感僵硬）**：
> 每个人都在用 AI。几乎没有人真正理解它是怎么工作的。人们随口抛出 transformers、embeddings、RAG、agents、RLHF——好像每个人都该知道。其实大多数人不懂。而且说实话，一旦你看到心智模型，AI 并没那么复杂。

**✅ 推荐译法**：
> 人人都在用 AI。但几乎没人真正理解它到底怎么工作。人们随口抛出 transformers、embeddings、RAG、agents、RLHF 这些词……仿佛大家都已经懂了。但大多数人并没有。说实话？只要掌握了这些核心思维框架，理解 AI 其实没那么复杂。

**优化点**：
- 英文靠换行制造节奏，中文靠**转折词**——"但"是中文口语天生的连接力，英文用新段落暗示的转折，中文不显式写出就散了
- `And honestly?` → `说实话？`：英文 `And` 在中文里是多余的过渡脂肪，直接砍掉。句尾 `?` 保留制造停顿感
- `see` → `看懂`：这里 `see` 是"理解/领会"，不是"视线看到"。`看到` 是直译，`看懂` 是中文日常语感
- `it actually works` → `它到底怎么工作`：`到底` 把英文 `actually` 从生硬事实副词转化为中文口语追问，比 `是……的` 结构（"它是怎么工作的"）自然得多
- `Most don't.` → `但大多数人并没有。`：中文口语倾向靠连词断句，不用"然而"。加上"并"和"有"，节奏完整
- `mental models` → `核心思维框架`：泛读者科普场景用"思维框架"降低认知门槛，符合 `glossary-ai.md` 译法

---

## 案例 2：名词句转主谓句 + 标点 + 数字语感

**原文**：
> The brain of every AI model.
> A neural network is a pipeline of layers.
> → Data enters the input layer → Passes through hidden layers → Exits as a prediction
> Each connection has a "weight" — a tiny score that controls how much influence one neuron has on the next.
> Training = adjusting billions of these weights until the output is accurate.
> Simple idea. Insane at scale.
> GPT-4 has ~1.8 trillion parameters. Claude 3 Opus has hundreds of billions.
> All from the same basic concept: layered neurons with adjustable connections.

**❌ 易错（名词句照搬 + 连接词缺失 + 形容词直译）**：
> 每个 AI 模型的大脑。神经网络是一层一层的管道：数据进入输入层 → 穿过隐藏层 → 以预测的形式输出。每条连接有一个"权重"——一个微小的分数，控制一个神经元对下一个神经元的影响程度。训练 = 调整数十亿个这样的权重，直到输出准确。简单的想法。可怕的规模效应。GPT-4 有约 1.8 万亿参数。Claude 3 Opus 有数千亿。全都基于同一个基础概念：带可调连接的层状神经元。

**✅ 推荐译法**：
> 每个 AI 模型的大脑
> 
> 神经网络是一个由多层结构组成的流水线。
> → 数据进入输入层 → 穿过隐藏层 → 以预测结果输出
> 
> 每条连接都有一个`weight（权重）`——一个微小的数值，控制着一个神经元对下一个神经元的影响程度。
> 
> 训练 = 不断调整这数十亿个权重，直到输出结果足够准确。
> 
> 想法很简单。规模上来就惊人。
> 
> GPT-4 拥有约 1.8 万亿个参数，Claude 3 Opus 也有数千亿个。
> 
> 而这一切，都源于同一个基础概念：分层排列的神经元，加上可调节的连接权重。

**优化点**：
- `The brain of every AI model.` → `每个 AI 模型的大脑`：英文的独词句做主标题。中文不加冒号或破折号，直接作为独立短句即可，让后续段落来承接
- `Simple idea. Insane at scale.` → `想法很简单。规模上来就惊人。`：英文用名词句制造停顿冲击。中文名词句（"简单的想法。可怕的规模效应。"）读起来像字典条目，没有主语丧失了断言力。恢复为主谓结构才通顺
- `a pipeline of layers` → `由多层结构组成的流水线`：抽象名词需补感官描述，`由……组成` 注入架构感，`多层结构` 让 pipeline 不只是"一层层管道"的意象而是具体运作单元
- `.` → `，`合并数字句：英文结构独立并列短句（前句 GPT-4，后句 Claude 3 Opus），但中文应串成一个对比流——`GPT-4 ……，Claude …… 也有……` 读起来才是自然中文
- `All from the same basic concept:` → `而这一切，都源于同一个基础概念：`：英文 `All` 开头很轻松，中文需要把 `All` 翻译成先行总结词"这一切"。前面加"而"制造思路上提的转折感
- `trained` → `调整` 补副词"不断"：中文习惯显式表达持续性；`直到输出结果足够准确` 比简短版本"直到输出准确"加了"结果"和"足够"，承受移动端阅读的语境自然感
- `weight` 首次出现加英文标注：术语双语策略——`weight（权重）`，不必在正文反复解释，首次出现时建立对应关系
- `layered neurons with adjustable connections` → `分层排列的神经元，加上可调节的连接权重`：英文一个名词短语压缩到底，中文必须拆开——"分层排列"修饰神经元，"可调节"的连接权重单独成成分

---

## 🔁 可复用模式速查

| 英文特征 | 中文正确做法 | 对应案例 |
|:---|:---|:---|
| `And` 开头串联段落 | 直接砍掉，或用"但/而"代替 | 案例 1 |
| `X. Y.` 名词句制造停顿 | 恢复为主谓结构，中文名词句丧失断言力 | 案例 2 |
| `how it works` 类宾语从句 | 拆成主谓句 + 追问词（"到底"/"究竟"） | 案例 1 |
| `see` 当"看到" | 按上下文选：看懂/理解/领会/发现 | 案例 1 |
| 英文换行暗示的转折关系 | 用"而/但/却"显式连接，中文不靠换行传逻辑 | 案例 1+2 |

> 💡 **核心心法**：中文语感的核心是"动作先行 + 逻辑显式 + 节奏紧凑"。翻译时先问自己："这句中文母语者会这么说吗？"若答案是否定的，立即重组句式。

---

## 案例 3：通用动词+抽象宾语搭配越界——整段语感崩塌

> 以下 3 句全部来自同一次 Ethan Mollick "Choosing to Stay Human" 翻译。问题不在术语、不在句式、不在代词——每个词单独看都正确，但动词和宾语连在一起，中文母语者读完就皱眉头。

### 3a. `cut through` + 内容材料

**原文**：
> The article cuts through two education studies, the BCG elite consultant experiment, and an Anthropic programmer study, before landing on one question.

**❌ 搭配越界（词合法，读感别扭）**：
> 文章穿过两篇教育研究、BCG 精英顾问实验和 Anthropic 程序员研究，最后停在一个问题上。

**✅ 自然中文搭配**：
> 文章贯穿了两篇教育研究、BCG 精英顾问实验与 Anthropic 程序员研究，最后停在一个核心问题上。

**优化点**：
- `cut through` 的空间隐喻（劈开丛林走到对岸）中文没有对应的抽象延伸。`穿过` 的宾语必须是物理空间（穿过隧道/广场/人群），不能是论文或实验
- 正确做法：用 `贯穿`（保留"从头到尾"的时间线语义但接受抽象宾语），或更口语的"从 A 切入，途经 B 和 C，最后停在 D"

### 3b. `spend` + 注意力 / `equivalent` + 理解

**原文**：
> …these posts are just meaning-shaped attention vampires that take mental effort to decode and give you no equivalent understanding in return.

**❌ 搭配越界**：
> 你花掉了注意力，却没得到等量的理解。

**✅ 自然中文搭配**：
> 这些帖子不过是披着意义外皮的注意力吸血鬼，你耗费了注意力，却未能获得相应的理解。

**优化点**：
- `花（掉）` + 注意力 ❌：中文"花"仅与时间/金钱/精力自然搭配。注意力不用"花"，用"耗费/投入/分散"
- `等量` + 理解 ❌：中文抽象名词"理解"不接受"量"修饰。`equivalent` 应译为"相应的"或转换结构为"理解了同样的东西"
- `give you no X in return` → `give` 和 `return` 无需逐词翻译——中文`未能获得` 已经包含了"付出之后没有回报"的完整语义

### 3c. `offload` + 认知任务 / `to some degree` + 二值动词

**原文**：
> AI is different because the technology is general enough that virtually any cognitive task can be offloaded into it to some degree.

**❌ 搭配越界**：
> 几乎任何一个认知任务，你都可以部分卸载给它。

**✅ 自然中文搭配**：
> AI 的不同之处在于它的通用性极强。几乎任何认知任务，你都可以部分交由它处理。

**优化点**：
- `offload` → `卸载` ❌：中文"卸载"的语义锚点是"拆除已安装的东西/移除程序"（uninstall）。认知任务的转移不是"拆除"，是"移交/转交/外包"。`offload cognitive tasks` → `交由它处理` / `甩给它做`
- `部分` + `卸载` ❌："卸载"是二值动词（装/卸），天然排斥程度修饰。你不会说"部分删除"一个文件。`to some degree` 应转移到动词选择上（"或多或少可以交由"）或省略程度副词让动词本身含粒度感
- `AI is different because...` → `与……不同之处在于` 而非 `不同是因为`——`because` 在中文科普文体中直接译为"因为"会破坏节奏，改用"之所以/不同之处在于/关键在于"更自然

## 🔁 可复用模式速查

| 英文特征 | 中文正确做法 | 对应案例 |
|:---|:---|:---|
| `动词+抽象宾语`在中文里越界 | 遮住动词只看"动+宾"两个词——这俩能单独成词组吗？（"穿过+研究"？）不能→换动词 | 案例 3a/3b/3c |
| 英文空间隐喻动词（cut through/walk into/step into） | 检查中文对应动词的宾语约束。空间动词+物理宾语 ✅，+抽象宾语 ❌ | 案例 3a |
| 英文程度副词（partially/to some degree）+二值动词 | 二值动词（装/卸、删/留）不接受"部分"修饰。把程度转移到动词选择上 | 案例 3c |

---

## 案例 4：介词框架"在……后"内缺动作主体——句子断了气

**原文**：
> But this article is his systematic course-correction on "the default posture of using AI," written after he accumulated a mountain of experimental evidence.

**❌ 介词框架直译（缺主谓，读感断气）**：
> 但这篇文章是他在大量实验证据积累后，对"用 AI 的默认姿势"做的一次系统性纠偏。

**✅ 恢复主谓结构**：
> 但这篇文章是在他积累大量实验证据后，对"用 AI 的默认姿势"做的一次系统性纠偏。

**优化点**：
- `在大量实验证据积累后` → `在他积累大量实验证据后`：英文 `after + noun phrase` 翻译到中文时，如果直接丢进"在……后"框架而框架内只有名词堆、没有主谓结构，中文读起来动作主体悬空
- 中文"在+……+后"框架天然期望框架内是一个**事件**（谁做了什么事），不是一坨名词。`在大量实验证据积累后` 缺"谁积累"——补"他积累"就通了
- 这不是语法错误，是信息结构问题：英文 `after he accumulated...` 的 `he accumulated` 在翻译中被压成了 `积累`（名词化），丢掉了主语。正确做法是保留主谓结构，或改用"经过"（`经过大量实验证据的积累` 也可，但主谓结构更自然）

## 🔁 可复用模式速查

| 英文特征 | 中文正确做法 | 对应案例 |
|:---|:---|:---|
| `动词+抽象宾语`在中文里越界 | 遮住动词只看"动+宾"两个词——这俩能单独成词组吗？（"穿过+研究"？）不能→换动词 | 案例 3a/3b/3c |
| 英文空间隐喻动词（cut through/walk into/step into） | 检查中文对应动词的宾语约束。空间动词+物理宾语 ✅，+抽象宾语 ❌ | 案例 3a |
| 英文程度副词（partially/to some degree）+二值动词 | 二值动词（装/卸、删/留）不接受"部分"修饰。把程度转移到动词选择上 | 案例 3c |
| `在+名词堆+后` / `after+名词短语` | "在……后"框架内必须含主谓结构。纯名词堆→补主语+动词，或改"经过" | 案例 4 |
