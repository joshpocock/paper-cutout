#!/usr/bin/env python3
"""The voice for JOB/script.txt. Writes JOB/audio/voice.wav.

  python scripts/voice.py JOB --file my_take.m4a        your own recording (any audio or video file)
  python scripts/voice.py JOB [--voice am_michael]      a free voice made on your computer (Kokoro, no key)

The free voice runs through `npx hyperframes tts`. The first run downloads the model once.
Voices: am_michael, am_adam, bm_george, af_heart, af_nova, bf_emma.
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import HF, die, job_dir, media_duration, need, npx, say  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job")
    ap.add_argument("--file", help="your own recording")
    ap.add_argument("--voice", default="am_michael", help="free voice id")
    ap.add_argument("--speed", default="1.05", help="free voice speed")
    a = ap.parse_args()
    job = job_dir(a.job)
    out = job / "audio" / "voice.wav"
    if a.file:
        if not Path(a.file).exists():
            die("no file %s" % a.file)
        subprocess.run([need("ffmpeg"), "-v", "error", "-y", "-i", a.file, "-vn", "-ac", "1", "-ar", "44100", str(out)], check=True)
    else:
        script = job / "script.txt"
        if not script.exists():
            die("no %s" % script)
        r = subprocess.run([npx(), "-y", HF, "tts", str(script), "-o", str(out), "-v", a.voice, "-s", a.speed])
        if r.returncode != 0 or not out.exists():
            die("the free voice failed. Record the script yourself and pass --file.")
    say("voice saved: %s (%.1f s)" % (out, media_duration(out)))


if __name__ == "__main__":
    main()
