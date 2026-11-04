"""Conversion d'une note en minutes (spec grade-conversion)."""

import math
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from fractions import Fraction

from .config import Config


class InvalidGradeError(ValueError):
    """Note incohérente (barème, valeur ou coefficient invalide)."""


@dataclass(frozen=True)
class Grade:
    id: str
    subject: str
    date: date
    value: object  # nombre, ou texte comme « Abs » / « Disp »
    scale: object = 20
    coefficient: object = 1

    def numeric_value(self) -> Fraction | None:
        """Valeur numérique de la note, ou None (absent, dispensé, non noté, vide)."""
        return _to_fraction(self.value)


def _to_fraction(raw: object) -> Fraction | None:
    if isinstance(raw, bool) or raw is None:
        return None
    if isinstance(raw, str):
        raw = raw.strip().replace(",", ".")
        if not raw:
            return None
    try:
        return Fraction(Decimal(str(raw)))
    except (InvalidOperation, ValueError):
        return None


def round_half_away_from_zero(x: Fraction) -> int:
    magnitude = math.floor(abs(x) + Fraction(1, 2))
    return magnitude if x >= 0 else -magnitude


def convert(grade: Grade, config: Config) -> int:
    """Minutes à créditer (>0) ou débiter (<0) pour une note à valeur numérique."""
    value = grade.numeric_value()
    scale = _to_fraction(grade.scale)
    coefficient = _to_fraction(grade.coefficient)
    if value is None:
        raise InvalidGradeError(f"note {grade.id} : valeur non numérique")
    if scale is None or scale <= 0:
        raise InvalidGradeError(f"note {grade.id} : barème invalide ({grade.scale!r})")
    if not 0 <= value <= scale:
        raise InvalidGradeError(f"note {grade.id} : valeur {value} hors du barème {scale}")
    if coefficient is None or coefficient < 0:
        raise InvalidGradeError(f"note {grade.id} : coefficient invalide ({grade.coefficient!r})")

    on_20 = value * 20 / scale
    minutes = (
        config.base_rate
        * config.multiplier_for(grade.subject)
        * (on_20 - config.pivot)
        * coefficient
    )
    return round_half_away_from_zero(minutes)
