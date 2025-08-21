# API Reference

Complete reference for PyScheduler classes and functions.

## Core Classes

### PyScheduler

Main scheduler class for managing tasks.

```python
PyScheduler(
    config_file: str = None,
    timezone: str = "UTC", 
    max_workers: int = 10,
    log_level: str = "INFO"
)
```

#### Methods

**`add_task(func, interval=None, cron=None, daily_at=None, **kwargs)`**
```python
scheduler.add_task(my_function, interval=60)
scheduler.add_task(my_function, cron="0 9 * * *")
scheduler.add_task(my_function, daily_at="14:30")
```

**`start()` / `stop()`**
```python
scheduler.start()  # Start scheduler
scheduler.stop()   # Stop gracefully
```

**`list_tasks()` / `get_task_status(name)`**
```python
tasks = scheduler.list_tasks()           # All tasks info
status = scheduler.get_task_status("my_task")  # Single task
```

### Task Decorators

**`@task(interval=None, cron=None, **kwargs)`**
```python
@task(60)                    # Every 60 seconds
@task(cron="0 9 * * 1-5")   # 9 AM weekdays
@task(interval=30, priority=Priority.HIGH)
```

**`@daily(time_str)`**
```python
@daily("09:00")    # Every day at 9 AM
@daily("23:30")    # Every day at 11:30 PM
```

**`@startup()` / `@shutdown()`**
```python
@startup()     # Run on scheduler start
@shutdown()    # Run on scheduler stop
```

## Configuration Classes

### Priority
```python
from pyscheduler.config import Priority

Priority.CRITICAL  # Highest priority
Priority.HIGH      
Priority.NORMAL    # Default
Priority.LOW       
Priority.IDLE      # Lowest priority
```

### RetryConfig
```python
from pyscheduler.config import RetryConfig

RetryConfig(
    max_attempts=3,      # Max retry attempts
    backoff_factor=2.0,  # Exponential backoff
    max_delay=300        # Max delay between retries
)
```

## Complete Example

```python
from pyscheduler import PyScheduler, task, daily, startup
from pyscheduler.config import Priority, RetryConfig

# Decorator usage
@task(interval=30, priority=Priority.HIGH)
def health_check():
    return check_system()

@daily("02:00")
def backup():
    return backup_database()

@startup()
def init_app():
    return initialize()

# Programmatic usage
scheduler = PyScheduler(log_level="INFO")

scheduler.add_task(
    func=critical_task,
    interval=60,
    name="critical",
    priority=Priority.CRITICAL,
    timeout=30,
    retry_config=RetryConfig(max_attempts=5)
)

with scheduler:  # Context manager
    scheduler.run_forever()
```

## YAML Configuration

```yaml
global_settings:
  timezone: "UTC"
  log_level: "INFO" 
  max_workers: 10

tasks:
  - name: "my_task"
    module: "myapp.tasks"
    function: "my_function"
    schedule:
      type: "interval"  # or "cron", "daily"
      value: 60
    priority: "HIGH"    # CRITICAL, HIGH, NORMAL, LOW, IDLE
    timeout: 30
    retry_policy:
      max_attempts: 3
      backoff_factor: 2.0
```

## Error Handling

All PyScheduler exceptions inherit from `PySchedulerError`:

- `TaskError`: Task execution issues
- `ConfigurationError`: Configuration problems  
- `SchedulerNotRunning`: Operations on stopped scheduler

```python
from pyscheduler.exceptions import PySchedulerError

try:
    scheduler.start()
except PySchedulerError as e:
    print(f"Scheduler error: {e}")
```
