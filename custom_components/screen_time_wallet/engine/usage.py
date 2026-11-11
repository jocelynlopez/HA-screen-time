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
    suspect: bool = False  # total périmé de la veille repris sous la date du jour : la prochaine baisse vaut remise à zéro

    def to_json(self) -> dict:
        data = {"minutes": f"{self.minutes.numerator}/{self.minutes.denominator}", "date": self.day}
        if self.suspect:
            data["suspect"] = True
        return data

    @classmethod
    def from_json(cls, data: dict) -> "Baseline":
        return cls(Fraction(data["minutes"]), normalize_day(data.get("date")), data.get("suspect") is True)


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

    Un jour différent de celui de la référence vaut remise à zéro du compteur, sauf si le relevé est identique à la
    référence : c'est alors le total périmé de la veille (la date change avant les minutes), rien n'est consommé et la
    baisse suivante est acceptée. Le compteur ne baissant pas dans la journée, une baisse le même jour est ignorée : la
    référence garde le maximum du jour (une valeur oscillante n'est jamais recomptée). Sans date, une baisse est une
    remise à zéro immédiate.
    La référence n'avance que des minutes consommées : les fractions sont reportées au relevé suivant.
    Un relevé invalide est ignoré (rien consommé, référence inchangée).
    """
    reading = to_fraction(minutes)
    if reading is None or reading < 0:
        return 0, baseline
    day = normalize_day(day)
    if baseline is None:
        return 0, Baseline(reading, day)
    if day and baseline.day and day != baseline.day:
        if reading == baseline.minutes and reading > 0:
            return 0, Baseline(baseline.minutes, day, True)
        baseline = Baseline(Fraction(0), day)
    elif reading < baseline.minutes:
        if day and baseline.day and not baseline.suspect:
            return 0, baseline
        baseline = Baseline(Fraction(0), day)
    consumed = floor(reading - baseline.minutes)
    return consumed, Baseline(baseline.minutes + consumed, day or baseline.day)
