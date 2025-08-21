"""
PyScheduler - Main Scheduler Core
=================================

Le scheduler principal qui orchestre tout le système PyScheduler.
C'est le chef d'orchestre qui coordonne tâches, triggers, executors et configuration.
"""

import asyncio
import atexit
import signal
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union
import json

# Import de nos utilitaires (cohérence maximale!)
from ..utils import (
    PySchedulerError, TaskError, SchedulerNotRunningError, TaskNotFoundError,
    DuplicateTaskError, get_default_logger, setup_default_logger,
    safe_call, format_duration, create_safe_filename, deep_merge_dicts
)
from ..config import (
    ConfigManager, PySchedulerConfig, TaskConfig, GlobalConfig,
    ScheduleType, Priority, get_task_registry
)
from .task import Task, TaskExecution, TaskStatus
from .triggers import TriggerFactory
from .executors import ExecutorManager, ExecutorFactory, ExecutorType, BaseExecutor


class SchedulerState:
    """États possibles du scheduler"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    PAUSED = "paused"


class PyScheduler:
    """
    Scheduler principal de PyScheduler
    
    Le cœur du système qui coordonne :
    - Les tâches et leur planification
    - Les exécuteurs et leur gestion
    - La configuration et la persistance
    - Les événements et le monitoring
    
    Utilisation simple :
        scheduler = PyScheduler()
        scheduler.add_task(my_function, interval=60)
        scheduler.start()
    
    Utilisation avancée :
        config = ConfigManager().load_from_file("config.yaml")
        scheduler = PyScheduler(config=config)
        scheduler.start()
    """
    
    def __init__(
        self,
        config: Optional[PySchedulerConfig] = None,
        config_file: Optional[str] = None,
        timezone: Optional[str] = None,
        max_workers: int = 10,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        json_logs: bool = False,
        persistence_file: Optional[str] = None,
        auto_start: bool = False
    ):
        """
        Initialise le scheduler PyScheduler
        
        Args:
            config: Configuration complète (prioritaire)
            config_file: Fichier de configuration YAML
            timezone: Fuseau horaire par défaut
            max_workers: Nombre max de workers
            log_level: Niveau de log
            log_file: Fichier de log
            json_logs: Format JSON pour les logs
            persistence_file: Fichier de persistance de l'état
            auto_start: Démarrer automatiquement
        """
        # Configuration
        self._load_configuration(
            config, config_file, timezone, max_workers,
            log_level, log_file, json_logs, persistence_file
        )
        
        # État du scheduler
        self._state = SchedulerState.STOPPED
        self._state_lock = threading.RLock()
        self._stop_event = threading.Event()
        
        # Collections principales
        self._tasks: Dict[str, Task] = {}
        self._task_executions: List[TaskExecution] = []
        self._tasks_lock = threading.RLock()
        
        # Gestionnaire d'exécuteurs
        self._executor_manager = ExecutorManager()
        self._setup_default_executors()
        
        # Threads de contrôle
        self._scheduler_thread: Optional[threading.Thread] = None
        self._monitoring_thread: Optional[threading.Thread] = None
        
        # Événements et callbacks
        self._event_callbacks: Dict[str, List[Callable]] = {
            'scheduler_start': [],
            'scheduler_stop': [],
            'task_add': [],
            'task_remove': [],
            'task_start': [],
            'task_complete': [],
            'task_error': []
        }
        
        # Statistiques globales
        self._start_time: Optional[datetime] = None
        self._total_executions = 0
        self._successful_executions = 0
        self._failed_executions = 0
        
        # Setup logging
        self.logger = get_default_logger()
        
        # Enregistrer les handlers de sortie
        self._register_exit_handlers()
        
        # Charger l'état persisté
        if self.config.global_config.persistence_file:
            self._load_persisted_state()
        
        # Auto-démarrage
        if auto_start:
            self.start()
    
    def _load_configuration(
        self, config, config_file, timezone, max_workers,
        log_level, log_file, json_logs, persistence_file
    ):
        """Charge et merge la configuration"""
        # Configuration par défaut
        default_config = PySchedulerConfig(
            global_config=GlobalConfig(
                timezone=timezone or "UTC",
                max_workers=max_workers,
                log_level=log_level,
                log_file=log_file,
                json_logs=json_logs,
                persistence_file=persistence_file
            )
        )
        
        # Configuration finale
        if config:
            # Configuration fournie directement
            self.config = config
        elif config_file:
            # Chargement depuis fichier
            manager = ConfigManager()
            file_config = manager.load_from_file(config_file)
            self.config = file_config
        else:
            # Configuration par défaut
            self.config = default_config
        
        # Merge avec la config par défaut pour les valeurs manquantes
        if config or config_file:
            # Merger intelligemment
            default_dict = default_config.to_dict()
            current_dict = self.config.to_dict()
            merged_dict = deep_merge_dicts(default_dict, current_dict)
            
            # Recréer la config depuis le dict mergé
            manager = ConfigManager()
            self.config = manager.load_from_dict(merged_dict)
        
        # Setup du logger avec la config finale
        setup_default_logger(
            level=self.config.global_config.log_level,
            log_file=self.config.global_config.log_file,
            json_format=self.config.global_config.json_logs
        )
    
    def _setup_default_executors(self):
        """Configure les exécuteurs par défaut"""
        # Exécuteur principal (threads)
        main_executor = ExecutorFactory.create_executor(
            ExecutorType.THREAD,
            max_workers=self.config.global_config.max_workers,
            name="main"
        )
        self._executor_manager.add_executor("main", main_executor, is_default=True)
        
        # Exécuteur async
        async_executor = ExecutorFactory.create_executor(
            ExecutorType.ASYNC,
            max_workers=self.config.global_config.max_workers * 2,
            name="async"
        )
        self._executor_manager.add_executor("async", async_executor)
        
        # Exécuteur immédiat pour debug
        immediate_executor = ExecutorFactory.create_executor(
            ExecutorType.IMMEDIATE,
            name="immediate"
        )
        self._executor_manager.add_executor("immediate", immediate_executor)
        
        # Setup des callbacks sur les exécuteurs
        for executor_name in self._executor_manager.list_executors():
            executor = self._executor_manager.get_executor(executor_name)
            if executor:
                executor.set_callbacks(
                    on_start=self._on_task_execution_start,
                    on_complete=self._on_task_execution_complete,
                    on_error=self._on_task_execution_error
                )
    
    def _register_exit_handlers(self):
        """Enregistre les handlers de sortie propre"""
        # Handler atexit
        atexit.register(self._cleanup_on_exit)
        
        # Handlers de signaux (Unix/Linux)
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except (AttributeError, ValueError):
            # Windows ou environnement qui ne supporte pas ces signaux
            pass
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signaux pour arrêt propre"""
        self.logger.info(f"Signal {signum} reçu, arrêt du scheduler...")
        self.stop()
    
    def _cleanup_on_exit(self):
        """Nettoyage à la sortie du programme"""
        if self._state in [SchedulerState.RUNNING, SchedulerState.STARTING]:
            self.logger.info("Nettoyage automatique du scheduler à la sortie")
            self.stop(timeout=10.0)
    
    # ====================================================================
    # GESTION DES TÂCHES
    # ====================================================================
    
    def add_task(
        self,
        func: Optional[Callable] = None,
        name: Optional[str] = None,
        # Méthodes de planification
        interval: Optional[Union[int, float, str]] = None,
        cron: Optional[str] = None,
        daily_at: Optional[str] = None,
        weekly_at: Optional[tuple] = None,
        once_at: Optional[Union[str, datetime]] = None,
        on_startup: bool = False,
        on_shutdown: bool = False,
        # Configuration
        enabled: bool = True,
        priority: Union[str, Priority] = Priority.NORMAL,
        timeout: Optional[Union[int, float, str]] = None,
        max_runs: Optional[int] = None,
        executor: Optional[str] = None,
        # Retry
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
        max_delay: Union[int, float, str] = 300,
        # Métadonnées
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Union[Task, Callable]:
        """
        Ajoute une tâche au scheduler
        
        Cette méthode offre une API unifiée pour ajouter des tâches soit
        directement, soit comme décorateur.
        
        Exemples:
            # Usage direct
            scheduler.add_task(my_func, interval=60)
            scheduler.add_task(my_func, cron="0 9 * * *")
            scheduler.add_task(my_func, daily_at="14:30")
            
            # Usage décorateur
            @scheduler.add_task(interval=60)
            def my_task():
                pass
        
        Args:
            func: Fonction à exécuter (None pour usage décorateur)
            name: Nom de la tâche
            interval: Intervalle en secondes
            cron: Expression cron
            daily_at: Heure quotidienne (HH:MM)
            weekly_at: Planification hebdomadaire (jour, heure)
            once_at: Exécution unique
            on_startup: Exécuter au démarrage
            on_shutdown: Exécuter à l'arrêt
            enabled: Tâche activée
            priority: Priorité d'exécution
            timeout: Timeout d'exécution
            max_runs: Nombre max d'exécutions
            executor: Exécuteur spécifique à utiliser
            max_attempts: Tentatives en cas d'échec
            backoff_factor: Facteur de délai pour retry
            max_delay: Délai maximum entre tentatives
            tags: Tags pour catégorisation
            metadata: Métadonnées additionnelles
            **kwargs: Paramètres additionnels
            
        Returns:
            Task si func fournie, sinon décorateur
            
        Raises:
            DuplicateTaskError: Si la tâche existe déjà
            ValidationError: Si la configuration est invalide
        """
        # Usage décorateur
        if func is None:
            def decorator(f):
                return self.add_task(
                    f, name, interval, cron, daily_at, weekly_at, once_at,
                    on_startup, on_shutdown, enabled, priority, timeout, max_runs,
                    executor, max_attempts, backoff_factor, max_delay, tags, metadata, **kwargs
                )
            return decorator
        
        # Déterminer le type et la valeur de planification
        schedule_type, schedule_value = self._determine_schedule_from_params(
            interval, cron, daily_at, weekly_at, once_at, on_startup, on_shutdown
        )
        
        # Nom de la tâche
        task_name = name or f"{func.__module__}.{func.__name__}"
        
        # Vérifier les doublons
        with self._tasks_lock:
            if task_name in self._tasks:
                raise DuplicateTaskError(task_name)
        
        # Convertir priority si nécessaire
        if isinstance(priority, str):
            priority = Priority[priority.upper()]
        
        # Parser timeout et max_delay
        from ..utils import parse_duration
        parsed_timeout = parse_duration(timeout) if timeout else None
        parsed_max_delay = parse_duration(max_delay)
        
        # Créer la tâche
        from ..config import RetryConfig
        retry_config = RetryConfig(
            max_attempts=max_attempts,
            backoff_factor=backoff_factor,
            max_delay=parsed_max_delay
        )
        
        task = Task(
            name=task_name,
            func=func,
            schedule_type=schedule_type,
            schedule_value=schedule_value,
            module_path=func.__module__,
            enabled=enabled,
            priority=priority,
            timeout=parsed_timeout,
            max_runs=max_runs,
            retry_config=retry_config,
            tags=tags or set(),
            metadata=metadata or {}
        )
        
        # Ajouter au scheduler
        with self._tasks_lock:
            self._tasks[task_name] = task
        
        # Router vers un exécuteur spécifique si demandé
        if executor:
            self._executor_manager.route_task(task_name, executor)
        
        # Événement d'ajout
        self._emit_event('task_add', task)
        
        self.logger.info(f"Tâche '{task_name}' ajoutée ({schedule_type.value})")
        return task
    
    def _determine_schedule_from_params(self, *args) -> tuple:
        """Détermine le type de planification depuis les paramètres"""
        interval, cron, daily_at, weekly_at, once_at, on_startup, on_shutdown = args
        
        # Compter les méthodes spécifiées
        methods = [
            (interval is not None, ScheduleType.INTERVAL, interval),
            (cron is not None, ScheduleType.CRON, cron),
            (daily_at is not None, ScheduleType.DAILY, daily_at),
            (weekly_at is not None, ScheduleType.WEEKLY, weekly_at),
            (once_at is not None, ScheduleType.ONCE, once_at),
            (on_startup, ScheduleType.STARTUP, None),
            (on_shutdown, ScheduleType.SHUTDOWN, None)
        ]
        
        specified = [m for m in methods if m[0]]
        
        if len(specified) == 0:
            raise TaskError("Au moins une méthode de planification doit être spécifiée")
        
        if len(specified) > 1:
            method_names = [m[1].value for m in specified]
            raise TaskError(f"Une seule méthode de planification autorisée: {method_names}")
        
        return specified[0][1], specified[0][2]
    
    def add_task_from_config(self, task_config: TaskConfig, func: Callable) -> Task:
        """
        Ajoute une tâche depuis une configuration
        
        Args:
            task_config: Configuration de la tâche
            func: Fonction à exécuter
            
        Returns:
            Tâche créée
        """
        task = Task(
            name=task_config.name,
            func=func,
            schedule_type=task_config.schedule_type,
            schedule_value=task_config.schedule_value,
            module_path=task_config.module,
            enabled=task_config.enabled,
            priority=task_config.priority,
            timeout=task_config.timeout,
            max_runs=task_config.max_runs,
            retry_config=task_config.retry_config,
            tags=set(task_config.tags),
            metadata=task_config.metadata
        )
        
        with self._tasks_lock:
            if task.name in self._tasks:
                raise DuplicateTaskError(task.name)
            self._tasks[task.name] = task
        
        self._emit_event('task_add', task)
        self.logger.info(f"Tâche '{task.name}' ajoutée depuis config")
        return task
    
    def remove_task(self, task_name: str, wait_completion: bool = True) -> bool:
        """
        Supprime une tâche du scheduler
        
        Args:
            task_name: Nom de la tâche
            wait_completion: Attendre la fin de l'exécution en cours
            
        Returns:
            True si supprimée, False si introuvable
        """
        with self._tasks_lock:
            if task_name not in self._tasks:
                return False
            
            task = self._tasks[task_name]
            
            # Annuler la tâche
            task.cancel()
            
            # Attendre la fin si demandé
            if wait_completion and task.is_running:
                self.logger.info(f"Attente de la fin de '{task_name}'...")
                timeout = 30.0
                start_wait = time.time()
                
                while task.is_running and (time.time() - start_wait) < timeout:
                    time.sleep(0.1)
                
                if task.is_running:
                    self.logger.warning(f"Timeout lors de l'attente de '{task_name}'")
            
            # Supprimer
            del self._tasks[task_name]
        
        self._emit_event('task_remove', task)
        self.logger.info(f"Tâche '{task_name}' supprimée")
        return True
    
    def get_task(self, task_name: str) -> Optional[Task]:
        """
        Récupère une tâche par nom
        
        Args:
            task_name: Nom de la tâche
            
        Returns:
            Tâche ou None si introuvable
        """
        with self._tasks_lock:
            return self._tasks.get(task_name)
    
    def list_tasks(self, include_disabled: bool = True, tags: Optional[Set[str]] = None) -> List[Task]:
        """
        Liste les tâches
        
        Args:
            include_disabled: Inclure les tâches désactivées
            tags: Filtrer par tags
            
        Returns:
            Liste des tâches
        """
        with self._tasks_lock:
            tasks = list(self._tasks.values())
        
        # Filtrer par état
        if not include_disabled:
            tasks = [t for t in tasks if t.enabled]
        
        # Filtrer par tags
        if tags:
            tasks = [t for t in tasks if tags.issubset(t.tags)]
        
        return tasks
    
    def pause_task(self, task_name: str) -> bool:
        """Met en pause une tâche"""
        task = self.get_task(task_name)
        if task:
            task.pause()
            self.logger.info(f"Tâche '{task_name}' mise en pause")
            return True
        return False
    
    def resume_task(self, task_name: str) -> bool:
        """Reprend une tâche en pause"""
        task = self.get_task(task_name)
        if task:
            task.resume()
            self.logger.info(f"Tâche '{task_name}' reprise")
            return True
        return False
    
    def run_task_now(self, task_name: str, executor_name: Optional[str] = None) -> str:
        """
        Exécute immédiatement une tâche
        
        Args:
            task_name: Nom de la tâche
            executor_name: Exécuteur spécifique (optionnel)
            
        Returns:
            ID de la demande d'exécution
            
        Raises:
            TaskNotFoundError: Si la tâche n'existe pas
            SchedulerNotRunningError: Si le scheduler n'est pas démarré
        """
        if self._state != SchedulerState.RUNNING:
            raise SchedulerNotRunningError("run_task_now")
        
        task = self.get_task(task_name)
        if not task:
            raise TaskNotFoundError(task_name)
        
        # Soumettre à l'exécuteur
        request_id = self._executor_manager.submit_task(task, executor_name)
        
        self.logger.info(f"Exécution immédiate de '{task_name}' demandée (ID: {request_id})")
        return request_id
    
    # ====================================================================
    # GESTION DU CYCLE DE VIE
    # ====================================================================
    
    def start(self):
        """
        Démarre le scheduler
        
        Raises:
            PySchedulerError: Si déjà démarré ou erreur de démarrage
        """
        with self._state_lock:
            if self._state != SchedulerState.STOPPED:
                raise PySchedulerError(f"Scheduler déjà dans l'état {self._state}")
            
            self._state = SchedulerState.STARTING
        
        try:
            self.logger.scheduler_started()
            self._start_time = datetime.now()
            
            # Charger les tâches depuis la configuration
            self._load_tasks_from_config()
            
            # Charger les tâches depuis le registre des décorateurs
            self._load_tasks_from_registry()
            
            # Démarrer les exécuteurs
            self._executor_manager.start_all()
            
            # Démarrer les threads de contrôle
            self._stop_event.clear()
            self._start_control_threads()
            
            # Exécuter les tâches de startup
            self._run_startup_tasks()
            
            # Événement de démarrage
            self._emit_event('scheduler_start')
            
            with self._state_lock:
                self._state = SchedulerState.RUNNING
            
            self.logger.info(f"PyScheduler démarré avec {len(self._tasks)} tâches")
            
        except Exception as e:
            with self._state_lock:
                self._state = SchedulerState.STOPPED
            self.logger.error(f"Erreur lors du démarrage: {e}")
            raise PySchedulerError(f"Échec du démarrage: {e}")
    
    def stop(self, timeout: float = 30.0):
        """
        Arrête le scheduler proprement
        
        Args:
            timeout: Timeout total pour l'arrêt
        """
        with self._state_lock:
            if self._state == SchedulerState.STOPPED:
                self.logger.warning("Scheduler déjà arrêté")
                return
            
            if self._state == SchedulerState.STOPPING:
                self.logger.warning("Scheduler déjà en cours d'arrêt")
                return
            
            self._state = SchedulerState.STOPPING
        
        self.logger.info("Arrêt du scheduler en cours...")
        start_stop_time = time.time()
        
        try:
            # Signaler l'arrêt
            self._stop_event.set()
            
            # Exécuter les tâches de shutdown
            self._run_shutdown_tasks()
            
            # Arrêter les threads de contrôle
            self._stop_control_threads(timeout / 3)
            
            # Arrêter les exécuteurs
            self._executor_manager.stop_all(timeout / 3)
            
            # Sauvegarder l'état si persistance activée
            if self.config.global_config.persistence_file:
                self._save_persistent_state()
            
            # Événement d'arrêt
            self._emit_event('scheduler_stop')
            
            stop_duration = time.time() - start_stop_time
            self.logger.scheduler_stopped()
            self.logger.info(f"Scheduler arrêté en {stop_duration:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'arrêt: {e}")
        finally:
            with self._state_lock:
                self._state = SchedulerState.STOPPED
    
    def pause(self):
        """Met en pause le scheduler (arrête la planification, pas les exécutions en cours)"""
        with self._state_lock:
            if self._state == SchedulerState.RUNNING:
                self._state = SchedulerState.PAUSED
                self.logger.info("Scheduler mis en pause")
    
    def resume(self):
        """Reprend le scheduler depuis une pause"""
        with self._state_lock:
            if self._state == SchedulerState.PAUSED:
                self._state = SchedulerState.RUNNING
                self.logger.info("Scheduler repris")
    
    def restart(self, timeout: float = 30.0):
        """Redémarre le scheduler"""
        self.logger.info("Redémarrage du scheduler...")
        self.stop(timeout)
        time.sleep(1)  # Petite pause pour laisser les ressources se libérer
        self.start()
    
    # ====================================================================
    # THREADS DE CONTRÔLE
    # ====================================================================
    
    def _start_control_threads(self):
        """Démarre les threads de contrôle"""
        # Thread principal de planification
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="PyScheduler-Main",
            daemon=True
        )
        self._scheduler_thread.start()
        
        # Thread de monitoring (optionnel)
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name="PyScheduler-Monitor",
            daemon=True
        )
        self._monitoring_thread.start()
    
    def _stop_control_threads(self, timeout: float):
        """Arrête les threads de contrôle"""
        threads_to_wait = []
        
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            threads_to_wait.append(self._scheduler_thread)
        
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            threads_to_wait.append(self._monitoring_thread)
        
        # Attendre que les threads se terminent
        for thread in threads_to_wait:
            thread.join(timeout / len(threads_to_wait) if threads_to_wait else timeout)
            if thread.is_alive():
                self.logger.warning(f"Thread {thread.name} ne s'est pas arrêté dans les temps")
    
    def _scheduler_loop(self):
        """
        Boucle principale du scheduler
        
        Vérifie périodiquement quelles tâches doivent s'exécuter
        et les soumet aux exécuteurs appropriés.
        """
        self.logger.debug("Boucle principale du scheduler démarrée")
        
        while not self._stop_event.is_set():
            try:
                # Pause si le scheduler est en pause
                if self._state == SchedulerState.PAUSED:
                    time.sleep(1)
                    continue
                
                # Vérifier les tâches à exécuter
                current_time = datetime.now()
                tasks_to_run = []
                
                with self._tasks_lock:
                    for task in self._tasks.values():
                        if task.should_run(current_time):
                            tasks_to_run.append(task)
                
                # Soumettre les tâches aux exécuteurs
                for task in tasks_to_run:
                    try:
                        self._executor_manager.submit_task(task)
                    except Exception as e:
                        self.logger.error(f"Erreur soumission tâche '{task.name}': {e}")
                
                # Dormir un peu pour éviter une charge CPU excessive
                time.sleep(0.1)  # 100ms de résolution
                
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle principale: {e}")
                time.sleep(1)  # Pause plus longue en cas d'erreur
        
        self.logger.debug("Boucle principale du scheduler arrêtée")
    
    def _monitoring_loop(self):
        """
        Boucle de monitoring
        
        Surveille l'état du système et effectue des tâches de maintenance.
        """
        self.logger.debug("Boucle de monitoring démarrée")
        
        last_stats_log = time.time()
        stats_interval = 300  # Log des stats toutes les 5 minutes
        
        while not self._stop_event.is_set():
            try:
                # Log périodique des statistiques
                if time.time() - last_stats_log > stats_interval:
                    self._log_stats()
                    last_stats_log = time.time()
                
                # Nettoyage de l'historique des exécutions
                self._cleanup_execution_history()
                
                # Sauvegarde périodique de l'état
                if self.config.global_config.persistence_file:
                    self._save_persistent_state()
                
                # Dormir 30 secondes
                if self._stop_event.wait(30):
                    break
                
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de monitoring: {e}")
                if self._stop_event.wait(60):  # Pause plus longue en cas d'erreur
                    break
        
        self.logger.debug("Boucle de monitoring arrêtée")
    
    # ====================================================================
    # GESTION DES ÉVÉNEMENTS
    # ====================================================================
    
    def _emit_event(self, event_type: str, *args, **kwargs):
        """Émet un événement vers les callbacks enregistrés"""
        callbacks = self._event_callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Erreur dans callback {event_type}: {e}")
    
    def add_event_listener(self, event_type: str, callback: Callable):
        """
        Ajoute un listener d'événement
        
        Args:
            event_type: Type d'événement (scheduler_start, task_complete, etc.)
            callback: Fonction callback
        """
        if event_type not in self._event_callbacks:
            self._event_callbacks[event_type] = []
        
        self._event_callbacks[event_type].append(callback)
        self.logger.debug(f"Listener ajouté pour {event_type}")
    
    def remove_event_listener(self, event_type: str, callback: Callable):
        """Supprime un listener d'événement"""
        if event_type in self._event_callbacks:
            try:
                self._event_callbacks[event_type].remove(callback)
                self.logger.debug(f"Listener supprimé pour {event_type}")
            except ValueError:
                pass
    
    # Callbacks pour les exécutions de tâches
    async def _on_task_execution_start(self, task: Task, execution: Optional[TaskExecution]):
        """Callback appelé au début d'une exécution"""
        self._emit_event('task_start', task, execution)
    
    async def _on_task_execution_complete(self, task: Task, execution: TaskExecution):
        """Callback appelé à la fin d'une exécution réussie"""
        with self._tasks_lock:
            self._task_executions.append(execution)
            self._total_executions += 1
            if execution.status == TaskStatus.SUCCESS:
                self._successful_executions += 1
            else:
                self._failed_executions += 1
        
        self._emit_event('task_complete', task, execution)
    
    async def _on_task_execution_error(self, task: Task, execution: TaskExecution, error: str):
        """Callback appelé en cas d'erreur d'exécution"""
        self._emit_event('task_error', task, execution, error)
    
    # ====================================================================
    # CHARGEMENT ET PERSISTANCE
    # ====================================================================
    
    def _load_tasks_from_config(self):
        """Charge les tâches depuis la configuration"""
        for task_config in self.config.tasks:
            try:
                # Importer la fonction
                from ..utils import import_function
                func = import_function(task_config.module, task_config.function)
                
                # Créer et ajouter la tâche
                self.add_task_from_config(task_config, func)
                
            except Exception as e:
                self.logger.error(f"Erreur chargement tâche '{task_config.name}': {e}")
    
    def _load_tasks_from_registry(self):
        """Charge les tâches depuis le registre des décorateurs"""
        registry = get_task_registry()
        
        for task_config in registry.get_all_tasks():
            try:
                # La fonction est stockée dans les métadonnées
                func = task_config.metadata.get('_function_ref')
                if func:
                    # Éviter les doublons
                    if task_config.name not in self._tasks:
                        self.add_task_from_config(task_config, func)
                
            except Exception as e:
                self.logger.error(f"Erreur chargement tâche décorée '{task_config.name}': {e}")
    
    def _run_startup_tasks(self):
        """Exécute les tâches marquées pour le démarrage"""
        startup_tasks = [
            task for task in self._tasks.values()
            if task.schedule_type == ScheduleType.STARTUP
        ]
        
        self.logger.info(f"Exécution de {len(startup_tasks)} tâches de démarrage")
        
        for task in startup_tasks:
            try:
                self._executor_manager.submit_task(task)
            except Exception as e:
                self.logger.error(f"Erreur tâche de startup '{task.name}': {e}")
    
    def _run_shutdown_tasks(self):
        """Exécute les tâches marquées pour l'arrêt"""
        shutdown_tasks = [
            task for task in self._tasks.values()
            if task.schedule_type == ScheduleType.SHUTDOWN
        ]
        
        if not shutdown_tasks:
            return
        
        self.logger.info(f"Exécution de {len(shutdown_tasks)} tâches d'arrêt")
        
        # Utiliser l'exécuteur immédiat pour les tâches de shutdown
        immediate_executor = self._executor_manager.get_executor("immediate")
        if not immediate_executor:
            self.logger.warning("Exécuteur immédiat non disponible pour les tâches de shutdown")
            return
        
        # Exécuter de manière synchrone
        for task in shutdown_tasks:
            try:
                immediate_executor.submit_task(task)
            except Exception as e:
                self.logger.error(f"Erreur tâche de shutdown '{task.name}': {e}")
    
    def _save_persistent_state(self):
        """Sauvegarde l'état du scheduler"""
        if not self.config.global_config.persistence_file:
            return
        
        try:
            state = {
                'scheduler': {
                    'start_time': self._start_time.isoformat() if self._start_time else None,
                    'total_executions': self._total_executions,
                    'successful_executions': self._successful_executions,
                    'failed_executions': self._failed_executions
                },
                'tasks': [task.to_dict() for task in self._tasks.values()],
                'recent_executions': [
                    exec.to_dict() for exec in self._task_executions[-100:]  # Garder les 100 dernières
                ],
                'executors': self._executor_manager.get_stats(),
                'saved_at': datetime.now().isoformat()
            }
            
            persistence_path = Path(self.config.global_config.persistence_file)
            persistence_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(persistence_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"État sauvegardé dans {persistence_path}")
            
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde état: {e}")
    
    def _load_persisted_state(self):
        """Charge l'état persisté"""
        persistence_file = self.config.global_config.persistence_file
        if not persistence_file or not Path(persistence_file).exists():
            return
        
        try:
            with open(persistence_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Restaurer les statistiques globales
            scheduler_state = state.get('scheduler', {})
            self._total_executions = scheduler_state.get('total_executions', 0)
            self._successful_executions = scheduler_state.get('successful_executions', 0)
            self._failed_executions = scheduler_state.get('failed_executions', 0)
            
            self.logger.info(f"État chargé depuis {persistence_file}")
            
        except Exception as e:
            self.logger.error(f"Erreur chargement état: {e}")
    
    # ====================================================================
    # MONITORING ET STATISTIQUES
    # ====================================================================
    
    def _log_stats(self):
        """Log les statistiques du scheduler"""
        uptime = time.time() - self._start_time.timestamp() if self._start_time else 0
        
        self.logger.info(
            f"Stats PyScheduler - Uptime: {format_duration(uptime)}, "
            f"Tâches: {len(self._tasks)}, "
            f"Exécutions: {self._total_executions} "
            f"(Succès: {self._successful_executions}, Échecs: {self._failed_executions})"
        )
    
    def _cleanup_execution_history(self):
        """Nettoie l'historique des exécutions pour éviter la consommation mémoire"""
        max_history = 1000
        
        with self._tasks_lock:
            if len(self._task_executions) > max_history:
                # Garder seulement les plus récentes
                self._task_executions = self._task_executions[-max_history//2:]
                self.logger.debug("Historique des exécutions nettoyé")
    
    def get_stats(self) -> dict:
        """
        Retourne les statistiques complètes du scheduler
        
        Returns:
            Dictionnaire avec toutes les statistiques
        """
        uptime = time.time() - self._start_time.timestamp() if self._start_time else 0
        success_rate = self._successful_executions / max(self._total_executions, 1) * 100
        
        with self._tasks_lock:
            task_stats = {
                'total': len(self._tasks),
                'enabled': len([t for t in self._tasks.values() if t.enabled]),
                'running': len([t for t in self._tasks.values() if t.is_running]),
                'cancelled': len([t for t in self._tasks.values() if t.is_cancelled])
            }
        
        return {
            'scheduler': {
                'state': self._state,
                'uptime_seconds': round(uptime, 2),
                'uptime_formatted': format_duration(uptime),
                'start_time': self._start_time.isoformat() if self._start_time else None
            },
            'tasks': task_stats,
            'executions': {
                'total': self._total_executions,
                'successful': self._successful_executions,
                'failed': self._failed_executions,
                'success_rate': round(success_rate, 2)
            },
            'executors': self._executor_manager.get_stats()
        }
    
    def get_task_stats(self, task_name: Optional[str] = None) -> Union[dict, List[dict]]:
        """
        Retourne les statistiques des tâches
        
        Args:
            task_name: Nom d'une tâche spécifique (None pour toutes)
            
        Returns:
            Stats d'une tâche ou liste des stats de toutes les tâches
        """
        if task_name:
            task = self.get_task(task_name)
            return task.to_dict() if task else None
        else:
            with self._tasks_lock:
                return [task.to_dict() for task in self._tasks.values()]
    
    def get_recent_executions(self, task_name: Optional[str] = None, limit: int = 50) -> List[dict]:
        """
        Retourne les exécutions récentes
        
        Args:
            task_name: Filtrer par nom de tâche
            limit: Nombre maximum d'exécutions
            
        Returns:
            Liste des exécutions récentes
        """
        with self._tasks_lock:
            executions = self._task_executions
            
            if task_name:
                executions = [e for e in executions if e.task_name == task_name]
            
            executions = executions[-limit:]
            return [e.to_dict() for e in executions]
    
    # ====================================================================
    # CONTEXT MANAGER ET MÉTHODES UTILITAIRES
    # ====================================================================
    
    def __enter__(self):
        """Entrée du context manager"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sortie du context manager"""
        self.stop()
    
    def run_forever(self):
        """
        Exécute le scheduler indéfiniment (bloquant)
        
        Utile pour les scripts qui ne font que du scheduling.
        """
        if self._state != SchedulerState.RUNNING:
            self.start()
        
        try:
            self.logger.info("Scheduler en mode run_forever - Ctrl+C pour arrêter")
            while self._state == SchedulerState.RUNNING:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Interruption clavier reçue")
        finally:
            self.stop()
    
    @property
    def state(self) -> str:
        """État actuel du scheduler"""
        return self._state
    
    @property
    def is_running(self) -> bool:
        """True si le scheduler est en marche"""
        return self._state == SchedulerState.RUNNING
    
    @property
    def is_stopped(self) -> bool:
        """True si le scheduler est arrêté"""
        return self._state == SchedulerState.STOPPED
    
    @property
    def uptime(self) -> float:
        """Durée de fonctionnement en secondes"""
        if self._start_time:
            return time.time() - self._start_time.timestamp()
        return 0.0
    
    def __str__(self) -> str:
        """Représentation en chaîne du scheduler"""
        return (
            f"PyScheduler(state={self._state}, tasks={len(self._tasks)}, "
            f"uptime={format_duration(self.uptime)})"
        )
    
    def __repr__(self) -> str:
        return self.__str__()