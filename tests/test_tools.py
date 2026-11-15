import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import plan as plan_mod  # noqa: E402
import score as score_mod  # noqa: E402
import words as words_mod  # noqa: E402

SCRIPT = ("Stop renaming your files by hand. Claude can do it in one line. Point it at a folder. "
          "Tell it the pattern you want. It shows you the new names first, so nothing breaks. "
          "Say yes, and four hundred files are renamed in two seconds. That is the whole trick.")


def timed():
    return words_mod.estimate(SCRIPT.split(), 16.5)


class WordsTest(unittest.TestCase):
    def test_estimate_is_ordered_and_fills_the_time(self):
        w = timed()
        self.assertEqual(len(w), len(SCRIPT.split()))
        self.assertTrue(all(a["start"] < b["start"] for a, b in zip(w, w[1:])))
        self.assertLessEqual(w[-1]["end"], 16.5 + 1e-6)

    def test_align_uses_heard_times_and_fills_gaps(self):
        words = "the mat is green today".split()
        heard = [{"text": "the", "start": 0.0, "end": 0.2}, {"text": "mat", "start": 0.2, "end": 0.5},
                 {"text": "today", "start": 1.4, "end": 1.9}]
        out = words_mod.align(words, heard)
        self.assertEqual(out[1]["start"], 0.2)
        self.assertEqual(out[4]["start"], 1.4)
        self.assertTrue(0.5 <= out[2]["start"] < out[3]["start"] < 1.4)


class PlanTest(unittest.TestCase):
    def setUp(self):
        self.plan = plan_mod.plan(timed())

    def test_every_word_is_on_a_tile(self):
        said = " ".join(t["text"] for s in self.plan["scenes"] for t in s["tiles"]).split()
        self.assertEqual(len(said), len(SCRIPT.split()))

    def test_tiles_are_short_and_scenes_do_not_overlap(self):
        for s in self.plan["scenes"]:
            self.assertLessEqual(len(s["tiles"]), plan_mod.MAX_TILES)
            for t in s["tiles"]:
                self.assertLessEqual(len(t["text"].split()), plan_mod.MAX_TILE_WORDS)
                self.assertEqual(t["enter"], "cut")
        for a, b in zip(self.plan["scenes"], self.plan["scenes"][1:]):
            self.assertEqual(a["end"], b["start"])
            self.assertNotEqual(a["desk"], b["desk"])

    def test_pose_never_changes_inside_a_sentence(self):
        for a, b in zip(self.plan["scenes"], self.plan["scenes"][1:]):
            if a["sentence"] == b["sentence"]:
                self.assertEqual(a["pose"], b["pose"])

    def test_fresh_plan_passes_the_scorecard(self):
        rows = score_mod.score(self.plan)
        self.assertTrue(all(r["pass"] for r in rows), [r for r in rows if not r["pass"]])


class ScoreTest(unittest.TestCase):
    def setUp(self):
        self.plan = plan_mod.plan(timed())

    def failed(self, plan):
        return {r["check"] for r in score_mod.score(plan) if not r["pass"]}

    def test_bouncing_word_fails_rule_three(self):
        p = copy.deepcopy(self.plan)
        p["scenes"][0]["tiles"][0]["enter"] = "bounce"
        self.assertIn("word tiles that animate in", self.failed(p))

    def test_smooth_thirty_fails_rule_one(self):
        p = copy.deepcopy(self.plan)
        p["poses_per_second"] = 30
        self.assertIn("poses a second", self.failed(p))

    def test_still_camera_everywhere_fails_rule_four(self):
        p = copy.deepcopy(self.plan)
        for s in p["scenes"]:
            s["move"] = "still"
        self.assertIn("scenes with a moving camera (share)", self.failed(p))

    def test_same_desk_twice_fails_rule_two(self):
        p = copy.deepcopy(self.plan)
        for s in p["scenes"]:
            s["desk"] = "grid"
        self.assertIn("scenes on a new desk (share)", self.failed(p))

    def test_pose_flicker_fails_rule_five(self):
        p = copy.deepcopy(self.plan)
        for a, b in zip(p["scenes"], p["scenes"][1:]):
            if a["sentence"] == b["sentence"]:
                b["pose"] = a["pose"] + 1
                break
        self.assertIn("pose changes inside a sentence", self.failed(p))


if __name__ == "__main__":
    unittest.main()
