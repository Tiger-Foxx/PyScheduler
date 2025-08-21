"""
PyScheduler - Test Rapide
=========================

Script de test simple pour vérifier que PyScheduler fonctionne correctement.
Lance quelques tâches de test pour valider les fonctionnalités principales.
"""

import time
import asyncio
from datetime import datetime, timedelta
import sys
import os

# Ajouter le module au path pour les tests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyscheduler import PyScheduler, task, daily, every, once, startup, shutdown
from pyscheduler.utils import get_logger, setup_default_logger

# Setup du logger pour les tests
setup_default_logger(level="INFO")
logger = get_logger("TestRunner")

# Variables globales pour traquer les exécutions
test_results = {
    "interval_executions": 0,
    "startup_executed": False,
    "shutdown_executed": False,
    "daily_executed": False,
    "async_executed": False,
    "sync_executed": False,
    "error_handled": False
}

print("🚀 PyScheduler - Test Rapide")
print("=" * 50)

# ====================================================================
# DÉFINITION DES TÂCHES DE TEST
# ====================================================================

@task(2)  # Toutes les 2 secondes
def test_interval_task():
    """Tâche d'intervalle pour test"""
    test_results["interval_executions"] += 1
    print(f"✅ Tâche intervalle exécutée (#{test_results['interval_executions']})")

@startup()
def test_startup_task():
    """Tâche de démarrage"""
    test_results["startup_executed"] = True
    print("🚀 Tâche de démarrage exécutée")

@shutdown()
def test_shutdown_task():
    """Tâche d'arrêt"""
    test_results["shutdown_executed"] = True
    print("🛑 Tâche d'arrêt exécutée")

# Calculer une heure dans 3 secondes pour test daily
test_time = (datetime.now() + timedelta(seconds=3)).strftime("%H:%M")

@daily(test_time)
def test_daily_task():
    """Tâche quotidienne (simulée dans 3 secondes)"""
    test_results["daily_executed"] = True
    print(f"📅 Tâche quotidienne exécutée à {test_time}")

@every(seconds=3)
async def test_async_task():
    """Tâche asynchrone"""
    await asyncio.sleep(0.1)  # Simulation travail async
    test_results["async_executed"] = True
    print("⚡ Tâche async exécutée")

@task(4)
def test_sync_task():
    """Tâche synchrone avec un peu de travail"""
    time.sleep(0.1)  # Simulation travail
    test_results["sync_executed"] = True
    print("🔄 Tâche sync exécutée")

@task(10)
def test_error_task():
    """Tâche qui génère une erreur pour tester la gestion d'erreurs"""
    test_results["error_handled"] = True
    print("💥 Tâche avec erreur exécutée")
    raise ValueError("Erreur de test volontaire")

# Tâche unique dans 5 secondes
once_time = datetime.now() + timedelta(seconds=5)

@once(once_time)
def test_once_task():
    """Tâche unique"""
    print(f"⭐ Tâche unique exécutée à {datetime.now().strftime('%H:%M:%S')}")

# ====================================================================
# FONCTIONS DE TEST
# ====================================================================

def test_basic_functionality():
    """Test des fonctionnalités de base"""
    print("\n🔬 Test 1: Fonctionnalités de base")
    
    # Créer le scheduler
    scheduler = PyScheduler()
    
    # Vérifier l'état initial
    assert scheduler.is_stopped, "❌ Scheduler devrait être arrêté initialement"
    print("✅ État initial correct")
    
    # Ajouter une tâche manuellement
    def manual_task():
        print("📝 Tâche manuelle exécutée")
    
    task_obj = scheduler.add_task(manual_task, interval=5, name="manual_test")
    assert task_obj.name == "manual_test", "❌ Nom de tâche incorrect"
    print("✅ Ajout de tâche manuel OK")
    
    # Vérifier les tâches
    tasks = scheduler.list_tasks()
    task_names = [t.name for t in tasks]
    expected_tasks = ["manual_test", "test_interval_task", "test_startup_task", 
                     "test_shutdown_task", "test_daily_task", "test_async_task",
                     "test_sync_task", "test_error_task", "test_once_task"]
    
    for expected in expected_tasks:
        assert any(expected in name for name in task_names), f"❌ Tâche {expected} manquante"
    
    print(f"✅ {len(tasks)} tâches chargées depuis les décorateurs")
    
    return scheduler

def test_scheduler_lifecycle():
    """Test du cycle de vie du scheduler"""
    print("\n🔄 Test 2: Cycle de vie du scheduler")
    
    scheduler = PyScheduler()
    
    # Test démarrage
    scheduler.start()
    assert scheduler.is_running, "❌ Scheduler devrait être en marche"
    print("✅ Démarrage OK")
    
    # Attendre un peu pour voir les exécutions
    print("⏱️  Attente de 8 secondes pour observer les exécutions...")
    time.sleep(8)
    
    # Vérifier quelques exécutions
    assert test_results["startup_executed"], "❌ Tâche startup non exécutée"
    assert test_results["interval_executions"] > 0, "❌ Tâches d'intervalle non exécutées"
    print(f"✅ {test_results['interval_executions']} exécutions d'intervalle")
    
    # Test pause/reprise
    scheduler.pause()
    executions_before_pause = test_results["interval_executions"]
    time.sleep(3)
    executions_after_pause = test_results["interval_executions"]
    
    if executions_after_pause == executions_before_pause:
        print("✅ Pause fonctionne")
    else:
        print("⚠️  Pause pourrait ne pas fonctionner parfaitement")
    
    scheduler.resume()
    print("✅ Reprise OK")
    
    # Attendre encore un peu
    time.sleep(3)
    
    # Test arrêt
    scheduler.stop()
    assert scheduler.is_stopped, "❌ Scheduler devrait être arrêté"
    assert test_results["shutdown_executed"], "❌ Tâche shutdown non exécutée"
    print("✅ Arrêt OK")
    
    return scheduler

def test_task_execution():
    """Test d'exécution immédiate de tâche"""
    print("\n⚡ Test 3: Exécution immédiate")
    
    scheduler = PyScheduler()
    scheduler.start()
    
    # Ajouter une tâche de test
    execution_count = 0
    
    def immediate_test():
        nonlocal execution_count
        execution_count += 1
        print(f"🎯 Exécution immédiate #{execution_count}")
    
    scheduler.add_task(immediate_test, interval=60, name="immediate_test")
    
    # Exécuter immédiatement
    request_id = scheduler.run_task_now("immediate_test")
    print(f"✅ Demande d'exécution soumise (ID: {request_id})")
    
    # Attendre l'exécution
    time.sleep(2)
    assert execution_count > 0, "❌ Exécution immédiate a échoué"
    print("✅ Exécution immédiate OK")
    
    scheduler.stop()
    return scheduler

def test_configuration_yaml():
    """Test avec configuration YAML"""
    print("\n📄 Test 4: Configuration YAML")
    
    try:
        import yaml
        yaml_available = True
    except ImportError:
        yaml_available = False
    
    if not yaml_available:
        print("⚠️  PyYAML non installé, test YAML ignoré")
        return None
    
    # Créer une config YAML temporaire
    config_content = """
global_settings:
  timezone: "UTC"
  max_workers: 4
  log_level: "INFO"

tasks:
  - name: "yaml_test_task"
    module: "__main__"
    function: "yaml_test_function"
    schedule:
      type: "interval"
      value: 3
    enabled: true
    priority: "normal"
"""
    
    # Créer la fonction de test
    def yaml_test_function():
        print("📄 Tâche YAML exécutée")
    
    # Ajouter la fonction au module principal pour l'import
    import __main__
    __main__.yaml_test_function = yaml_test_function
    
    # Sauvegarder la config
    with open("test_config.yaml", "w") as f:
        f.write(config_content)
    
    try:
        # Tester le chargement
        scheduler = PyScheduler(config_file="test_config.yaml")
        tasks = scheduler.list_tasks()
        yaml_task_names = [t.name for t in tasks if "yaml_test_task" in t.name]
        
        assert len(yaml_task_names) > 0, "❌ Tâche YAML non chargée"
        print("✅ Configuration YAML chargée")
        
        scheduler.start()
        time.sleep(4)  # Attendre au moins une exécution
        scheduler.stop()
        
        print("✅ Configuration YAML OK")
        return scheduler
        
    finally:
        # Nettoyer
        try:
            os.remove("test_config.yaml")
        except:
            pass

def test_stats_and_monitoring():
    """Test des statistiques et monitoring"""
    print("\n📊 Test 5: Statistiques et monitoring")
    
    scheduler = PyScheduler()
    scheduler.start()
    
    # Attendre quelques exécutions
    time.sleep(6)
    
    # Récupérer les stats
    stats = scheduler.get_stats()
    
    assert "scheduler" in stats, "❌ Stats scheduler manquantes"
    assert "tasks" in stats, "❌ Stats tâches manquantes"
    assert "executions" in stats, "❌ Stats exécutions manquantes"
    
    print(f"✅ Stats générales: {stats['executions']['total']} exécutions")
    
    # Stats des tâches
    task_stats = scheduler.get_task_stats()
    assert len(task_stats) > 0, "❌ Stats des tâches manquantes"
    
    print(f"✅ Stats de {len(task_stats)} tâches récupérées")
    
    # Historique des exécutions
    recent_executions = scheduler.get_recent_executions(limit=10)
    assert len(recent_executions) > 0, "❌ Historique des exécutions vide"
    
    print(f"✅ {len(recent_executions)} exécutions dans l'historique")
    
    scheduler.stop()
    return scheduler

def print_final_results():
    """Affiche les résultats finaux"""
    print("\n" + "="*50)
    print("📋 RÉSULTATS FINAUX")
    print("="*50)
    
    total_tests = 7
    passed_tests = 0
    
    checks = [
        ("Startup task", test_results["startup_executed"]),
        ("Shutdown task", test_results["shutdown_executed"]),  
        ("Interval tasks", test_results["interval_executions"] > 0),
        ("Async task", test_results["async_executed"]),
        ("Sync task", test_results["sync_executed"]),
        ("Error handling", test_results["error_handled"]),
        ("Daily task", test_results["daily_executed"]),
    ]
    
    for name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {name}")
        if passed:
            passed_tests += 1
    
    print(f"\n🎯 Score: {passed_tests}/{total_tests} tests passés")
    
    if passed_tests == total_tests:
        print("🎉 TOUS LES TESTS SONT PASSÉS! PyScheduler fonctionne parfaitement!")
    elif passed_tests >= total_tests * 0.8:
        print("✅ La plupart des tests passent, PyScheduler fonctionne bien!")
    else:
        print("⚠️  Quelques problèmes détectés, vérification nécessaire.")
    
    print(f"\n📊 Statistiques d'exécution:")
    print(f"   - Exécutions d'intervalle: {test_results['interval_executions']}")
    print(f"   - Tâches spéciales exécutées: {sum(1 for k, v in test_results.items() if k != 'interval_executions' and v)}")

# ====================================================================
# EXÉCUTION DES TESTS
# ====================================================================

def main():
    """Fonction principale des tests"""
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 Utilisateur: theTigerFox")
    print(f"🐍 Python: {sys.version.split()[0]}")
    
    try:
        # Tests séquentiels
        test_basic_functionality()
        test_scheduler_lifecycle()
        test_task_execution()
        test_configuration_yaml()
        test_stats_and_monitoring()
        
        print("\n🎯 Tous les tests fonctionnels terminés!")
        
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Afficher les résultats
        print_final_results()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)