"""Portefeuille de minutes de temps d'écran (spec screen-time-wallet)."""

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta

from .config import Config
from .grades import Grade, convert


def monday_midnight(moment: datetime) -> datetime:
    """Lundi 00h00 de la semaine contenant `moment` (heure locale naïve)."""
    return datetime.combine(moment.date() - timedelta(days=moment.weekday()), time.min)


@dataclass
class Wallet:
    balance: int
    last_allocation: datetime  # dernier lundi 00h00 crédité
    config: Config = field(default_factory=Config)
    processed_ids: set[str] = field(default_factory=set)

    @classmethod
    def create(cls, now: datetime, config: Config | None = None) -> "Wallet":
        """Crée un portefeuille avec l'allocation de la semaine en cours."""
        config = config or Config()
        return cls(config.weekly_allocation, monday_midnight(now), config)

    def update(self, now: datetime) -> int:
        """Crédite l'allocation de chaque lundi 00h00 écoulé ; renvoie les minutes créditées."""
        weeks = (monday_midnight(now) - self.last_allocation).days // 7
        if weeks <= 0:
            return 0
        credited = weeks * self.config.weekly_allocation
        self.balance += credited
        self.last_allocation += timedelta(weeks=weeks)
        return credited

    def apply_grade(self, grade: Grade) -> int:
        """Applique une note au solde ; renvoie les minutes ajoutées (0 si ignorée).

        Lève InvalidGradeError, sans rien modifier, si la note est invalide.
        """
        if grade.id in self.processed_ids:
            return 0
        if grade.numeric_value() is None:
            return 0  # absent, dispensé, non noté : ignorée, id non marqué
        minutes = convert(grade, self.config)
        self.balance += minutes
        self.processed_ids.add(grade.id)
        return minutes
