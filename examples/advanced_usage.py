
"""
PyScheduler - Exemples d'usage avancé
====================================

Ce fichier présente les fonctionnalités avancées de PyScheduler :
- Configuration fine des retry
- Gestion des priorités  
- Hooks et callbacks
- Tâches asynchrones
- Gestion d'erreurs sophistiquée
- Monitoring et statistiques
"""

import asyncio
import time
import random
from datetime import datetime, timedelta
from pyscheduler import PyScheduler, task, startup, shutdown
from pyscheduler.config import Priority, RetryConfig

# ============================================================================
# EXEMPLE 1: Configuration avancée des retry
# ============================================================================

@task(
    interval=8,
    retry_config=RetryConfig(
        max_attempts=5,
        backoff_factor=2.0,
        max_delay=60.0
    ),
    timeout=10.0
)
def unreliable_api_call():
    """Simulation d'un appel API qui échoue parfois"""
    print(f"🌐 Tentative d'appel API à {datetime.now().strftime('%H:%M:%S')}")
    
    # 40% de chance d'échec pour simuler une API instable
    if random.random() < 0.4:
        error_types = [
            "Timeout de connexion",
            "Erreur 500 du serveur", 
            "Rate limit dépassé",
            "Service temporairement indisponible"
        ]
        raise ConnectionError(random.choice(error_types))
    
    print("✅ API appelée avec succès")
    return {"status": "success", "data": "important_data"}

# ============================================================================
# EXEMPLE 2: Gestion des priorités
# ============================================================================

@task(interval=5, priority=Priority.CRITICAL)
def critical_health_check():
    """Vérification critique de santé - priorité maximale"""
    print("🚨 [CRITIQUE] Vérification santé système")
    return "system_healthy"

@task(interval=6, priority=Priority.HIGH)
def high_priority_backup():
    """Sauvegarde haute priorité"""
    print("⚡ [HAUTE] Sauvegarde prioritaire")
    return "backup_done"

@task(interval=7, priority=Priority.NORMAL)
def normal_log_rotation():
    """Rotation des logs - priorité normale"""
    print("📋 [NORMALE] Rotation des logs")
    return "logs_rotated"

@task(interval=10, priority=Priority.LOW)
def low_priority_cleanup():
    """Nettoyage - basse priorité"""
    print("🧹 [BASSE] Nettoyage fichiers temporaires")
    return "cleanup_done"

# ============================================================================
# EXEMPLE 3: Tâches asynchrones natives
# ============================================================================

@task(interval=12)
async def async_data_processing():
    """Traitement asynchrone de données"""
    print("⚡ Début traitement async des données...")
    
    # Simulation de plusieurs opérations I/O parallèles
    async def fetch_data(source):
        await asyncio.sleep(random.uniform(0.5, 2.0))  # Simulation I/O
        return f"data_from_{source}"
    
    # Traitement parallèle
    sources = ["database", "api", "cache", "file"]
    tasks = [fetch_data(source) for source in sources]
    results = await asyncio.gather(*tasks)
    
    print(f"✅ Données traitées: {results}")
    return {"processed": len(results), "sources": sources}

@task(interval=15)
async def async_notification_batch():
    """Envoi de notifications en lot (async)"""
    print("📧 Envoi de notifications en lot...")
    
    # Simulation d'envoi de notifications
    notifications = ["email", "sms", "push", "slack"]
    
    async def send_notification(notif_type):
        await asyncio.sleep(random.uniform(0.2, 1.0))
        print(f"  ✉️ {notif_type} envoyé")
        return f"{notif_type}_sent"
    
    # Envoi parallèle
    results = await asyncio.gather(*[
        send_notification(notif) for notif in notifications
    ])
    
    print(f"✅ {len(results)} notifications envoyées")
    return {"sent": len(results)}

# ============================================================================
# EXEMPLE 4: Hooks et callbacks avancés
# ============================================================================

def before_task_hook(task_name, execution_id):
    """Hook appelé avant chaque exécution de tâche"""
    print(f"🎣 [BEFORE] Tâche {task_name} va démarrer (ID: {execution_id})")

def after_task_hook(task_name, execution_id, result, duration):
    """Hook appelé après chaque exécution réussie"""
    print(f"🎣 [AFTER] Tâche {task_name} terminée en {duration:.2f}s (résultat: {result})")

def error_task_hook(task_name, execution_id, error):
    """Hook appelé en cas d'erreur"""
    print(f"🎣 [ERROR] Tâche {task_name} échouée: {error}")

@task(interval=9)
def task_with_hooks():
    """Tâche avec hooks personnalisés"""
    print("🔧 Exécution de tâche avec hooks")
    
    # Parfois échouer pour tester le hook d'erreur
    if random.random() < 0.3:
        raise ValueError("Erreur simulée pour test hook")
    
    return "task_completed"

# ============================================================================
# EXEMPLE 5: Tâches avec dépendances et métadonnées
# ============================================================================

@task(interval=20, tags={"category": "maintenance", "level": "system"})
def system_maintenance():
    """Maintenance système avec métadonnées"""
    print("🔧 Maintenance système avec tags")
    return {"maintenance_type": "system", "completed_at": datetime.now().isoformat()}

@task(interval=25, tags={"category": "reporting", "level": "business"})
def business_reporting():
    """Rapport business avec métadonnées"""
    print("📊 Génération rapport business")
    return {"report_type": "business", "metrics": {"users": 1250, "revenue": 45600}}

# ============================================================================
# EXEMPLE 6: Monitoring et statistiques avancées
# ============================================================================

def show_advanced_monitoring():
    """Démonstration du monitoring avancé"""
    print("\n" + "="*70)
    print("📊 EXEMPLE: Monitoring et Statistiques Avancées")
    print("="*70)
    
    # Créer scheduler avec monitoring
    scheduler = PyScheduler(log_level="INFO")
    
    # Ajouter des tâches avec des configurations différentes
    scheduler.add_task(
        func=lambda: print("📈 Tâche de monitoring"),
        interval=3,
        name="monitoring_task",
        priority=Priority.HIGH,
        timeout=5.0,
        retry_config=RetryConfig(max_attempts=3),
        tags={"type": "monitoring"}
    )
    
    scheduler.add_task(
        func=lambda: random.choice([print("✅ Succès"), print("❌ Échec") or (_ for _ in ()).throw(Exception("Test"))]),
        interval=4,
        name="flaky_task", 
        retry_config=RetryConfig(max_attempts=2, backoff_factor=1.5)
    )
    
    try:
        scheduler.start()
        print("⏰ Collecte de statistiques pendant 15 secondes...")
        
        time.sleep(15)
        
        # Afficher les statistiques détaillées
        print("\n📊 Statistiques détaillées:")
        print("-" * 50)
        
        tasks = scheduler.list_tasks()
        for task_info in tasks:
            print(f"\n🎯 Tâche: {task_info['name']}")
            print(f"  📊 Stats: {task_info['stats']}")
            print(f"  ⏰ Prochaine: {task_info['next_run_time']}")
            print(f"  🏷️ Tags: {task_info['tags']}")
        
        # Statistiques des exécuteurs
        executor_stats = scheduler.get_executor_stats()
        print(f"\n⚙️ Statistiques des exécuteurs:")
        for name, stats in executor_stats.items():
            print(f"  {name}: {stats}")
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé")
    finally:
        scheduler.stop()
        print("✅ Monitoring terminé")

# ============================================================================
# EXEMPLE 7: Configuration programmatique avancée
# ============================================================================

def advanced_programmatic_config():
    """Configuration programmatique avancée"""
    print("\n" + "="*70)
    print("⚙️ EXEMPLE: Configuration Programmatique Avancée")
    print("="*70)
    
    # Scheduler avec configuration personnalisée
    scheduler = PyScheduler(
        max_workers=8,
        log_level="DEBUG",
        timezone="Europe/Paris"
    )
    
    # Configuration des hooks globaux
    scheduler.set_global_hooks(
        before_task=before_task_hook,
        after_task=after_task_hook,
        on_error=error_task_hook
    )
    
    # Tâches avec configurations très spécifiques
    tasks_config = [
        {
            "func": lambda: print("🎯 Tâche critique"),
            "interval": 5,
            "name": "critical_task",
            "priority": Priority.CRITICAL,
            "timeout": 30.0,
            "retry_config": RetryConfig(max_attempts=5, backoff_factor=3.0),
            "tags": {"critical": True, "business_unit": "core"}
        },
        {
            "func": unreliable_api_call,
            "interval": 8, 
            "name": "api_task",
            "priority": Priority.HIGH,
            "retry_config": RetryConfig(max_attempts=4, max_delay=120.0)
        }
    ]
    
    # Ajouter toutes les tâches
    for config in tasks_config:
        scheduler.add_task(**config)
    
    # Démarrage avec tâches planifiées à des moments spécifiques
    scheduler.add_task(
        func=lambda: print("🌅 Tâche du matin"),
        daily_at="09:00",
        name="morning_task"
    )
    
    try:
        scheduler.start()
        print("⏰ Configuration avancée active - 20 secondes...")
        time.sleep(20)
        
        # Modifier des tâches en cours d'exécution
        print("\n🔄 Modification dynamique des tâches...")
        scheduler.pause_task("api_task")
        print("⏸️ Tâche API mise en pause")
        
        time.sleep(5)
        
        scheduler.resume_task("api_task")
        print("▶️ Tâche API reprise")
        
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé")
    finally:
        scheduler.stop()
        print("✅ Configuration avancée terminée")

# ============================================================================
# EXEMPLE 8: Intégration avec des frameworks externes
# ============================================================================

class DatabaseManager:
    """Simulation d'un gestionnaire de base de données"""
    def __init__(self):
        self.connected = False
    
    def connect(self):
        print("🔌 Connexion à la base de données...")
        time.sleep(0.5)  # Simulation
        self.connected = True
        return "connected"
    
    def disconnect(self):
        print("🔌 Déconnexion de la base de données...")
        self.connected = False
        return "disconnected"
    
    def cleanup_old_records(self):
        if not self.connected:
            raise Exception("Database not connected")
        print("🗑️ Suppression des anciens enregistrements...")
        return {"deleted_records": random.randint(10, 100)}

# Instance globale (pattern singleton simulé)
db_manager = DatabaseManager()

@startup()
def init_database():
    """Initialisation de la base de données au démarrage"""
    return db_manager.connect()

@shutdown()
def close_database():
    """Fermeture de la base de données à l'arrêt"""
    return db_manager.disconnect()

@task(interval=30)
def database_cleanup():
    """Nettoyage périodique de la base de données"""
    try:
        result = db_manager.cleanup_old_records()
        print(f"✅ Nettoyage DB réussi: {result}")
        return result
    except Exception as e:
        print(f"❌ Erreur nettoyage DB: {e}")
        raise

# ============================================================================
# FONCTION PRINCIPALE POUR TESTER
# ============================================================================

def main():
    """Menu principal pour les exemples avancés"""
    print("🎯 PyScheduler - Exemples d'usage avancé")
    print("=" * 50)
    
    examples = {
        "1": ("Retry et timeout avancés", lambda: run_retry_examples()),
        "2": ("Gestion des priorités", lambda: run_priority_examples()),
        "3": ("Tâches asynchrones", lambda: run_async_examples()),
        "4": ("Monitoring avancé", show_advanced_monitoring),
        "5": ("Configuration programmatique", advanced_programmatic_config),
        "6": ("Intégration framework", lambda: run_framework_integration()),
        "7": ("Tous les exemples", lambda: run_all_advanced_examples()),
    }
    
    print("Choisissez un exemple avancé:")
    for key, (description, _) in examples.items():
        print(f"  {key}. {description}")
    print("  q. Quitter")
    
    choice = input("\nVotre choix: ").strip().lower()
    
    if choice == 'q':
        print("👋 Au revoir!")
        return
    
    if choice in examples:
        print(f"\n🚀 Exécution: {examples[choice][0]}")
        examples[choice][1]()
    else:
        print("❌ Choix invalide")

def run_retry_examples():
    """Lance les exemples de retry"""
    scheduler = PyScheduler(log_level="INFO")
    scheduler.add_task(unreliable_api_call)
    
    try:
        scheduler.start()
        print("⏰ Test retry pendant 30 secondes...")
        time.sleep(30)
    finally:
        scheduler.stop()

def run_priority_examples():
    """Lance les exemples de priorités"""
    scheduler = PyScheduler(log_level="INFO")
    
    try:
        scheduler.start()
        print("⏰ Test priorités pendant 25 secondes...")
        time.sleep(25)
    finally:
        scheduler.stop()

def run_async_examples():
    """Lance les exemples async"""
    scheduler = PyScheduler(log_level="INFO")
    
    try:
        scheduler.start()
        print("⏰ Test tâches async pendant 30 secondes...")
        time.sleep(30)
    finally:
        scheduler.stop()

def run_framework_integration():
    """Exemple d'intégration avec framework externe"""
    scheduler = PyScheduler(log_level="INFO")
    
    try:
        scheduler.start()
        print("⏰ Test intégration framework pendant 60 secondes...")
        time.sleep(60)
    finally:
        scheduler.stop()

def run_all_advanced_examples():
    """Lance tous les exemples avancés"""
    print("🎪 Tous les exemples avancés - Ctrl+C pour arrêter")
    
    scheduler = PyScheduler(log_level="INFO")
    
    # Configurer les hooks
    scheduler.set_global_hooks(
        before_task=before_task_hook,
        after_task=after_task_hook,
        on_error=error_task_hook
    )
    
    try:
        scheduler.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé")
    finally:
        scheduler.stop()

if __name__ == "__main__":
    main()