#!/usr/bin/env python3
"""Draw the desks in code: grid paper, cutting mat, kraft paper, felt, wood, cork. Plus paper fibre and grain.

  python scripts/desks.py JOB

Writes JOB/assets/desk_<name>.jpg, paper.jpg and grain.png. Needs Pillow. Nothing is downloaded or generated
by an AI model: every surface is drawn, then given fibre, a lamp in one corner and a dark edge so it is not flat.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import die, job_dir, say  # noqa: E402

S = 2400   # square, so one desk covers vertical and wide frames


def _noise(size, sigma, stretch=None):
    from PIL import Image
    n = Image.effect_noise(size if not stretch else (size[0] // stretch[0], size[1] // stretch[1]), sigma)
    return n.resize(size, Image.BICUBIC) if stretch else n


def _tint(noise, dark, light):
    from PIL import ImageOps
    return ImageOps.colorize(noise, dark, light)


def _light(im):
    """A lamp top left and a darker edge."""
    from PIL import Image, ImageChops
    lamp = Image.radial_gradient("L").resize((S * 2, S * 2)).crop((S // 2 + 300, S // 2 + 300, S // 2 + 300 + S, S // 2 + 300 + S))
    lamp = lamp.point(lambda v: 255 - int(v * 0.62))            # bright near the lamp, falls off
    shade = Image.merge("RGB", (lamp, lamp, lamp))
    return ImageChops.multiply(im, shade)


def grid():
    from PIL import ImageDraw
    im = _tint(_noise((S, S), 9), "#d9d6cd", "#f4f1e8")
    d = ImageDraw.Draw(im)
    for x in range(0, S, 60):
        d.line((x, 0, x, S), fill="#b9c2d6", width=2)
        d.line((0, x, S, x), fill="#b9c2d6", width=2)
    return im


def mat():
    from PIL import ImageDraw
    im = _tint(_noise((S, S), 12), "#16603c", "#2c8a5a")
    d = ImageDraw.Draw(im)
    for x in range(0, S, 30):
        w = 3 if x % 150 == 0 else 1
        d.line((x, 0, x, S), fill="#cfe9d8" if w == 3 else "#62a984", width=w)
        d.line((0, x, S, x), fill="#cfe9d8" if w == 3 else "#62a984", width=w)
    return im


def kraft():
    from PIL import Image
    a = _tint(_noise((S, S), 26), "#8e6a3f", "#c59a63")
    b = _tint(_noise((S, S), 40, (8, 8)), "#9a7446", "#c79d68")
    return Image.blend(a, b, 0.5)


def felt():
    return _tint(_noise((S, S), 34), "#0c0c0c", "#2e2b29")


def wood():
    from PIL import Image
    grain = _tint(_noise((S, S), 46, (60, 2)), "#7a4a1c", "#c98a3e")
    fine = _tint(_noise((S, S), 20, (12, 1)), "#8a5522", "#c48537")
    return Image.blend(grain, fine, 0.45)


def cork():
    from PIL import Image
    a = _tint(_noise((S, S), 60, (3, 3)), "#8a5a26", "#d59a52")
    b = _tint(_noise((S, S), 40), "#9a6830", "#cf9550")
    return Image.blend(a, b, 0.4)


DESKS = {"grid": grid, "mat": mat, "kraft": kraft, "felt": felt, "wood": wood, "cork": cork}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job")
    a = ap.parse_args()
    try:
        from PIL import Image
    except ImportError:
        die("Pillow is missing. Run: pip install pillow")
    assets = job_dir(a.job) / "assets"
    for name, fn in DESKS.items():
        _light(fn().convert("RGB")).save(assets / ("desk_%s.jpg" % name), quality=88)
    _tint(_noise((900, 900), 14), "#d8d4c8", "#ffffff").save(assets / "paper.jpg", quality=88)
    n = Image.effect_noise((512, 512), 60)
    Image.merge("RGB", (n, n, n)).save(assets / "grain.png")
    say("6 desks, paper fibre and grain saved to %s" % assets)


if __name__ == "__main__":
    main()
