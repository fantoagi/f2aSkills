# 示例：结构忠实度 + 引语质感 + 标题保真

> 以下 3 个案例全部来自同一次跳步翻译事故——跳过预处理、逐段对齐翻译和执行后检查，直接"理解后重写"导致的问题。

---

## 案例 1：收尾段整体丢失——只翻了第一句，后面 3 句全丢

**原文**：
> You now know more about Claude than most people who use it every day.
> Pick one feature from this list. Just one. Set it up today. You don't need to implement everything at once - knowing what exists is already half the battle.
> Come back to this article when you're ready for the next one.

**❌ 易错（4 句收尾只翻了第 1 句，后面全丢）**：
> （第 1 句翻了，后半截直接消失）

**✅ 推荐译法**：
> 现在，你对 Claude 的了解，已经超过大多数每天使用它的人。
> 
> 从这份清单里选一个功能。就一个。今天就把它设置好。
> 
> 你不需要一次性实现所有功能——知道它们存在，就已经成功了一半。
> 
> 当你准备好尝试下一个时，再回到这篇文章。

**优化点**：
- 原文 4 句构成一个完整的行动闭环：认知建立 → 降低行动门槛（"就一个"）→ 消除心理负担（"成功了一半"）→ 给出返回锚点。缺任何一句，这个闭环就断了
- 4 句分别承担不同功能：第 1 句建立信心，第 2 句推动行动，第 3 句消除负担，第 4 句给读者一个"回头"的承诺。翻译时必须逐句对齐，不能因为"意思差不多"而合并或省略
- 预处理阶段应对结尾段整体标记为"高价值结构块"，不允许拆分或省略

---

## 案例 2：直接引语质感被概括

**原文**：
> Most people use Claude as a validation machine. They describe a problem. Claude says that sounds hard and offers five bullet points of advice.

**❌ 易错（引语感丢失）**：
> 大多数人把 Claude 当作认可机器。描述一个问题，Claude 说这很难，然后给出五点建议。

**✅ 推荐译法**：
> 大多数人把 Claude 当作一台"认可机器"。他们描述一个问题，Claude 回复说"这听起来确实很难"，然后给出五条建议要点。

**优化点**：
- `"认可机器"` 加引号——中文习惯用引号标出比喻性非正式术语。原文 `validation machine` 是非正式造词，引号还原了原文的口语批评感
- `says` → `回复说`：比"说"更贴合人机对话场景
- `"that sounds hard"` → `"这听起来确实很难"`：保留原文模拟对话的直接引语质感，加引号明确这是角色扮演式回应，不是译者的概括
- `bullet points` → `建议要点`：保留"bullet points"的结构信息（不是一段话，是列清单），而非压缩为模糊的"建议"

---

## 案例 3：标题丢失 + 动词选词偏差

**原文**：
> Practice a difficult conversation
> Most people walk into hard conversations unprepared. They know what they want to say but not what the other person will actually say back.

**❌ 易错（标题丢失，直译痕迹）**：
> （标题未翻，直接跳到正文）
> 大多数人毫无准备地走进艰难对话。他们知道想说什么，但不知道对方实际会怎么回应。

**✅ 推荐译法**：
> 练习一场高难度对话
> 
> 大多数人面对棘手对话时毫无准备。他们知道自己想说什么，却不知道对方实际会怎么回应。

**优化点**：
- 标题 `Practice a difficult conversation` 必须保留——翻译指南要求"逻辑段落严格对应"，节标题是最不该丢的结构元素
- `walk into` → `面对`：英文空间隐喻直译成"走进"在中文里生硬，`面对` 保留"即将进入"的语境
- `hard` → `棘手` vs `艰难`：标题用"高难度"（与 `Practice` 搭配更自然），正文用"棘手"（与"对话"搭配更自然）——中文里形容词与名词的搭配比英文更挑剔

---

## 🔁 底层教训：三层护栏全部跳步

| 跳过的步骤 | 直接后果 | 对应案例 |
|:---|:---|:---|
| 预处理：通读标记核心句/引语/隐喻/结构 | 关键收束句未被标记，结尾执行时丢失 | 案例 1 |
| 翻译执行：逐段对齐 + 规则强制检查 | 引语被概括为叙述，"bullet points"信息维度缩水 | 案例 2 |
| 翻译执行：连续自问"结构元素是否对齐" | 节标题直接跳过 | 案例 3 |
| 后校验：对照 checklist 逐项打勾 | 以上问题一个都没被捞回来 | 全部 |

> 💡 **核心结论**：翻译流程不是"先理解再重写"——是"逐段对齐翻译 + 规则强制检查 + 后校验兜底"。三层少一层，遗漏就变成定局。
