# 封面图生成 — 完整规范

> 由 `SKILL.md` 按需加载。

## 设计原则

1. **基于文章核心内容生成示意图**，而非纯文字排版或通用占位图。封面应让读者一眼看懂文章在讲什么。
2. **解构清晰、布局合理**，所有内容必须清晰展示，**严禁元素遮挡或重叠**。
3. **优先使用分层/堆叠式布局**（独立的水平条从上到下排列），避免嵌套同心矩形——嵌套矩形会导致内层遮挡外层内容。
4. **左图右文**：左侧放置架构示意图，右侧放置标题、金句、标签等元信息。左右比例约 45:55。
5. **每层独立可读**：层与层之间有明确间距和虚线/箭头连接，每层有左侧色条 + 编号 + 层名 + 组件列表。

## 配色

- 不同层使用不同颜色区分（如绿/蓝/紫/深蓝从外到内），每层左侧 4-5px 色条作为视觉标识
- 核心层（LLM）使用最深颜色 + 白色文字突出
- 文字色用 `#0f172a` / `#475569` / `#64748b`，层级递减

## CDP 环境准备（封面渲染的前置依赖）

封面图从 SVG 渲染为 PNG 需要 Chrome DevTools Protocol 浏览器。**每次写文章前，先确认 CDP 可用**——未确认不得跳过渲染步骤。

**Chrome 启动命令（必须包含 `--remote-allow-origins=*`）**：

```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" \
  --remote-debugging-port=9222 \
  --headless \
  --disable-gpu \
  --no-sandbox \
  --remote-allow-origins=* \
  --window-size=1280,800
```

**关键约束**：
- `--remote-allow-origins=*` **必须加**。Chrome 148+ 的 WebSocket 默认拒绝非浏览器来源，不加则 `websocket.create_connection` 返回 403
- CDP 在 Chrome 148+ 默认绑定 IPv6（`[::1]:9222`），脚本自动探测；curl 测试时优先用 `http://[::1]:9222/json/version`
- Python 依赖：`websocket-client`（`pip install websocket-client`），标准库无此模块

## 生成流程

1. 用 `Write` 工具写入 SVG 文件（如 `cover_<topic>.svg`）
2. 将 SVG 渲染为 PNG，**按优先级依次尝试**：
   - **优先（推荐）**：调用本 skill 自带的固化脚本 `scripts/render_cover.py <svg_path> [png_path]`——此脚本封装了经过 Chrome 148+ 验证的完整 CDP canvas 渲染链路（`file:///` URL → `Page.navigate` → WebSocket 排空事件 → `toDataURL`），一条命令出 PNG，无需手动处理 WebSocket 消息顺序或事件队列
   - **降级 A**：若环境安装了 `cairosvg` 且 Cairo DLL 可用，直接 `cairosvg.svg2png(url=svg_path, write_to=png_path)`
   - **降级 B**：若以上均不可用，手动走 CDP WebSocket 链路。**注意：以下 4 个坑已有脚本规避，手动操作必须逐条对照：**
     1. **不要**用 HTTP 服务器 + `/json/new?url=http://127.0.0.1:PORT`——Chrome 148+ 忽略该 URL，tab 始终停在 `about:blank`
     2. **必须**先开 `about:blank`，再通过 WebSocket 发 `Page.navigate` 到 `file:///` 路径
     3. **必须**在 `Page.loadEventFired` 后排空缓冲事件，再发 `Runtime.evaluate`
     4. **必须**逐条 `send()` 后 `recv()` 匹配 `id` 字段，避免事件消息交叠导致取错响应
3. 渲染完成后清理中间 HTML 文件，保留 SVG 源文件和最终 PNG

## 自检

1. 比例是否为 2.35:1？
2. 元素是否有重叠或遮挡？
3. 各层文字是否完整可读（不小于 10px 等效字号）？
4. 标题、金句、来源标注是否完整？
5. SVG → PNG 渲染是否实际执行？（不可 SVG 写完就宣告完成，必须确认 PNG 文件存在且 > 0 字节）
