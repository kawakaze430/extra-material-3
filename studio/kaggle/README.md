# Kaggle GPU preflight

This folder prepares a small **private Kaggle notebook** that reports the GPU,
memory, storage, PyTorch, and FFmpeg available to your account. It does not
download animation models or generate a video. A successful preflight establishes
hardware visibility only; the animation model still needs a separate installation
and inference test.

Codex can submit and monitor the job, then download its report. The GPU runs on
Kaggle; it does not become a local CUDA device inside Codex Cloud.

## Authentication and installation

Use Python 3.11+ and an isolated environment for the official CLI:

```bash
python -m venv work/kaggle-cli-env
work/kaggle-cli-env/bin/python -m pip install 'kaggle>=2.2.5' six
```

`six` is included because the clean Kaggle 2.2.5 installation in this session
failed to import until that dependency was installed.

Generate an API token in [Kaggle account settings](https://www.kaggle.com/settings/api)
and configure **KAGGLE_API_TOKEN** through the cloud environment's secret settings.
Do not paste the token into chat or put it in a notebook, command-line argument,
source file, ZIP, or version control. This launcher passes the existing environment
to the CLI and never writes credential values. It deliberately requires the token
variable for remote commands; no browser login is started automatically.

Your Kaggle account must have GPU access and available quota. Account verification
may be required. Check current quota using the installed CLI's `kaggle quota` command.
Having an API token does not itself establish GPU eligibility.

## Commands

Run these from the parent folder containing `kaggle/`. Replace `YOUR_USERNAME` with
your real Kaggle username. The `--kaggle-bin` option is unnecessary if `kaggle` is on
PATH; otherwise supply the full path to the executable in your environment.

Prepare notebook and metadata locally, without an API call:

```bash
python kaggle/launch.py --username YOUR_USERNAME prepare
```

Submit and run the preflight. **This consumes Kaggle GPU quota.** The default timeout
is five minutes and the notebook's internet access is disabled. No model weights or
paid external services are used.

```bash
python kaggle/launch.py --username YOUR_USERNAME \
  --kaggle-bin /absolute/path/to/kaggle submit
```

Read the latest run's status, then download the report after completion:

```bash
python kaggle/launch.py --username YOUR_USERNAME status
python kaggle/launch.py --username YOUR_USERNAME download --out work/kaggle-results
```

Add the same `--kaggle-bin` option to these commands if needed. The report is named
`gpu_preflight.json`. Each submission updates the private notebook
`YOUR_USERNAME/cafe-animation-gpu-preflight`; the launcher does not create a public
notebook. If that slug already belongs to your account, inspect it before submitting,
because Kaggle pushes update existing notebooks with the same slug.

`--accelerator` is an option on `submit`, for example `submit --accelerator NvidiaL4`.
Only request an accelerator your account can use. Kaggle's `NvidiaTeslaT4` identifier
currently means T4 ×2. The report lists each device separately: two devices do not
automatically combine their memory into one larger GPU. Accelerator availability and
weekly quota are account dependent; no particular GPU or runtime allocation is promised.

## Reading the report

- `torch.cuda_available` and `torch.devices` report actual device visibility and VRAM.
- `gpu_allocation_test` performs a small tensor operation on the first GPU and records
  success or an error; it does not load any model.
- `memory` includes system memory and the cgroup limit where reported by the runtime.
- `storage` reports free disk space at the output location.
- `ffmpeg` records availability and version.
- `preflight_ok` means a GPU tensor operation succeeded, not that an animation model fits.

Errors are recorded in the JSON. The notebook then raises an error if its basic GPU
test fails. Kaggle can therefore mark the run as failed while still retaining the
diagnostic output file.

## Official references

- [CLI installation and authentication](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md)
- [Notebook push, status, output, and accelerators](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md)
- [Kernel metadata](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels_metadata.md)
- [CLI changelog](https://github.com/Kaggle/kaggle-cli/blob/main/CHANGELOG.md)
- [Kaggle notebook documentation](https://www.kaggle.com/docs/notebooks)
