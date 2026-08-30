# 示例：长句逻辑显式化 + 关键判断加粗

> 英文长句常隐含因果/条件/转折关系，中文需显式连接词强化逻辑链，同时按规范加粗核心判断句。

---

## 案例 1：多步因果用`——`串联

**原文**：
> "A 10-step flow with 99% per-step success rate yields only ~90.4% end-to-end success. Errors compound quickly."

**❌ 易错译法**：
> "一个 10 步流程、每步 99% 成功率，端到端成功率只有 ~90.4%。错误复利很快。"

**✅ 推荐译法**：
> "一个 10 步流程，若每步成功率 99%，端到端成功率仅 ~90.4%**——错误会快速累积放大**。"

**优化点**：
- 用 `若` 显式表达条件关系，替代英文隐含的 `with` 结构
- 用 `——` 串联"数据结论→风险警示"，强化逻辑递进
- 关键判断 `错误会快速累积放大` 按 `translation-quickref.md` 标准加粗，便于快速抓取

---

## 案例 2：商业价值断言 + 破折号插入语

**原文**：
> This small size of KV cache - without compromising on quality - is the reason they can offer long held cache at such a ridiculously low price - less than 3% price of Cache hits for Sonnet 4.6 - and they hold it for multiple hours.
> Small amount of cache for long horizon task enables offloading to SSDs and reloading very cost effective. This reduces requirement of HBM that is in short supply and hardest to make memory from Chinese AI hardware industry perspective. DeepSeek have also developed techniques to load KV cache faster from SSD.

**❌ 易错译法**：
> 这个小的 KV 缓存 - 在不牺牲质量的情况下 - 是他们能够以如此低的价格提供长期缓存的原因 - 不到 Sonnet 4.6 缓存命中价格的 3% - 并且他们持有它数小时。少量缓存用于长程任务使得卸载到 SSD 和重载非常具有成本效益。这减少了对 HBM 的需求，HBM 是供应短缺且最难制造的内存，从中国 AI 硬件产业的角度来看。DeepSeek 也开发了从 SSD 更快加载 KV 缓存的技术。

**✅ 推荐译法**：
> 如此紧凑的`KV Cache（键值缓存）`——**在不牺牲质量的前提下**——正是他们能够以极低价格提供长时缓存的原因：价格不到`Sonnet 4.6`缓存命中费用的 3%，且能持续持有数小时。
> 
> 面向**长周期任务**的少量缓存，使得**"卸载至`SSD` + 高效重载"极具成本效益**。这降低了对`HBM（高带宽内存）`的需求——而从中国 AI 硬件产业视角看，`HBM` 正是供应最紧张、量产难度最高的内存类型。`DeepSeek` 还开发了从`SSD` 更快加载`KV Cache` 的技术。

**优化点**：
- `KV Cache`/`HBM` 首次出现严格采用 `英文（中文释义）` 格式，插入长句中间不破坏主干节奏
- 英文双破折号插入语 `- without... -` 转换为中文全角破折号 `——` 隔离，保留原文让步状语的强调语气，并同步加粗 `**在不牺牲质量的前提下**`
- `offloading... and reloading...` 拟人技术动作用引号包裹 `"卸载/重载"`，既保留工程严谨性又增强可读性
- `ridiculously low price` / `very cost effective` 准确还原商业强度为 `极低价格` / `极具成本效益`，避免直译失真
- `long horizon task` 统一译为 `长周期任务`（对齐 `glossary-ai.md` 与行业惯例）
- 关键商业/技术判断 `正是...的原因` / `"卸载...极具成本效益"` 按规范加粗，强化视觉锚点
- 盘古之白执行：`SSD`/`KV Cache` 等英文术语与中文间添加半角空格

---

## 🔁 可复用模式速查

| 英文逻辑结构 | ✅ 中文连接策略 | 适用场景 |
|:---|:---|:---|
| `X with Y yields Z` | `若 Y，则 Z` + `——` 串联结论 | 数据推导/性能分析 |
| `- insertion -` 插入语 | `——插入语——` 全角破折号隔离 | 让步状语/补充说明 |
| `enables X and Y` | `"X + Y"极具价值` 拟人动作加引号 | 技术方案/成本效益 |
| `that is in short supply and hardest to make` | `正是供应最紧张、量产难度最高的` 四字短语并列 | 资源约束/产业分析 |

> 💡 **核心心法**：中文长句的清晰度 = 显式连接词 × 关键判断加粗 × 插入语隔离。翻译时先画出逻辑骨架，再填充血肉。

