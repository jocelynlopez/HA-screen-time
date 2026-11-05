"""Entité « Minutes » et boutons d'ajout et de retrait de temps (spec ha-integration, Commandes du portefeuille)."""

import pytest
from homeassistant.core import State
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import mock_restore_cache_with_extra_data

from custom_components.screen_time_wallet.const import DOMAIN

from conftest import make_entry
from test_blocking import LOCK, Switches, settled
from test_settlement import WEDNESDAY, start


def entity_id(hass, entry, domain, key):
    found = er.async_get(hass).async_get_entity_id(domain, DOMAIN, f"{entry.entry_id}_{key}")
    assert found, f"{domain} {key} introuvable"
    return found


async def set_minutes(hass, entry, value):
    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id(hass, entry, "number", "minutes"), "value": value},
        blocking=True,
    )


async def press(hass, entry, key):
    await hass.services.async_call(
        "button", "press", {"entity_id": entity_id(hass, entry, "button", key)}, blocking=True
    )
    await hass.async_block_till_done()


@pytest.fixture
async def runtime(hass, freezer, entry):
    hass.config.language = "fr"
    return await start(hass, freezer, entry, when=WEDNESDAY)


@pytest.mark.requirement("ha-integration/Commandes du portefeuille")
async def test_valeur_par_defaut(hass, entry, runtime):
    state = hass.states.get(entity_id(hass, entry, "number", "minutes"))
    assert float(state.state) == 15 and state.attributes["step"] == 5
    assert (state.attributes["min"], state.attributes["max"]) == (1, 600)


@pytest.mark.requirement("ha-integration/Commandes du portefeuille")
async def test_ajouter_du_temps(hass, entry, runtime):
    runtime.wallet.notes_capital = 100
    await set_minutes(hass, entry, 30)
    await press(hass, entry, "add_time")
    assert runtime.wallet.notes_capital == 130 and runtime.wallet.available == 240 + 130
    movement = runtime.wallet.movements[-1]
    assert (movement.kind, movement.reason, movement.capital_change) == ("ajustement", "bouton", 30)


@pytest.mark.requirement("ha-integration/Commandes du portefeuille")
async def test_retirer_du_temps(hass, entry, runtime):
    runtime.wallet.weekly_credit = 228
    await set_minutes(hass, entry, 45)
    await press(hass, entry, "remove_time")
    assert runtime.wallet.weekly_credit == 183
    movement = runtime.wallet.movements[-1]
    assert (movement.kind, movement.reason) == ("consommation", "bouton")
    available = entity_id(hass, entry, "sensor", "available")
    assert hass.states.get(available).state == "183"


@pytest.mark.requirement("ha-integration/Commandes du portefeuille")
async def test_retrait_superieur_au_temps_disponible(hass, entry, runtime):
    runtime.wallet.weekly_credit = 10
    await set_minutes(hass, entry, 30)
    await press(hass, entry, "remove_time")
    assert (runtime.wallet.weekly_credit, runtime.wallet.notes_capital) == (0, -20)


@pytest.mark.requirement("ha-integration/Commandes du portefeuille")
async def test_bouton_declenche_le_blocage(hass, freezer):
    switches = Switches(hass)
    hass.states.async_set(LOCK, "off")
    entry = make_entry(options={"lock_switches": [LOCK]})
    entry.add_to_hass(hass)
    runtime = await start(hass, freezer, entry, when=WEDNESDAY)
    runtime.wallet.weekly_credit = 15
    await set_minutes(hass, entry, 15)
    await press(hass, entry, "remove_time")
    await settled(hass)
    assert switches.calls == [("on", LOCK)]


@pytest.mark.requirement("ha-integration/Commandes du portefeuille")
async def test_valeur_conservee_au_redemarrage(hass, freezer, entry):
    mock_restore_cache_with_extra_data(hass, [(
        State("number.mael_minutes", "60"),
        {"native_max_value": 600, "native_min_value": 1, "native_step": 5,
         "native_unit_of_measurement": "min", "native_value": 60},
    )])
    runtime = await start(hass, freezer, entry, when=WEDNESDAY)
    assert runtime.control_minutes == 60
    assert float(hass.states.get(entity_id(hass, entry, "number", "minutes")).state) == 60


@pytest.mark.requirement("ha-integration/Commandes du portefeuille")
async def test_valeur_hors_limites_refusee(hass, entry, runtime):
    with pytest.raises(HomeAssistantError):
        await set_minutes(hass, entry, 700)
    assert runtime.control_minutes == 15


@pytest.mark.requirement("ha-integration/Commandes du portefeuille")
async def test_commandes_sur_l_appareil_de_l_enfant(hass, entry, runtime):
    device, = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)  # un seul appareil
    assert (DOMAIN, entry.entry_id) in device.identifiers
    domains = {e.domain for e in er.async_entries_for_device(er.async_get(hass), device.id)}
    keys = {e.unique_id.split("_", 1)[1] for e in er.async_entries_for_device(er.async_get(hass), device.id)}
    assert {"sensor", "number", "button"} <= domains
    assert {"minutes", "add_time", "remove_time", "available"} <= keys
