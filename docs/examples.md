# Examples Guide

Complete examples demonstrating PyScheduler features.

## Running Examples

After installation, run examples directly:

```bash
python -c "from pyscheduler.examples import basic_usage; basic_usage.main()"
python -c "from pyscheduler.examples import advanced_usage; advanced_usage.main()"
```

## Basic Usage Examples

### Simple Interval Tasks
```python
from pyscheduler import task, PyScheduler

@task(10)  # Every 10 seconds
def simple_task():
    print("Simple task running")

scheduler = PyScheduler()
scheduler.start()
```

### CRON Schedule Tasks
```python
@task(cron="0 9 * * 1-5")  # 9 AM weekdays
def weekday_report():
    print("Weekday report generated")

@task(cron="0 2 * * 0")    # 2 AM Sundays
def weekly_backup():
    print("Weekly backup completed")
```

### Daily Tasks
```python
from pyscheduler import daily

@daily("06:00")
def morning_task():
    print("Good morning!")

@daily("22:00") 
def evening_task():
    print("Good night!")
```

## Advanced Examples

### Retry and Error Handling
```python
from pyscheduler.config import RetryConfig

@task(
    interval=60,
    retry_config=RetryConfig(max_attempts=3, backoff_factor=2.0),
    timeout=30
)
def unreliable_task():
    # Task that might fail
    import random
    if random.random() < 0.3:
        raise Exception("Random failure")
    return "success"
```

### Async Tasks
```python
import asyncio
import aiohttp

@task(120)
async def async_web_task():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com") as response:
            data = await response.json()
            return data
```

### Priority Tasks
```python
from pyscheduler.config import Priority

@task(interval=30, priority=Priority.CRITICAL)
def critical_health_check():
    return monitor_critical_systems()

@task(interval=300, priority=Priority.LOW)
def cleanup_task():
    return cleanup_temp_files()
```

## Production Examples

### Web App Monitoring
```python
@task(300)  # Every 5 minutes
def monitor_website():
    import requests
    try:
        response = requests.get("https://myapp.com/health")
        return {"status": "up", "code": response.status_code}
    except Exception as e:
        return {"status": "down", "error": str(e)}

@task(cron="0 */6 * * *")  # Every 6 hours
def detailed_check():
    return comprehensive_health_check()
```

### Data Pipeline
```python
@task(3600)  # Hourly
def process_data():
    import pandas as pd
    df = pd.read_csv("input.csv")
    processed = df.groupby("category").sum()
    processed.to_csv("output.csv")
    return f"Processed {len(df)} records"

@daily("02:00")
def daily_report():
    generate_comprehensive_report()
    return "Daily report generated"
```

### Microservice Tasks
```python
@task(30)
async def sync_users():
    # Sync user data between services
    return await sync_user_database()

@task(600)  # Every 10 minutes
def cleanup_cache():
    # Clean expired cache entries
    return cleanup_redis_cache()
```

## Configuration Examples

### YAML Config File
```yaml
# config.yaml
global_settings:
  timezone: "Europe/Paris"
  log_level: "INFO"
  max_workers: 8

tasks:
  - name: "backup"
    module: "myapp.tasks"
    function: "backup_database"
    schedule:
      type: "cron"
      value: "0 2 * * *"
    priority: "HIGH"
    timeout: 3600

  - name: "health_check"
    module: "myapp.tasks" 
    function: "check_health"
    schedule:
      type: "interval"
      value: 300
    priority: "CRITICAL"
```

Load config:
```python
scheduler = PyScheduler(config_file="config.yaml")
scheduler.start()
```

## Complete Working Examples

All examples are available in the `examples/` directory:

- **basic_usage.py**: Simple interval and CRON tasks
- **advanced_usage.py**: Retry, priorities, async tasks
- **config_file_example.py**: YAML configuration examples
- **cron_examples.py**: Comprehensive CRON patterns
- **error_handling.py**: Robust error handling
- **async_tasks.py**: Asynchronous task examples

Run any example:
```bash
cd examples/
python basic_usage.py
python advanced_usage.py
```


