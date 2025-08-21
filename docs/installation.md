# Installation Guide

## Quick Installation

### Standard Installation (Recommended)
```bash
pip install pyscheduler[full]
```

This installs PyScheduler with all optional dependencies for the best experience.

### Minimal Installation
```bash
pip install pyscheduler
```

This installs only the core PyScheduler without optional dependencies.

## Optional Dependencies

PyScheduler works without any external dependencies, but optional packages enhance functionality:

### YAML Configuration Support
```bash
pip install pyscheduler[yaml]
# OR manually
pip install pyyaml>=5.1.0
```

### Timezone Support
```bash
pip install pyscheduler[timezone]
# OR manually
pip install pytz>=2021.1
```

### CRON Expression Support
```bash
pip install pyscheduler[cron]
# OR manually
pip install croniter>=1.0.0
```

### All Optional Dependencies
```bash
pip install pyscheduler[full]
```

## Development Installation

### From Source
```bash
git clone https://github.com/Tiger-Foxx/PyScheduler.git
cd PyScheduler
pip install -e .[dev]
```

### Development Dependencies
```bash
pip install pyscheduler[dev]
```

Includes: pytest, pytest-cov, black, flake8, mypy

## Requirements

- **Python**: 3.7 or higher
- **Operating System**: Windows, macOS, Linux
- **Memory**: Minimal (< 20MB for typical usage)

## Verification

Test your installation:

```python
from pyscheduler import PyScheduler, task

@task(5)
def test_task():
    print("PyScheduler is working!")

scheduler = PyScheduler()
scheduler.start()
# You should see the message every 5 seconds
```

## Docker Installation

```dockerfile
FROM python:3.9-slim

RUN pip install pyscheduler[full]

COPY your_tasks.py /app/
WORKDIR /app

CMD ["python", "your_tasks.py"]
```

## Conda Installation

```bash
# Coming soon - not yet available on conda-forge
# For now, use pip within conda environment
conda create -n pyscheduler python=3.9
conda activate pyscheduler
pip install pyscheduler[full]
```

## Troubleshooting Installation

### Common Issues

**ImportError: No module named 'pyscheduler'**
```bash
pip install --upgrade pip
pip install pyscheduler[full]
```

**Permission Denied (Linux/macOS)**
```bash
pip install --user pyscheduler[full]
```

**Dependencies Conflict**
```bash
pip install pyscheduler --no-deps
# Then install dependencies manually
```

### Virtual Environment (Recommended)

```bash
python -m venv pyscheduler_env
source pyscheduler_env/bin/activate  # Linux/macOS
# OR
pyscheduler_env\Scripts\activate     # Windows

pip install pyscheduler[full]
```