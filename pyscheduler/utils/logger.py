"""
PyScheduler - Logging Utilities
===============================

Système de logging simple et efficace pour PyScheduler.
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum


class LogLevel(Enum):
    """Niveaux de log disponibles"""
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class PySchedulerLogger:
    """Logger personnalisé pour PyScheduler"""
    
    def __init__(
        self,
        name: str = "PyScheduler",
        level: str = "INFO",
        log_file: Optional[str] = None,
        console_output: bool = True,
        json_format: bool = False
    ):
        """
        Initialise le logger
        
        Args:
            name: Nom du logger
            level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Fichier de log (optionnel)
            console_output: Afficher dans la console
            json_format: Format JSON pour les logs
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.json_format = json_format
        
        # Éviter les doublons de handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Handler console
        if console_output:
            self._add_console_handler()
        
        # Handler fichier
        if log_file:
            self._add_file_handler(log_file)
    
    def _add_console_handler(self):
        """Ajoute un handler pour la console"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self, log_file: str):
        """Ajoute un handler pour un fichier"""
        # Créer le dossier si nécessaire
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(file_handler)
    
    def _get_formatter(self):
        """Retourne le formateur approprié"""
        if self.json_format:
            return JsonFormatter()
        else:
            return logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
    
    def debug(self, message: str, **kwargs):
        """Log niveau DEBUG"""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log niveau INFO"""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log niveau WARNING"""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log niveau ERROR"""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log niveau CRITICAL"""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log avec contexte additionnel"""
        if kwargs and self.json_format:
            # En format JSON, on peut inclure des données structurées
            extra_data = {'context': kwargs}
            self.logger.log(level, message, extra=extra_data)
        else:
            # Format texte simple
            if kwargs:
                context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
                message = f"{message} | {context_str}"
            self.logger.log(level, message)
    
    def task_started(self, task_name: str, **kwargs):
        """Log spécifique: tâche démarrée"""
        self.info(f"Tâche '{task_name}' démarrée", task_name=task_name, **kwargs)
    
    def task_completed(self, task_name: str, duration: float, **kwargs):
        """Log spécifique: tâche terminée"""
        self.info(
            f"Tâche '{task_name}' terminée avec succès en {duration:.2f}s",
            task_name=task_name,
            duration=duration,
            status="success",
            **kwargs
        )
    
    def task_failed(self, task_name: str, error: str, **kwargs):
        """Log spécifique: tâche échouée"""
        self.error(
            f"Tâche '{task_name}' échouée: {error}",
            task_name=task_name,
            error=error,
            status="failed",
            **kwargs
        )
    
    def scheduler_started(self):
        """Log spécifique: scheduler démarré"""
        self.info("PyScheduler démarré", event="scheduler_start")
    
    def scheduler_stopped(self):
        """Log spécifique: scheduler arrêté"""
        self.info("PyScheduler arrêté", event="scheduler_stop")


class JsonFormatter(logging.Formatter):
    """Formateur JSON pour les logs"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }
        
        # Ajouter le contexte si disponible
        if hasattr(record, 'context'):
            log_entry.update(record.context)
        
        # Ajouter les infos d'exception
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


# Instance globale par défaut
_default_logger = None

def get_logger(
    name: str = "PyScheduler",
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    json_format: bool = False
) -> PySchedulerLogger:
    """
    Obtient une instance de logger
    
    Args:
        name: Nom du logger
        level: Niveau de log
        log_file: Fichier de log optionnel
        console_output: Affichage console
        json_format: Format JSON
    
    Returns:
        Instance de PySchedulerLogger
    """
    return PySchedulerLogger(name, level, log_file, console_output, json_format)


def setup_default_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    json_format: bool = False
):
    """
    Configure le logger par défaut
    
    Args:
        level: Niveau de log
        log_file: Fichier de log optionnel
        console_output: Affichage console
        json_format: Format JSON
    """
    global _default_logger
    _default_logger = get_logger(
        "PyScheduler", level, log_file, console_output, json_format
    )


def get_default_logger() -> PySchedulerLogger:
    """Retourne le logger par défaut"""
    # global _default_logger
    if _default_logger is None:
        setup_default_logger()
    return _default_logger