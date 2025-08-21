# PyScheduler - Utilitaires

Ce module contient tous les utilitaires de base utilisés dans PyScheduler. Ces outils assurent la cohérence, la validation et la robustesse de l'ensemble du système.

## Table des matières

- [Exceptions](#exceptions)
- [Logger](#logger)
- [Helpers](#helpers)
- [Exemples d'utilisation](#exemples-dutilisation)

---

## Exceptions

Module : `pyscheduler.utils.exceptions`

Hiérarchie d'exceptions personnalisées avec contexte enrichi.

### Classes principales

#### `PySchedulerError` (Base)
```python
class PySchedulerError(Exception):
    def __init__(self, message: str, details: dict = None)
```

Exception de base avec support de détails contextuels.

**Exemple :**
```python
raise PySchedulerError("Erreur de traitement", {"task": "backup", "attempt": 3})
```

#### Exceptions spécialisées

| Exception | Description | Usage |
|-----------|-------------|-------|
| `TaskError` | Erreurs liées aux tâches | Tâche invalide, non trouvée |
| `SchedulingError` | Erreurs de planification | Expression cron invalide |
| `ConfigurationError` | Erreurs de configuration | Fichier YAML incorrect |
| `ExecutionError` | Erreurs d'exécution | Timeout, échec de tâche |
| `ValidationError` | Erreurs de validation | Paramètres invalides |

#### Exceptions spécifiques

| Exception | Paramètres | Description |
|-----------|------------|-------------|
| `SchedulerNotRunningError` | `operation: str` | Scheduler non démarré |
| `TaskNotFoundError` | `task_name: str` | Tâche introuvable |
| `DuplicateTaskError` | `task_name: str` | Tâche déjà existante |
| `InvalidScheduleError` | `schedule_type, schedule_value` | Planification invalide |
| `TaskTimeoutError` | `task_name, timeout` | Dépassement de timeout |
| `MaxRetriesExceededError` | `task_name, max_retries, last_error` | Échec après toutes les tentatives |

**Exemples :**
```python
# Exception simple
raise TaskNotFoundError("backup_task")

# Exception avec contexte
raise InvalidScheduleError("cron", "invalid expression")

# Capture avec détails
try:
    # code...
except TaskTimeoutError as e:
    print(f"Tâche {e.task_name} timeout après {e.timeout}s")
```

---

## Logger

Module : `pyscheduler.utils.logger`

Système de logging flexible avec support console, fichier et JSON.

### Classes principales

#### `PySchedulerLogger`
```python
class PySchedulerLogger:
    def __init__(
        self,
        name: str = "PyScheduler",
        level: str = "INFO", 
        log_file: Optional[str] = None,
        console_output: bool = True,
        json_format: bool = False
    )
```

Logger principal avec configuration flexible.

### Méthodes de logging

| Méthode | Description | Exemple |
|---------|-------------|---------|
| `debug(message, **kwargs)` | Log niveau DEBUG | `logger.debug("Détail", task="test")` |
| `info(message, **kwargs)` | Log niveau INFO | `logger.info("Démarrage", port=8080)` |
| `warning(message, **kwargs)` | Log niveau WARNING | `logger.warning("Attention", retry=3)` |
| `error(message, **kwargs)` | Log niveau ERROR | `logger.error("Échec", error="timeout")` |
| `critical(message, **kwargs)` | Log niveau CRITICAL | `logger.critical("Arrêt", reason="fatal")` |

### Méthodes spécialisées

| Méthode | Description | Paramètres |
|---------|-------------|------------|
| `task_started(task_name, **kwargs)` | Tâche démarrée | nom de tâche + contexte |
| `task_completed(task_name, duration, **kwargs)` | Tâche terminée | nom, durée + contexte |
| `task_failed(task_name, error, **kwargs)` | Tâche échouée | nom, erreur + contexte |
| `scheduler_started()` | Scheduler démarré | aucun |
| `scheduler_stopped()` | Scheduler arrêté | aucun |

### Fonctions utilitaires

| Fonction | Retour | Description |
|----------|--------|-------------|
| `get_logger(...)` | `PySchedulerLogger` | Crée un logger |
| `setup_default_logger(...)` | `None` | Configure le logger par défaut |
| `get_default_logger()` | `PySchedulerLogger` | Obtient le logger par défaut |

**Exemples :**
```python
# Logger simple
from pyscheduler.utils import get_logger
logger = get_logger("MonApp", level="DEBUG")
logger.info("Application démarrée")

# Logger avec fichier
logger = get_logger(
    "MonApp", 
    log_file="app.log",
    json_format=True
)

# Logger par défaut
from pyscheduler.utils import setup_default_logger, get_default_logger
setup_default_logger(level="INFO", log_file="scheduler.log")
logger = get_default_logger()

# Logging avec contexte
logger.task_started("backup", database="users", size="1.2GB")
logger.task_completed("backup", 45.2, records=15000)
logger.task_failed("sync", "Connection timeout", host="api.example.com")
```

**Format JSON :**
```json
{
  "timestamp": "2025-08-21T12:09:33.123456",
  "level": "INFO",
  "logger": "PyScheduler",
  "message": "Tâche 'backup' terminée avec succès en 45.20s",
  "task_name": "backup",
  "duration": 45.2,
  "status": "success"
}
```

---

## Helpers

Module : `pyscheduler.utils.helpers`

Fonctions utilitaires pour validation, parsing, import et manipulation de données.

### Validation

| Fonction | Paramètres | Retour | Description |
|----------|------------|---------|-------------|
| `validate_cron_expression(cron_expr)` | `str` | `bool` | Valide expression cron |
| `validate_time_string(time_str)` | `str` | `bool` | Valide format HH:MM |

**Exemples :**
```python
from pyscheduler.utils import validate_cron_expression, validate_time_string

# Validation cron
validate_cron_expression("0 9 * * 1-5")  # ✅ True
validate_cron_expression("invalid")      # ❌ ValidationError

# Validation time
validate_time_string("09:30")  # ✅ True  
validate_time_string("25:00")  # ❌ ValidationError
```

### Parsing et conversion

| Fonction | Paramètres | Retour | Description |
|----------|------------|---------|-------------|
| `parse_duration(duration)` | `Union[str, int, float]` | `float` | Parse en secondes |
| `ensure_datetime(value)` | `Union[str, datetime]` | `datetime` | Convertit en datetime |
| `format_duration(seconds)` | `float` | `str` | Formate durée lisible |

**Exemples :**
```python
from pyscheduler.utils import parse_duration, ensure_datetime, format_duration

# Parse durée
parse_duration(60)        # 60.0
parse_duration("5m")      # 300.0
parse_duration("2h30m")   # 9000.0
parse_duration("1d")      # 86400.0

# Conversion datetime
ensure_datetime("2025-08-21 12:00:00")  # datetime object
ensure_datetime("2025-08-21")           # datetime object

# Format durée
format_duration(90)      # "1m 30s"
format_duration(3661)    # "1h 1m 1s"
format_duration(86401)   # "1j 1s"
```

### Import et fonctions

| Fonction | Paramètres | Retour | Description |
|----------|------------|---------|-------------|
| `import_function(module_path, function_name)` | `str, str` | `Callable` | Import dynamique |
| `safe_call(func, *args, **kwargs)` | `Callable, ...` | `Tuple[bool, Any, str]` | Appel sécurisé |
| `get_function_info(func)` | `Callable` | `Dict` | Infos sur fonction |

**Exemples :**
```python
from pyscheduler.utils import import_function, safe_call, get_function_info

# Import dynamique
func = import_function("math", "sqrt")
result = func(16)  # 4.0

# Appel sécurisé
success, result, error = safe_call(func, 16)
if success:
    print(f"Résultat: {result}")
else:
    print(f"Erreur: {error}")

# Infos fonction
info = get_function_info(func)
print(info['name'])      # "sqrt"
print(info['module'])    # "math"
print(info['is_async'])  # False
```

### Utilitaires divers

| Fonction | Paramètres | Retour | Description |
|----------|------------|---------|-------------|
| `create_safe_filename(name)` | `str` | `str` | Nom fichier sécurisé |
| `deep_merge_dicts(dict1, dict2)` | `dict, dict` | `dict` | Fusion récursive |

**Exemples :**
```python
from pyscheduler.utils import create_safe_filename, deep_merge_dicts

# Nom fichier sécurisé
create_safe_filename("Task: Backup/Restore")  # "Task_Backup_Restore"
create_safe_filename("file<>name")            # "file__name"

# Fusion dictionnaires
dict1 = {"a": 1, "b": {"x": 1}}
dict2 = {"b": {"y": 2}, "c": 3}
result = deep_merge_dicts(dict1, dict2)
# {"a": 1, "b": {"x": 1, "y": 2}, "c": 3}
```

---

## Exemples d'utilisation

### Logger complet

```python
from pyscheduler.utils import setup_default_logger, get_default_logger

# Configuration
setup_default_logger(
    level="INFO",
    log_file="app.log", 
    json_format=True
)

logger = get_default_logger()

# Utilisation dans une tâche
def backup_task():
    logger.task_started("backup", database="users")
    
    try:
        # Simulation travail
        import time
        time.sleep(2)
        
        logger.info("Sauvegarde en cours", progress="50%")
        time.sleep(2)
        
        logger.task_completed("backup", 4.0, size="1.2GB")
        
    except Exception as e:
        logger.task_failed("backup", str(e))
        raise
```

### Validation et parsing

```python
from pyscheduler.utils import (
    validate_cron_expression, parse_duration, 
    ensure_datetime, ValidationError
)

def parse_schedule_config(schedule_data):
    """Parse et valide une configuration de planification"""
    
    schedule_type = schedule_data.get("type")
    schedule_value = schedule_data.get("value")
    
    try:
        if schedule_type == "cron":
            validate_cron_expression(schedule_value)
            return schedule_type, schedule_value
            
        elif schedule_type == "interval":
            seconds = parse_duration(schedule_value)
            return schedule_type, seconds
            
        elif schedule_type == "once":
            dt = ensure_datetime(schedule_value)
            return schedule_type, dt
            
        else:
            raise ValidationError(f"Type de planification inconnu: {schedule_type}")
            
    except ValidationError as e:
        logger.error(f"Configuration invalide: {e}")
        raise
```

### Import et exécution sécurisée

```python
from pyscheduler.utils import import_function, safe_call, get_function_info

def execute_task_function(module_name, function_name, *args, **kwargs):
    """Exécute une fonction de tâche de manière sécurisée"""
    
    try:
        # Import de la fonction
        func = import_function(module_name, function_name)
        
        # Obtenir des infos sur la fonction
        info = get_function_info(func)
        logger.debug(f"Exécution de {info['name']}", module=info['module'])
        
        # Exécution sécurisée
        success, result, error = safe_call(func, *args, **kwargs)
        
        if success:
            logger.info(f"Fonction exécutée avec succès", result=str(result)[:100])
            return result
        else:
            logger.error(f"Erreur d'exécution: {error}")
            raise RuntimeError(error)
            
    except Exception as e:
        logger.error(f"Échec import/exécution: {e}")
        raise
```

### Gestion de configuration avancée

```python
from pyscheduler.utils import deep_merge_dicts, create_safe_filename
import json

def merge_configurations(base_config, override_config):
    """Fusionne deux configurations"""
    
    # Fusion récursive
    merged = deep_merge_dicts(base_config, override_config)
    
    # Création d'un nom de fichier sécurisé pour sauvegarde
    config_name = f"merged_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    safe_filename = create_safe_filename(config_name) + ".json"
    
    # Sauvegarde
    with open(safe_filename, 'w') as f:
        json.dump(merged, f, indent=2, default=str)
    
    logger.info(f"Configuration fusionnée sauvée: {safe_filename}")
    return merged
```

---

## Intégration avec les autres modules

Les utilitaires sont utilisés massivement dans tout PyScheduler :

### Dans la configuration
```python
# config/manager.py utilise :
from ..utils import (
    ConfigurationError, ValidationError,
    validate_cron_expression, parse_duration,
    import_function, get_default_logger
)
```

### Dans le core
```python
# core/scheduler.py utilise :
from ..utils import (
    get_default_logger, PySchedulerError,
    safe_call, format_duration
)
```

### Dans CLI
```python
# cli/main.py utilise :
from ..utils import (
    setup_default_logger, ValidationError,
    create_safe_filename
)
```

Cette architecture évite toute duplication de code et assure la cohérence à travers tout le projet.

---

## Notes de performance

- **Logging :** Le logger utilise des handlers Python standard, optimisés pour la performance
- **Validation :** Les validations sont mises en cache quand possible  
- **Import dynamique :** Les modules importés sont mis en cache par Python
- **Parsing :** Les regex de parsing sont compilées une seule fois

## Extensibilité

Les utilitaires sont conçus pour être facilement étendus :

```python
# Ajout d'une nouvelle exception
class CustomTaskError(TaskError):
    def __init__(self, task_name, custom_info):
        super().__init__(f"Erreur personnalisée pour {task_name}")
        self.custom_info = custom_info

# Ajout d'un validator personnalisé  
def validate_custom_format(value):
    if not value.startswith("CUSTOM_"):
        raise ValidationError("Doit commencer par CUSTOM_")
    return True
```