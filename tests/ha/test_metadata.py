"""Métadonnées d'installation (spec ha-integration)."""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "custom_components" / "screen_time_wallet" / "manifest.json"


@pytest.mark.requirement("ha-integration/Métadonnées d'installation")
def test_manifeste_valide():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["domain"] == "screen_time_wallet"
    assert manifest["config_flow"] is True
    assert manifest["iot_class"] == "calculated"
    assert manifest["version"].count(".") == 2
    assert manifest["requirements"] == []  # aucune dépendance Python à l'exécution


@pytest.mark.requirement("ha-integration/Métadonnées d'installation")
def test_fichier_hacs_valide():
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    assert hacs["name"]
