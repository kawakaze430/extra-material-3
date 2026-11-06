#!/usr/bin/env python3
"""Render the illustrated café dialogue with a CPU-only Pillow/FFmpeg pipeline.

The eight-frame character sheets are original generated illustrations. Mouth
poses follow the speech signal and Piper's model phoneme timings; this is
limited 2D sprite animation, not a generative video or a fully rigged 3D scene.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1280, 720, 24
SR = 22050
SANS = str(ROOT / 'assets/fonts/DejaVuSans.ttf')
BOLD = str(ROOT / 'assets/fonts/DejaVuSans-Bold.ttf')
SERIF = str(ROOT / 'assets/fonts/DejaVuSerif.ttf')
FONTS = {
    'title': ImageFont.truetype(SERIF, 30),
    'small': ImageFont.truetype(BOLD, 12),
    'name': ImageFont.truetype(BOLD, 15),
    'caption': ImageFont.truetype(BOLD, 29),
    'intro': ImageFont.truetype(SERIF, 25),
    'outro': ImageFont.truetype(SANS, 20),
}


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def centered(draw, text, y, font, fill, cx=W / 2):
    draw.text((cx - draw.textlength(text, font=font) / 2, y), text,
              font=font, fill=fill)


def read_wav(path):
    with wave.open(str(path), 'rb') as wav:
        assert wav.getnchannels() == 1 and wav.getsampwidth() == 2
        assert wav.getframerate() == SR
        return np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2').astype(np.float32) / 32768


def write_wav(path, data):
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        wav.writeframes((np.clip(data, -.99, .99) * 32767).astype('<i2').tobytes())


def srt_time(t):
    ms = round(t * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'


class CafeMovie:
    def __init__(self):
        self.config = json.loads((ROOT / 'episode.json').read_text())
        meta = json.loads((ROOT / self.config.get('dialogue_metadata', 'audio/dialogue.json')).read_text())
        self.lines = meta['lines']
        at = self.config['intro_seconds']
        for line in self.lines:
            # Relative paths make the complete source bundle portable.
            line['file'] = f"audio/line_{line['index']:02}.wav"
            line['audio'] = read_wav(ROOT / line['file'])
            line['duration'] = len(line['audio']) / SR
            line['start'] = at
            line['end'] = at + line['duration']
            at = line['end'] + self.config['gap_seconds']
        self.end_speech = self.lines[-1]['end']
        self.duration = math.ceil((self.end_speech + self.config['outro_seconds']) * FPS) / FPS
        self.bg = Image.open(ROOT / 'assets/cafe.png').convert('RGBA').resize((W, H), Image.Resampling.LANCZOS)
        self.sprites = {}
        for speaker in ['Maya', 'Leo']:
            sheet = Image.open(ROOT / f'assets/{speaker.lower()}.png').convert('RGBA')
            alpha = np.asarray(sheet.getchannel('A'))
            if np.mean(alpha < 5) < .15:
                raise RuntimeError(f'{speaker} sheet is not sufficiently transparent; regenerate the asset.')
            frames = []
            for index in range(8):
                col, row = index % 4, index // 4
                cell = sheet.crop((round(col * sheet.width / 4), round(row * sheet.height / 2),
                                   round((col + 1) * sheet.width / 4), round((row + 1) * sheet.height / 2)))
                # Every frame keeps the same canvas; no pose-dependent bbox resizing.
                frames.append(cell.resize((444, 444), Image.Resampling.LANCZOS))
            self.sprites[speaker] = frames
        self.export_audio_and_timing()

    def export_audio_and_timing(self):
        n = round(self.duration * SR)
        signal = np.zeros(n, np.float32)
        for line in self.lines:
            start = round(line['start'] * SR)
            signal[start:start + len(line['audio'])] += line['audio'] * .77
        # Very quiet original room tone and brief original bell-like notes.
        rng = np.random.default_rng(72)
        room = rng.normal(0, .001, n)
        room = np.convolve(room, np.ones(9) / 9, mode='same')
        signal += room.astype(np.float32)
        for start, hz in [(0.12, 523.25), (0.30, 659.25), (0.48, 783.99),
                          (self.end_speech + .32, 659.25), (self.end_speech + .55, 523.25)]:
            t = np.arange(int(.6 * SR)) / SR
            tone = .012 * np.sin(2 * np.pi * hz * t) * np.exp(-6 * t)
            tone += .003 * np.sin(2 * np.pi * hz * 2 * t) * np.exp(-10 * t)
            offset = int(start * SR)
            length = min(len(tone), n - offset)
            signal[offset:offset + length] += tone[:length]
        fade = int(.2 * SR)
        signal[-fade:] *= np.linspace(1, 0, fade)
        self.audio_file = ROOT / 'audio/dialogue_timeline.wav'
        write_wav(self.audio_file, signal)
        manifest = {
            'duration': self.duration, 'width': W, 'height': H, 'fps': FPS,
            'animation': 'Original illustration sprites; speech-driven limited 2D animation',
            'word_timing': 'Piper model phoneme-duration alignment grouped by word; not manually corrected',
            'lines': [{k: v for k, v in line.items() if k != 'audio'} for line in self.lines],
        }
        (ROOT / 'timeline.json').write_text(json.dumps(manifest, indent=2))
        captions = []
        for i, line in enumerate(self.lines, 1):
            captions.append(f"{i}\n{srt_time(line['start'])} --> {srt_time(line['end'])}\n{line['speaker']}: {line['text']}\n")
        (ROOT / 'captions.srt').write_text('\n'.join(captions))

    def current_line(self, t):
        for line in self.lines:
            if line['start'] <= t < line['end']:
                return line
        return None

    def mouth(self, line, t):
        if line is None:
            return 0
        dt = round((t - line['start']) * 12) / 12
        j = int(max(0, dt) * SR)
        sample = line['audio'][max(0, j - 220):j + 441]
        amp = float(np.sqrt(np.mean(sample ** 2))) if len(sample) else 0
        if amp < .018:
            return 0
        for ph in line.get('phonemes', []):
            if ph['start'] <= dt < ph['end']:
                char = ph['phoneme']
                if char in ('m', 'b', 'p', ' ', '.', ',', '!', '?'):
                    return 0
                if char in ('a', 'ɑ', 'ɒ', 'ɔ', 'ʌ', 'ɛ', 'ɐ'):
                    return 2
                return 1
        return 2 if amp > .13 else 1

    def character(self, canvas, speaker, t, active):
        is_maya = speaker == 'Maya'
        line = active if active and active['speaker'] == speaker else None
        state = self.mouth(line, t)
        phase = .7 if is_maya else 2.1
        # Calm blinks, placed in listening beats and occasional speech pauses.
        blink_centers = [0.67, 4.67, 8.78, 12.95] if is_maya else [1.75, 5.15, 8.03, 13.20]
        blinking = any(abs(t - c) < .085 for c in blink_centers)
        if blinking and state == 0:
            state = 3
        gesture = 0.0
        for speaking in self.lines:
            if speaking['speaker'] != speaker:
                continue
            # One clear hand gesture per speaking turn, with a short transition.
            dt = t - speaking['start']
            g = smooth((dt - .18) / .28) * (1 - smooth((dt - speaking['duration'] + .34) / .28))
            gesture = max(gesture, g)
        neutral, raised = self.sprites[speaker][state], self.sprites[speaker][state + 4]
        sprite = neutral if gesture <= 0 else raised if gesture >= 1 else Image.blend(neutral, raised, gesture)
        # Torso breathing and tiny conversational nod, anchored at the counter.
        breath = 1.7 * math.sin(t * 2.0 + phase)
        nod = (2.3 * math.sin(t * 4.1 + phase)) if line else .8 * math.sin(t * 2.3 + phase)
        x = 155 if is_maya else 692
        y = 110 + int(breath + nod)
        canvas.alpha_composite(sprite, (x, y))

    def frame(self, t):
        active = self.current_line(t)
        scene = self.bg.copy()
        self.character(scene, 'Maya', t, active)
        self.character(scene, 'Leo', t, active)
        # The existing counter is the foreground layer; it hides torso cut edges.
        scene.alpha_composite(self.bg.crop((0, 548, W, H)), (0, 548))
        # Gentle continuous camera push-in, applied to the illustration only.
        zoom = 1 + .016 * smooth(t / self.duration)
        if zoom > 1:
            sw, sh = round(W / zoom), round(H / zoom)
            left, top = (W - sw) // 2, int((H - sh) * .40)
            scene = scene.crop((left, top, left + sw, top + sh)).resize((W, H), Image.Resampling.BICUBIC)
        layer = Image.new('RGBA', (W, H))
        d = ImageDraw.Draw(layer)
        # Quiet, editorial title treatment.
        d.rounded_rectangle((34, 27, 456, 112), radius=15, fill=(24, 42, 37, 218))
        d.text((53, 41), 'EVERYDAY ENGLISH  /  EPISODE 01', font=FONTS['small'], fill=(192, 213, 180, 255))
        d.text((51, 63), self.config['title'], font=FONTS['title'], fill=(255, 238, 201, 255))
        d.rounded_rectangle((1110, 35, 1245, 67), radius=16, fill=(255, 241, 209, 216))
        centered(d, 'AT THE CAFÉ', 44, FONTS['small'], (47, 65, 53, 255), 1177)
        for name, cx in [('Maya', 374), ('Leo', 911)]:
            speaking = active and active['speaker'] == name
            d.rounded_rectangle((cx - 55, 554, cx + 55, 585), radius=15,
                                fill=(25, 61, 48, 240) if speaking else (34, 43, 35, 185))
            if speaking:
                d.ellipse((cx - 40, 566, cx - 34, 572), fill=(251, 215, 99))
            centered(d, name.upper(), 562, FONTS['small'], (255, 238, 206, 255), cx + (4 if speaking else 0))
        # Captions stay legible over the dark wooden counter.
        shown = active
        if shown is None:
            for line in self.lines:
                if line['end'] <= t < line['end'] + .22:
                    shown = line
        if shown:
            d.rounded_rectangle((98, 605, 1182, 681), radius=20, fill=(12, 28, 23, 233))
            words = shown['words']
            widths = [d.textlength(w['word'], font=FONTS['caption']) for w in words]
            space = d.textlength(' ', font=FONTS['caption'])
            total = sum(widths) + space * (len(words) - 1)
            x = (W - total) / 2
            for word, width in zip(words, widths):
                dt = t - shown['start']
                highlight = word['start'] <= dt <= word['end']
                if highlight:
                    d.rounded_rectangle((x - 5, 621, x + width + 5, 663), radius=9,
                                        fill=(255, 214, 83, 255))
                d.text((x, 625), word['word'], font=FONTS['caption'],
                       fill=(30, 44, 28, 255) if highlight else (161, 227, 139, 255))
                x += width + space
        elif t < self.lines[0]['start']:
            d.rounded_rectangle((305, 610, 975, 674), radius=18, fill=(18, 39, 31, 225))
            centered(d, 'A friendly conversation at the café', 627, FONTS['intro'], (244, 229, 194, 255))
        elif t > self.end_speech + .28:
            opacity = int(230 * smooth((t - self.end_speech - .28) / .3))
            d.rounded_rectangle((315, 609, 965, 676), radius=18, fill=(18, 39, 31, opacity))
            centered(d, 'Small moments. Real conversation.', 629, FONTS['outro'], (246, 232, 201, opacity))
        scene = Image.alpha_composite(scene, layer).convert('RGB')
        # A short fade from/to deep warm charcoal, never cutting off dialogue.
        visibility = smooth(t / .35) * (1 - smooth((t - self.duration + .4) / .4))
        if visibility < 1:
            scene = Image.blend(Image.new('RGB', (W, H), (15, 24, 20)), scene, visibility)
        return scene

    def render(self, output):
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        cmd = ['ffmpeg', '-y', '-v', 'warning', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
               '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', str(self.audio_file),
               '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
               '-threads', '2', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
               '-movflags', '+faststart', '-shortest', str(output)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        try:
            for frame in range(round(self.duration * FPS)):
                proc.stdin.write(self.frame(frame / FPS).tobytes())
                if frame % (FPS * 3) == 0:
                    print(f'Rendered {frame / FPS:.0f}/{self.duration:.1f} seconds', flush=True)
            proc.stdin.close()
            if proc.wait() != 0:
                raise RuntimeError('FFmpeg failed')
        finally:
            if proc.poll() is None:
                proc.terminate()
        samples = [0.7, 1.6, 2.5, 4.9, 6.3, 8.2, 10.9, 13.1]
        sheet = Image.new('RGB', (W, 420), '#192c24')
        for i, t in enumerate(samples):
            shot = self.frame(min(t, self.duration - .6)).resize((320, 180), Image.Resampling.LANCZOS)
            sheet.paste(shot, ((i % 4) * 320, (i // 4) * 210))
            draw = ImageDraw.Draw(sheet)
            draw.text(((i % 4) * 320 + 12, (i // 4) * 210 + 187), f'{t:.1f} seconds',
                      font=FONTS['name'], fill='#fff0cb')
        sheet.save(ROOT / 'contact-sheet.jpg', quality=94)
        print(json.dumps({'output': str(output), 'seconds': self.duration, 'frames': round(self.duration * FPS)}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default=str(ROOT / 'cafe-conversation.mp4'))
    parser.add_argument('--preview', type=float)
    args = parser.parse_args()
    movie = CafeMovie()
    if args.preview is not None:
        movie.frame(args.preview).save(ROOT / 'preview.png')
        print(ROOT / 'preview.png')
    else:
        movie.render(args.output)


if __name__ == '__main__':
    main()
