# What was actually used

| Stage | Tool or asset | Role |
| --- | --- | --- |
| Art | OpenAI image-generation tool | Cafe background and original Maya/Leo pose sheets; exact prompts are in `ASSET_GENERATION.md`. Exact model version was not returned. |
| Speech | Piper 1.8.0 | CPU synthesis of the four English dialogue lines. |
| Maya voice | `en_US-ljspeech-medium` | Pretrained Piper voice; no custom training or voice cloning. |
| Leo voice | `en_US-john-medium` | Pretrained Piper voice; no custom training or voice cloning. |
| Speech runtime | ONNX 1.23.2, ONNX Runtime 1.31.1 | Model loading, CPU inference, and Piper alignment output. |
| Animation | Python 3.12.14, Pillow 13.0.0, NumPy 2.3.5 | Sprite selection, transforms, compositing, audio timeline, word highlights and titles. |
| Video export | FFmpeg 7.1.5 | H.264/AAC MP4 encoding, audio normalization, 48 kHz audio, faststart. |
| Typography | DejaVu Sans/Serif | Bundled font files with their original license. |
| Delivery | Git and GitHub CLI | Repository upload; these do not generate the animation. |

The speech environment used NumPy 2.5.4 separately from the renderer's NumPy 2.3.5. See `studio/environment/` for recorded versions. Requirements files describe the small packages needed to run the project; they do not recreate the whole Codex machine.

## Data flow

```text
episode.json dialogue
  -> Piper voice weights + synthesize_dialogue.py
  -> line WAVs + audio/dialogue.json (words and phonemes)

background + character sheets + line WAVs + timing metadata
  -> render.py
  -> composited RGB frames + dialogue timeline WAV
  -> FFmpeg
  -> MP4 + captions.srt + timeline.json
```

Piper's phoneme durations are grouped into word timings. The renderer chooses three mouth states using those phonemes plus audio amplitude; this is simplified mouth animation, not a complete viseme system. Body poses crossfade between two drawings. Breathing and nodding use small programmed vertical movements. The camera performs a gentle crop-and-scale move.

The renderer generates quiet room tone and short bell-like tones mathematically. There is no downloaded music track. Voice data, generated line audio, captions, timing data, font files, and artwork are included in `studio/`.

## Reproduction

To render the bundled dialogue, only the artwork, prerecorded WAVs, timing metadata, Python dependencies, and FFmpeg are needed. No API access or model download is required:

```bash
cd studio
python -m pip install -r requirements.txt
python render.py --output next-render.mp4
```

For new spoken dialogue, use `studio/setup/download_voices.py` and the speech requirements, then edit `studio/episode.json`, synthesize, and render. The model downloader verifies SHA-256 hashes. `studio/model-sources.json` lists URLs, hashes, local filenames and whether each file is bundled. The two large ONNX weight files are retrieved from their original host; they are not copied into Git history. Voice model cards and JSON configurations are included.

Art generation and speech synthesis can vary across reruns. The checked-in art and WAVs reproduce the visual/audio inputs; an exact byte-identical MP4 additionally depends on the encoder and runtime versions.

## Tools that were not used to render this pilot

Blender was installed in the environment but did not render this video. Rhubarb, ComfyUI, WanGP, InfiniteTalk, MultiTalk and LongCat were not used. No video model or LoRA was trained. No GPU inference was performed.

Kaggle CLI 2.2.5 and `six` 1.17.0 were installed separately for a possible future GPU connection. The `studio/kaggle/` folder contains a hardware preflight only. No Kaggle authentication was configured and no Kaggle GPU job ran as part of this production.

## Source and license records

- [Piper software](https://github.com/OHF-Voice/piper1-gpl)
- [Piper voice models](https://huggingface.co/rhasspy/piper-voices)
- [Voice credits](../studio/audio/VOICE_CREDITS.md)
- [Used voice model cards](../studio/voices/)
- [Bundled font license](../studio/assets/fonts/LICENSE.txt)
- [FFmpeg](https://ffmpeg.org/), [Pillow](https://python-pillow.org/), [NumPy](https://numpy.org/)

The voice cards describe their training recordings as public domain. That statement is not a blanket license for every tool or asset: the original software and font licenses still apply. No license for unrelated third-party assets is implied.
