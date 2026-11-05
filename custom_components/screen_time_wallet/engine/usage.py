"""Consommation déduite des relevés d'un compteur journalier en minutes (spec screen-time-usage)."""

from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from math import floor

from .config import to_fraction


@dataclass(frozen=True)
class Baseline:
    """Relevé de référence d'un compteur : minutes et jour du relevé (None si le capteur n'en donne pas)."""

    minutes: Fraction
    day: str | None = None

    def to_json(self) -> dict:
        return {"minutes": f"{self.minutes.numerator}/{self.minutes.denominator}", "date": self.day}

    @classmethod
    def from_json(cls, data: dict) -> "Baseline":
        return cls(Fraction(data["minutes"]), normalize_day(data.get("date")))


def normalize_day(raw) -> str | None:
    """Jour AAAA-MM-JJ lisible, ou None."""
    if isinstance(raw, date):
        return raw.isoformat()
    if not isinstance(raw, str):
        return None
    try:
        return date.fromisoformat(raw.strip()).isoformat()
    except ValueError:
        return None


def reading_minutes(state, total_seconds=None) -> Fraction | None:
    """Relevé en minutes : `total_seconds` / 60 s'il est numérique, sinon l'état ; None si invalide ou négatif."""
    seconds = to_fraction(total_seconds)
    minutes = seconds / 60 if seconds is not None else to_fraction(state)
    if minutes is None or minutes < 0:
        return None
    return minutes


def consumed_since(baseline: Baseline | None, minutes, day=None) -> tuple[int, Baseline | None]:
    """Minutes entières consommées depuis la référence, et nouvelle référence.

    Un jour différent de celui de la référence, ou à défaut de jour une valeur plus basse, vaut remise à zéro du
    compteur. La référence n'avance que des minutes consommées : les fractions sont reportées au relevé suivant.
    Un relevé invalide est ignoré (rien consommé, référence inchangée).
    """
    reading = to_fraction(minutes)
    if reading is None or reading < 0:
        return 0, baseline
    day = normalize_day(day)
    if baseline is None:
        return 0, Baseline(reading, day)
    if (day and baseline.day and day != baseline.day) or reading < baseline.minutes:
        baseline = Baseline(Fraction(0), day)
    consumed = floor(reading - baseline.minutes)
    return consumed, Baseline(baseline.minutes + consumed, day or baseline.day)
