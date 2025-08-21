"""
PyScheduler - Configuration Decorators
======================================

Décorateurs pour configurer facilement les tâches en utilisant nos utilitaires.
"""

import functools
from typing import Callable, Optional, Union, List, Dict, Any, Tuple
from datetime import datetime

# Import de nos utilitaires
from ..utils import (
    ValidationError, get_default_logger,
    parse_duration, validate_time_string, validate_cron_expression,
    ensure_datetime, get_function_info
)
from .manager import TaskConfig, ScheduleType, Priority, RetryConfig


class TaskRegistry:
    """
    Registre global des tâches définies par décorateurs
    
    Permet de collecter toutes les tâches définies dans le code
    pour les ajouter automatiquement au scheduler.
    """
    
    def __init__(self):
        self._tasks: Dict[str, TaskConfig] = {}
        self.logger = get_default_logger()
    
    def register(self, task_config: TaskConfig, func: Callable):
        """Enregistre une tâche"""
        if task_config.name in self._tasks:
            self.logger.warning(f"Tâche '{task_config.name}' redéfinie")
        
        # Stocker la fonction aussi pour référence
        task_config.metadata['_function_ref'] = func
        task_config.metadata['_function_info'] = get_function_info(func)
        
        self._tasks[task_config.name] = task_config
        self.logger.debug(f"Tâche '{task_config.name}' enregistrée")
    
    def get_all_tasks(self) -> List[TaskConfig]:
        """Retourne toutes les tâches enregistrées"""
        return list(self._tasks.values())
    
    def get_task(self, name: str) -> Optional[TaskConfig]:
        """Retourne une tâche par nom"""
        return self._tasks.get(name)
    
    def clear(self):
        """Vide le registre"""
        self._tasks.clear()
        self.logger.debug("Registre des tâches vidé")


# Instance globale du registre
_task_registry = TaskRegistry()


def get_task_registry() -> TaskRegistry:
    """Retourne le registre global des tâches"""
    return _task_registry


def schedule_task(
    # Méthodes de planification (exclusives)
    interval: Optional[Union[int, float, str]] = None,
    cron: Optional[str] = None,
    daily_at: Optional[str] = None,
    weekly_at: Optional[Tuple[int, str]] = None,
    once_at: Optional[Union[str, datetime]] = None,
    on_startup: bool = False,
    on_shutdown: bool = False,
    
    # Configuration générale
    name: Optional[str] = None,
    enabled: bool = True,
    priority: Union[str, Priority] = Priority.NORMAL,
    timeout: Optional[Union[int, float, str]] = None,
    max_runs: Optional[int] = None,
    
    # Configuration retry
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    max_delay: Union[int, float, str] = 300,
    
    # Métadonnées
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Décorateur pour planifier une tâche
    
    Exemples d'utilisation:
    
        @schedule_task(interval=60)
        def task_every_minute():
            print("Exécuté chaque minute")
        
        @schedule_task(cron="0 9 * * 1-5")
        def weekday_morning():
            print("Lundi à vendredi à 9h")
        
        @schedule_task(daily_at="14:30", priority="high")
        def afternoon_report():
            print("Rapport de 14h30")
        
        @schedule_task(weekly_at=(1, "09:00"))  # Mardi à 9h
        def weekly_task():
            print("Chaque mardi à 9h")
        
        @schedule_task(once_at="2025-12-25 00:00:00")
        def christmas_task():
            print("Joyeux Noël!")
        
        @schedule_task(on_startup=True)
        def startup_task():
            print("Exécuté au démarrage")
    
    Args:
        interval: Intervalle en secondes (ou chaîne parsable comme "5m")
        cron: Expression cron standard
        daily_at: Heure quotidienne au format "HH:MM"
        weekly_at: Tuple (jour_semaine, "HH:MM") où jour_semaine = 0-6
        once_at: Date/heure d'exécution unique
        on_startup: Exécuter au démarrage du scheduler
        on_shutdown: Exécuter à l'arrêt du scheduler
        name: Nom de la tâche (par défaut: nom de la fonction)
        enabled: Tâche activée
        priority: Priorité (critical, high, normal, low, idle)
        timeout: Timeout d'exécution
        max_runs: Nombre maximum d'exécutions
        max_attempts: Nombre max de tentatives en cas d'échec
        backoff_factor: Facteur de délai exponentiel pour les retries
        max_delay: Délai maximum entre les retries
        tags: Tags pour catégoriser la tâche
        metadata: Métadonnées additionnelles
    
    Returns:
        Fonction décorée
        
    Raises:
        ValidationError: Si la configuration est invalide
    """
    
    def decorator(func: Callable) -> Callable:
        # Déterminer le type et la valeur de planification
        schedule_type, schedule_value = _determine_schedule(
            interval, cron, daily_at, weekly_at, once_at, on_startup, on_shutdown
        )
        
        # Générer un nom si non fourni
        task_name = name or f"{func.__module__}.{func.__name__}"
        
        # Convertir priority en enum si nécessaire
        task_priority = priority
        if isinstance(priority, str):
            try:
                task_priority = Priority[priority.upper()]
            except KeyError:
                raise ValidationError(f"Priorité invalide: {priority}")
        
        # Parser timeout si fourni
        task_timeout = None
        if timeout is not None:
            task_timeout = parse_duration(timeout)
        
        # Parser max_delay
        parsed_max_delay = parse_duration(max_delay)
        
        # Créer la configuration retry
        retry_config = RetryConfig(
            max_attempts=max_attempts,
            backoff_factor=backoff_factor,
            max_delay=parsed_max_delay
        )
        
        # Créer la configuration de tâche
        task_config = TaskConfig(
            name=task_name,
            function=func.__name__,
            module=func.__module__,
            schedule_type=schedule_type,
            schedule_value=schedule_value,
            enabled=enabled,
            priority=task_priority,
            timeout=task_timeout,
            max_runs=max_runs,
            retry_config=retry_config,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Enregistrer dans le registre global
        _task_registry.register(task_config, func)
        
        # Ajouter des métadonnées à la fonction
        func._pyscheduler_config = task_config
        func._pyscheduler_registered = True
        
        return func
    
    return decorator


def _determine_schedule(
    interval, cron, daily_at, weekly_at, once_at, on_startup, on_shutdown
) -> Tuple[ScheduleType, Any]:
    """
    Détermine le type et la valeur de planification
    
    Returns:
        Tuple (ScheduleType, schedule_value)
        
    Raises:
        ValidationError: Si la configuration est ambiguë ou invalide
    """
    # Compter les méthodes de planification spécifiées
    methods = [
        (interval is not None, "interval"),
        (cron is not None, "cron"), 
        (daily_at is not None, "daily_at"),
        (weekly_at is not None, "weekly_at"),
        (once_at is not None, "once_at"),
        (on_startup, "on_startup"),
        (on_shutdown, "on_shutdown")
    ]
    
    specified_methods = [method for specified, method in methods if specified]
    
    if len(specified_methods) == 0:
        raise ValidationError(
            "Au moins une méthode de planification doit être spécifiée: "
            "interval, cron, daily_at, weekly_at, once_at, on_startup, on_shutdown"
        )
    
    if len(specified_methods) > 1:
        raise ValidationError(
            f"Une seule méthode de planification autorisée. Spécifiées: {specified_methods}"
        )
    
    # Traiter selon la méthode choisie
    if interval is not None:
        parsed_interval = parse_duration(interval)
        return ScheduleType.INTERVAL, parsed_interval
    
    elif cron is not None:
        validate_cron_expression(cron)
        return ScheduleType.CRON, cron
    
    elif daily_at is not None:
        validate_time_string(daily_at)
        return ScheduleType.DAILY, daily_at
    
    elif weekly_at is not None:
        if not isinstance(weekly_at, (list, tuple)) or len(weekly_at) != 2:
            raise ValidationError("weekly_at doit être un tuple (jour_semaine, 'HH:MM')")
        
        day, time = weekly_at
        if not isinstance(day, int) or not (0 <= day <= 6):
            raise ValidationError("Jour de la semaine doit être 0-6 (0=dimanche)")
        
        validate_time_string(time)
        return ScheduleType.WEEKLY, weekly_at
    
    elif once_at is not None:
        parsed_datetime = ensure_datetime(once_at)
        return ScheduleType.ONCE, parsed_datetime
    
    elif on_startup:
        return ScheduleType.STARTUP, None
    
    elif on_shutdown:
        return ScheduleType.SHUTDOWN, None


def task(
    schedule: Union[str, int, float],
    **kwargs
):
    """
    Décorateur simplifié pour planifier une tâche
    
    Auto-détecte le type de planification basé sur le format:
    - Nombre: intervalle en secondes
    - "5m", "2h", "1d": intervalle parsé
    - "HH:MM": quotidien
    - Expression avec 5 parties: cron
    
    Exemples:
        @task(60)  # Toutes les 60 secondes
        def task1(): pass
        
        @task("5m")  # Toutes les 5 minutes
        def task2(): pass
        
        @task("09:30")  # Tous les jours à 9h30
        def task3(): pass
        
        @task("0 */2 * * *")  # Toutes les 2 heures (cron)
        def task4(): pass
    
    Args:
        schedule: Planification (auto-détectée)
        **kwargs: Autres paramètres pour schedule_task
    
    Returns:
        Fonction décorée
    """
    
    def decorator(func: Callable) -> Callable:
        # Auto-détection du type de planification
        if isinstance(schedule, (int, float)):
            # Intervalle en secondes
            return schedule_task(interval=schedule, **kwargs)(func)
        
        elif isinstance(schedule, str):
            schedule_str = schedule.strip()
            
            # Format HH:MM (quotidien)
            if ":" in schedule_str and len(schedule_str.split()) == 1:
                try:
                    validate_time_string(schedule_str)
                    return schedule_task(daily_at=schedule_str, **kwargs)(func)
                except ValidationError:
                    pass
            
            # Expression cron (5 parties)
            if len(schedule_str.split()) == 5:
                try:
                    validate_cron_expression(schedule_str)
                    return schedule_task(cron=schedule_str, **kwargs)(func)
                except ValidationError:
                    pass
            
            # Intervalle parsable (5m, 2h, etc.)
            try:
                return schedule_task(interval=schedule_str, **kwargs)(func)
            except ValidationError:
                pass
            
            # Si rien ne marche, erreur
            raise ValidationError(
                f"Format de planification non reconnu: {schedule}. "
                "Utilisez un nombre (secondes), 'HH:MM' (quotidien), "
                "expression cron, ou chaîne d'intervalle ('5m', '2h', etc.)"
            )
        
        else:
            raise ValidationError(f"Type de planification non supporté: {type(schedule)}")
    
    return decorator


def every(
    seconds: Optional[Union[int, float]] = None,
    minutes: Optional[Union[int, float]] = None,
    hours: Optional[Union[int, float]] = None,
    days: Optional[Union[int, float]] = None,
    **kwargs
):
    """
    Décorateur pour planification d'intervalle lisible
    
    Exemples:
        @every(seconds=30)
        def task1(): pass
        
        @every(minutes=5)
        def task2(): pass
        
        @every(hours=2, minutes=30)  # Toutes les 2h30
        def task3(): pass
        
        @every(days=1)  # Quotidien
        def task4(): pass
    
    Args:
        seconds: Nombre de secondes
        minutes: Nombre de minutes
        hours: Nombre d'heures
        days: Nombre de jours
        **kwargs: Autres paramètres pour schedule_task
    
    Returns:
        Fonction décorée
    """
    
    def decorator(func: Callable) -> Callable:
        # Calculer l'intervalle total en secondes
        total_seconds = 0
        
        if seconds is not None:
            total_seconds += seconds
        if minutes is not None:
            total_seconds += minutes * 60
        if hours is not None:
            total_seconds += hours * 3600
        if days is not None:
            total_seconds += days * 86400
        
        if total_seconds <= 0:
            raise ValidationError(
                "Au moins une unité de temps doit être spécifiée et positive"
            )
        
        return schedule_task(interval=total_seconds, **kwargs)(func)
    
    return decorator


def daily(time: str, **kwargs):
    """
    Décorateur pour planification quotidienne
    
    Exemple:
        @daily("09:30")
        def morning_task(): pass
    
    Args:
        time: Heure au format "HH:MM"
        **kwargs: Autres paramètres pour schedule_task
    """
    return schedule_task(daily_at=time, **kwargs)


def weekly(day: int, time: str, **kwargs):
    """
    Décorateur pour planification hebdomadaire
    
    Exemple:
        @weekly(1, "09:00")  # Mardi à 9h
        def weekly_task(): pass
    
    Args:
        day: Jour de la semaine (0=dimanche, 1=lundi, ..., 6=samedi)
        time: Heure au format "HH:MM"
        **kwargs: Autres paramètres pour schedule_task
    """
    return schedule_task(weekly_at=(day, time), **kwargs)


def once(when: Union[str, datetime], **kwargs):
    """
    Décorateur pour exécution unique
    
    Exemple:
        @once("2025-12-25 00:00:00")
        def christmas_task(): pass
    
    Args:
        when: Date/heure d'exécution
        **kwargs: Autres paramètres pour schedule_task
    """
    return schedule_task(once_at=when, **kwargs)


def startup(**kwargs):
    """
    Décorateur pour tâche de démarrage
    
    Exemple:
        @startup()
        def init_task(): pass
    
    Args:
        **kwargs: Autres paramètres pour schedule_task
    """
    return schedule_task(on_startup=True, **kwargs)


def shutdown(**kwargs):
    """
    Décorateur pour tâche d'arrêt
    
    Exemple:
        @shutdown()
        def cleanup_task(): pass
    
    Args:
        **kwargs: Autres paramètres pour schedule_task
    """
    return schedule_task(on_shutdown=True, **kwargs)


def high_priority(**schedule_kwargs):
    """Décorateur pour tâche haute priorité"""
    return schedule_task(priority=Priority.HIGH, **schedule_kwargs)


def low_priority(**schedule_kwargs):
    """Décorateur pour tâche basse priorité"""
    return schedule_task(priority=Priority.LOW, **schedule_kwargs)


def critical(**schedule_kwargs):
    """Décorateur pour tâche critique"""
    return schedule_task(priority=Priority.CRITICAL, **schedule_kwargs)