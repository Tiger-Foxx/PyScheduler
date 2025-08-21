"""
PyScheduler - Task Core
=======================

Classe Task représentant une tâche planifiée avec toute sa logique.
Utilise massivement nos utilitaires pour éviter la duplication.
"""

import asyncio
import inspect
import threading
import time
import traceback
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field
from enum import Enum

# Import de nos utilitaires (cohérence!)
from ..utils import (
    TaskError, ExecutionError, ValidationError,
    get_default_logger, safe_call, get_function_info,
    format_duration
)
from ..config import ScheduleType, Priority, RetryConfig


class TaskStatus(Enum):
    """États d'une tâche"""
    PENDING = "pending"         # En attente
    RUNNING = "running"         # En cours d'exécution
    SUCCESS = "success"         # Succès
    FAILED = "failed"          # Échec
    CANCELLED = "cancelled"     # Annulée
    PAUSED = "paused"          # En pause
    EXPIRED = "expired"        # Expirée
    TIMEOUT = "timeout"        # Timeout


@dataclass
class TaskExecution:
    """Résultat d'une exécution de tâche"""
    task_name: str
    execution_id: str
    status: TaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    result: Any = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    attempt: int = 1
    
    @property
    def is_finished(self) -> bool:
        """Vrai si l'exécution est terminée"""
        return self.status in [
            TaskStatus.SUCCESS, TaskStatus.FAILED, 
            TaskStatus.CANCELLED, TaskStatus.TIMEOUT
        ]
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire"""
        return {
            'task_name': self.task_name,
            'execution_id': self.execution_id,
            'status': self.status.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'result': str(self.result) if self.result is not None else None,
            'error': self.error,
            'traceback': self.traceback,
            'attempt': self.attempt
        }


@dataclass
class TaskStats:
    """Statistiques d'une tâche"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    avg_duration: float = 0.0
    last_execution: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    
    def update(self, execution: TaskExecution):
        """Met à jour les statistiques avec une nouvelle exécution"""
        if not execution.is_finished:
            return
        
        self.total_executions += 1
        self.total_duration += execution.duration
        self.last_execution = execution.end_time or execution.start_time
        
        # Durée min/max/moyenne
        if execution.duration > 0:
            self.min_duration = min(self.min_duration, execution.duration)
            self.max_duration = max(self.max_duration, execution.duration)
            self.avg_duration = self.total_duration / self.total_executions
        
        # Compteurs par statut
        if execution.status == TaskStatus.SUCCESS:
            self.successful_executions += 1
            self.last_success = execution.end_time
        elif execution.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT]:
            self.failed_executions += 1
            self.last_failure = execution.end_time
    
    @property
    def success_rate(self) -> float:
        """Taux de succès (0.0 à 1.0)"""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire"""
        return {
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': round(self.success_rate * 100, 2),
            'total_duration': round(self.total_duration, 2),
            'min_duration': round(self.min_duration if self.min_duration != float('inf') else 0, 2),
            'max_duration': round(self.max_duration, 2),
            'avg_duration': round(self.avg_duration, 2),
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'last_success': self.last_success.isoformat() if self.last_success else None,
            'last_failure': self.last_failure.isoformat() if self.last_failure else None
        }


class Task:
    """
    Représente une tâche planifiée avec sa logique d'exécution
    
    Cette classe encapsule :
    - La fonction à exécuter
    - La configuration de planification  
    - L'état d'exécution
    - Les statistiques
    - La logique de retry
    """
    
    def __init__(
        self,
        name: str,
        func: Callable,
        schedule_type: ScheduleType,
        schedule_value: Any,
        module_path: Optional[str] = None,
        enabled: bool = True,
        priority: Priority = Priority.NORMAL,
        timeout: Optional[float] = None,
        max_runs: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        retry_config: Optional[RetryConfig] = None,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialise une tâche
        
        Args:
            name: Nom unique de la tâche
            func: Fonction à exécuter
            schedule_type: Type de planification
            schedule_value: Valeur de planification
            module_path: Chemin du module (pour sérialisation)
            enabled: Tâche activée
            priority: Priorité d'exécution
            timeout: Timeout d'exécution en secondes
            max_runs: Nombre maximum d'exécutions
            start_time: Date de début de validité
            end_time: Date de fin de validité
            retry_config: Configuration des tentatives
            tags: Tags pour catégorisation
            metadata: Métadonnées additionnelles
        """
        # Configuration de base
        self.name = name
        self.func = func
        self.schedule_type = schedule_type
        self.schedule_value = schedule_value
        self.module_path = module_path
        self.enabled = enabled
        self.priority = priority
        self.timeout = timeout
        self.max_runs = max_runs
        self.start_time = start_time or datetime.now()
        self.end_time = end_time
        self.retry_config = retry_config or RetryConfig()
        self.tags = tags or set()
        self.metadata = metadata or {}
        
        # État d'exécution
        self._lock = threading.RLock()
        self._is_running = False
        self._is_cancelled = False
        self._run_count = 0
        self._last_execution_id = 0
        self._current_execution: Optional[TaskExecution] = None
        
        # Statistiques et historique
        self.stats = TaskStats()
        self._execution_history: List[TaskExecution] = []
        
        # Logger
        self.logger = get_default_logger()
        
        # Planification
        self.next_run_time: Optional[datetime] = None
        self._calculate_next_run()
        
        
        # Informations sur la fonction
        self._function_info = get_function_info(func)
        
        # Validation initiale
        self._validate()
    
    def _validate(self):
        """Valide la configuration de la tâche"""
        if not self.name:
            raise ValidationError("Le nom de la tâche ne peut pas être vide")
        
        if not callable(self.func):
            raise ValidationError("func doit être une fonction callable")
        
        if self.timeout is not None and self.timeout <= 0:
            raise ValidationError("timeout doit être positif")
        
        if self.max_runs is not None and self.max_runs <= 0:
            raise ValidationError("max_runs doit être positif")
        
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError("end_time doit être après start_time")
    
    def _calculate_next_run(self):
        """Calcule la prochaine exécution selon le type de planification"""
        if not self.enabled or self._is_cancelled:
            self.next_run_time = None
            return
        
        # Vérifier si on a atteint le maximum d'exécutions
        if self.max_runs and self._run_count >= self.max_runs:
            self.next_run_time = None
            self.logger.debug(f"Tâche '{self.name}' : maximum d'exécutions atteint")
            return
        
        # Vérifier si on est dans la période de validité
        now = datetime.now()
        if now < self.start_time:
            self.next_run_time = self.start_time
            return
        
        if self.end_time and now > self.end_time:
            self.next_run_time = None
            self.logger.debug(f"Tâche '{self.name}' : période de validité expirée")
            return
        
        # Calcul selon le type de planification
        from .triggers import TriggerFactory  # Import local pour éviter la circularité
        
        trigger = TriggerFactory.create_trigger(self.schedule_type, self.schedule_value)
        self.next_run_time = trigger.get_next_run_time(self._get_last_run_time())
        
        if self.next_run_time:
            self.logger.debug(
                f"Tâche '{self.name}' : prochaine exécution à {self.next_run_time}"
            )
    
    def _get_last_run_time(self) -> Optional[datetime]:
        """Retourne la date de dernière exécution"""
        if self._execution_history:
            return self._execution_history[-1].start_time
        return None
    
    def should_run(self, current_time: Optional[datetime] = None) -> bool:
        """
        Détermine si la tâche doit s'exécuter maintenant
        
        Args:
            current_time: Heure actuelle (par défaut: datetime.now())
            
        Returns:
            True si la tâche doit s'exécuter
        """
        if not self.enabled or self._is_cancelled or self._is_running:
            return False
        
        if not self.next_run_time:
            return False
        
        current_time = current_time or datetime.now()
        return current_time >= self.next_run_time
    
    async def execute(self) -> TaskExecution:
        """
        Exécute la tâche avec gestion complète des erreurs et retry
        
        Returns:
            Résultat de l'exécution
        """
        if self._is_running:
            raise TaskError(f"Tâche '{self.name}' déjà en cours d'exécution")
        
        if not self.enabled:
            raise TaskError(f"Tâche '{self.name}' désactivée")
        
        if self._is_cancelled:
            raise TaskError(f"Tâche '{self.name}' annulée")
        
        # Préparer l'exécution
        with self._lock:
            self._is_running = True
            self._run_count += 1
            self._last_execution_id += 1
            execution_id = f"{self.name}_{self._last_execution_id}"
        
        execution = TaskExecution(
            task_name=self.name,
            execution_id=execution_id,
            status=TaskStatus.RUNNING,
            start_time=datetime.now()
        )
        
        self._current_execution = execution
        self.logger.task_started(self.name, execution_id=execution_id)
        
        try:
            # Exécution avec retry
            result = await self._execute_with_retry(execution)
            execution.result = result
            execution.status = TaskStatus.SUCCESS
            
            # Calculer la prochaine exécution
            self._calculate_next_run()
            
            self.logger.task_completed(
                self.name, 
                execution.duration,
                execution_id=execution_id,
                result=str(result)[:100] if result else None
            )
            
        except asyncio.TimeoutError:
            execution.status = TaskStatus.TIMEOUT
            execution.error = f"Timeout après {self.timeout}s"
            self.logger.task_failed(self.name, execution.error, execution_id=execution_id)
            
        except Exception as e:
            execution.status = TaskStatus.FAILED
            execution.error = str(e)
            execution.traceback = traceback.format_exc()
            self.logger.task_failed(self.name, execution.error, execution_id=execution_id)
            
        finally:
            # Finaliser l'exécution
            execution.end_time = datetime.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            
            with self._lock:
                self._is_running = False
                self._current_execution = None
                
                # Mettre à jour l'historique et les stats
                self._execution_history.append(execution)
                self.stats.update(execution)
                
                # Limiter l'historique pour éviter la consommation mémoire
                if len(self._execution_history) > 100:
                    self._execution_history = self._execution_history[-50:]
        
        return execution
    
    async def _execute_with_retry(self, execution: TaskExecution) -> Any:
        """
        Exécute la fonction avec logique de retry
        
        Args:
            execution: Objet d'exécution à mettre à jour
            
        Returns:
            Résultat de la fonction
            
        Raises:
            Exception: Dernière exception après épuisement des tentatives
        """
        last_exception = None
        
        for attempt in range(1, self.retry_config.max_attempts + 1):
            execution.attempt = attempt
            
            try:
                # Exécution avec timeout si configuré
                if self.timeout:
                    result = await asyncio.wait_for(
                        self._call_function(),
                        timeout=self.timeout
                    )
                else:
                    result = await self._call_function()
                
                # Succès !
                if attempt > 1:
                    self.logger.info(
                        f"Tâche '{self.name}' réussie à la tentative {attempt}",
                        execution_id=execution.execution_id
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Si c'est la dernière tentative, on lève l'exception
                if attempt >= self.retry_config.max_attempts:
                    break
                
                # Calculer le délai avant retry
                delay = min(
                    self.retry_config.backoff_factor ** (attempt - 1),
                    self.retry_config.max_delay
                )
                
                self.logger.warning(
                    f"Tâche '{self.name}' échouée (tentative {attempt}/{self.retry_config.max_attempts}). "
                    f"Retry dans {format_duration(delay)}",
                    execution_id=execution.execution_id,
                    error=str(e)
                )
                
                # Attendre avant retry
                await asyncio.sleep(delay)
        
        # Toutes les tentatives ont échoué
        raise ExecutionError(
            f"Tâche '{self.name}' échouée après {self.retry_config.max_attempts} tentatives",
            {"last_error": str(last_exception)}
        )
    
    async def _call_function(self) -> Any:
        """
        Appelle la fonction de la tâche de manière appropriée
        
        Returns:
            Résultat de la fonction
        """
        if self._function_info['is_async']:
            # Fonction asynchrone
            return await self.func()
        else:
            # Fonction synchrone - exécuter dans un thread
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.func)
    
    def cancel(self):
        """Annule la tâche"""
        with self._lock:
            self._is_cancelled = True
            self.next_run_time = None
        
        self.logger.info(f"Tâche '{self.name}' annulée")
    
    def pause(self):
        """Met en pause la tâche"""
        with self._lock:
            self.enabled = False
            self.next_run_time = None
        
        self.logger.info(f"Tâche '{self.name}' mise en pause")
    
    def resume(self):
        """Reprend l'exécution de la tâche"""
        with self._lock:
            if not self._is_cancelled:
                self.enabled = True
                self._calculate_next_run()
        
        self.logger.info(f"Tâche '{self.name}' reprise")
    
    def reset_stats(self):
        """Remet à zéro les statistiques"""
        with self._lock:
            self.stats = TaskStats()
            self._execution_history.clear()
        
        self.logger.debug(f"Statistiques de la tâche '{self.name}' remises à zéro")
    
    def get_recent_executions(self, limit: int = 10) -> List[TaskExecution]:
        """
        Retourne les exécutions récentes
        
        Args:
            limit: Nombre maximum d'exécutions à retourner
            
        Returns:
            Liste des exécutions récentes
        """
        with self._lock:
            return self._execution_history[-limit:] if self._execution_history else []
    
    @property
    def is_running(self) -> bool:
        """True si la tâche est en cours d'exécution"""
        return self._is_running
    
    @property
    def is_cancelled(self) -> bool:
        """True si la tâche est annulée"""
        return self._is_cancelled
    
    @property
    def run_count(self) -> int:
        """Nombre d'exécutions effectuées"""
        return self._run_count
    
    @property
    def current_execution(self) -> Optional[TaskExecution]:
        """Exécution en cours (si applicable)"""
        return self._current_execution
    
    def to_dict(self) -> dict:
        """
        Convertit la tâche en dictionnaire pour sérialisation
        
        Returns:
            Dictionnaire représentant la tâche
        """
        return {
            'name': self.name,
            'schedule_type': self.schedule_type.value,
            'schedule_value': str(self.schedule_value),
            'module_path': self.module_path,
            'function_name': self._function_info['name'],
            'enabled': self.enabled,
            'priority': self.priority.value,
            'timeout': self.timeout,
            'max_runs': self.max_runs,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'next_run_time': self.next_run_time.isoformat() if self.next_run_time else None,
            'is_running': self.is_running,
            'is_cancelled': self.is_cancelled,
            'run_count': self.run_count,
            'tags': list(self.tags),
            'metadata': self.metadata,
            'stats': self.stats.to_dict(),
            'function_info': self._function_info,
            'retry_config': {
                'max_attempts': self.retry_config.max_attempts,
                'backoff_factor': self.retry_config.backoff_factor,
                'max_delay': self.retry_config.max_delay
            }
        }
    
    def __str__(self) -> str:
        """Représentation en chaîne de la tâche"""
        status = "Running" if self.is_running else "Cancelled" if self.is_cancelled else "Enabled" if self.enabled else "Disabled"
        next_run = self.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if self.next_run_time else "Never"
        
        return (
            f"Task(name='{self.name}', status={status}, "
            f"type={self.schedule_type.value}, next_run={next_run}, "
            f"runs={self.run_count}, success_rate={self.stats.success_rate:.1%})"
        )
    
    def __repr__(self) -> str:
        return self.__str__()