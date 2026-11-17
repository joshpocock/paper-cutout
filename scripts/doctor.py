#!/usr/bin/env python3
"""Check this computer has what paper-cutout needs. Prints one line per check and a verdict.

  python scripts/doctor.py

Needs nothing itself (standard library). Exit code 1 if something required is missing.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def version(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except Exception:
        return None


def main():
    rows, bad = [], 0

    def row(ok, name, detail, required=True):
        nonlocal bad
        if not ok and required:
            bad += 1
        rows.append("%s  %-10s %s" % ("OK  " if ok else ("MISS" if required else "opt "), name, detail))

    v = sys.version_info
    row(v >= (3, 8), "python", "%d.%d.%d (need 3.8+)" % (v[0], v[1], v[2]))
    try:
        import PIL
        row(True, "pillow", PIL.__version__)
    except ImportError:
        row(False, "pillow", "missing: pip install pillow")
    try:
        import rembg  # noqa: F401
        row(True, "rembg", "installed (cuts you out of a photo with a background)", False)
    except ImportError:
        row(False, "rembg", "not installed: only needed for photos with a background (pip install rembg)", False)
    try:
        import kokoro_onnx  # noqa: F401
        row(True, "kokoro", "installed (the free voice)", False)
    except ImportError:
        row(False, "kokoro", "not installed: only needed for the free voice (pip install kokoro-onnx soundfile)", False)
    for tool, need in (("ffmpeg", True), ("ffprobe", True), ("node", True)):
        p = shutil.which(tool)
        row(bool(p), tool, (version([tool, "-version" if tool != "node" else "--version"]) or "found") if p else "missing: see references/setup.md", need)
    if shutil.which("node"):
        nv = version(["node", "--version"]) or "v0"
        try:
            major = int(nv.lstrip("v").split(".")[0])
        except ValueError:
            major = 0
        row(major >= 20, "node 20+", nv)
    font = ROOT / "kit" / "fonts" / "Anton-Regular.ttf"
    row(font.exists(), "font", str(font.relative_to(ROOT)) if font.exists() else "missing kit/fonts/Anton-Regular.ttf")
    print("\n".join(rows))
    print("\nDOCTOR %s: %s" % ("PASS" if bad == 0 else "FAIL", "ready to make videos" if bad == 0 else "%d required item(s) missing" % bad))
    sys.exit(0 if bad == 0 else 1)


if __name__ == "__main__":
    main()
