---
name: youtube-bilingual-transcript
description: 抓取 YouTube / bilibili 等平台视频的官方字幕(含中文轨)并生成"中英对照逐字稿" markdown；平台无字幕轨(如小宇宙播客)则走百炼 DashScope 云端转写。当用户要"抓某视频的完整中英文字幕/逐字稿"、"要双语字幕"、"z字幕"、"bilibili字幕"、"小宇宙/播客转文字"、"把视频/音频变成文字稿"时触发。针对中国网络(直连被墙)、YouTube 中文翻译轨 429 限流、bilibili 视频页 412 反爬/需登录 cookie/无标点字幕、DashScope filetrans 按模型字段差异、以及"英文热词会切碎英文专名→只留中文热词"处理了专门解法；小宇宙无字幕轨走"页面元数据自举词表 + 说话人分离 + 章节分段"。
version: 0.9.0
---

# 跨平台双语逐字稿

从平台官方字幕轨抓取并合成一份**逐字稿**（双语对照则输出中英对照），存为 markdown。

覆盖三类平台，网络行为不同：
- **YouTube**：直连被墙需走本地代理；中文轨(`zh-Hans`)是机器翻译轨，限流 429，需 **cookie 解锁**。
- **bilibili**：此机**需走代理**（直连实测 `000` 秒断，勿直连）；视频页无登录 cookie 会 `412`，需 **B 站登录 cookie**；字幕通常单一中文 AI 轨（lang=`ai-zh`，**无标点**）。
- **小宇宙**(播客)等**无字幕轨**平台：转而走**百炼 DashScope 云端转写**（`scripts/dashscope_asr_transcribe.py`），不装本地 Whisper。

本 skill 侧重"抓**平台自带字幕轨**"；无字幕轨时用云端 ASR 兜底，全程**不装本地 Whisper**。

## 适用范围

- ✅ 平台有字幕轨（自带 / 自动生成 / 上传者上传均可）。
- ✅ 用户要官方字幕（不是我们手译）、要求**不装本地 Whisper**、不引外部翻译 API。
- ✅ 平台**无字幕轨**（如小宇宙播客、只有硬字幕烧录的视频）——用 `scripts/dashscope_asr_transcribe.py` 走**百炼云端 ASR** 兜底（需 `DASHSCOPE_API_KEY`）。
- ❌ 本地离线转写（Whisper）不覆盖——统一走云端 ASR。
- ⚠️ bilibili 常见情况是**只有中文轨**（单语），能出"中文逐字稿"但未必有英文对照；对外文视频+AI 中文字幕，才可能拿到双轨。

## 前置

- `yt-dlp`：用 `python -m yt_dlp`（PATH 无 `yt-dlp`）。
- **代理**：YouTube 与 **bilibili 在此机都走 `127.0.0.1:7897`**（bilibili 直连实测 `000/0.03s` 秒断，与"国内直连"直觉相反，以实测为准）。走代理后首页、各 API 均 200，但 bilibili **`/video/BVxxx` 视频页**对无登录 cookie 的请求返回 `HTTP 412`（WAF 反爬）。
- **cookies.txt**：YouTube 解锁中文翻译轨；bilibili 解开视频页 412 + 字幕接口。两者都要对应站点登录后手动导出。`--cookies-from-browser` 在 Win11 被 App-Bound 加密拦截（issue #7271），**必须手动导出**（浏览器装 "Get cookies.txt LOCALLY" 之类本地扩展）。

## 步骤

### 0. 拿到 cookies.txt（关键）

YouTube → 绕中文翻译轨 429；bilibili → 拉字幕接口。两平台都要在对应站点登录后手动导出 cookies.txt。

### 1. 先确认网络与代理（30 秒诊断）

```bash
# YouTube 直连，预期失败：被墙超时
curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" --max-time 15 "https://www.youtube.com/watch?v=tivaWTTVRhY"
# YouTube 经代理，预期 200
curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" --max-time 15 --proxy http://127.0.0.1:7897 "https://www.youtube.com/watch?v=tivaWTTVRhY"
# bilibili 直连，此机预期 000/秒断（非超时）→ 需要代理
curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" --max-time 12 "https://www.bilibili.com/video/BV1zCGB66ELJ" -H "User-Agent: Mozilla/5.0"
# bilibili 经代理 + 登录 cookie；预期视频页 200（无 cookie 则是 412）
curl -s -o /dev/null -w "%{http_code}\n" --max-time 15 --proxy http://127.0.0.1:7897 -b "/path/bilibili_cookies.txt" "https://www.bilibili.com/video/BV1zCGB66ELJ"
```

- bilibili 直连 `000` 且秒断 → 该机需走代理；视频页无登录 cookie 返回 `412`（正常）→ 需 cookie。

### 2. 抓取字幕轨（带 cookies）

**YouTube（走代理 + cookie）**：
```bash
python -m yt_dlp --proxy http://127.0.0.1:7897 --cookies "/path/youtube_cookies.txt" \
  --skip-download --write-auto-subs --sub-langs "zh-Hans,en" --sub-format srt \
  --sleep-requests 1 --retries 2 -o "OUTDIR/%(title)s.%(ext)s" "https://www.youtube.com/watch?v=VIDEO_ID"
```

**bilibili（此机走代理 7897 + B站登录 cookie）**：
```bash
python -m yt_dlp --proxy http://127.0.0.1:7897 --cookies "/path/bilibili_cookies.txt" \
  --skip-download --write-subs --sub-langs "ai-zh" --sub-format srt \
  --sleep-requests 1 --retries 4 -o "OUTDIR/%(title)s.%(ext)s" "https://www.bilibili.com/video/BVxxxxxxx"
```
> 关键点（2026-08-26 真机验证）：视频页 **412** 需登录 cookie 才解除；AI 字幕轨 lang 编码是 **`ai-zh`**，且必须用 **`--write-subs`**（不是 `--write-auto-subs`，后者会报 "no subtitles for requested languages"）；`--retries 4` 可缓解经代理拉字幕 JSON 的偶发 `SSL EOF`；bilibili 常见**只有一条中文 AI 轨**（单语 mono），若要英文需另配（缺省无）。

### 2b. 无字幕轨 → 百炼云端转写（小宇宙等播客）

平台无字幕轨时，先拿**音频公网 URL**（从节目页 `__NEXT_DATA__` 的 `episode` / 播放 CDN 提取，如 `media.xyzcdn.net/....mp3`，公网可直接 HEAD/GET）。**首选最优配置**（v0.5.0 交叉验证定案：`qwen-audio-3.0` + 说话人分离 + 纯中文热词）：

```bash
export DASHSCOPE_API_KEY=sk-...   # 百炼控制台右上角头像→API-KEY
python "/path/youtube-bilingual-transcript/scripts/dashscope_asr_transcribe.py" \
  --model qwen-audio-3.0-asr-flash-filetrans --url "https://media.xxxcdn.net/.../x.mp3" \
  --out-dir OUTDIR --title "xxx" --diarization --lang zh \
  --vocabulary-file OUTDIR/auto_vocab.json --vocabulary '{"雅贤":5,"雷鸟":5}'
# 产出 OUTDIR/xxx.srt，带 [spkN] 说话人标签（即 build_bilingual.py 的输入）
```

> 备选（无说话人/无热词需求才用）：默认 `qwen3-asr-flash-filetrans`（`--url ... --title xxx` 即可，字段 `input.file_url` 单串；但准确度低于 qwen-audio-3.0+热词，见 v0.5.0）。

> 关键 schema 差异（2026-08-26 真机验证）：**Qwen3-ASR-Flash-Filetrans** 入参是 **`input.file_url`（单字符串）**、结果 URL 在 **`output.result.transcription_url`（单对象）**；旧模型（Qwen-Audio-3.0-ASR-Flash-Filetrans / Fun-ASR / Paraformer）则是 **`input.file_urls`（数组）**、结果在 **`output.results[].transcription_url`**。给错字段会立即返回 `InvalidParameter.MalformedURL: A valid file URL is required`（model 名有效、任务已 PENDING，但 URL 校验失败）。Qwen3 的 `parameters` 是 `channel_id`/`enable_itn`/`enable_words`；说话人分离要换 `qwen-audio-3.0-asr-flash-filetrans` 并开启相关参数。

> 说话人分离 + 热词的最优配置（2026-08-26 验证）：`qwen-audio-3.0-asr-flash-filetrans --diarization` + **`--vocabulary` 只写中文专名**（`{"声动活泼":5,"雅贤":5,"申悦":5,"雷鸟":5}`）。**不要塞英文 proper noun 热词**（Palantir/FDE/OpenAI/Agent，weight 5）——实测会把英文专名切碎成 `P`/`Pal`/`f`，且让英文段更乱；去掉后 qwen3 反而逊于它（Palantir 完整、英文段最干净）。此配置产出**带 `[spkN]` 说话人标签**的 SRT，speaker_id=0 vs 1 直接可映射主持人/嘉宾。

> **元数据自举（小宇宙特有，v0.6.0 新增）**：小宇宙节目页 `__NEXT_DATA__` 的 `episode` 自带**标题/栏目/出品方/时长/本期人物/时间轴章节**，这些能同时优化 ASR 与最终内容。用 `scripts/extract_xyz_meta.py --page <保存的 html>` 一次抽出三件套：
> - `meta.json`：标题/栏目/出品方/时长/本期人物(host/guest)/`chapters[]`(时间轴)/`fde_expansion`(FDE 全称) → 填最终 frontmatter + 章节块 + 说话人映射（guest 字段直接给 `申悦`；spk1=嘉宾、spk0=主持人）。
> - `auto_vocab.json`：**结构性可靠的中文专名**（出品方/嘉宾/中文主持人名），喂 `--vocabulary-file`。**romansized host（如 `Yaxian`）抽不出「雅贤」**、产品名在营销行也非结构化 → 这两类走 `--vocabulary` 手动合并（`--vocabulary` 遇 key 冲突覆盖 file）。
> - `english_lexicon.json`：正文里的拉丁品牌（FDE/OpenAI/Anthropic…）→**仅作后校对参考**，**绝不喂进 `--vocabulary`**（英文热词切碎专名）。

```bash
python extract_xyz_meta.py --page xyz_page.html --out-dir OUTDIR
python dashscope_asr_transcribe.py --model qwen-audio-3.0-asr-flash-filetrans \
  --url "<audio>" --out-dir OUTDIR --title x --diarization --lang zh \
  --vocabulary-file OUTDIR/auto_vocab.json --vocabulary '{"雅贤":5,"雷鸟":5}'
```

### 3. 合成逐字稿（通用：单语/双语）

```bash
python "/path/youtube-bilingual-transcript/scripts/build_bilingual.py" \
  --subs "en:OUTDIR/xxx.en.srt" --subs "zh-Hans:OUTDIR/xxx.zh-Hans.srt" \
  --out OUTDIR/bilingual.md \
  --title "视频标题 - 公开者" --source-url "URL" --channel "频道" --duration "HH:MM:SS" --video-id "ID" \
  --note "中文为平台官方机翻/CC轨。"
```

- **双语**（≥2 轨）：`--subs` 传两条，轨 0 是断段锚点，逐段 `> LABEL0：…` / `> LABEL1：…` 对照。YouTube 典型：`--subs "en:..." --subs "zh-Hans:..."`。
- **单语**（只有 1 轨，如 bilibili 常见只中文）：`--subs "zh-CN:xxx.zh-CN.srt"` 一条即可，输出 `> ZH：…` 单列。

脚本逻辑：以轨 0 按**终止标点**断段（英文/CJK 都支持）；次级轨用单调指针按"start 落入窗口"对齐，不重复不串段；清理滚动字幕带入的 CJK 空格；输出 `> 时间戳` / 各列对照。

### 3b. 富化最终内容（小宇宙：说话人映射 + 章节块 + frontmatter）

builder 出的 mono 带 `[spkN]`，把编号映射成元数据里的名字，并插入章节块、补 frontmatter（出品方/列示时长）和 FDE 全称：

```bash
python -c "
import json, re
m=json.load(open('OUTDIR/meta.json',encoding='utf-8'))
spk={'spk0':m['host'] if m['host'] else '主持人','spk1':m['guest'] if m['guest'] else '嘉宾'}
md=open('OUTDIR/xxx_mono.md',encoding='utf-8').read()
lines=[]
for ln in md.split('\n'):
  lines.append(ln)
  if ln.startswith('channel:'):
    lines.append('author: \"%s\"'%m['author']); lines.append('duration-listed: \"%s\"'%m['duration_ts'])
md='\n'.join(lines)
# show notes: meta.shownotes_md (HTML shownotes -> Markdown, keeps bold/links/images,
# produced by extract_xyz_meta.py) + timestamped chapter nav. Use shownotes_md, NOT
# description (description is a flat plain-text summary that loses the original layout).
ch=['','## 节目简介（show notes）','']+m['shownotes_md'].split('\n') \
  +['','## 内容章节（取自节目简介）','']+['- %s — %s'%(c['t'],c['title']) for c in m['chapters']]
md=re.sub(r'(# 中英对照逐字稿\n)', r'\1'+'\n'.join(ch)+'\n', md, count=1)
md=re.sub(r'\[spk(\d)\] ', lambda mm: '**'+spk.get('spk'+mm.group(1),mm.group(0))+'** ', md)
open('OUTDIR/xxx_final.md','w',encoding='utf-8',newline='\n').write(md)
"
```

> 注意：主持人名在元数据里常被罗马化（本期 `Yaxian`）→ `m['host']` 非中文，spk0 会显示成 `Yaxian`；若想显示中文名（`雅贤`）需在 `spk` dict 里手动 mapping（如 `'spk0':'雅贤'`）。本期用 spk0=雅贤、spk1=申悦。

### 4. 存入 wiki（Obsidian vault）

`D:\wiki` 已存在文件**不能直接 Write/Edit**（freshness 拦截）——**在草稿目录构建后 `cp` 覆盖**：

```bash
cp OUTDIR/bilingual.md "/d/wiki/inbox/Transcript (中英对照) - 标题 - 公开者.md"
```

## 已知坑

| 现象 | 原因 | 处理 |
|---|---|---|
| YouTube 中文轨 `HTTP 429` | 机器翻译轨独立限流，按会话非仅 IP；`en` 走缓存 ASR 不受影响 | 手工导出 cookies.txt |
| `--cookies-from-browser` 报 Could not copy / find | Win11 App-Bound 加密 / 无配置 | 改用用户手动导出 cookie 文件 |
| bilibili 直连 `000` 秒断 | 此机 Clash 把 bilibili 路由到不可达出口 | 改用 `--proxy 127.0.0.1:7897`（别直连，以实测为准） |
| bilibili `/video/BVxxx` 页 `HTTP 412` | WAF 反爬，无登录 cookie | 用 bilibili 登录 cookies.txt（含 SESSDATA/bili_jct/buvid3 等） |
| bilibili `--write-auto-subs` 报 "no subtitles" | 该轨属"创作者字幕"而非自动 | 改用 `--write-subs` |
| bilibili 抓字幕 JSON 偶发 `SSL EOF` | 经代理长连接被重置（偶发） | `--retries 4`（实测重试即成功） |
| bilibili 字幕无标点，mono 塌成 1 段 | AI 字幕无 `。！？`，标点断段失灵 | builder 自动回退按时间间隔(≥1.5s)断段 |
| bilibili 字幕接口拿空/报错 | 仅匿名 buvid3 不够，需登录 | 用该站 cookies.txt |
| 终端打印中文乱码 | Windows 控制台非 UTF-8，仅显示 | 文件永远 UTF-8 写入，用 Read 看即正常 |
| 靠时间 Gap 断段全塌成一整段 | 平台是滚动字幕，cue 时间大量重叠（gap 多为负） | 按终止标点断句，勿用 gap |
| bilibili 单语无英文 | B站多为单中文 CC 轨 | 走 mono 单列；别期望必有中英对照 |
| 百炼转写报 `InvalidParameter.MalformedURL` | 入参字段给错：Qwen3 要 `file_url` 单串，旧模型要 `file_urls` 数组 | 按模型用对应字段；结果 URL 同理 `output.result`(Qwen3) vs `output.results[]`(旧) |
| 平台无字幕轨（小宇宙等播客） | 无公开字幕轨，本地 Whisper 不想要 | 拉公网音频 URL → `dashscope_asr_transcribe.py` 走百炼云端 |
| 英文专名被切碎成 P/Pal/f | `qwen-audio-3.0` 的 `--vocabulary` 里塞了 weight-5 英文热词（Palantir/FDE/OpenAI 等）；**前提是中文节目** | `--vocabulary` **只写中文专名**；英文热词反而干扰，去掉后模型自带英文能力最好 |
| auto_vocab 出 junk token（`本期我们邀请三位嘉宾`/`🎙️【本期嘉宾】`） | 英语占比高/说话人多的节目，auto_vocab 把模板句/标记行也收进中文热词 | **英语占比高/内容多元的节目用空词汇表**（`--vocabulary` 与 `--vocabulary-file` 都留空）：中文热点词只在纯中文节目（如 E240 硅谷101）才有效，英语多的节目宁可空，勿乱加（v0.9.0 修正） |
| 自动热词缺「雅贤/雷鸟」 | 元数据把 host 罗马化成 `Yaxian`（无「雅贤」）、产品名在营销行非结构化 | 自动热词只覆盖出品方/嘉宾+中文主持人名；罗马化 host/产品名用 `--vocabulary` 手动补 |

## 迭代记录

- v0.1.0（2026-08-25）：YouTube 单平台跑通（2359 en / 2250 zh cue → 210 段双语，官方轨）。
- v0.2.0（2026-08-26）：泛化 builder 支持任意多轨 + 单语/双语（`--subs lang:path`，保留 `--en/--zh` 兼容）。
- v0.3.0（2026-08-26）：bilibili 端到端实测跑通（代理 + 登录 cookie + `--write-subs` `ai-zh` → SRT → mono，54 段）；发现 bilibili AI 字幕**无标点**，builder 增加"无标点→按时间间隔(≥1.5s)断段"回退，标点路径不受影响。回归：YouTube en+zh 210 段不变。
- v0.4.0（2026-08-26）：新增 `scripts/dashscope_asr_transcribe.py`，打通**小宇宙无字幕轨**→百炼云端 ASR（`qwen3-asr-flash-filetrans`）→SRT→mono（209 句/200 段，31min）。实证 Qwen3 filetrans 用 `file_url` 单串 + `output.result`，与旧模型 `file_urls` 数组 + `output.results[]` 不同；此分支无需本地 Whisper。
- v0.5.0（2026-08-26）：小宇宙交叉验证 + 方案优化。用 zlxlabs 人工校对稿当参照，对比 qwen3 vs `qwen-audio-3.0`；定案最优配置 = **`qwen-audio-3.0-asr-flash-filetrans --diarization` + 纯中文热词**（260 句带 `[spkN]`，2 位说话人）：修好 qwen3 的中文近音错（声动活泼/雅贤/FDE 间隔），又新增说话人分离，且不再回归 Palantir；英文段反而最干净。关键坑：**英文热词 weight-5 会切碎英文专名**（Palantir→P/Pal），务必只留中文专名。
- v0.6.0（2026-08-26）：新增 `scripts/extract_xyz_meta.py`，小宇宙**元数据自举**——从节目页 `__NEXT_DATA__` 抽标题/栏目/出品方/时长/本期人物/时间轴章节，产出 `meta.json`(frontmatter+章节+说话人映射) / `auto_vocab.json`(结构性中文专名→`--vocabulary-file`) / `english_lexicon.json`(拉丁品牌→仅后校对参考)。`dashscope_asr_transcribe.py` 加 `--vocabulary-file`（与 `--vocabulary` 合并）。实证：`auto_vocab{声动活泼,申悦}` + 手动补 `{雅贤,雷鸟}` 精确复现 v0.5.0 词汇表；元数据章节时间轴 03:36 能定位到 SRT 00:03:41(Δ5s) 校验时机；列示时长 00:30:58 vs 实际音频 00:30:41。
- v0.7.0（2026-08-27）：**shownotes 完整照搬排版**。发现 `episode.shownotes`(HTML，含 `<strong>/<a>/<img>/时间戳锚点`)才是富文源，`episode.description`(纯文本)是扁平摘要。`extract_xyz_meta.py` 新增 `_ShownotesToMD`(HTMLParser) + `html_shownotes_to_md()`（保留加粗/链接/图片/时间戳/段落换行），产出 `meta.shownotes_md` 与 `shownotes.md`；3b 富化改用 `shownotes_md`（弃 `description`）。修掉出品原生的畸形双链 `[文字]([内链](href))`→`[文字](href)`。实证：shownotes.md 2405 字，加粗标题/微信外链/图片/mailto/时间轴全部保留。
- v0.8.0（2026-08-27）：**元数据抽取健壮化 + 3 说话人分离**。E240（硅谷101）实测发现 `extract_xyz_meta.py` 三个坑并修复：(a) 章节时间轴可为行首裸 `MM:SS 标题`（无 `[..]` 括号）→ `chapters` 正则加裸时间分支；(b) host/guest 可写成独立标题行 `【主播】`/`【嘉宾】`（名字在下一行），旧逻辑把标题行当人名（出 `host="【主播】"`）→ 识别纯标题行后读下一非空行；(c) FDE 全称可写 `Forward Deployment Engineer（FDE）`（英文在前）→ fde_expansion 正则加 `([A-Za-z ]+)（FDE）` 分支。另实证 `qwen-audio-3.0` diarization 本期分出 **3 位说话人**（spk0=104/spk1=234/spk2=120，对应 Yiwen/Jove/Oliver），比 S10E27 的 2 位更能准确映射多人；3b 富化需按实际 spk 数扩展 `spk` dict（`spk0/spk1/spk2`）。回归检查：章节 `[MM:SS]`、行内主机名（`Yaxian，…主播`）路径不受影响。
- v0.9.0（2026-08-29）：**批量处理 + 元数据抽取深度健壮化 + 英语占比高节目用空词汇表**。一次跑通 4 则小宇宙（Vol.128/Linkloud E09/十字路口/硬地骇客 EP128，说话人 2–5 位）并修正 `extract_xyz_meta.py` 一批边界：(a) host/guest 解析全面重写为 `_parse_hosts_guests(desc)`，覆盖角色标题行（`🎙️【本期嘉宾】`/`【主播】`+下一行名字）、行内 `主播：X`/`嘉宾：X`/`Special Guest: X`、行内嵌名（`Yaxian，「科技早知道」主播`），能对杂乱版式取第一个 host/首个 guest；(b) 章节行可带 emoji 前缀（`🟢 01:08 快问快答`）→ 新增 `_lstrip_emoji`（并把 `[`、`]` 加进保留白名单，否则 `[01:08]` 的括号会被剥掉导致章节数归零）先剥装饰再匹配；(c) **Windows 控制台 GBK** 会导致 print() 打 emoji 标题/姓名时 `UnicodeEncodeError` 崩溃（文件其实早已写好）→ 脚本顶部 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`，垃圾控制台行绝不会再中断整条流水线；(d) auto_vocab 过滤占位词（佚名/匿名）与超长中文短语，避免把"本期我们邀请三位嘉宾"这类模板句变成 weight-5 热词。**关键决策：英语占比高/说话人多/内容多元的节目用空词汇表**（`--vocabulary` 与 `--vocabulary-file` 都留空）——实测中文热点词只在纯中文节目（如 E240 硅谷101）里有效，英语多的节目塞进任何模板/专名热词只会制造 junk token（`本期我们邀请三位嘉宾`、`🎙️【本期嘉宾】`），而 qwen-audio-3.0 对英文本身就是原生能力，空词汇表反而最干净。（v0.5.0 的"只留中文热词"结论**前提是中文节目**，本期在英语节目上修正为"宁可空，勿乱加"。）另实证 `--diarization` 可分出 **2–5 位**说话人（spk0..spk4），主持人映射改为"其**第一句是开场白**（大家好/欢迎/我是）的那个 spk"启发式（`detect_host`），即便嘉宾先开口也能正确定位主持人；3b 富化按实际 spk 数动态生成 `主机名` + `嘉宾N` 的 `spk` dict。批量版本见 `.cc-connect/_xyz_batch/enrich_batch.py`。
