# The five rules of the paper cut-out look

These numbers were measured frame by frame from five short videos in this look by two different
makers, then checked against a rebuild. `scripts/score.py` tests a plan against them.

## Rule 1. Sixteen poses a second

The video file is 30 frames a second, but the picture only changes about 16 times a second, so most
poses are held for two frames. All five videos did this. `build.py` draws every piece from the pose
number, `floor(time x 16)`, so nothing can move between poses.

Check: poses a second = 16, video frames a second = 30.

## Rule 2. A new desk about every second and a half

A new scene roughly every 1.5 seconds, and almost every scene sits on a new surface: grid paper,
a cutting mat, kraft paper, felt, wood, cork. The first change comes early.

Checks: median scene length 0.65 to 2.57 s; at least 0.9 of scenes on a different desk from the
one before; first scene change at 1.71 s or sooner.

## Rule 3. Words do not bounce

Big words do not fade, slide or scale in. A tile is absent on one pose and whole on the next. The
only life is a small settle of rotation over two poses, like dropped paper. Measured overshoot: 0%.

Checks: 0 tiles with an entrance other than "cut"; overshoot 0.

## Rule 4. The camera never stops

Every scene pushes in or pulls out: a big first step, a slow drift, then a fast move into a hard
cut. In the main video 22 of 27 shots moved and the longest still was 0.93 s. Pull-outs were 46% of
shots. The cut lands about two frames before the first word of the new line. No fades anywhere.

Checks: at least 0.75 of scenes moving; pull-outs 0.31 to 0.61; no still of 1.0 s or longer; the
cut 1 to 3 frames before the word.

## Rule 5. The paper person

A real photo of a face, printed big, on a tiny body. A thin white cut line, a thick border in one
colour, print grain and a soft shadow. The mouth swaps between two real photos (closed and open)
from the loudness of the voice, so it talks. The pose changes once per sentence at most; a person
that changes pose inside a sentence reads as a glitch.

Checks: 0 pose changes inside a sentence; every word tile sits inside its own scene.

## Three things that went wrong in the first build

1. **The mouth.** Cutting the jaw and dropping it looked like a black bar over the face. Swapping
   two real photos fixed it.
2. **Bouncing words.** The first build scaled words in with a bounce, the habit of every motion
   graphics template. Removing it made the video look more handmade at once.
3. **Flat desks.** Plain colour fills looked digital. Fibre, a lamp in one corner and a dark edge
   on every desk fixed it. Shadows are the only depth in this look: without them it is a slide.

## What the score does not see

The scorecard reads the plan, not the pixels. It cannot tell you that a word is hard to read on a
dark desk, that the face is covered, or that the script is dull. Look at the frames yourself.
