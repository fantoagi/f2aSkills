# f2aSkills

A repository for maintaining reusable Claude Code skills.

## Included skills

- `fanto-article-generator` - writes fantoAGI-style articles and spin-offs in plain, conversational Chinese with analogy-first explanations and a fixed article rhythm
- `cc2Feishu` - orchestrates publishing Markdown or drafted content into Feishu docs, inserts and backfills whiteboards, and validates the final result
- `feishu-to-wechat-prep` - prepares Feishu doc content or local text into a "WeChat publishable format", handles diagrams, and organizes standard layout elements
- `wechat-draft-publisher` - publishes local Markdown articles to the WeChat Official Account draft box with preflight checks, preview rendering, and draft-only safeguards
- `youtube-bilingual-transcript` - fetches YouTube / bilibili subtitles (incl. Chinese) into a bilingual side-by-side transcript; for no-subtitle podcasts (e.g. xiaoyuzhou) it drives DashScope cloud ASR with speaker diarization + metadata-bootstrapped Chinese hotwords.
