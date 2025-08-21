"""
PyScheduler - Configuration Package
===================================

Configuration et décorateurs pour PyScheduler utilisant nos utilitaires.
"""

from .manager import (
    ConfigManager,
    PySchedulerConfig,
    GlobalConfig,
    TaskConfig,
    RetryConfig,
    ScheduleType,
    Priority
)

from .decorators import (
    schedule_task,
    task,
    every,
    daily,
    weekly,
    once,
    startup,
    shutdown,
    high_priority,
    low_priority,
    critical,
    get_task_registry,
    TaskRegistry
)

__all__ = [
    # Manager
    'ConfigManager',
    'PySchedulerConfig',
    'GlobalConfig', 
    'TaskConfig',
    'RetryConfig',
    'ScheduleType',
    'Priority',
    
    # Decorators
    'schedule_task',
    'task',
    'every',
    'daily',
    'weekly', 
    'once',
    'startup',
    'shutdown',
    'high_priority',
    'low_priority',
    'critical',
    'get_task_registry',
    'TaskRegistry'
]

# Fonction utilitaire pour créer une configuration par défaut
def create_default_config(file_path: str = "scheduler_config.yaml"):
    """
    Crée un fichier de configuration par défaut
    
    Args:
        file_path: Chemin du fichier à créer
    """
    manager = ConfigManager()
    manager.create_default_config(file_path)


# Fonction utilitaire pour valider une configuration
def validate_config_file(file_path: str) -> bool:
    """
    Valide un fichier de configuration
    
    Args:
        file_path: Chemin du fichier à valider
        
    Returns:
        True si valide
        
    Raises:
        ConfigurationError: Si la validation échoue
    """
    manager = ConfigManager()
    config = manager.load_from_file(file_path)
    
    # Valider toutes les fonctions de tâches
    for task in config.tasks:
        manager.validate_task_function(task)
    
    return True