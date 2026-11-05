"""Entités des versions précédentes retirées du registre (spec ha-integration, Entités de commande retirées)."""

import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.screen_time_wallet.const import DOMAIN

from test_settlement import WEDNESDAY, start

RETIRED = (("number", "minutes"), ("button", "add_time"), ("button", "remove_time"))


def retired_entities(hass, entry):
    registry = er.async_get(hass)
    return [registry.async_get_entity_id(domain, DOMAIN, f"{entry.entry_id}_{key}") for domain, key in RETIRED]


@pytest.mark.requirement("ha-integration/Entités de commande retirées")
async def test_entites_orphelines_supprimees(hass, freezer, entry):
    registry = er.async_get(hass)
    for domain, key in RETIRED:  # entités créées par la v0.5.0
        registry.async_get_or_create(domain, DOMAIN, f"{entry.entry_id}_{key}", config_entry=entry)
    assert all(retired_entities(hass, entry))
    await start(hass, freezer, entry, when=WEDNESDAY)
    assert retired_entities(hass, entry) == [None, None, None]


@pytest.mark.requirement("ha-integration/Entités de commande retirées")
async def test_capteurs_conserves(hass, freezer, entry):
    er.async_get(hass).async_get_or_create("number", DOMAIN, f"{entry.entry_id}_minutes", config_entry=entry)
    await start(hass, freezer, entry, when=WEDNESDAY)
    registry = er.async_get(hass)
    keys = {"available", "weekly_credit", "notes_capital", "last_settlement"}
    assert all(registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_{key}") for key in keys)
