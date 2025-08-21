"""
PyScheduler - Exemples de configuration par fichier
==================================================

Ce fichier démontre comment utiliser PyScheduler avec des fichiers de configuration YAML.
Idéal pour des déploiements en production et des configurations complexes.
"""

import os
import time
import yaml
from datetime import datetime
from pyscheduler import PyScheduler

# ============================================================================
# FONCTIONS MÉTIER POUR LES TÂCHES
# ============================================================================

def backup_database():
    """Sauvegarde de la base de données"""
    print(f"💾 [BACKUP] Sauvegarde de la base de données à {datetime.now().strftime('%H:%M:%S')}")
    # Simulation d'une vraie sauvegarde
    time.sleep(1)
    print("✅ [BACKUP] Sauvegarde terminée avec succès")
    return {"backup_size": "1.2GB", "duration": "1s", "status": "success"}

def send_daily_report():
    """Envoi du rapport quotidien"""
    print(f"📊 [REPORT] Génération du rapport quotidien...")
    return {
        "report_type": "daily", 
        "generated_at": datetime.now().isoformat(),
        "recipients": ["admin@company.com", "team@company.com"]
    }

def cleanup_temp_files():
    """Nettoyage des fichiers temporaires"""
    print(f"🧹 [CLEANUP] Nettoyage des fichiers temporaires...")
    import random
    files_deleted = random.randint(5, 50)
    print(f"✅ [CLEANUP] {files_deleted} fichiers supprimés")
    return {"files_deleted": files_deleted}

def system_health_check():
    """Vérification de santé du système"""
    print(f"🔍 [HEALTH] Vérification santé système...")
    import random
    
    metrics = {
        "cpu_usage": random.randint(10, 90),
        "memory_usage": random.randint(30, 85),
        "disk_usage": random.randint(20, 70),
        "timestamp": datetime.now().isoformat()
    }
    
    status = "healthy" if all(v < 80 for v in [metrics["cpu_usage"], metrics["memory_usage"], metrics["disk_usage"]]) else "warning"
    
    print(f"✅ [HEALTH] Système {status} - CPU: {metrics['cpu_usage']}%, RAM: {metrics['memory_usage']}%, Disk: {metrics['disk_usage']}%")
    return {**metrics, "status": status}

def weekly_maintenance():
    """Maintenance hebdomadaire"""
    print(f"🔧 [MAINTENANCE] Maintenance hebdomadaire en cours...")
    time.sleep(2)  # Simulation
    print("✅ [MAINTENANCE] Maintenance terminée")
    return {"maintenance_type": "weekly", "completed": True}

def process_user_registrations():
    """Traitement des inscriptions utilisateurs"""
    print(f"👥 [USERS] Traitement des nouvelles inscriptions...")
    import random
    new_users = random.randint(0, 15)
    print(f"✅ [USERS] {new_users} nouvelles inscriptions traitées")
    return {"new_users_processed": new_users}

def cache_warmup():
    """Préchauffage du cache"""
    print(f"🔥 [CACHE] Préchauffage du cache...")
    return {"cache_entries": 1250, "warmup_time": "0.8s"}

def security_scan():
    """Scan de sécurité"""
    print(f"🛡️ [SECURITY] Scan de sécurité en cours...")
    import random
    threats_found = random.randint(0, 3)
    print(f"✅ [SECURITY] Scan terminé - {threats_found} menaces détectées")
    return {"threats_found": threats_found, "scan_duration": "45s"}

# ============================================================================
# CRÉATION DES FICHIERS DE CONFIGURATION EXEMPLES
# ============================================================================

def create_example_configs():
    """Crée les fichiers de configuration d'exemple"""
    
    # Configuration basique
    basic_config = {
        'global_settings': {
            'timezone': 'Europe/Paris',
            'log_level': 'INFO',
            'max_workers': 5,
            'log_file': 'scheduler.log'
        },
        'tasks': [
            {
                'name': 'backup_task',
                'module': '__main__',
                'function': 'backup_database',
                'schedule': {
                    'type': 'interval',
                    'value': 15  # Toutes les 15 secondes pour la demo
                },
                'enabled': True,
                'priority': 'HIGH',
                'timeout': 30,
                'retry_policy': {
                    'max_attempts': 3,
                    'backoff_factor': 2.0,
                    'max_delay': 60
                },
                'tags': ['backup', 'database'],
                'metadata': {
                    'owner': 'admin',
                    'critical': True
                }
            },
            {
                'name': 'health_check',
                'module': '__main__',
                'function': 'system_health_check',
                'schedule': {
                    'type': 'interval',
                    'value': 10  # Toutes les 10 secondes
                },
                'priority': 'CRITICAL',
                'tags': ['monitoring', 'health']
            },
            {
                'name': 'cleanup_task',
                'module': '__main__',
                'function': 'cleanup_temp_files',
                'schedule': {
                    'type': 'interval',
                    'value': 30  # Toutes les 30 secondes
                },
                'priority': 'LOW',
                'tags': ['cleanup', 'maintenance']
            }
        ]
    }
    
    # Configuration de production (plus réaliste)
    production_config = {
        'global_settings': {
            'timezone': 'UTC',
            'log_level': 'INFO',
            'max_workers': 10,
            'log_file': '/var/log/pyscheduler/scheduler.log',
            'persistence_file': '/var/lib/pyscheduler/state.json'
        },
        'tasks': [
            {
                'name': 'database_backup',
                'module': '__main__',
                'function': 'backup_database',
                'schedule': {
                    'type': 'cron',
                    'value': '0 2 * * *'  # Tous les jours à 2h du matin
                },
                'enabled': True,
                'priority': 'HIGH',
                'timeout': 3600,  # 1 heure max
                'retry_policy': {
                    'max_attempts': 3,
                    'backoff_factor': 2.0,
                    'max_delay': 300
                },
                'tags': ['backup', 'database', 'critical'],
                'metadata': {
                    'owner': 'dba_team',
                    'alert_on_failure': True,
                    'business_critical': True
                }
            },
            {
                'name': 'daily_report',
                'module': '__main__',
                'function': 'send_daily_report',
                'schedule': {
                    'type': 'cron',
                    'value': '0 9 * * 1-5'  # À 9h en semaine
                },
                'priority': 'NORMAL',
                'tags': ['reporting', 'business'],
                'metadata': {
                    'owner': 'business_team'
                }
            },
            {
                'name': 'system_health',
                'module': '__main__',
                'function': 'system_health_check',
                'schedule': {
                    'type': 'interval',
                    'value': 300  # Toutes les 5 minutes
                },
                'priority': 'CRITICAL',
                'timeout': 30,
                'tags': ['monitoring', 'health', 'alerting']
            },
            {
                'name': 'temp_cleanup',
                'module': '__main__',
                'function': 'cleanup_temp_files',
                'schedule': {
                    'type': 'cron',
                    'value': '0 3 * * *'  # Tous les jours à 3h
                },
                'priority': 'LOW',
                'tags': ['cleanup', 'maintenance']
            },
            {
                'name': 'weekly_maintenance',
                'module': '__main__',
                'function': 'weekly_maintenance',
                'schedule': {
                    'type': 'cron',
                    'value': '0 1 * * 0'  # Dimanche à 1h
                },
                'priority': 'NORMAL',
                'timeout': 7200,  # 2 heures max
                'tags': ['maintenance', 'weekly']
            },
            {
                'name': 'user_processing',
                'module': '__main__',
                'function': 'process_user_registrations',
                'schedule': {
                    'type': 'interval',
                    'value': 900  # Toutes les 15 minutes
                },
                'priority': 'NORMAL',
                'tags': ['users', 'processing']
            },
            {
                'name': 'cache_warmup',
                'module': '__main__',
                'function': 'cache_warmup',
                'schedule': {
                    'type': 'cron',
                    'value': '0 */6 * * *'  # Toutes les 6 heures
                },
                'priority': 'NORMAL',
                'tags': ['cache', 'performance']
            },
            {
                'name': 'security_scan',
                'module': '__main__',
                'function': 'security_scan',
                'schedule': {
                    'type': 'cron',
                    'value': '0 4 * * *'  # Tous les jours à 4h
                },
                'priority': 'HIGH',
                'timeout': 1800,  # 30 minutes max
                'tags': ['security', 'scanning']
            }
        ]
    }
    
    # Configuration microservices
    microservice_config = {
        'global_settings': {
            'timezone': 'UTC',
            'log_level': 'DEBUG',
            'max_workers': 3,
            'service_name': 'user-service-scheduler'
        },
        'tasks': [
            {
                'name': 'user_sync',
                'module': '__main__',
                'function': 'process_user_registrations',
                'schedule': {
                    'type': 'interval',
                    'value': 30
                },
                'priority': 'HIGH',
                'tags': ['sync', 'users']
            },
            {
                'name': 'health_ping',
                'module': '__main__',
                'function': 'system_health_check',
                'schedule': {
                    'type': 'interval',
                    'value': 60
                },
                'priority': 'CRITICAL',
                'tags': ['health', 'monitoring']
            }
        ]
    }
    
    # Sauvegarder les fichiers
    configs = {
        'basic_config.yaml': basic_config,
        'production_config.yaml': production_config,
        'microservice_config.yaml': microservice_config
    }
    
    for filename, config in configs.items():
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        print(f"✅ Configuration créée: {filename}")
    
    return list(configs.keys())

# ============================================================================
# EXEMPLES D'UTILISATION
# ============================================================================

def example_basic_config():
    """Exemple avec configuration basique"""
    print("\n" + "="*70)
    print("📋 EXEMPLE: Configuration Basique")
    print("="*70)
    
    config_file = 'basic_config.yaml'
    
    if not os.path.exists(config_file):
        print(f"❌ Fichier {config_file} introuvable. Création...")
        create_example_configs()
    
    # Charger et afficher la configuration
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    print(f"📄 Configuration chargée depuis {config_file}:")
    print(f"  - Timezone: {config['global_settings']['timezone']}")
    print(f"  - Workers: {config['global_settings']['max_workers']}")
    print(f"  - Tâches: {len(config['tasks'])}")
    
    # Créer le scheduler avec la configuration
    scheduler = PyScheduler(config_file=config_file)
    
    try:
        scheduler.start()
        print("⏰ Scheduler démarré avec config basique - 30 secondes...")
        time.sleep(30)
        
        # Afficher les statistiques
        print("\n📊 Statistiques:")
        tasks = scheduler.list_tasks()
        for task in tasks:
            print(f"  - {task['name']}: {task['stats']['total_runs']} exécutions")
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé")
    finally:
        scheduler.stop()
        print("✅ Exemple basique terminé")

def example_production_config():
    """Exemple avec configuration de production"""
    print("\n" + "="*70)
    print("📋 EXEMPLE: Configuration Production")
    print("="*70)
    
    config_file = 'production_config.yaml'
    
    if not os.path.exists(config_file):
        print(f"❌ Fichier {config_file} introuvable. Création...")
        create_example_configs()
    
    # Modifier temporairement les crons pour la démo
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Adapter les intervalles pour la démo (plus courts)
    demo_config = config.copy()
    for task in demo_config['tasks']:
        if task['schedule']['type'] == 'cron':
            # Convertir en intervalles pour la démo
            if 'backup' in task['name']:
                task['schedule'] = {'type': 'interval', 'value': 20}
            elif 'report' in task['name']:
                task['schedule'] = {'type': 'interval', 'value': 25}
            elif 'weekly' in task['name']:
                task['schedule'] = {'type': 'interval', 'value': 45}
            elif 'security' in task['name']:
                task['schedule'] = {'type': 'interval', 'value': 35}
            elif 'cache' in task['name']:
                task['schedule'] = {'type': 'interval', 'value': 30}
            elif 'cleanup' in task['name']:
                task['schedule'] = {'type': 'interval', 'value': 40}
    
    # Sauvegarder la config démo
    demo_file = 'production_demo.yaml'
    with open(demo_file, 'w', encoding='utf-8') as f:
        yaml.dump(demo_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"📄 Configuration production adaptée pour démo: {demo_file}")
    print(f"  - Tâches: {len(demo_config['tasks'])}")
    
    scheduler = PyScheduler(config_file=demo_file)
    
    try:
        scheduler.start()
        print("⏰ Scheduler production en mode démo - 60 secondes...")
        
        # Monitoring en temps réel
        for i in range(12):  # 60 secondes / 5 = 12 fois
            time.sleep(5)
            tasks = scheduler.list_tasks()
            active_tasks = sum(1 for t in tasks if t['stats']['total_runs'] > 0)
            total_runs = sum(t['stats']['total_runs'] for t in tasks)
            print(f"📊 [{i*5:2d}s] {active_tasks}/{len(tasks)} tâches actives, {total_runs} exécutions totales")
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé")
    finally:
        scheduler.stop()
        
        # Nettoyage
        if os.path.exists(demo_file):
            os.remove(demo_file)
        
        print("✅ Exemple production terminé")

def example_dynamic_config_modification():
    """Exemple de modification dynamique de configuration"""
    print("\n" + "="*70)
    print("📋 EXEMPLE: Modification Dynamique de Configuration")
    print("="*70)
    
    # Créer une configuration de base
    config = {
        'global_settings': {
            'timezone': 'UTC',
            'log_level': 'INFO',
            'max_workers': 4
        },
        'tasks': [
            {
                'name': 'dynamic_task_1',
                'module': '__main__',
                'function': 'system_health_check',
                'schedule': {'type': 'interval', 'value': 8},
                'enabled': True,
                'priority': 'NORMAL'
            }
        ]
    }
    
    config_file = 'dynamic_config.yaml'
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    scheduler = PyScheduler(config_file=config_file)
    
    try:
        scheduler.start()
        print("⏰ Scheduler démarré avec 1 tâche...")
        time.sleep(10)
        
        # Ajouter une tâche dynamiquement via configuration
        print("\n🔄 Ajout d'une nouvelle tâche...")
        config['tasks'].append({
            'name': 'dynamic_task_2',
            'module': '__main__',
            'function': 'cleanup_temp_files',
            'schedule': {'type': 'interval', 'value': 12},
            'enabled': True,
            'priority': 'LOW',
            'tags': ['dynamic', 'added_runtime']
        })
        
        # Sauvegarder et recharger
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # Simuler un rechargement de config (dans une vraie app, ce serait un signal)
        scheduler.add_task(
            func=cleanup_temp_files,
            interval=12,
            name='dynamic_task_2',
            tags={'dynamic', 'added_runtime'}
        )
        
        print("✅ Nouvelle tâche ajoutée en cours d'exécution")
        time.sleep(15)
        
        # Afficher l'état final
        print("\n📊 État final:")
        tasks = scheduler.list_tasks()
        for task in tasks:
            print(f"  - {task['name']}: {task['stats']['total_runs']} exécutions, tags: {task['tags']}")
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé")
    finally:
        scheduler.stop()
        
        # Nettoyage
        if os.path.exists(config_file):
            os.remove(config_file)
        
        print("✅ Exemple modification dynamique terminé")

def example_config_validation():
    """Exemple de validation de configuration"""
    print("\n" + "="*70)
    print("📋 EXEMPLE: Validation de Configuration")
    print("="*70)
    
    # Configuration valide
    valid_config = {
        'global_settings': {
            'timezone': 'Europe/Paris',
            'log_level': 'INFO',
            'max_workers': 5
        },
        'tasks': [
            {
                'name': 'valid_task',
                'module': '__main__',
                'function': 'system_health_check',
                'schedule': {'type': 'interval', 'value': 10},
                'enabled': True
            }
        ]
    }
    
    # Configuration invalide
    invalid_config = {
        'global_settings': {
            'timezone': 'Invalid/Timezone',  # Timezone invalide
            'log_level': 'INVALID_LEVEL',    # Niveau invalide
            'max_workers': -5                # Valeur négative
        },
        'tasks': [
            {
                'name': 'invalid_task',
                'module': 'non_existent_module',  # Module inexistant
                'function': 'non_existent_function',
                'schedule': {'type': 'invalid_type', 'value': 'invalid'},  # Type invalide
                'enabled': 'not_boolean'  # Type invalide
            }
        ]
    }
    
    # Test configuration valide
    print("✅ Test configuration valide:")
    valid_file = 'valid_config.yaml'
    with open(valid_file, 'w', encoding='utf-8') as f:
        yaml.dump(valid_config, f, default_flow_style=False)
    
    try:
        scheduler = PyScheduler(config_file=valid_file)
        scheduler.start()
        print("  ✅ Configuration valide chargée avec succès")
        time.sleep(5)
        scheduler.stop()
    except Exception as e:
        print(f"  ❌ Erreur inattendue: {e}")
    finally:
        if os.path.exists(valid_file):
            os.remove(valid_file)
    
    # Test configuration invalide
    print("\n❌ Test configuration invalide:")
    invalid_file = 'invalid_config.yaml'
    with open(invalid_file, 'w', encoding='utf-8') as f:
        yaml.dump(invalid_config, f, default_flow_style=False)
    
    try:
        scheduler = PyScheduler(config_file=invalid_file)
        scheduler.start()
        print("  ❌ Configuration invalide acceptée (ne devrait pas arriver)")
        scheduler.stop()
    except Exception as e:
        print(f"  ✅ Configuration invalide rejetée correctement: {type(e).__name__}")
    finally:
        if os.path.exists(invalid_file):
            os.remove(invalid_file)

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def main():
    """Menu principal pour les exemples de configuration"""
    print("🎯 PyScheduler - Exemples de Configuration par Fichier")
    print("=" * 60)
    
    examples = {
        "1": ("Créer fichiers de configuration", create_example_configs),
        "2": ("Configuration basique", example_basic_config),
        "3": ("Configuration production", example_production_config),
        "4": ("Modification dynamique", example_dynamic_config_modification),
        "5": ("Validation de configuration", example_config_validation),
        "6": ("Voir le contenu des configs", lambda: show_config_contents()),
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

def show_config_contents():
    """Affiche le contenu des fichiers de configuration"""
    config_files = ['basic_config.yaml', 'production_config.yaml', 'microservice_config.yaml']
    
    for filename in config_files:
        if os.path.exists(filename):
            print(f"\n📄 Contenu de {filename}:")
            print("-" * 50)
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content)
        else:
            print(f"❌ {filename} n'existe pas. Créez-le d'abord avec l'option 1.")

if __name__ == "__main__":
    main()