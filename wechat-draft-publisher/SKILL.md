---
name: wechat-draft-publisher
description: Stable draft-only WeChat Official Account publisher for Markdown articles. Use when the user wants to publish a local Markdown file to 微信公众号草稿箱 with preflight checks, preview, and reliable error reporting.
---

# wechat-draft-publisher

Publish a local Markdown article to **WeChat Official Account draft box only** with a stable API-first flow.

## What this skill does

- Validates article structure before publish
- Verifies credential availability before publish
- Renders preview HTML for inspection
- Publishes to **draft box only** via `wenyan`
- Stores local run records for debugging and traceability
- Surfaces actionable errors for common WeChat failures

## Guarantees

- **Draft only**: this skill never auto-sends or mass-publishes
- **API first**: this skill uses the official WeChat API path through `wenyan`
- **No TOOLS.md parsing**: credentials come from explicit env vars or a skill-local `.env`

## Skill location

- Skill root: this skill directory
- Runtime data: `./data`

## First-time setup

### 1. Install wenyan CLI

```bash
npm install -g @wenyan-md/cli
```

### 2. Configure credentials

Recommended: create a skill-local `.env` file at:

```bash
<skill-root>/.env
```

Add:

```bash
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
```

You can also export them in the current shell or override with `--env-file /path/to/.env`.

### 3. Confirm the current machine IP is whitelisted

In WeChat Official Account backend:
- 设置与开发
- 基本配置
- IP 白名单

## Markdown requirements

Your article should contain frontmatter like:

```markdown
---
title: 文章标题
cover: ./assets/cover.jpg
---

# 正文
```

Recommended fields:
- `title` required
- `cover` strongly recommended
- `author` optional
- `source_url` optional

If `cover` is missing, the publish flow can fall back to the first body image. If neither exists, preflight will fail.

### Style settings

Default style settings are stored at:

```bash
<skill-root>/data/settings.json
```

Inspect current defaults:

```bash
python scripts/auth_manager.py style-show
```

Set default style:

```bash
python scripts/auth_manager.py style-set --theme lapis --highlight solarized-light
```

Clear persisted style overrides and fall back to built-in defaults:

```bash
python scripts/auth_manager.py style-clear
```

### Style when calling the skill

If you are invoking the skill directly, specify the style combination in the call itself for a one-off run.

Example intent:

```text
用 wechat-draft-publisher 发布 /path/to/article.md，theme=orangeheart，highlight=solarized-dark
```

Equivalent script-level commands:

```bash
python scripts/render_preview.py --file /path/to/article.md --theme orangeheart --highlight solarized-dark
python scripts/publish_article.py --file /path/to/article.md --theme orangeheart --highlight solarized-dark
```

Known working values:
- themes: `default`, `lapis`, `orangeheart`
- highlights: `solarized-light`, `solarized-dark`

Precedence order:
1. call-time `theme` / `highlight`
2. saved defaults in `<skill-root>/data/settings.json`
3. built-in defaults

`style-set` is for persistent defaults. Call-time `theme` / `highlight` are for a single invocation and do not modify `data/settings.json`.

## Commands

### Check credential status

```bash
python scripts/auth_manager.py status
```

### Validate article before publish

```bash
python scripts/preflight_check.py --file /path/to/article.md
```

### Render preview HTML only

```bash
python scripts/render_preview.py --file /path/to/article.md
```

### Publish to WeChat draft box

```bash
python scripts/publish_article.py --file /path/to/article.md
```

Optional flags:
- `--theme lapis`
- `--highlight solarized-light`
- `--env-file path/to/.env`
- `--app-id your_app_id`
- `--skip-preflight`

If `--theme` or `--highlight` are omitted, the scripts use `<skill-root>/data/settings.json` and then fall back to built-in defaults.

## Recommended Claude workflow

### No API yet

1. Run preflight for local article checks
2. Render preview HTML locally
3. Stop there until AppID/AppSecret are available

### Publish-ready

1. Create `<skill-root>/.env`
2. Optionally set defaults with `python scripts/auth_manager.py style-set --theme lapis --highlight solarized-light`
3. Verify with `python scripts/auth_manager.py status`
4. Run preflight
5. Publish to draft box

## Common failures

### Missing title
- Add `title` in frontmatter

### Missing cover and no body image
- Add `cover` in frontmatter or at least one image in article body

### Invalid credentials
- Recheck `WECHAT_APP_ID` and `WECHAT_APP_SECRET`
- Run `python scripts/auth_manager.py show-location` to see the default `<skill-root>/.env` path

### No API credentials yet
- You can still run preflight and preview locally
- Publishing to the WeChat draft box remains unavailable until credentials are configured

### IP not in whitelist
- Add the current public IP to WeChat backend whitelist

### Broken local image path
- Fix the file path before publish; preflight will identify bad local paths

## Output artifacts

Publish runs are saved under:

- `data/runs/*.json`
- `data/last_success.json`
- `data/last_preview.html`

These files help with debugging and replay.
