#!/usr/bin/env python3
"""Download the two café voices directly from their official Piper voice repository.

Uses Python HTTPS with certificate verification and inherited proxy settings.
Existing verified files are reused; each new download is checked before promotion.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US"
FILES = [
    ("ljspeech", "en_US-ljspeech-medium.onnx", "en_US-ljspeech-medium.onnx", "6f52a751e2349abe7a76735eb09dc1875298c77ea2342ffd2fef79ff81b87f22"),
    ("ljspeech", "en_US-ljspeech-medium.onnx.json", "en_US-ljspeech-medium.onnx.json", "141d612cc0a95ed7efc1ca936b845c2364967f2e9217c5dbfcf69fc4d6c65860"),
    ("ljspeech", "MODEL_CARD", "ljspeech_MODEL_CARD.txt", "fbee1529c89d36b3fe76d7e9f3f832dce17f44900a52d76a9bda735654766b4d"),
    ("john", "en_US-john-medium.onnx", "en_US-john-medium.onnx", "789c6c875726e627ddee93d51d8727859abe9c091c3d141591f4b83c2072e988"),
    ("john", "en_US-john-medium.onnx.json", "en_US-john-medium.onnx.json", "af60f177b6b550f3d7a302720c0fb89e7f94a82b5dca464775ef63b1c69ba09a"),
    ("john", "MODEL_CARD", "john_MODEL_CARD.txt", "a056da65cd70dcbda96fc3420fe8d3442dbf3c8b75f49cdf800a715b42e299d1"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def download(destination: Path, voice: str, remote_name: str, expected_hash: str):
    if destination.is_file() and sha256(destination) == expected_hash:
        print(f"Verified existing {destination.name}")
        return
    url = f"{BASE_URL}/{voice}/medium/{remote_name}"
    request = Request(url, headers={"User-Agent": "cafe-pilot-voice-setup/1.0"})
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".part", delete=False) as out:
            temporary = Path(out.name)
            with urlopen(request, timeout=60) as response:
                while chunk := response.read(1024 * 1024):
                    out.write(chunk)
        actual_hash = sha256(temporary)
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"Checksum mismatch for {destination.name}; the upstream file may have changed. "
                "The existing local file was preserved. Review the upstream revision before updating the expected hash."
            )
        temporary.replace(destination)
        print(f"Downloaded and verified {destination.name}")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--voices-dir", type=Path, default=ROOT / "voices")
    args = parser.parse_args()
    args.voices_dir.mkdir(parents=True, exist_ok=True)
    for voice, remote_name, local_name, expected_hash in FILES:
        download(args.voices_dir / local_name, voice, remote_name, expected_hash)


if __name__ == "__main__":
    main()
