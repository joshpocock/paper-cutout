#!/usr/bin/env python3
"""Build the video page from JOB/scenes.json: JOB/index.html (what gets rendered) and JOB/audio/hits.wav.

  python scripts/build.py JOB

Every picture is drawn from the pose number, floor(time x 16), so the video moves 16 times a second,
not 30. Word tiles appear whole on their pose (no bounce). Every paper piece shifts a hair on every pose.
The mouth swaps between your two photos from the loudness of JOB/audio/voice.wav.
"""
import argparse
import array
import html
import json
import math
import random
import shutil
import subprocess
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, die, load_json, say  # noqa: E402

CHAR_W = 0.47          # Anton capital, as a share of the font size
COLOURS = {"black": ("#151515", "#F6F2E8"), "white": ("#F6F2E8", "#141414"), "red": ("#C0281C", "#ffffff")}


def mouth_track(voice, duration):
    """'1' where the mouth is open, one character per pose: loud = open, never open more than 3 poses running."""
    n = int(duration * 16) + 2
    if not voice.exists() or shutil.which("ffmpeg") is None:
        return "0" * n
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(voice), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    x = array.array("h")
    x.frombytes(raw[: len(raw) // 2 * 2])
    levels = []
    for i in range(0, len(x) - 999, 1000):
        levels.append(math.sqrt(sum(v * v for v in x[i:i + 1000]) / 1000.0))
    if not levels:
        return "0" * n
    cut = 0.42 * sorted(levels)[int(len(levels) * 0.9)]
    out, run = [], 0
    for v in levels:
        is_open = v > cut
        run = run + 1 if is_open else 0
        if run > 3:
            is_open, run = False, 0
        out.append("1" if is_open else "0")
    return "".join(out).ljust(n, "0")[:n]


def hits(path, times, cuts, duration, seed=5):
    """A soft paper thump when a tile lands and a short whoosh into every cut."""
    sr = 22050
    rnd = random.Random(seed)
    x = [0.0] * int(sr * duration)
    for t in times:
        i0 = int((t + 0.0625) * sr)
        strength = 0.5 + 0.25 * rnd.random()
        for k in range(int(sr * 0.10)):
            if i0 + k >= len(x):
                break
            tt = k / sr
            x[i0 + k] += (math.sin(2 * math.pi * (95 - 200 * tt) * tt) * math.exp(-tt * 38) * 0.9 + rnd.uniform(-1, 1) * math.exp(-tt * 90) * 0.35) * strength
    for c in cuts:
        i0 = int((c - 0.13) * sr)
        for k in range(int(sr * 0.16)):
            if 0 <= i0 + k < len(x):
                x[i0 + k] += rnd.uniform(-1, 1) * math.sin(math.pi * k / (sr * 0.16)) ** 2 * 0.10
    peak = max(1e-6, max(abs(v) for v in x))
    w = wave.open(str(path), "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sr)
    w.writeframes(array.array("h", [int(v / peak * 0.7 * 32767) for v in x]).tobytes())
    w.close()


def piece(x, y, inner, t, rot, cls="", style="", w=None, h=None, drop=False):
    st = "left:%dpx;top:%dpx;" % (x, y) + ("width:%dpx;" % w if w else "") + ("height:%dpx;" % h if h else "") + style
    return '<div class="p %s" style="%s" data-in="%s" data-rot="%s"%s>%s</div>\n' % (cls, st, t, rot, ' data-drop="1"' if drop else "", inner)


def scene_html(i, s, d, person_aspect):
    W, H = d["size"]
    wide = W > H
    accent = d.get("accent", "#BA9926")
    # where the words go and where the person goes
    if wide:
        left = i % 2 == 0
        tb = (int(W * 0.05) if left else int(W * 0.53), int(H * 0.08), int(W * 0.42), int(H * 0.84))
        pw = int(H * 0.62)
        px = int(W * 0.72 - pw / 2) if left else int(W * 0.26 - pw / 2)
        py = int(H * 0.5 - pw * person_aspect / 2)
    else:
        tb = (int(W * 0.08), int(H * 0.09), int(W * 0.84), int(H * 0.36))
        pw = int(W * (0.76 if i % 3 else 0.64))
        px = int(W * 0.5 - pw / 2 + (40 if i % 2 else -40))
        py = int(H * 0.44)
    ph = int(pw * person_aspect)
    tilt = [-4, 3, -2, 4][s.get("pose", 0) % 4]
    body = ""
    # a sheet of paper under the person, and two bits of tape
    body += piece(px - 40, py + 40, "", 0, -tilt * 2, "sheet sh", "background:%s;" % ("#EFE7D2" if i % 2 else "#F7F4EC"), pw + 80, int(ph * 0.92))
    body += piece(px, py, '<img class="m0" src="assets/person_0.png"><img class="m1" src="assets/person_1.png">', 0, tilt, "person sh", "", pw, ph)
    body += piece(px + pw - 120, py + 10, "", 0, 30 + tilt, "tape shs", "", 190, 54)
    # word tiles, sized to fit their column
    sizes = [min(230 if wide else 250, (tb[2] - 52) / (CHAR_W * max(2, len(t["text"])))) for t in s["tiles"]]
    total = sum(z + 46 for z in sizes)
    if total > tb[3]:
        sizes = [z * tb[3] / total for z in sizes]
        total = tb[3]
    y = tb[1] + (tb[3] - total) // 2 if wide else tb[1]
    for k, t in enumerate(s["tiles"]):
        z = int(sizes[k])
        tw = CHAR_W * len(t["text"]) * z + 52
        x = tb[0] + (0 if k % 2 == 0 else min(60, max(0, tb[2] - tw)))
        bg, fg = (accent, "#ffffff") if t.get("colour") == "accent" else COLOURS.get(t.get("colour"), COLOURS["black"])
        body += piece(int(x), int(y), html.escape(t["text"]), t["t"], [-3, 3, -2, 4][(i + k) % 4], "tile sh",
                      "font-size:%dpx;background:%s;color:%s;" % (z, bg, fg), drop=True)
        y += z + 46
    move = s.get("move", "push")
    z0, z1 = (1.19, 1.0) if move == "pull" else ((1.0, 1.14) if move == "push" else (1.0, 1.0))
    return ('<div class="scene" data-s="%s" data-e="%s" data-z0="%s" data-z1="%s" data-dx="%s" data-dy="%s"%s>\n<div class="cam">'
            '<div class="ground" style="background-image:url(assets/desk_%s.jpg)"></div>\n<div class="lay">\n%s</div></div></div>\n'
            % (s["start"], s["end"], z0, z1, [10, -10, 0, 8, -8][i % 5], [-8, 0, 8, 6, -6][i % 5],
               "" if move in ("push", "pull") else ' data-still="1"', s["desk"], body))


PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="UTF-8" />
<meta name="viewport" content="width=__W__, height=__H__" />
<title>paper cut-out</title>
<style>
  @font-face { font-family: "Anton"; src: url("assets/fonts/Anton-Regular.ttf") format("truetype"); font-display: block; }
  html, body { margin: 0; background: #111; }
  #main { position: relative; width: __W__px; height: __H__px; overflow: hidden; background: #111; }
  .scene { position: absolute; inset: 0; opacity: 0; overflow: hidden; }
  .cam { position: absolute; inset: -120px; transform-origin: 50% 50%; }
  .ground { position: absolute; inset: 0; background-size: cover; background-position: center; }
  .lay { position: absolute; left: 120px; top: 120px; width: __W__px; height: __H__px; transform: scale(.86); transform-origin: 50% 50%; }
  .p { position: absolute; opacity: 0; transform-origin: 50% 50%; }
  .sh { filter: drop-shadow(10px 18px 12px rgba(0,0,0,.42)) drop-shadow(2px 4px 2px rgba(0,0,0,.4)); }
  .shs { filter: drop-shadow(6px 10px 7px rgba(0,0,0,.4)); }
  .tile { font-family: "Anton", Impact, sans-serif; text-transform: uppercase; line-height: 1; padding: 14px 26px 10px; white-space: nowrap; }
  .tile::after, .sheet::after { content: ""; position: absolute; inset: 0; background: url("assets/paper.jpg") center / 900px auto; mix-blend-mode: multiply; opacity: .8; pointer-events: none; }
  .tape { background: rgba(240,226,170,.82); }
  .person img { position: absolute; left: 0; top: 0; width: 100%; display: block; }
  .person .m1 { opacity: 0; }
  #grain { position: absolute; inset: -200px; z-index: 60; background: url("assets/grain.png") 0 0 / 512px 512px; opacity: .14; mix-blend-mode: multiply; pointer-events: none; }
  #vig { position: absolute; inset: 0; z-index: 62; background: radial-gradient(ellipse at 50% 48%, transparent 54%, rgba(0,0,0,.4) 100%); pointer-events: none; }
  .warm { position: absolute; left: -9999px; top: 0; font-family: "Anton"; }
</style></head>
<body>
<div id="main" data-composition-id="main" data-start="0" data-width="__W__" data-height="__H__" data-duration="__DUR__" data-no-timeline>
<div class="warm" aria-hidden="true">A</div>
__SCENES__
<div id="grain"></div><div id="vig"></div>
</div>
<script>
(function () {
  var POSES = 16, MOUTH = "__MOUTH__";
  function h(a, b) { var x = Math.sin(a * 127.1 + b * 311.7) * 43758.5453; return (x - Math.floor(x)) * 2 - 1; }
  var scenes = [].slice.call(document.querySelectorAll(".scene")).map(function (el, si) {
    return { el: el, cam: el.querySelector(".cam"), s: +el.dataset.s, e: +el.dataset.e, z0: +el.dataset.z0, z1: +el.dataset.z1, dx: +el.dataset.dx, dy: +el.dataset.dy,
      still: !!el.dataset.still,
      ps: [].slice.call(el.querySelectorAll(".p")).map(function (p, pi) {
        return { el: p, id: si * 37 + pi + 1, tin: +p.dataset.in, rot: +p.dataset.rot, drop: !!p.dataset.drop, m0: p.querySelector(".m0"), m1: p.querySelector(".m1") }; }) };
  });
  var grain = document.getElementById("grain"), main = document.getElementById("main");
  function draw(time) {
    var f = Math.floor(time * POSES + 1e-4);                       // the pose number: everything is drawn from it
    grain.style.backgroundPosition = Math.round(h(f, 1) * 240) + "px " + Math.round(h(f, 2) * 240) + "px";
    main.style.filter = "brightness(" + (1 + h(f, 21) * 0.014).toFixed(4) + ")";
    var open = MOUTH.charAt(f) === "1";
    for (var i = 0; i < scenes.length; i++) {
      var sc = scenes[i], on = time >= sc.s - 1e-4 && time < sc.e - 1e-4;
      sc.el.style.opacity = on ? 1 : 0;
      if (!on) continue;
      var fs = Math.floor(sc.s * POSES + 1e-4), fe = Math.floor(sc.e * POSES + 1e-4);
      var k = Math.pow(Math.max(0, Math.min(1, (f - fs) / Math.max(1, fe - fs - 1))), 0.62);   // big first step, slow drift
      var z = sc.z0 + (sc.z1 - sc.z0) * k, x = sc.dx * (k - 0.5) * 2, y = sc.dy * (k - 0.5) * 2;
      var left = (sc.still || i === scenes.length - 1) ? 99 : fe - 1 - f;
      if (left === 1) { z *= 1.03; y -= 9; } else if (left === 0) { z *= 1.06; y -= 24; }       // speeds up into the hard cut
      x += h(f, 9) * 1.6; y += h(f, 10) * 1.6;
      sc.cam.style.transform = "translate(" + x.toFixed(2) + "px," + y.toFixed(2) + "px) scale(" + z.toFixed(4) + ") rotate(" + (h(f, 11) * 0.12).toFixed(3) + "deg)";
      for (var j = 0; j < sc.ps.length; j++) {
        var p = sc.ps[j], fin = p.tin <= sc.s ? fs : Math.ceil(p.tin * POSES - 1e-4), d = f - fin;
        if (d < 0) { p.el.style.opacity = 0; continue; }
        p.el.style.opacity = 1;                                        // whole, on its pose: no fade, no scale, no bounce
        var r = p.rot + (p.drop && d < 2 ? [5, -2][d] : 0);            // it settles like dropped paper
        r += h(f, p.id) * 0.55;                                        // boil: a hair of movement on every pose
        p.el.style.transform = "translate(" + (h(f, p.id + 0.5) * 1.8).toFixed(2) + "px," + (h(f, p.id + 0.9) * 1.8).toFixed(2) + "px) rotate(" + r.toFixed(3) + "deg)";
        if (p.m0) { p.m0.style.opacity = open ? 0 : 1; p.m1.style.opacity = open ? 1 : 0; }
      }
    }
  }
  window.addEventListener("hf-seek", function (e) { draw(e.detail.time); });
  draw(0);
})();
</script>
</body></html>
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job")
    a = ap.parse_args()
    job = Path(a.job)
    if not (job / "scenes.json").exists():
        die("no %s. Run plan.py first." % (job / "scenes.json"))
    d = load_json(job / "scenes.json")
    assets = job / "assets"
    for needed in ("person_0.png", "person_1.png", "desk_grid.jpg", "paper.jpg", "grain.png"):
        if not (assets / needed).exists():
            die("missing %s. Run person.py and desks.py first." % (assets / needed))
    (assets / "fonts").mkdir(exist_ok=True)
    shutil.copy(ROOT / "kit" / "fonts" / "Anton-Regular.ttf", assets / "fonts" / "Anton-Regular.ttf")
    aspect = 1180 / 900
    try:
        from PIL import Image
        with Image.open(assets / "person_0.png") as im:
            aspect = im.height / im.width
    except ImportError:
        pass
    scenes = "".join(scene_html(i, s, d, aspect) for i, s in enumerate(d["scenes"]))
    mouth = mouth_track(job / "audio" / "voice.wav", d["duration"])
    page = (PAGE.replace("__W__", str(d["size"][0])).replace("__H__", str(d["size"][1])).replace("__DUR__", str(d["duration"]))
            .replace("__SCENES__", scenes).replace("__MOUTH__", mouth))
    (job / "index.html").write_text(page, encoding="utf-8")
    lands = sorted({t["t"] for s in d["scenes"] for t in s["tiles"]})
    hits(job / "audio" / "hits.wav", lands, [s["start"] for s in d["scenes"][1:]], d["duration"])
    (job / "build.json").write_text(json.dumps({"scenes": len(d["scenes"]), "tiles": len(lands), "duration": d["duration"]}), encoding="utf-8")
    say("built %s: %d scenes, %d word tiles, %.1f s" % (job / "index.html", len(d["scenes"]), len(lands), d["duration"]))


if __name__ == "__main__":
    main()
