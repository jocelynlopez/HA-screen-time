"""Paramètres modifiables du portefeuille (voir specs weekly-credit et grade-conversion)."""

import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from fractions import Fraction


class ConfigError(ValueError):
    """Configuration incohérente (pivot ≥ 20, somme des multiplicateurs nulle…)."""


def to_fraction(raw) -> Fraction | None:
    """Nombre lu de façon tolérante (virgule décimale acceptée), ou None s'il n'est pas numérique."""
    if isinstance(raw, bool) or raw is None:
        return None
    if isinstance(raw, Fraction):
        return raw
    if isinstance(raw, str):
        raw = raw.strip().replace(",", ".")
        if not raw:
            return None
    try:
        return Fraction(Decimal(str(raw)))
    except (InvalidOperation, ValueError):
        return None


def normalize_subject(name: str) -> str:
    """Nom de matière sans accents, casse ni espaces superflus."""
    decomposed = unicodedata.normalize("NFD", name)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return " ".join(stripped.casefold().split())


# Noms de matières tels que les fournit EcoleDirecte.
DEFAULT_MULTIPLIERS = {
    "MATHEMATIQUES": Fraction(3),
    "FRANCAIS": Fraction(3),
    "ANGLAIS LV1": Fraction(3),
    "ENS.INTEG.SC.&TECHNO": Fraction(3),
    "HISTOIRE-GEOGRAPHIE": Fraction(2),
    "EDUCATION MUSICALE": Fraction(1, 2),
    "ARTS PLASTIQUES": Fraction(1, 2),
    "ED PHYSIQUE & SPORT": Fraction(1, 2),
}


@dataclass(frozen=True)
class Config:
    max_weekly_minutes: Fraction = Fraction(1200)  # crédits d'une semaine à 20/20 partout
    notes_share: Fraction = Fraction(3, 5)  # part du maximum attribuée aux notes de la semaine
    pivot: Fraction = Fraction(12)  # note pivot, sur 20
    subject_multipliers: dict[str, Fraction] = field(
        default_factory=lambda: dict(DEFAULT_MULTIPLIERS)
    )
    min_weight: Fraction = Fraction(3)  # poids minimal des notes d'une semaine
    min_subjects: int = 4  # matières avec moyenne requises pour calculer les crédits
    fallback_credit: int = 240  # crédit initial quand il y a moins de min_subjects matières
    exclude_non_significant: bool = False  # ignorer les notes non significatives

    def __post_init__(self):
        for name in ("max_weekly_minutes", "notes_share", "pivot", "min_weight"):
            value = to_fraction(getattr(self, name))
            if value is None:
                raise ConfigError(f"{name} : valeur non numérique")
            object.__setattr__(self, name, value)
        table = {k: to_fraction(v) for k, v in self.subject_multipliers.items()}
        if any(v is None or v < 0 for v in table.values()):
            raise ConfigError("subject_multipliers : multiplicateur invalide")
        object.__setattr__(self, "subject_multipliers", table)
        if self.pivot >= 20:
            raise ConfigError("pivot : doit être inférieur à 20")
        if self.multiplier_total <= 0:
            raise ConfigError("subject_multipliers : somme des multiplicateurs nulle")
        if not 0 <= self.notes_share <= 1:
            raise ConfigError("notes_share : doit être compris entre 0 et 1")

    @property
    def _normalized_table(self) -> dict[str, Fraction]:
        return {normalize_subject(k): v for k, v in self.subject_multipliers.items()}

    @property
    def multiplier_total(self) -> Fraction:
        return sum(self.subject_multipliers.values(), Fraction(0))

    @property
    def average_rate(self) -> Fraction:
        """Minutes par point d'écart de la moyenne générale, par unité de multiplicateur."""
        return self.max_weekly_minutes * (1 - self.notes_share) / ((20 - self.pivot) * self.multiplier_total)

    @property
    def week_rate(self) -> Fraction:
        """Minutes par point d'écart de la moyenne de la semaine, par unité de multiplicateur."""
        return self.max_weekly_minutes * self.notes_share / ((20 - self.pivot) * self.multiplier_total)

    def is_known(self, subject: str) -> bool:
        return normalize_subject(subject) in self._normalized_table

    def multiplier_for(self, subject: str) -> Fraction:
        """Multiplicateur de la matière ; 0 si elle n'est pas dans la table."""
        return self._normalized_table.get(normalize_subject(subject), Fraction(0))
