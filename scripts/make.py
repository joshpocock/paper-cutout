#!/usr/bin/env python3
"""One command: a photo, a script and a voice in, a paper cut-out video out.

  python scripts/make.py JOB --photo me.jpg [--open me_open.jpg] [--take my_voice.m4a]
                             [--size 1080x1920] [--accent "#BA9926"] [--music bed.mp3] [--no-render]

JOB is a folder that holds script.txt (your words, plain text). Steps it runs, in order:
person, desks, voice, words, plan, score, build, render. It stops if the scorecard fails.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(script, *args):
    t0 = time.time()
    r = subprocess.run([sys.executable, str(HERE / script)] + [str(x) for x in args])
    if r.returncode != 0:
        print("stopped at %s" % script)
        sys.exit(r.returncode)
    return time.time() - t0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job")
    ap.add_argument("--photo", required=True)
    ap.add_argument("--open", dest="open_")
    ap.add_argument("--take", help="your own voice recording; without it a free local voice reads the script")
    ap.add_argument("--voice", default="am_michael")
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--accent", default="#BA9926")
    ap.add_argument("--music")
    ap.add_argument("--no-render", action="store_true", help="stop after the page is built")
    a = ap.parse_args()
    job = Path(a.job)
    if not (job / "script.txt").exists():
        print("ERROR: put your script in %s first" % (job / "script.txt"))
        sys.exit(1)
    t0 = time.time()
    person = ["--photo", a.photo, "--accent", a.accent] + (["--open", a.open_] if a.open_ else [])
    run("person.py", job, *person)
    run("desks.py", job)
    run("voice.py", job, *(["--file", a.take] if a.take else ["--voice", a.voice]))
    run("words.py", job)
    run("plan.py", job, "--size", a.size, "--accent", a.accent)
    run("score.py", job)
    run("build.py", job)
    if not a.no_render:
        run("render.py", job, *(["--music", a.music] if a.music else []))
    print("all steps finished in %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
