"""Options de l'interface et conversion vers la configuration du cœur (fonctions pures)."""

from collections.abc import Mapping

from .const import (
    OPT_EXCLUDE_NS,
    OPT_FALLBACK,
    OPT_MAX_HOURS,
    OPT_MIN_SUBJECTS,
    OPT_MIN_WEIGHT,
    OPT_MULTIPLIERS,
    OPT_NOTES_ENTITY,
    OPT_NOTES_SHARE,
    OPT_NOTIFY_SERVICE,
    OPT_PIVOT,
    OPT_WEEKLY_REPORT,
)
from .engine.config import DEFAULT_MULTIPLIERS, Config, to_fraction

DEFAULT_OPTIONS = {
    OPT_MAX_HOURS: 20,
    OPT_NOTES_SHARE: 60,
    OPT_PIVOT: 12,
    OPT_MIN_WEIGHT: 3,
    OPT_MIN_SUBJECTS: 4,
    OPT_FALLBACK: 240,
    OPT_EXCLUDE_NS: False,
    OPT_WEEKLY_REPORT: True,
    OPT_NOTIFY_SERVICE: "",
    OPT_NOTES_ENTITY: "",
    OPT_MULTIPLIERS: {name: float(value) for name, value in DEFAULT_MULTIPLIERS.items()},
}


def with_defaults(options: Mapping) -> dict:
    """Options complétées par les valeurs par défaut."""
    merged = {**DEFAULT_OPTIONS, **options}
    merged[OPT_MULTIPLIERS] = dict(merged[OPT_MULTIPLIERS])
    return merged


def build_config(options: Mapping) -> Config:
    """Configuration du cœur : heures → minutes, pourcentage → fraction. Lève ConfigError si incohérente."""
    o = with_defaults(options)
    return Config(
        max_weekly_minutes=to_fraction(o[OPT_MAX_HOURS]) * 60,
        notes_share=to_fraction(o[OPT_NOTES_SHARE]) / 100,
        pivot=to_fraction(o[OPT_PIVOT]),
        subject_multipliers={name: to_fraction(v) for name, v in o[OPT_MULTIPLIERS].items()},
        min_weight=to_fraction(o[OPT_MIN_WEIGHT]),
        min_subjects=int(o[OPT_MIN_SUBJECTS]),
        fallback_credit=int(o[OPT_FALLBACK]),
        exclude_non_significant=bool(o[OPT_EXCLUDE_NS]),
    )

