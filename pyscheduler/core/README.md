# PyScheduler Core Technical Documentation (`pyscheduler/core`)

This document provides a detailed technical description of each module, class, and important function within the `core` directory. It is intended for developers and aims to serve as an internal API reference.

---

## Table of Contents
1.  [**`scheduler.py` Module**](#1-schedulerpy-module---the-orchestrator)
2.  [**`task.py` Module**](#2-taskpy-module---the-work-unit)
3.  [**`triggers.py` Module**](#3-triggerspy-module---the-scheduling-mechanism)
4.  [**`executors.py` Module**](#4-executorspy-module---the-execution-engine)

---

## 1. `scheduler.py` Module - The Orchestrator

This module contains the main `PyScheduler` class, which acts as the central entry point and coordinator for the entire system.

### `PyScheduler` Class
Manages the lifecycle, task registry, configuration, and coordination of executors.

#### Main Methods

-   `__init__(config, config_file, timezone, ...)`
    -   **Description**: Initializes the scheduler. Loads the configuration from an object, a file, or the provided parameters. Sets up logging, default executors, and exit handlers (`atexit`, `signal`).
    -   **Parameters**:
        -   `config: PySchedulerConfig`: A complete configuration object.
        -   `config_file: str`: Path to a YAML configuration file.
        -   `...`: Multiple parameters to override the default configuration (logging, persistence, etc.).

-   `add_task(func, name, interval, cron, ...)` -> `Union[Task, Callable]`
    -   **Description**: Adds a task to the scheduler. This is a flexible method that can be used directly or as a decorator.
    -   **Parameters**:
        -   `func: Callable`: The function to execute. If `None`, the method returns a decorator.
        -   `name: str`: Unique name of the task.
        -   `interval`, `cron`, `daily_at`, etc.: Scheduling parameters (only one allowed per task).
        -   `priority`, `timeout`, `executor`, etc.: Execution configuration parameters.
    -   **Returns**: A `Task` instance if `func` is provided, otherwise a decorator.

-   `start()`
    -   **Description**: Starts the scheduler. This action loads tasks, starts the executors, and launches the control threads (scheduling loop and monitoring).

-   `stop(timeout: float = 30.0)`
    -   **Description**: Gracefully stops the scheduler. Executes `on_shutdown` tasks, stops control threads and executors, and saves the state if persistence is enabled.

-   `run_task_now(task_name: str, executor_name: str = None)` -> `str`
    -   **Description**: Forces the immediate execution of a task, bypassing its normal schedule.
    -   **Returns**: The ID of the execution request.

-   `get_task(task_name: str)` -> `Optional[Task]`
    -   **Description**: Retrieves a task instance by its name.

-   `list_tasks(include_disabled: bool = True, tags: Set[str] = None)` -> `List[Task]`
    -   **Description**: Returns a list of all registered tasks, with filtering options.

-   `get_stats()` -> `dict`
    -   **Description**: Returns a dictionary containing the complete statistics of the scheduler (state, uptime, task stats, executor stats).

### `SchedulerState` Class
An `Enum` that defines the possible operating states of the scheduler.
-   `STOPPED`, `STARTING`, `RUNNING`, `STOPPING`, `PAUSED`.

---

## 2. `task.py` Module - The Work Unit

This module defines the `Task` class, which is a complete and autonomous representation of a scheduled action.

### `Task` Class
Encapsulates a function, its schedule, its state, its execution configuration, and its statistics.

#### Key Methods and Properties

-   `__init__(name, func, schedule_type, ...)`
    -   **Description**: Initializes a task. Validates the configuration and calculates the first `next_run_time`.
    -   **Parameters**: Contains all the configuration of a task (name, function, scheduling type, priority, timeout, retry configuration, etc.).

-   `should_run(current_time: datetime)` -> `bool`
    -   **Description**: Crucial method called by the main scheduler loop. Determines if the task should run now by comparing `current_time` to `self.next_run_time`.

-   `execute()` -> `TaskExecution`
    -   **Description**: Entry point for task execution. Manages `timeout` and `retry` logic (`_execute_with_retry`), calls the target function, and updates statistics.
    -   **Returns**: A `TaskExecution` object containing all the details of this specific execution.

-   `cancel()`, `pause()`, `resume()`
    -   **Description**: Methods to control the task's state. `pause()` disables the task, `resume()` reactivates it, and `cancel()` permanently disables it.

-   `to_dict()` -> `dict`
    -   **Description**: Serializes the complete state of the task (configuration, state, statistics) into a dictionary.

-   `is_running: bool` (Property)
    -   **Description**: Returns `True` if the task is currently running.

### Support Dataclasses

-   **`TaskStatus(Enum)`**: Defines the possible states of a task *execution* (`PENDING`, `RUNNING`, `SUCCESS`, `FAILED`, `TIMEOUT`, `CANCELLED`).
-   **`TaskExecution`**: Stores information about a single execution: start/end times, duration, status, result, error, etc. It is the "receipt" of an execution.
-   **`TaskStats`**: Aggregates statistics from all executions of a task: total number, success rate, min/max/average durations, etc.

---

## 3. `triggers.py` Module - The Scheduling Mechanism

This module provides the classes (triggers) that calculate the next execution time of a task.

### `BaseTrigger` Class
Abstract base class that defines the interface for all triggers.

-   `get_next_run_time(last_run: Optional[datetime])` -> `Optional[datetime]`
    -   **Description**: Abstract method that each trigger must implement. Calculates and returns the next execution time based on the last one.

### Trigger Implementations

Each class inherits from `BaseTrigger` and implements `get_next_run_time` with its own logic:
-   **`IntervalTrigger`**: For regular intervals (e.g., every 30 seconds).
-   **`CronTrigger`**: For cron expressions (e.g., `"0 9 * * *"`).
-   **`DailyTrigger`**: For a fixed time each day (e.g., `"14:30"`).
-   **`WeeklyTrigger`**: For a fixed day of the week and time (e.g., `(0, "09:00")` for Monday at 9am).
-   **`OnceTrigger`**: For a single execution at a specific date/time.
-   **`StartupTrigger`**: For an execution at scheduler startup.
-   **`ShutdownTrigger`**: For an execution at scheduler shutdown.
-   **`MonthlyTrigger`**: For a fixed day of the month and time.

### `TriggerFactory` Class

-   `create_trigger(schedule_type: ScheduleType, schedule_value: any)` -> `BaseTrigger`
    -   **Description**: Static method that receives a schedule type and its value, and returns the corresponding concrete trigger instance. This is the central point for creating triggers.

---

## 4. `executors.py` Module - The Execution Engine

This module provides the classes (executors) that manage *how* a task is executed (threading, async, etc.).

### `BaseExecutor` Class
Abstract base class that defines the interface for all execution strategies.

-   `submit_task(task: Task, priority: Priority)` -> `str`
    -   **Description**: Submits a task for execution. The task is usually placed in an internal queue.
-   `start()` / `stop()`
    -   **Description**: Manage the lifecycle of the executor's worker pool.

### Executor Implementations

-   **`ThreadExecutor`**: Uses a `concurrent.futures.ThreadPoolExecutor`. Ideal for I/O-bound tasks. **This is the default executor.**
-   **`AsyncExecutor`**: Uses `asyncio` and an `asyncio.Semaphore` to run `async` tasks natively and concurrently.
-   **`ImmediateExecutor`**: Executes tasks immediately in the calling thread. Mainly for testing and debugging.

### `ExecutorManager` Class
Manages a collection of multiple executors, allowing for complex execution strategies.

-   `add_executor(name: str, executor: BaseExecutor, is_default: bool = False)`
    -   **Description**: Registers a new executor instance under a given name.
-   `route_task(task_name: str, executor_name: str)`
    -   **Description**: Creates a rule so that a specific task is always sent to a specific executor, instead of the default one.
-   `submit_task(task: Task)` -> `str`
    -   **Description**: Receives a task from the scheduler, determines which executor should handle it (based on routing rules or the default executor), and forwards it.

### Support Dataclasses

-   **`ExecutionRequest`**: Internal object that encapsulates a `Task` and its `Priority` to be placed in the executors' `PriorityQueue`.
-   **`ExecutorStats`**: Stores the statistics of an executor (active tasks, queue size, total number of executions, etc.).
