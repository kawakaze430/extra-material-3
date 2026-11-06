# Café pilot voice credits

The four original dialogue lines were synthesized locally with Piper 1.8.0 on CPU.

- Maya: `en_US-ljspeech-medium`, contributed by Bryce Beattie; its model card lists the LJ Speech training dataset as public domain and says the model was trained from scratch.
  - Model card: https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/ljspeech/medium/MODEL_CARD
  - Dataset: https://keithito.com/LJ-Speech-Dataset/
- Leo: `en_US-john-medium`, contributed by Bryce Beattie; its model card lists the LibriVox training recordings as public domain.
  - Model card: https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/john/medium/MODEL_CARD
  - Dataset source: https://librivox.org
- Piper software: https://github.com/OHF-Voice/piper1-gpl

These voice cards do not state an attribution requirement. This credit records the sources used. Ryan and Lessac were inspected but were not used in the pilot.

`dialogue.json` records each line's duration, voice, and timing method. When available, word timings come from Piper's own phoneme-duration alignments, grouped at word boundaries. These are model alignments, not a separate human-verified transcript alignment. Any fallback approximate timings are explicitly marked.
