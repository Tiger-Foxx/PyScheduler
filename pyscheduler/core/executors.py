"""
PyScheduler - Executors Core
============================

Système d'exécution des tâches avec support multi-threading, async et gestion des priorités.
Gère l'orchestration et la distribution des tâches selon leur configuration.
"""

import asyncio
import threading
import time
import uuid
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime
from enum import Enum
from queue import PriorityQueue, Queue, Empty
from typing import Any, Callable, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field

# Import de nos utilitaires (cohérence!)
from ..utils import (
    ExecutionError, TaskError, get_default_logger,
    safe_call, format_duration
)
from ..config import Priority
from .task import Task, TaskExecution, TaskStatus


class ExecutorType(Enum):
    """Types d'exécuteurs disponibles"""
    THREAD = "thread"           # Exécution dans des threads
    PROCESS = "process"         # Exécution dans des processus
    ASYNC = "async"            # Exécution asynchrone
    IMMEDIATE = "immediate"     # Exécution immédiate (blocking)


@dataclass
class ExecutionRequest:
    """Demande d'exécution d'une tâche"""
    task: Task
    priority: Priority
    request_time: datetime = field(default_factory=datetime.now)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    def __lt__(self, other):
        """Comparaison pour PriorityQueue (priorité plus basse = plus important)"""
        return self.priority.value < other.priority.value


@dataclass
class ExecutorStats:
    """Statistiques d'un exécuteur"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_duration: float = 0.0
    active_tasks: int = 0
    queue_size: int = 0
    avg_duration: float = 0.0
    
    def update_execution(self, execution: TaskExecution):
        """Met à jour les stats avec une exécution"""
        self.total_executions += 1
        self.total_duration += execution.duration
        self.avg_duration = self.total_duration / self.total_executions
        
        if execution.status == TaskStatus.SUCCESS:
            self.successful_executions += 1
        elif execution.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT]:
            self.failed_executions += 1
    
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
            'avg_duration': round(self.avg_duration, 2),
            'active_tasks': self.active_tasks,
            'queue_size': self.queue_size
        }


class BaseExecutor(ABC):
    """
    Classe de base pour tous les exécuteurs
    
    Un exécuteur gère l'exécution des tâches selon une stratégie spécifique
    (threads, processus, async, etc.)
    """
    
    def __init__(self, max_workers: int = 10, name: Optional[str] = None):
        """
        Initialise l'exécuteur
        
        Args:
            max_workers: Nombre maximum de workers simultanés
            name: Nom de l'exécuteur (pour logging)
        """
        self.max_workers = max_workers
        self.name = name or self.__class__.__name__
        self.logger = get_default_logger()
        
        # État
        self._running = False
        self._stopping = False
        self._lock = threading.RLock()
        
        # Queue des tâches à exécuter
        self._task_queue = PriorityQueue()
        self._active_tasks: Dict[str, Task] = {}
        
        # Statistiques
        self.stats = ExecutorStats()
        
        # Callbacks
        self._on_task_start: Optional[Callable] = None
        self._on_task_complete: Optional[Callable] = None
        self._on_task_error: Optional[Callable] = None
    
    @abstractmethod
    async def _execute_task(self, task: Task) -> TaskExecution:
        """
        Exécute une tâche spécifique à l'implémentation
        
        Args:
            task: Tâche à exécuter
            
        Returns:
            Résultat de l'exécution
        """
        pass
    
    @abstractmethod
    def start(self):
        """Démarre l'exécuteur"""
        pass
    
    @abstractmethod
    def stop(self, timeout: float = 30.0):
        """Arrête l'exécuteur proprement"""
        pass
    
    def submit_task(self, task: Task, priority: Optional[Priority] = None) -> str:
        """
        Soumet une tâche pour exécution
        
        Args:
            task: Tâche à exécuter
            priority: Priorité (par défaut: priorité de la tâche)
            
        Returns:
            ID de la demande d'exécution
            
        Raises:
            ExecutionError: Si l'exécuteur n'est pas démarré
        """
        if not self._running:
            raise ExecutionError("L'exécuteur n'est pas démarré")
        
        if self._stopping:
            raise ExecutionError("L'exécuteur est en cours d'arrêt")
        
        # Utiliser la priorité de la tâche si non spécifiée
        task_priority = priority or task.priority
        
        # Créer la demande d'exécution
        request = ExecutionRequest(task=task, priority=task_priority)
        
        # Ajouter à la queue
        self._task_queue.put(request)
        
        with self._lock:
            self.stats.queue_size = self._task_queue.qsize()
        
        self.logger.debug(
            f"Tâche '{task.name}' soumise à l'exécuteur {self.name}",
            request_id=request.request_id,
            priority=task_priority.name
        )
        
        return request.request_id
    
    def get_active_tasks(self) -> List[str]:
        """Retourne la liste des tâches en cours d'exécution"""
        with self._lock:
            return list(self._active_tasks.keys())
    
    def get_queue_size(self) -> int:
        """Retourne la taille de la queue"""
        return self._task_queue.qsize()
    
    def is_running(self) -> bool:
        """Vérifie si l'exécuteur est en marche"""
        return self._running
    
    def set_callbacks(
        self, 
        on_start: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ):
        """
        Configure les callbacks d'événements
        
        Args:
            on_start: Callback appelé au début d'exécution (task, execution)
            on_complete: Callback appelé à la fin d'exécution (task, execution)
            on_error: Callback appelé en cas d'erreur (task, execution, error)
        """
        self._on_task_start = on_start
        self._on_task_complete = on_complete
        self._on_task_error = on_error
    
    async def _handle_task_execution(self, request: ExecutionRequest):
        """
        Gère l'exécution complète d'une tâche avec callbacks
        
        Args:
            request: Demande d'exécution
        """
        task = request.task
        
        # Marquer comme active
        with self._lock:
            self._active_tasks[task.name] = task
            self.stats.active_tasks = len(self._active_tasks)
        
        try:
            # Callback de début
            if self._on_task_start:
                try:
                    await self._call_callback(self._on_task_start, task, None)
                except Exception as e:
                    self.logger.warning(f"Erreur callback start: {e}")
            
            # Exécution de la tâche
            execution = await self._execute_task(task)
            
            # Mettre à jour les stats
            with self._lock:
                self.stats.update_execution(execution)
            
            # Callback de fin
            if self._on_task_complete:
                try:
                    await self._call_callback(self._on_task_complete, task, execution)
                except Exception as e:
                    self.logger.warning(f"Erreur callback complete: {e}")
            
            # Callback d'erreur si échec
            if execution.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT] and self._on_task_error:
                try:
                    await self._call_callback(self._on_task_error, task, execution, execution.error)
                except Exception as e:
                    self.logger.warning(f"Erreur callback error: {e}")
            
            return execution
            
        except Exception as e:
            # Erreur inattendue dans l'exécuteur lui-même
            self.logger.error(f"Erreur exécuteur lors de l'exécution de '{task.name}': {e}")
            
            # Créer un résultat d'erreur
            error_execution = TaskExecution(
                task_name=task.name,
                execution_id=f"error_{request.request_id}",
                status=TaskStatus.FAILED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                error=f"Erreur exécuteur: {e}"
            )
            
            with self._lock:
                self.stats.update_execution(error_execution)
            
            return error_execution
            
        finally:
            # Retirer des tâches actives
            with self._lock:
                self._active_tasks.pop(task.name, None)
                self.stats.active_tasks = len(self._active_tasks)
                self.stats.queue_size = self._task_queue.qsize()
    
    async def _call_callback(self, callback: Callable, *args):
        """Appelle un callback de manière sécurisée"""
        if asyncio.iscoroutinefunction(callback):
            await callback(*args)
        else:
            # Exécuter dans un thread pour ne pas bloquer
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, callback, *args)
    
    def get_stats(self) -> dict:
        """Retourne les statistiques de l'exécuteur"""
        with self._lock:
            stats_dict = self.stats.to_dict()
            stats_dict.update({
                'name': self.name,
                'type': self.__class__.__name__,
                'max_workers': self.max_workers,
                'is_running': self._running,
                'is_stopping': self._stopping
            })
            return stats_dict


class ThreadExecutor(BaseExecutor):
    """
    Exécuteur basé sur ThreadPoolExecutor
    
    Idéal pour les tâches I/O bound et la plupart des cas d'usage.
    """
    
    def __init__(self, max_workers: int = 10, name: Optional[str] = None):
        super().__init__(max_workers, name or "ThreadExecutor")
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._worker_tasks: Set[asyncio.Task] = set()
    
    def start(self):
        """Démarre l'exécuteur avec pool de threads"""
        if self._running:
            self.logger.warning(f"Exécuteur {self.name} déjà démarré")
            return
        
        self._running = True
        self._stopping = False
        
        # Créer le pool de threads
        self._thread_pool = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix=f"PyScheduler-{self.name}"
        )
        
        # Démarrer les workers async
        loop = asyncio.get_event_loop()
        for i in range(min(self.max_workers, 5)):  # Limiter les workers async
            worker_task = loop.create_task(self._worker_loop(f"worker-{i}"))
            self._worker_tasks.add(worker_task)
        
        self.logger.info(f"Exécuteur {self.name} démarré avec {self.max_workers} threads")
    
    def stop(self, timeout: float = 30.0):
        """Arrête l'exécuteur proprement"""
        if not self._running:
            return
        
        self.logger.info(f"Arrêt de l'exécuteur {self.name}...")
        self._stopping = True
        
        # Arrêter les workers
        for task in self._worker_tasks:
            task.cancel()
        
        # Attendre la fin des workers
        if self._worker_tasks:
            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(
                    asyncio.wait_for(
                        asyncio.gather(*self._worker_tasks, return_exceptions=True),
                        timeout=timeout / 2
                    )
                )
            except asyncio.TimeoutError:
                self.logger.warning("Timeout lors de l'arrêt des workers")
        
        # Arrêter le pool de threads
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True, timeout=timeout / 2)
            self._thread_pool = None
        
        self._running = False
        self.logger.info(f"Exécuteur {self.name} arrêté")
    
    async def _worker_loop(self, worker_name: str):
        """
        Boucle principale d'un worker
        
        Args:
            worker_name: Nom du worker pour logging
        """
        self.logger.debug(f"Worker {worker_name} démarré")
        
        while self._running and not self._stopping:
            try:
                # Récupérer une tâche de la queue (avec timeout)
                try:
                    request = self._task_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # Exécuter la tâche
                await self._handle_task_execution(request)
                
                # Marquer comme terminée
                self._task_queue.task_done()
                
            except asyncio.CancelledError:
                self.logger.debug(f"Worker {worker_name} annulé")
                break
            except Exception as e:
                self.logger.error(f"Erreur dans worker {worker_name}: {e}")
                await asyncio.sleep(1)  # Éviter les boucles d'erreur
        
        self.logger.debug(f"Worker {worker_name} arrêté")
    
    async def _execute_task(self, task: Task) -> TaskExecution:
        """Exécute une tâche dans le pool de threads"""
        if not self._thread_pool:
            raise ExecutionError("Pool de threads non initialisé")
        
        # Déléguer à la méthode execute de la tâche
        return await task.execute()


class AsyncExecutor(BaseExecutor):
    """
    Exécuteur asynchrone natif
    
    Idéal pour les tâches async et les opérations non-bloquantes.
    """
    
    def __init__(self, max_workers: int = 50, name: Optional[str] = None):
        super().__init__(max_workers, name or "AsyncExecutor")
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._worker_tasks: Set[asyncio.Task] = set()
    
    def start(self):
        """Démarre l'exécuteur async"""
        if self._running:
            self.logger.warning(f"Exécuteur {self.name} déjà démarré")
            return
        
        self._running = True
        self._stopping = False
        
        # Créer le semaphore pour limiter la concurrence
        self._semaphore = asyncio.Semaphore(self.max_workers)
        
        # Démarrer les workers
        loop = asyncio.get_event_loop()
        num_workers = min(self.max_workers // 10, 10)  # Moins de workers car async
        for i in range(max(1, num_workers)):
            worker_task = loop.create_task(self._worker_loop(f"async-worker-{i}"))
            self._worker_tasks.add(worker_task)
        
        self.logger.info(f"Exécuteur {self.name} démarré avec {self.max_workers} slots async")
    
    def stop(self, timeout: float = 30.0):
        """Arrête l'exécuteur async"""
        if not self._running:
            return
        
        self.logger.info(f"Arrêt de l'exécuteur {self.name}...")
        self._stopping = True
        
        # Arrêter les workers
        for task in self._worker_tasks:
            task.cancel()
        
        # Attendre la fin
        if self._worker_tasks:
            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(
                    asyncio.wait_for(
                        asyncio.gather(*self._worker_tasks, return_exceptions=True),
                        timeout=timeout
                    )
                )
            except asyncio.TimeoutError:
                self.logger.warning("Timeout lors de l'arrêt des workers async")
        
        self._running = False
        self.logger.info(f"Exécuteur {self.name} arrêté")
    
    async def _worker_loop(self, worker_name: str):
        """Boucle d'un worker async"""
        self.logger.debug(f"Worker async {worker_name} démarré")
        
        while self._running and not self._stopping:
            try:
                # Récupérer une tâche
                try:
                    request = self._task_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # Exécuter avec limitation de concurrence
                async with self._semaphore:
                    await self._handle_task_execution(request)
                
                self._task_queue.task_done()
                
            except asyncio.CancelledError:
                self.logger.debug(f"Worker async {worker_name} annulé")
                break
            except Exception as e:
                self.logger.error(f"Erreur dans worker async {worker_name}: {e}")
                await asyncio.sleep(1)
        
        self.logger.debug(f"Worker async {worker_name} arrêté")
    
    async def _execute_task(self, task: Task) -> TaskExecution:
        """Exécute une tâche de manière asynchrone"""
        return await task.execute()


class ImmediateExecutor(BaseExecutor):
    """
    Exécuteur immédiat (bloquant)
    
    Exécute les tâches immédiatement dans le thread principal.
    Utile pour les tests et le debugging.
    """
    
    def __init__(self, name: Optional[str] = None):
        super().__init__(max_workers=1, name=name or "ImmediateExecutor")
    
    def start(self):
        """Démarre l'exécuteur immédiat"""
        self._running = True
        self._stopping = False
        self.logger.info(f"Exécuteur {self.name} démarré (mode immédiat)")
    
    def stop(self, timeout: float = 30.0):
        """Arrête l'exécuteur immédiat"""
        self._running = False
        self.logger.info(f"Exécuteur {self.name} arrêté")
    
    async def _execute_task(self, task: Task) -> TaskExecution:
        """Exécute une tâche immédiatement"""
        return await task.execute()
    
    def submit_task(self, task: Task, priority: Optional[Priority] = None) -> str:
        """Exécute la tâche immédiatement au lieu de la mettre en queue"""
        if not self._running:
            raise ExecutionError("L'exécuteur n'est pas démarré")
        
        request_id = str(uuid.uuid4())[:8]
        
        # Exécution immédiate
        loop = asyncio.get_event_loop()
        execution = loop.run_until_complete(self._execute_task(task))
        
        # Mettre à jour les stats
        with self._lock:
            self.stats.update_execution(execution)
        
        return request_id


class ExecutorManager:
    """
    Gestionnaire des exécuteurs
    
    Orchestre plusieurs exécuteurs et distribue les tâches selon leurs besoins.
    """
    
    def __init__(self):
        self.logger = get_default_logger()
        self._executors: Dict[str, BaseExecutor] = {}
        self._default_executor: Optional[str] = None
        self._task_routing: Dict[str, str] = {}  # task_name -> executor_name
        self._lock = threading.RLock()
    
    def add_executor(self, name: str, executor: BaseExecutor, is_default: bool = False):
        """
        Ajoute un exécuteur
        
        Args:
            name: Nom de l'exécuteur
            executor: Instance de l'exécuteur
            is_default: Utiliser comme exécuteur par défaut
        """
        with self._lock:
            self._executors[name] = executor
            
            if is_default or not self._default_executor:
                self._default_executor = name
        
        self.logger.info(f"Exécuteur '{name}' ajouté ({executor.__class__.__name__})")
    
    def route_task(self, task_name: str, executor_name: str):
        """
        Route une tâche vers un exécuteur spécifique
        
        Args:
            task_name: Nom de la tâche
            executor_name: Nom de l'exécuteur
        """
        if executor_name not in self._executors:
            raise ExecutionError(f"Exécuteur '{executor_name}' introuvable")
        
        with self._lock:
            self._task_routing[task_name] = executor_name
        
        self.logger.debug(f"Tâche '{task_name}' routée vers '{executor_name}'")
    
    def submit_task(self, task: Task, executor_name: Optional[str] = None) -> str:
        """
        Soumet une tâche à l'exécuteur approprié
        
        Args:
            task: Tâche à exécuter
            executor_name: Exécuteur spécifique (optionnel)
            
        Returns:
            ID de la demande
        """
        # Déterminer l'exécuteur
        target_executor = executor_name
        
        if not target_executor:
            # Vérifier le routing spécifique à la tâche
            target_executor = self._task_routing.get(task.name)
        
        if not target_executor:
            # Utiliser l'exécuteur par défaut
            target_executor = self._default_executor
        
        if not target_executor or target_executor not in self._executors:
            raise ExecutionError("Aucun exécuteur disponible")
        
        executor = self._executors[target_executor]
        return executor.submit_task(task)
    
    def start_all(self):
        """Démarre tous les exécuteurs"""
        with self._lock:
            for name, executor in self._executors.items():
                try:
                    executor.start()
                except Exception as e:
                    self.logger.error(f"Erreur démarrage exécuteur '{name}': {e}")
    
    def stop_all(self, timeout: float = 30.0):
        """Arrête tous les exécuteurs"""
        with self._lock:
            for name, executor in self._executors.items():
                try:
                    executor.stop(timeout=timeout / len(self._executors))
                except Exception as e:
                    self.logger.error(f"Erreur arrêt exécuteur '{name}': {e}")
    
    def get_stats(self) -> Dict[str, dict]:
        """Retourne les stats de tous les exécuteurs"""
        with self._lock:
            return {name: executor.get_stats() for name, executor in self._executors.items()}
    
    def get_executor(self, name: str) -> Optional[BaseExecutor]:
        """Retourne un exécuteur par nom"""
        return self._executors.get(name)
    
    def list_executors(self) -> List[str]:
        """Liste les noms des exécuteurs"""
        with self._lock:
            return list(self._executors.keys())


# Factory pour créer des exécuteurs
class ExecutorFactory:
    """Factory pour créer des exécuteurs selon le type"""
    
    @staticmethod
    def create_executor(
        executor_type: ExecutorType,
        max_workers: int = 10,
        name: Optional[str] = None
    ) -> BaseExecutor:
        """
        Crée un exécuteur selon le type
        
        Args:
            executor_type: Type d'exécuteur
            max_workers: Nombre max de workers
            name: Nom personnalisé
            
        Returns:
            Instance de l'exécuteur
        """
        if executor_type == ExecutorType.THREAD:
            return ThreadExecutor(max_workers, name)
        elif executor_type == ExecutorType.ASYNC:
            return AsyncExecutor(max_workers, name)
        elif executor_type == ExecutorType.IMMEDIATE:
            return ImmediateExecutor(name)
        else:
            raise ExecutionError(f"Type d'exécuteur non supporté: {executor_type}")