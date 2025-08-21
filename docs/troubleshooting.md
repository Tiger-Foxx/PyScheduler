# Troubleshooting Guide

Common issues and solutions for PyScheduler.

## Installation Issues

### ImportError: No module named 'pyscheduler'

**Problem**: Module not found after installation
```
ImportError: No module named 'pyscheduler'
```

**Solutions**:
```bash
# Verify installation
pip list | grep pyscheduler

# Reinstall
pip uninstall pyscheduler
pip install pyscheduler-fox[full]

# Check Python path
python -c "import sys; print(sys.path)"
```

### Optional Dependencies Missing

**Problem**: Features not working (YAML, CRON, etc.)
```
Warning: PyYAML not installed. YAML configuration disabled.
```

**Solution**:
```bash
# Install all optional dependencies
pip install pyscheduler-fox[full]

# Or install specific features
pip install pyscheduler-fox[yaml,cron,timezone]
```

## Runtime Issues

### Tasks Not Executing

**Problem**: Tasks configured but not running

**Diagnostic**:
```python
scheduler = PyScheduler(log_level="DEBUG")
scheduler.start()

# Check task list
tasks = scheduler.list_tasks()
for task in tasks:
    print(f"Task: {task['name']}, Next run: {task['next_run_time']}")
```

**Common causes**:
- Scheduler not started: `scheduler.start()`
- Task disabled: `enabled=False`
- Invalid CRON expression
- Timezone issues

### Memory Usage Issues

**Problem**: High memory consumption

**Solutions**:
```python
# Reduce max_workers
scheduler = PyScheduler(max_workers=5)

# Clear old results
scheduler.clear_results()

# Use process executor for heavy tasks
scheduler.add_task(
    func=heavy_task,
    interval=3600,
    executor_type="process"
)
```

### Task Timeout Issues

**Problem**: Tasks timing out frequently

**Solutions**:
```python
# Increase timeout
@task(interval=60, timeout=120)  # 2 minutes
def slow_task():
    pass

# Use async for I/O bound tasks
@task(interval=60)
async def io_task():
    async with aiohttp.ClientSession() as session:
        # Async I/O operations
        pass
```

## Configuration Issues

### YAML Configuration Not Loading

**Problem**: Config file not recognized
```
ConfigurationError: Invalid configuration format
```

**Solutions**:
```python
# Check file exists
import os
if not os.path.exists("config.yaml"):
    print("Config file not found")

# Validate YAML syntax
import yaml
with open("config.yaml") as f:
    config = yaml.safe_load(f)
    print("YAML is valid")

# Check file encoding
with open("config.yaml", encoding="utf-8") as f:
    content = f.read()
```

### Invalid CRON Expressions

**Problem**: CRON tasks not scheduling
```
ValueError: Invalid CRON expression
```

**Common fixes**:
```python
# Correct CRON format: minute hour day month weekday
"0 9 * * *"      # ✅ 9 AM daily
"* 9 * * *"      # ❌ Every minute at 9 AM
"0 9 * * 1-5"    # ✅ 9 AM weekdays
"0 25 * * *"     # ❌ Invalid hour
```

**Test CRON expressions**:
```python
from croniter import croniter
from datetime import datetime

try:
    cron = croniter("0 9 * * *", datetime.now())
    next_run = cron.get_next(datetime)
    print(f"Next run: {next_run}")
except ValueError as e:
    print(f"Invalid CRON: {e}")
```

## Performance Issues

### Slow Task Execution

**Problem**: Tasks taking longer than expected

**Diagnostics**:
```python
# Enable detailed logging
scheduler = PyScheduler(log_level="DEBUG")

# Monitor task statistics
tasks = scheduler.list_tasks()
for task in tasks:
    stats = task['stats']
    print(f"Task: {task['name']}")
    print(f"  Average duration: {stats['average_duration']:.2f}s")
    print(f"  Success rate: {stats['success_rate']:.1%}")
```

**Solutions**:
```python
# Use threading for I/O bound tasks (default)
@task(interval=60)
def io_bound_task():
    pass

# Use process executor for CPU bound tasks
scheduler.add_task(
    func=cpu_intensive_task,
    interval=3600,
    executor_type="process"
)

# Use async for concurrent I/O
@task(interval=60)
async def concurrent_io():
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks)
```

### High CPU Usage

**Problem**: PyScheduler consuming too much CPU

**Solutions**:
```python
# Reduce polling frequency (internal setting)
scheduler = PyScheduler()
scheduler._polling_interval = 1.0  # Check every 1 second instead of 0.1

# Reduce concurrent tasks
scheduler = PyScheduler(max_workers=3)

# Use longer intervals between tasks
@task(300)  # Every 5 minutes instead of every minute
def less_frequent_task():
    pass
```

## Common Error Messages

### "Scheduler not running"

**Error**: Operations attempted on stopped scheduler
```python
try:
    scheduler.add_task(my_task, interval=60)
except SchedulerNotRunning:
    scheduler.start()
    scheduler.add_task(my_task, interval=60)
```

### "Task already exists"

**Error**: Duplicate task names
```python
# Use unique names
scheduler.add_task(my_task, interval=60, name="task_1")
scheduler.add_task(my_task, interval=120, name="task_2")

# Or remove existing task first
scheduler.remove_task("existing_task")
scheduler.add_task(my_task, interval=60, name="existing_task")
```

### "Maximum retry attempts exceeded"

**Error**: Task failing repeatedly
```python
# Increase retry attempts
@task(
    interval=60,
    retry_config=RetryConfig(
        max_attempts=5,  # More attempts
        max_delay=600    # Longer delays
    )
)
def unreliable_task():
    pass

# Or handle errors gracefully
@task(interval=60)
def robust_task():
    try:
        risky_operation()
    except Exception as e:
        logger.error(f"Task failed but continuing: {e}")
        return "failed_gracefully"
```

## Debug Mode

Enable comprehensive debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

scheduler = PyScheduler(log_level="DEBUG")

# Monitor all operations
@task(60)
def debug_task():
    print("Debug task running")
    return "debug_success"

scheduler.start()
```

## Getting Help

### Collect Diagnostic Information

```python
import pyscheduler
import sys
import platform

print(f"PyScheduler version: {pyscheduler.__version__}")
print(f"Python version: {sys.version}")
print(f"Platform: {platform.platform()}")

# Task information
scheduler = PyScheduler()
tasks = scheduler.list_tasks()
print(f"Active tasks: {len(tasks)}")

# System resources
import psutil
print(f"Memory usage: {psutil.virtual_memory().percent}%")
print(f"CPU usage: {psutil.cpu_percent()}%")
```

### Report Issues

When reporting issues, include:

1. **PyScheduler version**: `pip show pyscheduler`
2. **Python version**: `python --version`
3. **Operating system**: Windows/Linux/macOS
4. **Minimal reproduction code**
5. **Error messages and stack traces**
6. **Expected vs actual behavior**

**Report at**: https://github.com/Tiger-Foxx/PyScheduler/issues

### Community Support

- 📚 **Documentation**: https://pyscheduler.readthedocs.io/
- 💬 **Discussions**: https://github.com/Tiger-Foxx/PyScheduler/discussions
- 🐛 **Issues**: https://github.com/Tiger-Foxx/PyScheduler/issues
- 📧 **Email**: donfackarthur750@gmail.com


