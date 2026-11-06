"""Report Kaggle hardware without reading credentials or downloading models."""
import json
import platform
from pathlib import Path
import shutil
import subprocess

output = Path('/kaggle/working') if Path('/kaggle/working').is_dir() else Path.cwd()
report = {'python': platform.python_version(), 'preflight_ok': False}
disk = shutil.disk_usage(output)
report['storage'] = {'path': str(output), 'free_gib': round(disk.free / 2**30, 2)}
report['memory'] = {}
meminfo = Path('/proc/meminfo')
if meminfo.exists():
    for line in meminfo.read_text().splitlines():
        if line.startswith(('MemTotal:', 'MemAvailable:')):
            key, value = line.split(':', 1)
            report['memory'][key + '_kib'] = int(value.strip().split()[0])
limit = Path('/sys/fs/cgroup/memory.max')
if limit.exists():
    report['memory']['cgroup_limit_bytes_or_max'] = limit.read_text().strip()
report['ffmpeg'] = {'available': bool(shutil.which('ffmpeg'))}
if report['ffmpeg']['available']:
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        report['ffmpeg']['version'] = result.stdout.splitlines()[0]
    except Exception as exc:
        report['ffmpeg']['error'] = str(exc)
try:
    import torch
    report['torch'] = {'version': torch.__version__, 'cuda_available': torch.cuda.is_available(), 'devices': []}
    for i in range(torch.cuda.device_count()):
        prop = torch.cuda.get_device_properties(i)
        report['torch']['devices'].append({'index': i, 'name': prop.name, 'vram_gib': round(prop.total_memory / 2**30, 2)})
    if torch.cuda.is_available():
        tensor = torch.ones((32, 32), device='cuda:0')
        value = float((tensor @ tensor).sum().item())
        report['gpu_allocation_test'] = {'ok': value == 32768.0, 'sum': value}
        report['preflight_ok'] = report['gpu_allocation_test']['ok']
        del tensor
    else:
        report['gpu_allocation_test'] = {'ok': False, 'error': 'No CUDA device visible.'}
except Exception as exc:
    report['gpu_allocation_test'] = {'ok': False, 'error': str(exc)}
path = output / 'gpu_preflight.json'
path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
if not report['preflight_ok']:
    raise RuntimeError('GPU preflight did not pass; inspect gpu_preflight.json.')
