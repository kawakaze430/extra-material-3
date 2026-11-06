# Working on this animation repository

Read `README.md` and `docs/HANDOFF.md` before changing the project. The root README points to the expanded source directory and downloadable project archive.

## Current implementation

- The published pilot is a 14-second, 720p, 24 fps illustrated 2D café conversation.
- Artwork was generated with an image-generation tool. Python/Pillow/NumPy select and composite sprite poses; Piper generates speech; FFmpeg exports MP4.
- The character assets are waist-up 4 × 2 sprite sheets. They contain two body poses with mouth/blink variants. There are no legs, skeletal rigs, editable Blender characters, or trained animation weights.
- The counter foreground masks the torso cut at y=548 in the existing 720p renderer. Removing this mask will not create the missing body.
- Full-body routes in the handoff are proposals. Do not describe them as implemented or claim a Kaggle GPU pipeline is working: only preflight tooling is present.

## Scope and continuity

- Follow the current user request. Documentation/recommendation work should not silently replace the renderer or redesign characters.
- Preserve the published pilot as a baseline. Use separate names/directories or a branch for new episode outputs and experiments.
- Treat `episode.json` as the editable dialogue/timing input. New dialogue needs speech and timing regeneration; rerendering existing WAVs alone cannot change spoken words.
- Inspect existing files before adding assets, especially when asked for full-body characters, camera changes, or new gestures.
- Preserve unrelated repository files such as `demo.py`.

## Validation and handling

- For source changes, run checks appropriate to the change. A representative frame preview and an audio/video probe are useful for render changes; avoid repeating full renders without a reason.
- Keep model timing distinct from manually corrected alignment, and limited sprite animation distinct from rigged or generative motion.
- Retain source/model/voice/font attribution. Use the checksummed voice downloader instead of committing environments or caches.
- Do not add credentials, tokens, `.env` contents, virtual environments, or downloaded model weights to commits. Use the cloud environment's secret configuration for authentication.
- Repository publishing, visibility changes, and external GPU submissions must stay within the user's current authorization. Do not infer a GPU connection merely from an installed CLI.
