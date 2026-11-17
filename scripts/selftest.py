#!/usr/bin/env python3
"""Prove the skill works on this computer without your photo, voice or a render.

  python scripts/selftest.py [JOB]

Draws a test face (two mouths) in code, writes a 40-word script, then runs person, desks, words (paced, no
audio), plan and score, and builds the page if ffmpeg is installed. Prints one line:
  SELFTEST PASS  ...   or   SELFTEST FAIL  ...
and leaves JOB/scenes.json and JOB/assets/selftest_frame.png for Claude to open and look at before
telling you it works. JOB defaults to paper/selftest. Needs Pillow.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = ("This is a test of the paper look. A face, two mouths and six desks, all drawn in code. "
          "Every word lands whole. The camera moves on every scene. If this passes, the skill is ready for your photo.")


def face(path, mouth_open):
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (600, 760), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((90, 60, 510, 560), fill=(232, 196, 160, 255))                     # head
    d.ellipse((80, 20, 520, 260), fill=(60, 40, 30, 255))                         # hair
    d.ellipse((120, 140, 480, 560), fill=(232, 196, 160, 255))
    for x in (215, 385):
        d.ellipse((x - 28, 280, x + 28, 330), fill=(255, 255, 255, 255))
        d.ellipse((x - 12, 292, x + 12, 318), fill=(40, 30, 25, 255))
    if mouth_open:
        d.ellipse((250, 430, 350, 500), fill=(120, 30, 30, 255))
    else:
        d.line((250, 460, 350, 460), fill=(120, 30, 30, 255), width=10)
    d.rectangle((210, 560, 390, 760), fill=(232, 196, 160, 255))                 # neck
    im.save(path)


def run(step, *args):
    r = subprocess.run([sys.executable, str(HERE / step)] + list(args), capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job", nargs="?", default="paper/selftest", help="folder to write the test into (default paper/selftest)")
    job = Path(ap.parse_args().job)
    (job / "assets").mkdir(parents=True, exist_ok=True)
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("SELFTEST FAIL  Pillow is missing: pip install pillow"); sys.exit(1)
    (job / "script.txt").write_text(SCRIPT, encoding="utf-8")
    face(job / "test_closed.png", False); face(job / "test_open.png", True)
    steps = [("person.py", str(job), "--photo", str(job / "test_closed.png"), "--open", str(job / "test_open.png")),
             ("desks.py", str(job)), ("words.py", str(job), "--wps", "2.6"), ("plan.py", str(job)), ("score.py", str(job))]
    for s in steps:
        code, out = run(*s)
        if code != 0:
            print(out[-800:]); print("SELFTEST FAIL  at %s" % s[0]); sys.exit(1)
        if s[0] == "score.py":
            card = out.splitlines()[-1]
    built = "page not built (ffmpeg missing)"
    import shutil
    if shutil.which("ffmpeg"):
        code, out = run("build.py", str(job))
        built = "page built" if code == 0 else "page build failed: " + out[-200:]
    # one picture to look at: the paper person on the first desk
    from PIL import Image
    desks = sorted((job / "assets").glob("desk_*.jpg"))
    frame = Image.open(desks[0]).convert("RGB").resize((540, 960)) if desks else Image.new("RGB", (540, 960), "#d8d2c0")
    person = Image.open(job / "assets" / "person_1.png").convert("RGBA")
    person.thumbnail((420, 560))
    frame.paste(person, ((540 - person.width) // 2, 960 - person.height - 80), person)
    frame.save(job / "assets" / "selftest_frame.png")
    print("SELFTEST PASS  %s, %s. Look at %s and %s" % (card, built, job / "scenes.json", job / "assets" / "selftest_frame.png"))


if __name__ == "__main__":
    main()
