# cc2Feishu Workflow

## 目标

把“内容发布到飞书”固定成一条可重复执行的链路：

1. 读取当前线上文档并确认事实源
2. 整理正文
3. 创建/更新文档
4. 插入 blank whiteboard
5. 逐个回填 whiteboard 内容
6. 发布后校验
7. 失败时排障

## 数据流

### 输入
- 主题 / 草稿 / markdown 文件 / 目标飞书位置
- 可选：已有文档 URL 或 token
- 可选：已有 diagram / DSL 文件
- 可选：用户刚刚手动修改过的线上文档

### 中间产物
- 当前线上 `docs +fetch` 结果（更新模式下的 canonical baseline）
- Lark-flavored Markdown
- `doc_id` / `doc_url`
- `data.board_tokens`
- whiteboard 图表产物（如 `diagram.json` / `diagram.png`）

### 输出
- 飞书文档 URL
- 本次采用的模式：局部修补或整段重建
- 已回填的 whiteboard token 列表
- 被保留未改的对象范围
- 发布后校验结果

## 详细步骤

### A. 判断目标容器

- 新建文档：使用 folder-token / wiki-node / wiki-space
- 更新文档：使用 doc_id 或 URL
- 如果给的是 wiki URL，先解析真实 `obj_token`

### B. 建立事实源并整理 markdown

- 若是 update 已有文档，先 `docs +fetch` 读取当前线上版本
- 当前线上 fetch 结果是唯一事实源；memory、旧本地 markdown、历史 rebuild 文件都只能作为参考
- 若输入来自对话，先整理出适合飞书的分节 markdown
- 若输入来自本地文件，可读取并做轻量清洗，但仅限新内容草稿，不默认替代当前线上正文
- 更新已有文档时，准备发布内容必须由“当前线上 fetch 内容 + 本次新增内容”现场整理
- 命中图表语义时，在相关段落后插入 `<whiteboard type="blank"></whiteboard>`

### C. 选择更新策略

#### 0. Preflight impact check

在真正 update 前，先基于当前 fetch 结果检查：
- 本次变更会触达哪些标题范围
- 会不会改动已有文章正文、结尾、配图说明或 whiteboard 位置
- 哪些对象范围必须保留未改

如果会影响已有文章，而用户没有明确要求修改旧文章：
- 立即停止继续 update
- 改用 append / insert 方案，或重新划定更小边界

#### 1. 局部修补模式

适用条件：
- 小范围文本调整
- 单节增删
- 少量新增 whiteboard
- 新增文章 / 新章节的 append-only / insert-only 更新
- 修改范围可被纯文本稳定定位

执行要求：
- 优先 `append` / `insert_after` / `insert_before` / `replace_range`
- 新增文章默认只追加，不改已有文章结构和正文
- 每次局部修改后立即 `docs +fetch`
- 先验证本次修改没有把文档结构带偏，再做下一轮修改

#### 2. 整段重建模式

出现以下任一情况，直接停止继续叠加局部修改：
- 连续两次局部替换后 `fetch` 结果仍异常
- 章节顺序漂移
- 出现重复段落或残段
- 需要跨多个章节改写
- 修改目标已经无法被安全定位

执行要求：
- 先从**当前线上 fetch 版本**抽出一份 canonical markdown 作为目标正文
- 明确保留区与重建区边界，而且边界必须最小化
- 重建区内 whiteboard 按新 token 重建和回填
- 必要时用 `overwrite` 一次性重建目标区域
- 不要直接拿旧的总稿、历史 draft 或 rebuild 文件覆盖线上全文

### D. 发布正文

- create：`docs +create`
- update：按已选模式执行局部修补或整段重建
- 记录所有返回字段，尤其是 `data.board_tokens`
- 同时记录哪些范围被明确保留未改

### E. fetch 输出的使用边界

`docs +fetch` 返回的 `<whiteboard token="..."/>` 只用于：
- 识别已有对象
- 建立 token 映射
- 发布后验收

不要把它直接写回新的 markdown 源。

如果重建内容需要保留已有 whiteboard，只能二选一：
- 避开该对象所在区域，不覆盖它
- 承认该区域不可安全复用，重建该区域并拿新的 `board_tokens`

## whiteboard 编排

### F. 建立 token 与图意图映射

whiteboard token 的顺序必须与文中图的位置一一对应。

建议在发布前就明确：
- 第 1 个 token 对应哪一幅图
- 第 2 个 token 对应哪一幅图
- 每幅图的类型与核心信息是什么

### G. 逐个生成图

默认策略：现场生成。

对每个 token：
1. 判断图类型（架构图、流程图、对比图、飞轮图等）
2. 跳转到 `lark-whiteboard` 对应 route
3. 生成 diagram 产物
4. 渲染预览检查
5. 用 `whiteboard +update` 写入

### H. 逐个验收

每写完一个 token 就做最小验收：
- 缩略图能下载
- 不再是 blank board
- 必要时 raw query 有节点

## 发布后总验收

至少做以下五类检查：

### 1. 文档对象检查
- `docs +fetch` 中 whiteboard token 数量与预期一致
- whiteboard block 顺序没有错位

### 2. 结构检查
- 目标栏目顺序符合预期
- 指定文章仍在正确栏目下
- 标题层级没有漂移
- 没有明显重复段落或正文残段

### 3. 旧内容保护检查
- 本应保留的已有文章标题没有变化
- 本应保留的已有正文没有被改写
- 本应保留的结尾、配图说明和 whiteboard 位置没有被移动

### 4. 图像缩略图检查
- 使用 `docs +media-download --type whiteboard`
- blank board 通常文件很小、且多个空板大小一致
- 正常板通常明显更大

### 5. 原始节点检查
- `whiteboard +query --output_as raw`
- 正常应返回 `nodes`
- 空板通常返回 `whiteboard is empty`

> 只要结构检查不通过，或发现覆盖了用户线上手动修改，就不要继续叠加下一轮局部更新；先止损，再切换到排障或整段重建。

## 失败回退策略

- 文档已发布但图没回填：不要宣布完成，继续逐板修复
- 某个 whiteboard 写失败：记录 token、报错、当前图类型，再进入排障
- 多图发布时，始终按 token 顺序处理，避免 token 与图内容错配
- 发现结构异常时，停止继续做 `replace_all` / 大范围 `replace_range`
- 如果发现本次变更会覆盖用户线上手动修改，立即停止继续 update，重新 fetch 当前线上版本并改用新的边界方案
- 改为准备 canonical markdown、划定保留区和重建区，再执行重建
