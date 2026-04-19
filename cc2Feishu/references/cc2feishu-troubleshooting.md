# cc2Feishu Troubleshooting

## 1. 文档里出现 whiteboard，但显示为空白

### 症状
- `docs +fetch` 能看到 `<whiteboard token="..."/>`
- 阅读态里图是空白
- 缩略图下载后多个板大小几乎一致且很小

### 原因
通常是：
- 只创建了 blank whiteboard，占位成功但没回填
- whiteboard 回填失败，但文档 block 仍保留

### 处理
1. 用 `docs +fetch` 确认 token 列表
2. 用 `docs +media-download --type whiteboard` 下载缩略图
3. 用 `whiteboard +query --output_as raw` 检查是否为空
4. 找到对应 token 后重新回填，不要只改正文

## 2. wiki 链接能打开，但更新命令失败

### 原因
wiki token 不是实际 doc token。

### 处理
先按 `lark-doc` 的 wiki 解析流程获取真实 `obj_token`，再进行 create/update/fetch。

## 3. 图已经做出来了，但写入 whiteboard 失败

### 处理链路
1. 保留当前图源文件和 token 映射
2. 先做 dry-run
3. 若 live update 失败，记录报错和 token
4. 下载当前缩略图确认板是否仍为空
5. 必要时 query raw 节点判断是否真的写入了对象

### 经验规则
- 不能只看 dry-run 成功就认为发布完成
- 必须以 live update 结果 + 缩略图 / raw query 双重验证为准

## 4. 文档里图数对不上

### 原因
- 插入的 `<whiteboard type="blank"></whiteboard>` 数量与预期不一致
- whiteboard token 与图意图顺序错位

### 处理
- 重新建立“段落位置 → whiteboard token → 图类型”的映射表
- 坚持按 token 顺序逐个回填

## 5. 误用普通图片代替 whiteboard

### 风险
- 用户后续不能在飞书里继续编辑图
- 不符合 `lark-doc` / `lark-whiteboard` 的正式流程

### 正确做法
- 结构图、流程图、对比图、飞轮图等应走 whiteboard block
- 普通图片只用于非结构化插图，不用于替代 whiteboard 图表

## 6. 反复 replace_range 后文档结构漂移

### 症状
- 章节顺序漂移
- 出现重复段落
- 删除后仍残留正文碎片
- whiteboard 非空，但整篇结构已经错乱

### 原因
- 在已经变动过的文档上继续叠加 `replace_range` / `replace_all`
- 修改范围无法再被纯文本稳定定位
- 一边发现结构异常，一边继续叠加新的局部更新

### 处理
1. 立即停止继续做 `replace_all` / 大范围 `replace_range`
2. 抽出一份新的 canonical markdown 作为目标正文
3. 选择保留区与重建区边界
4. 重建区内 whiteboard 全部重新创建并重新回填
5. 用 `fetch + 缩略图 + raw query` 三类校验全部通过后再结束

### 经验规则
- 结构异常时，先止损，不要继续赌下一次局部替换会修好它
- whiteboard 验收通过，不等于文档结构也正确

## 6.1 新增文章被插到了错误位置

### 症状
- 新文章出现在整篇文档末尾，而不是目标栏目末尾
- 文章被插到了 `03｜能力模块 / 方法论` 之后或其他错误栏目下
- 标题本身是对的，但栏目归属不对

### 原因
- 把“append 到文档末尾”误当成“追加到目标栏目末尾”
- 发布前没有从当前 `docs +fetch` 结果里明确目标栏目边界
- 没有先确认“目标栏目最后一篇现有文章”和“下一栏目标题”

### 处理
1. 重新 `docs +fetch` 获取当前线上结构
2. 明确目标栏目标题、目标栏目最后一篇现有文章、下一栏目标题
3. 优先改用 `insert_before` 下一栏目标题或 `insert_after` 目标栏目最后对象
4. 发布后再次验证标题是否位于正确栏目内部

### 经验规则
- “栏目末尾追加”默认不是 `append`
- 只有当“文档末尾 = 目标栏目末尾”被明确验证时，才能把 `append` 当安全路线

## 6.2 流程式代码块没有转成 whiteboard

### 症状
- 线上正文里还能看到 Mermaid、ASCII 箭头流程或其他流程式 fenced code block
- 本该是图的位置显示成代码块
- 文档里可能没有新 whiteboard token，或 token 数量少于预期

### 原因
- 发布前只识别了“需要配图”，但没有把流程式代码块强制切到 whiteboard 路线
- 只发布了正文，没有完成 blank whiteboard → token 映射 → 回填链路

### 处理
1. 从草稿里找出所有结构性代码块 / 流程片段
2. 在对应位置插入 `<whiteboard type="blank"></whiteboard>`
3. 记录返回的 `board_tokens`
4. 用 Mermaid / DSL / 正式 whiteboard 路线逐个回填
5. 发布后确认代码块没有残留，且 whiteboard 非空

### 经验规则
- 结构性代码块不是“正文样式”，而是“待转换的图源”
- 只要代码块还留在线上正文里，就说明图表交付还没完成

## 6.3 修复时先插入后删除，导致重复块

### 症状
- 同标题文章在全文中出现 2 次或更多次
- 其中一块位置正确，另一块残留在旧位置
- 删除时报 selection 匹配不唯一

### 原因
- 在未确认旧块边界前，先插入了一份新的整块内容
- 发布前缺少同标题重复保护检查
- 发生结构异常后仍继续叠加局部替换

### 处理
1. 先 `docs +fetch` 统计同标题出现次数并定位每一块附近锚点
2. 先决定保留哪一块，再删除、移动或重建另一块
3. 若删除范围已不唯一，补充更长的唯一锚点，不要继续盲删
4. 删除或移动后再次验证标题出现次数恢复正常

### 经验规则
- 修复重复问题时，先辨认、后动作，不要先再插一份
- “先插后删”只能在边界完全唯一且回退方案清楚时使用；默认不采用

## 7. 出现 `[WARNING:BOARD_TOKEN_NOT_SUPPORTED]`

### 含义
你把不支持回写的 whiteboard token 形式放进了新的 markdown 源。

### 常见成因
- 把 `docs +fetch` 返回的 `<whiteboard token="..."/>` 当成可写内容直接回灌
- 试图在整段重建时原样复用 fetch 出来的 whiteboard 标签

### 正确处理
- 把 fetch 输出当作只读对象清单，不当作可写正文源
- 若要保留已有 whiteboard，就避开它所在区域不覆盖
- 若无法安全保留，就承认该区域需要重建，重新拿新的 `board_tokens`

## 8. 旧本地稿覆盖了用户线上手动修改

### 症状
- 用户明明刚在飞书里手动改过标题、章节边界或正文，更新后这些改动又消失了
- 原本已经删掉的章节被旧稿重新加回来了
- 旧文章的结尾、配图位置、whiteboard 顺序被恢复成历史版本

### 原因
- 更新时没有先读取当前线上 `docs +fetch` 版本
- 把旧本地 markdown、历史 rebuild 文件或记忆内容当成了当前权威源
- 直接用旧总稿 `overwrite` 了线上全文或大范围区域

### 处理
1. 立即停止继续叠加 update
2. 重新 `docs +fetch` 获取当前线上版本并确认最新边界
3. 明确哪些内容是用户刚手动改过、必须保留的
4. 改用 append / insert / 更小范围 replace 的方案
5. 若确实需要重建，只能从当前线上版本整理 canonical markdown，并圈定最小重建区

### 经验规则
- 更新已有文档时，当前线上版本永远优先于旧本地稿
- 本地文件和记忆只能帮助回忆文案，不能替代线上最新事实

## 9. 什么时候才算完成

以下条件都满足才算完成：
- 正文已发布
- 预期 whiteboard 都已创建
- 每个 whiteboard 都已回填
- 缩略图不再是 blank board
- 必要时 raw query 返回非空节点
- 文档结构检查通过
- 本应保留的已有线上内容没有被意外覆盖
