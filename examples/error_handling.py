"""
PyScheduler - Gestion d'erreurs et robustesse
===========================================

Exemples de gestion d'erreurs robuste avec PyScheduler.
"""

import random
import time
from datetime import datetime
from pyscheduler import PyScheduler, task
from pyscheduler.config import RetryConfig, Priority

# ============================================================================
# EXEMPLES D'ERREURS ET RETRY
# ============================================================================

@task(
    interval=8,
    retry_config=RetryConfig(max_attempts=3, backoff_factor=2.0),
    timeout=5.0
)
def flaky_api_call():
    """API qui échoue 50% du temps"""
    print(f"🌐 [API] Tentative d'appel à {datetime.now().strftime('%H:%M:%S')}")
    
    if random.random() < 0.5:
        raise ConnectionError("API temporairement indisponible")
    
    print("✅ [API] Succès!")
    return {"status": "success", "data": "api_data"}

@task(interval=10, timeout=3.0)
def slow_task():
    """Tâche qui peut dépasser le timeout"""
    print(f"🐌 [SLOW] Début tâche lente...")
    
    duration = random.uniform(1, 6)  # 1 à 6 secondes
    time.sleep(duration)
    
    print(f"✅ [SLOW] Terminé en {duration:.1f}s")
    return f"completed_in_{duration:.1f}s"

@task(interval=12)
def memory_intensive_task():
    """Tâche qui peut manquer de mémoire"""
    print(f"💾 [MEMORY] Début traitement mémoire...")
    
    if random.random() < 0.3:
        raise MemoryError("Mémoire insuffisante")
    
    print("✅ [MEMORY] Traitement réussi")
    return "memory_ok"

def main():
    """Démo gestion d'erreurs"""
    print("🛡️ PyScheduler - Gestion d'erreurs")
    print("=" * 50)
    
    scheduler = PyScheduler(log_level="INFO")
    
    try:
        scheduler.start()
        print("⏰ Test gestion d'erreurs - 30 secondes...")
        time.sleep(30)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé")
    finally:
        scheduler.stop()

if __name__ == "__main__":
    main()