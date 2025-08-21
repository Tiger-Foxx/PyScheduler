"""
PyScheduler - Utilities Package
===============================

Utilitaires pour PyScheduler.
"""

from .exceptions import (
    PySchedulerError,
    TaskError,
    SchedulingError,
    ConfigurationError,
    ExecutionError,
    ValidationError,
    SchedulerNotRunningError,
    TaskNotFoundError,
    DuplicateTaskError,
    InvalidScheduleError,
    TaskTimeoutError,
    MaxRetriesExceededError
)

from .logger import (
    PySchedulerLogger,
    LogLevel,
    get_logger,
    setup_default_logger,
    get_default_logger
)

from .helpers import (
    validate_cron_expression,
    validate_time_string,
    parse_duration,
    import_function,
    safe_call,
    get_function_info,
    ensure_datetime,
    create_safe_filename,
    format_duration,
    deep_merge_dicts
)

__all__ = [
    # Exceptions
    'PySchedulerError',
    'TaskError', 
    'SchedulingError',
    'ConfigurationError',
    'ExecutionError',
    'ValidationError',
    'SchedulerNotRunningError',
    'TaskNotFoundError',
    'DuplicateTaskError',
    'InvalidScheduleError',
    'TaskTimeoutError',
    'MaxRetriesExceededError',
    
    # Logger
    'PySchedulerLogger',
    'LogLevel',
    'get_logger',
    'setup_default_logger', 
    'get_default_logger',
    
    # Helpers
    'validate_cron_expression',
    'validate_time_string',
    'parse_duration',
    'import_function',
    'safe_call',
    'get_function_info',
    'ensure_datetime',
    'create_safe_filename',
    'format_duration',
    'deep_merge_dicts'
]