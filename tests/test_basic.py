"""
PyScheduler - Tests Unitaires de Base
====================================

Tests unitaires pour vérifier les composants individuels.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
import sys
import os

# Ajouter le module au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyscheduler import PyScheduler, Task, TaskStatus
from pyscheduler.config import ScheduleType, Priority, TaskConfig, RetryConfig
from pyscheduler.core.triggers import TriggerFactory, IntervalTrigger, DailyTrigger
from pyscheduler.utils import ValidationError, TaskError


class TestUtils:
    """Tests des utilitaires"""
    
    def test_duration_parsing(self):
        """Test du parsing des durées"""
        from pyscheduler.utils import parse_duration
        
        assert parse_duration(60) == 60.0
        assert parse_duration("5m") == 300.0
        assert parse_duration("2h") == 7200.0
        assert parse_duration("1d") == 86400.0
        
        with pytest.raises(ValidationError):
            parse_duration("invalid")
    
    def test_cron_validation(self):
        """Test de validation des expressions cron"""
        from pyscheduler.utils import validate_cron_expression
        
        # Expressions valides
        validate_cron_expression("0 9 * * *")
        validate_cron_expression("*/15 * * * *")
        validate_cron_expression("0 2 1 * *")
        
        # Expressions invalides
        with pytest.raises(ValidationError):
            validate_cron_expression("invalid")
        
        with pytest.raises(ValidationError):
            validate_cron_expression("0 25 * * *")  # Heure invalide
    
    def test_time_validation(self):
        """Test de validation des heures"""
        from pyscheduler.utils import validate_time_string
        
        # Heures valides
        validate_time_string("09:30")
        validate_time_string("23:59")
        validate_time_string("00:00")
        
        # Heures invalides
        with pytest.raises(ValidationError):
            validate_time_string("25:00")
        
        with pytest.raises(ValidationError):
            validate_time_string("12:70")


class TestTriggers:
    """Tests des triggers"""
    
    def test_interval_trigger(self):
        """Test du trigger d'intervalle"""
        trigger = IntervalTrigger(60)
        
        # Première exécution
        next_run = trigger.get_next_run_time(None)
        assert next_run is not None
        
        # Exécution suivante
        last_run = datetime.now()
        next_run = trigger.get_next_run_time(last_run)
        expected = last_run + timedelta(seconds=60)
        assert abs((next_run - expected).total_seconds()) < 1
    
    def test_daily_trigger(self):
        """Test du trigger quotidien"""
        trigger = DailyTrigger("09:30")
        
        next_run = trigger.get_next_run_time(None)
        assert next_run is not None
        assert next_run.hour == 9
        assert next_run.minute == 30
    
    def test_trigger_factory(self):
        """Test de la factory de triggers"""
        # Interval
        trigger = TriggerFactory.create_trigger(ScheduleType.INTERVAL, 60)
        assert isinstance(trigger, IntervalTrigger)
        
        # Daily
        trigger = TriggerFactory.create_trigger(ScheduleType.DAILY, "09:00")
        assert isinstance(trigger, DailyTrigger)
        
        # Type invalide
        with pytest.raises(Exception):
            TriggerFactory.create_trigger("invalid", 60)


class TestTask:
    """Tests des tâches"""
    
    def test_task_creation(self):
        """Test de création de tâche"""
        def test_func():
            return "test"
        
        task = Task(
            name="test_task",
            func=test_func,
            schedule_type=ScheduleType.INTERVAL,
            schedule_value=60
        )
        
        assert task.name == "test_task"
        assert task.func == test_func
        assert task.schedule_type == ScheduleType.INTERVAL
        assert task.schedule_value == 60
        assert task.enabled
        assert not task.is_running
    
    @pytest.mark.asyncio
    async def test_task_execution(self):
        """Test d'exécution de tâche"""
        executed = []
        
        def test_func():
            executed.append(True)
            return "success"
        
        task = Task(
            name="test_execution",
            func=test_func,
            schedule_type=ScheduleType.INTERVAL,
            schedule_value=60
        )
        
        execution = await task.execute()
        
        assert len(executed) == 1
        assert execution.status == TaskStatus.SUCCESS
        assert execution.result == "success"
        assert execution.duration > 0
    
    @pytest.mark.asyncio
    async def test_task_error_handling(self):
        """Test de gestion d'erreur de tâche"""
        def error_func():
            raise ValueError("Test error")
        
        task = Task(
            name="test_error",
            func=error_func,
            schedule_type=ScheduleType.INTERVAL,
            schedule_value=60,
            retry_config=RetryConfig(max_attempts=1)  # Pas de retry pour ce test
        )
        
        execution = await task.execute()
        
        assert execution.status == TaskStatus.FAILED
        assert "Test error" in execution.error
        assert execution.traceback is not None


class TestScheduler:
    """Tests du scheduler principal"""
    
    def test_scheduler_creation(self):
        """Test de création du scheduler"""
        scheduler = PyScheduler()
        
        assert scheduler.is_stopped
        assert len(scheduler.list_tasks()) >= 0  # Peut avoir des tâches des décorateurs
    
    def test_add_task(self):
        """Test d'ajout de tâche"""
        scheduler = PyScheduler()
        
        def test_func():
            pass
        
        task = scheduler.add_task(test_func, interval=60, name="test_add")
        
        assert task.name == "test_add"
        assert "test_add" in [t.name for t in scheduler.list_tasks()]
    
    def test_remove_task(self):
        """Test de suppression de tâche"""
        scheduler = PyScheduler()
        
        def test_func():
            pass
        
        scheduler.add_task(test_func, interval=60, name="test_remove")
        assert scheduler.remove_task("test_remove")
        assert "test_remove" not in [t.name for t in scheduler.list_tasks()]
        
        # Tentative de suppression d'une tâche inexistante
        assert not scheduler.remove_task("nonexistent")
    
    def test_scheduler_lifecycle(self):
        """Test du cycle de vie du scheduler"""
        scheduler = PyScheduler()
        
        # État initial
        assert scheduler.is_stopped
        
        # Démarrage
        scheduler.start()
        assert scheduler.is_running
        
        # Pause
        scheduler.pause()
        time.sleep(0.1)  # Laisser le temps à la pause de prendre effet
        
        # Reprise
        scheduler.resume()
        assert scheduler.is_running
        
        # Arrêt
        scheduler.stop(timeout=5.0)  # <-- Ajouter timeout court
        assert scheduler.is_stopped


class TestIntegration:
    """Tests d'intégration"""
    
    def test_end_to_end_execution(self):
        """Test d'exécution complète"""
        executions = []
        
        def test_task():
            executions.append(datetime.now())
        
        scheduler = PyScheduler()
        scheduler.add_task(test_task, interval=1, name="integration_test")
        
        scheduler.start()
        
        # Attendre quelques exécutions
        time.sleep(3.5)
        
        scheduler.stop(timeout=2.0)
        
        # Vérifier qu'on a eu au moins 2-3 exécutions
        assert len(executions) >= 2, f"Seulement {len(executions)} exécutions"
        
        # Vérifier que les intervalles sont corrects
        if len(executions) >= 2:
            interval = (executions[1] - executions[0]).total_seconds()
            assert 0.8 <= interval <= 1.5, f"Intervalle incorrect: {interval}s"


# Fonction utilitaire pour lancer les tests
def run_tests():
    """Lance tous les tests"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()