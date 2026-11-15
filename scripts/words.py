#!/usr/bin/env python3
"""Word timings: when each word of JOB/script.txt is spoken. Writes JOB/audio/words.json.

  python scripts/words.py JOB                      spread the words over JOB/audio/voice.wav by word length
  python scripts/words.py JOB --from heard.json    use a transcript ([{"text","start","end"}]) and align it to your script
  python scripts/words.py JOB --wps 2.6            no audio yet: pace the words at this many words a second
"""
import argparse
import difflib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import die, load_json, media_duration, norm, save_json, say  # noqa: E402


def estimate(words, total, lead=0.1):
    """Spread words over `total` seconds. Longer words get more time; sentence ends get a short pause."""
    weights = []
    for w in words:
        wt = 1.0 + len(norm(w)) * 0.35
        if w[-1:] in ".?!":
            wt += 2.2
        elif w[-1:] in ",;:":
            wt += 1.0
        weights.append(wt)
    scale = max(0.01, total - lead) / sum(weights)
    out, t = [], lead
    for w, wt in zip(words, weights):
        spoken = (1.0 + len(norm(w)) * 0.35) * scale
        out.append({"text": w, "start": round(t, 3), "end": round(t + spoken, 3)})
        t += wt * scale
    return out


def align(words, heard):
    """Give every script word a time from the transcript. Unmatched runs share the gap between matches."""
    a = [norm(w) for w in words]
    b = [norm(h["text"]) for h in heard]
    times = [None] * len(words)
    for blk in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = (float(heard[blk.b + k]["start"]), float(heard[blk.b + k]["end"]))
    end_all = float(heard[-1]["end"]) if heard else 0.0
    i = 0
    while i < len(words):
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < len(words) and times[j] is None:
            j += 1
        t0 = times[i - 1][1] if i > 0 else 0.0
        t1 = times[j][0] if j < len(words) else end_all
        step = max(0.0, t1 - t0) / (j - i)
        for k in range(i, j):
            times[k] = (t0 + (k - i) * step, t0 + (k - i + 1) * step)
        i = j
    return [{"text": w, "start": round(s, 3), "end": round(e, 3)} for w, (s, e) in zip(words, times)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job")
    ap.add_argument("--from", dest="src", help="transcript JSON to align to the script")
    ap.add_argument("--wps", type=float, help="words a second when there is no audio yet")
    a = ap.parse_args()
    job = Path(a.job)
    script = job / "script.txt"
    if not script.exists():
        die("no %s" % script)
    words = script.read_text(encoding="utf-8").split()
    if not words:
        die("script.txt is empty")
    if a.src:
        heard = load_json(a.src)
        heard = heard.get("words", heard) if isinstance(heard, dict) else heard
        out = align(words, heard)
    elif a.wps:
        out = estimate(words, len(words) / a.wps + 0.4)
    else:
        voice = job / "audio" / "voice.wav"
        if not voice.exists():
            die("no %s. Run voice.py first, or pass --wps 2.6" % voice)
        out = estimate(words, media_duration(voice))
    (job / "audio").mkdir(parents=True, exist_ok=True)
    save_json(job / "audio" / "words.json", out)
    say("%d words, last ends at %.2f s" % (len(out), out[-1]["end"]))


if __name__ == "__main__":
    main()
