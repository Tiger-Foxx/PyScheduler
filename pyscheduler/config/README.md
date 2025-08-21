# PyScheduler - Configuration

Ce module gère toute la configuration de PyScheduler. Il propose deux approches principales :
1. **Fichiers YAML** pour configuration externe
2. **Décorateurs Python** pour configuration dans le code

## Table des matières

- [Configuration via fichier YAML](#configuration-via-fichier-yaml)
- [Configuration via décorateurs](#configuration-via-décorateurs)
- [Types de planification](#types-de-planification)
- [Configuration avancée](#configuration-avancée)
- [API du ConfigManager](#api-du-configmanager)
- [Registre des tâches](#registre-des-tâches)

---

## Configuration via fichier YAML

### Structure de base

```yaml
# scheduler_config.yaml
global_settings:
  timezone: "Europe/Paris"
  max_workers: 8
  log_level: "INFO"
  log_file: "scheduler.log"
  json_logs: false
  persistence_file: "scheduler_state.json"
  shutdown_timeout: 30.0

tasks:
  - name: "backup_task"
    module: "myapp.tasks"
    function: "backup_database"
    schedule:
      type: "daily"
      value: "03:00"
    enabled: true
    priority: "high"
    timeout: 1800  # 30 minutes
    max_runs: null
    retry_policy:
      max_attempts: 3
      backoff_factor: 2.0
      max_delay: 300
    tags: ["backup", "database"]
    metadata:
      description: "Sauvegarde quotidienne de la base"
```

### Exemple complet avec plusieurs tâches

```yaml
global_settings:
  timezone: "UTC"
  max_workers: 4
  log_level: "INFO"

tasks:
  # Tâche d'intervalle simple
  - name: "health_check"
    module: "monitoring"
    function: "check_system_health"
    schedule:
      type: "interval"
      value: 300  # 5 minutes
    enabled: true

  # Tâche avec expression cron
  - name: "weekly_report"
    module: "reports"
    function: "generate_weekly_report"
    schedule:
      type: "cron"
      value: "0 9 * * 1"  # Lundi à 9h
    priority: "normal"
    timeout: "30m"
    retry_policy:
      max_attempts: 2
      backoff_factor: 1.5

  # Tâche unique
  - name: "migration_task"
    module: "maintenance"
    function: "migrate_data"
    schedule:
      type: "once"
      value: "2025-09-01 02:00:00"
    priority: "critical"
    
  # Tâche de démarrage
  - name: "init_system"
    module: "system"
    function: "initialize"
    schedule:
      type: "startup"
      value: null
```

### Chargement d'un fichier YAML

```python
from pyscheduler.config import ConfigManager

# Charger la configuration
manager = ConfigManager()
config = manager.load_from_file("scheduler_config.yaml")

# Utiliser avec le scheduler
from pyscheduler import PyScheduler
scheduler = PyScheduler(config=config)
```

---

## Configuration via décorateurs

### Décorateurs de base

```python
from pyscheduler.config import schedule_task, task, every, daily

# Méthode explicite avec schedule_task
@schedule_task(interval=60, priority="high")
def check_logs():
    print("Vérification des logs")

# Méthode simplifiée avec auto-détection
@task(60)  # Auto-détecte: intervalle de 60 secondes
def simple_task():
    print("Tâche simple")

@task("09:30")  # Auto-détecte: quotidien à 9h30
def morning_task():
    print("Tâche matinale")

@task("0 */2 * * *")  # Auto-détecte: expression cron
def cron_task():
    print("Toutes les 2 heures")

# Méthode lisible avec every
@every(minutes=5)
def frequent_task():
    print("Toutes les 5 minutes")

@every(hours=2, minutes=30)
def periodic_task():
    print("Toutes les 2h30")

# Méthode spécialisée
@daily("14:00")
def afternoon_report():
    print("Rapport de l'après-midi")
```

### Décorateurs avancés

```python
from pyscheduler.config import weekly, once, startup, shutdown, critical

# Tâche hebdomadaire
@weekly(1, "09:00")  # Mardi à 9h (0=dimanche, 1=lundi, ...)
def weekly_maintenance():
    print("Maintenance hebdomadaire")

# Tâche unique
@once("2025-12-25 00:00:00")
def christmas_greeting():
    print("Joyeux Noël!")

# Tâches spéciales
@startup()
def initialize_app():
    print("Initialisation au démarrage")

@shutdown()
def cleanup_app():
    print("Nettoyage à l'arrêt")

# Tâche critique
@critical(interval=30)
def monitor_critical_service():
    print("Surveillance critique")
```

### Configuration complète avec décorateur

```python
@schedule_task(
    interval="5m",           # Toutes les 5 minutes
    name="custom_monitor",   # Nom personnalisé
    priority="high",         # Priorité élevée
    timeout="2m",           # Timeout de 2 minutes
    max_runs=100,           # Maximum 100 exécutions
    max_attempts=3,         # 3 tentatives en cas d'échec
    backoff_factor=2.0,     # Délai exponentiel
    max_delay="5m",         # Délai max entre tentatives
    tags=["monitoring", "critical"],
    metadata={"team": "ops", "alert": True}
)
def advanced_monitor():
    """Surveillance avancée avec configuration complète"""
    print("Surveillance en cours...")
```

---

## Types de planification

### 1. Interval (Intervalle)

Exécution toutes les X secondes.

```python
# Via décorateur
@task(60)  # 60 secondes
@every(minutes=5)  # 5 minutes
@schedule_task(interval="2h")  # 2 heures

# Via YAML
schedule:
  type: "interval"
  value: 300  # 5 minutes en secondes
```

### 2. Cron (Expression cron)

Utilise la syntaxe cron standard (5 champs).

```python
# Via décorateur  
@task("0 9 * * 1-5")  # 9h du lundi au vendredi
@schedule_task(cron="*/15 * * * *")  # Toutes les 15 minutes

# Via YAML
schedule:
  type: "cron"
  value: "0 2 * * 0"  # Dimanche à 2h
```

**Format cron :** `minute heure jour_mois mois jour_semaine`
- `*` : toutes les valeurs
- `*/5` : toutes les 5 unités
- `1-5` : plage de 1 à 5
- `1,3,5` : valeurs spécifiques

### 3. Daily (Quotidien)

Exécution tous les jours à une heure précise.

```python
# Via décorateur
@daily("09:30")
@task("14:00")  # Auto-détecté comme quotidien

# Via YAML
schedule:
  type: "daily"
  value: "03:00"
```

### 4. Weekly (Hebdomadaire)

Exécution une fois par semaine.

```python
# Via décorateur
@weekly(1, "09:00")  # Mardi à 9h

# Via YAML
schedule:
  type: "weekly"
  value: [1, "09:00"]  # [jour_semaine, heure]
```

**Jours de la semaine :** 0=dimanche, 1=lundi, ..., 6=samedi

### 5. Once (Unique)

Exécution unique à une date/heure précise.

```python
# Via décorateur
@once("2025-09-15 14:30:00")

# Via YAML
schedule:
  type: "once"
  value: "2025-09-15 14:30:00"
```

### 6. Startup/Shutdown

Exécution au démarrage ou arrêt du scheduler.

```python
# Via décorateur
@startup()
@shutdown()

# Via YAML
schedule:
  type: "startup"
  value: null
```

---

## Configuration avancée

### Gestion des erreurs et retry

```python
@schedule_task(
    interval=60,
    max_attempts=5,        # 5 tentatives maximum
    backoff_factor=1.5,    # Délai x1.5 à chaque tentative
    max_delay="10m"        # Délai maximum de 10 minutes
)
def fragile_task():
    # Code pouvant échouer
    pass
```

```yaml
retry_policy:
  max_attempts: 3
  backoff_factor: 2.0
  max_delay: 300
```

### Priorités

```python
# Via décorateur
@critical(interval=30)     # Priorité critique
@high_priority(daily="09:00")  # Priorité haute
@low_priority(weekly=(0, "23:00"))  # Priorité basse

# Via configuration
@schedule_task(interval=60, priority="normal")
```

```yaml
priority: "critical"  # critical, high, normal, low, idle
```

### Timeout

```python
@schedule_task(interval=60, timeout="5m")  # Timeout de 5 minutes
```

```yaml
timeout: 300  # 5 minutes en secondes
```

### Tags et métadonnées

```python
@schedule_task(
    interval=60,
    tags=["monitoring", "health"],
    metadata={
        "team": "ops",
        "alert_channel": "#alerts",
        "documentation": "https://wiki.company.com/task123"
    }
)
def tagged_task():
    pass
```

---

## API du ConfigManager

### Chargement de configuration

```python
from pyscheduler.config import ConfigManager

manager = ConfigManager()

# Depuis un fichier YAML
config = manager.load_from_file("config.yaml")

# Depuis un dictionnaire
config_dict = {
    "global_settings": {"timezone": "UTC"},
    "tasks": [...]
}
config = manager.load_from_dict(config_dict)
```

### Sauvegarde de configuration

```python
# Sauvegarder en YAML
manager.save_to_file(config, "output.yaml")

# Créer une configuration par défaut
manager.create_default_config("default_config.yaml")
```

### Validation

```python
# Valider qu'une fonction de tâche existe
for task in config.tasks:
    manager.validate_task_function(task)
```

### Manipulation de configuration

```python
# Ajouter une tâche
from pyscheduler.config import TaskConfig, ScheduleType

task = TaskConfig(
    name="new_task",
    function="my_function", 
    module="mymodule",
    schedule_type=ScheduleType.INTERVAL,
    schedule_value=60
)
config.add_task(task)

# Supprimer une tâche
config.remove_task("task_name")

# Récupérer une tâche
task = config.get_task("task_name")
```

---

## Registre des tâches

Le registre collecte automatiquement toutes les tâches définies avec les décorateurs.

```python
from pyscheduler.config import get_task_registry

# Dans votre code, définissez des tâches
@task(60)
def task1():
    pass

@daily("09:00")
def task2():
    pass

# Récupérer toutes les tâches enregistrées
registry = get_task_registry()
all_tasks = registry.get_all_tasks()

# Utiliser avec le scheduler
from pyscheduler import PyScheduler
scheduler = PyScheduler()

# Ajouter toutes les tâches du registre
for task_config in all_tasks:
    func = task_config.metadata['_function_ref']
    scheduler.add_task_from_config(task_config, func)
```

### Nettoyage du registre

```python
# Vider le registre (utile pour les tests)
registry = get_task_registry()
registry.clear()
```

---

## Exemples pratiques

### Application web avec surveillance

```python
from pyscheduler.config import *

@every(minutes=1)
def check_database():
    """Vérification de la base toutes les minutes"""
    # Code de vérification
    pass

@every(minutes=5)
def check_api_endpoints():
    """Test des endpoints API"""
    # Code de test
    pass

@daily("02:00")
def backup_database():
    """Sauvegarde quotidienne"""
    # Code de sauvegarde
    pass

@weekly(0, "23:00")  # Dimanche 23h
def weekly_cleanup():
    """Nettoyage hebdomadaire"""
    # Code de nettoyage
    pass

@startup()
def initialize_monitoring():
    """Initialisation au démarrage"""
    print("Système de surveillance démarré")

@shutdown()
def cleanup_monitoring():
    """Nettoyage à l'arrêt"""
    print("Arrêt du système de surveillance")
```

### Configuration mixte (YAML + décorateurs)

```python
# config.yaml
global_settings:
  timezone: "Europe/Paris"
  max_workers: 4

tasks:
  - name: "external_sync"
    module: "sync"
    function: "sync_external_data"
    schedule:
      type: "cron"
      value: "0 */6 * * *"  # Toutes les 6h

# app.py
from pyscheduler.config import *
from pyscheduler import PyScheduler

# Tâches définies par décorateur
@every(minutes=15)
def internal_health_check():
    pass

@daily("08:00")
def morning_report():
    pass

# Chargement et fusion
manager = ConfigManager()
yaml_config = manager.load_from_file("config.yaml")

registry = get_task_registry()
decorator_tasks = registry.get_all_tasks()

# Utilisation avec le scheduler
scheduler = PyScheduler(config=yaml_config)
for task_config in decorator_tasks:
    func = task_config.metadata['_function_ref']
    scheduler.add_task_from_config(task_config, func)
```

---

## Conseils d'utilisation

### 1. Choix entre YAML et décorateurs

**Utilisez YAML quand :**
- Configuration externe nécessaire
- Déploiement avec différentes configs
- Non-développeurs doivent modifier la config
- Tâches définies dans des modules séparés

**Utilisez les décorateurs quand :**
- Configuration proche du code
- Développement rapide
- Tâches simples et intégrées
- Prototypage

### 2. Bonnes pratiques

```python
# ✅ Bon : noms explicites
@task(300, name="user_cleanup")
def cleanup_inactive_users():
    pass

# ❌ Éviter : noms génériques
@task(300)
def task():
    pass

# ✅ Bon : tags pour l'organisation
@daily("03:00", tags=["backup", "critical"])
def backup_user_data():
    pass

# ✅ Bon : timeout pour tâches longues
@schedule_task(interval=3600, timeout="30m")
def long_running_task():
    pass

# ✅ Bon : métadonnées pour documentation
@task(
    "0 9 * * 1-5",
    metadata={
        "description": "Rapport quotidien des ventes",
        "owner": "team-sales",
        "documentation": "https://wiki.internal/sales-report"
    }
)
def daily_sales_report():
    pass
```

### 3. Gestion des erreurs

```python
# Configuration robuste avec retry
@schedule_task(
    interval="5m",
    max_attempts=3,
    backoff_factor=2.0,
    max_delay="10m",
    timeout="2m"
)
def api_sync():
    """Synchronisation avec API externe"""
    try:
        # Code de synchronisation
        pass
    except Exception as e:
        # Log l'erreur, elle sera gérée par le retry
        print(f"Erreur sync: {e}")
        raise
```

---

## Dépannage

### Erreurs courantes

1. **Expression cron invalide**
   ```
   ValidationError: Expression cron doit avoir 5 parties, 6 trouvées
   ```
   → Vérifiez le format : `minute heure jour mois jour_semaine`

2. **Fonction introuvable**
   ```
   ConfigurationError: Fonction 'my_func' introuvable dans 'mymodule'
   ```
   → Vérifiez que le module et la fonction existent

3. **Durée invalide**
   ```
   ValidationError: Format de durée invalide: 5x
   ```
   → Utilisez `5s`, `5m`, `5h`, `5d` ou un nombre

4. **Planification ambiguë**
   ```
   ValidationError: Une seule méthode de planification autorisée
   ```
   → N'utilisez qu'un seul paramètre : `interval` OU `cron` OU `daily_at`, etc.

### Validation de configuration

```python
from pyscheduler.config import validate_config_file

try:
    validate_config_file("my_config.yaml")
    print("Configuration valide ✅")
except Exception as e:
    print(f"Configuration invalide ❌: {e}")
```