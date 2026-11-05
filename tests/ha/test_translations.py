"""Traductions : mêmes clés en français et en anglais, et toutes les clés utilisées existent."""

import json
from pathlib import Path

import pytest
import yaml

from custom_components.screen_time_wallet import report, sensor
from custom_components.screen_time_wallet.const import (
    OPT_EXCLUDE_NS, OPT_FALLBACK, OPT_MAX_HOURS, OPT_MIN_SUBJECTS, OPT_MIN_WEIGHT,
    OPT_NOTES_SHARE, OPT_NOTIFY_SERVICE, OPT_PIVOT, OPT_WEEKLY_REPORT,
)

COMPONENT = Path(__file__).resolve().parents[2] / "custom_components" / "screen_time_wallet"


def load(language):
    return json.loads((COMPONENT / "translations" / f"{language}.json").read_text(encoding="utf-8"))


def keys(tree, prefix=""):
    out = set()
    for key, value in tree.items():
        path = f"{prefix}.{key}" if prefix else key
        out |= keys(value, path) if isinstance(value, dict) else {path}
    return out


@pytest.mark.requirement("ha-integration/Traductions")
def test_memes_cles_en_francais_et_en_anglais():
    assert keys(load("fr")) == keys(load("en"))


@pytest.mark.requirement("ha-integration/Traductions")
def test_libelles_du_rapport_dans_les_deux_langues():
    assert set(report.TEXTS["fr"]) == set(report.TEXTS["en"])


@pytest.mark.requirement("ha-integration/Traductions")
@pytest.mark.parametrize("language", ["fr", "en"])
def test_textes_utilises_par_le_code_presents(language):
    t = load(language)
    option_fields = {OPT_MAX_HOURS, OPT_NOTES_SHARE, OPT_PIVOT, OPT_MIN_WEIGHT, OPT_MIN_SUBJECTS,
                     OPT_FALLBACK, OPT_EXCLUDE_NS, OPT_WEEKLY_REPORT, OPT_NOTIFY_SERVICE}
    assert option_fields <= set(t["options"]["step"]["parametres"]["data"])
    assert {d.translation_key for d in sensor.DESCRIPTIONS} <= set(t["entity"]["sensor"])
    assert {"invalid_config", "invalid_notify_service", "subject_required", "unknown_subject",
            "empty_table", "no_source", "source_unavailable"} <= set(t["options"]["error"])
    assert {"subjects_added", "no_new_subjects"} <= set(t["options"]["abort"])
    assert "detect" in t["options"]["step"]["matieres"]["data"]
    assert {"subjects_title", "subjects_added"} <= set(report.TEXTS[language])
    services = yaml.safe_load((COMPONENT / "services.yaml").read_text(encoding="utf-8"))
    assert set(services) == set(t["services"])
