"""SteelDig 架构讲演版（面向非技术听众，25 页）。

与《数据库设计》技术版分开：这一版只讲“框架 + 设计逻辑 + 演示”，
术语出现时当场解释，每页只讲一件事。
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from deck_kit import (AMBER, BG, BLUE, BLUE_SOFT, BODY, FAINT, FONT, GREEN, H,
                      INK, INK2, LINE, M, MONO, MUTED, RED, SHOTS, TEAL,
                      VIOLET, W, WHITE, code_block, footer, head, kpi,
                      new_slide, para, picture, pill, rect, rule, table,
                      textbox, arrow_down)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "SteelDig_数据库架构_讲演版.pptx"

prs = Presentation()
prs.slide_width = Inches(W)
prs.slide_height = Inches(H)

DARK = RGBColor(0x0B, 0x12, 0x20)
DARK2 = RGBColor(0x14, 0x22, 0x3F)
SOFT = RGBColor(0xF2, 0xF4, 0xF7)
SOFT_BLUE = RGBColor(0xEF, 0xF4, 0xFF)
SOFT_GREEN = RGBColor(0xEC, 0xF7, 0xF1)
SOFT_RED = RGBColor(0xFD, 0xF0, 0xEE)
SOFT_AMBER = RGBColor(0xFF, 0xF7, 0xE8)


def pg(s, dark=False):
    footer(s, prs.slides.index(s) + 1, dark=dark,
           note="SteelDig · 架构与设计逻辑")


def card(s, x, y, w, h, fill=WHITE, line=LINE, radius=0.05):
    return rect(s, x, y, w, h, fill=fill, line=line, radius=radius)


def tag(s, x, y, text, color=BLUE, bg=SOFT_BLUE):
    pill(s, x, y, 0.9, text, bg=bg, fg=color, size=9)


# ===========================================================================
# 01 封面
# ===========================================================================
s = new_slide(prs, DARK)
glow = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(8.4), Inches(-1.8), Inches(7.6), Inches(7.6))
glow.fill.solid(); glow.fill.fore_color.rgb = DARK2
glow.line.fill.background(); glow.shadow.inherit = False

tf = textbox(s, 0.95, 1.45, 6.0, 0.3)
para(tf, "STEELDIG · MATERIALS KNOWLEDGE BASE", 10.5, True,
     RGBColor(0x7D, 0xA7, 0xFF), first=True)

tf = textbox(s, 0.95, 1.86, 8.4, 1.1)
para(tf, "把论文变成数据库", 42, True, WHITE, first=True, line=1.05)

rect(s, 0.97, 3.02, 1.0, 0.05, fill=RGBColor(0xF5, 0x9E, 0x0B), shape=MSO_SHAPE.RECTANGLE)

tf = textbox(s, 0.95, 3.26, 8.2, 0.5)
para(tf, "SteelDig 材料知识库 · 架构与设计逻辑", 19, False, RGBColor(0xC3, 0xCA, 0xD9), first=True)

tf = textbox(s, 0.95, 3.88, 7.6, 0.6)
para(tf, "68 篇论文 → 一个能查、能改、能审的数据库", 13,
     False, RGBColor(0x9A, 0xA7, 0xBD), first=True)

stats = [("68", "篇论文"), ("638", "个样品"), ("1,508", "条性能数据")]
for i, (v, l) in enumerate(stats):
    x = 0.95 + i * 2.25
    tf = textbox(s, x, 5.35, 2.0, 0.5)
    para(tf, v, 25, True, WHITE, first=True)
    tf = textbox(s, x, 5.86, 2.0, 0.28)
    para(tf, l, 10.5, False, RGBColor(0x86, 0x98, 0xB8), first=True)

tf = textbox(s, 0.95, 6.62, 6.0, 0.3)
para(tf, "2026.10 · 内部汇报", 9.5, False, RGBColor(0x5C, 0x67, 0x79), first=True)

# ===========================================================================
# 02 一页看懂
# ===========================================================================
s = new_slide(prs, BG)
head(s, "一页看懂：这个库是什么", "开场")
rule(s)

tf = textbox(s, M, 1.55, 11.9, 0.5)
para(tf, "它不是文件柜，是一个能查、能改、能审的数据库。", 24, True, INK, first=True)

kpis = [("68", "篇", "论文"), ("638", "个", "样品"), ("1,508", "条", "性能数据"), ("332", "MB", "全库体积")]
for i, (v, u, l) in enumerate(kpis):
    kpi(s, M + i * 3.05, 2.35, 2.6, l, v, u)

lines = [
    ("查", BLUE, "一个条件，两秒出结果", "成分、强度、年份、关键词、语义，都能筛"),
    ("改", GREEN, "改了就是改了，重跑不丢", "人工修正单独存一层，入库后自动贴回"),
    ("说", AMBER, "每个数字都能找到出处", "68,944 条溯源；75% 到段落，其余标注"),
]
for i, (k, c, head_line, sub_line) in enumerate(lines):
    x = M + i * 4.0
    card(s, x, 4.15, 3.8, 1.55)
    rect(s, x, 4.15, 0.06, 1.75, fill=c, shape=MSO_SHAPE.RECTANGLE)
    tf = textbox(s, x + 0.25, 4.32, 0.5, 0.4)
    para(tf, k, 18, True, c, first=True)
    tf = textbox(s, x + 0.75, 4.35, 2.9, 0.35)
    para(tf, head_line, 12, True, INK, first=True)
    tf = textbox(s, x + 0.25, 4.92, 3.35, 0.8)
    para(tf, sub_line, 10, False, MUTED, first=True, line=1.4)

tf = textbox(s, M, 6.3, 11.9, 0.35)
para(tf, "下面先看三个真实场景 —— 它们分别对应查、说、改。", 10.5, False, FAINT, first=True)
pg(s)

# ===========================================================================
# 03 三个场景
# ===========================================================================
s = new_slide(prs, BG)
head(s, "没有这个库，日常是三个样子", "痛点")
rule(s)

scenes = [
    ("01", "找一个“抗拉 > 800、还能拉 30%”的钢", "打开 68 个 PDF，一页页翻表格，两天。", "查"),
    ("02", "审稿人问：这个 850 MPa 哪来的？", "翻回原文，凭记忆找那句话，半天。", "说"),
    ("03", "发现一个数抄错了，改完", "下周重跑入库，又被覆盖了。", "改"),
]
for i, (n, title, body, key) in enumerate(scenes):
    x = M + i * 4.0
    card(s, x, 1.75, 3.8, 3.9)
    tf = textbox(s, x + 0.28, 1.95, 1.0, 0.5)
    para(tf, n, 22, True, RGBColor(0xD3, 0xDA, 0xE6), first=True, name=MONO)
    tf = textbox(s, x + 0.28, 2.55, 3.25, 1.2)
    para(tf, title, 14.5, True, INK, first=True, line=1.35)
    tf = textbox(s, x + 0.28, 3.95, 3.25, 1.0)
    para(tf, body, 11.5, False, BODY, first=True, line=1.5)
    tag(s, x + 0.28, 5.12, key, BLUE if i != 2 else GREEN)

tf = textbox(s, M, 5.95, 11.9, 0.5)
para(tf, "三件事，正好对应数据库的三件事：查、说、改。", 14, True, INK2, first=True)
pg(s)

# ===========================================================================
# 04 五个问题
# ===========================================================================
s = new_slide(prs, BG)
head(s, "一个数据库要回答五个问题", "框架")
rule(s)

rows = [
    ("1", "存得住", "原始文件不被改，数据随时能重建", "6,667 个对象 · 36 张表"),
    ("2", "查得到", "按成分、性能、年份、意思找得到", "5,099 条可检索文档"),
    ("3", "改得动", "人工修正生效，重跑不会被冲掉", "修订可撤销、可重放"),
    ("4", "说得清", "每个值能回到原句，每次修改有记录", "68,944 条溯源"),
    ("5", "用得上", "不会 SQL 的人也能用", "10 个页面 · 22 个接口"),
]
y = 1.62
for i, (n, verb, desc, proof) in enumerate(rows):
    card(s, M, y, 11.9, 0.78, fill=WHITE)
    tf = textbox(s, M + 0.22, y + 0.19, 0.4, 0.4)
    para(tf, n, 12, True, RGBColor(0xB9, 0xC3, 0xD4), first=True, name=MONO)
    tf = textbox(s, M + 0.70, y + 0.16, 1.7, 0.4)
    para(tf, verb, 16, True, INK, first=True)
    tf = textbox(s, M + 2.45, y + 0.22, 5.7, 0.35)
    para(tf, desc, 11.5, False, BODY, first=True)
    tf = textbox(s, M + 8.35, y + 0.22, 3.3, 0.35)
    para(tf, proof, 10, False, MUTED, first=True, align=PP_ALIGN.RIGHT)
    y += 0.90

tf = textbox(s, M, 6.42, 11.9, 0.35)
para(tf, "四层架构，就是为这五件事服务的。", 11.5, True, INK2, first=True)
pg(s)

# ===========================================================================
# 05 四层
# ===========================================================================
s = new_slide(prs, BG)
head(s, "四层：一层回答一个问题", "框架")
rule(s)

layers = [
    ("消费层", "网页 · 接口 · 给 AI 用的语料", "人在这里看", BLUE),
    ("检索层", "列索引 · 全文 · 语义 · 成分区间", "帮人找到", VIOLET),
    ("事实源", "36 张表 + 12 个视图（PostgreSQL）", "数据本体", TEAL),
    ("资产湖", "原始 JSON + 图片，按内容指纹存", "证据的根", AMBER),
]
y = 1.58
for i, (name, desc, hint, color) in enumerate(layers):
    card(s, M, y, 7.45, 0.98, fill=WHITE)
    rect(s, M, y, 0.07, 0.98, fill=color, shape=MSO_SHAPE.RECTANGLE)
    tf = textbox(s, M + 0.28, y + 0.14, 1.5, 0.4)
    para(tf, name, 14, True, color, first=True)
    tf = textbox(s, M + 1.85, y + 0.16, 3.6, 0.35)
    para(tf, desc, 10.5, False, BODY, first=True)
    tf = textbox(s, M + 5.55, y + 0.16, 1.7, 0.35)
    para(tf, hint, 9.5, False, FAINT, first=True, align=PP_ALIGN.RIGHT)
    if i < 3:
        arrow_down(s, M + 3.65, y + 1.00, 0.16, RGBColor(0xD5, 0xDD, 0xEA), 0.14)
    y += 1.18

card(s, 8.55, 1.58, 4.05, 4.7, fill=DARK, line=None)
tf = textbox(s, 8.85, 1.82, 3.5, 0.3)
para(tf, "一句记住", 10, True, RGBColor(0x7D, 0xA7, 0xFF), first=True, space_after=8)
for i, (a, b) in enumerate([("湖", "保险柜"), ("仓", "账本"), ("检索层", "目录"), ("消费层", "柜台")]):
    tf = textbox(s, 8.85, 2.25 + i * 0.68, 3.4, 0.6)
    para(tf, a, 12.5, True, WHITE, first=True, space_after=1)
    para(tf, "＝ " + b, 10.5, False, RGBColor(0xA9, 0xB6, 0xCC), space_after=0)
rect(s, 8.85, 5.12, 3.35, 0.015, fill=RGBColor(0x2C, 0x3A, 0x52), shape=MSO_SHAPE.RECTANGLE)
tf = textbox(s, 8.85, 5.28, 3.45, 0.8)
para(tf, "账本可以重抄，\n保险柜不能重造。", 10, False, RGBColor(0x86, 0x98, 0xB8), first=True, line=1.45)

tf = textbox(s, M, 6.36, 11.9, 0.4)
para(tf, "上层可以换，下层不能错：网页可以重写，账本不能丢，保险柜不能改。", 11, True, INK2, first=True)
pg(s)

# ===========================================================================
# 06 四层分工表
# ===========================================================================
s = new_slide(prs, BG)
head(s, "每层只做一件事，改动才不会牵连全库", "框架")
rule(s)

rows = [
    ["层", "回答什么问题", "里面有什么", "现在做到"],
    ["消费层", "不会写 SQL 的人怎么用？", "10 个页面 / 22 个接口 / 检索语料", "界面 + 接口可用"],
    ["检索层", "怎么在两秒内找到？", "列索引 / 全文 / 语义 / 成分区间", "5,099 条文档"],
    ["事实源", "有哪些样品、性能、相？", "36 表 + 12 视图，332 MB", "68 篇全量入库"],
    ["资产湖", "原始文件还是那一份吗？", "6,667 个对象，148 MB，sha256", "0 损坏"],
]
tbl = table(s, M, 1.70, 11.9, rows, [1.4, 3.4, 4.6, 2.5], size=10.5,
            row_h=0.92, header_h=0.4)
for i, c in enumerate([BLUE, VIOLET, TEAL, AMBER], start=1):
    for r in tbl.cell(i, 0).text_frame.paragraphs[0].runs:
        r.font.bold = True
        r.font.color.rgb = c
        r.font.size = Pt(11.5)

tf = textbox(s, M, 6.05, 11.9, 0.7)
para(tf, "这一页可以先不记细节，只记一句：每层只做一件事。", 11, True, INK2, first=True, space_after=3)
para(tf, "所以换网页不会动数据，换模型不会动网页，重灌数据库不会动原始文件。", 10, False, MUTED)
pg(s)

# ===========================================================================
# 07 流水线
# ===========================================================================
s = new_slide(prs, BG)
head(s, "数据是怎么进来的：从 PDF 到一条能查的记录", "从原料到成品")
rule(s)

steps = [
    ("论文 PDF", "68 篇，约 700 MB", "原文留在这里，不进库", MUTED),
    ("① 解析", "文字 / 表格 / 图片 / 版面", "MinerU，产出 10,316 个块", AMBER),
    ("② 抽取", "成分、工艺、性能、相", "大模型读成结构化 JSON", VIOLET),
    ("③ 入库", "表 + 湖，30 秒", "校验、归一、挂溯源", BLUE),
]
for i, (name, sub, note, color) in enumerate(steps):
    x = M + i * 3.05
    card(s, x, 1.72, 2.72, 1.78, fill=WHITE)
    rect(s, x, 1.72, 2.72, 0.06, fill=color, shape=MSO_SHAPE.RECTANGLE)
    tf = textbox(s, x + 0.2, 1.9, 2.3, 0.35)
    para(tf, name, 13.5, True, INK, first=True)
    tf = textbox(s, x + 0.2, 2.32, 2.35, 0.7)
    para(tf, sub, 10.5, False, BODY, first=True, line=1.35)
    tf = textbox(s, x + 0.2, 3.02, 2.35, 0.4)
    para(tf, note, 8.5, False, FAINT, first=True, line=1.3)
    if i < 3:
        ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + 2.76), Inches(2.42),
                                Inches(0.22), Inches(0.26))
        ar.fill.solid(); ar.fill.fore_color.rgb = RGBColor(0xB7, 0xC4, 0xD9)
        ar.line.fill.background()

tf = textbox(s, M, 4.15, 11.9, 0.9)
para(tf, "每一步的产物都留着。", 14, True, INK2, first=True, space_after=4)
para(tf, "解析错了，不用重跑模型；模型抽错了，不用重新解析 PDF；入库错了，从湖里 30 秒重放。",
     11, False, BODY)

# 小对照
rows = [
    ["产物", "数量", "用来做什么"],
    ["原文切块 evidence_block", "10,316", "溯源的终点：每句话都在这里"],
    ["样品 sample", "638", "成分 × 工艺，性能挂在它下面"],
    ["性能值 property_value", "1,508", "数值 + 单位归一，可直接比较"],
]
table(s, M, 5.05, 11.9, rows, [4.4, 1.5, 6.0], size=10, row_h=0.38, header_h=0.34)
pg(s)

# ===========================================================================
# 08 资产盘点
# ===========================================================================
s = new_slide(prs, BG)
head(s, "库里到底有什么", "资产盘点")
rule(s)

items = [
    ("68", "篇", "论文"), ("250", "个", "合金"), ("638", "个", "样品"), ("1,508", "条", "性能值"),
    ("10,316", "块", "原文证据"), ("68,944", "条", "溯源记录"), ("5,099", "条", "检索文档"), ("6,667", "个", "湖内对象"),
]
for i, (v, u, l) in enumerate(items):
    x = M + (i % 4) * 3.05
    y = 1.72 + (i // 4) * 1.72
    card(s, x, y, 2.75, 1.42, fill=WHITE)
    tf = textbox(s, x + 0.18, y + 0.18, 2.4, 0.25)
    para(tf, l, 9.5, False, MUTED, first=True)
    tf = textbox(s, x + 0.18, y + 0.5, 2.4, 0.55)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = v
    from deck_kit import _font
    _font(r, 24, True, INK)
    r2 = p.add_run(); r2.text = " " + u
    _font(r2, 10, False, MUTED)

tf = textbox(s, M, 5.35, 11.9, 0.9)
para(tf, "68 篇论文，拆成 638 个样品、1,508 条性能、68,944 条溯源。", 13, True, INK2, first=True, space_after=4)
para(tf, "全库 332 MB。同样的数据如果只存 PDF，是 700 MB，而且一个字都查不了。", 10.5, False, MUTED)
pg(s)

# ===========================================================================
# 09 存得住
# ===========================================================================
s = new_slide(prs, BG)
head(s, "存得住：湖是保险柜，仓是账本", "设计逻辑 ①")
rule(s)

# 湖
card(s, M, 1.66, 5.85, 3.45, fill=SOFT_BLUE, line=RGBColor(0xD8, 0xE3, 0xFA))
tf = textbox(s, M + 0.3, 1.86, 5.2, 0.35)
para(tf, "资产湖 · 保险柜", 15, True, BLUE, first=True)
tf = textbox(s, M + 0.3, 2.3, 5.2, 0.4)
para(tf, "6,667 个对象 / 148 MB", 11, True, INK, first=True)
bullets = [
    "每个文件按内容指纹（sha256）命名",
    "只允许新增，不允许修改",
    "改一个字节，指纹就对不上",
]
for i, b in enumerate(bullets):
    tf = textbox(s, M + 0.3, 2.85 + i * 0.55, 5.1, 0.4)
    para(tf, "· " + b, 10.5, False, BODY, first=True, line=1.35)

# 仓
card(s, 6.75, 1.66, 5.85, 3.45, fill=SOFT_GREEN, line=RGBColor(0xCF, 0xE8, 0xDA))
tf = textbox(s, 7.05, 1.86, 5.2, 0.35)
para(tf, "事实源 · 账本", 15, True, GREEN, first=True)
tf = textbox(s, 7.05, 2.3, 5.2, 0.4)
para(tf, "36 张表 + 12 个视图 / 332 MB", 11, True, INK, first=True)
bullets = [
    "每个值有类型、有单位、能建索引",
    "整库可以从湖里重灌，30 秒",
    "所以表设计错了，改完重放就行",
]
for i, b in enumerate(bullets):
    tf = textbox(s, 7.05, 2.85 + i * 0.55, 5.1, 0.4)
    para(tf, "· " + b, 10.5, False, BODY, first=True, line=1.35)

tf = textbox(s, M, 5.35, 11.9, 0.85)
para(tf, "PDF 没入库，但没丢：68 篇都在 01_raw/ 下，按 DOI 命名，约 700 MB。", 11, True, INK2, first=True, space_after=4)
para(tf, "库只存“解析出来的结果”，因为 PDF 是输入，不是结果；需要看原文时按 DOI 取。", 10, False, MUTED)
pg(s)

# ===========================================================================
# 10 列 vs JSONB
# ===========================================================================
s = new_slide(prs, BG)
head(s, "查得到（一）：要筛的做成列，原文留在 JSONB", "设计逻辑 ②")
rule(s)

card(s, M, 1.62, 5.3, 2.05, fill=WHITE)
tf = textbox(s, M + 0.25, 1.78, 4.9, 0.35)
para(tf, "进“列”：经常要用的", 12.5, True, BLUE, first=True)
for i, b in enumerate(["身份、外键（论文号、样品号）", "会被筛选的维度（强度、年份、元素）", "需要类型、单位、索引和约束"]):
    tf = textbox(s, M + 0.25, 2.22 + i * 0.5, 4.85, 0.42)
    para(tf, "· " + b, 10, False, BODY, first=True, line=1.3)

card(s, 6.35, 1.62, 6.25, 2.05, fill=WHITE)
tf = textbox(s, 6.6, 1.78, 5.8, 0.35)
para(tf, "进“JSONB”：不常筛、但要保真的", 12.5, True, VIOLET, first=True)
for i, b in enumerate(["整份原始 JSON（结构随论文变）", "长尾内容（界面、缺陷、曲线描述）", "暂时不查、以后可能要查的字段"]):
    tf = textbox(s, 6.6, 2.22 + i * 0.5, 5.75, 0.42)
    para(tf, "· " + b, 10, False, BODY, first=True, line=1.3)

rows = [
    ["原文", "最终去了哪", "为什么"],
    ["\"685\" + 单位 \"MPa\"", "列：value_num / unit_canonical", "要比较大小、要换算"],
    ["\"Bal.\"（余量）", "JSONB 原文 + 另建一行推断值", "字符串不能当数字用"],
    ["试验条件（温度、应变速率）", "JSONB（目前不筛）", "要用时再提升为列"],
]
table(s, M, 4.05, 11.9, rows, [3.5, 4.8, 3.6], size=10, row_h=0.46, header_h=0.36)

tf = textbox(s, M, 6.15, 11.9, 0.4)
para(tf, "规则：先放 JSONB；等它第二次出现在查询条件里，再提升为列。", 10.5, True, INK2, first=True)
pg(s)

# ===========================================================================
# 11 三种索引
# ===========================================================================
s = new_slide(prs, BG)
head(s, "查得到（二）：三种问法，三种索引", "设计逻辑 ②")
rule(s)

cols = [
    ("精确条件", "铝 8–11%，抗拉 > 800", "列索引", BLUE, "像查字典：直接翻到那一页"),
    ("关键词", "TWIP、κ-碳化物", "全文索引", VIOLET, "像书末索引：按词找段落"),
    ("一个意思", "为什么加铝能降密度", "语义（向量）", TEAL, "像找相似的人：不看名字，看气质"),
]
for i, (name, example, tech, color, analogy) in enumerate(cols):
    x = M + i * 4.0
    card(s, x, 1.72, 3.8, 3.0, fill=WHITE)
    tf = textbox(s, x + 0.25, 1.9, 3.3, 0.35)
    para(tf, name, 14, True, color, first=True)
    tf = textbox(s, x + 0.25, 2.36, 3.3, 0.75)
    para(tf, "“" + example + "”", 11, False, INK, first=True, line=1.4)
    tf = textbox(s, x + 0.25, 3.2, 3.3, 0.3)
    para(tf, tech, 10, True, MUTED, first=True)
    tf = textbox(s, x + 0.25, 3.62, 3.3, 0.8)
    para(tf, analogy, 9.5, False, FAINT, first=True, line=1.4)

tf = textbox(s, M, 5.05, 11.9, 0.8)
para(tf, "5,099 条可检索文档，三种结果按“名次”合并（不是按分数），因为三种分数量纲根本不可比。",
     11, False, BODY, first=True, line=1.4)
tf = textbox(s, M, 5.75, 11.9, 0.4)
para(tf, "中文还有个坑：入库时用 jieba 切词，查询时必须用同一套切法，否则索引和查询对不上。",
     9.5, False, FAINT, first=True)
pg(s)

# ===========================================================================
# 12 改得动
# ===========================================================================
s = new_slide(prs, BG)
head(s, "改得动：修改写在便利贴上，重跑再贴回去", "设计逻辑 ③")
rule(s)

# 错误做法
card(s, M, 1.7, 5.85, 2.9, fill=SOFT_RED, line=RGBColor(0xF3, 0xD3, 0xCF))
tf = textbox(s, M + 0.3, 1.88, 5.2, 0.35)
para(tf, "直接改表（不推荐）", 12.5, True, RED, first=True)
flow = ["人工改一个值", "下次入库：整篇删掉重写", "修改没了"]
for i, t in enumerate(flow):
    tf = textbox(s, M + 0.3, 2.36 + i * 0.62, 5.2, 0.4)
    para(tf, ("→ " if i else "") + t, 10.5, False, BODY, first=True)
tf = textbox(s, M + 0.3, 4.2, 5.2, 0.3)
para(tf, "实测发生过，不是假设。", 9, False, RGBColor(0x9A, 0x5B, 0x52), first=True)

# 正确做法
card(s, 6.75, 1.7, 5.85, 2.9, fill=SOFT_GREEN, line=RGBColor(0xCF, 0xE8, 0xDA))
tf = textbox(s, 7.05, 1.88, 5.2, 0.35)
para(tf, "走校订层（推荐）", 12.5, True, GREEN, first=True)
flow = ["修改写进修订记录", "入库时保留，结束后自动重放", "修改还在，且有记录"]
for i, t in enumerate(flow):
    tf = textbox(s, 7.05, 2.36 + i * 0.62, 5.2, 0.4)
    para(tf, ("→ " if i else "") + t, 10.5, False, BODY, first=True)
tf = textbox(s, 7.05, 4.2, 5.2, 0.3)
para(tf, "重放 = 把便利贴再贴一遍。", 9, False, RGBColor(0x3F, 0x7A, 0x5E), first=True)

cards = [("前后值", "改前 850 → 改后 845"), ("理由", "原文表 2 是 845"), ("可撤销", "撤销后回到 850")]
for i, (t, d) in enumerate(cards):
    x = M + i * 4.0
    card(s, x, 4.85, 3.8, 1.15, fill=WHITE)
    tf = textbox(s, x + 0.2, 5.0, 3.4, 0.3)
    para(tf, t, 10, True, MUTED, first=True)
    tf = textbox(s, x + 0.2, 5.34, 3.4, 0.45)
    para(tf, d, 10.5, False, BODY, first=True)

tf = textbox(s, M, 6.25, 11.9, 0.35)
para(tf, "所以“改得动”不是能改，是改完还算数。", 11, True, INK2, first=True)
pg(s)

# ===========================================================================
# 13 说得清（一）
# ===========================================================================
s = new_slide(prs, BG)
head(s, "说得清（一）：从值找到论文，再找到原句", "设计逻辑 ④")
rule(s)

chain = [
    ("值", "屈服 880 ± 19 MPa", "property_value"),
    ("指针", "JSON 路径 + 证据块号", "sample_trace"),
    ("原句", "b0035 · 3.1.2 节 · 第 4 页", "evidence_block"),
    ("论文", "10.1002/srin.202400475", "paper"),
]
for i, (t, d, tbl) in enumerate(chain):
    x = M + i * 3.05
    card(s, x, 1.66, 2.72, 1.3, fill=WHITE)
    tf = textbox(s, x + 0.2, 1.8, 2.3, 0.3)
    para(tf, t, 11, True, BLUE, first=True)
    tf = textbox(s, x + 0.2, 2.12, 2.35, 0.55)
    para(tf, d, 10, False, INK, first=True, line=1.3)
    tf = textbox(s, x + 0.2, 2.78, 2.35, 0.25)
    para(tf, tbl, 8, False, FAINT, first=True, name=MONO)
    if i < 3:
        ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + 2.76), Inches(2.18),
                                Inches(0.22), Inches(0.24))
        ar.fill.solid(); ar.fill.fore_color.rgb = RGBColor(0xA9, 0xB8, 0xD4)
        ar.line.fill.background()

# 原句引用
card(s, M, 3.3, 7.6, 1.8, fill=SOFT, line=LINE)
tf = textbox(s, M + 0.3, 3.46, 7.0, 0.3)
para(tf, "原文（b0035，第 4 页）", 9, True, MUTED, first=True)
tf = textbox(s, M + 0.3, 3.78, 7.0, 1.2)
para(tf, "“…the yield strength from 880 MPa in the as-cast state to 1041 MPa, accompanied by a decrease in total elongation from 39% to 8%.”",
     10.5, False, BODY, first=True, line=1.55)

nums = [("68,944", "条溯源记录"), ("75%", "能到段落"), ("25%", "标注“弱溯源”")]
for i, (v, l) in enumerate(nums):
    tf = textbox(s, 8.75, 3.45 + i * 0.66, 3.8, 0.5)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = v
    from deck_kit import _font
    _font(r, 20, True, INK if i == 0 else (GREEN if i == 1 else AMBER))
    r2 = p.add_run(); r2.text = "  " + l
    _font(r2, 9.5, False, MUTED)

tf = textbox(s, M, 5.4, 11.9, 0.6)
para(tf, "挂不上出处的 25%，界面直接显示“弱溯源”，不假装都有。", 10.5, True, INK2, first=True, space_after=3)
para(tf, "能定位到论文是 100%；能定位到段落的，是 75%。", 9.5, False, MUTED)
pg(s)

# ===========================================================================
# 14 说得清（二）
# ===========================================================================
s = new_slide(prs, BG)
head(s, "说得清（二）：换模型、改数据，都留痕", "设计逻辑 ④")
rule(s)

tf = textbox(s, M, 1.6, 6.4, 0.3)
para(tf, "同一篇论文，跑过 4 个批次", 11, True, MUTED, first=True)
runs = [
    ("0915 / pro", "13 篇", "最早一批"),
    ("0917 / pro", "4 篇", ""),
    ("0919 / pro", "4 篇", ""),
    ("1009 / flash", "47 篇", "主力批次"),
]
for i, (r, n, note) in enumerate(runs):
    y = 2.0 + i * 0.78
    card(s, M, y, 6.0, 0.62, fill=WHITE)
    tf = textbox(s, M + 0.2, y + 0.14, 2.2, 0.3)
    para(tf, r, 10.5, True, INK, first=True, name=MONO)
    tf = textbox(s, M + 2.5, y + 0.14, 1.5, 0.3)
    para(tf, n, 10, False, BODY, first=True)
    tf = textbox(s, M + 3.9, y + 0.14, 1.9, 0.3)
    para(tf, note, 8.5, False, FAINT, first=True, align=PP_ALIGN.RIGHT)

card(s, 6.95, 1.6, 5.65, 3.55, fill=DARK, line=None)
tf = textbox(s, 7.2, 1.8, 5.1, 0.3)
para(tf, "每次修改，记四件事", 10, True, RGBColor(0x7D, 0xA7, 0xFF), first=True)
audit = [("改前 / 改后", "850 → 845"), ("理由", "原文表 2 是 845"), ("操作人 / 时间", "谁、什么时候"), ("可撤销", "撤销即回到 850")]
for i, (k, v) in enumerate(audit):
    tf = textbox(s, 7.2, 2.25 + i * 0.62, 5.0, 0.5)
    para(tf, k, 10, True, WHITE, first=True, space_after=1)
    para(tf, v, 9, False, RGBColor(0xA9, 0xB6, 0xCC), space_after=0)

tf = textbox(s, M, 5.05, 11.9, 0.8)
para(tf, "换模型不是“覆盖”，是“并存”：新批次上线，旧批次仍可查、可对比。", 11, True, INK2, first=True, space_after=3)
para(tf, "查当前数据时加一个条件（is_latest），要历史就去掉它。", 9.5, False, MUTED)
pg(s)

# ===========================================================================
# 15 SQL 演示
# ===========================================================================
s = new_slide(prs, DARK)
head(s, "演示 ①：一条 SQL，从值找到论文", "演示", dark=True)
rule(s, color=RGBColor(0x7D, 0xA7, 0xFF))

code = [
    "select p.paper_id, pa.doi,",
    "       p.metric, p.value_raw,",
    "       b.block_id, b.section, b.page_idx",
    "from core.property_value p",
    "join core.paper pa using (paper_id)",
    "left join lateral unnest(p.source_block_ids) bid",
    "       on true",
    "left join core.evidence_block b",
    "       on b.paper_id = p.paper_id",
    "      and b.block_id = bid",
    "where p.value_raw = '880 ± 19';",
]
code_block(s, M, 1.62, 7.15, 2.5, code, size=9.5)

rows = [
    ["证据块", "章节", "页"],
    ["b0035", "3.1.2 机械性能", "4"],
    ["b0049", "3.2.2 机械性能", "6"],
]
tf = textbox(s, 8.15, 1.62, 4.4, 0.3)
para(tf, "查询结果", 9, True, RGBColor(0x86, 0x98, 0xB8), first=True)
table(s, 8.15, 1.95, 4.4, rows, [1.2, 2.4, 0.8], size=9.5, row_h=0.5, header_h=0.34)

tf = textbox(s, 8.15, 3.75, 4.45, 1.6)
para(tf, "同一个值，两条证据：", 10, True, RGBColor(0xC3, 0xCA, 0xD9), first=True, space_after=4)
para(tf, "正文里说了一遍，表 2 里又列了一遍。", 9.5, False, RGBColor(0x9A, 0xA7, 0xBD), line=1.45)

tf = textbox(s, M, 5.15, 11.9, 0.9)
para(tf, "这就是“说得清”：不是给一个数，是给一个数 + 它的出处 + 它所在的页。",
     13, True, WHITE, first=True, space_after=4)
para(tf, "界面上点一下证据徽标，看到的就是这条路径。", 9.5, False, RGBColor(0x86, 0x98, 0xB8))
pg(s, dark=True)

# ===========================================================================
# 16 界面演示
# ===========================================================================
s = new_slide(prs, BG)
head(s, "演示 ②：证据就在数字旁边", "演示")
rule(s)

picture(s, SHOTS / "03-sample-top.jpg", M, 1.58, 7.55)

tf = textbox(s, 8.55, 1.6, 4.05, 0.3)
para(tf, "界面上一眼能看到", 10, True, MUTED, first=True)
notes = [
    ("证据徽标", "每个数字后面标着“1 条证据”，点开就是原句"),
    ("单位已归一", "62.5 %、832.5 MPa、685 MPa，可直接比较"),
    ("工艺链", "1423 K 均匀化 → 热锻 → 空冷，逐步可读"),
    ("中文词条", "这个样品是做什么的、为什么，写成人话"),
]
for i, (t, d) in enumerate(notes):
    y = 2.0 + i * 1.05
    tf = textbox(s, 8.55, y, 4.05, 0.3)
    para(tf, t, 10.5, True, INK, first=True)
    tf = textbox(s, 8.55, y + 0.3, 4.0, 0.6)
    para(tf, d, 9, False, MUTED, first=True, line=1.4)

tf = textbox(s, M, 6.42, 11.9, 0.3)
para(tf, "不追求炫，追求三秒内判断：这个样品值不值得看。", 9.5, False, FAINT, first=True)
pg(s)

# ===========================================================================
# 17 成分检索
# ===========================================================================
s = new_slide(prs, BG)
head(s, "演示 ③：成分检索，像查元素周期表", "演示")
rule(s)

picture(s, SHOTS / "09-composition-exact.jpg", M, 1.58, 5.3)
picture(s, SHOTS / "10-composition-fuzzy.jpg", 6.92, 1.58, 5.3)

tf = textbox(s, M, 6.3, 5.3, 0.25)
para(tf, "精确命中：找到 2 个完全匹配", 9.5, True, GREEN, first=True)
tf = textbox(s, 6.92, 6.3, 5.3, 0.25)
para(tf, "没有精确结果：给最接近的，并说明差多少", 9.5, True, AMBER, first=True)

steps = ["点元素、设区间", "先找完全匹配", "没有再按距离排序"]
for i, t in enumerate(steps):
    tf = textbox(s, M + i * 4.0, 6.6, 3.8, 0.25)
    para(tf, f"{i+1}. " + t, 9, False, MUTED, first=True)
pg(s)

# ===========================================================================
# 18 接口演示
# ===========================================================================
s = new_slide(prs, DARK)
head(s, "演示 ④：一个接口，一条命令", "演示", dark=True)
rule(s, color=RGBColor(0x7D, 0xA7, 0xFF))

curl = [
    'curl "http://127.0.0.1:8011/api/samples/',
    '  10.1002_srin.202400475/',
    '  sample_fe-12mn-9al-3cr-1.4c-0.02nb__as-cast/trace"',
]
code_block(s, M, 1.6, 11.9, 1.0, curl, size=8.5)

resp = """{ "n": 219, "items": [ {
    "path": "$.properties[0].mechanical...",
    "status": "ok",
    "block_ids": ["b0035","b0049"],
    "evidence_text": "the yield strength from 880 MPa..."
  } ] }""".splitlines()
code_block(s, M, 2.78, 7.3, 2.35, resp, size=9.5)

tf = textbox(s, 8.35, 2.85, 4.3, 2.4)
for i, t in enumerate(["22 个接口，覆盖论文、样品、性能、检索、校订",
                       "只读：所有写操作都走专门的校订入口",
                       "返回 JSON，前端、脚本、AI 都能直接用"]):
    tf2 = textbox(s, 8.35, 2.85 + i * 0.75, 4.2, 0.6)
    para(tf2, "· " + t, 9.5, False, RGBColor(0xC3, 0xCA, 0xD9), first=True, line=1.4)

tf = textbox(s, M, 5.55, 11.9, 0.9)
para(tf, "接口文档在 /docs，每个接口都能直接在浏览器里试。", 12, True, WHITE, first=True, space_after=4)
para(tf, "同一份数据，网页给“人”看，接口给“程序”用。", 9.5, False, RGBColor(0x86, 0x98, 0xB8))
pg(s, dark=True)

# ===========================================================================
# 19 检索演示
# ===========================================================================
s = new_slide(prs, BG)
head(s, "演示 ⑤：用人话搜，也能搜到", "演示")
rule(s)

tf = textbox(s, M, 1.6, 11.9, 0.4)
para(tf, "搜：“为什么加铝能降低钢的密度”", 14, True, INK, first=True)

card(s, M, 2.2, 5.75, 1.5, fill=SOFT_RED, line=RGBColor(0xF3, 0xD3, 0xCF))
tf = textbox(s, M + 0.25, 2.36, 5.2, 0.3)
para(tf, "关键词检索：0 条", 11, True, RED, first=True)
tf = textbox(s, M + 0.25, 2.72, 5.2, 0.85)
para(tf, "它要求每个词同时出现：“为什么 / 加铝 / 降低 / 密度”，同一段里凑不齐。", 9.5, False, BODY, first=True, line=1.45)

card(s, 6.7, 2.2, 5.9, 1.55, fill=SOFT_GREEN, line=RGBColor(0xCF, 0xE8, 0xDA))
tf = textbox(s, 6.95, 2.34, 5.4, 0.3)
para(tf, "语义检索：命中", 11, True, GREEN, first=True)
tf = textbox(s, 6.95, 2.68, 5.4, 1.3)
para(tf, "“Fe-Al alloys containing 6-9 wt.% Al show about a 10% reduction in density.”", 9.5, False, BODY, first=True, line=1.45)

rows = [
    ["做法", "原理", "适合"],
    ["关键词", "按词匹配", "术语、牌号"],
    ["语义", "把句子变成 384 个数字，比距离", "用大白话问"],
    ["合并", "按名次相加（RRF）", "两种都试"],
]
table(s, M, 3.95, 7.4, rows, [1.4, 3.6, 2.4], size=9.5, row_h=0.42, header_h=0.34)

tf = textbox(s, 8.45, 4.05, 4.1, 1.5)
para(tf, "向量是什么？", 10, True, INK, first=True, space_after=4)
para(tf, "把一句话压成 384 个数字的坐标：意思越近，坐标越近。字面一个词都不重合，也能找到。", 9.5, False, MUTED, first=True, line=1.45)

tf = textbox(s, M, 6.35, 11.9, 0.3)
para(tf, "三种结果各取前 200，按名次融合：第 1 名 1/61，第 2 名 1/62……", 9, False, FAINT, first=True)
pg(s)

# ===========================================================================
# 20 表为什么这样
# ===========================================================================
s = new_slide(prs, BG)
head(s, "表为什么长这样：三个决定", "数据模型")
rule(s)

items = [
    ("身份证，不是座位号", "主键用（论文号 + 样品号）", "因为每篇论文里都有一个 sample_1；带上论文号才不会串。"),
    ("一行一个值，不是一行一个样品", "1,508 条性能 = 1,508 行", "68 篇测的性能种类不一样，宽表会有几百列、九成是空。"),
    ("事实与出处分两张表", "sample_data 存值，sample_trace 存出处", "重跑时值会变，出处不该跟着变。"),
]
for i, (t, sub, why) in enumerate(items):
    x = M + i * 4.0
    card(s, x, 1.75, 3.8, 3.1, fill=WHITE)
    tf = textbox(s, x + 0.25, 1.95, 3.3, 0.55)
    para(tf, t, 12.5, True, INK, first=True, line=1.3)
    tf = textbox(s, x + 0.25, 2.6, 3.3, 0.45)
    para(tf, sub, 9.5, True, BLUE, first=True, line=1.35)
    tf = textbox(s, x + 0.25, 3.15, 3.3, 1.5)
    para(tf, why, 9.5, False, MUTED, first=True, line=1.5)

tf = textbox(s, M, 5.3, 11.9, 0.8)
para(tf, "一句话：只把“要用来找”的东西做成列，其余原样留着。", 12, True, INK2, first=True, space_after=3)
para(tf, "这样既不会几百列半空，也不会只剩一堆查不了的 JSON。", 9.5, False, MUTED)
pg(s)

# ===========================================================================
# 21 为什么不是 Excel / Mongo / AI
# ===========================================================================
s = new_slide(prs, BG)
head(s, "为什么不是 Excel、MongoDB，或者直接问 AI", "选型")
rule(s)

rows = [
    ["方案", "能做什么", "做不到什么"],
    ["Excel", "看数据、画图", "多人同时查、68,944 条溯源、改一处处处一致"],
    ["MongoDB", "原样存 JSON，结构自由", "跨样品聚合、区间比较、join 都弱"],
    ["直接问 AI", "问答很顺", "同一问题两次答案不同；答错指不出原文；量大就崩"],
    ["这个库", "存 + 查 + 改 + 审", "要自己运维；不是“零成本”"],
]
tbl = table(s, M, 1.75, 11.9, rows, [2.2, 4.1, 5.6], size=10.5, row_h=0.78, header_h=0.4)
for r in tbl.cell(4, 0).text_frame.paragraphs[0].runs:
    r.font.bold = True
    r.font.color.rgb = BLUE

tf = textbox(s, M, 5.95, 11.9, 0.8)
para(tf, "不是它们不好，是这批数据需要四种能力放在同一个事务里：表格、JSON、中文检索、向量。", 10.5, True, INK2, first=True, space_after=3)
para(tf, "PostgreSQL 一个库全有，所以选它 —— 少一个组件，就少一类半夜出问题。", 9.5, False, MUTED)
pg(s)

# ===========================================================================
# 22 质量
# ===========================================================================
s = new_slide(prs, BG)
head(s, "数据质量：先把“扎实”摆在桌面上", "质量")
rule(s)

kpis2 = [("0", "条", "error 级问题（阻断发布）"), ("844", "条", "warn，每条都有解释"),
         ("99.94%", "", "证据 id 能对齐"), ("95", "项", "自动化测试全部通过")]
for i, (v, u, l) in enumerate(kpis2):
    x = M + i * 3.05
    card(s, x, 1.7, 2.75, 1.65, fill=WHITE)
    tf = textbox(s, x + 0.2, 1.88, 2.4, 0.25)
    para(tf, l, 8.5, False, MUTED, first=True, line=1.3)
    tf = textbox(s, x + 0.2, 2.25, 2.4, 0.6)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = v
    from deck_kit import _font
    _font(r, 26, True, GREEN if i in (0, 2, 3) else AMBER)
    if u:
        r2 = p.add_run(); r2.text = " " + u
        _font(r2, 9.5, False, MUTED)

lines = [
    ("入库前", "95 项测试 + 12 条质量规则，error 级 0 条"),
    ("入库时", "每个值尽量挂出处；挂不上的标“弱溯源”，不隐藏"),
    ("入库后", "可改、可撤销、可重放；改完还回得去"),
]
for i, (k, v) in enumerate(lines):
    y = 3.85 + i * 0.72
    card(s, M, y, 11.9, 0.6, fill=SOFT if i == 1 else WHITE)
    tf = textbox(s, M + 0.25, y + 0.15, 1.4, 0.3)
    para(tf, k, 10, True, BLUE, first=True)
    tf = textbox(s, M + 1.75, y + 0.15, 9.8, 0.3)
    para(tf, v, 10, False, BODY, first=True)

tf = textbox(s, M, 6.3, 11.9, 0.35)
para(tf, "844 条 warn 不是“忽略”，是每一类都知道原因、都能量化。", 9.5, False, FAINT, first=True)
pg(s)

# ===========================================================================
# 23 和别的库差在哪
# ===========================================================================
s = new_slide(prs, BG)
head(s, "和 Materials Project 们差在哪", "定位")
rule(s)

card(s, M, 1.7, 5.85, 3.9, fill=WHITE)
tf = textbox(s, M + 0.3, 1.9, 5.2, 0.35)
para(tf, "结果库：MP / NOMAD / ICSD", 13, True, MUTED, first=True)
for i, t in enumerate(["一条记录 = 一个材料或结构", "数据来自计算或测量", "错了重算一遍", "核心价值：全、准"]):
    tf = textbox(s, M + 0.3, 2.45 + i * 0.68, 5.2, 0.4)
    para(tf, "· " + t, 10, False, BODY, first=True)

card(s, 6.75, 1.7, 5.85, 3.9, fill=SOFT_BLUE, line=RGBColor(0xD8, 0xE3, 0xFA))
tf = textbox(s, 7.05, 1.9, 5.2, 0.35)
para(tf, "这个库：声明库", 13, True, BLUE, first=True)
for i, t in enumerate(["一条记录 = 论文里的一句声明", "数据从文字里读出来", "错了回到原句、修订、重放", "核心价值：可引用、可复核"]):
    tf = textbox(s, 7.05, 2.45 + i * 0.68, 5.2, 0.4)
    para(tf, "· " + t, 10, False, BODY, first=True)

tf = textbox(s, M, 5.9, 11.9, 0.9)
para(tf, "他们在记录“结果”，我们在记录“谁、在哪篇、哪句说了什么，以及后来谁改了它”。", 12, True, INK2, first=True, space_after=3)
para(tf, "两者不冲突：将来可以把 MP 的计算值作为外部关联表接进来，但绝不混成一条记录。", 9.5, False, MUTED)
pg(s)

# ===========================================================================
# 24 代价与边界
# ===========================================================================
s = new_slide(prs, BG)
head(s, "这套设计的账单", "取舍")
rule(s)

groups = [
    ("我们认的代价", BLUE, ["存储放大：1,508 条值 → 68,944 条溯源",
                        "表多：36 张，新人要一周熟悉",
                        "不能直接改表：必须走校订",
                        "单机：没有分布式"]),
    ("还没做的", AMBER, ["下游训练数据导出",
                     "OpenSearch（规模没到）",
                     "多人审批与权限",
                     "备份恢复演练"]),
    ("什么时候该换", TEAL, ["论文到 10 万篇：检索外迁",
                        "多团队写：加权限与审计",
                        "要实时：改增量入库",
                        "要联邦：加查询层"]),
]
for i, (title, color, items) in enumerate(groups):
    x = M + i * 4.0
    card(s, x, 1.7, 3.8, 3.5, fill=WHITE)
    rect(s, x, 1.7, 3.8, 0.06, fill=color, shape=MSO_SHAPE.RECTANGLE)
    tf = textbox(s, x + 0.25, 1.9, 3.3, 0.35)
    para(tf, title, 12, True, color, first=True)
    for j, t in enumerate(items):
        tf = textbox(s, x + 0.25, 2.42 + j * 0.66, 3.3, 0.55)
        para(tf, "· " + t, 9, False, BODY, first=True, line=1.4)

tf = textbox(s, M, 6.0, 11.9, 0.4)
para(tf, "这些账单我们都认。唯一不能接受的是：让用户拿到一个查不到出处、又改不动的数。", 10, True, INK2, first=True)
pg(s)

# ===========================================================================
# 25 收尾
# ===========================================================================
s = new_slide(prs, DARK)
glow = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(9.2), Inches(4.0), Inches(6.4), Inches(6.4))
glow.fill.solid(); glow.fill.fore_color.rgb = DARK2
glow.line.fill.background(); glow.shadow.inherit = False

tf = textbox(s, 0.95, 1.5, 6.0, 0.3)
para(tf, "收尾", 10, True, RGBColor(0x7D, 0xA7, 0xFF), first=True)
tf = textbox(s, 0.95, 1.9, 10.8, 1.2)
para(tf, "一个能查、能改、能审的\n材料数据库", 32, True, WHITE, first=True, line=1.3)

tf = textbox(s, 0.95, 4.05, 10.8, 0.5)
para(tf, "湖是保险柜，仓是账本；账本可以重抄，保险柜不能重造。", 14, False, RGBColor(0xC3, 0xCA, 0xD9), first=True)

tf = textbox(s, 0.95, 5.15, 11.5, 0.3)
para(tf, "下一步", 9.5, True, RGBColor(0x5C, 0x67, 0x79), first=True)
steps = ["多模型对比", "校订审批流", "训练数据导出", "跨论文合并"]
for i, t in enumerate(steps):
    tf = textbox(s, 0.95 + i * 2.9, 5.5, 2.7, 0.4)
    para(tf, "0" + str(i + 1) + "  " + t, 10.5, False, RGBColor(0xA9, 0xB6, 0xCC), first=True)

tf = textbox(s, 0.95, 6.6, 8.0, 0.3)
para(tf, "SteelDig · 材料知识库", 9, False, RGBColor(0x5C, 0x67, 0x79), first=True)

prs.save(OUT)
print(f"saved {OUT} slides={len(prs.slides)}")
