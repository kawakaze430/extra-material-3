# A Little Coffee Break

A reusable, CPU-rendered café conversation with original illustrated characters Maya and Leo, two synthesized English voices, gestures, listener reactions, lip movement, and green captions with yellow word highlighting.

## Render the bundled conversation

Use Python 3.11 or later and install FFmpeg so `ffmpeg` is available on your command path. Run these commands from this folder in a Python virtual environment:

```sh
python -m pip install -r requirements.txt
python render.py --output out.mp4
```

The included WAV files and alignment metadata are enough to rerender the original conversation. No model download or GPU is needed for that command. The renderer also writes a combined dialogue WAV, a timing manifest, and an SRT caption file beside the source assets. Output video is 1280 × 720 at 24 fps.

`episode.json` contains the title, intro/turn/outro pauses, character names, and editable dialogue. Changing pause values only requires rerendering. Changing spoken text requires regenerating the speech first.

## Generate new dialogue with the same characters

Edit the `dialogue` list in `episode.json`. Keep speakers as `Maya` or `Leo`; the available voice names are `ljspeech` and `john`.

```json
{
  "speaker": "Maya",
  "voice": "ljspeech",
  "text": "Could I have a cappuccino, please?"
}
```

Install the optional speech dependencies and download the two official Piper voice models:

```sh
python -m pip install -r requirements-speech.txt
python setup/download_voices.py
python synthesize_dialogue.py
python render.py --output out.mp4
```

The downloader fetches about 127 MB of model weights, their configurations, and their model cards directly from `rhasspy/piper-voices` on Hugging Face. It checks SHA-256 hashes and reuses matching local downloads. If an upstream file changes, it stops rather than using an unverified replacement. Models and virtual environments are separate from the portable source bundle.

Speech synthesis uses Piper 1.8.0 on CPU, with two inference threads per voice session. It replaces `audio/line_*.wav` for the current dialogue and rewrites `audio/dialogue.json`; copy a finished episode before generating a new one. Generated metadata records relative model, configuration, and audio paths.

Word timings are grouped from Piper's phoneme-duration alignments. These are model-generated timings and have not been manually corrected. A fallback uses approximate proportional word timing and is explicitly marked in the metadata when needed.

## Animation scope

Each character has eight illustrated poses in a transparent 4 × 2 sheet. The renderer selects mouth and gesture poses, adds subtle movement and blinking, and gives the listening character reactions. This is limited 2D character animation. The assets contain a fixed set of poses and expressions; they cannot supply arbitrary new views, actions, or precise finger movements.

Advanced image/video-driven performances using models such as InfiniteTalk require a compatible remote GPU runtime. Kaggle can serve as that remote job runner when an authenticated account has GPU access; it does not turn this CPU environment into a GPU machine. See the separate `kaggle/` instructions for the prepared workflow and its current execution status.

## Files and sources

- `assets/cafe.png`, `assets/maya.png`, `assets/leo.png`: original illustrations generated for this pilot with OpenAI image generation.
- `episode.json`: reusable dialogue and episode timing configuration.
- `render.py`: original Pillow/NumPy/FFmpeg animation and export code.
- `synthesize_dialogue.py`: local speech generation and alignment metadata.
- `audio/VOICE_CREDITS.md`: voice model and dataset credits.
- Piper software: https://github.com/OHF-Voice/piper1-gpl
- Piper voice models: https://huggingface.co/rhasspy/piper-voices
- Pillow: https://python-pillow.org/
- NumPy: https://numpy.org/
- FFmpeg: https://ffmpeg.org/

Maya uses `en_US-ljspeech-medium`; Leo uses `en_US-john-medium`. Their model cards identify the source recordings as public domain. Credits retain the source links. The model cards do not state an attribution requirement; third-party tools retain their own licenses.

The local pilot was rendered with Python 3.12, Pillow 13.0.0, NumPy 2.3.5, and FFmpeg 7.1.5. The optional speech environment used Piper 1.8.0. Regeneration can vary slightly because synthesis includes stochastic voice variation.
