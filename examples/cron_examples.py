"""
PyScheduler - Exemples d'expressions CRON
=========================================

Ce fichier présente tous les types d'expressions CRON supportées par PyScheduler.
Guide complet avec exemples pratiques et cas d'usage réels.

Format CRON: * * * * *
             │ │ │ │ │
             │ │ │ │ └─── Jour de la semaine (0-7, 0 et 7 = Dimanche)
             │ │ │ └───── Mois (1-12)
             │ │ └─────── Jour du mois (1-31)
             │ └───────── Heure (0-23)
             └─────────── Minute (0-59)
"""

import time
from datetime import datetime
from pyscheduler import PyScheduler, task

# ============================================================================
# EXEMPLES CRON BASIQUES
# ============================================================================

@task(cron="*/2 * * * *")  # Toutes les 2 minutes
def every_two_minutes():
    """Tâche qui s'exécute toutes les 2 minutes"""
    print(f"⏰ [2MIN] Exécution toutes les 2 minutes - {datetime.now().strftime('%H:%M:%S')}")
    return "every_2min_ok"

@task(cron="0 * * * *")  # Toutes les heures pile
def every_hour():
    """Tâche qui s'exécute toutes les heures à la minute 0"""
    print(f"🕐 [HOURLY] Exécution horaire - {datetime.now().strftime('%H:%M:%S')}")
    return "hourly_ok"

@task(cron="0 9 * * *")  # Tous les jours à 9h
def daily_at_9am():
    """Tâche quotidienne à 9h du matin"""
    print(f"🌅 [DAILY] Rapport quotidien 9h - {datetime.now().strftime('%H:%M:%S')}")
    return "daily_9am_ok"

@task(cron="0 0 * * 0")  # Tous les dimanches à minuit
def weekly_sunday():
    """Tâche hebdomadaire le dimanche"""
    print(f"📅 [WEEKLY] Maintenance dominicale - {datetime.now().strftime('%H:%M:%S')}")
    return "weekly_sunday_ok"

# ============================================================================
# EXEMPLES CRON BUSINESS
# ============================================================================

@task(cron="0 9 * * 1-5")  # 9h en semaine (lundi à vendredi)
def business_hours_start():
    """Démarrage des heures de bureau"""
    print(f"💼 [BUSINESS] Démarrage heures bureau - {datetime.now().strftime('%H:%M:%S')}")
    return "business_start_ok"

@task(cron="0 18 * * 1-5")  # 18h en semaine
def business_hours_end():
    """Fin des heures de bureau"""
    print(f"🏠 [BUSINESS] Fin heures bureau - {datetime.now().strftime('%H:%M:%S')}")
    return "business_end_ok"

@task(cron="0 12 * * 1-5")  # Midi en semaine
def lunch_break():
    """Pause déjeuner"""
    print(f"🍽️ [LUNCH] Pause déjeuner - {datetime.now().strftime('%H:%M:%S')}")
    return "lunch_break_ok"

@task(cron="0 0 1 * *")  # Le 1er de chaque mois à minuit
def monthly_report():
    """Rapport mensuel"""
    print(f"📊 [MONTHLY] Rapport mensuel - {datetime.now().strftime('%H:%M:%S')}")
    return "monthly_report_ok"

# ============================================================================
# EXEMPLES CRON MAINTENANCE
# ============================================================================

@task(cron="0 2 * * *")  # Tous les jours à 2h du matin
def daily_backup():
    """Sauvegarde quotidienne"""
    print(f"💾 [BACKUP] Sauvegarde nocturne - {datetime.now().strftime('%H:%M:%S')}")
    return "backup_ok"

@task(cron="0 3 * * 0")  # Dimanche à 3h
def weekly_cleanup():
    """Nettoyage hebdomadaire"""
    print(f"🧹 [CLEANUP] Nettoyage hebdomadaire - {datetime.now().strftime('%H:%M:%S')}")
    return "cleanup_ok"

@task(cron="0 1 1 1 *")  # 1er janvier à 1h (annuel)
def yearly_archive():
    """Archivage annuel"""
    print(f"📦 [ARCHIVE] Archivage annuel - {datetime.now().strftime('%H:%M:%S')}")
    return "archive_ok"

@task(cron="*/15 * * * *")  # Toutes les 15 minutes
def health_check():
    """Vérification de santé"""
    print(f"🔍 [HEALTH] Vérification santé - {datetime.now().strftime('%H:%M:%S')}")
    return "health_ok"

# ============================================================================
# EXEMPLES CRON AVANCÉS
# ============================================================================

@task(cron="0 9,12,15,18 * * 1-5")  # 9h, 12h, 15h, 18h en semaine
def multiple_times_workday():
    """Plusieurs heures en semaine"""
    print(f"📈 [MULTI] Rapport 4x par jour - {datetime.now().strftime('%H:%M:%S')}")
    return "multi_workday_ok"

@task(cron="0 */4 * * *")  # Toutes les 4 heures
def every_four_hours():
    """Toutes les 4 heures"""
    print(f"🔄 [4H] Synchronisation 4h - {datetime.now().strftime('%H:%M:%S')}")
    return "every_4h_ok"

@task(cron="30 2 * * 1")  # Lundi à 2h30
def monday_maintenance():
    """Maintenance du lundi"""
    print(f"🔧 [MONDAY] Maintenance lundi - {datetime.now().strftime('%H:%M:%S')}")
    return "monday_maintenance_ok"

@task(cron="0 0 15 * *")  # Le 15 de chaque mois
def mid_month_task():
    """Tâche du milieu de mois"""
    print(f"📅 [MID-MONTH] Tâche 15 du mois - {datetime.now().strftime('%H:%M:%S')}")
    return "mid_month_ok"

@task(cron="0 6 * * 6")  # Samedi à 6h
def weekend_task():
    """Tâche du weekend"""
    print(f"🏖️ [WEEKEND] Tâche weekend - {datetime.now().strftime('%H:%M:%S')}")
    return "weekend_ok"

# ============================================================================
# EXEMPLES CRON E-COMMERCE / WEB
# ============================================================================

@task(cron="0 0 * * *")  # Tous les jours à minuit
def daily_analytics():
    """Analytics quotidiennes"""
    print(f"📊 [ANALYTICS] Analytics quotidiennes - {datetime.now().strftime('%H:%M:%S')}")
    return "analytics_ok"

@task(cron="*/5 9-17 * * 1-5")  # Toutes les 5 min pendant les heures de bureau
def business_monitoring():
    """Monitoring pendant heures bureau"""
    print(f"👀 [MONITOR] Monitoring business - {datetime.now().strftime('%H:%M:%S')}")
    return "monitor_business_ok"

@task(cron="0 8 * * 1")  # Lundi à 8h
def weekly_newsletter():
    """Newsletter hebdomadaire"""
    print(f"📧 [NEWSLETTER] Newsletter hebdo - {datetime.now().strftime('%H:%M:%S')}")
    return "newsletter_ok"

@task(cron="0 23 * * 0")  # Dimanche à 23h
def cache_preload():
    """Préchargement du cache"""
    print(f"🚀 [CACHE] Préchargement cache - {datetime.now().strftime('%H:%M:%S')}")
    return "cache_preload_ok"

# ============================================================================
# TÂCHES POUR DÉMO AVEC INTERVALLES COURTS
# ============================================================================

def demo_cron_short_intervals():
    """Crée des tâches CRON avec intervalles courts pour la démo"""
    scheduler = PyScheduler(log_level="INFO")
    
    # Simuler des expressions cron avec des intervalles courts
    demo_tasks = [
        {
            "func": lambda: print(f"⏰ [DEMO-MINUTE] Simulation tâche minute - {datetime.now().strftime('%H:%M:%S')}"),
            "interval": 5,  # Toutes les 5 secondes au lieu de chaque minute
            "name": "demo_every_minute",
            "description": "Simule: * * * * * (chaque minute)"
        },
        {
            "func": lambda: print(f"🕐 [DEMO-HOUR] Simulation tâche horaire - {datetime.now().strftime('%H:%M:%S')}"),
            "interval": 20,  # Toutes les 20 secondes au lieu de chaque heure
            "name": "demo_hourly",
            "description": "Simule: 0 * * * * (chaque heure)"
        },
        {
            "func": lambda: print(f"🌅 [DEMO-DAILY] Simulation tâche quotidienne - {datetime.now().strftime('%H:%M:%S')}"),
            "interval": 30,  # Toutes les 30 secondes au lieu de quotidien
            "name": "demo_daily",
            "description": "Simule: 0 9 * * * (tous les jours à 9h)"
        },
        {
            "func": lambda: print(f"💼 [DEMO-BUSINESS] Simulation heures bureau - {datetime.now().strftime('%H:%M:%S')}"),
            "interval": 15,  # Toutes les 15 secondes
            "name": "demo_business",
            "description": "Simule: 0 9 * * 1-5 (9h en semaine)"
        }
    ]
    
    # Ajouter toutes les tâches
    for task_config in demo_tasks:
        func = task_config["func"]
        scheduler.add_task(
            func=func,
            interval=task_config["interval"],
            name=task_config["name"]
        )
        print(f"✅ Tâche ajoutée: {task_config['name']} - {task_config['description']}")
    
    return scheduler

# ============================================================================
# GUIDE CRON INTERACTIF
# ============================================================================

def cron_guide():
    """Guide interactif pour comprendre les expressions CRON"""
    print("\n" + "="*80)
    print("📚 GUIDE INTERACTIF DES EXPRESSIONS CRON")
    print("="*80)
    
    cron_examples = {
        "Basiques": {
            "* * * * *": "Chaque minute",
            "0 * * * *": "Chaque heure (à la minute 0)",
            "0 0 * * *": "Chaque jour à minuit",
            "0 0 * * 0": "Chaque dimanche à minuit",
            "0 0 1 * *": "Le 1er de chaque mois à minuit"
        },
        "Business": {
            "0 9 * * 1-5": "9h du matin en semaine",
            "0 18 * * 1-5": "18h en semaine",
            "0 12 * * 1-5": "Midi en semaine",
            "0 9,12,15,18 * * 1-5": "9h, 12h, 15h, 18h en semaine"
        },
        "Maintenance": {
            "0 2 * * *": "2h du matin tous les jours",
            "0 3 * * 0": "3h du matin le dimanche",
            "*/15 * * * *": "Toutes les 15 minutes",
            "0 */4 * * *": "Toutes les 4 heures"
        },
        "Avancés": {
            "30 2 * * 1": "Lundi à 2h30",
            "0 0 15 * *": "Le 15 de chaque mois",
            "0 6 * * 6": "Samedi à 6h",
            "*/5 9-17 * * 1-5": "Toutes les 5 min de 9h à 17h en semaine"
        }
    }
    
    for category, examples in cron_examples.items():
        print(f"\n🎯 {category}:")
        print("-" * 40)
        for cron_expr, description in examples.items():
            print(f"  {cron_expr:<20} → {description}")
    
    print(f"\n💡 Format CRON: MINUTE HEURE JOUR_MOIS MOIS JOUR_SEMAINE")
    print(f"   Plages: minute(0-59) heure(0-23) jour(1-31) mois(1-12) jour_semaine(0-7)")
    print(f"   Spéciaux: * (tous) , (liste) - (plage) / (intervalle)")

def cron_validator():
    """Validateur d'expressions CRON interactif"""
    print("\n" + "="*70)
    print("🔍 VALIDATEUR D'EXPRESSIONS CRON")
    print("="*70)
    
    common_patterns = {
        "1": ("* * * * *", "Chaque minute"),
        "2": ("0 * * * *", "Chaque heure"),
        "3": ("0 0 * * *", "Chaque jour à minuit"),
        "4": ("0 9 * * 1-5", "9h en semaine"),
        "5": ("*/15 * * * *", "Toutes les 15 minutes"),
        "6": ("0 2 * * 0", "Dimanche à 2h"),
        "7": ("0 0 1 * *", "1er du mois à minuit"),
        "custom": ("", "Expression personnalisée")
    }
    
    print("Choisissez une expression CRON à tester:")
    for key, (expr, desc) in common_patterns.items():
        if key != "custom":
            print(f"  {key}. {expr:<15} → {desc}")
    print(f"  {len(common_patterns)}. Expression personnalisée")
    print("  q. Retour")
    
    choice = input("\nVotre choix: ").strip().lower()
    
    if choice == 'q':
        return
    
    if choice in common_patterns:
        if choice == "custom":
            cron_expr = input("Entrez votre expression CRON: ").strip()
        else:
            cron_expr = common_patterns[choice][0]
        
        # Test de l'expression
        print(f"\n🧪 Test de l'expression: {cron_expr}")
        
        try:
            # Créer une tâche temporaire pour valider
            @task(cron=cron_expr)
            def test_cron_task():
                return "test"
            
            scheduler = PyScheduler()
            
            # Vérifier que la tâche est bien ajoutée
            tasks = scheduler.list_tasks()
            cron_task = next((t for t in tasks if 'test_cron_task' in t['name']), None)
            
            if cron_task:
                print(f"✅ Expression CRON valide!")
                print(f"   Prochaine exécution: {cron_task['next_run_time']}")
            else:
                print(f"❌ Expression CRON invalide")
                
        except Exception as e:
            print(f"❌ Expression CRON invalide: {e}")
    
    else:
        print("❌ Choix invalide")

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def main():
    """Menu principal pour les exemples CRON"""
    print("🎯 PyScheduler - Exemples d'Expressions CRON")
    print("=" * 50)
    
    examples = {
        "1": ("Guide des expressions CRON", cron_guide),
        "2": ("Validateur CRON interactif", cron_validator),
        "3": ("Démo CRON avec intervalles courts", lambda: demo_cron_intervals()),
        "4": ("Toutes les tâches CRON (vraies)", lambda: run_real_cron_tasks()),
        "5": ("Exemples par catégorie", lambda: show_cron_by_category()),
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

def demo_cron_intervals():
    """Démo avec intervalles courts"""
    print("🎪 Démo CRON avec intervalles accélérés pour voir le fonctionnement")
    print("⚠️ Les vraies expressions CRON sont remplacées par des intervalles courts")
    
    scheduler = demo_cron_short_intervals()
    
    try:
        scheduler.start()
        print("⏰ Observation pendant 45 secondes...")
        time.sleep(45)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé")
    finally:
        scheduler.stop()
        print("✅ Démo terminée")

def run_real_cron_tasks():
    """Lance les vraies tâches CRON (pour test en conditions réelles)"""
    print("⚠️ ATTENTION: Les tâches utilisent de vraies expressions CRON")
    print("   Certaines peuvent ne pas s'exécuter immédiatement selon l'heure")
    
    confirm = input("Continuer? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Annulé")
        return
    
    scheduler = PyScheduler(log_level="INFO")
    
    try:
        scheduler.start()
        print("⏰ Scheduler CRON réel actif - Ctrl+C pour arrêter")
        print("📊 Monitoring des tâches...")
        
        start_time = time.time()
        while True:
            time.sleep(10)
            elapsed = int(time.time() - start_time)
            
            tasks = scheduler.list_tasks()
            total_runs = sum(t['stats']['total_runs'] for t in tasks)
            
            print(f"📊 [{elapsed:3d}s] {total_runs} exécutions totales")
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé")
    finally:
        scheduler.stop()
        print("✅ Scheduler CRON arrêté")

def show_cron_by_category():
    """Affiche les exemples CRON par catégorie"""
    categories = {
        "🕐 Intervalles Réguliers": [
            ("*/1 * * * *", "Chaque minute"),
            ("*/5 * * * *", "Toutes les 5 minutes"),
            ("*/15 * * * *", "Toutes les 15 minutes"),
            ("*/30 * * * *", "Toutes les 30 minutes"),
            ("0 * * * *", "Toutes les heures"),
            ("0 */2 * * *", "Toutes les 2 heures"),
            ("0 */4 * * *", "Toutes les 4 heures"),
            ("0 */6 * * *", "Toutes les 6 heures")
        ],
        "📅 Quotidien / Hebdomadaire": [
            ("0 0 * * *", "Chaque jour à minuit"),
            ("0 6 * * *", "Chaque jour à 6h"),
            ("0 9 * * *", "Chaque jour à 9h"),
            ("0 18 * * *", "Chaque jour à 18h"),
            ("0 0 * * 0", "Chaque dimanche à minuit"),
            ("0 0 * * 1", "Chaque lundi à minuit"),
            ("0 2 * * 0", "Dimanche à 2h"),
            ("0 3 * * 6", "Samedi à 3h")
        ],
        "💼 Heures de Bureau": [
            ("0 9 * * 1-5", "9h en semaine"),
            ("0 12 * * 1-5", "Midi en semaine"),
            ("0 18 * * 1-5", "18h en semaine"),
            ("*/15 9-17 * * 1-5", "Toutes les 15min de 9h-17h en semaine"),
            ("0 9,12,15,18 * * 1-5", "9h, 12h, 15h, 18h en semaine"),
            ("30 8 * * 1-5", "8h30 en semaine"),
            ("0 17 * * 1-5", "17h en semaine")
        ],
        "📊 Mensuel / Annuel": [
            ("0 0 1 * *", "1er de chaque mois à minuit"),
            ("0 0 15 * *", "15 de chaque mois à minuit"),
            ("0 0 L * *", "Dernier jour du mois (si supporté)"),
            ("0 0 1 1 *", "1er janvier à minuit"),
            ("0 0 1 4,7,10,1 *", "Début de trimestre"),
            ("0 0 * * 0#1", "Premier dimanche du mois (si supporté)"),
            ("0 2 1 */3 *", "Tous les trimestres à 2h")
        ]
    }
    
    for category, examples in categories.items():
        print(f"\n{category}:")
        print("-" * 60)
        for cron_expr, description in examples:
            print(f"  {cron_expr:<20} → {description}")

if __name__ == "__main__":
    main()