---
name: feishu-to-wechat-prep
description: 把飞书正文或本地正文转化为“微信公众号可发布格式”的前置内容整理 skill。包含抓取线上正文、把特定的流程式代码块转为核心流程图图片、自动补齐 WeChat 必须的 frontmatter 与图片要求，最终输出 `*_wechat.md`，供后续用 wechat-draft-publisher 发布。
---

# feishu-to-wechat-prep

把正文内容（来自飞书或本地）自动转化为“微信公众号草稿箱可发布格式”的前置内容整理编排 skill。

## What this skill does

- 提供“飞书文档/wiki链接”或“本地 markdown 文件”作为双向入口。
- 如输入是飞书，通过底层 `lark-doc` 自动抓取当前线上正文（强制作为唯一事实源）。
- 检测核心的“纵向多步流程”或“横向对比关系”等结构化表达（如代码块里的 `text` / `Mermaid` / 特殊文字列表）。
- 调用 Python Pillow 将这些核心结构本地渲染为 PNG 图片资源。
- 复用 `wechat-draft-publisher` 的检查要求，为新稿自动补齐 frontmatter (`title`, `cover`)。
- 最终产出 `*_wechat.md` 文件以及对应的图片，供后续安全发布。

## 适用场景与限制

- 这个 skill **只做内容改造，不做实际发布**；它产出的 Markdown 应该交给 `wechat-draft-publisher` 走 `preflight` -\> `publish`。
- 不追求全自动理解任意类型的 Diagram，当前支持两类高频结构：“多步流程（纵向）”与“三段关系（左中右）”。
- 默认采用“只转核心图”策略（`--core-diagrams-only`），保留原始排版与内容。

## 为什么不在 publish 环节做？

`wechat-draft-publisher` 提供了一套稳定的本地 markdown 验证与发布 API 隔离（Draft-only guarantee）。如果在那个环节隐式做复杂的“抓取远端内容”、“排版变换”、“图片渲染”，不仅会破坏其独立验证职责，还会导致排障困难。把改造过程隔离到独立前置编排 skill 里，输出产物后再用基础 skill 校验，是最安全的。

## Workflow

1. 获取输入：调用 `scripts/prepare_wechat_article.py`。
2. 读取正文：如果是飞书 URL，走 `lark-cli docs fetch`；如果是本地文件，直接读取。
3. 渲染识别：扫描正文特征，将可转化的结构转成图片并存盘。
4. 重构正文：插入 `![]()`，拼接前端 frontmatter。
5. 生成输出：输出到 `--output-file`，并在 `data/runs/` 保存结构化记录，方便 debug 为什么没转图。

## Usage 示例

```bash
# 从本地文章准备微信稿
python scripts/prepare_wechat_article.py \
  --source-file "fanto_article_03_prompt_bridge.md" \
  --title "Prompt 到底是什么？" \
  --cover "./board2_render.png" \
  --output-file "fanto_article_03_wechat.md"

# 从飞书文档/wiki准备微信稿（使用 lark-cli 底层能力抓取）
python scripts/prepare_wechat_article.py \
  --feishu-doc "https://my.feishu.cn/wiki/xxxxxx" \
  --cover "./board2_render.png" \
  --output-file "fanto_article_from_feishu_wechat.md"
```

生成完毕后，推荐执行：
```bash
python ../wechat-draft-publisher/scripts/preflight_check.py --file "fanto_article_03_wechat.md"
python ../wechat-draft-publisher/scripts/publish_article.py --file "fanto_article_03_wechat.md"
```