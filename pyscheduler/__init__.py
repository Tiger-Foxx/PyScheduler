"""
PyScheduler - A Powerful Yet Simple Python Task Scheduler
=========================================================

PyScheduler est un système de planification de tâches Python conçu pour être :
- Extrêmement simple à utiliser
- Très puissant sous le capot  
- Production-ready avec monitoring complet
- Compatible avec async/sync, threads, configuration YAML/décorateurs

Exemples d'utilisation rapide :

    # Ultra-simple
    from pyscheduler import PyScheduler
    
    scheduler = PyScheduler()
    
    @scheduler.add_task(interval=60)
    def my_task():
        print("Exécuté chaque minute!")
    
    scheduler.run_forever()

    # Avec décorateurs
    from pyscheduler.config import task, daily
    
    @task(60)  # Toutes les minutes
    def check_system(): pass
    
    @daily("09:00")  # Tous les jours à 9h
    def morning_report(): pass
    
    scheduler = PyScheduler(auto_start=True)

Auteur: theTigerFox
Version: 1.0.0
License: MIT
Site: https://github.com/theTigerFox/PyScheduler
"""

__version__ = "1.0.0"
__author__ = "theTigerFox"
__email__ = "thetigerfox@example.com"
__license__ = "MIT"
__url__ = "https://github.com/theTigerFox/PyScheduler"

# Imports principaux pour usage simple
from .core.scheduler import PyScheduler, SchedulerState
from .core.task import Task, TaskExecution, TaskStatus
from .config import (
    schedule_task, task, every, daily, weekly, once, startup, shutdown,
    ScheduleType, Priority
)
from .utils import (
    PySchedulerError, TaskError, ConfigurationError, ValidationError,
    get_logger, setup_default_logger
)

# Imports pour usage avancé (pas dans __all__ pour garder l'API simple)
from .core import *
from .config import *
from .utils import *

__all__ = [
    # Version et métadonnées
    '__version__',
    '__author__', 
    '__license__',
    
    # Classes principales (usage simple)
    'PyScheduler',
    'SchedulerState',
    'Task',
    'TaskExecution',
    'TaskStatus',
    
    # Décorateurs (usage simple)
    'schedule_task',
    'task',
    'every', 
    'daily',
    'weekly',
    'once',
    'startup',
    'shutdown',
    
    # Enums utiles
    'ScheduleType',
    'Priority',
    
    # Exceptions principales
    'PySchedulerError',
    'TaskError',
    'ConfigurationError', 
    'ValidationError',
    
    # Logging
    'get_logger',
    'setup_default_logger'
]

# Message de bienvenue (optionnel, pour débug)
def _print_welcome():
    """Affiche un message de bienvenue lors de l'import (debug)"""
    import sys
    if hasattr(sys, 'ps1'):  # Mode interactif
        print(f"🚀 PyScheduler {__version__} chargé - Prêt pour la planification!")

# Décommenter pour activer le message de bienvenue
# _print_welcome()