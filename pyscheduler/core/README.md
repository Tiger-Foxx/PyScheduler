# Documentation Technique du Cœur de PyScheduler (`pyscheduler/core`)

Ce document fournit une description technique détaillée de chaque module, classe et fonction importante au sein du dossier `core`. Il est destiné aux développeurs et a pour but de servir de référence API interne.

---

## Table des Matières
1.  [**Module `scheduler.py`**](#1-module-schedulerpy---le-chef-dorchestre)
2.  [**Module `task.py`**](#2-module-taskpy---lunité-de-travail)
3.  [**Module `triggers.py`**](#3-module-triggerspy---le-mécanisme-de-planification)
4.  [**Module `executors.py`**](#4-module-executorspy---le-moteur-dexécution)

---

## 1. Module `scheduler.py` - Le Chef d'Orchestre

Ce module contient la classe principale `PyScheduler` qui agit comme le point d'entrée central et le coordinateur de tout le système.

### Classe `PyScheduler`
Gère le cycle de vie, le registre des tâches, la configuration et la coordination des exécuteurs.

#### Méthodes Principales

-   `__init__(config, config_file, timezone, ...)`
    -   **Description**: Initialise le scheduler. Charge la configuration depuis un objet, un fichier, ou les paramètres fournis. Met en place les logs, les exécuteurs par défaut et les gestionnaires de sortie (`atexit`, `signal`).
    -   **Paramètres**:
        -   `config: PySchedulerConfig`: Un objet de configuration complet.
        -   `config_file: str`: Chemin vers un fichier de configuration YAML.
        -   `...`: Multiples paramètres pour surcharger la configuration par défaut (log, persistance, etc.).

-   `add_task(func, name, interval, cron, ...)` -> `Union[Task, Callable]`
    -   **Description**: Ajoute une tâche au scheduler. C'est une méthode flexible qui peut être utilisée directement ou comme décorateur.
    -   **Paramètres**:
        -   `func: Callable`: La fonction à exécuter. Si `None`, la méthode retourne un décorateur.
        -   `name: str`: Nom unique de la tâche.
        -   `interval`, `cron`, `daily_at`, etc.: Paramètres de planification (un seul autorisé par tâche).
        -   `priority`, `timeout`, `executor`, etc.: Paramètres de configuration de l'exécution.
    -   **Retourne**: Une instance de `Task` si `func` est fourni, sinon un décorateur.

-   `start()`
    -   **Description**: Démarre le scheduler. Cette action charge les tâches, démarre les exécuteurs et lance les threads de contrôle (boucle de planification et de monitoring).

-   `stop(timeout: float = 30.0)`
    -   **Description**: Arrête proprement le scheduler. Exécute les tâches `on_shutdown`, arrête les threads de contrôle et les exécuteurs, et sauvegarde l'état si la persistance est activée.

-   `run_task_now(task_name: str, executor_name: str = None)` -> `str`
    -   **Description**: Force l'exécution immédiate d'une tâche, en contournant sa planification normale.
    -   **Retourne**: L'ID de la demande d'exécution.

-   `get_task(task_name: str)` -> `Optional[Task]`
    -   **Description**: Récupère une instance de tâche par son nom.

-   `list_tasks(include_disabled: bool = True, tags: Set[str] = None)` -> `List[Task]`
    -   **Description**: Retourne une liste de toutes les tâches enregistrées, avec des options de filtrage.

-   `get_stats()` -> `dict`
    -   **Description**: Retourne un dictionnaire contenant les statistiques complètes du scheduler (état, uptime, stats des tâches, stats des exécuteurs).

### Classe `SchedulerState`
Un `Enum` qui définit les états de fonctionnement possibles du scheduler.
-   `STOPPED`, `STARTING`, `RUNNING`, `STOPPING`, `PAUSED`.

---

## 2. Module `task.py` - L'Unité de Travail

Ce module définit la classe `Task`, qui est une représentation complète et autonome d'une action planifiée.

### Classe `Task`
Encapsule une fonction, sa planification, son état, sa configuration d'exécution et ses statistiques.

#### Méthodes et Propriétés Clés

-   `__init__(name, func, schedule_type, ...)`
    -   **Description**: Initialise une tâche. Valide la configuration et calcule la première `next_run_time`.
    -   **Paramètres**: Contient toute la configuration d'une tâche (nom, fonction, type de planification, priorité, timeout, configuration de retry, etc.).

-   `should_run(current_time: datetime)` -> `bool`
    -   **Description**: Méthode cruciale appelée par la boucle principale du scheduler. Détermine si la tâche doit s'exécuter maintenant en comparant `current_time` à `self.next_run_time`.

-   `execute()` -> `TaskExecution`
    -   **Description**: Point d'entrée pour l'exécution de la tâche. Gère la logique de `timeout` et de `retry` (`_execute_with_retry`), appelle la fonction cible, et met à jour les statistiques.
    -   **Retourne**: Un objet `TaskExecution` contenant tous les détails de cette exécution spécifique.

-   `cancel()`, `pause()`, `resume()`
    -   **Description**: Méthodes pour contrôler l'état de la tâche. `pause()` désactive la tâche, `resume()` la réactive, et `cancel()` la désactive de manière permanente.

-   `to_dict()` -> `dict`
    -   **Description**: Sérialise l'état complet de la tâche (configuration, état, statistiques) en un dictionnaire.

-   `is_running: bool` (Propriété)
    -   **Description**: Retourne `True` si la tâche est actuellement en cours d'exécution.

### Dataclasses de Support

-   **`TaskStatus(Enum)`**: Définit les états possibles d'une *exécution* de tâche (`PENDING`, `RUNNING`, `SUCCESS`, `FAILED`, `TIMEOUT`, `CANCELLED`).
-   **`TaskExecution`**: Stocke les informations d'une seule exécution : heures de début/fin, durée, statut, résultat, erreur, etc. C'est le "reçu" d'une exécution.
-   **`TaskStats`**: Agrège les statistiques de toutes les exécutions d'une tâche : nombre total, taux de succès, durées min/max/moyenne, etc.

---

## 3. Module `triggers.py` - Le Mécanisme de Planification

Ce module fournit les classes (triggers) qui calculent la prochaine date d'exécution d'une tâche.

### Classe `BaseTrigger`
Classe de base abstraite qui définit l'interface pour tous les triggers.

-   `get_next_run_time(last_run: Optional[datetime])` -> `Optional[datetime]`
    -   **Description**: Méthode abstraite que chaque trigger doit implémenter. Calcule et retourne la prochaine date d'exécution en se basant sur la dernière.

### Implémentations des Triggers

Chaque classe hérite de `BaseTrigger` et implémente `get_next_run_time` avec sa propre logique :
-   **`IntervalTrigger`**: Pour des intervalles réguliers (ex: toutes les 30 secondes).
-   **`CronTrigger`**: Pour des expressions cron (ex: `"0 9 * * *"`).
-   **`DailyTrigger`**: Pour une heure fixe chaque jour (ex: `"14:30"`).
-   **`WeeklyTrigger`**: Pour un jour de la semaine et une heure fixes (ex: `(0, "09:00")` pour Lundi à 9h).
-   **`OnceTrigger`**: Pour une exécution unique à une date/heure précise.
-   **`StartupTrigger`**: Pour une exécution au démarrage du scheduler.
-   **`ShutdownTrigger`**: Pour une exécution à l'arrêt du scheduler.
-   **`MonthlyTrigger`**: Pour un jour du mois et une heure fixes.

### Classe `TriggerFactory`

-   `create_trigger(schedule_type: ScheduleType, schedule_value: any)` -> `BaseTrigger`
    -   **Description**: Méthode statique qui reçoit un type de planification et sa valeur, et retourne l'instance du trigger concret correspondant. C'est le point central pour la création des triggers.

---

## 4. Module `executors.py` - Le Moteur d'Exécution

Ce module fournit les classes (exécuteurs) qui gèrent *comment* une tâche est exécutée (threading, async, etc.).

### Classe `BaseExecutor`
Classe de base abstraite qui définit l'interface pour toutes les stratégies d'exécution.

-   `submit_task(task: Task, priority: Priority)` -> `str`
    -   **Description**: Soumet une tâche pour exécution. La tâche est généralement placée dans une file d'attente interne.
-   `start()` / `stop()`
    -   **Description**: Gèrent le cycle de vie du pool de workers de l'exécuteur.

### Implémentations des Exécuteurs

-   **`ThreadExecutor`**: Utilise un `concurrent.futures.ThreadPoolExecutor`. Idéal pour les tâches I/O-bound. **C'est l'exécuteur par défaut.**
-   **`AsyncExecutor`**: Utilise `asyncio` et un `asyncio.Semaphore` pour exécuter des tâches `async` de manière native et concurrente.
-   **`ImmediateExecutor`**: Exécute les tâches immédiatement dans le thread appelant. Principalement pour les tests et le débogage.

### Classe `ExecutorManager`
Gère une collection de plusieurs exécuteurs, permettant des stratégies d'exécution complexes.

-   `add_executor(name: str, executor: BaseExecutor, is_default: bool = False)`
    -   **Description**: Enregistre une nouvelle instance d'exécuteur sous un nom donné.
-   `route_task(task_name: str, executor_name: str)`
    -   **Description**: Crée une règle pour qu'une tâche spécifique soit toujours envoyée à un exécuteur spécifique, au lieu de celui par défaut.
-   `submit_task(task: Task)` -> `str`
    -   **Description**: Reçoit une tâche du scheduler, détermine quel exécuteur doit la gérer (en fonction des règles de routage ou de l'exécuteur par défaut), et la lui transmet.

### Dataclasses de Support

-   **`ExecutionRequest`**: Objet interne qui encapsule une `Task` et sa `Priority` pour être placé dans la `PriorityQueue` des exécuteurs.
-   **`ExecutorStats`**: Stocke les statistiques d'un exécuteur (tâches actives, taille de la file d'attente, nombre total d'exécutions, etc.).