#!/usr/bin/env python3
"""C2 机械扫描 — 改写版中文质控自动化脚本。

为什么这个脚本存在：
  本脚本把中文稿件的机械语言、语义和渲染检查封装为确定性扫描，
  输出结构化报告，供 v2 分级质控和 legacy 回归使用。

用法：
  # 只扫描改写版中文（C2 标准模式）
  python scripts/c2_scan.py <translated_zh.md>

  # 同时比对英文原文（额外检查数字完整性、反引号成对）
  python scripts/c2_scan.py <translated_zh.md> --original-en <original_en.md>

输出：
  结构化报告到 stdout。包含每道扫描的触发计数、匹配行、命中内容。
  v2 默认将事实、结构、渲染问题作为 BLOCKER，将风格提示作为 WARNING。
  Exit code 0 = 无 BLOCKER；Exit code 1 = 存在 BLOCKER；Exit code 2 = 参数/文件错误。
  使用 --legacy 可恢复 v1 的“核心扫描必须为 0”退出语义。

扫描范围：
  - 代码块（```...```）和 inline code 内的内容自动跳过
  - 纯 markdown 语法行（# 标题、> 引用、| 表格、- 列表）跳过部分检查

依赖：Python 3.8+ stdlib only
"""

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ── 数据结构 ─────────────────────────────────────────────────────────────────

@dataclass
class Hit:
    line: int
    content: str
    match_detail: str  # 命中的具体 pattern 或 context


@dataclass
class ScanGroup:
    id: int
    name: str
    method: str
    hits: list = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.hits)


# ── 辅助函数 ─────────────────────────────────────────────────────────────────

def _lines_outside_code_blocks(text: str) -> list:
    """Return (line_number, content) for lines NOT inside fenced code blocks."""
    result = []
    in_block = False
    for i, line in enumerate(text.split("\n"), 1):
        if line.strip().startswith("```"):
            in_block = not in_block
            continue
        if not in_block:
            result.append((i, line))
    return result


def _strip_inline_code(line: str) -> str:
    """Remove inline code spans (`...`) from a line for scanning."""
    return re.sub(r"`[^`]+`", "", line)


def _is_syntax_line(line: str) -> bool:
    """Check if a line is pure markdown syntax (skip for most checks).

    Only skips empty lines, headings, and table rows.
    Does NOT skip list items (- / *) — list content can contain translation errors.
    """
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("#"):
        return True
    if stripped.startswith("|") and stripped.endswith("|"):
        return True
    return False


# ── 扫描 1：翻译腔句式 ──────────────────────────────────────────────────────

TRANSLATION_TONE_PATTERNS = [
    # Group A: 高频直译
    ("这就是为什么", "This is why 直译"),
    ("这一事实", "the fact that 直译"),
    ("事实证明", "It turns out that 直译"),
    ("关键的洞察", "key insight 直译"),
    ("不仅是关于", "not just about 直译"),
    ("之间的桥", "bridge between 结构隐喻"),
    ("之间的铰链", "hinge between 结构隐喻"),
    ("的纽带", "link between 结构隐喻"),
    ("的桥梁", "bridge between 结构隐喻"),
    # Group B: 英文设问/收尾/占位词直译
    ("是什么？", "英文设问 What's X? 直译"),
    ("整件事就是", "That's the whole thing 直译"),
    ("事情就是这样", "The whole process is like this 直译"),
    # Group C: say+状态码直译
]

# say+状态码 need special regex
SAY_CODE_PATTERN = re.compile(r"说.{0,5}(BLOCK|SHIP|PASS|FAIL)")


def scan_translation_tone(text: str) -> ScanGroup:
    group = ScanGroup(id=1, name="翻译腔句式", method="C2 扫描 1")
    lines = _lines_outside_code_blocks(text)
    for ln, line in lines:
        if _is_syntax_line(line):
            continue
        clean = _strip_inline_code(line)
        # Group A & B: simple substring
        for pattern, explanation in TRANSLATION_TONE_PATTERNS:
            if pattern in clean:
                group.hits.append(Hit(ln, line.strip(), f"'{pattern}' — {explanation}"))
        # Group C: regex
        m = SAY_CODE_PATTERN.search(clean)
        if m:
            group.hits.append(Hit(ln, line.strip(), f"'{m.group()}' — say+状态码直译"))
    return group


# ── 扫描 2：搭配越界 — 空间→抽象 ────────────────────────────────────────────

SPACE_TO_ABSTRACT_PATTERNS = [
    "穿过.*障碍", "穿过.*对话", "穿过.*研究", "穿过.*领域",
    "走过.*对话", "走进.*对话", "走进.*研究",
    "踏入.*领域", "踏入.*研究", "步入.*对话", "跨过.*障碍",
]


def scan_space_to_abstract(text: str) -> ScanGroup:
    group = ScanGroup(id=2, name="搭配越界——空间→抽象", method="C2 扫描 2")
    compiled = [re.compile(p) for p in SPACE_TO_ABSTRACT_PATTERNS]
    lines = _lines_outside_code_blocks(text)
    for ln, line in lines:
        if _is_syntax_line(line):
            continue
        clean = _strip_inline_code(line)
        for pat in compiled:
            m = pat.search(clean)
            if m:
                group.hits.append(Hit(ln, line.strip(), f"'{m.group()}'"))
    return group


# ── 扫描 3：搭配越界 — 感官/物理/生物→抽象 ───────────────────────────────────

SENSORY_PATTERNS = [
    "苦涩.*事", "甜蜜.*经历", "酸涩.*经历", "辛辣.*讽刺",
    "逃出.*预算", "逃出.*框架", "逃脱.*约束", "逃离.*系统", "挣脱.*结构",
    "爬行", "蠕动", "匍匐",
    "扑向.*地盘", "扑向.*市场", "扑向.*领域",
    "住在.*规则", "住在.*引擎", "住在.*系统",
]


def scan_sensory_to_abstract(text: str) -> ScanGroup:
    group = ScanGroup(id=3, name="搭配越界——感官/物理/生物→抽象", method="C2 扫描 3")
    compiled = [re.compile(p) for p in SENSORY_PATTERNS]
    lines = _lines_outside_code_blocks(text)
    for ln, line in lines:
        if _is_syntax_line(line):
            continue
        clean = _strip_inline_code(line)
        for pat in compiled:
            m = pat.search(clean)
            if m:
                group.hits.append(Hit(ln, line.strip(), f"'{m.group()}'"))
    return group


# ── 扫描 4：语义反转 / 动宾跨域 / 名词堆叠 ───────────────────────────────────

SEMANTIC_REVERSAL_PATTERNS = [
    "恢复.*差距", "恢复.*失地", "追回.*失地", "挽回.*损失",
]

VERB_OBJECT_CROSS_PATTERNS = [
    "拦下.*原因", "抓住.*问题", "修复.*想法", "抓住.*机会",
]

NOUN_STACKING_PATTERN = re.compile(r"(\S+的){3,}\S+")


def scan_semantic_verb_noun(text: str) -> ScanGroup:
    group = ScanGroup(id=4, name="语义反转/动宾跨域/名词堆叠", method="C2 扫描 4")
    sr_compiled = [re.compile(p) for p in SEMANTIC_REVERSAL_PATTERNS]
    vo_compiled = [re.compile(p) for p in VERB_OBJECT_CROSS_PATTERNS]
    lines = _lines_outside_code_blocks(text)
    for ln, line in lines:
        if _is_syntax_line(line):
            continue
        clean = _strip_inline_code(line)
        # 语义反转
        for pat in sr_compiled:
            m = pat.search(clean)
            if m:
                group.hits.append(Hit(ln, line.strip(), f"语义反转: '{m.group()}'"))
        # 动宾跨域
        for pat in vo_compiled:
            m = pat.search(clean)
            if m:
                group.hits.append(Hit(ln, line.strip(), f"动宾跨域: '{m.group()}'"))
        # 名词堆叠
        m = NOUN_STACKING_PATTERN.search(clean)
        if m:
            group.hits.append(Hit(ln, line.strip(), f"名词堆叠: '{m.group()}'"))
    return group


# ── 扫描 5：输入法（IME）残留 ────────────────────────────────────────────────

IME_PATTERNS = [
    "的的", "了了",
    "欧阳", "司马", "诸葛",  # IME candidate buffer residue
    "已经经", "可能能",
]


def scan_ime_residue(text: str) -> ScanGroup:
    group = ScanGroup(id=5, name="输入法残留", method="C2 扫描 5")
    lines = _lines_outside_code_blocks(text)
    for ln, line in lines:
        if _is_syntax_line(line):
            continue
        clean = _strip_inline_code(line)
        for pat in IME_PATTERNS:
            if pat in clean:
                group.hits.append(Hit(ln, line.strip(), f"'{pat}'"))
    return group


# ── 扫描 6（补充）：盘古之白 ─────────────────────────────────────────────────

CN_THEN_EN = re.compile(r"[一-鿿㐀-䶿](?=[A-Za-z0-9])")
EN_THEN_CN = re.compile(r"(?<=[A-Za-z0-9])[一-鿿㐀-䶿]")


def scan_pangu_spacing(text: str) -> ScanGroup:
    group = ScanGroup(id=6, name="盘古之白（中英空格）", method="补充扫描")
    lines = _lines_outside_code_blocks(text)
    for ln, line in lines:
        stripped = line.strip()
        if not stripped or _is_syntax_line(line):
            continue
        clean = _strip_inline_code(line)
        for m in CN_THEN_EN.finditer(clean):
            ctx = clean[max(0, m.start() - 4):m.end() + 4]
            group.hits.append(Hit(ln, line.strip(), f"中→英缺空格: '{ctx}'"))
        for m in EN_THEN_CN.finditer(clean):
            ctx = clean[max(0, m.start() - 4):m.end() + 4]
            group.hits.append(Hit(ln, line.strip(), f"英→中缺空格: '{ctx}'"))
    return group


# ── 扫描 7（补充）：已知搭配越界词表 ─────────────────────────────────────────

# 与 translation_lint.py 的 KNOWN_COLLOCATION_VIOLATIONS 完全同步
KNOWN_COLLOCATIONS = [
    ("穿过", "研究"), ("穿过", "实验"), ("穿过", "论文"), ("穿过", "论证"), ("穿过", "文章"),
    ("花掉", "注意力"), ("花掉", "精力"), ("花掉", "心力"),
    ("花", "注意力"), ("的花", "注意力"),
    ("卸载", "任务"), ("卸载", "认知"), ("卸载", "工作"), ("部分卸载", ""),
    ("等量的", "理解"), ("等量的", "收获"), ("等量的", "价值"),
    ("走进", "对话"), ("走进", "处境"), ("走进", "陷阱"), ("踏进", "对话"),
    ("桥", "之间"), ("铰链", "之间"), ("纽带", "之间"),
    ("发货", ""), ("引擎盖", ""), ("头条功能", ""),
    ("部分删除", ""), ("部分关闭", ""),
    ("动了", "数据"), ("动了", "评测"),
    ("冷酷洞察", ""),  # 2026-08-11 硬组合：冷酷 修饰 现实/真相，洞察 搭配 深刻/敏锐
    ("证出", ""),  # 2026-08-11 口语动词：数学/学术语境应为"证明"
    ("悬而未决", ""),  # 2026-08-11 需人工复核：成语直接顶数量词时节奏断裂（悬而未决 50 年→50 年未解）
    ("同时为真", ""),  # 2026-08-11 逻辑术语误入叙事语境：both were true 直译 → 同时成立
    ("显而易见的反驳", ""),  # 2026-08-11 obvious objection 直译：显而易见 修饰 道理/事实，不修饰 反驳 → 最常见的反驳
    ("提取", "价值"),  # 2026-08-11 extract value 直译：提取 搭配 数据/物质，价值 搭配 创造/产生 → 创造价值
    ("论证的地基", ""),  # 2026-08-11 建筑名词隐喻误用：论说隐喻用 基石/基础，不用 地基
    ("分两半", ""),  # 2026-08-11 物理切分意象误用：方案等抽象物用 分两部分
]


def scan_known_collocations(text: str) -> ScanGroup:
    group = ScanGroup(id=7, name="已知搭配越界词表", method="补充扫描")
    lines = _lines_outside_code_blocks(text)
    for ln, line in lines:
        if _is_syntax_line(line):
            continue
        clean = _strip_inline_code(line)
        for verb, obj in KNOWN_COLLOCATIONS:
            if obj:
                if verb in clean and obj in clean:
                    v_pos = clean.find(verb)
                    o_pos = clean.find(obj)
                    if abs(v_pos - o_pos) <= 15:
                        group.hits.append(Hit(ln, line.strip(), f"'{verb}+{obj}'"))
            else:
                if verb in clean:
                    group.hits.append(Hit(ln, line.strip(), f"'{verb}'"))
    return group


# ── 扫描 10：标题/小标题位 L3 词块与口语动词 ─────────────────────────────────
# 背景（2026-08-05 trq212 文章三轮审校实测）：正文扫描（1-5）全部跳过 # 标题行
# （_is_syntax_line 对 "#" 开头直接 return True），而三轮审校修正的 28 处中
# 约 1/3 位于标题/小标题位（"新玩法""删掉""想成""怎么落地""什么都没发生"
# "评分细则/评估标准"术语摇摆）。标题是读者第一接触点，L3 口语与术语摇摆
# 在标题位的杀伤力高于正文。本扫描对 # 开头的行单独跑 L3 词块表。

HEADING_L3_BLOCKLIST = [
    ("新玩法", "L3 传播语 → 新规则/新法则（忠实原文 rules）"),
    ("删掉", "标题位口语动词 → 删减/精简"),
    ("想成", "口语动词 → 视为/将其视为"),
    ("怎么落地", "标题位口语 → 落地实践"),
    ("什么都没发生", "标题位平淡缺数据支撑 → 用带数据感的表述"),
    ("封神", "L3 互联网黑话"),
    ("炸了", "L3 情绪词"),
    ("命根子", "L3 词块"),
    ("最要命", "L3 词块"),
    ("管这叫", "L3 词块"),
    ("脊背发凉", "L3 词块"),
    ("撂在桌上", "L3 词块"),
    ("刹一脚", "L3 词块"),
    ("矛头", "L3 暴力隐喻"),
    ("老黄", "过度亲昵人称 → 黄仁勋"),
    ("小札", "过度亲昵人称 → 扎克伯格"),
    ("老马", "过度亲昵人称 → 马斯克"),
    ("三把火", "成语通胀"),
    ("一锅端", "L3 词块"),
    ("干崩", "工程口语 → 瘫痪/不可用"),
    ("跑分", "工程博客禁用 → 基准测试"),
    ("踩坑", "工程博客禁用"),
    ("发帖的人", "BBS 语域 → 推文原作者"),
    ("最贵", "计算代价语境缺精度"),
    ("叫什么", "口语化解释 → 被称为"),
]


def scan_heading_l3(zh_text: str) -> ScanGroup:
    group = ScanGroup(id=10, name="标题位 L3 词块与口语动词", method="C2 扫描 10")
    for line_no, line in _lines_outside_code_blocks(zh_text):
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        clean = _strip_inline_code(stripped)
        for word, note in HEADING_L3_BLOCKLIST:
            if word in clean:
                group.hits.append(Hit(line_no, stripped[:120], f"{word} — {note}"))
    return group


# ── 扫描 11：专名大小写一致性 ───────────────────────────────────────────────
# 背景（2026-08-10 AI Adoption 文章 B 轮审校）：vas→Vas 全局替换暴露——
# 人名/产品名/公司名全小写是排版事故，且无机械扫描兜底（G19 术语一致性
# 靠人工对照清单，专名大小写被遗漏）。
# 本扫描对登记表内的专名检查裸小写出现。注意两类合法小写需人工复核排除：
#   a) @handle 上下文（@vasuman）；b) 引语中故意的口语化小写（quickref 排版铁律）。

PROPER_NOUNS = [
    "vas", "varick", "claude", "hermes", "jira", "salesforce",
    "netsuite", "dynamics", "outlook", "chatgpt", "mckinsey",
]


def scan_proper_noun_case(text: str) -> ScanGroup:
    group = ScanGroup(id=11, name="专名大小写一致性", method="补充扫描")
    lines = _lines_outside_code_blocks(text)
    for ln, line in lines:
        if _is_syntax_line(line):
            continue
        clean = _strip_inline_code(line)
        for noun in PROPER_NOUNS:
            pat = re.compile(rf"(?<![A-Za-z@]){noun}(?![A-Za-z])")
            m = pat.search(clean)
            if m:
                group.hits.append(Hit(ln, line.strip(),
                    f"专名 '{noun}' 全小写 → 应首字母大写 '{noun.capitalize()}'；排除 @handle/引语故意小写后复核"))
    return group


# ── 扫描 12：正文口语词（提示级）────────────────────────────────────────────
# 背景（2026-08-28 SDLC 文章 4 轮审校）：c2 扫描 10 只查标题位，正文里的
# "温和口语词"（跑顺了/摊开讲/兜底/练熟/活儿/跟单…）全部逃逸。
# 本扫描全量扫正文（含列表项），报告供人工判断——口语属风格选择，模式 A/掘金
# 允许一定口语度，故定位"提示级"而非核心阻断；同一词在工程博客/技术复盘体裁
# （阶段 1.2 词汇约束：禁止口语动词）应书面化。

BODY_COLLOQUIAL_LIST = [
    "跑顺了", "摊开讲", "兜底", "练熟", "活儿", "跟单",
    "闷头", "喂给", "堆出", "卡得更",
]


def scan_body_colloquial(text: str) -> ScanGroup:
    group = ScanGroup(id=12, name="正文口语词（提示级）", method="补充扫描")
    lines = _lines_outside_code_blocks(text)
    for ln, line in lines:
        if _is_syntax_line(line):
            continue
        clean = _strip_inline_code(line)
        for word in BODY_COLLOQUIAL_LIST:
            if word in clean:
                group.hits.append(Hit(ln, line.strip(), f"'{word}' → 考虑书面化（工程博客/技术复盘体裁必改）"))
    return group


# ── 扫描 13：渲染等价性（LaTeX / 裸 HTML）───────────────────────────────────
# 背景（2026-08-28）：公众号/微信 Markdown 不渲染 LaTeX（$..$）、MathML、未转义
# HTML 标签，出现即以裸字符显示。代码块与 inline code 已被 _strip_inline_code
# 与 _lines_outside_code_blocks 排除，此处只在正文正文里命中。

RENDER_RISK_PATTERNS = [
    (r"\$\$?[^$\n]+\$", "LaTeX 数学标记（公众号/微信不渲染，会显示裸 $..$）"),
    (r"\\[a-zA-Z]{2,}", "LaTeX 命令残留（如 \\sigma）"),
    (r"<(\w+)(?=\s|>)", "裸 HTML 标签（公众号编辑器可能吞掉或报错）"),
]


def scan_render_risk(text: str) -> ScanGroup:
    group = ScanGroup(id=13, name="渲染等价性（LaTeX/裸 HTML）", method="补充扫描")
    lines = _lines_outside_code_blocks(text)
    for ln, line in lines:
        if _is_syntax_line(line):
            continue
        clean = _strip_inline_code(line)
        for pat, note in RENDER_RISK_PATTERNS:
            for m in re.finditer(pat, clean):
                ctx = clean[max(0, m.start() - 4):m.end() + 4]
                group.hits.append(Hit(ln, line.strip(), f"'{ctx}' — {note}"))
    return group


# ── 扫描 14：中文正文半角标点（提示级）─────────────────────────────────────
# 背景：中文语境混入半角括号/冒号/逗号是排版瑕疵。代码块/URL/inline code 已
# 排除，此处只报"中文行内半角标点与中文紧邻"的孤例，需人工改全角。

def scan_halfwidth_punct(text: str) -> ScanGroup:
    group = ScanGroup(id=14, name="中文正文半角标点", method="补充扫描")
    lines = _lines_outside_code_blocks(text)
    for ln, line in lines:
        if _is_syntax_line(line):
            continue
        clean = _strip_inline_code(line)
        for m in re.finditer(r"\([^)\n]*[一-鿿][^)\n]*\)", clean):
            group.hits.append(Hit(ln, line.strip(), f"半角括号内夹中文 → 应改全角（）: '{m.group()}'"))
        for m in re.finditer(r"[一-鿿][:,]|[,:][一-鿿]", clean):
            group.hits.append(Hit(ln, line.strip(), f"半角标点紧邻中文 → 应改全角：'{m.group()}'"))
    return group


# ── 扫描 15：品牌/标题大小写变体并存（提示级）─────────────────────────────
# 背景（2026-08-28 SDLC 文章）：同一品牌/概念在文件里并存两种写法
# （正文 AI-native vs 书名 AI-Native；playbook vs Playbook；beta vs 公测）。
# 逐一统计登记词的各种写法，若 >1 种同时存在即报告——需人工决定用哪种并统一。

BRAND_CASING_GROUPS = {
    "AI-native 写法": ["AI-native", "AI-Native"],
    "playbook 大小写": ["playbook", "Playbook"],
    "产品测试状态(beta/公测)": ["（beta）", "（Beta）", "公测"],
    "GitHub 大小写": ["GitHub", "Github"],
    "Claude 大小写": ["Claude", "claude"],
}


def _casing_clean(text: str) -> str:
    """剔除代码块/inline code/图片引用/URL，避免品牌大小写计数被文件名
    （claude-tag.png）、URL（claude.com）、代码 span 误触发。"""
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]*`", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"<https?://[^>]+>", "", text)
    return text


def scan_brand_casing_variants(text: str) -> ScanGroup:
    group = ScanGroup(id=15, name="品牌/标题大小写变体并存", method="补充扫描")
    clean = _casing_clean(text)
    for label, variants in BRAND_CASING_GROUPS.items():
        present = {v: clean.count(v) for v in variants if clean.count(v) > 0}
        if len(present) > 1:
            summary = "，".join(f"'{k}'×{v}" for k, v in present.items())
            group.hits.append(Hit(0, "", f"{label}: 并存 {summary} → 需统一（标题式 vs 正文式可区分，但同语境勿混）"))
    return group


# ── 扫描 16（提示级）：去AI味（H2-H5：AI 腔句式/解释腔/节奏均匀/结尾升华）──────────
# 背景（2026-08-30 从 oh-story story-deslop 移植）：fanto C2 五道扫描（扫描 1-5）
# 是翻译腔/搭配/语法 Linter，缺「中文自媒体 AI 味」这条线。story-deslop 是当前
# 最强中文去AI味工程，但它是 fiction 调：C 心理外化 / E 对话腔 / 伏笔剧情 不适用
# fanto 非虚构技术文；「口语化门禁」已关闭（mode-B register 禁白话化）。
# 本扫描只做 DETECTION（确定性），"怎么改 / 用多大力 / 能删多少 / 各模式强度"
# 的判断见 references/ai-humanize-gates.md（该文档使用 H2-H5，避免与 v2 G1-G5 重名）。定位提示级——AI 腔是风格梯度而非二元错，
# 不硬阻断，供人工按模式感知强度决定是否改写。注意：本扫描保留 # 标题行（升华
# 口号常落在小标题），只跳过空行和表格行，与扫描 10 用不同 _is_syntax_line。

DEAI_PATTERNS = [
    # (family, regex, note)
    ("H2 否定翻转", r"不是[^。！？；，\n]{2,30}而是",
     "AI 高频套路「不是A而是B」→ 刻意对比可保留，套现式改直述"),
    ("H2 与其说…不如说", r"与其说[^。！？；，\n]{1,25}不如说",
     "AI 句式套路 → 拆回两层直接陈述"),
    ("H2 万能状语", r"，带着",
     "story-deslop 判最毒「，带着X」万能状语 → 去副词直述"),
    ("H2 洞察路标", r"更微妙的是|更深层次的是|更关键的是|耐人寻味的是|值得注意的是|令人惊讶的是",
     "AI 洞察路标连词 → 删或用具体事实落地"),
    ("H2 总结路标冒号", r"一句话总结|一言以蔽之|概括起来说|总的来说|归根结底",
     "「总结」路标 → 用结论句替换，别自报预告"),
    ("H3 解释因果", r"之所以[^。！？\n]{1,40}是因为|这意味着|原因在于",
     "叙述者解释因果（上帝感）→ 交给事实自己说话"),
    ("H3 剧透定性", r"殊不知|其实质是|本质上|说到底",
     "剧透/定性（AI 全知视角）→ 删或将判断后置"),
    ("H3 软评判", r"堪称|恰到好处|恰如其分|再合适不过",
     "软评判万能赞美 → 用可验证细节替代"),
    ("H3 假细节", r"凌晨[一二三四]?点|深夜[一二三四]?点|夜深人静",
     "无来源假精确时间（AI 幻觉典型）→ 无来源则删，不补时间"),
    ("H4 连排比", r"(?:[一-鿿]{2,10}，){2,}[一-鿿]{2,10}",
     "三连+短句排比（节奏均匀）→ 打散成参差句长"),
    ("H5 结尾升华", r"这次事件告诉我们|这件事告诉我们|未来已来|它启示我们|它提醒我们|我们有理由相信|从某种意义上说|在当今这个[^。\n]{0,12}时代",
     "结尾升华口号（AI 版）→ 换具体判断+数字+结论"),
]

DEAI_RHYTHM_LIMITS = {
    "——": ("破折号", 2, "≤2/篇，AI 爱用破折号制造顿挫 → 删"),
    "……": ("省略号", 2, "≤2/篇，AI 爱用省略号留白 → 删"),
    "！": ("感叹号", 1, "≤1/千字，调性克制 → 删或改陈述"),
}


def scan_deai_tone(text: str) -> ScanGroup:
    """Detect AI-tone patterns (句式套路/解释腔/节奏/升华) and set 轻/中/重级.

    Warning-level (提示级): reports hits for human review; the mode-aware
    intensity + deletion-ratio protection + convergence rules live in
    references/ai-humanize-gates.md.
    """
    group = ScanGroup(id=16, name="去AI味（H2-H5：AI腔句式/解释腔/节奏/结尾升华） · 提示级",
                      method="C2 扫描 16（提示级）")
    lines = _lines_outside_code_blocks(text)
    cjk_chars = 0
    rhythm_counts = {k: 0 for k in DEAI_RHYTHM_LIMITS}
    for ln, line in lines:
        stripped = line.strip()
        # 保留 # 标题行（升华口号常落小标题）；只跳过空行与表格行
        if not stripped or (stripped.startswith("|") and stripped.endswith("|")):
            continue
        clean = _strip_inline_code(line)
        cjk_chars += len(re.findall(r"[一-鿿]", clean))
        for family, pat, note in DEAI_PATTERNS:
            for m in re.finditer(pat, clean):
                group.hits.append(Hit(ln, line.strip(), f"[{family}] '{m.group()}' — {note}"))
        for marker in rhythm_counts:
            rhythm_counts[marker] += clean.count(marker)

    # 全篇节奏超标（line-0，无需定位）
    per1k = max(cjk_chars, 1) / 1000.0
    for marker, (label, allowed, note) in DEAI_RHYTHM_LIMITS.items():
        limit = allowed * per1k if marker == "！" else allowed
        if rhythm_counts[marker] > limit:
            group.hits.append(
                Hit(0, "", f"[H4 节奏] {label} {rhythm_counts[marker]} 次（阈值 {limit:g}）— {note}"))

    # 定级：命中密度 + 破折号超标（轻/中/重）
    density = len(group.hits) / per1k
    if density >= 2.5 or rhythm_counts["——"] > 4:
        level = "重"
    elif density >= 1.2 or rhythm_counts["——"] > 2:
        level = "中"
    else:
        level = "轻"
    group.name = f"去AI味（H2-H5：AI腔句式/解释腔/节奏/结尾升华） · {level}"
    note = (f"整篇去AI味定级【{level}】：命中 {max(0, len(group.hits) - 1)} 处 / {cjk_chars} 字，"
            f"密度 {density:.1f} 处/千字。H2-H5 阈值/模式强度/删除保护见 ai-humanize-gates.md")
    group.hits.append(Hit(0, "", note))
    return group


# ── 补充扫描（有英文原文时）：数字完整性 ─────────────────────────────────────

def _extract_numbers(text: str) -> list:
    return re.findall(r"\b\d[\d,.]*(?:\s*%|\s*[-–]\s*\d[\d,.]*\s*%)?", text)


def scan_number_parity(en_text: str, zh_text: str) -> ScanGroup:
    group = ScanGroup(id=8, name="数字完整性（EN↔ZH）", method="补充扫描（需 --original-en）")
    en_nums = _extract_numbers(en_text)
    zh_nums = _extract_numbers(zh_text)
    diff = abs(len(en_nums) - len(zh_nums))
    if diff > max(2, len(en_nums) * 0.05):
        en_set = set(en_nums)
        zh_set = set(zh_nums)
        missing = en_set - zh_set
        detail = f"原文 {len(en_nums)} 个数字，译文 {len(zh_nums)} 个数字，差值 {diff}"
        if missing:
            detail += f"。疑似缺失: {sorted(missing)[:8]}"
        group.hits.append(Hit(0, "", detail))
    return group


def scan_backtick_pairs(text: str) -> ScanGroup:
    group = ScanGroup(id=9, name="反引号成对", method="补充扫描")
    single_count = 0
    in_fence = False
    problem_lines = []
    for i, line in enumerate(text.split("\n"), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        singles = line.count("`") - line.count("``") * 2
        single_count += singles
        if singles < 0:
            problem_lines.append(i)
    if single_count % 2 != 0:
        group.hits.append(Hit(0, "", f"反引号(`) 不成对，总数 {single_count}（应为偶数）"))
    return group


# ── 报告格式化 ────────────────────────────────────────────────────────────────

def _severity(group_id: int) -> str:
    """Return v2 severity for a scan group.

    Mechanical language/style signals are advisory. Structural, rendering,
    terminology and translation-integrity signals remain delivery blockers.
    """
    if group_id in {1, 2, 3, 4, 5, 8, 9, 11, 13}:
        return "BLOCKER"
    return "WARNING"


def format_markdown_report(groups: list, total_lines: int, zh_path: str, legacy: bool = False) -> str:
    """Format v2 report while keeping the historical report readable."""
    lines = []
    lines.append("## C2 机械扫描报告")
    lines.append("")
    lines.append(f"工作流：{'v1/legacy' if legacy else 'v2'}")
    lines.append(f"源文件：`{zh_path}` ({total_lines} 行)")
    lines.append("")

    lines.append("### 扫描摘要")
    lines.append("")
    lines.append("| # | 扫描项 | 级别 | 触发数 | 判定 |")
    lines.append("|---|--------|------|--------|------|")
    for g in groups:
        severity = _severity(g.id)
        if legacy and (g.id <= 5 or g.id == 10):
            status = "✅" if g.count == 0 else f"❌ {g.count}"
            verdict = "通过" if g.count == 0 else "阻塞"
        elif legacy:
            # v1's exit contract only blocked the historical core scans;
            # supplementary findings remain visible as advisory diagnostics.
            status = "✅ 0" if g.count == 0 else f"⚠️ {g.count}"
            verdict = "通过" if g.count == 0 else "警告"
        elif g.count == 0:
            status = "✅ 0"
            verdict = "通过"
        elif severity == "BLOCKER":
            status = f"❌ {g.count}"
            verdict = "阻塞"
        else:
            status = f"⚠️ {g.count}"
            verdict = "警告"
        lines.append(f"| {g.id} | {g.name} | {severity} | {status} | {verdict} |")
    lines.append("")

    non_zero = [g for g in groups if g.count > 0]
    if non_zero:
        lines.append("### 触发详情")
        lines.append("")
        for g in non_zero:
            lines.append(f"#### 扫描 {g.id}：{g.name}（{_severity(g.id)}，{g.count} 触发）")
            lines.append("")
            shown = set()
            for hit in g.hits[:20]:
                key = (hit.line, hit.match_detail)
                if key in shown:
                    continue
                shown.add(key)
                loc = f"L{hit.line}" if hit.line else "—"
                lines.append(f"- **{loc}**: {hit.match_detail}")
                if hit.content:
                    content_short = hit.content[:80] + "..." if len(hit.content) > 80 else hit.content
                    lines.append(f"  > {content_short}")
            if len(g.hits) > 20:
                lines.append(f"- ... 及其他 {len(g.hits) - 20} 条（已截断）")
            lines.append("")

    blockers = sum(g.count for g in groups if _severity(g.id) == "BLOCKER")
    warnings = sum(g.count for g in groups if _severity(g.id) == "WARNING")
    lines.append("### 结论")
    lines.append("")
    if legacy:
        legacy_core = sum(g.count for g in groups if g.id <= 5 or g.id == 10)
        if legacy_core == 0:
            lines.append("**v1 核心扫描全部通过（0 触发）。**")
        else:
            lines.append(f"**v1 核心扫描有 {legacy_core} 处触发，需改写后重新扫描。**")
    elif blockers == 0:
        if warnings:
            lines.append(f"**v2 通过但有警告：0 个 BLOCKER，{warnings} 个 WARNING。**")
        else:
            lines.append("**v2 通过：0 个 BLOCKER，0 个 WARNING。**")
    else:
        lines.append(f"**v2 未通过：{blockers} 个 BLOCKER，另有 {warnings} 个 WARNING。**")
    lines.append("")
    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="C2 机械扫描 — 改写版中文质控自动化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("zh_file", type=Path, help="待扫描的中文 Markdown 文件")
    parser.add_argument("--original-en", type=Path, default=None,
                        help="英文原文（可选，启用数字完整性检查）")
    parser.add_argument("--json", action="store_true",
                        help="输出 JSON 格式（供程序消费）")
    parser.add_argument("--legacy", action="store_true",
                        help="使用 v1 退出语义：核心扫描（1-5、10）有触发即返回 1")
    args = parser.parse_args()

    if not args.zh_file.exists():
        print(f"[ERROR] 文件不存在: {args.zh_file}", file=sys.stderr)
        return 2

    zh_text = args.zh_file.read_text(encoding="utf-8")
    total_lines = len(zh_text.split("\n"))

    # Run C2 core scans (1-5)
    groups = [
        scan_translation_tone(zh_text),
        scan_space_to_abstract(zh_text),
        scan_sensory_to_abstract(zh_text),
        scan_semantic_verb_noun(zh_text),
        scan_ime_residue(zh_text),
    ]

    # Supplementary scans (6-7, ZH-only)
    groups.append(scan_pangu_spacing(zh_text))
    groups.append(scan_known_collocations(zh_text))

    # Heading L3 scan (10) — 标题位独立于正文扫描，v2 作为风格警告
    groups.append(scan_heading_l3(zh_text))

    # Proper noun case scan (11) — 专名大小写一致性
    groups.append(scan_proper_noun_case(zh_text))

    # 补充扫描（12-16）：正文口语词 / 渲染等价性 / 半角标点 / 品牌大小写变体 / 去AI味
    groups.append(scan_body_colloquial(zh_text))
    groups.append(scan_render_risk(zh_text))
    groups.append(scan_halfwidth_punct(zh_text))
    groups.append(scan_brand_casing_variants(zh_text))
    groups.append(scan_deai_tone(zh_text))

    # EN-ZH comparison scans (8-9, require --original-en)
    if args.original_en:
        if not args.original_en.exists():
            print(f"[ERROR] 英文原文不存在: {args.original_en}", file=sys.stderr)
            return 2
        en_text = args.original_en.read_text(encoding="utf-8")
        groups.append(scan_number_parity(en_text, zh_text))
        groups.append(scan_backtick_pairs(zh_text))

    # Output
    if args.json:
        import json
        result = {
            "zh_file": str(args.zh_file),
            "total_lines": total_lines,
            "groups": [
                {
                    "id": g.id,
                    "name": g.name,
                    "severity": _severity(g.id),
                    "count": g.count,
                    "hits": [
                        {"line": h.line, "detail": h.match_detail, "content": h.content[:100]}
                        for h in g.hits[:20]
                    ]
                }
                for g in groups
            ],
            "workflow": "v1/legacy" if args.legacy else "v2",
            "blockers": sum(g.count for g in groups if _severity(g.id) == "BLOCKER"),
            "warnings": sum(g.count for g in groups if _severity(g.id) == "WARNING"),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_markdown_report(groups, total_lines, str(args.zh_file), legacy=args.legacy))

    if args.legacy:
        core_errors = sum(g.count for g in groups if g.id <= 5 or g.id == 10)
        return 1 if core_errors > 0 else 0
    blockers = sum(g.count for g in groups if _severity(g.id) == "BLOCKER")
    return 1 if blockers > 0 else 0


if __name__ == "__main__":
    # Fix Windows GBK encoding issues with emoji output
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.exit(main())

