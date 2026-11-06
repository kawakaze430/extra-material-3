#!/usr/bin/env python3
"""Prepare or run a private Kaggle GPU preflight, without embedding credentials."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


HERE = Path(__file__).resolve().parent
SLUG = "cafe-animation-gpu-preflight"


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", help="Your Kaggle username; required for every command")
    parser.add_argument(
        "--kaggle-bin", default=shutil.which("kaggle") or "kaggle",
        help="Path to the installed Kaggle CLI executable",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="Create the private job locally; no API call")
    prepare.add_argument("--out", type=Path, help="Local directory for notebook and metadata")
    submit = commands.add_parser("submit", help="Upload and RUN the GPU preflight (uses quota)")
    submit.add_argument("--out", type=Path, help="Local directory for notebook and metadata")
    submit.add_argument("--accelerator", default="NvidiaTeslaT4", help="Kaggle accelerator ID")
    submit.add_argument("--timeout", type=int, default=300, help="Maximum job runtime in seconds")
    commands.add_parser("status", help="Read the status of the latest preflight run")
    download = commands.add_parser("download", help="Download the preflight JSON report")
    download.add_argument("--out", type=Path, default=HERE / "results")
    args = parser.parse_args()
    if not args.username or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,49}", args.username):
        parser.error("provide --username with your Kaggle username (not an email address or URL)")
    if args.command == "submit" and args.timeout <= 0:
        parser.error("--timeout must be positive")
    return args


def prepare_job(args: argparse.Namespace) -> Path:
    directory = (args.out or HERE / ".prepared" / args.username).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((HERE / "kernel-metadata.template.json").read_text())
    metadata["id"] = f"{args.username}/{SLUG}"
    metadata["machine_shape"] = getattr(args, "accelerator", "NvidiaTeslaT4")
    (directory / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    shutil.copyfile(HERE / "gpu_preflight.ipynb", directory / "gpu_preflight.ipynb")
    print(f"Private job prepared: {directory}")
    return directory


def cli(args: argparse.Namespace, command: list[str]) -> int:
    if not os.environ.get("KAGGLE_API_TOKEN", "").strip():
        print(
            "KAGGLE_API_TOKEN is not configured. Add it through the cloud environment's "
            "secret settings; do not put it in this repository or notebook. "
            "The prepare command works without authentication.",
            file=sys.stderr,
        )
        return 2
    env = os.environ.copy()
    # The CLI creates its configuration directory on import. Keep that directory
    # within this project rather than writing into the user's home directory.
    env["KAGGLE_CONFIG_DIR"] = str(HERE / ".kaggle-config")
    try:
        return subprocess.run([args.kaggle_bin, *command], env=env, check=False).returncode
    except FileNotFoundError:
        print("Kaggle CLI is missing. Install it, or supply --kaggle-bin PATH.", file=sys.stderr)
        return 2


def main() -> int:
    args = arguments()
    reference = f"{args.username}/{SLUG}"
    if args.command == "prepare":
        prepare_job(args)
        return 0
    if args.command == "submit":
        directory = prepare_job(args)
        print(f"Submitting private preflight {reference}; this consumes Kaggle GPU quota.")
        return cli(args, [
            "kernels", "push", "-p", str(directory), "--accelerator", args.accelerator,
            "--timeout", str(args.timeout),
        ])
    if args.command == "status":
        return cli(args, ["kernels", "status", reference])
    args.out.mkdir(parents=True, exist_ok=True)
    return cli(args, [
        "kernels", "output", reference, "-p", str(args.out.resolve()),
        "--file-pattern", r"(^|/)gpu_preflight\.json$",
    ])


if __name__ == "__main__":
    raise SystemExit(main())
