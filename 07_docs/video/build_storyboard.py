"""Generate the editorial Markdown and review page from the v2 scene data."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "v2"
ACTIONS = [
    "首页停在标题和 KPI；第 6 秒缓慢下滚到强度–塑性散点图，留出阅读时间。",
    "依次点 Al、Mn，输入 Al 8–11、Mn 25–30 wt%，搜索。下滚展示蓝色结果条“41 个完全匹配的合金”；再滚到 FeMn28Al10C0.8N0.0025，打开 LN 样品。",
    "接上镜同一 LN 样品：成分、热加工步骤、性能同屏。停在 yield strength 685 MPa，随后指向旁边的证据链接。",
    "点击屈服强度后的证据链接进入 b0029。停在 LN 行，核对 YS 685(±1.5)；再指向右侧引用关系。这里是抽取的原文证据块，不是 PDF 阅读器。",
    "切到 Al 20–25 wt% 条件，先看区间，再下滚到橙色提示和最近候选。第一条 Al 12.6 wt%，相对目标下限低 7.4 个百分点。",
    "输入 κ-碳化物并检索；展示来源、类型和摘要，缓慢下滚一次。是否启用语义召回，以页面实际状态为准。",
    "回到同一 LN 样品，展开“修正一条性能值”；选 yield_strength，填草稿 690 和“演示草稿：请先核对原文，不提交”。不点提交。",
    "质量页停在“无 error · 可发布”，展示 warn 规则数量，然后下滚到人工校订汇总。告警合计 821 + 15 + 8 = 844。",
    "回到首页，保留 SteelDig 标题和片尾文案，最后留约 2 秒安静画面。",
]


def clock(t):
    return f"{t//60:02}:{t%60:02}"


def main():
    scenes = json.loads((OUT / "scenes.json").read_text())
    md = """# SteelDig 材料知识库 · 演示视频分镜 v2.0

- 版本日期：2026-10-23；数据为当日服务快照，后续录制需重新核验。
- 主片：2 分 32 秒，9 镜，真实浏览器录屏，中文合成旁白与中文字幕。
- 审片入口：v2/index.html；主片：v2/SteelDig_演示预览_v2.mp4。

## 一、叙事与取舍

以研究者的问题开场：我能找到什么材料，这个数值从哪里来？围绕同一个 LN 低氮样品，串起“筛选 → 理解 → 核对 → 探索 → 检索 → 校订入口 → 质量”。重点展示成分条件、685 MPa 与原文表格。

SQL 与“直接改表 / 校订重放”移至可选技术加长版。删除原稿清空全部校订记录的准备步骤；主片不需要复位数据库。本次未提交校订、未重灌、未修改数据库事实。

有据属性可以跳转原文，弱溯源仍保留标记；不能宣称每个数值都有完整证据。0 error 是当前质量规则的结果，844 warn 仍需检查；不能标注“全部可解释”或“数据没有缺陷”。表单中的 690 只是未提交草稿，不代表核实后的正确值，也不证明本次验证了重跑持久性。

## 二、时间轴与逐字旁白

“／”表示段间停顿。旁白和时长由 v2/scenes.json 管理；实际配音时间点见 v2/narration_timing.json。

| 镜号 / 时间 | 镜头标题 | 逐字旁白 |
|---|---|---|
"""
    total = 0
    cards = []
    for i, (scene, action) in enumerate(zip(scenes, ACTIONS), 1):
        timing = f'{clock(total)}–{clock(total+scene["duration"])}'
        md += f'| {i:02} / {timing}（{scene["duration"]}s） | {scene["title"]} | {"／".join(scene["lines"])} |\n'
        cards.append(f'<article><a href="screenshots/take_{scene["id"]}.png"><img src="screenshots/take_{scene["id"]}.png" loading="lazy" alt="镜 {i} 实录"></a><div><small>{i:02} · {timing}</small><h3>{html.escape(scene["title"])}</h3><p>{html.escape(action)}</p><blockquote>{html.escape(" ".join(scene["lines"]))}</blockquote><a href="recordings/{scene["id"]}.webm">原始录屏 ↗</a></div></article>')
        total += scene["duration"]
    md += "\n## 三、逐镜操作\n\n"
    for i, (scene, action) in enumerate(zip(scenes, ACTIONS), 1):
        md += f'### 镜 {i:02} · {scene["title"]}\n\n{action}\n\n'
    md += """## 四、已核验的画面锚点

| 对象 | 服务快照 | 口径与限制 |
|---|---|---|
| 数据规模 | 68 篇文献、250 个合金、638 个样品 | 成分页当前有 249 个可解析成分的合金，口径不同 |
| 性能 | 1,304 条可数值化性能；总属性 1,508 条 | 不混用总属性数与可数值化性能数 |
| 精确条件 | Al 8–11 + Mn 25–30 wt% → 41 个合金 | 是合金数，不是样品数；页面仅展示部分结果 |
| LN 样品 | Mn 28、Al 10、C 0.8、N 0.0025 wt%；YS 685 MPa、UTS 832.5 MPa、EL 62.5% | 与精确检索选中的记录一致 |
| 原文证据 | 10.1002_srin.202100643 / b0029，保留 685(±1.5) | 展示抽取证据块，不称为原始 PDF 画面 |
| 最近候选 | Al 12.6 wt%，距目标下限 20 wt% 低 7.4 | 是百分点差，不是相对误差 7.4% |
| 质量 | 0 error、844 warn（821 + 15 + 8） | 保留告警，避免绝对质量承诺 |

完整核验结果在 v2/verification.json，包括 API 结果、证据文本、属性路径、浏览器错误和手机溢出检查。

## 五、页面与录制环境

| 页面 | URL |
|---|---|
| 首页 | http://127.0.0.1:8011/ |
| 成分检索 | http://127.0.0.1:8011/composition |
| 精确条件 | http://127.0.0.1:8011/composition?el=Al:8-11&el=Mn:25-30 |
| 最近条件 | http://127.0.0.1:8011/composition?el=Al:20-25 |
| LN 样品 | http://127.0.0.1:8011/samples/10.1002_srin.202100643/sample_fe-28mn-10al-0.8c-0.0025n__hot-forged-1123-1323k-ac |
| 原文表格 | http://127.0.0.1:8011/evidence/10.1002_srin.202100643/b0029 |
| 检索 | http://127.0.0.1:8011/search?q=κ-碳化物 |
| 质量 | http://127.0.0.1:8011/quality |

- 采集视口 1440×810，输出 1920×1080；另附 1920×1080 桌面静帧、390px 手机长截图。录屏不含地址栏和桌面通知，不宣称素材原生 60 fps。
- 上方章节条高 80px，下方字幕区高 118px；关键数值需滚到中部。操作指示圈为录制叠层，不属于产品 UI。
- 深蓝 #0B1220 为底，蓝色用于操作与精确结果，橙色用于无完全匹配提示；绿色仅用于页面实际质量状态。采用硬切，无背景音乐。
- 旁白使用本机 Tingting 合成语音，供审节奏，可按逐字稿重新录制真人声音。字幕 34px，宽度不超 1600px，最多两行；次要界面文字可暂停阅读，关键数值按需局部放大。
- 导出 H.264 / yuv420p / 25 fps / AAC。成片烧录字幕，另交独立 SRT。当前不宣称已完成专业配音或响度母带处理。

## 六、复现与后期修改

从仓库根目录执行；需本地服务、Python Playwright 与浏览器、Pillow、numpy、ffmpeg 和 macOS Tingting 语音。

```bash
# 只读截图与数据核验
/Users/mac/miniconda3/bin/python database/07_docs/video/capture_demo.py
# 逐镜录屏，脚本阻止 GET / HEAD / OPTIONS 以外的请求
/Users/mac/miniconda3/bin/python database/07_docs/video/capture_demo.py --record
# 旁白、章节条、字幕与合成
/Users/mac/miniconda3/bin/python database/07_docs/video/build_preview.py
# 更新 Markdown、审片网页与 Word
/Users/mac/miniconda3/bin/python database/07_docs/video/build_storyboard.py
database/06_db/.venv/bin/python database/07_docs/video/make_script_doc.py
```

叙事和时长编辑 v2/scenes.json；操作编辑 capture_demo.py 与 build_storyboard.py 的 ACTIONS。修改台词后删除 v2/media 中对应行的缓存 WAV / AIFF 再合成；改变时长需重新录屏。目前录屏脚本每次重录全部镜头。旧版视频保留，不覆盖。

## 七、可选技术加长版（本次未录制）

SQL 可增加 15–20 秒：预先写好只读查询，运行并解释，不在片中逐字输入长 SQL。下列 UTS×EL/100 沿用旧稿口径，单位 MPa，不与直接使用百分数相乘的 MPa·% 数值混用。WHERE 已排除空值，无需旁白解释 NULLS LAST。

```sql
SELECT paper_id, sample_id,
       round((tensile_strength_mpa * elongation_pct / 100)::numeric, 0) AS uts_x_el
FROM api.sample_summary
WHERE tensile_strength_mpa IS NOT NULL AND elongation_pct IS NOT NULL
ORDER BY uts_x_el DESC, paper_id, sample_id
LIMIT 5;
```

校订重放可增加 35–45 秒：在隔离演示库中保存目标记录与现有校订，核对具体 run_id 和 path；根据原文建立一条校订，显示审计记录，再重跑指定论文核对持久性。只录真实命令、真实时间和真实结果；压缩等待时间时加标注。结束后撤销本次 change_id，不清空 curate.change。不要把示例 690 当成已经核实的正确值。本次主片只展示校订入口，没有验证或演示重灌能力。

## 八、交付与验收

- v2/SteelDig_演示预览_v2.mp4：2:32 带合成旁白预览；v2/SteelDig_中文字幕_v2.srt：独立字幕。
- v2/index.html：视频、逐镜图、旁白与原始录屏链接；v2/封面.png：封面。
- 脚本分镜.md 和数据库目录下 SteelDig_演示视频_分镜脚本.docx：同源脚本。
- v2/recordings/：9 段浏览器真实录屏；v2/screenshots/：桌面、手机与逐镜静帧。
- 验收：41 个合金、685 MPa、b0029 表格、7.4 差值、844 warn 与对应台词一致；校订未提交；完整观看检查字幕安全区和操作节奏。
- 已新增测试覆盖证据链接、校订属性路径和表格安全渲染。手机首页、样品、成分页无整页横向溢出；桌面检查无浏览器脚本错误。
"""
    (ROOT / "脚本分镜.md").write_text(md)
    page = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SteelDig · 演示审片 v2</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b1220;color:#e8eef9;font:15px/1.8 -apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif}main{max-width:1280px;margin:auto;padding:54px 32px}small{color:#80aaff;letter-spacing:1px}h1{font-size:42px;line-height:1.3;margin:18px 0}p{color:#9cadc8}a{color:#8cb7ff}video{width:100%;border:1px solid #294064;border-radius:14px;background:#030812;margin:20px 0}.meta{display:flex;gap:24px;flex-wrap:wrap;border-bottom:1px solid #253349;padding-bottom:26px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:32px}article{border:1px solid #253349;border-radius:12px;overflow:hidden;background:#101c2e}article img{width:100%;display:block}article>div{padding:22px}h3{font-size:20px;margin:8px 0}blockquote{margin:16px 0;color:#bccce3;border-left:2px solid #3f73c6;padding-left:14px;font-size:14px}footer{margin-top:40px;color:#8194b0}@media(max-width:700px){main{padding:28px 16px}h1{font-size:30px}.grid{grid-template-columns:1fr}}
</style><main><small>STEELDIG · DEMO FILM / V2.0</small><h1>从材料问题出发，回到原文证据。</h1><p>2 分 32 秒 · 真实浏览器操作 · 中文合成旁白 · 2026.10.23 数据快照</p><video controls preload="metadata" poster="封面.png"><source src="SteelDig_演示预览_v2.mp4" type="video/mp4"></video><div class="meta"><a href="SteelDig_演示预览_v2.mp4" download>下载 MP4</a><a href="SteelDig_中文字幕_v2.srt">中文字幕</a><a href="../脚本分镜.md">分镜脚本</a><a href="../../../SteelDig_演示视频_分镜脚本.docx">Word 文档</a><a href="SteelDig_演示视频_分镜脚本.pdf">PDF 分镜</a><a href="verification.json">核验快照</a></div><p>校订只填写未提交草稿。本片未运行数据库重灌；语音为本机合成，供审片。</p><div class="grid">"""
    page += "".join(cards) + "</div><footer>旧版视频保留在上级目录。台词与时间轴：scenes.json；原始录屏：recordings/。</footer></main></html>"
    (OUT / "index.html").write_text(page)
    print(f"saved storyboard and review page ({total}s)")


if __name__ == "__main__":
    main()
