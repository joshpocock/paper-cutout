"""Shared helpers for the paper-cutout tools (standard library only)."""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSES_PER_SECOND = 16
FPS = 30


def die(msg):
    print("ERROR: " + msg)
    sys.exit(1)


def say(msg):
    print(msg, flush=True)


def job_dir(name):
    p = Path(name)
    p.mkdir(parents=True, exist_ok=True)
    for sub in ("assets", "audio"):
        (p / sub).mkdir(exist_ok=True)
    return p


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=1), encoding="utf-8")


def norm(word):
    return re.sub(r"[^a-z0-9']", "", word.lower().replace("’", "'"))


def need(tool):
    if shutil.which(tool) is None:
        die("%s is not installed or not on PATH. See references/setup.md." % tool)
    return tool


def media_duration(path):
    out = subprocess.run([need("ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out) if out else 0.0


HF = "hyperframes@0.8.222"   # pinned: an unpinned npx checks the internet for a newer version on every run


def npx():
    return "npx.cmd" if os.name == "nt" else "npx"
