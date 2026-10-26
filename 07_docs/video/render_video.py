"""生成 SteelDig 功能演示视频：帧序列 → ffmpeg → mp4，并配上旁白。

用法：
    python render_video.py                     # 渲染完整视频
    python render_video.py preview 14 27 44    # 导出指定秒数的静帧，检查版式

依赖：Pillow、numpy、ffmpeg、macOS 的 say（旁白）。
素材：shots/*.png（页面截图）、audio/*.wav + timing.json（旁白）。
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "shots"
AUDIO = ROOT / "audio"
OUT = ROOT / "SteelDig_功能演示.mp4"

W, H = 1920, 1080
FPS = 25

BG_TOP = (11, 18, 32)
BG_BOT = (7, 12, 22)
SURF = (16, 24, 40)
SURF_2 = (22, 32, 51)
BORDER = (34, 46, 68)
INK = (231, 236, 245)
BODY = (196, 206, 222)
MUTED = (148, 163, 184)
FAINT = (100, 116, 139)
GREEN = (52, 211, 153)
BLUE = (96, 165, 250)
AMBER = (251, 191, 36)
RED = (248, 113, 113)
VIOLET = (167, 139, 250)
TEAL = (45, 212, 191)

CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"
MONO = "/System/Library/Fonts/Menlo.ttc"

_fonts = {}


def cjk(size, bold=False):
    k = ("cjk", size, bold)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(CJK, size, index=1 if bold else 0)
    return _fonts[k]


def mono(size, bold=False):
    k = ("mono", size, bold)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(MONO, size, index=1 if bold else 0)
    return _fonts[k]


def background():
    img = Image.new("RGB", (W, H), BG_BOT)
    d = ImageDraw.Draw(img)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)],
               fill=tuple(int(BG_TOP[i] * (1 - k) + BG_BOT[i] * k) for i in range(3)))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W - 760, -520, W + 300, 500], fill=(16, 30, 56))
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(160)), 0.55)
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdd = ImageDraw.Draw(grid)
    for x in range(0, W, 60):
        gdd.line([(x, 0), (x, H)], fill=(255, 255, 255, 5))
    for y in range(0, H, 60):
        gdd.line([(0, y), (W, y)], fill=(255, 255, 255, 5))
    return Image.alpha_composite(img.convert("RGBA"), grid).convert("RGB")


def rr(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def wrap(s, font, max_w):
    lines, cur = [], ""
    for ch in s:
        if font.getlength(cur + ch) > max_w:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def draw_chrome(d, box, title, kind="term"):
    x, y, x2, y2 = box
    rr(d, box, 16, fill=SURF, outline=BORDER, width=2)
    rr(d, (x, y, x2, y + 46), 16, fill=SURF_2)
    d.rectangle((x, y + 30, x2, y + 46), fill=SURF_2)
    for i, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        d.ellipse((x + 20 + i * 22, y + 17, x + 32 + i * 22, y + 29), fill=c)
    if kind == "term":
        d.text((x + 100, y + 11), title, font=mono(18), fill=MUTED)
    else:
        ub = (x + 96, y + 10, x2 - 24, y + 36)
        rr(d, ub, 13, fill=(13, 20, 34), outline=(40, 54, 78))
        d.text((ub[0] + 16, y + 14), title, font=mono(16), fill=BODY)


def progress(d, t, total):
    d.rectangle((0, H - 5, W, H), fill=(18, 26, 43))
    d.rectangle((0, H - 5, int(W * min(t / max(total, 0.1), 1.0)), H), fill=BLUE)


def subtitle(d, s):
    if not s:
        return
    f = cjk(30)
    max_w = int(W * 0.70)
    lines = wrap(s, f, max_w)[:3]
    lh = 46
    box_h = lh * len(lines) + 30
    y0 = H - 40 - box_h
    box = (W // 2 - max_w // 2 - 40, y0, W // 2 + max_w // 2 + 40, y0 + box_h)
    rr(d, box, 16, fill=(8, 13, 24), outline=(30, 42, 62))
    for i, ln in enumerate(lines):
        d.text((W // 2, y0 + 18 + i * lh), ln, font=f, fill=INK, anchor="ma")


@dataclass
class Scene:
    key: str
    dur: float
    draw: object
    caption: str = ""


@dataclass
class Line:
    s: str
    t: float
    color: tuple = BODY
    kind: str = "out"
    cps: float = 45.0


def ease_out(t, dur):
    k = min(1.0, t / max(dur, 0.001))
    return 1 - (1 - k) ** 3


def has_cjk(s):
    return any("\u4e00" <= ch <= "\u9fff" for ch in s)


def terminal_scene(key, lines, dur, caption, title="steeldig — zsh", note_color=AMBER):
    lh = 40
    need = 74 + sum(lh if ln.kind != "gap" else lh // 2 for ln in lines) + 48
    box = (140, 108, W - 140, min(108 + need, H - 215))
    x0, y0, x1, y1 = box
    tx, ty = x0 + 34, y0 + 74

    def draw(img, t):
        d = ImageDraw.Draw(img)
        draw_chrome(d, box, title, "term")
        y = ty
        for ln in lines:
            if t < ln.t:
                break
            if ln.kind == "gap":
                y += lh // 2
                continue
            if y > y1 - 54:
                break
            f = cjk(24) if (ln.kind == "note" or has_cjk(ln.s)) else mono(24)
            if ln.kind == "cmd":
                shown = ln.s[: max(0, int((t - ln.t) * ln.cps))]
                d.text((tx, y), "$ ", font=f, fill=GREEN)
                x = tx + f.getlength("$ ")
                d.text((x, y), shown, font=f, fill=INK)
                if len(shown) < len(ln.s):
                    cx = x + f.getlength(shown)
                    d.rectangle((cx + 1, y + 3, cx + 11, y + 27), fill=GREEN)
            elif ln.kind == "note":
                d.text((tx, y), "· ", font=f, fill=note_color)
                d.text((tx + f.getlength("· "), y), ln.s, font=f, fill=note_color)
            else:
                d.text((tx + f.getlength("  "), y), ln.s, font=f, fill=ln.color)
            y += lh
        subtitle(d, caption)

    return Scene(key, dur, draw, caption)


def browser_scene(key, shot, dur, caption, url, zoom=(1.0, 1.04),
                  focus=None, callouts=(), box=(110, 96, 1540, H - 232)):
    src = Image.open(SHOTS / shot).convert("RGB")
    x0, y0, x1, y1 = box
    view = (x0 + 10, y0 + 56, x1 - 10, y1 - 10)
    vw, vh = view[2] - view[0], view[3] - view[1]
    scale0 = max(vw / src.width, vh / src.height)

    def draw(img, t):
        d = ImageDraw.Draw(img)
        draw_chrome(d, box, url, "browser")
        k = ease_out(t, dur)
        z = zoom[0] + (zoom[1] - zoom[0]) * k
        sc = scale0 * z
        nw, nh = int(src.width * sc), int(src.height * sc)
        panel = src.resize((nw, nh), Image.LANCZOS)
        fx, fy = focus if focus else (0.5, 0.42)
        left = max(0, min(int(nw * fx - vw / 2), max(0, nw - vw)))
        top = max(0, min(int(nh * fy - vh / 2), max(0, nh - vh)))
        img.paste(panel.crop((left, top, left + vw, top + vh)), (view[0], view[1]))
        d.rectangle(view, outline=(30, 42, 62), width=2)

        for i, (nx, ny, label, color) in enumerate(callouts):
            start = 0.55 + i * 0.75
            if t < start:
                continue
            px = view[0] + int(vw * nx)
            py = view[1] + int(vh * ny)
            r = int(9 + 3 * math.sin((t - start) * 3.2))
            d.ellipse((px - r, py - r, px + r, py + r), outline=color, width=3)
            d.ellipse((px - 3, py - 3, px + 3, py + 3), fill=color)

            bx = view[2] + 30
            by = view[1] + 26 + i * 116
            f2 = cjk(19)
            bw = 316
            rr(d, (bx, by, bx + bw, by + 92), 12, fill=(9, 14, 26), outline=color)
            d.rectangle((bx + 1, by + 14, bx + 5, by + 78), fill=color)
            for j, ln in enumerate(wrap(label, f2, bw - 36)[:3]):
                d.text((bx + 20, by + 14 + j * 27), ln, font=f2,
                       fill=color if j == 0 else BODY)
            d.line([(bx, by + 46), (px + r + 6, py)], fill=color, width=2)
            d.ellipse((px + r + 1, py - 4, px + r + 10, py + 5), fill=color)

        subtitle(d, caption)

    return Scene(key, dur, draw, caption)


def title_scene(dur):
    def draw(img, t):
        d = ImageDraw.Draw(img)
        a = ease_out(t, 0.9)
        y = 300 + int(18 * (1 - a))
        d.text((140, y), "SteelDig", font=cjk(92, True), fill=INK)
        d.text((140, y + 124), "材料知识库 · 功能演示", font=cjk(52), fill=BODY)
        d.rectangle((140, y + 212, 140 + int(120 * a), y + 218), fill=BLUE)
        d.text((140, y + 262),
               "68 篇文献 · 638 个样品 · 1,304 条可数值化性能 · 68,944 条溯源",
               font=cjk(28), fill=MUTED)
        d.text((140, H - 116), "PostgreSQL 16 + pgvector · FastAPI · 服务端渲染界面",
               font=cjk(24), fill=FAINT)

    return Scene("title", dur, draw, "")


def end_scene(dur):
    def draw(img, t):
        d = ImageDraw.Draw(img)
        d.text((140, 320), "已经可用，但还没到运营级", font=cjk(64, True), fill=INK)
        rows = [
            ("查询", "SQL / REST / 界面，三种入口"),
            ("修改", "走校订层 curate，重跑不丢，可审计"),
            ("重建", "reset → migrate → ingest --all，30 秒"),
        ]
        y = 470
        for k, v in rows:
            d.text((146, y), k, font=cjk(30, True), fill=BLUE)
            d.text((300, y), v, font=cjk(30), fill=BODY)
            y += 62
        d.text((140, H - 176), "http://127.0.0.1:8011/", font=mono(26), fill=TEAL)
        d.text((140, H - 128), "数据库 · 接口 · 界面 · 文档 · 91 项测试",
               font=cjk(22), fill=FAINT)

    return Scene("end", dur, draw, "")


# ---------------------------------------------------------------- 时间轴
def load_timing():
    return {d["name"]: d for d in json.loads((AUDIO / "timing.json").read_text())}


def seq(items, start=0.55, cps=42.0):
    out, t = [], start
    for text_, color, kind in items:
        out.append(Line(text_, t, color, kind))
        if kind == "cmd":
            t += len(text_) / cps + 0.30
        elif kind == "gap":
            t += 0.18
        else:
            t += 0.16
    return out


def build_scenes():
    tm = load_timing()
    pad = 1.40

    def dur(k):
        return tm[k]["dur"] + pad

    scenes = [title_scene(dur("01_title"))]

    scenes.append(terminal_scene("svc", seq([
        ("docker compose ps", INK, "cmd"),
        ("steeldig-db   pgvector/pgvector:pg16   Up 3 hours (healthy)   5435->5432", BODY, "out"),
        ("", BODY, "gap"),
        ("curl -s localhost:8011/api/health", INK, "cmd"),
        ('{"status":"ok","db":true,"ts":"2026-10-23T01:12:42Z"}', GREEN, "out"),
    ]), dur("02_service"), tm["02_service"]["text"]))

    scenes.append(browser_scene(
        "home", "home.png", dur("03_home"), tm["03_home"]["text"],
        url="127.0.0.1:8011/", zoom=(1.0, 1.05), focus=(0.5, 0.32),
        callouts=[
            (0.36, 0.34, "1,304 条性能已数值化", BLUE),
            (0.32, 0.70, "强度 — 塑性分布", GREEN),
        ]))

    scenes.append(terminal_scene("sql", seq([
        ("docker exec -it steeldig-db psql -U steeldig -d steeldig", INK, "cmd"),
        ("steeldig=# select sample_id,", BODY, "out"),
        ("             round((tensile_strength_mpa*elongation_pct/100)::numeric,0) uts_x_el", BODY, "out"),
        ("           from api.sample_summary", BODY, "out"),
        ("           where tensile_strength_mpa is not null and elongation_pct is not null", BODY, "out"),
        ("           order by uts_x_el desc nulls last limit 5;", BODY, "out"),
        ("              sample_id                | uts_x_el", MUTED, "out"),
        (" ---------------------------------------+----------", MUTED, "out"),
        ("  sample_fe-28mn-9al-0.9c__hr-cr-1173k  |      778", TEAL, "out"),
        ("  sample_fe-28mn-9al-0.9c__hot-roll...  |      666", TEAL, "out"),
        ("  sample_fe-30mn-1.2c__homog-1100c-2h  |      639", TEAL, "out"),
        ("", BODY, "gap"),
        ("提示：DESC 默认把 NULL 排在最前，必须写 NULLS LAST", AMBER, "note"),
    ]), dur("04_sql"), tm["04_sql"]["text"]))

    scenes.append(browser_scene(
        "sample", "sample.png", dur("05_sample"), tm["05_sample"]["text"],
        url="127.0.0.1:8011/samples/10.1002_srin.202100643/...",
        zoom=(1.02, 1.10), focus=(0.62, 0.30),
        callouts=[
            (0.66, 0.30, "每个值都挂着证据", GREEN),
            (0.66, 0.62, "机制推断与结论", VIOLET),
        ]))

    scenes.append(terminal_scene("overwrite", seq([
        ("# 直接改一条：立即生效", MUTED, "note"),
        ("steeldig=# update core.property_value set value_canonical=700 where ...;", INK, "cmd"),
        ("UPDATE 1", BODY, "out"),
        ("steeldig=# select value_canonical ...;", INK, "cmd"),
        ("     700", RED, "out"),
        ("", BODY, "gap"),
        ("# 重跑一次入库（从资产湖重建本篇）", MUTED, "note"),
        ("steeldig_db ingest --papers 10.1002_srin.202100643", INK, "cmd"),
        ("校订：重放 0 条生效校订（失败 0）", BODY, "out"),
        ("steeldig=# select value_canonical ...;", INK, "cmd"),
        ("     685        ← 改的值没了", RED, "out"),
    ], cps=52), dur("06_overwrite"), tm["06_overwrite"]["text"], note_color=RED))

    scenes.append(terminal_scene("curate", seq([
        ("# 走校订层：记录意图，重跑时重放", MUTED, "note"),
        ('curl -X POST .../api/curate/changes -d \'{"op":"update", ...}\'', INK, "cmd"),
        ('{"change_id": 40, "status": "applied"}', BODY, "out"),
        ("steeldig=# select value_canonical ...;", INK, "cmd"),
        ("     690", GREEN, "out"),
        ("", BODY, "gap"),
        ("steeldig_db ingest --papers 10.1002_srin.202100643", INK, "cmd"),
        ("校订：重放 1 条生效校订（失败 0）", GREEN, "out"),
        ("steeldig=# select value_canonical ...;", INK, "cmd"),
        ("     690        ← 重跑也冲不掉", GREEN, "out"),
    ], cps=52), dur("07_curate"), tm["07_curate"]["text"], note_color=GREEN))

    scenes.append(browser_scene(
        "comp", "comp_exact.png", dur("08_comp"), tm["08_comp"]["text"],
        url="127.0.0.1:8011/composition?el=Al:8-11&el=Mn:25-30",
        zoom=(1.0, 1.05), focus=(0.5, 0.46),
        callouts=[
            (0.60, 0.19, "点元素 + 设区间", VIOLET),
            (0.23, 0.72, "已选元素与区间", GREEN),
        ]))

    # 无声插入一段：没有精确匹配时的回退效果
    scenes.append(browser_scene(
        "comp2", "comp_fuzzy.png", 5.6,
        "没有精确匹配时：按成分距离排序，并说明差了多少",
        url="127.0.0.1:8011/composition?el=Al:20-25",
        zoom=(1.0, 1.04), focus=(0.5, 0.62),
        callouts=[
            (0.24, 0.49, "未找到完全匹配", AMBER),
            (0.39, 0.63, "按距离给最近的 24 个", GREEN),
        ]))

    scenes.append(browser_scene(
        "quality", "quality.png", dur("09_quality"), tm["09_quality"]["text"],
        url="127.0.0.1:8011/quality", zoom=(1.0, 1.04), focus=(0.5, 0.28),
        callouts=[(0.30, 0.40, "844 条 warn 均可解释", GREEN)]))

    scenes.append(end_scene(dur("10_end")))
    return scenes


AUDIO_OF = {
    "title": "01_title", "svc": "02_service", "home": "03_home", "sql": "04_sql",
    "sample": "05_sample", "overwrite": "06_overwrite", "curate": "07_curate",
    "comp": "08_comp", "quality": "09_quality", "end": "10_end",
}


def render(scenes, out):
    total = sum(s.dur for s in scenes)
    frames = int(total * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "21",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    starts, acc = [], 0.0
    for s in scenes:
        starts.append(acc)
        acc += s.dur

    base = background()
    for i in range(frames):
        t = i / FPS
        idx = len(scenes) - 1
        for j, st in enumerate(starts):
            if t < st + scenes[j].dur:
                idx = j
                break
        img = base.copy()
        scenes[idx].draw(img, max(0.0, t - starts[idx]))
        progress(ImageDraw.Draw(img), t, total)
        proc.stdin.write(img.tobytes())
        if i % 500 == 0:
            print(f"  frame {i}/{frames}  {t:.1f}s", flush=True)
    proc.stdin.close()
    proc.wait()
    return total


def build_audio(scenes, total, out):
    sr = 48000
    n = int(total * sr) + sr
    track = np.zeros(n, dtype=np.float32)
    acc = 0.0
    for s in scenes:
        name = AUDIO_OF.get(s.key)
        if name:
            with wave.open(str(AUDIO / f"{name}.wav"), "rb") as w:
                data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
            start = int((acc + 0.55) * sr)
            end = min(n, start + len(data))
            track[start:end] += data[: end - start].astype(np.float32) / 32768.0
        acc += s.dur
    peak = float(np.max(np.abs(track))) or 1.0
    pcm = (np.clip(track / peak * 0.9, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def preview(scenes, times):
    starts, acc = [], 0.0
    for s in scenes:
        starts.append(acc)
        acc += s.dur
    base = background()
    for t in times:
        idx = len(scenes) - 1
        for j, st in enumerate(starts):
            if t < st + scenes[j].dur:
                idx = j
                break
        img = base.copy()
        scenes[idx].draw(img, max(0.0, t - starts[idx]))
        progress(ImageDraw.Draw(img), t, acc)
        p = ROOT / f"preview_{t:.1f}.png"
        img.save(p)
        print("saved", p.name, "scene", scenes[idx].key)


def main():
    scenes = build_scenes()
    total = sum(s.dur for s in scenes)
    print(f"总时长 {total:.1f}s，{len(scenes)} 个场景")
    for s in scenes:
        print(f"  {s.key:10s} {s.dur:5.2f}s")

    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        preview(scenes, [float(x) for x in sys.argv[2:]])
        return

    tmp_v, tmp_a = ROOT / "_v.mp4", ROOT / "_a.wav"
    print("渲染帧…")
    render(scenes, tmp_v)
    print("合成音轨…")
    build_audio(scenes, total, tmp_a)
    print("封装…")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                    "-i", str(tmp_v), "-i", str(tmp_a),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", "-movflags", "+faststart", str(OUT)], check=True)
    tmp_v.unlink(missing_ok=True)
    tmp_a.unlink(missing_ok=True)
    print("done:", OUT, f"{OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
