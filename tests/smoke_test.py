"""
PyScheduler - Smoke Test
========================

Test ultra-rapide pour vérifier que l'import et les fonctions de base marchent.
"""

import sys
import os

# Ajouter le module au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def smoke_test():
    """Test de fumée ultra-rapide"""
    print("PyScheduler Smoke Test")
    print("-" * 30)
    
    try:
        # Test 1: Import basique
        print("1. Test import... ", end="")
        from pyscheduler import PyScheduler
        print("OK")
        
        # Test 2: Création scheduler
        print("2. Test création scheduler... ", end="")
        scheduler = PyScheduler()
        print("OK")
        
        # Test 3: Ajout de tâche
        print("3. Test ajout tâche... ", end="")
        def dummy_task():
            pass
        
        task = scheduler.add_task(dummy_task, interval=60, name="smoke_test")
        print("OK")
        
        # Test 4: Décorateurs
        print("4. Test décorateurs... ", end="")
        from pyscheduler.config import task, daily
        
        @task(30)
        def decorated_task():
            pass
        
        print("OK")
        
        # Test 5: Utilitaires
        print("5. Test utilitaires... ", end="")
        from pyscheduler.utils import parse_duration, validate_cron_expression
        
        duration = parse_duration("5m")
        assert duration == 300.0
        
        validate_cron_expression("0 9 * * *")
        print("OK")
        
        # Test 6: Configuration
        print("6. Test configuration... ", end="")
        from pyscheduler.config import ScheduleType, Priority
        
        assert ScheduleType.INTERVAL.value == "interval"
        assert Priority.HIGH.value == 1
        print("OK")
        
        print("\nTous les tests de fumée passent!")
        return True
        
    except Exception as e:
        print(f"ÉCHEC: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = smoke_test()
    sys.exit(0 if success else 1)