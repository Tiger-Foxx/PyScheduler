# PyScheduler - Configuration

This module handles all of PyScheduler's configuration. It offers two main approaches:
1.  **YAML files** for external configuration
2.  **Python decorators** for in-code configuration

## Table of Contents

- [Configuration via YAML file](#configuration-via-yaml-file)
- [Configuration via decorators](#configuration-via-decorators)
- [Scheduling Types](#scheduling-types)
- [Advanced Configuration](#advanced-configuration)
- [ConfigManager API](#configmanager-api)
- [Task Registry](#task-registry)

---

## Configuration via YAML file

### Basic Structure

```yaml
# scheduler_config.yaml
global_settings:
  timezone: "Europe/Paris"
  max_workers: 8
  log_level: "INFO"
  log_file: "scheduler.log"
  json_logs: false
  persistence_file: "scheduler_state.json"
  shutdown_timeout: 30.0

tasks:
  - name: "backup_task"
    module: "myapp.tasks"
    function: "backup_database"
    schedule:
      type: "daily"
      value: "03:00"
    enabled: true
    priority: "high"
    timeout: 1800  # 30 minutes
    max_runs: null
    retry_policy:
      max_attempts: 3
      backoff_factor: 2.0
      max_delay: 300
    tags: ["backup", "database"]
    metadata:
      description: "Daily database backup"
```

### Complete Example with Multiple Tasks

```yaml
global_settings:
  timezone: "UTC"
  max_workers: 4
  log_level: "INFO"

tasks:
  # Simple interval task
  - name: "health_check"
    module: "monitoring"
    function: "check_system_health"
    schedule:
      type: "interval"
      value: 300  # 5 minutes
    enabled: true

  # Task with cron expression
  - name: "weekly_report"
    module: "reports"
    function: "generate_weekly_report"
    schedule:
      type: "cron"
      value: "0 9 * * 1"  # Monday at 9am
    priority: "normal"
    timeout: "30m"
    retry_policy:
      max_attempts: 2
      backoff_factor: 1.5

  # One-time task
  - name: "migration_task"
    module: "maintenance"
    function: "migrate_data"
    schedule:
      type: "once"
      value: "2025-09-01 02:00:00"
    priority: "critical"
    
  # Startup task
  - name: "init_system"
    module: "system"
    function: "initialize"
    schedule:
      type: "startup"
      value: null
```

### Loading a YAML file

```python
from pyscheduler.config import ConfigManager

# Load configuration
manager = ConfigManager()
config = manager.load_from_file("scheduler_config.yaml")

# Use with the scheduler
from pyscheduler import PyScheduler
scheduler = PyScheduler(config=config)
```

---

## Configuration via decorators

### Basic Decorators

```python
from pyscheduler.config import schedule_task, task, every, daily

# Explicit method with schedule_task
@schedule_task(interval=60, priority="high")
def check_logs():
    print("Checking logs")

# Simplified method with auto-detection
@task(60)  # Auto-detects: 60-second interval
def simple_task():
    print("Simple task")

@task("09:30")  # Auto-detects: daily at 9:30am
def morning_task():
    print("Morning task")

@task("0 */2 * * *")  # Auto-detects: cron expression
def cron_task():
    print("Every 2 hours")

# Readable method with every
@every(minutes=5)
def frequent_task():
    print("Every 5 minutes")

@every(hours=2, minutes=30)
def periodic_task():
    print("Every 2h30")

# Specialized method
@daily("14:00")
def afternoon_report():
    print("Afternoon report")
```

### Advanced Decorators

```python
from pyscheduler.config import weekly, once, startup, shutdown, critical

# Weekly task
@weekly(1, "09:00")  # Tuesday at 9am (0=sunday, 1=monday, ...)
def weekly_maintenance():
    print("Weekly maintenance")

# One-time task
@once("2025-12-25 00:00:00")
def christmas_greeting():
    print("Merry Christmas!")

# Special tasks
@startup()
def initialize_app():
    print("Initialization at startup")

@shutdown()
def cleanup_app():
    print("Cleanup at shutdown")

# Critical task
@critical(interval=30)
def monitor_critical_service():
    print("Critical monitoring")
```

### Complete Configuration with Decorator

```python
@schedule_task(
    interval="5m",           # Every 5 minutes
    name="custom_monitor",   # Custom name
    priority="high",         # High priority
    timeout="2m",           # 2-minute timeout
    max_runs=100,           # Maximum 100 runs
    max_attempts=3,         # 3 attempts on failure
    backoff_factor=2.0,     # Exponential backoff
    max_delay="5m",         # Max delay between attempts
    tags=["monitoring", "critical"],
    metadata={"team": "ops", "alert": True}
)
def advanced_monitor():
    """Advanced monitoring with full configuration"""
    print("Monitoring in progress...")
```

---

## Scheduling Types

### 1. Interval

Runs every X seconds.

```python
# Via decorator
@task(60)  # 60 seconds
@every(minutes=5)  # 5 minutes
@schedule_task(interval="2h")  # 2 hours

# Via YAML
schedule:
  type: "interval"
  value: 300  # 5 minutes in seconds
```

### 2. Cron (Cron Expression)

Uses standard cron syntax (5 fields).

```python
# Via decorator  
@task("0 9 * * 1-5")  # 9am from Monday to Friday
@schedule_task(cron="*/15 * * * *")  # Every 15 minutes

# Via YAML
schedule:
  type: "cron"
  value: "0 2 * * 0"  # Sunday at 2am
```

**Cron format:** `minute hour day_of_month month day_of_week`
- `*`: all values
- `*/5`: every 5 units
- `1-5`: range from 1 to 5
- `1,3,5`: specific values

### 3. Daily

Runs every day at a specific time.

```python
# Via decorator
@daily("09:30")
@task("14:00")  # Auto-detected as daily

# Via YAML
schedule:
  type: "daily"
  value: "03:00"
```

### 4. Weekly

Runs once a week.

```python
# Via decorator
@weekly(1, "09:00")  # Tuesday at 9am

# Via YAML
schedule:
  type: "weekly"
  value: [1, "09:00"]  # [day_of_week, time]
```

**Days of the week:** 0=sunday, 1=monday, ..., 6=saturday

### 5. Once

Single execution at a specific date/time.

```python
# Via decorator
@once("2025-09-15 14:30:00")

# Via YAML
schedule:
  type: "once"
  value: "2025-09-15 14:30:00"
```

### 6. Startup/Shutdown

Runs on scheduler startup or shutdown.

```python
# Via decorator
@startup()
@shutdown()

# Via YAML
schedule:
  type: "startup"
  value: null
```

---

## Advanced Configuration

### Error Handling and Retry

```python
@schedule_task(
    interval=60,
    max_attempts=5,        # 5 maximum attempts
    backoff_factor=1.5,    # Delay x1.5 on each attempt
    max_delay="10m"        # Maximum delay of 10 minutes
)
def fragile_task():
    # Code that might fail
    pass
```

```yaml
retry_policy:
  max_attempts: 3
  backoff_factor: 2.0
  max_delay: 300
```

### Priorities

```python
# Via decorator
@critical(interval=30)     # Critical priority
@high_priority(daily="09:00")  # High priority
@low_priority(weekly=(0, "23:00"))  # Low priority

# Via configuration
@schedule_task(interval=60, priority="normal")
```

```yaml
priority: "critical"  # critical, high, normal, low, idle
```

### Timeout

```python
@schedule_task(interval=60, timeout="5m")  # 5-minute timeout
```

```yaml
timeout: 300  # 5 minutes in seconds
```

### Tags and Metadata

```python
@schedule_task(
    interval=60,
    tags=["monitoring", "health"],
    metadata={
        "team": "ops",
        "alert_channel": "#alerts",
        "documentation": "https://wiki.company.com/task123"
    }
)
def tagged_task():
    pass
```

---

## ConfigManager API

### Loading Configuration

```python
from pyscheduler.config import ConfigManager

manager = ConfigManager()

# From a YAML file
config = manager.load_from_file("config.yaml")

# From a dictionary
config_dict = {
    "global_settings": {"timezone": "UTC"},
    "tasks": [...]
}
config = manager.load_from_dict(config_dict)
```

### Saving Configuration

```python
# Save to YAML
manager.save_to_file(config, "output.yaml")

# Create a default configuration
manager.create_default_config("default_config.yaml")
```

### Validation

```python
# Validate that a task function exists
for task in config.tasks:
    manager.validate_task_function(task)
```

### Manipulating Configuration

```python
# Add a task
from pyscheduler.config import TaskConfig, ScheduleType

task = TaskConfig(
    name="new_task",
    function="my_function", 
    module="mymodule",
    schedule_type=ScheduleType.INTERVAL,
    schedule_value=60
)
config.add_task(task)

# Remove a task
config.remove_task("task_name")

# Get a task
task = config.get_task("task_name")
```

---

## Task Registry

The registry automatically collects all tasks defined with decorators.

```python
from pyscheduler.config import get_task_registry

# In your code, define tasks
@task(60)
def task1():
    pass

@daily("09:00")
def task2():
    pass

# Get all registered tasks
registry = get_task_registry()
all_tasks = registry.get_all_tasks()

# Use with the scheduler
from pyscheduler import PyScheduler
scheduler = PyScheduler()

# Add all tasks from the registry
for task_config in all_tasks:
    func = task_config.metadata['_function_ref']
    scheduler.add_task_from_config(task_config, func)
```

### Clearing the Registry

```python
# Clear the registry (useful for tests)
registry = get_task_registry()
registry.clear()
```

---

## Practical Examples

### Web Application with Monitoring

```python
from pyscheduler.config import *

@every(minutes=1)
def check_database():
    """Check the database every minute"""
    # Verification code
    pass

@every(minutes=5)
def check_api_endpoints():
    """Test API endpoints"""
    # Test code
    pass

@daily("02:00")
def backup_database():
    """Daily backup"""
    # Backup code
    pass

@weekly(0, "23:00")  # Sunday 11pm
def weekly_cleanup():
    """Weekly cleanup"""
    # Cleanup code
    pass

@startup()
def initialize_monitoring():
    """Initialization at startup"""
    print("Monitoring system started")

@shutdown()
def cleanup_monitoring():
    """Cleanup at shutdown"""
    print("Shutting down monitoring system")
```

### Mixed Configuration (YAML + Decorators)

```python
# config.yaml
global_settings:
  timezone: "Europe/Paris"
  max_workers: 4

tasks:
  - name: "external_sync"
    module: "sync"
    function: "sync_external_data"
    schedule:
      type: "cron"
      value: "0 */6 * * *"  # Every 6 hours

# app.py
from pyscheduler.config import *
from pyscheduler import PyScheduler

# Tasks defined by decorator
@every(minutes=15)
def internal_health_check():
    pass

@daily("08:00")
def morning_report():
    pass

# Loading and merging
manager = ConfigManager()
yaml_config = manager.load_from_file("config.yaml")

registry = get_task_registry()
decorator_tasks = registry.get_all_tasks()

# Use with the scheduler
scheduler = PyScheduler(config=yaml_config)
for task_config in decorator_tasks:
    func = task_config.metadata['_function_ref']
    scheduler.add_task_from_config(task_config, func)
```

---

## Usage Tips

### 1. Choosing between YAML and Decorators

**Use YAML when:**
- External configuration is needed
- Deployment with different configs
- Non-developers need to modify the config
- Tasks are defined in separate modules

**Use decorators when:**
- Configuration is close to the code
- Rapid development
- Simple and integrated tasks
- Prototyping

### 2. Best Practices

```python
# ✅ Good: explicit names
@task(300, name="user_cleanup")
def cleanup_inactive_users():
    pass

# ❌ Avoid: generic names
@task(300)
def task():
    pass

# ✅ Good: tags for organization
@daily("03:00", tags=["backup", "critical"])
def backup_user_data():
    pass

# ✅ Good: timeout for long tasks
@schedule_task(interval=3600, timeout="30m")
def long_running_task():
    pass

# ✅ Good: metadata for documentation
@task(
    "0 9 * * 1-5",
    metadata={
        "description": "Daily sales report",
        "owner": "team-sales",
        "documentation": "https://wiki.internal/sales-report"
    }
)
def daily_sales_report():
    pass
```

### 3. Error Handling

```python
# Robust configuration with retry
@schedule_task(
    interval="5m",
    max_attempts=3,
    backoff_factor=2.0,
    max_delay="10m",
    timeout="2m"
)
def api_sync():
    """Synchronization with external API"""
    try:
        # Synchronization code
        pass
    except Exception as e:
        # Log the error, it will be handled by the retry
        print(f"Sync error: {e}")
        raise
```

---

## Troubleshooting

### Common Errors

1.  **Invalid cron expression**
    ```
    ValidationError: Cron expression must have 5 parts, 6 found
    ```
    → Check the format: `minute hour day month day_of_week`

2.  **Function not found**
    ```
    ConfigurationError: Function 'my_func' not found in 'mymodule'
    ```
    → Check that the module and function exist

3.  **Invalid duration**
    ```
    ValidationError: Invalid duration format: 5x
    ```
    → Use `5s`, `5m`, `5h`, `5d` or a number

4.  **Ambiguous scheduling**
    ```
    ValidationError: Only one scheduling method allowed
    ```
    → Use only one parameter: `interval` OR `cron` OR `daily_at`, etc.

### Configuration Validation

```python
from pyscheduler.config import validate_config_file

try:
    validate_config_file("my_config.yaml")
    print("Configuration valid ✅")
except Exception as e:
    print(f"Configuration invalid ❌: {e}")
```
