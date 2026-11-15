#!/usr/bin/env python3
"""Render JOB/index.html to JOB/final.mp4 with the voice and the paper hits.

  python scripts/render.py JOB [--music bed.mp3] [--drop 10.2,12.1]

--music  an optional music file you have the right to use, mixed low under the voice.
--drop   start,end in seconds where the music goes silent (put it under your punchline).
Needs Node.js (for `npx hyperframes render`) and ffmpeg. Nothing is uploaded.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import HF, die, load_json, need, npx, say  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job")
    ap.add_argument("--music")
    ap.add_argument("--drop", help="start,end seconds of music silence")
    a = ap.parse_args()
    job = Path(a.job).resolve()
    if not (job / "index.html").exists():
        die("no %s. Run build.py first." % (job / "index.html"))
    need("ffmpeg")
    dur = load_json(job / "scenes.json")["duration"]
    t0 = time.time()
    silent = job / "silent.mp4"
    r = subprocess.run([npx(), "-y", HF, "render", ".", "-o", str(silent)], cwd=str(job))
    if r.returncode != 0 or not silent.exists():
        die("the render failed. Read the lines above, and see references/setup.md.")
    render_s = time.time() - t0
    ins = ["-i", str(silent)]
    parts, labels, n = [], [], 1
    voice = job / "audio" / "voice.wav"
    if voice.exists():
        ins += ["-i", str(voice)]
        parts.append("[%d:a]loudnorm=I=-15:TP=-1.5:LRA=11[v]" % n)
        labels.append("[v]")
        n += 1
    hitsf = job / "audio" / "hits.wav"
    if hitsf.exists():
        ins += ["-i", str(hitsf)]
        parts.append("[%d:a]volume=0.5[h]" % n)
        labels.append("[h]")
        n += 1
    if a.music:
        ins += ["-stream_loop", "-1", "-i", a.music]
        drop = ""
        if a.drop:
            s, e = a.drop.split(",")
            drop = ",volume=enable='between(t,%s,%s)':volume=0" % (s, e)
        parts.append("[%d:a]volume=0.16%s,afade=t=out:st=%.2f:d=0.7[m]" % (n, drop, max(0, dur - 0.7)))
        labels.append("[m]")
    final = job / "final.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y"] + ins
    if labels:
        mix = ";".join(parts) + ";" + "".join(labels) + "amix=inputs=%d:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]" % len(labels)
        cmd += ["-filter_complex", mix, "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-t", str(dur), str(final)]
    subprocess.run(cmd, check=True)
    silent.unlink()
    say("done: %s (%.1f s of video, rendered in %.0f s)" % (final, dur, render_s))


if __name__ == "__main__":
    main()
