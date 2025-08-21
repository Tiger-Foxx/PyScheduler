# Configuration Guide

Complete guide to configuring PyScheduler.

## Basic Configuration

### Programmatic Configuration
```python
from pyscheduler import PyScheduler
from pyscheduler.config import Priority, RetryConfig

scheduler = PyScheduler(
    timezone="UTC",           # Default timezone
    log_level="INFO",         # DEBUG, INFO, WARNING, ERROR
    max_workers=10,           # Max concurrent tasks
    log_file="scheduler.log"  # Optional log file
)
```

### YAML Configuration
```yaml
# scheduler_config.yaml
global_settings:
  timezone: "UTC"
  log_level: "INFO"
  max_workers: 10
  log_file: "scheduler.log"

tasks:
  - name: "example_task"
    module: "myapp.tasks"
    function: "my_function"
    schedule:
      type: "interval"        # interval, cron, daily
      value: 60               # 60 seconds
    enabled: true
    priority: "NORMAL"        # CRITICAL, HIGH, NORMAL, LOW, IDLE
    timeout: 30               # Optional timeout in seconds
    retry_policy:
      max_attempts: 3
      backoff_factor: 2.0
      max_delay: 300
    tags: ["backup", "daily"]
    metadata:
      owner: "admin"
      description: "Daily backup task"
```

Load YAML config:
```python
scheduler = PyScheduler(config_file="scheduler_config.yaml")
```

## Task Configuration

### Schedule Types

**Interval**: Fixed time intervals
```python
@task(interval=60)          # Every 60 seconds
@task(30)                   # Shorthand for interval=30
```

**CRON**: CRON expressions
```python
@task(cron="0 9 * * 1-5")   # 9 AM weekdays
@task(cron="*/15 * * * *")  # Every 15 minutes
```

**Daily**: Daily at specific time
```python
@daily("09:00")             # Every day at 9 AM
@daily("23:30")             # Every day at 11:30 PM
```

### Task Options

```python
scheduler.add_task(
    func=my_function,
    interval=60,
    name="my_task",              # Unique task name
    priority=Priority.HIGH,      # Task priority
    timeout=30,                  # Execution timeout
    enabled=True,                # Enable/disable task
    max_runs=100,               # Limit executions
    tags={"backup", "critical"}, # Task tags
    retry_config=RetryConfig(    # Retry configuration
        max_attempts=3,
        backoff_factor=2.0,
        max_delay=300
    )
)
```

## Retry Configuration

```python
from pyscheduler.config import RetryConfig

# Basic retry
retry_config = RetryConfig(max_attempts=3)

# Advanced retry with exponential backoff
retry_config = RetryConfig(
    max_attempts=5,           # Max retry attempts
    backoff_factor=2.0,       # Multiply delay by this factor
    max_delay=300,            # Maximum delay between retries
    retry_on=(ConnectionError, TimeoutError)  # Which exceptions to retry
)
```

## Priority Levels

```python
from pyscheduler.config import Priority

Priority.CRITICAL  # Executed first
Priority.HIGH      # High priority  
Priority.NORMAL    # Default priority
Priority.LOW       # Low priority
Priority.IDLE      # Executed when nothing else
```

## Timezone Support

```python
# Global timezone
scheduler = PyScheduler(timezone="Europe/Paris")

# Task-specific timezone (if supported)
@task(cron="0 9 * * *", timezone="America/New_York")
def us_morning_task():
    pass
```

## Logging Configuration

```python
scheduler = PyScheduler(
    log_level="DEBUG",              # DEBUG, INFO, WARNING, ERROR
    log_file="/var/log/scheduler.log",  # Optional log file
    log_format="%(asctime)s - %(levelname)s - %(message)s"
)
```

## Environment Variables

Set configuration via environment variables:

```bash
export PYSCHEDULER_LOG_LEVEL=DEBUG
export PYSCHEDULER_MAX_WORKERS=20
export PYSCHEDULER_TIMEZONE=UTC
```

```python
import os
scheduler = PyScheduler(
    log_level=os.getenv("PYSCHEDULER_LOG_LEVEL", "INFO"),
    max_workers=int(os.getenv("PYSCHEDULER_MAX_WORKERS", "10"))
)
```

## Production Configuration Example

```yaml
# production_config.yaml
global_settings:
  timezone: "UTC"
  log_level: "INFO"
  max_workers: 20
  log_file: "/var/log/pyscheduler/scheduler.log"
  persistence_file: "/var/lib/pyscheduler/state.json"

tasks:
  - name: "critical_health_check"
    module: "monitoring.tasks"
    function: "health_check"
    schedule:
      type: "interval"
      value: 60
    priority: "CRITICAL"
    timeout: 30
    retry_policy:
      max_attempts: 5
      backoff_factor: 2.0
      max_delay: 120

  - name: "daily_backup"
    module: "backup.tasks"
    function: "full_backup"
    schedule:
      type: "cron"
      value: "0 2 * * *"
    priority: "HIGH"
    timeout: 7200  # 2 hours
    retry_policy:
      max_attempts: 2
      backoff_factor: 1.5
```


