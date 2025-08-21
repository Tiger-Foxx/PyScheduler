"""Test avec debug complet"""

import sys
import os
import time
from datetime import datetime

# Ajouter le module au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyscheduler import PyScheduler, task, startup

hello_count = 0
salut_count = 0

@task(3)  # Toutes les 3 secondes
def show_hello():
    global hello_count
    hello_count += 1
    print(f"🔥 HELLO #{hello_count} à {datetime.now().strftime('%H:%M:%S')}")
    return f"hello_{hello_count}"

@task(7)  # Toutes les 7 secondes  
def show_salut():
    global salut_count
    salut_count += 1
    print(f"🎉 SALUT #{salut_count} à {datetime.now().strftime('%H:%M:%S')}")
    return f"salut_{salut_count}"

@startup()
def init_demo():
    print("✅ DÉMARRAGE - PyScheduler lancé !")
    return "startup_ok"

def main():
    print("🚀 PyScheduler - Test Debug")
    print("=" * 50)
    
    scheduler = PyScheduler(log_level="DEBUG")  # Log debug activé
    
    try:
        scheduler.start()
        print("🎯 Scheduler démarré - Observez les logs...")
        
        # Attendre 20 secondes
        for i in range(20):
            time.sleep(1)
            if i % 5 == 0:
                print(f"... {i}s écoulées - Hello: {hello_count}, Salut: {salut_count}")
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé...")
    finally:
        scheduler.stop(timeout=3.0)
        print(f"✅ FINAL - Hello: {hello_count}, Salut: {salut_count}")

if __name__ == "__main__":
    main()