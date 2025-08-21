"""
PyScheduler - Custom Exceptions
===============================

Exceptions personnalisées pour PyScheduler avec hiérarchie claire.
"""

class PySchedulerError(Exception):
    """Exception de base pour PyScheduler"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class TaskError(PySchedulerError):
    """Erreurs liées aux tâches"""
    pass


class SchedulingError(PySchedulerError):
    """Erreurs de planification"""
    pass


class ConfigurationError(PySchedulerError):
    """Erreurs de configuration"""
    pass


class ExecutionError(PySchedulerError):
    """Erreurs d'exécution"""
    pass


class ValidationError(PySchedulerError):
    """Erreurs de validation"""
    pass


class SchedulerNotRunningError(PySchedulerError):
    """Erreur quand le scheduler n'est pas démarré"""
    
    def __init__(self, operation: str = ""):
        message = f"Le scheduler doit être démarré pour effectuer cette opération"
        if operation:
            message += f": {operation}"
        super().__init__(message)


class TaskNotFoundError(TaskError):
    """Erreur quand une tâche n'est pas trouvée"""
    
    def __init__(self, task_name: str):
        super().__init__(f"Tâche '{task_name}' introuvable")
        self.task_name = task_name


class DuplicateTaskError(TaskError):
    """Erreur quand une tâche existe déjà"""
    
    def __init__(self, task_name: str):
        super().__init__(f"Tâche '{task_name}' existe déjà")
        self.task_name = task_name


class InvalidScheduleError(SchedulingError):
    """Erreur de planification invalide"""
    
    def __init__(self, schedule_type: str, schedule_value: str):
        super().__init__(
            f"Planification invalide: type='{schedule_type}', valeur='{schedule_value}'"
        )
        self.schedule_type = schedule_type
        self.schedule_value = schedule_value


class TaskTimeoutError(ExecutionError):
    """Erreur de timeout d'une tâche"""
    
    def __init__(self, task_name: str, timeout: float):
        super().__init__(f"Tâche '{task_name}' a dépassé le timeout de {timeout}s")
        self.task_name = task_name
        self.timeout = timeout


class MaxRetriesExceededError(ExecutionError):
    """Erreur quand le nombre max de tentatives est atteint"""
    
    def __init__(self, task_name: str, max_retries: int, last_error: str):
        super().__init__(
            f"Tâche '{task_name}' a échoué après {max_retries} tentatives. "
            f"Dernière erreur: {last_error}"
        )
        self.task_name = task_name
        self.max_retries = max_retries
        self.last_error = last_error