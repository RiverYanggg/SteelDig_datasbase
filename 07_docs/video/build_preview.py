"""Render v2 actual browser takes with local Chinese narration and subtitles.

Requires ffmpeg/ffprobe, macOS say (Tingting), Pillow and numpy.
Run with /Users/mac/miniconda3/bin/python. Existing v1 video is preserved.
"""
from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "v2"
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"


def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]))


def font(size, bold=False):
    return ImageFont.truetype(FONT, size, index=int(bold))


def timestamp(seconds):
    ms = round(seconds * 1000)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"


def wrap(text, f, width):
    result, current = [], ""
    for ch in text:
        if f.getlength(current + ch) > width:
            result.append(current)
            current = ch
        else:
            current += ch
    if current:
        result.append(current)
    return result


def title_panel(scene, index):
    im = Image.new("RGBA", (1920, 1080))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1920, 80), fill=(11, 18, 32, 255))
    d.rectangle((0, 962, 1920, 1080), fill=(11, 18, 32, 250))
    d.rectangle((0, 0, 7, 80), fill="#609aff")
    d.text((34, 19), scene["title"], font=font(28, True), fill="#edf4ff")
    right = f'{scene["label"]}   ·   {index:02}/09'
    d.text((1884, 27), right, font=font(17), fill="#a8b9d3", anchor="ra")
    d.text((34, 1051), "本地服务实录 · 2026.10.23", font=font(14), fill="#8092af")
    d.text((1884, 1051), "SteelDig / 演示预览", font=font(14), fill="#8092af", anchor="ra")
    return im


def main():
    media = OUT / "media"
    media.mkdir(exist_ok=True)
    scenes = json.loads((OUT / "scenes.json").read_text())
    manifest = {x["id"]: x for x in json.loads((OUT / "recording_manifest.json").read_text())}
    subtitles, schedule, total = [], [], 0
    clips = []
    for index, scene in enumerate(scenes, 1):
        name, length = scene["id"], scene["duration"]
        panel = media / f"{name}_panel.png"
        title_panel(scene, index).save(panel)
        captions = []
        speech = np.zeros(round(length * 48000), dtype=np.float32)
        previous_end = 0
        for j, line in enumerate(scene["lines"]):
            aiff = media / f"{name}_{j}.aiff"
            wav = aiff.with_suffix(".wav")
            if not wav.exists():
                run(["say", "-v", "Tingting", "-r", "195", "-o", str(aiff), line])
                run(["ffmpeg", "-v", "error", "-y", "-i", str(aiff), "-ar", "48000", "-ac", "1", str(wav)])
            with wave.open(str(wav)) as f:
                values = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32)
            assert len(values), f"Speech synthesis returned empty audio: {line}"
            start = max(scene["line_starts"][j], previous_end + .15)
            end = start + len(values) / 48000
            assert end <= length - .15, f"Narration overrun {name}: {end:.2f}s > {length}s"
            a = round(start * 48000)
            speech[a:a+len(values)] = values
            previous_end = end
            cap_end = min(length - .1, end + .4)
            # SRT line breaks use the same measured layout as the burnt subtitles.
            lines = wrap(line, font(34), 1600)
            caption = Image.new("RGBA", (1920, 1080))
            d = ImageDraw.Draw(caption)
            for k, txt in enumerate(lines):
                d.text((960, 985 + k*39 - (len(lines)-1)*16), txt, font=font(34), fill="white", anchor="ma")
            path = media / f"{name}_{j}_caption.png"
            caption.save(path)
            captions.append((path, start, cap_end))
            subtitles.append(f"{len(subtitles)+1}\n{timestamp(total+start)} --> {timestamp(total+cap_end)}\n" + "\n".join(lines) + "\n")
            schedule.append({"scene": name, "text":line, "start":round(total+start,3), "end":round(total+end,3)})
        audio = media / f"{name}_voice.wav"
        with wave.open(str(audio), "wb") as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(48000)
            f.writeframes(np.clip(speech, -32768, 32767).astype(np.int16).tobytes())
        take = manifest[name]
        clip = media / f"{name}.mp4"
        args = ["ffmpeg", "-v", "error", "-y", "-ss", str(take["offset"]), "-i", str(OUT / take["file"]), "-i", str(panel)]
        for path, _, _ in captions:
            args += ["-i", str(path)]
        args += ["-i", str(audio)]
        filters = [f"[0:v]scale=1920:1080,fps=25,trim=duration={length},setpts=PTS-STARTPTS[v0]", "[v0][1:v]overlay=0:0[v1]"]
        for j, (_, start, end) in enumerate(captions):
            filters.append(f"[v{j+1}][{j+2}:v]overlay=0:0:enable='between(t,{start:.3f},{end:.3f})'[v{j+2}]")
        args += ["-filter_complex", ";".join(filters), "-map", f"[v{len(captions)+1}]", "-map", f"{len(captions)+2}:a", "-t", str(length), "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(clip)]
        run(args)
        clips.append(clip)
        total += length
        print(f"rendered {name}", flush=True)
    listing = media / "concat.txt"
    listing.write_text("\n".join(f"file '{p.name}'" for p in clips))
    output = OUT / "SteelDig_演示预览_v2.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", "-movflags", "+faststart", str(output)])
    (OUT / "SteelDig_中文字幕_v2.srt").write_text("\n".join(subtitles))
    (OUT / "narration_timing.json").write_text(json.dumps(schedule, ensure_ascii=False, indent=2))
    assert abs(duration(output) - total) < .5
    print(f"saved {output} ({total}s)")


if __name__ == "__main__":
    main()
