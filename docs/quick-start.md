# Quick Start Guide

Get up and running with PyScheduler in under 5 minutes!

## 30-Second Start

```python
from pyscheduler import PyScheduler, task

@task(10)  # Every 10 seconds
def hello_world():
    print("Hello from PyScheduler!")

scheduler = PyScheduler()
scheduler.start()
```

**That's it!** 🎉 Your first scheduled task is running.

## 2-Minute Tour

### Basic Task Types

```python
from pyscheduler import task, daily, startup, shutdown

# Interval-based
@task(30)  # Every 30 seconds
def health_check():
    print("System is healthy")

# CRON expressions
@task(cron="0 9 * * 1-5")  # 9 AM on weekdays
def morning_report():
    print("Daily report generated")

# Daily at specific time
@daily("14:30")  # Every day at 2:30 PM
def afternoon_backup():
    print("Backup completed")

# Lifecycle tasks
@startup()
def initialize():
    print("Application starting...")

@shutdown()
def cleanup():
    print("Application shutting down...")
```

### Context Manager (Recommended)

```python
from pyscheduler import PyScheduler

with PyScheduler() as scheduler:
    # Add tasks
    scheduler.add_task(
        func=lambda: print("Dynamic task!"),
        interval=15,
        name="dynamic_task"
    )
    
    # Run forever (Ctrl+C to stop)
    scheduler.run_forever()
```

## 5-Minute Deep Dive

### Advanced Configuration

```python
from pyscheduler import PyScheduler
from pyscheduler.config import Priority, RetryConfig

scheduler = PyScheduler(
    log_level="INFO",
    max_workers=5,
    timezone="UTC"
)

# Task with advanced options
scheduler.add_task(
    func=important_task,
    interval=60,
    name="critical_task",
    priority=Priority.HIGH,
    timeout=30,
    retry_config=RetryConfig(
        max_attempts=3,
        backoff_factor=2.0,
        max_delay=120
    ),
    tags={"critical", "monitoring"}
)
```

### Async Tasks

```python
import asyncio
from pyscheduler import task

@task(45)
async def async_task():
    # Native async support
    await asyncio.sleep(1)
    print("Async task completed")
    return "success"
```

### YAML Configuration

Create `scheduler_config.yaml`:
```yaml
global_settings:
  timezone: "UTC"
  log_level: "INFO"
  max_workers: 10

tasks:
  - name: "backup_task"
    module: "myapp.tasks"
    function: "backup_database"
    schedule:
      type: "cron"
      value: "0 2 * * *"  # 2 AM daily
    priority: "HIGH"
    timeout: 3600
```

Load configuration:
```python
scheduler = PyScheduler(config_file="scheduler_config.yaml")
scheduler.start()
```

## Real-World Examples

### Web Application Monitoring

```python
from pyscheduler import PyScheduler, task
import requests

@task(300)  # Every 5 minutes
def monitor_website():
    try:
        response = requests.get("https://mywebsite.com/health")
        if response.status_code == 200:
            print("✅ Website is up")
        else:
            print(f"⚠️ Website returned {response.status_code}")
    except Exception as e:
        print(f"❌ Website is down: {e}")

@task(cron="0 */6 * * *")  # Every 6 hours
def detailed_health_check():
    # Comprehensive health check
    pass

scheduler = PyScheduler()
scheduler.start()
```

### Data Processing Pipeline

```python
from pyscheduler import task, daily
import pandas as pd

@task(3600)  # Every hour
def process_new_data():
    # Process incoming data
    df = pd.read_csv("new_data.csv")
    # Process and save
    df.to_csv("processed_data.csv")
    print(f"Processed {len(df)} records")

@daily("02:00")  # Daily at 2 AM
def generate_daily_report():
    # Generate comprehensive daily report
    print("Daily report generated")

@task(cron="0 0 1 * *")  # First day of month
def monthly_archive():
    # Archive old data
    print("Monthly archive completed")
```

### Microservice Background Tasks

```python
from pyscheduler import PyScheduler, task
import asyncio
import aiohttp

@task(30)
async def sync_user_data():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.users.com/sync") as response:
            data = await response.json()
            print(f"Synced {len(data)} users")

@task(600)  # Every 10 minutes
def cleanup_temp_files():
    import os
    import glob
    
    temp_files = glob.glob("/tmp/app_*")
    for file in temp_files:
        os.remove(file)
    print(f"Cleaned up {len(temp_files)} temp files")

# Production setup
scheduler = PyScheduler(
    log_level="INFO",
    max_workers=3
)
scheduler.start()
```

## Next Steps

- 📖 Read the [Complete API Reference](api-reference.md)
- 🎯 Explore [Detailed Examples](examples.md)
- ⚙️ Learn about [Configuration Options](configuration.md)
- 🛠️ Check [Troubleshooting Guide](troubleshooting.md)

## Common Patterns

### Graceful Shutdown

```python
import signal
import sys

def signal_handler(sig, frame):
    print("Gracefully shutting down...")
    scheduler.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

scheduler.run_forever()
```

### Task Dependencies

```python
# Simple dependency pattern
@task(3600)
def data_extraction():
    # Extract data
    return extract_data()

@task(3605)  # 5 seconds after extraction
def data_processing():
    # Process extracted data
    return process_data()
```

### Error Notifications

```python
from pyscheduler.config import RetryConfig

def notify_on_error(task_name, error):
    # Send notification (email, Slack, etc.)
    print(f"Task {task_name} failed: {error}")

@task(
    interval=300,
    retry_config=RetryConfig(max_attempts=3),
    on_error=notify_on_error
)
def critical_task():
    # Critical business logic
    pass
```