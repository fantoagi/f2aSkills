# 示例：专有名词加注 + 核心观点强调

> 专有名词首次出现必须加注，但加注不应破坏句式流畅度。核心判断句需按规范加粗。

---

## 案例 1：厂商特有架构模式加注

**原文**：
> "Anthropic developed a two-stage 'Ralph Loop' mode for this: an Initializer Agent sets up the environment (init scripts, progress files, feature lists, initial git commit), then each session's Coding Agent reads git log and progress files to orient itself."

**❌ 易错译法**：
> "Anthropic 为此开发了两阶段 'Ralph Loop' 模式：Initializer Agent 搭建环境（init 脚本、进度文件、功能列表、初始 git commit），之后每个会话中的 Coding Agent 读取 git log 和进度文件定向自身。"

**✅ 推荐译法**：
> "Anthropic 为此开发了两阶段 `Ralph Loop`（Anthropic 两阶段初始化模式）：Initializer Agent 搭建环境（init 脚本、进度文件、功能列表、初始 git commit），之后每个会话中的 Coding Agent 通过读取 git 日志和进度文件来了解当前进度。"

**优化点**：
- `Ralph Loop` 首次出现加注 `（Anthropic 两阶段初始化模式）`，降低非通用术语的理解门槛
- 保留 `Initializer Agent`/`Coding Agent` 英文，符合行业习惯（`glossary-ai.md` 第 1 类）
- `orient itself` → `了解当前进度`：意译保留"自我定位"的核心语义，避免直译"定向自身"的生硬感

---

## 案例 2：长句中多术语加注 + 商业价值精准还原

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

| 加注场景 | ✅ 推荐格式 | 注意事项 |
|:---|:---|:---|
| 厂商特有架构 | `英文（厂商 + 功能描述）` | 如 `Ralph Loop（Anthropic 两阶段初始化模式）` |
| 技术概念/隐喻 | `中文（英文）` | 如 `上下文渗透（Context Bleed）` |
| 硬件/存储术语 | `英文（中文释义）` | 如 `KV Cache（键值缓存）`，后续可简化 |
| 长句中插入加注 | 用全角破折号`——`隔离 | 避免加注破坏主干节奏 |
| 拟人动作加注 | 动词 + 引号 + 专业等效 | 如 `"卸载/重载"` 而非直译"卸载" |

> 💡 **核心心法**：加注的核心是"降低门槛 + 保持流畅"。首次加注后，后续出现应果断简化，避免重复加注造成阅读负担。