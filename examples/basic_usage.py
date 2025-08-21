"""
PyScheduler - Exemples d'usage basique
======================================

Ce fichier montre les utilisations les plus courantes de PyScheduler.
Parfait pour débuter avec le module.
"""

import time
from datetime import datetime
from pyscheduler import PyScheduler, task, startup, shutdown, daily

# ============================================================================
# EXEMPLE 1: Tâches simples avec décorateurs
# ============================================================================

@task(5)  # Toutes les 5 secondes
def check_system():
    """Vérification système périodique"""
    print(f"🔍 Vérification système à {datetime.now().strftime('%H:%M:%S')}")
    return "system_ok"

@task(interval=10)  # Syntaxe alternative
def backup_data():
    """Sauvegarde des données"""
    print(f"💾 Sauvegarde en cours à {datetime.now().strftime('%H:%M:%S')}")
    # Simulation d'une sauvegarde
    time.sleep(1)
    print("✅ Sauvegarde terminée")
    return "backup_completed"

# ============================================================================
# EXEMPLE 2: Tâches de cycle de vie
# ============================================================================

@startup()
def initialize_app():
    """Initialisation au démarrage"""
    print("🚀 Application démarrée - Initialisation en cours...")
    return "init_ok"

@shutdown()
def cleanup_app():
    """Nettoyage à l'arrêt"""
    print("🧹 Nettoyage avant arrêt...")
    return "cleanup_ok"

# ============================================================================
# EXEMPLE 3: Tâches planifiées à des heures précises
# ============================================================================

@daily("09:00")
def morning_report():
    """Rapport quotidien du matin"""
    print("📊 Génération du rapport quotidien...")
    return "report_generated"

@task(cron="0 */2 * * *")  # Toutes les 2 heures
def hourly_maintenance():
    """Maintenance bi-horaire"""
    print("🔧 Maintenance automatique...")
    return "maintenance_done"

# ============================================================================
# EXEMPLE 4: Ajout programmatique de tâches
# ============================================================================

def send_notification(message="Notification par défaut"):
    """Envoie une notification"""
    print(f"📢 Notification: {message}")
    return f"sent: {message}"

def process_queue():
    """Traitement de la queue"""
    print("⚙️ Traitement de la queue...")
    return "queue_processed"

# ============================================================================
# EXEMPLE 5: Usage avec context manager
# ============================================================================

def example_basic_context_manager():
    """Utilisation avec context manager (recommandé)"""
    print("\n" + "="*60)
    print("📋 EXEMPLE: Context Manager")
    print("="*60)
    
    with PyScheduler() as scheduler:
        # Ajouter une tâche programmatiquement
        scheduler.add_task(
            func=send_notification,
            interval=3,
            name="notifier",
            kwargs={'message': 'Hello PyScheduler!'}
        )
        
        print("⏰ Scheduler actif pour 10 secondes...")
        time.sleep(10)
    
    print("✅ Scheduler arrêté automatiquement")

# ============================================================================
# EXEMPLE 6: Usage manuel (plus de contrôle)
# ============================================================================

def example_manual_control():
    """Contrôle manuel du scheduler"""
    print("\n" + "="*60)
    print("📋 EXEMPLE: Contrôle Manuel")
    print("="*60)
    
    # Créer le scheduler
    scheduler = PyScheduler(log_level="INFO")
    
    # Ajouter des tâches dynamiquement
    scheduler.add_task(process_queue, interval=7, name="queue_processor")
    
    try:
        # Démarrer
        scheduler.start()
        print("⏰ Scheduler démarré manuellement...")
        
        # Laisser tourner
        time.sleep(15)
        
        # Ajouter une tâche en cours d'exécution
        scheduler.add_task(
            lambda: print("🆕 Nouvelle tâche ajoutée dynamiquement!"),
            interval=4,
            name="dynamic_task"
        )
        
        # Continuer
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\n⚠️ Arrêt demandé par l'utilisateur")
    finally:
        # Arrêt propre
        scheduler.stop()
        print("✅ Scheduler arrêté proprement")

# ============================================================================
# EXEMPLE 7: Gestion d'erreurs basique
# ============================================================================

@task(8)
def task_with_potential_error():
    """Tâche qui peut échouer parfois"""
    import random
    
    if random.random() < 0.3:  # 30% de chance d'échouer
        raise Exception("Erreur simulée pour test")
    
    print("✅ Tâche exécutée avec succès")
    return "success"

# ============================================================================
# EXEMPLE 8: Informations sur les tâches
# ============================================================================

def show_scheduler_info():
    """Affiche les informations du scheduler"""
    print("\n" + "="*60)
    print("📋 EXEMPLE: Informations Scheduler")
    print("="*60)
    
    scheduler = PyScheduler()
    
    # Ajouter quelques tâches
    scheduler.add_task(lambda: print("Task 1"), interval=5, name="task1")
    scheduler.add_task(lambda: print("Task 2"), interval=10, name="task2")
    scheduler.add_task(lambda: print("Task 3"), cron="*/2 * * * *", name="task3")
    
    # Afficher la liste des tâches
    tasks = scheduler.list_tasks()
    print(f"📝 Nombre de tâches configurées: {len(tasks)}")
    
    for task_info in tasks:
        print(f"  - {task_info['name']}: {task_info['schedule_type']} "
              f"(prochaine: {task_info['next_run_time'] or 'N/A'})")
    
    scheduler.stop()

# ============================================================================
# FONCTION PRINCIPALE POUR TESTER
# ============================================================================

def main():
    """Fonction principale avec menu de choix"""
    print("🎯 PyScheduler - Exemples d'usage basique")
    print("=" * 50)
    
    examples = {
        "1": ("Tâches décorées (automatique)", lambda: run_decorated_tasks()),
        "2": ("Context Manager", example_basic_context_manager),
        "3": ("Contrôle Manuel", example_manual_control),
        "4": ("Informations Scheduler", show_scheduler_info),
        "5": ("Toutes les tâches décorées", lambda: run_all_decorated_examples()),
    }
    
    print("Choisissez un exemple:")
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

def run_decorated_tasks():
    """Lance les tâches décorées pour 20 secondes"""
    scheduler = PyScheduler(log_level="INFO")
    
    try:
        scheduler.start()
        print("⏰ Observation des tâches décorées pendant 20 secondes...")
        time.sleep(20)
    except KeyboardInterrupt:
        print("\n⚠️ Arrêt demandé")
    finally:
        scheduler.stop()

def run_all_decorated_examples():
    """Lance toutes les tâches décorées en une fois"""
    print("🎪 Toutes les tâches décorées vont s'exécuter!")
    print("Observez les différents types de planification...")
    
    scheduler = PyScheduler(log_level="INFO")
    
    try:
        scheduler.start()
        print("⏰ Tous les types de tâches actifs - Ctrl+C pour arrêter")
        
        # Boucle infinie jusqu'à interruption
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    finally:
        scheduler.stop()
        print("✅ Arrêt terminé")

if __name__ == "__main__":
    main()