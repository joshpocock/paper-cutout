---
name: paper-cutout
description: Make a paper cut-out stop-motion video from a script, a photo and a voice, built entirely in code (no video editor, no AI video or image generator). Your real face becomes a paper sticker on a tiny body, on desks drawn in code, moving at 16 poses a second with word tiles that drop in. Use when someone says "make a paper cutout video", "paper cut-out style", "stop motion paper video", "turn this script into a paper video", "make me a paper person", "faceless paper style video", "score my paper video" or "/paper-cutout".
---

# Paper Cutout

Turns a short script, one or two photos and a voice into a finished video in the paper cut-out
stop-motion look. Claude never posts or uploads anything. The video is a file on your computer.

The tools actually run: everything in `scripts/` is plain Python. `words.py`, `plan.py`, `score.py`,
`build.py`, `render.py` and `make.py` use the standard library only. `person.py` and `desks.py` need
Pillow (`pip install pillow`), and a photo with a background also needs `rembg`. Rendering needs
Node.js and ffmpeg. Setup and fixes: [references/setup.md](references/setup.md). If code cannot run
here, say so, and still do steps 1, 2 and 5 by hand (the script, the scene plan, the scorecard).

## Steps

1. **Intake. Ask for three things, once.** (a) A photo of the person, head and shoulders, mouth
   closed, and if they have one, the same framing with the mouth open (that is what makes it talk).
   It must be their own face or a character they made. (b) The script: 30 to 120 words, short
   sentences, one picture per line. (c) The voice: their own recording, or a free voice made on
   their computer. Also ask vertical (1080x1920) or wide (1920x1080), and a border colour.
2. **Tighten the script** only if asked. Keep every number and name. Save it as `JOB/script.txt`
   where JOB is a new folder in their project, for example `paper/first-video`.
3. **Make it.** One command runs every step and stops if the scorecard fails:
   `python scripts/make.py JOB --photo me.jpg --open me_open.jpg --take my_voice.m4a`
   Leave out `--take` for the free voice. Add `--size 1920x1080`, `--accent "#C0281C"`,
   `--music bed.mp3` as needed. Add `--no-render` to stop before the render.
   The steps, if you need to run one alone: `person.py` (the paper person), `desks.py` (the six
   desks), `voice.py`, `words.py` (word timings), `plan.py` (one scene per phrase, written to
   `JOB/scenes.json`), `score.py`, `build.py` (the page), `render.py` (the mp4).
4. **Better word timing (optional).** `words.py` spreads the words over the voice by length. For
   exact timing give it a transcript with word times: `python scripts/words.py JOB --from words.json`,
   then run `plan.py`, `score.py`, `build.py` and `render.py` again.
5. **Read the scorecard out loud.** `python scripts/score.py JOB` prints one row per check against
   the five rules in [references/look-rules.md](references/look-rules.md). Every row must pass
   before rendering. If you edit `scenes.json` by hand (different words on a tile, a different desk,
   a held shot), score it again.
6. **Look before you hand it over.** Pull four frames from `JOB/final.mp4` with ffmpeg and check:
   no word runs off the frame, the face is not covered, the first frame already has the person and
   a word. Fix `scenes.json` and rebuild if not.

## Hard rules

- The five rules are the look. Do not add fades, easing, bouncing words or smooth 30-a-second
  motion to "improve" it. Word tiles appear whole on their pose.
- The person's pose changes once per sentence at most. Never inside a sentence.
- Only the user's own face, or a character they made or own. If they ask for a celebrity or
  another real person, say no and offer their own face.
- No AI image or video model is used, and no key is needed. Do not add one.
- Music must be a file the user has the right to use. Never download music for them.
- Nothing is posted, uploaded or sent. Publishing is the user's own step.

## What to hand back

The path to `final.mp4`, its length and render time, the scorecard (rows passed of rows total),
which voice and timing method were used, and anything you changed in `scenes.json` by hand.
End with one question: **"Want a second version with a different border colour or the wide size?"**
