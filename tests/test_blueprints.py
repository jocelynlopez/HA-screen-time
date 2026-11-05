"""Blueprints de script « ajouter / retirer du temps » (spec ha-integration, Blueprints de script)."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINTS = ROOT / "blueprints" / "script" / "screen_time_wallet"
README = (ROOT / "README.md").read_text(encoding="utf-8")


class Loader(yaml.SafeLoader):
    """Lecteur YAML qui accepte l'étiquette !input des blueprints de Home Assistant."""


Loader.add_constructor("!input", lambda loader, node: {"__input__": loader.construct_scalar(node)})


def load(name):
    return yaml.load((BLUEPRINTS / f"{name}.yaml").read_text(encoding="utf-8"), Loader)


@pytest.mark.requirement("ha-integration/Blueprints de script")
@pytest.mark.parametrize("name, action", [("add_time", "screen_time_wallet.adjust"),
                                           ("remove_time", "screen_time_wallet.consume")])
def test_action_appelee_avec_les_minutes_et_la_raison(name, action):
    blueprint = load(name)
    assert blueprint["blueprint"]["domain"] == "script"
    (step,) = blueprint["sequence"]
    assert step["action"] == action
    assert step["target"]["entity_id"] == {"__input__": "wallet_sensor"}
    assert step["data"] == {"minutes": "{{ minutes }}", "reason": "{{ reason }}"}


@pytest.mark.requirement("ha-integration/Blueprints de script")
@pytest.mark.parametrize("name", ["add_time", "remove_time"])
def test_capteur_du_portefeuille_demande(name):
    selector = load(name)["blueprint"]["input"]["wallet_sensor"]["selector"]["entity"]
    assert selector["domain"] == "sensor" and selector["integration"] == "screen_time_wallet"


@pytest.mark.requirement("ha-integration/Blueprints de script")
@pytest.mark.parametrize("name", ["add_time", "remove_time"])
def test_raison_obligatoire_et_minutes_bornees(name):
    fields = load(name)["fields"]
    assert fields["reason"]["required"] is True and "text" in fields["reason"]["selector"]
    number = fields["minutes"]["selector"]["number"]
    assert fields["minutes"]["required"] is True and (number["min"], number["max"]) == (1, 600)


@pytest.mark.requirement("ha-integration/Blueprints de script")
@pytest.mark.parametrize("name", ["add_time", "remove_time"])
def test_import_propose_dans_le_readme(name):
    url = ("https%3A%2F%2Fgithub.com%2Fjocelynlopez%2FHA-screen-time%2Fblob%2Fmain%2Fblueprints%2Fscript"
           f"%2Fscreen_time_wallet%2F{name}.yaml")
    assert f"https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url={url}" in README
    assert load(name)["blueprint"]["source_url"].endswith(f"/blueprints/script/screen_time_wallet/{name}.yaml")
