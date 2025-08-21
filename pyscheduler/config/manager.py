"""
PyScheduler - Configuration Manager
===================================

Gestionnaire de configuration utilisant nos utilitaires.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

# Import de nos utilitaires (éviter répétition!)
from ..utils import (
    ConfigurationError, ValidationError,
    get_default_logger, validate_cron_expression, 
    validate_time_string, parse_duration, deep_merge_dicts,
    ensure_datetime, import_function
)

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ScheduleType(Enum):
    """Types de planification supportés"""
    INTERVAL = "interval"
    CRON = "cron"
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"  # <-- AJOUTÉ
    STARTUP = "startup"
    SHUTDOWN = "shutdown"


class Priority(Enum):
    """Niveaux de priorité"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    IDLE = 4


@dataclass
class RetryConfig:
    """Configuration des tentatives"""
    max_attempts: int = 3
    backoff_factor: float = 2.0
    max_delay: float = 300.0
    
    def __post_init__(self):
        """Validation après création"""
        if self.max_attempts < 1:
            raise ValidationError("max_attempts doit être >= 1")
        if self.backoff_factor < 1.0:
            raise ValidationError("backoff_factor doit être >= 1.0")
        if self.max_delay <= 0:
            raise ValidationError("max_delay doit être > 0")


@dataclass
class TaskConfig:
    """Configuration d'une tâche"""
    name: str
    function: str
    schedule_type: ScheduleType
    schedule_value: Union[int, str]
    module: Optional[str] = None
    enabled: bool = True
    priority: Priority = Priority.NORMAL
    timeout: Optional[float] = None
    max_runs: Optional[int] = None
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validation après création"""
        # Convertir les chaînes en enums si nécessaire
        if isinstance(self.schedule_type, str):
            try:
                self.schedule_type = ScheduleType(self.schedule_type.lower())
            except ValueError:
                raise ValidationError(f"Type de planification invalide: {self.schedule_type}")
        
        if isinstance(self.priority, str):
            try:
                self.priority = Priority[self.priority.upper()]
            except KeyError:
                raise ValidationError(f"Priorité invalide: {self.priority}")
        
        # Validation des valeurs de planification
        self._validate_schedule()
        
        # Validation timeout
        if self.timeout is not None:
            self.timeout = parse_duration(self.timeout)
        
        # Validation max_runs
        if self.max_runs is not None and self.max_runs < 1:
            raise ValidationError("max_runs doit être >= 1")
    
    def _validate_schedule(self):
        """Valide la planification selon le type"""
        if self.schedule_type == ScheduleType.INTERVAL:
            # Doit être un nombre (secondes) ou une chaîne parsable
            try:
                self.schedule_value = parse_duration(self.schedule_value)
            except ValidationError as e:
                raise ValidationError(f"Intervalle invalide: {e}")
        
        elif self.schedule_type == ScheduleType.CRON:
            # Doit être une expression cron valide
            if not isinstance(self.schedule_value, str):
                raise ValidationError("Expression cron doit être une chaîne")
            validate_cron_expression(self.schedule_value)
        
        elif self.schedule_type == ScheduleType.DAILY:
            # Doit être au format HH:MM
            if not isinstance(self.schedule_value, str):
                raise ValidationError("Heure quotidienne doit être une chaîne HH:MM")
            validate_time_string(self.schedule_value)
        
        elif self.schedule_type == ScheduleType.WEEKLY:
            # Doit être un tuple (jour_semaine, "HH:MM")
            if not isinstance(self.schedule_value, (list, tuple)) or len(self.schedule_value) != 2:
                raise ValidationError("Planification hebdomadaire doit être [jour_semaine, 'HH:MM']")
            
            day, time = self.schedule_value
            if not isinstance(day, int) or not (0 <= day <= 6):
                raise ValidationError("Jour de la semaine doit être 0-6")
            if not isinstance(time, str):
                raise ValidationError("Heure doit être une chaîne HH:MM")
            validate_time_string(time)
        
        elif self.schedule_type == ScheduleType.MONTHLY:
            # Doit être un tuple (jour_mois, "HH:MM")
            if not isinstance(self.schedule_value, (list, tuple)) or len(self.schedule_value) != 2:
                raise ValidationError("Planification mensuelle doit être [jour_mois, 'HH:MM']")
            
            day, time = self.schedule_value
            if not isinstance(day, int) or not (1 <= day <= 31):
                raise ValidationError("Jour du mois doit être 1-31")
            if not isinstance(time, str):
                raise ValidationError("Heure doit être une chaîne HH:MM")
            validate_time_string(time)
        
        elif self.schedule_type == ScheduleType.ONCE:
            # Doit être une date/heure
            try:
                self.schedule_value = ensure_datetime(self.schedule_value)
            except ValidationError as e:
                raise ValidationError(f"Date/heure invalide: {e}")


@dataclass
class GlobalConfig:
    """Configuration globale du scheduler"""
    timezone: str = "UTC"
    max_workers: int = 10
    log_level: str = "INFO"
    log_file: Optional[str] = None
    json_logs: bool = False
    persistence_file: Optional[str] = None
    shutdown_timeout: float = 30.0
    
    def __post_init__(self):
        """Validation après création"""
        if self.max_workers < 1:
            raise ValidationError("max_workers doit être >= 1")
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ValidationError(f"log_level doit être un de: {valid_log_levels}")
        
        if self.shutdown_timeout <= 0:
            raise ValidationError("shutdown_timeout doit être > 0")


@dataclass
class PySchedulerConfig:
    """Configuration complète de PyScheduler"""
    global_config: GlobalConfig = field(default_factory=GlobalConfig)
    tasks: List[TaskConfig] = field(default_factory=list)
    
    def add_task(self, task_config: TaskConfig):
        """Ajoute une tâche à la configuration"""
        # Vérifier les doublons
        existing_names = [task.name for task in self.tasks]
        if task_config.name in existing_names:
            raise ValidationError(f"Tâche '{task_config.name}' existe déjà")
        
        self.tasks.append(task_config)
    
    def remove_task(self, task_name: str) -> bool:
        """Supprime une tâche de la configuration"""
        for i, task in enumerate(self.tasks):
            if task.name == task_name:
                del self.tasks[i]
                return True
        return False
    
    def get_task(self, task_name: str) -> Optional[TaskConfig]:
        """Récupère une tâche par nom"""
        for task in self.tasks:
            if task.name == task_name:
                return task
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'global_settings': asdict(self.global_config),
            'tasks': [asdict(task) for task in self.tasks]
        }


class ConfigManager:
    """Gestionnaire de configuration principal"""
    
    def __init__(self):
        self.logger = get_default_logger()
        self._config: Optional[PySchedulerConfig] = None
    
    def load_from_file(self, config_file: str) -> PySchedulerConfig:
        """
        Charge la configuration depuis un fichier YAML
        
        Args:
            config_file: Chemin vers le fichier de configuration
            
        Returns:
            Configuration chargée
            
        Raises:
            ConfigurationError: Si le chargement échoue
        """
        if not YAML_AVAILABLE:
            raise ConfigurationError(
                "PyYAML requis pour charger des fichiers de configuration. "
                "Installez avec: pip install pyyaml"
            )
        
        config_path = Path(config_file)
        if not config_path.exists():
            raise ConfigurationError(f"Fichier de configuration introuvable: {config_file}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            self.logger.info(f"Configuration chargée depuis {config_file}")
            return self._parse_config_dict(data)
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Erreur de parsing YAML: {e}")
        except Exception as e:
            raise ConfigurationError(f"Erreur lors du chargement: {e}")
    
    def load_from_dict(self, config_data: Dict[str, Any]) -> PySchedulerConfig:
        """
        Charge la configuration depuis un dictionnaire
        
        Args:
            config_data: Données de configuration
            
        Returns:
            Configuration chargée
        """
        return self._parse_config_dict(config_data)
    
    def _parse_config_dict(self, data: Dict[str, Any]) -> PySchedulerConfig:
        """Parse un dictionnaire de configuration"""
        config = PySchedulerConfig()
        
        # Configuration globale
        if 'global_settings' in data:
            global_data = data['global_settings']
            try:
                config.global_config = GlobalConfig(**global_data)
            except TypeError as e:
                raise ConfigurationError(f"Configuration globale invalide: {e}")
        
        # Tâches
        if 'tasks' in data:
            for task_data in data['tasks']:
                try:
                    task_config = self._parse_task_config(task_data)
                    config.add_task(task_config)
                except Exception as e:
                    task_name = task_data.get('name', 'unnamed')
                    raise ConfigurationError(f"Erreur dans la tâche '{task_name}': {e}")
        
        self._config = config
        return config
    
    def _parse_task_config(self, task_data: Dict[str, Any]) -> TaskConfig:
        """Parse la configuration d'une tâche"""
        # Champs obligatoires
        required_fields = ['name', 'function', 'schedule']
        for field in required_fields:
            if field not in task_data:
                raise ConfigurationError(f"Champ obligatoire manquant: {field}")
        
        # Parse de la planification
        schedule_data = task_data['schedule']
        if not isinstance(schedule_data, dict):
            raise ConfigurationError("'schedule' doit être un dictionnaire")
        
        if 'type' not in schedule_data or 'value' not in schedule_data:
            raise ConfigurationError("'schedule' doit contenir 'type' et 'value'")
        
        # Parse de la configuration retry
        retry_config = RetryConfig()
        if 'retry_policy' in task_data:
            retry_data = task_data['retry_policy']
            if isinstance(retry_data, dict):
                retry_config = RetryConfig(**retry_data)
        
        # Création de la TaskConfig
        task_config = TaskConfig(
            name=task_data['name'],
            function=task_data['function'],
            module=task_data.get('module'),
            schedule_type=schedule_data['type'],
            schedule_value=schedule_data['value'],
            enabled=task_data.get('enabled', True),
            priority=task_data.get('priority', 'normal'),
            timeout=task_data.get('timeout'),
            max_runs=task_data.get('max_runs'),
            retry_config=retry_config,
            tags=task_data.get('tags', []),
            metadata=task_data.get('metadata', {})
        )
        
        return task_config
    
    def save_to_file(self, config: PySchedulerConfig, config_file: str):
        """
        Sauvegarde la configuration dans un fichier YAML
        
        Args:
            config: Configuration à sauvegarder
            config_file: Chemin du fichier de destination
        """
        if not YAML_AVAILABLE:
            raise ConfigurationError("PyYAML requis pour sauvegarder des fichiers YAML")
        
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config.to_dict(), f, default_flow_style=False, allow_unicode=True)
            
            self.logger.info(f"Configuration sauvegardée dans {config_file}")
            
        except Exception as e:
            raise ConfigurationError(f"Erreur lors de la sauvegarde: {e}")
    
    def create_default_config(self, config_file: str):
        """
        Crée un fichier de configuration par défaut
        
        Args:
            config_file: Chemin du fichier à créer
        """
        default_config = PySchedulerConfig()
        
        # Ajouter une tâche d'exemple
        example_task = TaskConfig(
            name="example_task",
            function="example_function",
            module="examples.basic_usage",
            schedule_type=ScheduleType.INTERVAL,
            schedule_value=300,  # 5 minutes
            enabled=False  # Désactivée par défaut
        )
        default_config.add_task(example_task)
        
        self.save_to_file(default_config, config_file)
        self.logger.info(f"Configuration par défaut créée: {config_file}")
    
    def validate_task_function(self, task_config: TaskConfig) -> bool:
        """
        Valide qu'une fonction de tâche peut être importée
        
        Args:
            task_config: Configuration de la tâche
            
        Returns:
            True si la fonction est valide
            
        Raises:
            ConfigurationError: Si la validation échoue
        """
        try:
            if task_config.module:
                # Import depuis un module
                func = import_function(task_config.module, task_config.function)
            else:
                # Fonction dans l'espace global (à éviter mais supporté)
                func = globals().get(task_config.function)
                if func is None:
                    raise ConfigurationError(
                        f"Fonction '{task_config.function}' introuvable dans l'espace global"
                    )
            
            if not callable(func):
                raise ConfigurationError(f"'{task_config.function}' n'est pas une fonction")
            
            return True
            
        except Exception as e:
            raise ConfigurationError(f"Validation de fonction échouée: {e}")
    
    @property
    def current_config(self) -> Optional[PySchedulerConfig]:
        """Retourne la configuration actuelle"""
        return self._config