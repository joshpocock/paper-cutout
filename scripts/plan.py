#!/usr/bin/env python3
"""Plan the scenes: one paper scene per phrase of JOB/script.txt, timed to JOB/audio/words.json.

  python scripts/plan.py JOB [--size 1080x1920] [--accent "#BA9926"]

Writes JOB/scenes.json. Every phrase becomes word tiles; the desk changes on every scene; the camera
pushes in or pulls out on every scene; the cut lands two frames before the first word.
You can edit scenes.json by hand, then run score.py to check it still follows the five rules.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import FPS, POSES_PER_SECOND, die, load_json, save_json, say  # noqa: E402

DESKS = ["grid", "wood", "mat", "kraft", "felt", "cork"]
MOVES = ["push", "pull"]   # alternate: pull-outs stay 33 to 50% for any scene count from 2 (the reels: 46%)
COLOURS = ["black", "white", "accent", "red"]
MAX_TILE_WORDS = 3
MAX_TILES = 3
MAX_SCENE_S = 2.3
CUT_LEAD_FRAMES = 2
FIRST_CHANGE_BY = 0.8


def _tile(cur, sent, last):
    text = " ".join(x["text"] for x in cur).strip(".,;:!?\"").upper()
    return {"text": text, "t": cur[0]["start"], "end": cur[-1]["end"], "sentence": sent, "last": last}


def chunk_words(words):
    """Group timed words into tiles of 1 to 3 words, breaking at punctuation."""
    tiles, cur, sent = [], [], 0
    for w in words:
        cur.append(w)
        end_sentence = w["text"][-1:] in ".?!"
        soft = w["text"][-1:] in ",;:"
        if end_sentence or soft or len(cur) >= MAX_TILE_WORDS:
            tiles.append(_tile(cur, sent, end_sentence))
            cur = []
        if end_sentence:
            sent += 1
    if cur:
        tiles.append(_tile(cur, sent, True))
    return tiles


def plan(words, size=(1080, 1920), accent="#BA9926"):
    tiles = chunk_words(words)
    groups, cur = [], []
    for t in tiles:
        too_long = cur and (t["end"] - cur[0]["t"]) > MAX_SCENE_S
        new_sentence = cur and t["sentence"] != cur[-1]["sentence"]
        early = cur and not groups and t["t"] > FIRST_CHANGE_BY      # the first scene change comes early
        if cur and (len(cur) >= MAX_TILES or too_long or new_sentence or early):
            groups.append(cur)
            cur = []
        cur.append(t)
    if cur:
        groups.append(cur)
    lead = CUT_LEAD_FRAMES / FPS
    scenes = []
    for i, g in enumerate(groups):
        start = 0.0 if i == 0 else round(max(0.0, g[0]["t"] - lead), 3)
        sentence = g[0]["sentence"]
        scenes.append({
            "start": start,
            "desk": DESKS[i % len(DESKS)],
            "move": MOVES[i % len(MOVES)],
            "sentence": sentence,
            "pose": sentence % 4,   # the person changes once per sentence, never inside one
            "tiles": [{"text": t["text"], "t": round(max(start, t["t"]), 3), "colour": COLOURS[(i + k) % 4], "enter": "cut"}
                      for k, t in enumerate(g)],
        })
    duration = round(words[-1]["end"] + 0.7, 3)
    for i, s in enumerate(scenes):
        s["end"] = scenes[i + 1]["start"] if i + 1 < len(scenes) else duration
    return {"size": list(size), "fps": FPS, "poses_per_second": POSES_PER_SECOND, "accent": accent, "word_overshoot": 0,
            "cut_lead_frames": CUT_LEAD_FRAMES, "duration": duration, "scenes": scenes}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job")
    ap.add_argument("--size", default="1080x1920", help="1080x1920 (vertical) or 1920x1080 (wide)")
    ap.add_argument("--accent", default="#BA9926", help="your border and highlight colour")
    a = ap.parse_args()
    job = Path(a.job)
    wp = job / "audio" / "words.json"
    if not wp.exists():
        die("no %s. Run words.py first." % wp)
    w, h = (int(x) for x in a.size.lower().split("x"))
    data = plan(load_json(wp), (w, h), a.accent)
    save_json(job / "scenes.json", data)
    n = len(data["scenes"])
    say("%d scenes over %.1f s (about one every %.2f s)" % (n, data["duration"], data["duration"] / n))


if __name__ == "__main__":
    main()
