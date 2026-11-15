#!/usr/bin/env python3
"""Score JOB/scenes.json against the five rules of the paper cut-out look. Exit code 1 if any row fails.

  python scripts/score.py JOB [--json]

The ranges were measured from five reels in this look (see references/look-rules.md).
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import die, load_json  # noqa: E402


def score(d):
    sc = d["scenes"]
    rows = []

    def row(rule, name, value, ok, want):
        rows.append({"rule": rule, "check": name, "value": value, "want": want, "pass": bool(ok)})

    lens = [s["end"] - s["start"] for s in sc]
    row(1, "poses a second", d.get("poses_per_second"), d.get("poses_per_second") == 16, "16")
    row(1, "video frames a second", d.get("fps"), d.get("fps") == 30, "30")
    med = round(statistics.median(lens), 2)
    row(2, "median scene length (s)", med, 0.65 <= med <= 2.57, "0.65 to 2.57")
    new_desk = sum(1 for a, b in zip(sc, sc[1:]) if a["desk"] != b["desk"]) / max(1, len(sc) - 1)
    row(2, "scenes on a new desk (share)", round(new_desk, 2), new_desk >= 0.9, "0.9 or more")
    first = round(sc[1]["start"], 2) if len(sc) > 1 else 0
    row(2, "first scene change (s)", first, len(sc) < 2 or first <= 1.71, "1.71 or sooner")
    bounce = sum(1 for s in sc for t in s["tiles"] if t.get("enter", "cut") != "cut")
    row(3, "word tiles that animate in", bounce, bounce == 0, "0")
    row(3, "word overshoot (%)", d.get("word_overshoot", 0), d.get("word_overshoot", 0) == 0, "0")
    moving = sum(1 for s in sc if s["move"] in ("push", "pull")) / len(sc)
    row(4, "scenes with a moving camera (share)", round(moving, 2), moving >= 0.75, "0.75 or more")
    pulls = sum(1 for s in sc if s["move"] == "pull") / len(sc)
    row(4, "pull-outs (share)", round(pulls, 2), 0.31 <= pulls <= 0.61, "0.31 to 0.61")
    still = max([ln for s, ln in zip(sc, lens) if s["move"] not in ("push", "pull")] or [0])
    row(4, "longest still (s)", round(still, 2), still < 1.0, "under 1.0")
    lead = d.get("cut_lead_frames", 0)
    row(4, "cut lands before the word (frames)", lead, 1 <= lead <= 3, "1 to 3")
    flick = sum(1 for a, b in zip(sc, sc[1:]) if a["sentence"] == b["sentence"] and a.get("pose") != b.get("pose"))
    row(5, "pose changes inside a sentence", flick, flick == 0, "0")
    stray = sum(1 for s in sc for t in s["tiles"] if not (s["start"] - 0.001 <= t["t"] < s["end"]))
    row(5, "words placed outside their scene", stray, stray == 0, "0")
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job")
    ap.add_argument("--json", action="store_true", help="print the scorecard as JSON")
    a = ap.parse_args()
    p = Path(a.job) / "scenes.json"
    if not p.exists():
        die("no %s. Run plan.py first." % p)
    rows = score(load_json(p))
    ok = sum(r["pass"] for r in rows)
    if a.json:
        print(json.dumps({"pass": ok, "of": len(rows), "rows": rows}, indent=1))
    else:
        for r in rows:
            print("%s  rule %d  %-38s %-8s want %s" % ("PASS" if r["pass"] else "FAIL", r["rule"], r["check"], r["value"], r["want"]))
        print("\n%d of %d rows pass" % (ok, len(rows)))
    sys.exit(0 if ok == len(rows) else 1)


if __name__ == "__main__":
    main()
