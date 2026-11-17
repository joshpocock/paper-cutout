# Setup and fixes

Written for Windows, macOS and Linux; tested on Windows 11. Nothing here needs an account or a key.

## Install the skill by hand

Clone it into the `skills` folder inside your Claude config folder, named `paper-cutout`:

Windows (Command Prompt):
```
git clone https://github.com/joshpocock/paper-cutout.git "%USERPROFILE%\.claude\skills\paper-cutout"
```

Mac or Linux (untested on Mac):
```
git clone https://github.com/joshpocock/paper-cutout.git "$HOME/.claude"/skills/paper-cutout
```

Then check this computer and run the test: `python scripts/doctor.py` and `python scripts/selftest.py`.

## What to install once

| Thing | Why | Check it |
|---|---|---|
| Python 3.8 or newer | runs every tool | `python --version` |
| Pillow | draws the paper person and the desks | `pip install pillow` |
| rembg (optional) | cuts you out of a photo that has a background | `pip install rembg` |
| Node.js 20 or newer | `npx hyperframes render` turns the page into video | `node --version` |
| ffmpeg | mixes the voice and writes the mp4 | `ffmpeg -version` |

The first render downloads HyperFrames and a browser once. After that it works offline.

## The free voice

`voice.py` without `--file` uses a free local voice through `npx hyperframes tts`. It needs two
Python packages the first time: `pip install kokoro-onnx soundfile`. If that fails, record the
script on your phone and pass the file: `python scripts/voice.py JOB --file take.m4a`.

## Common problems

- **"has a background"** from `person.py`: install rembg, or remove the background in any photo
  app and save a transparent PNG.
- **The person does not talk:** you gave one photo. Add `--open` with the same framing and your
  mouth open. Take both photos one after the other without moving.
- **The mouth jumps sideways when it opens:** the two photos are framed differently. Retake them.
- **"Low disk space" from the render:** the render needs a few GB free. Free some space or put the
  job folder on another drive.
- **Words feel early or late:** the default timing is an estimate. Use a word-level transcript
  with `words.py JOB --from words.json`.
- **A word runs off the frame:** open `JOB/scenes.json`, shorten that tile's text or split it into
  two tiles, then run `score.py`, `build.py` and `render.py` again.
- **Render is slow:** expect about 7 seconds of render per second of video on a busy computer, less on an idle
  one. In testing, videos of 11 to 32 seconds took 1 min 42 s to 3 min 49 s start to finish (runs saved).

## The job folder

```
JOB/
  script.txt          your words
  assets/             person_0.png, person_1.png, six desks, paper, grain, the font
  audio/              voice.wav, words.json, hits.wav
  scenes.json         the plan (safe to edit by hand)
  index.html          the page that gets rendered
  final.mp4           the video
```

The font is Anton (SIL Open Font License), included in `kit/fonts/`.
