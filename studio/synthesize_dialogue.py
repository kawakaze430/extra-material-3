"""Generate the café pilot dialogue locally with Piper and model alignments."""

from pathlib import Path
import json
import re
import wave

import numpy as np
import onnx
import onnxruntime as ort
from piper import PiperVoice, SynthesisConfig
from piper.config import PiperConfig
from piper.patch_voice_with_alignment import add_alignment_output


ROOT = Path(__file__).resolve().parent
VOICE_DIR = ROOT / "voices"
AUDIO_DIR = ROOT / "audio"
SUPPORTED_VOICES = {"ljspeech", "john"}


def load_dialogue():
    """Read editable episode text while keeping known character and voice assets."""
    episode = json.loads((ROOT / "episode.json").read_text(encoding="utf-8"))
    dialogue = episode.get("dialogue")
    if not isinstance(dialogue, list) or not dialogue:
        raise ValueError("episode.json must contain a nonempty dialogue list")
    lines = []
    for index, row in enumerate(dialogue, 1):
        if not isinstance(row, dict):
            raise ValueError(f"Dialogue line {index} must be an object")
        speaker, voice, text = row.get("speaker"), row.get("voice"), row.get("text")
        if speaker not in {"Maya", "Leo"}:
            raise ValueError(f"Dialogue line {index}: supported speakers are Maya and Leo")
        if voice not in SUPPORTED_VOICES:
            raise ValueError(f"Dialogue line {index}: voice must be ljspeech or john")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Dialogue line {index} needs nonempty text")
        lines.append((speaker, voice, text.strip()))
    return lines


def load_voice(name):
    path = VOICE_DIR / f"en_US-{name}-medium.onnx"
    model = onnx.load(str(path))
    add_alignment_output(model)
    settings = ort.SessionOptions()
    settings.intra_op_num_threads = 2
    settings.inter_op_num_threads = 1
    settings.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    session = ort.InferenceSession(
        model.SerializeToString(),
        sess_options=settings,
        providers=["CPUExecutionProvider"],
    )
    config = PiperConfig.from_dict(json.loads(Path(str(path) + ".json").read_text()))
    return PiperVoice(session=session, config=config, download_dir=VOICE_DIR)


def synthesize_line(voice, index, speaker, voice_name, text):
    config = SynthesisConfig(
        length_scale=0.98 if speaker == "Maya" else 0.96,
        noise_scale=0.55,
        noise_w_scale=0.65,
        normalize_audio=True,
        volume=0.90,
    )
    chunks = list(voice.synthesize(text, config, include_alignments=True))
    rate = chunks[0].sample_rate
    parts = []
    phonemes = []
    groups = []
    cursor_samples = 0
    for chunk_index, chunk in enumerate(chunks):
        parts.append(chunk.audio_int16_array)
        active = []
        local_samples = 0
        for alignment in chunk.phoneme_alignments or []:
            start = (cursor_samples + local_samples) / rate
            end = (cursor_samples + local_samples + alignment.num_samples) / rate
            local_samples += alignment.num_samples
            symbol = alignment.phoneme
            if symbol not in {"^", "$", "_"}:
                phonemes.append({"phoneme": symbol, "start": round(start, 6), "end": round(end, 6)})
            if symbol.isspace() or symbol in {"^", "$"}:
                if active:
                    groups.append(active)
                    active = []
            elif symbol not in {"_", ".", ",", "!", "?", ";", ":"}:
                active.append({"phoneme": symbol, "start": start, "end": end})
        if active:
            groups.append(active)
        cursor_samples += len(chunk.audio_int16_array)
        if chunk_index + 1 < len(chunks):
            # Preserve a short, natural pause between punctuation-separated sentences.
            pause = np.zeros(round(0.12 * rate), dtype=np.int16)
            parts.append(pause)
            cursor_samples += len(pause)

    signal = np.concatenate(parts)
    path = AUDIO_DIR / f"line_{index:02d}.wav"
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(signal.tobytes())

    text_words = re.findall(r"\S+", text)
    aligned = len(groups) == len(text_words)
    duration = len(signal) / rate
    if aligned:
        words = [
            {"word": word, "start": round(group[0]["start"], 6), "end": round(group[-1]["end"], 6)}
            for word, group in zip(text_words, groups)
        ]
    else:
        # This fallback is explicitly marked in metadata, never presented as measured alignment.
        weights = [max(1, len(re.sub(r"\W", "", word))) for word in text_words]
        total_weight = sum(weights)
        words, cursor = [], 0.0
        for word, weight in zip(text_words, weights):
            end = cursor + duration * weight / total_weight
            words.append({"word": word, "start": round(cursor, 6), "end": round(end, 6)})
            cursor = end

    return {
        "index": index,
        "speaker": speaker,
        "text": text,
        "voice": f"en_US-{voice_name}-medium",
        "voice_model": f"voices/en_US-{voice_name}-medium.onnx",
        "voice_config": f"voices/en_US-{voice_name}-medium.onnx.json",
        "file": path.relative_to(ROOT).as_posix(),
        "sample_rate": rate,
        "duration": round(duration, 6),
        "word_timing_method": "Piper model phoneme-duration alignment grouped by word" if aligned else "approximate proportional text-length timing",
        "word_timing_approximate": not aligned,
        "words": words,
        "phonemes": phonemes,
        "peak_dbfs": round(20 * np.log10(max(1, np.max(np.abs(signal.astype(np.float64)))) / 32768), 2),
        "clipped_samples": int(np.sum(np.abs(signal.astype(np.int32)) >= 32767)),
    }


def main():
    dialogue = load_dialogue()
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    voices = {name: load_voice(name) for name in {row[1] for row in dialogue}}
    lines = []
    for index, (speaker, voice_name, text) in enumerate(dialogue, 1):
        line = synthesize_line(voices[voice_name], index, speaker, voice_name, text)
        lines.append(line)
        print(f"{line['file']}: {line['duration']:.2f}s, {line['word_timing_method']}", flush=True)
    result = {"episode": "episode.json", "synthesizer": "piper-tts 1.8.0", "device": "CPU", "max_threads_per_session": 2, "lines": lines}
    (AUDIO_DIR / "dialogue.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
