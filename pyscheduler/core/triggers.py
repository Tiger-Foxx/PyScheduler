"""
PyScheduler - Triggers Core
===========================

Système de déclencheurs pour calculer les prochaines exécutions de tâches.
Chaque type de planification a son propre trigger spécialisé.
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Union, List, Tuple
from calendar import monthrange

# Import de nos utilitaires (cohérence!)
from ..utils import (
    SchedulingError, ValidationError, get_default_logger,
    validate_cron_expression, validate_time_string, ensure_datetime
)
from ..config import ScheduleType


class BaseTrigger(ABC):
    """
    Classe de base pour tous les triggers
    
    Un trigger détermine quand une tâche doit s'exécuter selon
    sa configuration de planification.
    """
    
    def __init__(self, schedule_value: any):
        """
        Initialise le trigger
        
        Args:
            schedule_value: Valeur de planification spécifique au type
        """
        self.schedule_value = schedule_value
        self.logger = get_default_logger()
        self._validate()
    
    @abstractmethod
    def _validate(self):
        """Valide la configuration du trigger"""
        pass
    
    @abstractmethod
    def get_next_run_time(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """
        Calcule la prochaine exécution
        
        Args:
            last_run: Dernière exécution (None si jamais exécutée)
            
        Returns:
            Prochaine date d'exécution ou None si plus d'exécution
        """
        pass
    
    def get_description(self) -> str:
        """Retourne une description lisible du trigger"""
        return f"{self.__class__.__name__}({self.schedule_value})"


class IntervalTrigger(BaseTrigger):
    """
    Trigger pour exécution à intervalle régulier
    
    Exemple: toutes les 60 secondes, toutes les 5 minutes, etc.
    """
    
    def _validate(self):
        """Valide l'intervalle"""
        if not isinstance(self.schedule_value, (int, float)):
            raise ValidationError("L'intervalle doit être un nombre (secondes)")
        
        if self.schedule_value <= 0:
            raise ValidationError("L'intervalle doit être positif")
        
        # Avertissement pour intervalles très courts
        if self.schedule_value < 1:
            self.logger.warning(f"Intervalle très court: {self.schedule_value}s")
    
    def get_next_run_time(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """Calcule la prochaine exécution basée sur l'intervalle"""
        now = datetime.now()
        
        if last_run is None:
            # Première exécution : immédiatement
            return now
        
        # Prochaine exécution = dernière + intervalle
        next_run = last_run + timedelta(seconds=self.schedule_value)
        
        # Si on est déjà en retard, exécuter immédiatement
        if next_run <= now:
            return now
        
        return next_run
    
    def get_description(self) -> str:
        """Description lisible"""
        from ..utils import format_duration  # Import local
        return f"Toutes les {format_duration(self.schedule_value)}"


class CronTrigger(BaseTrigger):
    """
    Trigger pour expressions cron
    
    Format: minute heure jour_mois mois jour_semaine
    Exemple: "0 9 * * 1-5" = 9h du lundi au vendredi
    """
    
    def _validate(self):
        """Valide l'expression cron"""
        if not isinstance(self.schedule_value, str):
            raise ValidationError("L'expression cron doit être une chaîne")
        
        validate_cron_expression(self.schedule_value)
        
        # Parser l'expression pour validation plus poussée
        self._parse_cron()
    
    def _parse_cron(self) -> Tuple[List, List, List, List, List]:
        """
        Parse l'expression cron en listes de valeurs possibles
        
        Returns:
            Tuple (minutes, heures, jours, mois, jours_semaine)
        """
        parts = self.schedule_value.strip().split()
        
        # Ranges pour validation
        ranges = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]
        
        parsed_parts = []
        for i, (part, (min_val, max_val)) in enumerate(zip(parts, ranges)):
            parsed_parts.append(self._parse_cron_field(part, min_val, max_val))
        
        return tuple(parsed_parts)
    
    def _parse_cron_field(self, field: str, min_val: int, max_val: int) -> List[int]:
        """Parse un champ individuel de l'expression cron"""
        if field == "*":
            return list(range(min_val, max_val + 1))
        
        values = set()
        
        # Gérer les listes (1,2,3)
        for part in field.split(","):
            part = part.strip()
            
            # Gérer les steps (*/5 ou 1-10/2)
            if "/" in part:
                base, step = part.split("/", 1)
                step = int(step)
                
                if base == "*":
                    base_values = list(range(min_val, max_val + 1))
                elif "-" in base:
                    start, end = map(int, base.split("-"))
                    base_values = list(range(start, end + 1))
                else:
                    base_values = [int(base)]
                
                # Appliquer le step
                for val in base_values:
                    if val % step == 0 or val == base_values[0]:
                        values.add(val)
            
            # Gérer les ranges (1-5)
            elif "-" in part:
                start, end = map(int, part.split("-"))
                values.update(range(start, end + 1))
            
            # Valeur simple
            else:
                values.add(int(part))
        
        # Filtrer les valeurs valides et convertir dimanche (7 -> 0)
        result = []
        for val in sorted(values):
            if min_val <= val <= max_val:
                # Convertir dimanche (7) en 0 pour les jours de semaine
                if max_val == 7 and val == 7:
                    result.append(0)
                else:
                    result.append(val)
        
        return result
    
    def get_next_run_time(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """Calcule la prochaine exécution selon l'expression cron"""
        now = datetime.now()
        start_time = last_run if last_run else now
        
        # Si on démarre maintenant, commencer à la minute suivante
        if last_run is None:
            start_time = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        else:
            start_time = start_time + timedelta(minutes=1)
        
        # Parser l'expression cron
        minutes, hours, days, months, weekdays = self._parse_cron()
        
        # Chercher la prochaine date valide (limite à 4 ans pour éviter boucle infinie)
        max_iterations = 365 * 4
        current = start_time.replace(second=0, microsecond=0)
        
        for _ in range(max_iterations):
            # Vérifier si la date actuelle correspond
            if (current.minute in minutes and
                current.hour in hours and
                current.day in days and
                current.month in months and
                current.weekday() in [d if d != 0 else 7 for d in weekdays]):  # Conversion 0->7 pour dimanche
                
                return current
            
            # Passer à la minute suivante
            current += timedelta(minutes=1)
        
        # Pas de prochaine exécution trouvée dans les 4 ans
        self.logger.warning(f"Pas de prochaine exécution trouvée pour: {self.schedule_value}")
        return None
    
    def get_description(self) -> str:
        """Description lisible de l'expression cron"""
        try:
            minutes, hours, days, months, weekdays = self._parse_cron()
            
            # Construire une description lisible
            desc_parts = []
            
            # Minutes
            if len(minutes) == 1 and minutes[0] == 0:
                min_desc = "à l'heure pile"
            elif len(minutes) == 1:
                min_desc = f"à {minutes[0]:02d} minutes"
            else:
                min_desc = f"aux minutes {','.join(f'{m:02d}' for m in minutes[:3])}{'...' if len(minutes) > 3 else ''}"
            
            # Heures
            if len(hours) == 24:
                hour_desc = "toutes les heures"
            elif len(hours) == 1:
                hour_desc = f"à {hours[0]:02d}h"
            else:
                hour_desc = f"aux heures {','.join(f'{h:02d}h' for h in hours[:3])}{'...' if len(hours) > 3 else ''}"
            
            # Combiner
            if len(hours) == 24:
                desc_parts.append(f"{min_desc} {hour_desc}")
            else:
                desc_parts.append(f"{hour_desc} {min_desc}")
            
            # Jours de semaine
            if len(weekdays) < 7:
                weekday_names = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
                day_names = [weekday_names[d] for d in weekdays if d < 7]
                if day_names:
                    desc_parts.append(f"le {', '.join(day_names)}")
            
            return " ".join(desc_parts)
            
        except Exception:
            return f"Cron: {self.schedule_value}"


class DailyTrigger(BaseTrigger):
    """
    Trigger pour exécution quotidienne à heure fixe
    
    Exemple: "09:30" = tous les jours à 9h30
    """
    
    def _validate(self):
        """Valide le format HH:MM"""
        if not isinstance(self.schedule_value, str):
            raise ValidationError("L'heure quotidienne doit être une chaîne HH:MM")
        
        validate_time_string(self.schedule_value)
        
        # Parser l'heure pour validation
        self.hour, self.minute = map(int, self.schedule_value.split(':'))
    
    def get_next_run_time(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """Calcule la prochaine exécution quotidienne"""
        now = datetime.now()
        
        # Calculer pour aujourd'hui
        today_run = now.replace(
            hour=self.hour, 
            minute=self.minute, 
            second=0, 
            microsecond=0
        )
        
        # Si l'heure d'aujourd'hui n'est pas encore passée
        if today_run > now:
            return today_run
        
        # Sinon, demain à la même heure
        tomorrow_run = today_run + timedelta(days=1)
        return tomorrow_run
    
    def get_description(self) -> str:
        """Description lisible"""
        return f"Tous les jours à {self.schedule_value}"


class WeeklyTrigger(BaseTrigger):
    """
    Trigger pour exécution hebdomadaire
    
    Exemple: (1, "09:00") = tous les mardis à 9h
    Jours: 0=lundi, 1=mardi, ..., 6=dimanche
    """
    
    def _validate(self):
        """Valide le format (jour, "HH:MM")"""
        if not isinstance(self.schedule_value, (list, tuple)) or len(self.schedule_value) != 2:
            raise ValidationError("La planification hebdomadaire doit être [jour_semaine, 'HH:MM']")
        
        day, time_str = self.schedule_value
        
        if not isinstance(day, int) or not (0 <= day <= 6):
            raise ValidationError("Le jour de la semaine doit être 0-6 (0=lundi)")
        
        if not isinstance(time_str, str):
            raise ValidationError("L'heure doit être une chaîne HH:MM")
        
        validate_time_string(time_str)
        
        self.weekday = day
        self.hour, self.minute = map(int, time_str.split(':'))
    
    def get_next_run_time(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """Calcule la prochaine exécution hebdomadaire"""
        now = datetime.now()
        
        # Calculer les jours jusqu'au prochain jour cible
        current_weekday = now.weekday()  # 0=lundi
        days_ahead = self.weekday - current_weekday
        
        # Si c'est le bon jour mais l'heure est passée, ou si le jour est passé
        if days_ahead < 0 or (days_ahead == 0 and now.hour > self.hour) or \
           (days_ahead == 0 and now.hour == self.hour and now.minute >= self.minute):
            days_ahead += 7
        
        # Calculer la date cible
        target_date = now + timedelta(days=days_ahead)
        target_time = target_date.replace(
            hour=self.hour,
            minute=self.minute,
            second=0,
            microsecond=0
        )
        
        return target_time
    
    def get_description(self) -> str:
        """Description lisible"""
        weekday_names = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
        day_name = weekday_names[self.weekday]
        return f"Tous les {day_name} à {self.hour:02d}:{self.minute:02d}"


class OnceTrigger(BaseTrigger):
    """
    Trigger pour exécution unique à date précise
    
    Exemple: "2025-12-25 00:00:00" = le 25 décembre 2025 à minuit
    """
    
    def _validate(self):
        """Valide la date/heure"""
        try:
            self.target_datetime = ensure_datetime(self.schedule_value)
        except Exception as e:
            raise ValidationError(f"Date/heure invalide: {e}")
    
    def get_next_run_time(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """Retourne la date cible si pas encore exécutée"""
        now = datetime.now()
        
        # Si déjà exécutée, plus d'exécution
        if last_run is not None:
            return None
        
        # Si la date cible est dans le futur
        if self.target_datetime > now:
            return self.target_datetime
        
        # Si la date cible est passée, exécuter immédiatement
        return now
    
    def get_description(self) -> str:
        """Description lisible"""
        return f"Une fois le {self.target_datetime.strftime('%d/%m/%Y à %H:%M')}"


class StartupTrigger(BaseTrigger):
    """
    Trigger pour exécution au démarrage du scheduler
    """
    
    def _validate(self):
        """Pas de validation spécifique"""
        pass
    
    def get_next_run_time(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """Exécute immédiatement si jamais exécutée"""
        if last_run is None:
            return datetime.now()
        return None
    
    def get_description(self) -> str:
        """Description lisible"""
        return "Au démarrage du scheduler"


class ShutdownTrigger(BaseTrigger):
    """
    Trigger pour exécution à l'arrêt du scheduler
    
    Note: Ce trigger est géré spécialement par le scheduler
    """
    
    def _validate(self):
        """Pas de validation spécifique"""
        pass
    
    def get_next_run_time(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """Ne s'exécute pas via le système normal"""
        return None
    
    def get_description(self) -> str:
        """Description lisible"""
        return "À l'arrêt du scheduler"


class MonthlyTrigger(BaseTrigger):
    """
    Trigger pour exécution mensuelle
    
    Exemple: (15, "14:30") = le 15 de chaque mois à 14h30
    """
    
    def _validate(self):
        """Valide le format (jour, "HH:MM")"""
        if not isinstance(self.schedule_value, (list, tuple)) or len(self.schedule_value) != 2:
            raise ValidationError("La planification mensuelle doit être [jour_mois, 'HH:MM']")
        
        day, time_str = self.schedule_value
        
        if not isinstance(day, int) or not (1 <= day <= 31):
            raise ValidationError("Le jour du mois doit être 1-31")
        
        if not isinstance(time_str, str):
            raise ValidationError("L'heure doit être une chaîne HH:MM")
        
        validate_time_string(time_str)
        
        self.day = day
        self.hour, self.minute = map(int, time_str.split(':'))
    
    def get_next_run_time(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """Calcule la prochaine exécution mensuelle"""
        now = datetime.now()
        
        # Calculer pour ce mois
        try:
            this_month_run = now.replace(
                day=self.day,
                hour=self.hour,
                minute=self.minute,
                second=0,
                microsecond=0
            )
            
            # Si pas encore passé ce mois
            if this_month_run > now:
                return this_month_run
        except ValueError:
            # Le jour n'existe pas ce mois (ex: 31 février)
            pass
        
        # Chercher le prochain mois où ce jour existe
        current_month = now.month
        current_year = now.year
        
        for _ in range(12):  # Maximum 12 mois
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
            
            # Vérifier si le jour existe dans ce mois
            max_day = monthrange(current_year, current_month)[1]
            if self.day <= max_day:
                target_date = datetime(
                    year=current_year,
                    month=current_month,
                    day=self.day,
                    hour=self.hour,
                    minute=self.minute,
                    second=0,
                    microsecond=0
                )
                return target_date
        
        # Aucune date trouvée (très improbable)
        return None
    
    def get_description(self) -> str:
        """Description lisible"""
        return f"Le {self.day} de chaque mois à {self.hour:02d}:{self.minute:02d}"


class TriggerFactory:
    """
    Factory pour créer les triggers appropriés selon le type de planification
    """
    
    _trigger_classes = {
        ScheduleType.INTERVAL: IntervalTrigger,
        ScheduleType.CRON: CronTrigger,
        ScheduleType.DAILY: DailyTrigger,
        ScheduleType.WEEKLY: WeeklyTrigger,
        ScheduleType.ONCE: OnceTrigger,
        ScheduleType.STARTUP: StartupTrigger,
        ScheduleType.SHUTDOWN: ShutdownTrigger,
        ScheduleType.MONTHLY: MonthlyTrigger,
    }
    
    @classmethod
    def create_trigger(cls, schedule_type: ScheduleType, schedule_value: any) -> BaseTrigger:
        """
        Crée un trigger selon le type de planification
        
        Args:
            schedule_type: Type de planification
            schedule_value: Valeur de planification
            
        Returns:
            Instance du trigger approprié
            
        Raises:
            SchedulingError: Si le type n'est pas supporté
        """
        if schedule_type not in cls._trigger_classes:
            raise SchedulingError(f"Type de planification non supporté: {schedule_type}")
        
        trigger_class = cls._trigger_classes[schedule_type]
        
        try:
            return trigger_class(schedule_value)
        except Exception as e:
            raise SchedulingError(
                f"Erreur création trigger {schedule_type.value}: {e}",
                {"schedule_type": schedule_type.value, "schedule_value": str(schedule_value)}
            )
    
    @classmethod
    def get_supported_types(cls) -> List[ScheduleType]:
        """Retourne la liste des types supportés"""
        return list(cls._trigger_classes.keys())
    
    @classmethod
    def describe_schedule(cls, schedule_type: ScheduleType, schedule_value: any) -> str:
        """
        Retourne une description lisible d'une planification
        
        Args:
            schedule_type: Type de planification
            schedule_value: Valeur de planification
            
        Returns:
            Description en français
        """
        try:
            trigger = cls.create_trigger(schedule_type, schedule_value)
            return trigger.get_description()
        except Exception as e:
            return f"Planification invalide: {e}"


# Fonctions utilitaires pour tests et validation

def validate_schedule(schedule_type: ScheduleType, schedule_value: any) -> bool:
    """
    Valide une configuration de planification
    
    Args:
        schedule_type: Type de planification
        schedule_value: Valeur de planification
        
    Returns:
        True si valide
        
    Raises:
        SchedulingError: Si invalide
    """
    TriggerFactory.create_trigger(schedule_type, schedule_value)
    return True


def get_next_executions(
    schedule_type: ScheduleType, 
    schedule_value: any, 
    count: int = 5,
    start_from: Optional[datetime] = None
) -> List[datetime]:
    """
    Calcule les prochaines exécutions d'une planification
    
    Args:
        schedule_type: Type de planification
        schedule_value: Valeur de planification
        count: Nombre d'exécutions à calculer
        start_from: Date de départ (par défaut: maintenant)
        
    Returns:
        Liste des prochaines dates d'exécution
    """
    trigger = TriggerFactory.create_trigger(schedule_type, schedule_value)
    executions = []
    
    last_run = start_from
    for _ in range(count):
        next_run = trigger.get_next_run_time(last_run)
        if next_run is None:
            break
        executions.append(next_run)
        last_run = next_run
    
    return executions