---
name: obsidian-llm-wiki
description: Maintain the specific Obsidian LLM wiki at D:\wiki from any working directory. Use when the task is to ingest sources into D:\wiki, answer from that vault, archive reusable outputs there, or lint and maintain its structure.
---

# Obsidian LLM Wiki

## Target vault

This skill always targets the same vault:

- `D:\wiki`

Use this skill when the task is to work on that vault, even if the current session was opened somewhere else.

## Use this skill when

- ingesting a new source into `D:\wiki`
- answering a question from knowledge already stored in `D:\wiki`
- archiving a reusable answer into `D:\wiki\wiki\outputs\`
- linting or maintaining the structure, links, metadata, navigation, or page quality of `D:\wiki`

## Do not use this skill when

- editing markdown that is unrelated to `D:\wiki`
- working on another Obsidian vault
- working on a normal code repository that only happens to contain markdown files
- the task is generic writing rather than vault maintenance, ingest, query, or lint work

## What this skill does

This skill is a **global entrypoint** for the wiki workflow. It should make Claude behave as if it were operating from the vault itself even when the session started somewhere else.

That means:

- always target `D:\wiki` explicitly
- use absolute paths instead of assuming the current working directory is the vault
- follow the vault's existing ingest / query / lint rules
- reuse the vault's live files and scripts instead of redefining the workflow here

## Source of truth

Always defer to these live files in `D:\wiki`:

- `D:\wiki\CLAUDE.md` — vault operating manual
- `D:\wiki\index.md` — first-read navigation for query work
- `D:\wiki\log.md` — append-only operation log
- `D:\wiki\templates\source-template.md` — source-page scaffold
- `D:\wiki\scripts\feishu_ingest.py` — canonical Feishu ingest path

If this skill and the vault files ever diverge, trust the vault files.

## Global-use rule

Do **not** assume the current directory is `D:\wiki`.

When using this skill from anywhere else:

- read files via absolute paths under `D:\wiki`
- write changes back to absolute paths under `D:\wiki`
- treat `D:\wiki` as the working knowledge base even if the surrounding session is for another folder
- avoid using relative paths like `wiki/...`, `raw/...`, or `index.md` unless the tool is already explicitly pointed at `D:\wiki`

## Action priority

Follow this order instead of guessing:

1. **Workflow-sensitive task** → read `D:\wiki\CLAUDE.md`
2. **Query / answer from the vault** → read `D:\wiki\index.md` first
3. **Feishu ingest** → use `D:\wiki\scripts\feishu_ingest.py`
4. **Meaningful ingest or lint change** → update `D:\wiki\index.md` and `D:\wiki\log.md` when needed

## Core rules

- Prefer updating existing pages over creating overlapping pages.
- Keep filenames stable.
- For Feishu ingest, preserve the original source title / filename.
- Preserve the boundary between source-backed facts and your synthesis.
- Do not casually rename raw files, source pages, or asset folders.
- Treat this as a reusable vault workflow, not a session-local convention tied to one directory.

## Common request → action map

### Ingest a new source

- Read `D:\wiki\CLAUDE.md`
- Identify source type
- If Feishu: run `D:\wiki\scripts\feishu_ingest.py`
- Confirm raw file and assets landed under the original title in `D:\wiki\raw\` and `D:\wiki\raw\assets\`
- Review / complete the generated source page in `D:\wiki\wiki\sources\`
- Add concept / entity pages only if the source adds durable reusable knowledge
- Update `D:\wiki\index.md` and `D:\wiki\log.md` if the vault changed materially

### Ingest a Feishu document

Use the existing script, because it already handles the established workflow:

- `lark-cli docs +fetch`
- original title preservation
- `D:\wiki\raw\assets\<原标题>\` media layout
- `+media-download` with `+media-preview` fallback
- mechanical normalization without changing meaning
- source-page scaffolding

After that, finish the higher-level synthesis manually if needed.

### Answer using the vault

- Read `D:\wiki\index.md` first
- Navigate through `D:\wiki\wiki\sources\`, `D:\wiki\wiki\concepts\`, and `D:\wiki\wiki\outputs\`
- Answer from the wiki, not from a single raw file unless the user wants source detail
- Separate supported facts, synthesis, and uncertainty
- If reusable, archive to `D:\wiki\wiki\outputs\`

### Lint the vault

Check for:

- broken or missing wikilinks
- stale navigation in `D:\wiki\index.md` or `D:\wiki\wiki\Home.md`
- weak source coverage on concept pages
- duplicated pages caused by naming drift
- source pages missing provenance or image-sync status
- confidence / review-needed markers that no longer fit

Record meaningful lint work in `D:\wiki\log.md`.

## When this skill should trigger

Examples:

- “不管我当前在哪个目录，都按 D:\wiki 的规则 ingest 这篇飞书文档”
- “基于 D:\wiki 这个 vault 回答问题”
- “把这个答案归档到 D:\wiki 的 outputs”
- “lint 一下 D:\wiki”
- “把这篇微信公众号文章纳入 D:\wiki”
