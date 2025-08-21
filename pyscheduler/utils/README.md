# PyScheduler - Utilities

This module contains all the basic utilities used in PyScheduler. These tools ensure consistency, validation, and robustness throughout the entire system.

## Table of Contents

- [Exceptions](#exceptions)
- [Logger](#logger)
- [Helpers](#helpers)
- [Usage Examples](#usage-examples)

---

## Exceptions

Module: `pyscheduler.utils.exceptions`

A hierarchy of custom exceptions with enriched context.

### Main Classes

#### `PySchedulerError` (Base)
```python
class PySchedulerError(Exception):
    def __init__(self, message: str, details: dict = None)
```

Base exception with support for contextual details.

**Example:**
```python
raise PySchedulerError("Processing error", {"task": "backup", "attempt": 3})
```

#### Specialized Exceptions

| Exception | Description | Usage |
|---|---|---|
| `TaskError` | Errors related to tasks | Invalid task, not found |
| `SchedulingError` | Scheduling errors | Invalid cron expression |
| `ConfigurationError` | Configuration errors | Incorrect YAML file |
| `ExecutionError` | Execution errors | Timeout, task failure |
| `ValidationError` | Validation errors | Invalid parameters |

#### Specific Exceptions

| Exception | Parameters | Description |
|---|---|---|
| `SchedulerNotRunningError` | `operation: str` | Scheduler not started |
| `TaskNotFoundError` | `task_name: str` | Task not found |
| `DuplicateTaskError` | `task_name: str` | Task already exists |
| `InvalidScheduleError` | `schedule_type, schedule_value` | Invalid schedule |
| `TaskTimeoutError` | `task_name, timeout` | Timeout exceeded |
| `MaxRetriesExceededError` | `task_name, max_retries, last_error` | Failed after all attempts |

**Examples:**
```python
# Simple exception
raise TaskNotFoundError("backup_task")

# Exception with context
raise InvalidScheduleError("cron", "invalid expression")

# Capture with details
try:
    # code...
except TaskTimeoutError as e:
    print(f"Task {e.task_name} timed out after {e.timeout}s")
```

---

## Logger

Module: `pyscheduler.utils.logger`

A flexible logging system with console, file, and JSON support.

### Main Classes

#### `PySchedulerLogger`
```python
class PySchedulerLogger:
    def __init__(
        self,
        name: str = "PyScheduler",
        level: str = "INFO", 
        log_file: Optional[str] = None,
        console_output: bool = True,
        json_format: bool = False
    )
```

Main logger with flexible configuration.

### Logging Methods

| Method | Description | Example |
|---|---|---|
| `debug(message, **kwargs)` | DEBUG level log | `logger.debug("Detail", task="test")` |
| `info(message, **kwargs)` | INFO level log | `logger.info("Starting", port=8080)` |
| `warning(message, **kwargs)` | WARNING level log | `logger.warning("Attention", retry=3)` |
| `error(message, **kwargs)` | ERROR level log | `logger.error("Failure", error="timeout")` |
| `critical(message, **kwargs)` | CRITICAL level log | `logger.critical("Stopping", reason="fatal")` |

### Specialized Methods

| Method | Description | Parameters |
|---|---|---|
| `task_started(task_name, **kwargs)` | Task started | task name + context |
| `task_completed(task_name, duration, **kwargs)` | Task completed | name, duration + context |
| `task_failed(task_name, error, **kwargs)` | Task failed | name, error + context |
| `scheduler_started()` | Scheduler started | none |
| `scheduler_stopped()` | Scheduler stopped | none |

### Utility Functions

| Function | Return | Description |
|---|---|---|
| `get_logger(...)` | `PySchedulerLogger` | Creates a logger |
| `setup_default_logger(...)` | `None` | Configures the default logger |
| `get_default_logger()` | `PySchedulerLogger` | Gets the default logger |

**Examples:**
```python
# Simple logger
from pyscheduler.utils import get_logger
logger = get_logger("MyApp", level="DEBUG")
logger.info("Application started")

# Logger with file
logger = get_logger(
    "MyApp", 
    log_file="app.log",
    json_format=True
)

# Default logger
from pyscheduler.utils import setup_default_logger, get_default_logger
setup_default_logger(level="INFO", log_file="scheduler.log")
logger = get_default_logger()

# Logging with context
logger.task_started("backup", database="users", size="1.2GB")
logger.task_completed("backup", 45.2, records=15000)
logger.task_failed("sync", "Connection timeout", host="api.example.com")
```

**JSON Format:**
```json
{
  "timestamp": "2025-08-21T12:09:33.123456",
  "level": "INFO",
  "logger": "PyScheduler",
  "message": "Task 'backup' completed successfully in 45.20s",
  "task_name": "backup",
  "duration": 45.2,
  "status": "success"
}
```

---

## Helpers

Module: `pyscheduler.utils.helpers`

Utility functions for validation, parsing, importing, and data manipulation.

### Validation

| Function | Parameters | Return | Description |
|---|---|---|---|
| `validate_cron_expression(cron_expr)` | `str` | `bool` | Validates cron expression |
| `validate_time_string(time_str)` | `str` | `bool` | Validates HH:MM format |

**Examples:**
```python
from pyscheduler.utils import validate_cron_expression, validate_time_string

# Cron validation
validate_cron_expression("0 9 * * 1-5")  # ✅ True
validate_cron_expression("invalid")      # ❌ ValidationError

# Time validation
validate_time_string("09:30")  # ✅ True  
validate_time_string("25:00")  # ❌ ValidationError
```

### Parsing and Conversion

| Function | Parameters | Return | Description |
|---|---|---|---|
| `parse_duration(duration)` | `Union[str, int, float]` | `float` | Parses to seconds |
| `ensure_datetime(value)` | `Union[str, datetime]` | `datetime` | Converts to datetime |
| `format_duration(seconds)` | `float` | `str` | Formats readable duration |

**Examples:**
```python
from pyscheduler.utils import parse_duration, ensure_datetime, format_duration

# Parse duration
parse_duration(60)        # 60.0
parse_duration("5m")      # 300.0
parse_duration("2h30m")   # 9000.0
parse_duration("1d")      # 86400.0

# Datetime conversion
ensure_datetime("2025-08-21 12:00:00")  # datetime object
ensure_datetime("2025-08-21")           # datetime object

# Format duration
format_duration(90)      # "1m 30s"
format_duration(3661)    # "1h 1m 1s"
format_duration(86401)   # "1d 1s"
```

### Import and Functions

| Function | Parameters | Return | Description |
|---|---|---|---|
| `import_function(module_path, function_name)` | `str, str` | `Callable` | Dynamic import |
| `safe_call(func, *args, **kwargs)` | `Callable, ...` | `Tuple[bool, Any, str]` | Safe call |
| `get_function_info(func)` | `Callable` | `Dict` | Info about function |

**Examples:**
```python
from pyscheduler.utils import import_function, safe_call, get_function_info

# Dynamic import
func = import_function("math", "sqrt")
result = func(16)  # 4.0

# Safe call
success, result, error = safe_call(func, 16)
if success:
    print(f"Result: {result}")
else:
    print(f"Error: {error}")

# Function info
info = get_function_info(func)
print(info['name'])      # "sqrt"
print(info['module'])    # "math"
print(info['is_async'])  # False
```

### Miscellaneous Utilities

| Function | Parameters | Return | Description |
|---|---|---|---|
| `create_safe_filename(name)` | `str` | `str` | Safe filename |
| `deep_merge_dicts(dict1, dict2)` | `dict, dict` | `dict` | Recursive merge |

**Examples:**
```python
from pyscheduler.utils import create_safe_filename, deep_merge_dicts

# Safe filename
create_safe_filename("Task: Backup/Restore")  # "Task_Backup_Restore"
create_safe_filename("file<>name")            # "file__name"

# Merge dictionaries
dict1 = {"a": 1, "b": {"x": 1}}
dict2 = {"b": {"y": 2}, "c": 3}
result = deep_merge_dicts(dict1, dict2)
# {"a": 1, "b": {"x": 1, "y": 2}, "c": 3}
```

---

## Usage Examples

### Complete Logger

```python
from pyscheduler.utils import setup_default_logger, get_default_logger

# Configuration
setup_default_logger(
    level="INFO",
    log_file="app.log", 
    json_format=True
)

logger = get_default_logger()

# Usage in a task
def backup_task():
    logger.task_started("backup", database="users")
    
    try:
        # Simulate work
        import time
        time.sleep(2)
        
        logger.info("Backup in progress", progress="50%")
        time.sleep(2)
        
        logger.task_completed("backup", 4.0, size="1.2GB")
        
    except Exception as e:
        logger.task_failed("backup", str(e))
        raise
```

### Validation and Parsing

```python
from pyscheduler.utils import (
    validate_cron_expression, parse_duration, 
    ensure_datetime, ValidationError
)

def parse_schedule_config(schedule_data):
    """Parses and validates a schedule configuration"""
    
    schedule_type = schedule_data.get("type")
    schedule_value = schedule_data.get("value")
    
    try:
        if schedule_type == "cron":
            validate_cron_expression(schedule_value)
            return schedule_type, schedule_value
            
        elif schedule_type == "interval":
            seconds = parse_duration(schedule_value)
            return schedule_type, seconds
            
        elif schedule_type == "once":
            dt = ensure_datetime(schedule_value)
            return schedule_type, dt
            
        else:
            raise ValidationError(f"Unknown schedule type: {schedule_type}")
            
    except ValidationError as e:
        logger.error(f"Invalid configuration: {e}")
        raise
```

### Secure Import and Execution

```python
from pyscheduler.utils import import_function, safe_call, get_function_info

def execute_task_function(module_name, function_name, *args, **kwargs):
    """Executes a task function securely"""
    
    try:
        # Import the function
        func = import_function(module_name, function_name)
        
        # Get info about the function
        info = get_function_info(func)
        logger.debug(f"Executing {info['name']}", module=info['module'])
        
        # Secure execution
        success, result, error = safe_call(func, *args, **kwargs)
        
        if success:
            logger.info(f"Function executed successfully", result=str(result)[:100])
            return result
        else:
            logger.error(f"Execution error: {error}")
            raise RuntimeError(error)
            
    except Exception as e:
        logger.error(f"Import/execution failed: {e}")
        raise
```

### Advanced Configuration Management

```python
from pyscheduler.utils import deep_merge_dicts, create_safe_filename
import json

def merge_configurations(base_config, override_config):
    """Merges two configurations"""
    
    # Recursive merge
    merged = deep_merge_dicts(base_config, override_config)
    
    # Create a safe filename for backup
    config_name = f"merged_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    safe_filename = create_safe_filename(config_name) + ".json"
    
    # Save
    with open(safe_filename, 'w') as f:
        json.dump(merged, f, indent=2, default=str)
    
    logger.info(f"Merged configuration saved: {safe_filename}")
    return merged
```

---

## Integration with Other Modules

The utilities are used extensively throughout PyScheduler:

### In Configuration
```python
# config/manager.py uses:
from ..utils import (
    ConfigurationError, ValidationError,
    validate_cron_expression, parse_duration,
    import_function, get_default_logger
)
```

### In Core
```python
# core/scheduler.py uses:
from ..utils import (
    get_default_logger, PySchedulerError,
    safe_call, format_duration
)
```

### In CLI
```python
# cli/main.py uses:
from ..utils import (
    setup_default_logger, ValidationError,
    create_safe_filename
)
```

This architecture avoids code duplication and ensures consistency across the entire project.

---

## Performance Notes

- **Logging:** The logger uses standard Python handlers, optimized for performance.
- **Validation:** Validations are cached when possible.
- **Dynamic Import:** Imported modules are cached by Python.
- **Parsing:** Parsing regexes are compiled only once.

## Extensibility

The utilities are designed to be easily extended:

```python
# Add a new exception
class CustomTaskError(TaskError):
    def __init__(self, task_name, custom_info):
        super().__init__(f"Custom error for {task_name}")
        self.custom_info = custom_info

# Add a custom validator  
def validate_custom_format(value):
    if not value.startswith("CUSTOM_"):
        raise ValidationError("Must start with CUSTOM_")
    return True
```

---

## Conclusion

The `utils` module is the foundation of PyScheduler. It provides the essential tools for robustness, validation, logging, and data manipulation, allowing other modules to focus on their business logic.

---

## Contact

For any questions, please open an issue on the GitHub repository.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
