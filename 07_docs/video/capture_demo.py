"""只读检查与采集 SteelDig 页面；不调用写接口。

运行：/Users/mac/miniconda3/bin/python database/07_docs/video/capture_demo.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "v2"
BASE = "http://127.0.0.1:8011"
PAPER = "10.1002_srin.202100643"
SAMPLE = "sample_fe-28mn-10al-0.8c-0.0025n__hot-forged-1123-1323k-ac"
SAMPLE_URL = f"/samples/{PAPER}/{SAMPLE}"


def inspect():
    OUT.mkdir(exist_ok=True)
    shots = OUT / "screenshots"
    shots.mkdir(exist_ok=True)
    errors = []
    snapshot = {"captured_at": datetime.now(timezone.utc).isoformat(), "base_url": BASE}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("response", lambda r: errors.append(f"HTTP {r.status}: {r.url}") if r.status >= 400 else None)
        for name, path in [
            ("health", "/api/health"), ("stats", "/api/stats"),
            ("exact", "/api/composition/search?el=Al:8-11&el=Mn:25-30"),
            ("nearest", "/api/composition/search?el=Al:20-25"),
            ("sample", f"/api/samples/{PAPER}/{SAMPLE}"),
        ]:
            response = ctx.request.get(BASE + path)
            assert response.ok, (name, response.status)
            snapshot[name] = response.json()
        for name, path in [
            ("01_home", "/"), ("02_composition", "/composition"),
            ("03_exact", "/composition?el=Al:8-11&el=Mn:25-30"),
            ("04_nearest", "/composition?el=Al:20-25"),
            ("05_sample", SAMPLE_URL),
            ("07_search", "/search?q=κ-碳化物"), ("08_quality", "/quality"),
        ]:
            response = page.goto(BASE + path, wait_until="networkidle")
            assert response.status == 200, path
            page.wait_for_timeout(700)
            page.screenshot(path=str(shots / f"{name}.png"))
            if name == "05_sample":
                snapshot["property_options"] = page.locator('select[name="path"] option').evaluate_all("els => els.map(e=>e.value)")
                source = page.locator("a.prop-src").first
                assert source.count(), "性能必须提供原文跳转"
                snapshot["evidence_url"] = source.get_attribute("href")
                source.click()
                page.wait_for_load_state("networkidle")
                assert page.locator("text=被引用为").count()
                page.screenshot(path=str(shots / "06_evidence.png"))
                snapshot["evidence_text"] = page.locator(".content").inner_text()
            if name == "08_quality":
                snapshot["quality_text"] = page.locator(".content").inner_text()
        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        snapshot["mobile_overflow"] = {}
        for name, path in [("home", "/"), ("sample", SAMPLE_URL), ("composition", "/composition")]:
            mobile.goto(BASE + path, wait_until="networkidle")
            mobile.screenshot(path=str(shots / f"mobile_{name}.png"), full_page=True)
            snapshot["mobile_overflow"][name] = mobile.evaluate("document.documentElement.scrollWidth > innerWidth")
        snapshot["browser_errors"] = errors
        browser.close()
    (OUT / "verification.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2))
    print(json.dumps({"stats": snapshot["stats"], "exact": snapshot["exact"].get("exact", {}).get("count"), "mobile_overflow": snapshot["mobile_overflow"], "browser_errors": errors}, ensure_ascii=False))


def record():
    """Capture actual read-only browser interaction, one editable take per shot."""
    out = OUT / "recordings"
    out.mkdir(exist_ok=True)
    scenes = json.loads((OUT / "scenes.json").read_text())
    manifest = []
    cursor = """(() => {
      addEventListener('DOMContentLoaded', () => {
        const c = document.createElement('div'); c.id = 'recording-pointer';
        c.style.cssText = 'position:fixed;left:-100px;top:-100px;width:26px;height:26px;border:2px solid #60a5fa;background:#60a5fa22;border-radius:50%;pointer-events:none;z-index:99999;transform:translate(-50%,-50%)';
        document.body.append(c);
        addEventListener('mousemove', e => { c.style.left=e.clientX+'px'; c.style.top=e.clientY+'px'; });
        addEventListener('mousedown', () => c.animate([{transform:'translate(-50%,-50%) scale(.7)',background:'#2563eb88'},{transform:'translate(-50%,-50%) scale(1.5)',background:'#60a5fa11'}],{duration:400}));
      });
    })();"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for scene in scenes:
            name = scene["id"]
            ctx = browser.new_context(viewport={"width": 1440, "height": 810},
                record_video_dir=str(out), record_video_size={"width": 1440, "height": 810})
            # Guard against accidental database mutation during recording.
            ctx.route("**/*", lambda route: route.continue_() if route.request.method in {"GET", "HEAD", "OPTIONS"} else route.abort())
            ctx.add_init_script(cursor)
            created = time.perf_counter()
            page = ctx.new_page()
            path = {
                "01_home":"/", "02_exact":"/composition", "03_sample":SAMPLE_URL,
                "04_evidence":SAMPLE_URL, "05_nearest":"/composition?el=Al:20-25",
                "06_search":"/search", "07_curate":SAMPLE_URL, "08_quality":"/quality", "09_end":"/",
            }[name]
            page.goto(BASE + path, wait_until="networkidle")
            if name == "07_curate":
                page.get_by_text("修正一条性能值", exact=True).scroll_into_view_if_needed()
                page.evaluate("scrollBy(0, 120)")
            page.wait_for_timeout(500)
            page.mouse.move(1120, 90)
            start = time.perf_counter()
            offset = start - created

            def at(t):
                page.wait_for_timeout(max(0, (start + t - time.perf_counter()) * 1000))

            def point(locator):
                box = locator.bounding_box()
                if box:
                    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=24)

            def scroll_to(locator, top=140):
                y = locator.evaluate("e=>e.getBoundingClientRect().top+scrollY")
                page.evaluate("y=>scrollTo({top:y,behavior:'smooth'})", max(0, y-top))
                page.wait_for_timeout(800)

            if name == "01_home":
                at(3); point(page.locator(".kpi").nth(1))
                at(6); page.evaluate("scrollTo({top:360,behavior:'smooth'})")
                at(9); point(page.locator("#scatter"))
            elif name == "02_exact":
                at(2); point(page.locator('[data-sym="Al"]')); page.locator('[data-sym="Al"]').click()
                at(4); point(page.locator('[data-sym="Mn"]')); page.locator('[data-sym="Mn"]').click()
                at(6); scroll_to(page.locator("#compForm"), 350)
                for t, sym, cls, value in [(8,"Al","min","8"),(9,"Al","max","11"),(11,"Mn","min","25"),(12,"Mn","max","30")]:
                    at(t); field = page.locator(f'.range-row[data-sym="{sym}"] .{cls}'); field.press_sequentially(value, delay=130)
                at(15); page.locator('#compForm button[type="submit"]').click(); page.wait_for_load_state("networkidle")
                scroll_to(page.locator(".note"), 150)
                assert "41" in page.locator(".note").inner_text()
                at(21); row = page.locator(f'a[href="{SAMPLE_URL}"]').first
                scroll_to(row, 300)
                at(24); point(row)
                at(26); row.click(); page.wait_for_load_state("networkidle")
            elif name == "03_sample":
                at(5); point(page.locator(".prop-row").filter(has_text="yield strength"))
                at(12); point(page.locator(".prop-row").filter(has_text="yield strength").locator("a.prop-src"))
            elif name == "04_evidence":
                at(1); link = page.locator(".prop-row").filter(has_text="yield strength").locator("a.prop-src"); point(link); link.click()
                page.wait_for_load_state("networkidle")
                assert page.locator(".evidence-table table").count()
                at(5); point(page.locator(".evidence-table tr").nth(1))
                at(12); point(page.locator(".content .card").nth(1).locator("h3"))
            elif name == "05_nearest":
                at(3); point(page.locator('.range-row[data-sym="Al"]'))
                at(7); scroll_to(page.locator(".note.warn"), 180)
                at(12); point(page.locator(".delta").first)
                assert "7.4" in page.locator(".delta").first.inner_text()
            elif name == "06_search":
                at(2); field=page.locator('.content input[name="q"]'); field.press_sequentially("κ-碳化物", delay=220)
                at(5); page.locator(".content button").click(); page.wait_for_load_state("networkidle")
                at(9); point(page.locator(".result").first)
                at(12); page.evaluate("scrollBy({top:250,behavior:'smooth'})")
            elif name == "07_curate":
                at(2); page.get_by_text("修正一条性能值", exact=True).click()
                scroll_to(page.locator('select[name="path"]'), 250)
                at(5); page.locator('select[name="path"]').select_option(label="mechanical · yield_strength（当前 685 MPa）")
                at(7); page.locator('input[name="new_value"]').press_sequentially("690", delay=180)
                at(9); page.locator('input[name="note"]').fill("演示草稿：请先核对原文，不提交")
                at(11); point(page.locator('input[name="note"]'))
            elif name == "08_quality":
                at(2); point(page.locator(".page-head .badge"))
                at(6); point(page.get_by_text("FIGURE_EVIDENCE_EMPTY", exact=True).first)
                at(10); page.evaluate("scrollBy({top:280,behavior:'smooth'})")
            elif name == "09_end":
                at(1); point(page.locator(".home-intro h1"))
            at(scene["duration"])
            page.screenshot(path=str(OUT / "screenshots" / f"take_{name}.png"))
            at(scene["duration"] + .5)
            video = page.video
            ctx.close()
            dest = out / f"{name}.webm"
            video.save_as(str(dest))
            video.delete()
            manifest.append({"id":name, "file":str(dest.relative_to(OUT)), "offset":round(offset,3), "duration":scene["duration"]})
            (OUT / "recording_manifest.json").write_text(json.dumps(manifest, indent=2))
            print(f"recorded {name}", flush=True)
        browser.close()


def review():
    """Check the delivered local review page and seek/play the final MP4."""
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((OUT / "index.html").as_uri())
        page.wait_for_function("document.querySelector('video').readyState >= 1")
        metadata = page.locator("video").evaluate("v => ({duration:v.duration,width:v.videoWidth,height:v.videoHeight})")
        assert abs(metadata["duration"] - 152) < .1, metadata
        assert (metadata["width"], metadata["height"]) == (1920, 1080), metadata
        page.locator("video").evaluate("v => {v.currentTime=70; v.muted=true;}")
        page.wait_for_function("document.querySelector('video').readyState >= 2")
        page.locator("video").evaluate("v => v.play()")
        page.wait_for_function("document.querySelector('video').currentTime > 70.5")
        page.locator("video").evaluate("v => v.pause()")
        assert not errors, errors
        report = {"metadata": metadata, "seek_and_play": True, "browser_errors": errors}
        (OUT / "playback_verification.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report))
        browser.close()


if __name__ == "__main__":
    if "--record" in sys.argv:
        record()
    elif "--review" in sys.argv:
        review()
    else:
        inspect()
