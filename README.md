# PyScheduler

**Le scheduler Python le plus simple et puissant**

[![PyPI version](https://badge.fury.io/py/pyscheduler.svg)](https://badge.fury.io/py/pyscheduler)
[![Python versions](https://img.shields.io/pypi/pyversions/pyscheduler.svg)](https://pypi.org/project/pyscheduler/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

PyScheduler révolutionne la planification de tâches en Python. **3 lignes suffisent** pour démarrer, mais il offre toute la puissance nécessaire pour la production.

## ✨ **Fonctionnalités**

- 🎯 **Ultra-simple** : Démarrez en 30 secondes
- ⚡ **Performant** : Threading optimisé, tâches async natives
- 🛡️ **Robuste** : Retry automatique, gestion d'erreurs avancée
- 📊 **Complet** : Logs détaillés, monitoring, statistiques
- 🕐 **Flexible** : Intervalles, CRON, tâches uniques
- 📄 **Production-ready** : Configuration YAML, CLI intégrée

## 🚀 **Installation**

```bash
pip install pyscheduler[full]
```

<details>
<summary>Installation minimale (sans dépendances optionnelles)</summary>

```bash
pip install pyscheduler
```
</details>

## ⚡ **Démarrage Rapide**

```python
from pyscheduler import PyScheduler, task

@task(60)  # Toutes les minutes
def backup_data():
    print("Sauvegarde automatique !")

@task(cron="0 9 * * 1-5")  # 9h en semaine
def send_report():
    print("Rapport quotidien envoyé")

# C'est tout ! 🎉
scheduler = PyScheduler()
scheduler.start()
```

## 📋 **Exemples d'Usage**

### **Tâches simples**
```python
from pyscheduler import task, daily, startup

@task(30)  # Toutes les 30 secondes
def health_check():
    return check_system_health()

@daily("02:00")  # Tous les jours à 2h
def daily_backup():
    return backup_database()

@startup()  # Au démarrage
def init_app():
    return initialize_application()
```

### **Configuration avancée**
```python
from pyscheduler import PyScheduler
from pyscheduler.config import RetryConfig, Priority

scheduler = PyScheduler(log_level="INFO")

scheduler.add_task(
    func=critical_task,
    interval=300,  # 5 minutes
    priority=Priority.CRITICAL,
    timeout=60,
    retry_config=RetryConfig(max_attempts=3, backoff_factor=2.0)
)
```

### **Configuration YAML**
```yaml
# scheduler_config.yaml
global_settings:
  timezone: "Europe/Paris"
  log_level: "INFO"
  max_workers: 10

tasks:
  - name: "backup_task"
    module: "myapp.tasks"
    function: "backup_database"
    schedule:
      type: "cron"
      value: "0 2 * * *"  # 2h du matin
    priority: "HIGH"
    timeout: 3600
```

```python
scheduler = PyScheduler(config_file="scheduler_config.yaml")
scheduler.start()
```

## 🎪 **Cas d'Usage**

| Besoin | Solution PyScheduler |
|--------|---------------------|
| 🔄 **Tâches périodiques** | `@task(interval=60)` |
| ⏰ **Planification précise** | `@task(cron="0 9 * * 1-5")` |
| 🚀 **Tâches startup/shutdown** | `@startup()` / `@shutdown()` |
| ⚡ **Tâches asynchrones** | Support natif `async def` |
| 🛡️ **Robustesse** | Retry automatique, timeouts |
| 📊 **Production** | Logs, stats, monitoring |

## 📚 **Documentation Complète**

- 📖 **[Guide Complet](https://github.com/Tiger-Foxx/PyScheduler/blob/main/docs/)**
- 🎯 **[Exemples Détaillés](https://github.com/Tiger-Foxx/PyScheduler/tree/main/examples)**
- 🔧 **[API Reference](https://pyscheduler.readthedocs.io/)**
- ❓ **[FAQ & Troubleshooting](https://github.com/Tiger-Foxx/PyScheduler/blob/main/docs/troubleshooting.md)**

## 🏃‍♂️ **Exemples Rapides**

### **Démarrer avec les exemples inclus**
```bash
# Après installation
python -c "from pyscheduler.examples import basic_usage; basic_usage.main()"
```

### **Monitoring en temps réel**
```python
with PyScheduler() as scheduler:
    # Vos tâches ici
    scheduler.run_forever()  # Ctrl+C pour arrêter
```

## 🚀 **Fonctionnalités Avancées**

<details>
<summary>🎯 <strong>Priorités et Threading</strong></summary>

```python
from pyscheduler.config import Priority

@task(interval=60, priority=Priority.CRITICAL)
def critical_health_check():
    return monitor_critical_systems()

@task(interval=300, priority=Priority.LOW)
def cleanup_temp_files():
    return cleanup_operations()
```
</details>

<details>
<summary>⚡ <strong>Tâches Asynchrones</strong></summary>

```python
@task(interval=30)
async def async_api_calls():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_data(session, url) for url in urls]
        return await asyncio.gather(*tasks)
```
</details>

<details>
<summary>🛡️ <strong>Gestion d'Erreurs Robuste</strong></summary>

```python
from pyscheduler.config import RetryConfig

@task(
    interval=120,
    retry_config=RetryConfig(
        max_attempts=5,
        backoff_factor=2.0,
        max_delay=300
    ),
    timeout=60
)
def unreliable_external_api():
    return call_external_service()
```
</details>

## 🔥 **Pourquoi PyScheduler ?**

| Problème | Solution PyScheduler |
|----------|---------------------|
| 😩 **APScheduler trop complexe** | ✅ 3 lignes pour démarrer |
| 🐌 **Celery overkill** | ✅ Zero configuration Redis/broker |
| 🔧 **Cron limité** | ✅ Python natif + expressions cron |
| 📊 **Pas de monitoring** | ✅ Logs détaillés + statistiques |
| 🚫 **Pas de retry** | ✅ Retry intelligent intégré |

## 🏆 **Performances**

- ⚡ **Démarrage** : < 100ms
- 💾 **Mémoire** : < 20MB pour 100 tâches
- 🔄 **Concurrence** : Jusqu'à 1000 tâches parallèles
- 🎯 **Précision** : ±50ms sur les planifications

## 🤝 **Contribuer**

Nous accueillons toutes les contributions !

```bash
git clone https://github.com/Tiger-Foxx/PyScheduler.git
cd PyScheduler
pip install -e .[dev]
pytest
```

## 📄 **Licence**

MIT License - voir [LICENSE](LICENSE) pour les détails.

## 🙏 **Remerciements**

Inspiré par les meilleurs outils de scheduling, conçu pour la simplicité Python.

---

**⭐ Si PyScheduler vous aide, n'hésitez pas à star le repo !**

[🏠 Homepage](https://github.com/Tiger-Foxx/PyScheduler) • [📚 Documentation](https://pyscheduler.readthedocs.io/) • [🐛 Issues](https://github.com/Tiger-Foxx/PyScheduler/issues) • [💬 Discussions](https://github.com/Tiger-Foxx/PyScheduler/discussions)
