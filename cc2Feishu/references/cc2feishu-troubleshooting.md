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
