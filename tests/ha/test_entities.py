"""Capteurs, journal exposé et services (spec ha-integration)."""

import pytest
import voluptuous as vol
from homeassistant.helpers import entity_registry as er

from custom_components.screen_time_wallet.const import DOMAIN

from test_settlement import AP_FR, MONDAY_9, SEVEN, FakeSource, start, tick


def entity_id(hass, entry, key):
    found = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_{key}")
    assert found, f"capteur {key} introuvable"
    return found


def state(hass, entry, key):
    return hass.states.get(entity_id(hass, entry, key))


@pytest.fixture
async def runtime(hass, freezer, entry):
    return await start(hass, freezer, entry)


# --- Capteurs du portefeuille ---------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Capteurs du portefeuille")
async def test_temps_disponible(hass, entry, runtime):
    runtime.wallet.weekly_credit, runtime.wallet.notes_capital = 228, -100
    runtime.async_notify_entities()
    await hass.async_block_till_done()
    sensor = state(hass, entry, "available")
    assert sensor.state == "128" and sensor.attributes["unit_of_measurement"] == "min"
    assert state(hass, entry, "weekly_credit").state == "228"
    assert state(hass, entry, "notes_capital").state == "-100"


@pytest.mark.requirement("ha-integration/Capteurs du portefeuille")
async def test_mise_a_jour_immediate_apres_consommation(hass, entry, runtime):
    assert state(hass, entry, "available").state == "240"
    await runtime.async_consume(100)
    await hass.async_block_till_done()
    assert state(hass, entry, "available").state == "140"
    assert state(hass, entry, "weekly_credit").state == "140"


@pytest.mark.requirement("ha-integration/Capteurs du portefeuille")
async def test_dernier_bilan(hass, freezer, entry, runtime):
    runtime.source = FakeSource(SEVEN, AP_FR)
    await tick(hass, freezer, MONDAY_9)
    sensor = state(hass, entry, "last_settlement")
    assert sensor.state.startswith("2026-11-09T00:00:00")
    assert sensor.attributes["initial_credit"] == 228 and sensor.attributes["week_credit"] == -374


@pytest.mark.requirement("ha-integration/Capteurs du portefeuille")
async def test_noms_des_entites_traduits(hass, entry, runtime):
    assert hass.states.get("sensor.mael_available_time") is not None
    assert hass.states.get("sensor.mael_notes_capital") is not None


# --- Journal des mouvements exposé -------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Journal des mouvements exposé")
async def test_journal_du_plus_recent_au_plus_ancien(hass, freezer, entry, runtime):
    runtime.source = FakeSource(SEVEN, AP_FR)
    await tick(hass, freezer, MONDAY_9)
    await runtime.async_consume(60, "jeu console")
    await runtime.async_adjust(30, "bonus")
    await hass.async_block_till_done()
    movements = state(hass, entry, "last_settlement").attributes["movements"]
    assert [m["kind"] for m in movements] == ["ajustement", "consommation", "bilan"]
    assert movements[0]["reason"] == "bonus" and movements[0]["capital_change"] == 30


@pytest.mark.requirement("ha-integration/Journal des mouvements exposé")
async def test_journal_limite_a_20(hass, entry, runtime):
    for i in range(25):
        await runtime.async_consume(1, str(i))
    await hass.async_block_till_done()
    movements = state(hass, entry, "last_settlement").attributes["movements"]
    assert len(movements) == 20 and movements[0]["reason"] == "24" and movements[-1]["reason"] == "5"


# --- Service de consommation ---------------------------------------------------------------------------

async def call(hass, service, **data):
    await hass.services.async_call(DOMAIN, service, data, blocking=True)


@pytest.mark.requirement("ha-integration/Service de consommation")
async def test_consommation_avec_motif_et_enregistrement(hass, hass_storage, entry, runtime):
    runtime.wallet.weekly_credit = 228
    await call(hass, "consume", entity_id=entity_id(hass, entry, "available"), minutes=45, reason="jeu console")
    assert runtime.wallet.weekly_credit == 183
    last = runtime.wallet.movements[-1]
    assert (last.kind, last.weekly_change, last.reason) == ("consommation", -45, "jeu console")
    assert hass_storage[f"{DOMAIN}.{entry.entry_id}"]["data"]["weekly_credit"] == 183


@pytest.mark.requirement("ha-integration/Service de consommation")
async def test_consommation_de_zero_refusee(hass, entry, runtime):
    with pytest.raises(vol.Invalid):
        await call(hass, "consume", entity_id=entity_id(hass, entry, "available"), minutes=0)
    assert runtime.wallet.weekly_credit == 240 and runtime.wallet.movements == []


# --- Service d'ajustement manuel ---------------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Service d'ajustement manuel")
async def test_bonus_parental(hass, hass_storage, entry, runtime):
    runtime.wallet.notes_capital = 100
    await call(hass, "adjust", entity_id=entity_id(hass, entry, "available"), minutes=30, reason="aide aux devoirs")
    assert runtime.wallet.notes_capital == 130 and runtime.wallet.movements[-1].reason == "aide aux devoirs"
    assert hass_storage[f"{DOMAIN}.{entry.entry_id}"]["data"]["notes_capital"] == 130


@pytest.mark.requirement("ha-integration/Service d'ajustement manuel")
async def test_sanction(hass, entry, runtime):
    runtime.wallet.notes_capital = 100
    await call(hass, "adjust", entity_id=entity_id(hass, entry, "available"), minutes=-50)
    assert runtime.wallet.notes_capital == 50


@pytest.mark.requirement("ha-integration/Service d'ajustement manuel")
async def test_ajustement_nul_refuse(hass, entry, runtime):
    with pytest.raises(vol.Invalid):
        await call(hass, "adjust", entity_id=entity_id(hass, entry, "available"), minutes=0)
    assert runtime.wallet.notes_capital == 0
