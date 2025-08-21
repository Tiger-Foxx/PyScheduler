"""Test direct de l'exécuteur - CORRIGÉ"""

import sys
import os
import time
import asyncio
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyscheduler.core.executors import ExecutorFactory, ExecutorType
from pyscheduler.config import Priority

def test_function():
    print(f"🔥 TEST FUNCTION EXÉCUTÉE à {datetime.now().strftime('%H:%M:%S')}")
    return "success"

async def test_async_function():
    print(f"🎉 ASYNC FUNCTION EXÉCUTÉE à {datetime.now().strftime('%H:%M:%S')}")
    return "async_success"

def main():
    print("🧪 Test direct des exécuteurs - CORRIGÉ")
    print("=" * 50)
    
    # Test ThreadExecutor
    print("1. Test ThreadExecutor...")
    thread_executor = ExecutorFactory.create_executor(ExecutorType.THREAD, max_workers=2)
    thread_executor.start()
    
    # Créer une fausse tâche COMPLÈTE
    class FakeTask:
        def __init__(self, func, name):
            self.func = func
            self.name = name
            self.priority = Priority.NORMAL  # ← AJOUTÉ !
        
        async def execute(self):
            print(f"🚀 Début exécution de {self.name}")
            result = self.func()
            print(f"✅ Tâche {self.name} exécutée avec résultat: {result}")
            
            # Créer un TaskExecution basique
            from pyscheduler.core.task import TaskExecution, TaskStatus
            execution = TaskExecution(
                task_name=self.name,
                execution_id=f"{self.name}_test",
                status=TaskStatus.SUCCESS,
                start_time=datetime.now(),
                end_time=datetime.now(),
                result=result
            )
            return execution
    
    fake_task = FakeTask(test_function, "test_sync")
    
    # Soumettre la tâche
    print("Soumission de la tâche...")
    request_id = thread_executor.submit_task(fake_task)
    print(f"✅ Tâche soumise avec ID: {request_id}")
    
    # Attendre l'exécution
    print("Attente de l'exécution (5 secondes)...")
    time.sleep(5)
    
    # Vérifier les stats
    stats = thread_executor.get_stats()
    print(f"📊 Stats: {stats}")
    
    # Arrêter
    thread_executor.stop()
    print("✅ Test terminé")

if __name__ == "__main__":
    main()