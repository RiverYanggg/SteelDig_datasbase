"""构建 SteelDig 数据库设计 PPT。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from deck_kit import (AMBER, BG, BLUE, BLUE_SOFT, BODY, FAINT, FONT, GREEN, H, INK,
                      INK2, LINE, M, MONO, MUTED, OUT, RED, SHOTS, TEAL, VIOLET, W,
                      WHITE, arrow_down, bullet, code_block, footer, head, kpi,
                      new_slide, para, picture, pill, rect, rule, table, textbox)

prs = Presentation()
prs.slide_width = Inches(W)
prs.slide_height = Inches(H)

def pg(slide, **kw):
    """页码 = 幻灯片在 deck 中的真实序号（插页不必手工重排）。"""
    footer(slide, prs.slides.index(slide) + 1, **kw)


# ===========================================================================
# 01 封面
# ===========================================================================
s = new_slide(prs, RGBColor(0x0B, 0x12, 0x20))
# 右侧光晕
glow = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(8.2), Inches(-1.6), Inches(7.4), Inches(7.4))
glow.fill.solid(); glow.fill.fore_color.rgb = RGBColor(0x14, 0x22, 0x3F)
glow.line.fill.background(); glow.shadow.inherit = False

tf = textbox(s, M, 1.55, 9, 0.3)
para(tf, "STEELDIG · MATERIALS KNOWLEDGE BASE", 10.5, True, RGBColor(0x7D, 0xA7, 0xFF), first=True)

tf = textbox(s, M, 2.00, 10.6, 1.9)
para(tf, "从 68 篇文献", 44, True, WHITE, first=True, line=1.12, space_after=0)
para(tf, "到一个企业级材料数据库", 44, True, WHITE, line=1.12, space_after=0)

rect(s, M, 4.05, 0.9, 0.05, fill=BLUE, shape=MSO_SHAPE.RECTANGLE)

tf = textbox(s, M, 4.30, 9.6, 0.9)
para(tf, "架构设计 · 数据模型 · 工程实现", 17, False, RGBColor(0xC3, 0xCA, 0xD9), first=True)

# 底部指标
metrics = [("68", "篇文献"), ("638", "个样品"), ("1,304", "条可数值化性能"),
           ("68,944", "条溯源记录"), ("0", "个 error")]
x = M
for v, k in metrics:
    tf = textbox(s, x, 5.72, 2.2, 0.42)
    para(tf, v, 22, True, WHITE, first=True, space_after=0)
    tf = textbox(s, x, 6.16, 2.2, 0.26)
    para(tf, k, 10, False, RGBColor(0x86, 0x98, 0xB8), first=True)
    x += 2.42

tf = textbox(s, M, 6.72, 9, 0.3)
para(tf, "2026.10  ·  PostgreSQL 16 + pgvector  ·  数据来自 4 个提取批次（pro ×3 / flash ×1）",
     9.5, False, RGBColor(0x5C, 0x67, 0x79), first=True)

# ===========================================================================
# 02 阅读路径
# ===========================================================================
s = new_slide(prs, RGBColor(0x0B, 0x12, 0x20))

tf = textbox(s, M, 0.62, 9, 0.3)
para(tf, "CONTENTS", 10, True, RGBColor(0x7D, 0xA7, 0xFF), first=True)

tf = textbox(s, M, 0.98, 11.2, 0.7)
para(tf, "先说清为什么长这样，再说清和谁不一样", 26, True, WHITE, first=True, line=1.15)

tf = textbox(s, M, 1.62, 11.2, 0.3)
para(tf, "六段材料，两个重点：第 2 段（设计逻辑）与第 4 段（框架差异）", 10.5, False,
     RGBColor(0x86, 0x98, 0xB8), first=True)

chapters = [
    ("01", "起点", "为什么另建一个库；两类原始资产，68 篇一一对应", "P03–P04", False),
    ("02", "架构与逻辑", "四层怎么来的 · 一个前提推出全部决定 · 为什么是这些组件 · 代价", "P05–P10", True),
    ("03", "数据模型", "48 个表怎么分工；列与 JSONB、data/trace、归一化、block_id", "P11–P16", False),
    ("04", "框架差异", "和 MP / NOMAD / ICSD / 手册库比，形状差在哪，为什么必须差", "P17–P19", True),
    ("05", "能用起来", "三路检索、成分查询、资产湖、增删改查、界面、真实 SQL", "P20–P26", False),
    ("06", "边界", "0 error 背后还有什么问题；这套库还没到哪一步", "P27–P28", False),
]
y = 2.24
for num, name, desc, pages, key in chapters:
    if key:
        rect(s, M - 0.02, y - 0.10, 11.94, 0.66, fill=RGBColor(0x12, 0x1D, 0x33), line=None, radius=0.05)
        rect(s, M - 0.02, y - 0.10, 0.045, 0.66, fill=BLUE, shape=MSO_SHAPE.RECTANGLE)
    tf = textbox(s, M + 0.14, y + 0.04, 0.5, 0.3)
    para(tf, num, 11, True, RGBColor(0x4C, 0x5D, 0x7D), first=True, name=MONO)
    tf = textbox(s, M + 0.66, y + 0.02, 2.0, 0.3)
    para(tf, name, 12.5, True, WHITE, first=True)
    tf = textbox(s, M + 2.72, y + 0.05, 7.4, 0.3)
    para(tf, desc, 10, False, RGBColor(0x9A, 0xA7, 0xBD), first=True)
    tf = textbox(s, 9.86, y + 0.05, 1.64, 0.3, PP_ALIGN.RIGHT)
    para(tf, pages, 9.5, False, RGBColor(0x5C, 0x67, 0x79), first=True, name=MONO)
    if key:
        pill(s, 11.62, y + 0.02, 0.62, "重点", RGBColor(0x1B, 0x2C, 0x4E), RGBColor(0x7D, 0xA7, 0xFF), 8)
    y += 0.72

# ===========================================================================
# 02(原) 为什么建
# ===========================================================================
s = new_slide(prs, BG)
head(s, "为什么需要另建一个数据库", "问题")
rule(s)

tf = textbox(s, M, 1.72, 5.7, 0.32)
para(tf, "原始资产很好看，但没法直接回答研究问题", 14, True, INK, first=True)

tf = textbox(s, M, 2.22, 5.6, 4.3)
items = [
    ("数值是自由文本", "“427–513 MPa” “~350-450” “up to 950 MPa” “1 GPa”——只能 LIKE，不能比较大小"),
    ("结构深且不稳定", "sample JSON 嵌套 6 层、9 个分区、100+ 字段，不同论文的键名还会漂移"),
    ("结论无法回溯", "说“屈服 685 MPa”时，要能点到原文第几段，而不是让人再翻一遍 PDF"),
]
for i, (t, d) in enumerate(items):
    y = 2.22 + i * 1.30
    rect(s, M, y, 0.055, 0.95, fill=BLUE, shape=MSO_SHAPE.RECTANGLE)
    tf = textbox(s, M + 0.22, y - 0.02, 5.3, 0.9)
    para(tf, t, 13.5, True, INK, first=True, space_after=3)
    para(tf, d, 10.5, False, MUTED, line=1.35)

# 右侧目标
rect(s, 6.75, 1.66, 5.86, 4.28, fill=WHITE, line=LINE, radius=0.04)
tf = textbox(s, 7.05, 1.92, 5.2, 0.3)
para(tf, "所以这个库要提供三件事", 13.5, True, INK, first=True)

goals = [
    ("可数值查询", "WHERE yield_strength_mpa > 700", "单位归一后是真查询"),
    ("可证据追溯", "每个值挂 block_id → 原文段落", "来源可被审计"),
    ("可增量运营", "多批次 / 多模型 / 人工校订", "不是一个静态转存"),
]
for i, (t, code, note) in enumerate(goals):
    y = 2.44 + i * 1.26
    pill(s, 7.05, y, 1.32, t, BLUE_SOFT, BLUE, 9.5)
    tf = textbox(s, 8.52, y - 0.04, 3.9, 0.36)
    para(tf, code, 10, False, INK2, first=True, name=MONO)
    tf = textbox(s, 8.52, y + 0.30, 3.9, 0.3)
    para(tf, note, 9.5, False, FAINT, first=True)

pg(s)

# ===========================================================================
# 03 资产盘点
# ===========================================================================
s = new_slide(prs, BG)
head(s, "起点：两类原始资产，68 篇一一对应", "资产盘点")
rule(s)

kpis = [("文献", "68", "篇", "DOI 转目录名，两侧 ID 集合完全一致"),
        ("MinerU 解析", "960", "MB", "PDF / 版面 / 图片 / full.md"),
        ("提取产物", "69", "MB", "preprocess + output + timing"),
        ("提取批次", "4", "个", "0915 / 0917 / 0919 用 pro，1009 用 flash")]
for i, (l, v, u, f) in enumerate(kpis):
    kpi(s, M + i * 3.02, 1.72, 2.8, l, v, u, f)

rect(s, M, 3.22, 11.9, 0.02, fill=LINE, shape=MSO_SHAPE.RECTANGLE)

rows = [
    ["资产", "内容", "规模", "在库中的角色"],
    ["A · MinerU", "content_list / layout / full.md / images/", "68 篇 · 960 MB", "版式与图片的原始来源"],
    ["B · 提取产物", "evidence_blocks / discover / sample / wiki / figure", "68 篇 · 69 MB", "结构化事实的来源"],
]
table(s, M, 3.46, 11.9, rows, [1.55, 4.6, 1.9, 3.85], size=11, row_h=0.44)

tf = textbox(s, M, 4.92, 11.9, 0.6)
para(tf, "统一以 <paper_id> 作为目录名（DOI 的 / 换成 _），两边可以直接 join；"
         "68 篇全部有 MinerU、也全部有提取结果。", 11.5, False, MUTED, first=True, line=1.4)

# 时间线式的小注
rect(s, M, 5.62, 11.9, 1.02, fill=WHITE, line=LINE, radius=0.04)
tf = textbox(s, M + 0.28, 5.82, 11.3, 0.7)
para(tf, "被排除的东西，以及为什么", 11, True, INK, first=True, space_after=5)
para(tf, "_monitor/（agent 会话日志，1.1 GB）——它是只增的审计态，output/ 才是被覆盖的权威当前态；"
         "原始 .mineru_source 里的 PDF 共 703 MB，属于“输入”而非“派生资产”，因此不入湖。",
     10.5, False, MUTED, line=1.35)

pg(s)

# ===========================================================================
# 04 总体架构
# ===========================================================================
s = new_slide(prs, BG)
head(s, "总体架构：四层，单向流动", "架构")
rule(s)

layers = [
    ("消费层", "浏览界面 · REST API · RAG · 分析看板", "Jinja2 + FastAPI · 只读视图 api.*", BLUE),
    ("检索层", "全文 tsvector · 模糊 pg_trgm · 语义 pgvector", "search.document · RRF 融合", VIOLET),
    ("事实源", "实体表(列) + JSONB(保真) + trace", "PostgreSQL 16 · core / canon / ops", TEAL),
    ("资产湖", "原始 JSON + 图片，写入后不可变", "内容寻址 sha256 · 可平移 MinIO/S3", AMBER),
]
y = 1.70
for i, (name, desc, tech, color) in enumerate(layers):
    rect(s, M, y, 7.55, 0.94, fill=WHITE, line=LINE, radius=0.05)
    rect(s, M, y, 0.06, 0.94, fill=color, shape=MSO_SHAPE.RECTANGLE)
    tf = textbox(s, M + 0.26, y + 0.14, 1.5, 0.3)
    para(tf, name, 13, True, INK, first=True)
    tf = textbox(s, M + 1.62, y + 0.13, 5.8, 0.34)
    para(tf, desc, 11, False, BODY, first=True)
    tf = textbox(s, M + 1.62, y + 0.50, 5.8, 0.3)
    para(tf, tech, 9.5, False, FAINT, first=True, name=MONO)
    if i < 3:
        arrow_down(s, M + 3.62, y + 0.99, 0.26)
    y += 1.26

# 右侧说明
rect(s, 8.62, 1.70, 4.0, 1.92, fill=INK, line=None, radius=0.05)
tf = textbox(s, 8.90, 1.90, 3.45, 1.6)
para(tf, "关键思想", 11, True, RGBColor(0x7D, 0xA7, 0xFF), first=True, space_after=6)
para(tf, "文件是“湖”，数据库是“仓”。", 13, True, WHITE, space_after=4, line=1.3)
para(tf, "湖不可变，可重建一切；\n仓为查询组织，随时可从湖重放。", 10.5, False,
     RGBColor(0xC3, 0xCA, 0xD9), line=1.45)

tf = textbox(s, 8.62, 3.86, 4.0, 2.6)
para(tf, "读路径", 10, True, MUTED, first=True, space_after=3)
para(tf, "API / 界面 → api 视图 → core 表 / search", 10, False, BODY, space_after=12)
para(tf, "写路径", 10, True, MUTED, space_after=3)
para(tf, "资产文件 → ETL → core（整篇重建）\n人工修改 → curate.change → 重放", 10, False, BODY, line=1.4)

pg(s)

# ===========================================================================
# 06 四层结构表
# ===========================================================================
s = new_slide(prs, BG)
head(s, "《数据库建立》里的四层结构表", "总体架构")
rule(s)

rows = [
    ["层", "原设计（2026.10 文档）", "现在落地"],
    ["消费层", "查询 API / RAG Agent / 分析看板 / 下游训练数据导出",
     "界面 10 页 · JSON 接口 22 个 · 语料走 search.document · 看板 3 张；训练数据导出未做"],
    ["检索层", "精确 / 面聚合：PG 列 + GIN；语义：pgvector(HNSW)；全文：tsvector（可升级 OpenSearch）",
     "B-tree + GIN 列索引 · pgvector HNSW 384 维（5,099 条文档全嵌入）· tsvector + pg_trgm，jieba 分词"],
    ["事实源", "PostgreSQL —— 实体表(列) + JSONB(保真) + trace",
     "36 表 + 12 视图 / 7 schema；payload jsonb 存 data.json 原文；sample_trace 68,944 条"],
    ["资产湖", "对象存储(MinIO/S3/OSS) —— 原始 JSON + 图片",
     "本地目录 + sha256 内容寻址：6,667 对象 / 148 MB；写路径已按 S3 的 key 布局"],
]
tbl = table(s, M, 1.70, 11.9, rows, [1.35, 4.40, 6.15], size=9, row_h=0.90, header_h=0.38)
for i, c in enumerate([BLUE, VIOLET, TEAL, AMBER], start=1):
    for r in tbl.cell(i, 0).text_frame.paragraphs[0].runs:
        r.font.bold = True
        r.font.color.rgb = c
        r.font.size = Pt(10.5)

tf = textbox(s, M, 5.86, 11.9, 0.75)
para(tf, "四层都落地了。真正没做的只有两件：下游训练数据导出、OpenSearch —— 后者是规模问题，不是设计问题。",
     10.5, True, INK2, first=True, space_after=4)
para(tf, "事实源 ↔ 资产湖：写入是“内容寻址、永不修改”；反向是 reset + migrate + ingest --all，30 秒从湖重放。",
     9.5, False, MUTED)

pg(s)

# ===========================================================================
# 07 一个前提推出整个架构
# ===========================================================================
s = new_slide(prs, BG)
head(s, "一个数据库要回答的五个问题", "设计逻辑")
rule(s)

# 左：底线
rect(s, M, 1.70, 3.92, 4.30, fill=INK, line=None, radius=0.05)
tf = textbox(s, M + 0.28, 1.92, 3.35, 0.3)
para(tf, "底线", 9.5, True, RGBColor(0x7D, 0xA7, 0xFF), first=True)
tf = textbox(s, M + 0.28, 2.22, 3.42, 1.2)
para(tf, "存储 + 增删改查，\n再加一条：可审计。", 17.5, True, WHITE, first=True, line=1.35)
tf = textbox(s, M + 0.28, 3.42, 3.42, 1.9)
para(tf, "前四条是企业级数据库的底线；文献数据还要多一条：每条记录都能回答"
         "“谁、在哪篇、哪句说的，后来谁改过”。",
     9.5, False, RGBColor(0xC3, 0xCA, 0xD9), first=True, line=1.5)
rect(s, M + 0.28, 5.28, 3.34, 0.02, fill=RGBColor(0x2C, 0x3A, 0x52), shape=MSO_SHAPE.RECTANGLE)
tf = textbox(s, M + 0.28, 5.42, 3.38, 0.5)
para(tf, "五条能力，缺一条，\n用户就会回到 PDF。", 10, True, WHITE, first=True, line=1.45)

# 右：五条能力
tf = textbox(s, 5.02, 1.70, 7.6, 0.28)
para(tf, "五个问题 —— 每一个都对应一组设施", 10, True, MUTED, first=True)

chain = [
    ("存得住", "湖按 sha256 只增 + 仓可从湖重建 + run 版本", "6,667 对象 / 148 MB / 30 秒重灌"),
    ("查得到", "只提升过滤维度为列 + 单位归一 + 三种索引", "1,304 / 1,508 条可数值查询"),
    ("改得动", "curate.change 叠加层，ingest 后自动重放", "直接 UPDATE 会被覆盖（实测）"),
    ("说得清", "sample_trace + 审计字段 + is_latest", "68,944 条指针，75% 到段落"),
    ("用得上", "10 个页面 + 22 个接口 + 检索语料", "界面 / REST / 导出"),
]
y = 2.02
for i, (claim, mech, proof) in enumerate(chain):
    rect(s, 5.02, y, 7.60, 0.76, fill=WHITE, line=LINE, radius=0.04)
    tf = textbox(s, 5.18, y + 0.09, 0.34, 0.3)
    para(tf, f"{i + 1}", 10, True, BLUE, first=True, name=MONO)
    tf = textbox(s, 5.54, y + 0.07, 2.6, 0.28)
    para(tf, claim, 10.5, True, INK, first=True)
    tf = textbox(s, 8.20, y + 0.09, 4.3, 0.28)
    para(tf, mech, 8.5, False, MUTED, first=True)
    tf = textbox(s, 5.54, y + 0.38, 5.4, 0.28)
    para(tf, "证据： " + proof, 8, False, FAINT, first=True)
    y += 0.84

tf = textbox(s, M, 6.38, 11.9, 0.4)
para(tf, "四层架构不是审美选择，是这五个问题的落点 —— 下一页的四条原则，是它的合同条款。",
     11, True, INK2, first=True)

pg(s)

# ===========================================================================
# 06 四条设计原则
# ===========================================================================
s = new_slide(prs, BG)
head(s, "四条设计原则，决定所有分表", "设计原则")
rule(s)

rows = [
    ["原则", "落地方式", "可验证的证据"],
    ["只把身份 / 外键 / 过滤维度\n提升为列",
     "实体表只暴露 *_id、外键与会被 WHERE 的维度；\n完整产物一律进 payload jsonb",
     "sample_data.payload 保存 data.json 原文，\nproperty_value 才是数值投影"],
    ["data / trace 分离",
     "科学事实与证据溯源两张表，\n通过 (paper_id, sample_id, path) 关联",
     "68,944 条 JSON Pointer 全部能在\npayload 上命中（测试守着）"],
    ["多 run / 多模型内建版本",
     "每条事实带 run_id；is_latest 部分唯一索引；\nops.run 记录 extractor / model / batch",
     "4 个 run：0915+0917+0919 用 pro（21 篇），\n1009 用 flash（47 篇）"],
    ["两级身份，不强行合并",
     "论文内用复合键；跨论文只给 canon 词表\n与可空 family_key / phase_key",
     "20 条合金族规则，250 个合金里\n7 个仍为“未分类”——保留而不是猜"],
]
table(s, M, 1.66, 11.9, rows, [2.55, 4.75, 4.6], size=10.5, row_h=0.92, header_h=0.42)
tf = textbox(s, M, 5.94, 11.9, 0.7)
para(tf, "前四条分别是上一页五条能力的“合同条款”；“查得到”落在检索层与成分检索（P20–P21）。",
     9.5, False, MUTED, first=True, space_after=3)
para(tf, "原则本身来自《数据库建立》：拍平 100+ 字段会碎成一堆半空表；全 JSONB 又没法过滤。",
     9.5, False, FAINT)

pg(s)

# ===========================================================================
# 07 技术选型：为什么不是 Mongo / Neo4j / ES
# ===========================================================================
s = new_slide(prs, BG)
head(s, "为什么不拼一个“最强组件”的组合", "技术选型")
rule(s)

rows = [
    ["候选方案", "它擅长什么", "在这批数据上，哪里不行", "我们的做法"],
    ["MySQL", "轻、上手快、生态最广", "JSONB 没有 GIN 索引，无 pgvector，窗口函数与 CTE 弱",
     "选 PostgreSQL：三种能力同库"],
    ["文档库　MongoDB", "原样保真，嵌套不用拆", "跨样品聚合、区间比较、join 都弱；换一种查询就多一套索引",
     "用 JSONB 拿 80% 好处，列只留给会被 WHERE 的字段"],
    ["图库　Neo4j", "溯源链、工艺链天然是图", "68,944 条 trace 用三列就够；多一套库就多一套备份与权限",
     "trace 表 + 递归 CTE 走工艺链，不加第二个存储"],
    ["Elasticsearch", "中文分词、模糊、聚合都强", "数值过滤与事务要回 PG 再 join，一致性只能靠补偿",
     "tsvector + pg_trgm，万级文档量级足够"],
    ["专用向量库", "大规模 ANN 检索", "5,099 × 384 维，HNSW 在 PG 里已经够快，没必要多一跳",
     "pgvector，与事实同库、同事务"],
    ["宽表 / Excel", "人一眼能看懂", "100+ 字段、键名跨论文漂移，三个月就碎成一堆空列",
     "列 + JSONB 混合，字段再多也不改表结构"],
]
table(s, M, 1.66, 11.9, rows, [2.30, 2.95, 3.85, 2.80], size=9, row_h=0.60, header_h=0.38)

rect(s, M, 5.76, 11.9, 0.86, fill=INK, line=None, radius=0.04)
tf = textbox(s, M + 0.28, 5.92, 11.3, 0.6)
para(tf, "判据不是“谁最强”，而是“能不能在一个事务、一份备份、一套权限里，同时满足保真、可查、可回滚”。",
     11.5, True, WHITE, first=True, space_after=3)
para(tf, "单体 PostgreSQL 的代价是规模上限（约 10⁷ 行）与检索能力的上限；收益是运维面收敛到一个进程。",
     9, False, RGBColor(0x9A, 0xA7, 0xBD))

pg(s)

# ===========================================================================
# 08 代价
# ===========================================================================
s = new_slide(prs, BG)
head(s, "每个决定都有账单", "取舍")
rule(s)

tf = textbox(s, M, 1.62, 11.9, 0.3)
para(tf, "这一页不列优点，只列我们为此付出的东西 —— 以及它现在有多贵", 10, False, MUTED, first=True)

rows = [
    ["决定", "换来的", "付出的", "现在的量级"],
    ["data / trace 拆表", "每个值都能点回原文", "行数 45 倍（68,944 : 1,508），溯源表 55 MB", "库 332 MB，可以接受"],
    ["列 + JSONB 混合", "上游字段漂移不会炸库", "复杂查询要写 JSONPath，索引得单独建", "12 列 · 89 个索引"],
    ["run 版本化", "多模型并存、随时可回滚", "每行乘 run 数，处处要过滤 is_latest", "4 个 run，视图里统一封掉"],
    ["curate 叠加层", "人工修改活过每一次重跑", "改表要登记白名单，入库后必须重放", "11 表 · 57 个可写字段"],
    ["单体 PostgreSQL", "一个事务、一份备份、一套权限", "没有 ES 的同义词，没有专用 ANN 压缩", "规模上限约 10⁷ 行"],
    ["服务端渲染", "零构建、离线可用、好部署", "交互不如 SPA，图表联动要服务端出图", "10 个页面，够用"],
]
table(s, M, 1.98, 11.9, rows, [2.55, 3.05, 3.65, 2.65], size=9, row_h=0.60, header_h=0.38)

tf = textbox(s, M, 6.02, 11.9, 0.6)
para(tf, "这些账单我们都认。唯一不能接受的是：让用户拿到一个查不到出处、又改不动的数。",
     12, True, INK2, first=True)

pg(s)

# ===========================================================================
# 11 从产物到表
# ===========================================================================
s = new_slide(prs, BG)
head(s, "从产物到表：每件都有归处", "数据来源")
rule(s)

rows = [
    ["产物", "里面是什么", "入库后成为", "数量"],
    ["evidence_blocks.json", "block_id / text / kind / page_idx / section；一篇 83 块",
     "core.evidence_block —— 所有下游都回指它", "10,316"],
    ["paper_context.json", "标题、摘要、12 个章节、block 与图的数量",
     "core.paper 的元数据 + 章节索引", "68"],
    ["image_groups.json", "图组、题注块与引用块的 id",
     "core.figure + 图 ↔ 块关联", "1,041"],
    ["multimodal_index.json", "与 image_groups 90% 重叠，多出产物引用",
     "不建表：二者取一（取它）", "—"],
    ["discover + sample", "5 类实体；sample 顶层 9 分区、嵌套 6 层",
     "core.sample / alloy / property_value；原文进 payload jsonb", "638"],
    ["timing.json", "预处理 / 提取 / 总计 三段耗时",
     "ops.ingest_run —— 成本可归因", "4 run"],
]
tbl = table(s, M, 1.70, 11.9, rows, [2.15, 3.95, 4.60, 1.20], size=9, row_h=0.62, header_h=0.36,
            align=["l", "l", "l", "r"])
for i in range(1, len(tbl.rows)):
    for r in tbl.cell(i, 0).text_frame.paragraphs[0].runs:
        r.font.bold = True
        r.font.color.rgb = INK

tf = textbox(s, M, 5.92, 11.9, 0.8)
para(tf, "入库只读 output/（当前态）；_monitor/ 只增不改，是审计态，所以不入库。", 10.5, True, INK2,
     first=True, space_after=4)
para(tf, "sample 有 rich / data 两版：rich 带 source 壳，入库的是 data 版 —— 溯源不进 JSON，单独进 trace。",
     9.5, False, MUTED)

pg(s)

# ===========================================================================
# 12 数据模型
# ===========================================================================
s = new_slide(prs, BG)
head(s, "数据模型：48 个表 / 视图，枢纽是“样品”", "数据模型")
rule(s)

groups = [
    ("资产湖 lake", ["object · object_ref", "paper_manifest"], 3, AMBER),
    ("事实 core", ["paper · evidence_block", "alloy / alloy_element", "process / process_edge",
                  "sample · sample_data / trace / wiki", "property_value · phase",
                  "figure / observation · equation"], 20, TEAL),
    ("规范 canon", ["element · phase", "alloy_family · technique"], 4, VIOLET),
    ("检索 search", ["document（全文 + 向量）"], 1, BLUE),
    ("治理 ops", ["run · ingest_run / log", "qa_rule / qa_issue", "block_id_resolution"], 6, MUTED),
    ("校订 curate", ["change（增删改流水）"], 2, RGBColor(0xBE, 0x18, 0x5D)),
]
x = M
for name, items, n, color in groups:
    rect(s, x, 1.68, 1.86, 3.02, fill=WHITE, line=LINE, radius=0.05)
    rect(s, x, 1.68, 1.86, 0.05, fill=color, shape=MSO_SHAPE.RECTANGLE)
    tf = textbox(s, x + 0.14, 1.84, 1.6, 0.3)
    para(tf, name, 10.5, True, INK, first=True)
    tf = textbox(s, x + 0.14, 2.18, 1.62, 2.4)
    for k, it in enumerate(items):
        para(tf, it, 8.5, False, MUTED, first=(k == 0), space_after=4, line=1.3)
    tf = textbox(s, x + 0.14, 4.34, 1.6, 0.3)
    para(tf, f"{n} 张表", 9, True, color, first=True)
    x += 1.98

rect(s, M, 4.92, 11.9, 1.44, fill=WHITE, line=LINE, radius=0.04)
tf = textbox(s, M + 0.26, 5.12, 11.4, 1.1)
para(tf, "核心关系：sample = 合金 × 工艺", 11.5, True, INK, first=True, space_after=5)
para(tf, "sample_id = alloy_id + \"__\" + process_id　→　性能 / 相 / 工艺步骤 / 词条 / 溯源 全部挂在样品下",
     10, False, BODY, name=MONO, space_after=4)
para(tf, "同一成分不同工艺是两个样品，因此“材料”的主键不是成分，而是 (paper_id, sample_id)。",
     9.5, False, FAINT)

pg(s)

# ===========================================================================
# 07 设计① 列 vs JSONB
# ===========================================================================
s = new_slide(prs, BG)
head(s, "设计①  列与 JSONB 的边界：只提升 12 列", "数据建模")
rule(s)

tf = textbox(s, M, 1.66, 5.6, 0.32)
para(tf, "sample JSON 的原始结构（9 个分区，嵌套 6 层）", 11, True, MUTED, first=True)

tree = [
    "samples[]               样本身份",
    "processing_steps[]      工艺链",
    "structures[]            phases_present / defects",
    "interfaces[]            相界面 / 相演化",
    "properties[]            mechanical / physical / chemical",
    "  └ tensile_properties  yield / UTS / elongation …",
    "performance[]           对标性能",
    "characterization_methods[]",
    "computational_details[]",
    "unmapped_findings[]     无法归类的发现",
]
rect(s, M, 2.04, 5.55, 3.30, fill=WHITE, line=LINE, radius=0.04)
tf = textbox(s, M + 0.24, 2.22, 5.1, 3.0)
for i, ln in enumerate(tree):
    para(tf, ln, 10, False, INK2 if i % 2 == 0 else BODY, first=(i == 0), space_after=2,
         name=MONO, line=1.35)

arrow = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(6.36), Inches(3.42),
                           Inches(0.42), Inches(0.3))
arrow.fill.solid(); arrow.fill.fore_color.rgb = RGBColor(0xC7, 0xD2, 0xFE)
arrow.line.fill.background()

tf = textbox(s, 6.94, 1.66, 5.5, 0.32)
para(tf, "入库后真正成为“列”的，只有这些", 11, True, MUTED, first=True)

cols = [
    ("身份", "paper_id · sample_id · run_id"),
    ("外键", "alloy_id · process_id"),
    ("可过滤维度", "value_canonical · unit_canonical"),
    ("区间", "value_low / value_high"),
    ("溯源", "source_block_ids · block_status"),
    ("版本", "is_latest · extracted_at"),
]
y = 2.06
for k, (label, v) in enumerate(cols):
    rect(s, 6.94, y, 5.46, 0.46, fill=WHITE, line=LINE, radius=0.12)
    tf = textbox(s, 7.10, y + 0.10, 1.0, 0.26)
    para(tf, label, 9.5, True, BLUE, first=True)
    tf = textbox(s, 8.06, y + 0.10, 4.2, 0.26)
    para(tf, v, 9.5, False, BODY, first=True, name=MONO)
    y += 0.54

rect(s, M, 5.56, 11.9, 0.86, fill=BLUE_SOFT, line=None, radius=0.04)
tf = textbox(s, M + 0.24, 5.70, 11.4, 0.6)
para(tf, "其余字段一律留在 payload jsonb 里：列级 bug 可以从湖重放修复，不需要回头重跑提取。",
     11, True, RGBColor(0x1E, 0x40, 0xAF), first=True)

pg(s)

# ===========================================================================
# 08 设计② data/trace
# ===========================================================================
s = new_slide(prs, BG)
head(s, "设计②  科学事实与证据溯源分开存", "可追溯性")
rule(s)

rect(s, M, 1.76, 4.55, 1.28, fill=WHITE, line=LINE, radius=0.05)
tf = textbox(s, M + 0.24, 1.94, 4.1, 1.2)
para(tf, "core.sample_data", 12, True, INK, first=True, space_after=3, name=MONO)
para(tf, "338 行 / 样品　纯数据版", 10, False, MUTED, space_after=3)
para(tf, "“屈服强度 = 685”", 11, False, TEAL, name=MONO)

rect(s, 6.72, 1.76, 5.9, 1.28, fill=WHITE, line=LINE, radius=0.05)
tf = textbox(s, 6.96, 1.94, 5.4, 1.2)
para(tf, "core.sample_trace", 12, True, INK, first=True, space_after=3, name=MONO)
para(tf, "929 行 / 样品　JSON Pointer 级", 10, False, MUTED, space_after=3)
para(tf, "$.properties[0]…yield_strength[0]  →  [b0013]", 10, False, VIOLET, name=MONO)

# 中间关联
conn = s.shapes.add_shape(MSO_SHAPE.LEFT_RIGHT_ARROW, Inches(5.35), Inches(2.36),
                          Inches(1.28), Inches(0.34))
conn.fill.solid(); conn.fill.fore_color.rgb = RGBColor(0xC7, 0xD2, 0xFE)
conn.line.fill.background()
tf = textbox(s, 5.28, 2.76, 1.45, 0.3)
para(tf, "path 关联", 9, True, MUTED, first=True, align=PP_ALIGN.CENTER)

kpis2 = [("68,944", "条溯源记录"), ("100%", "路径可在 payload 命中"),
         ("0", "条断链"), ("12,793", "条 block_id 对齐")]
for i, (v, l) in enumerate(kpis2):
    x = M + i * 3.02
    tf = textbox(s, x, 3.62, 2.8, 0.44)
    para(tf, v, 24, True, INK, first=True, space_after=0)
    tf = textbox(s, x, 4.10, 2.8, 0.28)
    para(tf, l, 9.5, False, MUTED, first=True)

rect(s, M, 5.02, 11.9, 1.20, fill=WHITE, line=LINE, radius=0.04)
tf = textbox(s, M + 0.26, 5.20, 11.4, 0.95)
para(tf, "为什么要拆开", 11, True, INK, first=True, space_after=4)
para(tf, "事实会随提取版本变化（重跑就变），证据溯源不该变；混在一张表里，"
         "任何一次重跑都会把“这句话从哪来”一起冲掉。拆开后，值可以重算，证据可以独立保留与审计。",
     10.5, False, BODY, line=1.45)

pg(s)

# ===========================================================================
# 09 设计③ 数值归一化
# ===========================================================================
s = new_slide(prs, BG)
head(s, "设计③  把自由文本变成可比较的数值", "数值归一化")
rule(s)

tf = textbox(s, M, 1.64, 6.9, 0.3)
para(tf, "解析结果：kind / 区间 / 规范单位 / 中值", 11, True, MUTED, first=True)

rows = [
    ["原文", "kind", "归一化后"],
    ["685（单位 MPa）", "numeric", "685 MPa"],
    ["427–513 MPa", "range", "[427, 513]，中点 470"],
    ["~350-450", "range", "[350, 450] MPa"],
    ["up to 950 MPa", "open_high", "≤ 950 MPa"],
    ["not less than 40%", "open_low", "≥ 40 %"],
    ["1050 °C", "numeric", "1323.15 K"],
    ["2 h", "numeric", "7200 s"],
    ["increases with Al content…", "qualitative", "保留原文，不臆造"],
]
table(s, M, 1.98, 6.9, rows, [2.75, 1.35, 2.8], size=10, row_h=0.385,
      align=["l", "c", "l"])

# 右侧数字
rect(s, 7.92, 1.98, 4.7, 1.62, fill=WHITE, line=LINE, radius=0.05)
tf = textbox(s, 8.18, 2.16, 4.2, 1.3)
para(tf, "1,304 / 1,508", 26, True, GREEN, first=True, space_after=2)
para(tf, "属性量已数值化（86%）", 10.5, False, MUTED, space_after=6)
para(tf, "规范单位：应力→MPa　尺寸→μm　温度→K　分数→%", 9, False, FAINT, name=MONO)

rect(s, 7.92, 3.76, 4.7, 1.48, fill=BLUE_SOFT, line=None, radius=0.05)
tf = textbox(s, 8.18, 3.94, 4.2, 1.4)
para(tf, "为什么不能只存字符串", 10.5, True, RGBColor(0x1E, 0x40, 0xAF), first=True, space_after=5)
para(tf, "只存原文时，“屈服强度 > 700 MPa”只能 LIKE，\n"
         "区间会被当成文本排序，跨论文无法比较。", 9.5, False, RGBColor(0x1E, 0x40, 0xAF), line=1.45)

tf = textbox(s, M, 5.92, 6.9, 0.9)
para(tf, "解析器是一个纯函数，有 12 个参数化用例守着；遇到“1 295 MPa”（欧洲千分位）"
         "这类写法也能正确解析成 1295。", 9.5, False, FAINT, first=True, line=1.4)

pg(s)

# ===========================================================================
# 10 设计④ block_id 对齐
# ===========================================================================
s = new_slide(prs, BG)
head(s, "设计④  修复断掉的溯源链", "block_id 对齐")
rule(s)

tf = textbox(s, M, 1.68, 6.6, 0.9)
para(tf, "提取产物里，图观察项的 evidence id 有 200+ 种形态：", 11, False, BODY, first=True,
     space_after=4)
para(tf, "b_caption_002 / b_citing_2 / caption_figure_003 / Fig. 4 / bXXXX …", 10,
     False, VIOLET, name=MONO)

tf = textbox(s, M, 2.44, 6.6, 0.5)
para(tf, "而 evidence_blocks.json 里的真实 id 只有 b0001…bNNNN 一种。", 11, False, BODY, first=True)

# 漏斗
funnel = [("12,405", "图观察项"), ("12,793", "条 evidence id"),
          ("99.94%", "可还原"), ("8", "条无法还原（标记保留）")]
x = M
for i, (v, l) in enumerate(funnel):
    w = 2.62
    rect(s, x, 3.22, w, 1.12, fill=WHITE, line=LINE, radius=0.05)
    tf = textbox(s, x + 0.2, 3.36, w - 0.3, 0.42)
    para(tf, v, 19, True, INK if i < 3 else RED, first=True, space_after=0)
    tf = textbox(s, x + 0.2, 3.80, w - 0.3, 0.4)
    para(tf, l, 9, False, MUTED, first=True, line=1.25)
    x += w + 0.16

rows = [
    ["方法", "说明", "数量"],
    ["figure_group", "按“角色 + 图表序号”回查 image_groups 的题注/引用块", "11,796"],
    ["direct", "本身就是 bNNNN（含 b013 → b0013 补零）", "989"],
    ["fuzzy", "从杂串抽取 bNNNN，或按 abstract 语义定位", "8"],
    ["unresolved", "无法还原：保留原值并标记，不臆造", "0"],
]
table(s, M, 4.62, 11.9, rows, [1.9, 8.1, 1.9], size=10, row_h=0.44, align=["l", "l", "r"])

pg(s)

# ===========================================================================
# 11 定位：我们不在他们任何一格里
# ===========================================================================
s = new_slide(prs, BG)
head(s, "我们不在他们任何一格里", "横向对比")
rule(s)

x0, x1, y0, y1 = 1.10, 6.90, 1.80, 5.58
rect(s, x0, y0, x1 - x0, y1 - y0, fill=WHITE, line=LINE, radius=0.02)
mx, my = (x0 + x1) / 2, (y0 + y1) / 2
rect(s, mx, y0, 0.008, y1 - y0, fill=RGBColor(0xEE, 0xF0, 0xF3), shape=MSO_SHAPE.RECTANGLE)
rect(s, x0, my, x1 - x0, 0.008, fill=RGBColor(0xEE, 0xF0, 0xF3), shape=MSO_SHAPE.RECTANGLE)

for tx, ty, txt, al in [(x0 + 0.14, y0 + 0.10, "计算生成 · 任务级溯源", PP_ALIGN.LEFT),
                        (x0 + 0.14, y1 - 0.30, "实验 / 文献 · 记录级溯源", PP_ALIGN.LEFT),
                        (x1 - 0.14, y1 - 0.30, "文献抽取 · 段落级溯源", PP_ALIGN.RIGHT)]:
    tf = textbox(s, tx, ty, 2.5, 0.24, al)
    para(tf, txt, 7.5, False, RGBColor(0xB4, 0xBB, 0xC7), first=True)

tf = textbox(s, mx + 0.10, y0 + 0.10, 2.55, 0.5)
para(tf, "（右上角是空的）", 7.5, False, RGBColor(0xC6, 0xCC, 0xD6), first=True, space_after=1)
para(tf, "计算没有原文，\n也就没有段落可溯。", 7.5, False, RGBColor(0xC6, 0xCC, 0xD6), line=1.3)


def _dot(fx, fy, name, color=MUTED, big=False, left=False, size=8.5, weight=False):
    px, py = x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)
    r = 0.075 if big else 0.055
    d = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(px - r), Inches(py - r),
                           Inches(r * 2), Inches(r * 2))
    d.fill.solid(); d.fill.fore_color.rgb = color
    d.line.fill.background(); d.shadow.inherit = False
    tw = 1.45
    tx = px - 0.10 - tw if left else px + 0.10
    tf = textbox(s, tx, py - 0.115, tw, 0.24, PP_ALIGN.RIGHT if left else PP_ALIGN.LEFT)
    para(tf, name, size, weight, color if weight else BODY, first=True)


_dot(0.32, 0.07, "AFLOW")
_dot(0.18, 0.15, "Materials Project")
_dot(0.44, 0.25, "NOMAD")
_dot(0.07, 0.29, "OQMD")
_dot(0.17, 0.68, "ICSD")
_dot(0.06, 0.84, "COD")
_dot(0.30, 0.89, "MatWeb / 手册")
_dot(0.60, 0.76, "Citrination")
_dot(0.82, 0.60, "SteelDig", BLUE, big=True, left=True, size=9.5, weight=True)

tf = textbox(s, M, 5.72, 6.1, 0.3)
para(tf, "横轴：能回到多细的原文　　纵轴：数据怎么来的", 8.5, False, FAINT, first=True)

# 右：三类
kinds = [
    ("计算型库", "MP · OQMD · AFLOW · NOMAD",
     "记录 = 一次计算。溯源就是 task id，天生完整；单位是 eV / Å，天生统一；身份按结构匹配去重。", MUTED),
    ("实验型库", "ICSD · COD · 手册 / 图集",
     "记录 = 一个晶体结构或一条手册值。溯源到 DOI 为止 —— 页面之内发生了什么，库里没有。", AMBER),
    ("抽取型库", "Citrination · 本项目",
     "记录 = 从一句话里读出的声明。溯源要落到段落，还得能被改 —— 只有这类库必须自带证据工程。", BLUE),
]
y = 1.80
for name, who, desc, color in kinds:
    rect(s, 7.30, y, 5.32, 1.10, fill=WHITE, line=LINE, radius=0.04)
    rect(s, 7.30, y, 0.05, 1.10, fill=color, shape=MSO_SHAPE.RECTANGLE)
    tf = textbox(s, 7.50, y + 0.10, 4.9, 0.26)
    para(tf, name, 10.5, True, INK, first=True)
    tf = textbox(s, 8.62, y + 0.12, 3.8, 0.26)
    para(tf, who, 8, False, FAINT, first=True, name=MONO)
    tf = textbox(s, 7.50, y + 0.40, 4.9, 0.62)
    para(tf, desc, 8.5, False, MUTED, first=True, line=1.45)
    y += 1.20

rect(s, 7.30, 5.42, 5.32, 0.62, fill=BLUE_SOFT, line=None, radius=0.04)
tf = textbox(s, 7.50, 5.54, 4.95, 0.45)
para(tf, "还有 LIMS / ELN：主键是实验单，记录“谁在何时做了什么”，不记录“文献说了什么”。",
     8.5, False, RGBColor(0x1E, 0x40, 0xAF), first=True, line=1.35)

tf = textbox(s, M, 6.12, 11.9, 0.5)
para(tf, "不比规模（MP 是十万量级，这里是 638 个样品），比的是：每一条记录，能不能回到原文那一句。",
     11, True, INK2, first=True)

pg(s)

# ===========================================================================
# 12 两种“真相”来源
# ===========================================================================
s = new_slide(prs, BG)
head(s, "同一张表，两种真相来源", "结构差异")
rule(s)

panels = [
    (M, "计算型　MP / OQMD / AFLOW / NOMAD", "真相在计算里：重算一次就能复现", MUTED,
     [("结构文件", "POSCAR / CIF"),
      ("第一性原理计算", "泛函 · 赝势 · 收敛判据"),
      ("task 记录", "输入 + 输出，本身就是真相"),
      ("材料条目", "mp-1234，按结构去重")],
     "溯源 = task_id，天生完整\n单位 = eV / Å，天生统一　·　身份 = 结构匹配去重"),
    (6.98, "抽取型　本项目", "真相在原文里：只能指回去，不能重算", BLUE,
     [("PDF", "正文 · 表格 · 图 · 题注"),
      ("模型抽取", "会漏字段、会串行、会补全"),
      ("value + block + trace", "值可能错，出处必须留"),
      ("sample 条目", "(paper_id, sample_id)")],
     "溯源 = 必须显式重建（99.94% 可还原）\n单位 = 作者写的，要归一　·　身份 = 论文 × 合金 × 工艺"),
]
for px, title, sub, color, boxes, note in panels:
    tf = textbox(s, px, 1.66, 5.6, 0.3)
    para(tf, title, 11.5, True, INK, first=True)
    tf = textbox(s, px, 1.98, 5.6, 0.28)
    para(tf, sub, 8.5, False, FAINT, first=True)
    y = 2.32
    for i, (name, det) in enumerate(boxes):
        last = i == len(boxes) - 1
        rect(s, px, y, 5.62, 0.54, fill=WHITE if not last else BLUE_SOFT,
             line=LINE if not last else None, radius=0.05)
        tf = textbox(s, px + 0.18, y + 0.08, 2.3, 0.26)
        para(tf, name, 9.5, True, INK if not last else RGBColor(0x1E, 0x40, 0xAF), first=True,
             name=MONO if name[0].isascii() else FONT)
        tf = textbox(s, px + 2.42, y + 0.09, 3.05, 0.26)
        para(tf, det, 8.5, False, MUTED, first=True)
        if not last:
            arrow_down(s, px + 2.76, y + 0.565, 0.175, RGBColor(0x9F, 0xB8, 0xE8), w=0.12)
        y += 0.72
    tf = textbox(s, px, 5.16, 5.62, 0.7)
    para(tf, note, 8.5, False, MUTED, first=True, line=1.45)

rect(s, M, 5.86, 11.88, 0.62, fill=INK, line=None, radius=0.04)
tf = textbox(s, M + 0.28, 5.98, 11.2, 0.44)
para(tf, "计算型多出来的成本是算力；抽取型多出来的成本是证据工程 —— 那 68,944 条 trace，就是这笔成本的账单。",
     10.5, True, WHITE, first=True)

pg(s)

# ===========================================================================
# 13 七维差异总表
# ===========================================================================
s = new_slide(prs, BG)
head(s, "七个维度，一眼看完差异", "框架差异")
rule(s)

rows = [
    ["维度", "主流材料库", "本项目", "为什么必须不同"],
    ["主键与身份", "全局材料 id，按结构去重", "(paper_id, sample_id)：合金 × 工艺", "同一成分、不同工艺是两个样品"],
    ["溯源粒度", "指向计算任务或 DOI，记录级", "JSON Pointer → block_id → 段落与图", "抽取会错，必须能回到原句"],
    ["版本", "按发布整体刷新，无单条历史", "run_id + is_latest，4 个 run 并存", "换模型、重跑不能丢历史"],
    ["数值", "eV / Å 等计算单位，天生统一", "value_kind + 规范单位 + 保留原文", "作者会写「~350-450」和「1 GPa」"],
    ["修正", "以重算为准，不设校订层", "curate.change 叠加层，入库后重放", "人工修正必须活过重跑"],
    ["存储布局", "一个库 + 一个文件服务", "内容寻址湖 + 关系仓 + 库内检索", "要能从原始字节重放事实"],
    ["检索", "化学式、元素、结构相似度", "中文全文 + 模糊 + 语义 + 成分区间", "用户用中文问「为什么加铝降密度」"],
    ["schema 演进", "固定 schema，重算即可", "14 个迁移 + 从湖重放", "上游字段命名会漂移"],
]
table(s, M, 1.66, 11.9, rows, [1.55, 3.55, 3.60, 3.20], size=9, row_h=0.50, header_h=0.36)

tf = textbox(s, M, 6.10, 11.9, 0.4)
para(tf, "一句话：他们在记录“结果”，我们在记录“声明 + 声明的出处 + 出处的修订史”。",
     11.5, True, INK2, first=True)

pg(s)

# ===========================================================================
# 11(原) 检索层
# ===========================================================================
# ===========================================================================
s = new_slide(prs, BG)
head(s, "检索层：三路召回，中文可用", "检索")
rule(s)

signals = [
    ("全文", "tsvector + GIN", "精确术语：κ-碳化物、TWIP", TEAL),
    ("模糊", "pg_trgm · word_similarity", "拼写差异、长中文查询", AMBER),
    ("语义", "pgvector HNSW（384 维）", "概念检索：为什么加铝能降密度", VIOLET),
]
y = 1.70
for name, tech, use, color in signals:
    rect(s, M, y, 5.55, 1.04, fill=WHITE, line=LINE, radius=0.05)
    rect(s, M, y, 0.055, 1.04, fill=color, shape=MSO_SHAPE.RECTANGLE)
    tf = textbox(s, M + 0.24, y + 0.13, 1.0, 0.3)
    para(tf, name, 12.5, True, INK, first=True)
    tf = textbox(s, M + 1.14, y + 0.13, 4.2, 0.3)
    para(tf, tech, 9.5, False, MUTED, first=True, name=MONO)
    tf = textbox(s, M + 1.14, y + 0.48, 4.2, 0.4)
    para(tf, use, 10, False, BODY, first=True)
    y += 1.18

# 融合公式
rect(s, M, 5.30, 5.55, 1.10, fill=INK, line=None, radius=0.05)
tf = textbox(s, M + 0.26, 5.46, 5.05, 0.85)
para(tf, "RRF 融合  score = Σ 1 / (60 + rank)", 11.5, True, WHITE, first=True, space_after=4, name=MONO)
para(tf, "不需要归一化三路分数量纲；任一信号缺失自动降级", 9, False,
     RGBColor(0xA9, 0xB4, 0xC6))

# 右图
picture(s, SHOTS / "05-search.jpg", 6.55, 1.70, 6.05)
tf = textbox(s, 6.55, 5.98, 6.05, 0.5)
para(tf, "中文先 jieba 分词再进 PG 全文索引；查询串与索引共用同一套分词，保证 token 一致。",
     9, False, FAINT, first=True, line=1.35)

pg(s)


# ===========================================================================
# 12 成分检索
# ===========================================================================
s = new_slide(prs, BG)
head(s, "按成分找样品：先给精确，再给最近的", "成分检索")
rule(s)

picture(s, SHOTS / "11-composition-slide.jpg", M, 1.66, 6.55)
tf = textbox(s, M, 6.44, 6.55, 0.3)
para(tf, "周期表里点元素 → 设 wt% 上下限 → 精确匹配 / 最近邻", 8.5, False, FAINT, first=True)

steps = [
    ("输入", "点周期表里的元素，设区间；留空表示“只要含有、不限含量”", BLUE),
    ("精确匹配", "所有指定元素都落在区间内 —— Al 8–11 + Mn 25–30 命中 41 个合金", GREEN),
    ("回退", "没有精确结果时，按到区间的最短距离排序，并标注「Al 低 7.4」", AMBER),
]
y = 1.70
for t, d, c in steps:
    rect(s, 7.35, y, 0.05, 0.86, fill=c, shape=MSO_SHAPE.RECTANGLE)
    tf = textbox(s, 7.56, y + 0.02, 4.9, 0.3)
    para(tf, t, 11, True, INK, first=True)
    tf = textbox(s, 7.56, y + 0.34, 4.9, 0.5)
    para(tf, d, 9, False, MUTED, first=True, line=1.35)
    y += 1.10

rect(s, 7.35, 5.02, 5.05, 1.10, fill=BLUE_SOFT, line=None, radius=0.05)
tf = textbox(s, 7.58, 5.18, 4.6, 0.85)
para(tf, "前置修复：Fe 写成 Bal. 时没有数值", 9.5, True, RGBColor(0x1E, 0x40, 0xAF), first=True, space_after=3)
para(tf, "按 100−Σ其余 补全并标记 is_inferred；界面上带 * 的就是推断值。",
     9, False, RGBColor(0x1E, 0x40, 0xAF), line=1.35)

pg(s)

# ===========================================================================
# 13 湖仓

# ===========================================================================
s = new_slide(prs, BG)
head(s, "资产湖：内容寻址，所以能去重、能重建", "湖仓关系")
rule(s)

code_block(s, M, 1.70, 6.35, 1.78, [
    "05_lake/objects/sha256/",
    "  ab/cd/abcdef…1234.json     ← JSON 产物",
    "  ef/90/ef90…beef.jpg        ← 图表原图",
    "",
    "lake.object      (object_id, bytes, media_type, uri)",
    "lake.object_ref  (object_id, paper_id, rel_path, role)",
], size=9.5)

kpis3 = [("6,667", "个对象"), ("148 MB", "去重后体积"), ("28", "次跨篇复用"), ("0", "个损坏")]
for i, (v, l) in enumerate(kpis3):
    x = M + i * 1.60
    tf = textbox(s, x, 3.86, 1.5, 0.4)
    para(tf, v, 17, True, INK, first=True, space_after=0)
    tf = textbox(s, x, 4.26, 1.5, 0.26)
    para(tf, l, 8.5, False, MUTED, first=True)

tf = textbox(s, M, 4.78, 6.35, 1.7)
para(tf, "重建链路", 10.5, True, INK, first=True, space_after=5)
para(tf, "reset → migrate → ingest --all：30 秒，从湖重放全部事实。\n"
         "因此列级 bug 可以修，不用回头重跑提取。", 10, False, BODY, line=1.45)

# 右侧：三块说明
right_cards = [
    ("为什么用哈希当主键",
     "同一份字节只有一个 object_id：跨论文重复的图片\n自动去重（已复用 28 次）。对象不可变，引用永远有效。"),
    ("完整性校验",
     "verify 会重算 6,667 个对象的 sha256，\n检查孤儿对象与溯源断链：\n损坏 0 · 孤儿 0 · 断链 0。"),
    ("平移到对象存储",
     "写路径已按 S3 key 布局设计，替换 Lake._put() 为\nboto3 put_object 即可，DB 侧零改动；\ncompose 里已带 MinIO profile。"),
]
y = 1.70
for title, body in right_cards:
    rect(s, 7.55, y, 5.07, 1.45, fill=WHITE, line=LINE, radius=0.05)
    tf = textbox(s, 7.80, y + 0.16, 4.6, 1.2)
    para(tf, title, 10.5, True, INK, first=True, space_after=5)
    para(tf, body, 9.5, False, BODY, line=1.5)
    y += 1.60

pg(s)

# ===========================================================================
# 13 CRUD
# ===========================================================================
s = new_slide(prs, BG)
head(s, "增删改查：为什么不能直接改表", "可运营性")
rule(s)

# 三层
layers = [("湖 05_lake", "不可变 · 权威来源", AMBER, 1.66),
          ("核心 core.*", "可重建 · 重跑即覆盖", TEAL, 2.86),
          ("校订 curate.change", "人写 · 持久 · 可审计", RGBColor(0xBE, 0x18, 0x5D), 4.06)]
for name, sub, color, y in layers:
    rect(s, M, y, 3.55, 0.80, fill=WHITE, line=LINE, radius=0.06)
    rect(s, M, y, 0.055, 0.80, fill=color, shape=MSO_SHAPE.RECTANGLE)
    tf = textbox(s, M + 0.24, y + 0.13, 3.2, 0.3)
    para(tf, name, 11.5, True, INK, first=True)
    tf = textbox(s, M + 0.24, y + 0.44, 3.2, 0.26)
    para(tf, sub, 9, False, MUTED, first=True)

arrow_down(s, M + 1.70, 2.50, 0.28)
arrow_down(s, M + 1.70, 3.70, 0.28)

# 右侧说明
rect(s, 4.85, 1.66, 7.75, 0.98, fill=RGBColor(0xFE, 0xF3, 0xF2), line=None, radius=0.04)
tf = textbox(s, 5.08, 1.80, 7.3, 1.05)
para(tf, "实测：直接 UPDATE 会被下一次入库覆盖", 10.5, True, RED, first=True, space_after=4)
para(tf, "把 685 改成 999 → 重跑 ingest → 又变回 685。因为入库是“整篇 DELETE + 重新 COPY”。",
     9.5, False, RGBColor(0x7A, 0x27, 0x1F), line=1.4)

rows = [
    ["能力", "路径", "持久", "审计"],
    ["查", "SQL / REST / 界面", "—", "—"],
    ["改", "POST /api/curate/changes  op=update", "重放后仍生效", "记录前后值"],
    ["增", "新论文走 ETL；新样品 op=create", "是", "可撤销"],
    ["删", "op=delete（重跑后再删一次）", "是", "可撤销"],
]
table(s, 4.85, 2.82, 7.75, rows, [0.85, 3.9, 1.5, 1.5], size=9.5, row_h=0.40)

tf = textbox(s, 4.85, 4.90, 7.75, 0.7)
para(tf, "白名单控制：只有登记过的表 / 列能改，API 不会退化成任意 SQL 执行器。"
         "每次 ingest 结束自动重放全部校订，因此人工修改不会被重跑冲掉。", 9.5, False, MUTED,
     first=True, line=1.5)

tf = textbox(s, M, 5.12, 3.55, 1.4)
para(tf, "写入口：REST · 界面 · CLI", 9.5, True, MUTED, first=True, space_after=4)
para(tf, "steeldig_db curate list / apply / revert", 8.5, False, BODY, name=MONO, line=1.4)

code_block(s, 4.85, 5.62, 7.75, 1.18, [
    '{"op":"update", "target_table":"core.property_value",',
    ' "target_key":{"paper_id":"…","sample_id":"…","path":"$.properties[0]…"},',
    ' "field":"value_canonical", "new_value":690,',
    ' "note":"原文 Table 2 为 690 MPa", "author":"zhang"}',
], size=7.6)

pg(s)

# ===========================================================================
# 14 界面（总览）
# ===========================================================================
s = new_slide(prs, RGBColor(0x0B, 0x12, 0x20))
head(s, "界面：从“能查”到“愿意查”", "交付形态", dark=True)

picture(s, SHOTS / "01-home.jpg", 6.55, 1.62, 6.05)
tf = textbox(s, 6.55, 5.98, 6.05, 0.3)
para(tf, "总览：KPI、强度-塑性散点、合金族构成、强塑积排行", 9, False,
     RGBColor(0x86, 0x98, 0xB8), first=True)

feats = [
    ("10 个页面", "总览 / 样品库 / 文献 / 成分检索 / 检索 / 分析 / 质量"),
    ("服务端渲染", "无构建步骤、ECharts 已 vendor，离线可用"),
    ("图表原图", "按内容哈希从资产湖取，Web 层不存副本"),
    ("与 API 同源", "根路径是界面，/api 与 /docs 是程序入口"),
]
y = 1.70
for t, d in feats:
    tf = textbox(s, M, y, 5.5, 0.3)
    para(tf, t, 12, True, WHITE, first=True)
    tf = textbox(s, M, y + 0.30, 5.5, 0.4)
    para(tf, d, 9.5, False, RGBColor(0x9A, 0xA7, 0xBD), first=True, line=1.35)
    y += 1.06

pg(s, dark=True)

# ===========================================================================
# 15 界面（样品详情）
# ===========================================================================
s = new_slide(prs, BG)
head(s, "样品详情：一屏内回答“这个材料值不值得看”", "交付形态")
rule(s)

picture(s, SHOTS / "03-sample-top.jpg", M, 1.66, 7.35)
tf = textbox(s, M, 6.44, 7.35, 0.3)
para(tf, "成分条 · 工艺时间线 · 相表 · 性能表 · 中文词条 · 真实图表", 8.5, False, FAINT, first=True)

notes = [
    ("证据徽标", "每个性能值后面 ◈ 1 条证据，可点到原文段落", TEAL),
    ("工艺时间线", "熔炼 → 锻造 → 冷却，逐步展开", BLUE),
    ("相表", "相名 + 体积分数 + 晶粒尺寸，已对齐 canon 词表", VIOLET),
    ("人工校订", "底部可直接修正数值并留痕", RGBColor(0xBE, 0x18, 0x5D)),
]
y = 1.70
for t, d, c in notes:
    rect(s, 8.35, y, 0.05, 0.86, fill=c, shape=MSO_SHAPE.RECTANGLE)
    tf = textbox(s, 8.56, y + 0.02, 4.1, 0.3)
    para(tf, t, 11, True, INK, first=True)
    tf = textbox(s, 8.56, y + 0.34, 4.1, 0.5)
    para(tf, d, 9, False, MUTED, first=True, line=1.35)
    y += 1.10

pg(s)

# ===========================================================================
# 16 真实查询
# ===========================================================================
s = new_slide(prs, BG)
head(s, "真实查询：强塑积排行", "用法示例")
rule(s)

code_block(s, M, 1.70, 6.30, 2.70, [
    "SELECT sample_id, formula,",
    "       yield_strength_mpa  AS ys,",
    "       elongation_pct      AS el,",
    "       round((tensile_strength_mpa",
    "             * elongation_pct / 100)::numeric, 0)",
    "                            AS uts_x_el",
    "FROM api.sample_summary",
    "WHERE tensile_strength_mpa IS NOT NULL",
    "  AND elongation_pct IS NOT NULL",
    "ORDER BY uts_x_el DESC NULLS LAST",
    "LIMIT 5;",
], size=9)

rows = [
    ["样品", "YS", "EL", "UTS×EL"],
    ["FeMn28Al9C0.9　热轧+冷轧", "504", "86.0", "778"],
    ["FeMn28.3Al9C0.9　热轧", "670", "68.0", "666"],
    ["FeMn30C1.2　均匀化+水淬", "360", "77.0", "639"],
    ["FeMn21Al8.5C1.3　固溶水淬", "700", "55.0", "633"],
    ["FeMn28Al10C0.8N0.1326", "647", "74.5", "627"],
]
table(s, 7.30, 1.70, 5.32, rows, [2.55, 0.85, 0.85, 1.07], size=9.5, row_h=0.40,
      align=["l", "r", "r", "r"])

rect(s, 7.30, 4.36, 5.32, 1.68, fill=WHITE, line=LINE, radius=0.04)
tf = textbox(s, 7.52, 4.52, 4.9, 1.4)
para(tf, "为什么这个结果是可信的", 10, True, INK, first=True, space_after=4)
para(tf, "Fe-28Mn-9Al-0.9C 是低密度钢的经典体系，\n"
         "905 MPa × 86% ≈ 778 GPa·% 与文献报道量级一致。\n"
         "如果单位换算错了，这个数会离谱到一眼可见。", 9, False, MUTED, line=1.45)

tf = textbox(s, M, 4.62, 6.3, 1.5)
para(tf, "同一套 SQL 可以直接换成任意维度：", 9.5, True, MUTED, first=True, space_after=4)
para(tf, "按元素筛（含 Al ≥ 8 wt%）· 按相筛（铁素体 > 5%）\n"
         "按工艺筛（退火 ≥ 900 °C）· 按证据查（这个值出自哪段）", 9.5, False, BODY, line=1.5)

pg(s)

# ===========================================================================
# 17 质量与测试
# ===========================================================================
s = new_slide(prs, BG)
head(s, "质量：0 个 error，844 条 warn 全部可解释", "质量门禁")
rule(s)

kpis4 = [("95", "项测试全部通过"), ("0", "error 级问题（阻断发布）"), ("844", "条 warn（可解释）"),
         ("48", "个表 / 视图")]
for i, (v, l) in enumerate(kpis4):
    x = M + i * 3.02
    tf = textbox(s, x, 1.66, 2.8, 0.46)
    para(tf, v, 26, True, INK, first=True, space_after=0)
    tf = textbox(s, x, 2.16, 2.8, 0.28)
    para(tf, l, 9.5, False, MUTED, first=True)

# 原生图表：指标覆盖
chart_data = CategoryChartData()
chart_data.categories = ["硬度", "延伸率", "屈服强度", "抗拉强度", "密度", "弹性模量"]
chart_data.add_series("行数", (329, 305, 273, 268, 160, 27))
chart_data.add_series("可数值化", (312, 272, 235, 244, 153, 18))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(M), Inches(2.62),
                        Inches(6.55), Inches(3.30), chart_data)
chart = gf.chart
chart.has_title = True
chart.chart_title.text_frame.text = "关键指标的数值化覆盖"
for p in chart.chart_title.text_frame.paragraphs:
    for r in p.runs:
        r.font.size = Pt(10.5); r.font.bold = True; r.font.color.rgb = INK
chart.has_legend = True
chart.legend.position = XL_LEGEND_POSITION.TOP
chart.legend.include_in_layout = False
chart.legend.font.size = Pt(9)
chart.font.size = Pt(9)
chart.font.color.rgb = MUTED
# 去掉图表外框（python-pptx 没有高层 API，直接写 c:spPr）
from pptx.oxml.ns import qn as _qn
_cs = chart._chartSpace
_sp = _cs.find(_qn("c:spPr"))
if _sp is None:
    _sp = _cs.makeelement(_qn("c:spPr"), {})
    _cs.insert(list(_cs).index(_cs.find(_qn("c:chart"))) + 1, _sp)
_ln = _sp.makeelement(_qn("a:ln"), {})
_ln.append(_ln.makeelement(_qn("a:noFill"), {}))
_sp.append(_ln)
# 绘图区同样去边框
_pa = _cs.find(_qn("c:chart")).find(_qn("c:plotArea"))
_psp = _pa.find(_qn("c:spPr"))
if _psp is None:
    _psp = _pa.makeelement(_qn("c:spPr"), {})
    _pa.append(_psp)
_pln = _psp.makeelement(_qn("a:ln"), {})
_pln.append(_pln.makeelement(_qn("a:noFill"), {}))
_psp.append(_pln)
va = chart.value_axis
va.has_major_gridlines = True
va.major_gridlines.format.line.color.rgb = RGBColor(0xF1, 0xF2, 0xF5)
va.major_gridlines.format.line.width = Pt(0.5)
va.format.line.color.rgb = RGBColor(0xE6, 0xE8, 0xEC)
va.tick_labels.font.size = Pt(8.5)
chart.category_axis.tick_labels.font.size = Pt(9)
plot = chart.plots[0]
plot.gap_width = 60
plot.series[0].format.fill.solid(); plot.series[0].format.fill.fore_color.rgb = RGBColor(0x93, 0xB4, 0xF8)
plot.series[1].format.fill.solid(); plot.series[1].format.fill.fore_color.rgb = BLUE

# 右侧 warn 明细
rows = [
    ["warn 规则", "数量", "含义"],
    ["FIGURE_EVIDENCE_EMPTY", "821", "非视觉观察项缺 evidence"],
    ["BLOCK_ID_UNRESOLVED", "15", "引用 figure_XXX 且该组无题注"],
    ["WIKI_SECTION_LEAK", "8", "mechanisms 混入章节名，已剔除"],
]
table(s, 7.55, 2.66, 5.07, rows, [2.0, 0.72, 2.35], size=8.5, row_h=0.52,
      align=["l", "r", "l"])

tf = textbox(s, 7.55, 4.92, 5.07, 1.4)
para(tf, "已知缺陷（需要上游改进）", 9.5, True, INK, first=True, space_after=4)
para(tf, "· 27% 样品没有结构化性能（提取阶段 properties 为空）\n"
         "· 硬度口径混杂 HV / HRC / MPa，查询须带标尺\n"
         "· 751 条图观察项无题注可溯", 9, False, MUTED, line=1.55)

pg(s)

# ===========================================================================
# 18 收尾
# ===========================================================================
s = new_slide(prs, RGBColor(0x0B, 0x12, 0x20))
glow = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(-3.4), Inches(4.4), Inches(7.2), Inches(7.2))
glow.fill.solid(); glow.fill.fore_color.rgb = RGBColor(0x10, 0x18, 0x2A)
glow.line.fill.background(); glow.shadow.inherit = False

tf = textbox(s, M, 1.30, 10, 0.3)
para(tf, "下一步", 10.5, True, RGBColor(0x7D, 0xA7, 0xFF), first=True)

tf = textbox(s, M, 1.70, 10.5, 0.7)
para(tf, "这套库已经可用，但还没到“运营级”", 27, True, WHITE, first=True)

items = [
    ("多模型对比", "把 flash / qwen 的输出也灌进来，用 run_id 做一致性分析，表结构不用改"),
    ("并发与审批", "校订目前无乐观锁、无审批流；多人协作前必须补上"),
    ("批量导入", "从 Excel 灌校订还缺一个 CSV loader，结构已就绪"),
    ("canonical 消解", "跨论文“同一合金 / 同一相”的合并，留给规模上来之后"),
]
y = 2.62
for i, (t, d) in enumerate(items):
    tf = textbox(s, M, y, 0.5, 0.32)
    para(tf, f"{i + 1:02d}", 11, True, RGBColor(0x5D, 0x6E, 0x8C), first=True, name=MONO)
    tf = textbox(s, M + 0.55, y - 0.02, 2.2, 0.3)
    para(tf, t, 12, True, WHITE, first=True)
    tf = textbox(s, M + 2.85, y - 0.02, 7.6, 0.4)
    para(tf, d, 10, False, RGBColor(0x9A, 0xA7, 0xBD), first=True)
    y += 0.86

rect(s, M, 6.22, 11.9, 0.02, fill=RGBColor(0x2A, 0x36, 0x4D), shape=MSO_SHAPE.RECTANGLE)
tf = textbox(s, M, 6.42, 11.9, 0.4)
para(tf, "交付物：PostgreSQL 实例 · 14 个迁移 · ETL / API / 界面代码 · 10 份文档 · 95 项测试",
     9.5, False, RGBColor(0x5C, 0x67, 0x79), first=True)


# ===========================================================================
# 备注（演讲提示）
# ===========================================================================
NOTES = [
 "开场：一句话说明这是什么——把 68 篇低密度钢文献，变成一个能查、能溯源、能运营的数据库。",
 "先给路线图：今天只重点回答两个问题——为什么长成这样（第 2 段）、和别人差在哪（第 4 段）。",
 "先说清痛点：原始资产是给人看的，不是给查询用的。三个问题对应后面三个能力。",
 "强调 68/68 一一对应：这是后面所有 join 的前提。顺便解释为什么 _monitor 和 PDF 没进库。",
 "四层从下往上是“写”，从上往下是“读”。核心一句：湖可重建仓，所以事实层可以被放心重算。",
 "这一页把原文那张四层表逐层对账。重点说“哪一层改了什么”：消费层多了界面、检索层换了实现方式、资产湖暂时用本地目录。",
 "这一页是全场最重要的一页。只讲一个前提：抽取一定有错。然后一条一条往下推——"
 "为什么要 trace、为什么版本化、为什么要校订层、为什么要湖、为什么还要列。"
 "可以反问听众：如果抽取是对的，这个库其实可以只有一张表。",
 "这四条不是口号，右边那列是能被测试或 SQL 验证的东西。它们就是上一页那五个推论的合同条款。",
 "选型这页要主动拆掉“为什么不用 ES / Neo4j”的疑问。重点讲最后那句：不是一个事务里的东西，"
 "最后都要靠补偿去凑一致性。",
 "这页是给技术负责人看的：每个决定都标了价钱。被问“能不能更省”时，就用这页回答——能，但要拿什么换。",
 "这页回答“表是怎么长出来的”：每张表都能指回一件产物。特别提 timing → ops.ingest_run，说明成本可以归因到每次入库。",
 "七个 schema 的职责边界。强调 sample 是枢纽：所有性能和证据都挂在样品下。",
 "可以现场翻一个 data.json，说明为什么不能全拍平——100 多个字段里大部分是 null。",
 "trace 是可追溯性的地基。这里值得强调 100% 命中是测试守着的，不是“大概对”。",
 "举几个真实例子，说明“自己写解析器”比想象中麻烦，但也比想象中值。",
 "这是一个数据缺陷被工程化修复的例子：200 多种 id 形态，最后 8 条修不了，就老老实实标出来。",
 "定位图先解释两个轴：横轴是能回到多细的原文，纵轴是数据怎么来的。右上角是空的，"
 "因为计算没有原文。我们和 Citrination 在同一格，但他们是记录级溯源，我们是段落级。",
 "左右两条流水线对照着讲：左边真相在计算里，右边真相在原文里。所以左边不需要证据工程，右边必须自建。",
 "这张表是第 4 段的落点。八行不用逐行念，挑“主键 / 溯源 / 修正”三行讲，最后念那句一句话总结。",
 "中文分词放在 ETL 侧是权衡：PG 没有原生中文分词，但要保证索引和查询用同一套切分。",
 "成分检索是研究者的真实入口。左侧是截图，右侧三步讲清“先精确、再最近邻”。"
 "顺手提一句：Fe 写成 Bal. 导致 60% 合金查不到 Fe，这个坑我们是先审计再补的。",
 "哈希主键带来两个好处：天然去重、天然可校验。这也是为什么敢说“可以从湖重建”。",
 "CRUD 这块要主动说清限制：不是不能改，而是不能直接改表。",
 "界面不追求炫，追求“三秒内判断这个样品值不值得看”。",
 "重点指出右边四个点，尤其是证据徽标和真实图表——这两点让它不像一个 JSON 查看器。",
 "用一个可信的结果收尾：数字和文献量级对得上，说明单位换算没出错。",
 "诚实报告：0 error 但仍有 844 warn，以及三条上游缺陷。",
 "收尾：可用 ≠ 运营级。四个下一步，按优先级排。",
]
for _s, _n in zip(prs.slides, NOTES):
    _s.notes_slide.notes_text_frame.text = _n

prs.save(OUT)
print(f"saved {OUT}  slides={len(prs.slides)}")
