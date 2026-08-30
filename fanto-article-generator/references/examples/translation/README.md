# 翻译案例库索引

> 按场景分类的优质案例，翻译执行时遇具体问题可快速查阅  
> 📍 位置：`references/examples/translation/`  
> 🔄 维护：新案例按模板追加 → 同步更新本索引表

---

## 🔄 标准工作流

翻译执行中遇具体问题
↓
判断问题类型 → 查阅本索引定位对应案例文件
↓
参考 ❌/✅ 对比 + 优化点解析重组译文
↓
执行翻译 → 对照 translation-quickref.md 确认格式/加粗/连接词
↓
提交前自检 → 对照 translation-checklist.md 逐项打勾
↓
复盘沉淀 → 新案例按模板入库 → 更新本索引表

---

## 📚 按问题类型检索

| 问题类型 | 对应案例文件 | 核心覆盖点 | 高频场景 |
|:---|:---|:---|:---|
| 英文句式→中文语感 | `english-to-chinese-naturalization.md` | 连词/名词句/动词/断句处理 | 开篇段/收尾段/口语化表达 |
| 长句逻辑显式化 | `long-sentence-logic.md` | 因果连接/关键判断加粗/破折号使用 | 技术论证/数据推导/商业分析 |
| 隐喻专业化替换 | `metaphor-professionalization.md` | 口语隐喻→专业等效表述 | 风险警示/能力描述/架构比喻 |
| 专有名词加注 | `proper-noun-annotation.md` | 首次加注格式/核心观点强调/长句术语插入 | 技术架构/厂商方案/评测基准 |
| 结构忠实度 | `structural-fidelity-and-quote-preservation.md` | 段落对应/引语质感/标题保真 | 行动号召/直接引语/章节标题 |
| 极客短句/科普文体 | `punchy-style-cases.md` | 断言语气/拟人引号/概念具象化 | X/Substack 风格短文/产品发布/观点输出 |
| X thread → 模式 C 长文改写 | `x-thread-to-mode-c.md` | hashtag/emoji 处理、推文→章节合并、slang 间接化、X 结构隐藏 | X 源材料 + 模式 C 改写（X + C 高频组合） |
| 软件动词介质对齐 | `engineering-context-alignment.md` + `glossary-ai.md` 第 3 节 | `shipped`→`推送`，禁用"发货" |
| 搜索指令认知校准 | `punchy-style-cases.md` + `translation-quickref.md` 映射表 | `内容名词`→`具体关键词` |
| 资源消耗表述精准 | `engineering-context-alignment.md` + `glossary-ai.md` 第 3 节 | `bloat`→`占用`，`cost`→`开销` |
| 商业隐喻本地化 | `metaphor-professionalization.md` + `glossary-ai.md` 第 3 节 | `tax`→`溢价`，禁用"税" |

---

## 🎯 按文章类型检索

| 文章类型 | 优先查阅案例 | 注意事项 |
|:---|:---|:---|
| 技术架构/深度长文 | `long-sentence-logic.md` + `proper-noun-annotation.md` | 重点保真技术细节 + 术语加注格式 |
| 产品发布/科普短文 | `english-to-chinese-naturalization.md` + `punchy-style-cases.md` | 重点还原语感 + 短句节奏 + 拟人引号 |
| 商业战略/投资分析 | `structural-fidelity-and-quote-preservation.md` + `punchy-style-cases.md` | 重点保留批判性语气 + 商业黑话转换 |
| 厂商动态/融资新闻 | `proper-noun-annotation.md` + `punchy-style-cases.md` | 重点处理公司名/产品名加注 + 商业断言语气 |
| **X/Twitter thread 改写** | **`x-thread-to-mode-c.md`** | **重点：hashtag/emoji 处理、推文→章节合并、slang 间接化、X 结构隐藏；与 `punchy-style-cases.md` 配合使用** |
| 高：配置指南/代码片段/架构分析 | `proper-noun-annotation.md` + `engineering-context-alignment.md` | 重点保真技术细节 + 研发黑话映射 + 代码格式隔离 |
| 中：产品发布/科普短文 | `english-to-chinese-naturalization.md` + `punchy-style-cases.md` | 重点还原语感 + 短句节奏 + 拟人引号 |
| 低：商业战略/投资分析 | `structural-fidelity-and-quote-preservation.md` + `punchy-style-cases.md` | 重点保留批判性语气 + 商业黑话转换 |

---

## 💡 使用建议

### 预处理阶段
1. 判断文章类型 → 查阅上表"优先查阅案例"
2. 扫描全文标记高频句式（如断言句/长因果/拟人动作）
3. 对照 `glossary-ai.md` 标记待加注术语

### 执行阶段
1. 遇不确定句式 → 按"问题类型"或"技术密度"检索对应案例文件
2. 参考 `❌/✅` 对比 + 优化点解析重组译文
3. 执行时连续自问（见 `ai-translation-guide.md` 阶段 2）
4. 研发语境词汇 → 立即查 `translation-quickref.md` → `🔧 研发语境映射表`
5. 极客短句/断言 → 立即查 `punchy-style-cases.md` → 按模板还原语气

### 复盘阶段
1. 新遇到的高质量问题 → 按模板新增案例文件
2. 同步更新本索引表 + 登记至 `glossary-ai.md` 待定区
3. 月末团队对齐时优先评审新案例

---

## 🆕 案例提交模板

```markdown
示例：[一句话概括案例核心教学点]
原文：
[英文原文段落]

❌ 易错译法：
[典型错误译文 + 简要说明问题]

✅ 推荐译法：
[优化后译文，保留加粗/引号/反引号等格式]

优化点：
- [优化点 1：术语/句式/语气/排版等维度]
- [优化点 2：对齐哪条规范条款]
- [优化点 3：可复用的模式总结]