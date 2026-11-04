"""Crédits du lundi : crédit initial (moyenne générale) et crédit de semaine (spec weekly-credit)."""

import math
from collections.abc import Iterable, Mapping
from fractions import Fraction

from .config import Config, to_fraction
from .grades import Grade


def round_half_away_from_zero(x: Fraction) -> int:
    magnitude = math.floor(abs(x) + Fraction(1, 2))
    return magnitude if x >= 0 else -magnitude


def usable_averages(averages: Mapping[str, object], config: Config) -> dict[str, Fraction]:
    """Moyennes numériques des matières de multiplicateur strictement positif."""
    usable = {}
    for subject, raw in averages.items():
        average = to_fraction(raw)
        if average is not None and config.multiplier_for(subject) > 0:
            usable[subject] = average
    return usable


def has_enough_subjects(averages: Mapping[str, object], config: Config) -> bool:
    return len(usable_averages(averages, config)) >= config.min_subjects


def general_average(averages: Mapping[str, object], config: Config) -> Fraction | None:
    """Moyenne des moyennes par matière pondérée par les multiplicateurs (None si aucune)."""
    usable = usable_averages(averages, config)
    total = sum((config.multiplier_for(s) for s in usable), Fraction(0))
    if total == 0:
        return None
    return sum((config.multiplier_for(s) * a for s, a in usable.items()), Fraction(0)) / total


def initial_credit(averages: Mapping[str, object], config: Config) -> int:
    """Crédit hebdomadaire du lundi : issu de la moyenne générale, plancher à 0, repli sous le minimum."""
    if not has_enough_subjects(averages, config):
        return config.fallback_credit
    average = general_average(averages, config)
    exact = config.average_rate * config.multiplier_total * (average - config.pivot)
    return max(0, round_half_away_from_zero(exact))


def counted_grades(grades: Iterable[Grade], config: Config) -> list[Grade]:
    """Notes qui entrent dans la moyenne de la semaine."""
    return [g for g in grades if not (config.exclude_non_significant and g.non_significant)]


def week_average(grades: Iterable[Grade], general: Fraction, config: Config) -> Fraction:
    """Moyenne pondérée des notes de la semaine, complétée par la moyenne générale sous le poids minimal."""
    notes = counted_grades(grades, config)
    weight = sum((g.weight(config) for g in notes), Fraction(0))
    weighted = sum((g.weight(config) * g.on_20() for g in notes), Fraction(0))
    denominator = max(weight, config.min_weight)
    if denominator == 0:
        return general
    return (weighted + max(Fraction(0), config.min_weight - weight) * general) / denominator


def week_credit(grades: Iterable[Grade], averages: Mapping[str, object], config: Config) -> int:
    """Crédit de semaine (positif ou négatif) ajouté au capital notes ; 0 sous le minimum de matières."""
    if not has_enough_subjects(averages, config):
        return 0
    general = general_average(averages, config)
    average = week_average(grades, general, config)
    exact = config.week_rate * config.multiplier_total * (average - config.pivot)
    return round_half_away_from_zero(exact)
