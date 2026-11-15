#!/usr/bin/env python3
"""Make the paper person: your real face, printed big, on a tiny body, with a sticker border.

  python scripts/person.py JOB --photo me.jpg [--open me_mouth_open.jpg] [--accent "#BA9926"] [--shirt "#1b1b1b"]

--photo  a head-and-shoulders photo, mouth closed. A plain background works best.
--open   the same framing with your mouth open. With it, the person talks (the two mouths swap on the voice).
Writes JOB/assets/person_0.png (closed) and person_1.png (open). Needs Pillow. Photos with a background also
need rembg (pip install rembg) to cut you out on your computer; a transparent PNG needs nothing extra.
No AI image is made: the face is your photo.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import die, job_dir, say  # noqa: E402

CANVAS = (900, 1180)
HEAD_H = 760


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def cut_out(path):
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    if im.split()[3].getextrema()[0] < 250:      # already has transparency
        return im
    try:
        from rembg import remove
    except ImportError:
        die("%s has a background. Install rembg (pip install rembg) or give a transparent PNG." % path)
    return remove(im)


def sticker(path, accent, shirt, grain_seed=7):
    from PIL import Image, ImageDraw, ImageFilter
    head = cut_out(path)
    head = head.crop(head.split()[3].getbbox())
    w = round(head.width * HEAD_H / head.height)
    if w > CANVAS[0] - 160:                       # very wide cut-outs (shoulders): fit the width instead
        w = CANVAS[0] - 160
    head = head.resize((w, round(head.height * w / head.width)), Image.LANCZOS)
    art = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    d = ImageDraw.Draw(art)
    cx, top = CANVAS[0] // 2, 70
    by = top + head.height - 90                   # the tiny body tucks under the chin
    d.rounded_rectangle((cx - 170, by, cx + 170, by + 290), 70, fill=shirt + (255,))
    d.ellipse((cx - 250, by + 40, cx - 110, by + 250), fill=shirt + (255,))
    d.ellipse((cx + 110, by + 40, cx + 250, by + 250), fill=shirt + (255,))
    art.alpha_composite(head, (cx - head.width // 2, top))
    alpha = art.split()[3]

    def ring(size, colour):
        layer = Image.new("RGBA", CANVAS, colour + (255,))
        layer.putalpha(alpha.filter(ImageFilter.MaxFilter(size)))
        return layer

    out = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    out.alpha_composite(ring(61, accent))         # thick border
    out.alpha_composite(ring(15, (255, 255, 255)))  # thin white cut line
    out.alpha_composite(art)
    noise = Image.effect_noise(CANVAS, 22).convert("L")      # print grain
    grain = Image.merge("RGBA", (noise, noise, noise, out.split()[3].point(lambda v: v * 0.10)))
    out.alpha_composite(grain)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job")
    ap.add_argument("--photo", required=True, help="head-and-shoulders photo, mouth closed")
    ap.add_argument("--open", dest="open_", help="same framing, mouth open")
    ap.add_argument("--accent", default="#BA9926", help="border colour")
    ap.add_argument("--shirt", default="#1b1b1b", help="body colour")
    a = ap.parse_args()
    try:
        import PIL  # noqa: F401
    except ImportError:
        die("Pillow is missing. Run: pip install pillow")
    job = job_dir(a.job)
    accent, shirt = hex_rgb(a.accent), hex_rgb(a.shirt)
    sticker(a.photo, accent, shirt).save(job / "assets" / "person_0.png")
    sticker(a.open_ or a.photo, accent, shirt).save(job / "assets" / "person_1.png")
    say("paper person saved to %s (%s)" % (job / "assets", "talks" if a.open_ else "one mouth: add --open to make it talk"))


if __name__ == "__main__":
    main()
