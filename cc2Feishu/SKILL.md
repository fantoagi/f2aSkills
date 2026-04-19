---
name: cc2Feishu
description: 把内容发布到飞书文档并自动补齐白板配图的发布编排 skill。当用户需要新建或更新飞书文档、把 markdown/草稿发布成飞书文档、自动插入 whiteboard 配图、发布后校验 whiteboard 是否非空，或排查 blank whiteboard 问题时使用。
---

# cc2Feishu

> 发布到飞书不是只把正文写进去；正文、whiteboard 占位、逐个回填、发布后校验，四步都完成才算交付。

## 开始前必读

1. 先读取 `../lark-shared/SKILL.md`
2. 再读取 `../lark-doc/SKILL.md`
3. 如需画图或回填 whiteboard，读取 `../lark-doc/references/lark-doc-whiteboard.md` 和 `../lark-whiteboard/SKILL.md`

## 硬约束

- **更新已有飞书 / wiki 文档时，当前线上 `docs +fetch` 内容是唯一事实源。**
- **memory、旧本地 markdown、历史 rebuild 文件、上一次发布时生成的中间稿都只能作为参考，不是权威源。**
- **如果用户可能手动改过飞书文档，任何 update 前都必须重新 fetch 当前线上版本，不能沿用旧结构。**
- **新增文章 / 新章节默认 append-only / insert-only，不改变已有文章的结构和正文。**
- **除非用户明确要求修改旧文章，否则不要重排旧标题、删旧段落、替换旧结尾、移动旧配图。**
- **`overwrite` 不是默认路线；只有局部更新已不安全且最小重建边界已明确时才能使用。**
- **禁止直接拿旧的总稿或历史 rebuild 文件覆盖当前线上全文。**

## 这个 skill 做什么

这是一个**发布编排 skill**，不替代底层 `lark-doc` / `lark-whiteboard`：
- 文档创建 / 更新：复用 `lark-cli docs +create` / `lark-cli docs +update`
- 白板内容生成 / 写入：复用 `lark-cli whiteboard +update` 和 `lark-whiteboard` 的正式路线
- 本 skill 负责把这些动作串成一条稳定流程

## 适用输入

支持两种入口：
- **本地文件驱动**：用户提供 markdown 文件、章节草稿、diagram/DSL 文件路径
- **对话内容驱动**：用户只提供主题、正文要点、目标位置，由 Claude 现场整理发布内容

详细约定见：
- `references/cc2feishu-inputs.md`
- `references/cc2feishu-workflow.md`

## 主 Workflow

### Step 0：确认身份、目标、输入来源和事实源

先确认：
- 是创建新文档，还是更新已有文档
- 目标是 `/docx/`、`/doc/`、`/wiki/` 还是 folder/wiki-space
- 输入来自本地文件还是对话内容
- 这次是否需要配图 / whiteboard
- 如果是 update，用户是否最近手动修改过当前文档、哪些现有内容必须保留

> wiki URL 不能直接当 doc token，用 `lark-doc` 的 wiki 解析流程先拿真实 `obj_token`。

如果是更新已有文档：
- 先用 `docs +fetch` 读取当前线上版本
- 以 fetch 回来的标题层级、章节顺序、文章边界、whiteboard 位置作为本次唯一基线
- 明确本地稿只用于参考新内容，不可默认替代当前线上正文

### Step 1：整理发布内容

- 本地文件驱动：读取用户给的 markdown / 草稿文件，但只把它当作新内容草稿或参考素材
- 对话内容驱动：先整理出 Lark-flavored Markdown，再发布
- 更新已有文档时，准备发布内容必须由“当前线上 fetch 内容 + 本次新增内容”现场整理出来
- 正文中凡是涉及架构、流程、关系、时间线、对比、因果等结构内容，默认要在对应段落后插入 `<whiteboard type="blank"></whiteboard>`

### Step 2：决定 create 还是 update

- 新文档：走 `docs +create`
- 已有文档：先做 preflight impact check，再判断走**局部修补模式**还是**整段重建模式**

#### Preflight impact check

发布前先基于当前 fetch 结果检查：
- 本次更新会触达哪些标题范围
- 会不会改动已有文章正文、结尾、配图说明或 whiteboard 位置
- 是否存在必须保留且不可覆盖的对象区域

只要发现本次修改会影响已有文章，而用户又没有明确要求修改旧文章：
- 立即停止继续 update
- 改用 append / insert 方案，或重新选择更小的边界

#### 局部修补模式

仅适用于：
- 小范围文本调整
- 单节增删
- 少量新增 whiteboard
- 新增文章 / 新章节的 append-only / insert-only 更新
- 能用纯文本稳定定位修改范围

处理要求：
- 优先使用 `append` / `insert_after` / `insert_before` / `replace_range` 等局部模式
- 新增文章默认只追加，不改已有文章结构和正文
- 每次局部修改后立即 `docs +fetch` 验证
- 只要结构出现异常，就停止继续叠加局部替换

#### 整段重建模式

命中以下任一信号时，停止继续做局部修补，改为准备一份规范化 markdown 源后一次性重建目标区域：
- 连续两次局部替换后，`fetch` 结果仍异常
- 章节顺序漂移、重复段落、正文残段混入其他栏目
- 需要跨多个章节做大面积改写
- 现有区域已经无法用小范围纯文本安全定位

处理要求：
- 明确重建区边界，只重建可重建区域
- canonical markdown 必须从**当前线上 fetch 版本**整理，而不是从旧本地稿逆推出
- 必要时使用 `overwrite`
- `overwrite` 不是默认路线，而是局部修补已不可靠时的受控回退路径
- 不要直接拿旧的总稿或历史 rebuild 文件覆盖当前线上全文

### Step 3：执行文档发布并记录返回值

执行后必须记录：
- `doc_id`
- `doc_url`
- `data.board_tokens`（如果本次创建了 whiteboard）
- 本次采用的是局部修补模式还是整段重建模式
- 哪些对象范围被保留未改

只把 blank whiteboard 插进文档还不算完成。

### Step 4：逐个生成并回填 whiteboard

默认策略：**现场生成图**。

按 whiteboard token 顺序逐个处理：
1. 判断图类型
2. 读取 `lark-whiteboard` 对应路线
3. 生成 diagram 产物
4. 用 `whiteboard +update` 回填到对应 token
5. 一个板成功后，再处理下一个

> 不要把 whiteboard 渲染成 PNG 再插入文档代替；这条路不合法。

### Step 5：发布后校验

发布完成后至少做以下校验：
1. `docs +fetch` 检查 whiteboard token 数量是否符合预期
2. `docs +media-download --type whiteboard` 下载缩略图，确认不是 blank board
3. 必要时 `whiteboard +query --output_as raw`，确认返回节点而不是 `whiteboard is empty`
4. 结构验收：目标栏目顺序、文章标题层级、指定文章位置、重复段落/残段、whiteboard 位置都符合预期
5. 检查本次更新没有改写本应保留的已有文章内容

### Step 6：失败时进入排障

常见故障包括：
- 文档里只有 blank whiteboard，占位成功但未回填
- wiki token / doc token 用错
- 误用普通图片代替 whiteboard
- whiteboard live update 报错后，文档里仍保留空板
- 连续 `replace_range` / `replace_all` 后结构漂移
- 把 `docs +fetch` 返回的 `<whiteboard token="..."/>` 当成可回写内容
- 旧本地稿覆盖了用户后来的线上手动修改

详见：`references/cc2feishu-troubleshooting.md`

## 关键规则

- **创建 blank whiteboard ≠ 完成配图**
- **whiteboard 必须逐个回填，不要只发布正文**
- **发布后必须做对象级校验，不凭肉眼猜**
- **发布后必须做结构验收，结构异常时先止损，不要继续叠加修改**
- **`docs +fetch` 返回的 `<whiteboard token="..."/>` 只用于识别和验收，不可直接回灌到更新 markdown**
- **更新已有文档时，先 fetch 当前线上版本，再决定怎么改**
- **新增文章默认只追加，不改已有文章结构和正文**
- **优先复用已有 lark skills，不要在这里重写底层 API 教程**
- **写入/删除前遵守 `lark-shared` 的确认和安全规则**

## 常用命令骨架

```bash
# 新建文档
lark-cli docs +create --title "<title>" --markdown @<content.md> --as user

# 更新已有文档
lark-cli docs +fetch --doc "<doc_id_or_url>" --as user
lark-cli docs +update --doc "<doc_id_or_url>" --mode append --markdown @<content.md> --as user

# 下载 whiteboard 缩略图做验收
lark-cli docs +media-download --type whiteboard --token <board_token> --output "./preview" --overwrite --as user

# 查询 whiteboard 原始节点
lark-cli whiteboard +query --whiteboard-token <board_token> --output_as raw --as user
```

具体编排、输入约定、排障规则见 references/。
