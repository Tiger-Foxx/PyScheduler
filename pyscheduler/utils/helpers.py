"""
PyScheduler - Helper Functions
==============================

Fonctions utilitaires pour PyScheduler.
"""

import re
import importlib
import inspect
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Union, Tuple
from pathlib import Path

from .exceptions import ValidationError, ConfigurationError


def validate_cron_expression(cron_expr: str) -> bool:
    """
    Valide une expression cron basique
    
    Args:
        cron_expr: Expression cron (format: "min hour day month weekday")
    
    Returns:
        True si valide
        
    Raises:
        ValidationError: Si l'expression est invalide
    """
    if not cron_expr or not isinstance(cron_expr, str):
        raise ValidationError("Expression cron vide ou invalide")
    
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValidationError(
            f"Expression cron doit avoir 5 parties, {len(parts)} trouvées: {cron_expr}"
        )
    
    # Validation basique des ranges
    ranges = [
        (0, 59),   # minutes
        (0, 23),   # heures  
        (1, 31),   # jour du mois
        (1, 12),   # mois
        (0, 7)     # jour de la semaine (0 et 7 = dimanche)
    ]
    
    for i, (part, (min_val, max_val)) in enumerate(zip(parts, ranges)):
        if part == "*":
            continue
        
        # Gestion des listes (1,2,3)
        if "," in part:
            values = part.split(",")
            for val in values:
                if not _validate_cron_value(val.strip(), min_val, max_val):
                    raise ValidationError(f"Valeur cron invalide: {val} dans {part}")
            continue
        
        # Gestion des ranges (1-5)
        if "-" in part:
            if part.count("-") != 1:
                raise ValidationError(f"Range cron invalide: {part}")
            start, end = part.split("-")
            if not (_validate_cron_value(start, min_val, max_val) and 
                    _validate_cron_value(end, min_val, max_val)):
                raise ValidationError(f"Range cron invalide: {part}")
            continue
        
        # Gestion des steps (*/5)
        if "/" in part:
            base, step = part.split("/", 1)
            if base != "*" and not _validate_cron_value(base, min_val, max_val):
                raise ValidationError(f"Base cron invalide: {base}")
            if not step.isdigit() or int(step) <= 0:
                raise ValidationError(f"Step cron invalide: {step}")
            continue
        
        # Valeur simple
        if not _validate_cron_value(part, min_val, max_val):
            raise ValidationError(f"Valeur cron invalide: {part}")
    
    return True


def _validate_cron_value(value: str, min_val: int, max_val: int) -> bool:
    """Valide une valeur cron individuelle"""
    try:
        val = int(value)
        return min_val <= val <= max_val
    except ValueError:
        return False


def validate_time_string(time_str: str) -> bool:
    """
    Valide une chaîne de temps au format HH:MM
    
    Args:
        time_str: Chaîne de temps (ex: "09:30")
    
    Returns:
        True si valide
        
    Raises:
        ValidationError: Si le format est invalide
    """
    if not time_str or not isinstance(time_str, str):
        raise ValidationError("Chaîne de temps vide ou invalide")
    
    pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$'
    if not re.match(pattern, time_str):
        raise ValidationError(f"Format de temps invalide: {time_str}. Attendu: HH:MM")
    
    return True


def parse_duration(duration: Union[str, int, float]) -> float:
    """
    Parse une durée en secondes
    
    Args:
        duration: Durée (secondes, ou chaîne comme "5m", "2h", "1d")
    
    Returns:
        Durée en secondes
        
    Raises:
        ValidationError: Si le format est invalide
    """
    if isinstance(duration, (int, float)):
        if duration <= 0:
            raise ValidationError("La durée doit être positive")
        return float(duration)
    
    if not isinstance(duration, str):
        raise ValidationError("Durée doit être un nombre ou une chaîne")
    
    # Parse des chaînes comme "5m", "2h", "1d"
    pattern = r'^(\d+(?:\.\d+)?)\s*([smhd]?)$'
    match = re.match(pattern, duration.lower().strip())
    
    if not match:
        raise ValidationError(f"Format de durée invalide: {duration}")
    
    value, unit = match.groups()
    value = float(value)
    
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        '': 1  # par défaut en secondes
    }
    
    return value * multipliers[unit]


def import_function(module_path: str, function_name: str) -> Callable:
    """
    Importe une fonction dynamiquement
    
    Args:
        module_path: Chemin du module (ex: "mypackage.mymodule")
        function_name: Nom de la fonction
    
    Returns:
        Fonction importée
        
    Raises:
        ConfigurationError: Si l'import échoue
    """
    try:
        module = importlib.import_module(module_path)
        func = getattr(module, function_name)
        
        if not callable(func):
            raise ConfigurationError(
                f"{function_name} dans {module_path} n'est pas une fonction"
            )
        
        return func
        
    except ImportError as e:
        raise ConfigurationError(f"Impossible d'importer {module_path}: {e}")
    except AttributeError:
        raise ConfigurationError(
            f"Fonction {function_name} introuvable dans {module_path}"
        )


def safe_call(func: Callable, *args, **kwargs) -> Tuple[bool, Any, Optional[str]]:
    """
    Appelle une fonction de manière sécurisée
    
    Args:
        func: Fonction à appeler
        *args: Arguments positionnels
        **kwargs: Arguments nommés
    
    Returns:
        Tuple (succès, résultat, erreur)
    """
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        return False, None, str(e)


def get_function_info(func: Callable) -> Dict[str, Any]:
    """
    Obtient des informations sur une fonction
    
    Args:
        func: Fonction à analyser
    
    Returns:
        Dictionnaire avec les infos de la fonction
    """
    info = {
        'name': getattr(func, '__name__', 'unknown'),
        'module': getattr(func, '__module__', 'unknown'),
        'doc': getattr(func, '__doc__', None),
        'is_async': inspect.iscoroutinefunction(func),
        'signature': None,
        'parameters': []
    }
    
    try:
        sig = inspect.signature(func)
        info['signature'] = str(sig)
        info['parameters'] = [
            {
                'name': param.name,
                'default': param.default if param.default != param.empty else None,
                'annotation': param.annotation if param.annotation != param.empty else None
            }
            for param in sig.parameters.values()
        ]
    except (ValueError, TypeError):
        # Certaines fonctions built-in n'ont pas de signature
        pass
    
    return info


def ensure_datetime(value: Union[str, datetime]) -> datetime:
    """
    Convertit une valeur en datetime
    
    Args:
        value: Valeur à convertir (chaîne ISO ou datetime)
    
    Returns:
        Objet datetime
        
    Raises:
        ValidationError: Si la conversion échoue
    """
    if isinstance(value, datetime):
        return value
    
    if isinstance(value, str):
        try:
            # Essai format ISO
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        try:
            # Essai format simple YYYY-MM-DD HH:MM:SS
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
        
        try:
            # Essai format simple YYYY-MM-DD
            return datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            pass
    
    raise ValidationError(f"Impossible de convertir en datetime: {value}")


def create_safe_filename(name: str) -> str:
    """
    Crée un nom de fichier sécurisé
    
    Args:
        name: Nom original
    
    Returns:
        Nom de fichier sécurisé
    """
    # Remplace les caractères dangereux
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
    safe_name = re.sub(r'\s+', '_', safe_name)
    safe_name = safe_name.strip('.')
    
    # Limite la longueur
    if len(safe_name) > 100:
        safe_name = safe_name[:100]
    
    return safe_name or 'unnamed'


def format_duration(seconds: float) -> str:
    """
    Formate une durée en texte lisible
    
    Args:
        seconds: Durée en secondes
    
    Returns:
        Durée formatée (ex: "2h 30m 15s")
    """
    if seconds < 0:
        return "0s"
    
    parts = []
    
    # Jours
    if seconds >= 86400:
        days = int(seconds // 86400)
        parts.append(f"{days}j")
        seconds %= 86400
    
    # Heures
    if seconds >= 3600:
        hours = int(seconds // 3600)
        parts.append(f"{hours}h")
        seconds %= 3600
    
    # Minutes
    if seconds >= 60:
        minutes = int(seconds // 60)
        parts.append(f"{minutes}m")
        seconds %= 60
    
    # Secondes
    if seconds > 0 or not parts:
        if seconds == int(seconds):
            parts.append(f"{int(seconds)}s")
        else:
            parts.append(f"{seconds:.1f}s")
    
    return " ".join(parts)


def deep_merge_dicts(dict1: dict, dict2: dict) -> dict:
    """
    Fusionne deux dictionnaires récursivement
    
    Args:
        dict1: Premier dictionnaire
        dict2: Deuxième dictionnaire (prioritaire)
    
    Returns:
        Dictionnaire fusionné
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result