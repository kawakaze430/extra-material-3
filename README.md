# Extra Material 3 — A Little Coffee Break

A 14-second café conversation starring two original illustrated characters, Maya and Leo. Created in Codex Cloud with two synthesized English voices, speaking gestures, blinks, mouth movement, and green captions with yellow word highlighting.

![Preview of Maya and Leo talking in the café](preview.png)

## Watch and download

- [Video: cafe-conversation.mp4](cafe-conversation.mp4) — 1280 × 720, 24 fps, H.264 video with AAC audio.
- [Reusable project: cafe-animation-project.zip](cafe-animation-project.zip) — renderer, character artwork, dialogue audio, timing metadata, captions, and setup instructions.
- [Subtitles: captions.srt](captions.srt)

GitHub may offer a download button instead of playing the MP4 inline. Download the video to watch it with sound.

## Render the project again

Extract `cafe-animation-project.zip`, open its `cafe-animation-project` folder, and use Python 3.11+ with FFmpeg installed:

```sh
python -m pip install -r requirements.txt
python render.py --output out.mp4
```

The bundled audio and artwork are enough to reproduce the conversation without a GPU or model downloads. The project README explains how to change the dialogue and generate new voices with Piper.

## Scope

This is limited 2D animation using eight illustrated poses per character and simplified speech-driven mouth shapes. It does not provide arbitrary full-body actions or editable 3D rigs.

The ZIP also includes a private Kaggle GPU preflight notebook and launcher. Kaggle authentication has not been configured, and no Kaggle GPU job has been run. That preflight checks hardware availability; it is not an advanced video-generation model.

Voice sources, font licenses, and tool credits are included in the project archive. No credentials, virtual environments, or model weights are included here.
