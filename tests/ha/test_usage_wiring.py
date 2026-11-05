"""Capteurs de temps d'écran : consommation automatique et relevés de référence (spec ha-integration)."""

from datetime import datetime

import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.screen_time_wallet.const import DOMAIN
from custom_components.screen_time_wallet.engine.usage import Baseline
from custom_components.screen_time_wallet.engine.wallet import Wallet

from conftest import make_entry
from test_settlement import WEDNESDAY, start

PC = "sensor.pc_mael_screen_time"
TABLET = "sensor.tablette_screen_time"
D1, D2 = "2026-11-04", "2026-11-05"


def set_usage(hass, entity, minutes, day=D1, seconds=True, name="PC-MAEL Screen Time"):
    attributes = {"date": day, "friendly_name": name}
    if seconds:
        attributes["total_seconds"] = minutes * 60
    hass.states.async_set(entity, str(int(minutes)), attributes)


async def set_and_wait(hass, entity, minutes, **kwargs):
    set_usage(hass, entity, minutes, **kwargs)
    await hass.async_block_till_done()


async def start_with(hass, freezer, sensors, **options):
    entry = make_entry(options={"usage_entities": sensors, **options})
    entry.add_to_hass(hass)
    return entry, await start(hass, freezer, entry)


def stored(hass_storage, entry):
    return hass_storage[f"{DOMAIN}.{entry.entry_id}"]["data"]


def preload(hass_storage, entry, baselines, weekly_credit=240):
    key = f"{DOMAIN}.{entry.entry_id}"
    wallet = Wallet(weekly_credit=weekly_credit, notes_capital=0, last_settlement=datetime(2026, 11, 2))
    data = {**wallet.to_dict(), "usage_baselines": {e: b.to_json() for e, b in baselines.items()}}
    hass_storage[key] = {"version": 1, "minor_version": 1, "key": key, "data": data}


# --- Capteurs de temps d'écran ---------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Capteurs de temps d'écran")
async def test_choix_d_un_capteur_prend_le_releve_pour_reference(hass, freezer):
    set_usage(hass, PC, 87)
    entry, runtime = await start_with(hass, freezer, [PC])
    assert runtime.baselines[PC] == Baseline(87, D1)
    assert runtime.wallet.weekly_credit == 240 and runtime.wallet.movements == []


@pytest.mark.requirement("ha-integration/Capteurs de temps d'écran")
async def test_releve_en_secondes_prioritaire_sur_l_etat(hass, freezer):
    hass.states.async_set(PC, "10", {"total_seconds": 660, "date": D1})
    entry, runtime = await start_with(hass, freezer, [PC])
    assert runtime.baselines[PC].minutes == 11


@pytest.mark.requirement("ha-integration/Capteurs de temps d'écran")
async def test_repli_sur_l_etat_sans_total_seconds(hass, freezer):
    set_usage(hass, PC, 10, seconds=False)
    entry, runtime = await start_with(hass, freezer, [PC])
    await set_and_wait(hass, PC, 25, seconds=False)
    assert runtime.wallet.weekly_credit == 225


@pytest.mark.requirement("ha-integration/Capteurs de temps d'écran")
async def test_capteur_retire_puis_rajoute(hass, freezer, hass_storage):
    set_usage(hass, PC, 10)
    entry, runtime = await start_with(hass, freezer, [PC])
    hass.config_entries.async_update_entry(entry, options={"usage_entities": []})
    await hass.async_block_till_done()
    assert PC not in entry.runtime_data.baselines and PC not in stored(hass_storage, entry)["usage_baselines"]
    set_usage(hass, PC, 50)
    hass.config_entries.async_update_entry(entry, options={"usage_entities": [PC]})
    await hass.async_block_till_done()
    assert entry.runtime_data.baselines[PC].minutes == 50
    assert entry.runtime_data.wallet.weekly_credit == 240  # rien consommé par le nouveau relevé


# --- Consommation automatique --------------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Consommation automatique")
async def test_consommation_d_un_releve(hass, freezer):
    set_usage(hass, PC, 10)
    entry, runtime = await start_with(hass, freezer, [PC])
    runtime.wallet.weekly_credit = 228
    await set_and_wait(hass, PC, 25)
    assert runtime.wallet.weekly_credit == 213
    movement = runtime.wallet.movements[-1]
    assert (movement.kind, movement.reason, movement.weekly_change) == ("consommation", "PC-MAEL Screen Time", -15)
    available = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_available")
    assert hass.states.get(available).state == "213"


@pytest.mark.requirement("ha-integration/Consommation automatique")
async def test_deux_capteurs_s_additionnent(hass, freezer):
    set_usage(hass, PC, 10)
    set_usage(hass, TABLET, 0, name="Tablette")
    entry, runtime = await start_with(hass, freezer, [PC, TABLET])
    await set_and_wait(hass, PC, 25)
    await set_and_wait(hass, TABLET, 20, name="Tablette")
    assert runtime.wallet.weekly_credit == 240 - 35
    assert sorted(m.reason for m in runtime.wallet.movements) == ["PC-MAEL Screen Time", "Tablette"]


@pytest.mark.requirement("ha-integration/Consommation automatique")
@pytest.mark.parametrize("unusable", ["unavailable", "unknown"])
async def test_releve_indisponible_ignore(hass, freezer, unusable):
    set_usage(hass, PC, 25)
    entry, runtime = await start_with(hass, freezer, [PC])
    hass.states.async_set(PC, unusable, {"total_seconds": 99999, "date": D1})
    await hass.async_block_till_done()
    assert runtime.wallet.weekly_credit == 240 and runtime.baselines[PC].minutes == 25
    await set_and_wait(hass, PC, 30)
    assert runtime.wallet.weekly_credit == 235


@pytest.mark.requirement("ha-integration/Consommation automatique")
async def test_remise_a_zero_du_compteur(hass, freezer):
    set_usage(hass, PC, 190)
    entry, runtime = await start_with(hass, freezer, [PC])
    await set_and_wait(hass, PC, 12)  # même jour : une baisse vaut remise à zéro
    assert runtime.wallet.weekly_credit == 240 - 12


@pytest.mark.requirement("ha-integration/Consommation automatique")
async def test_changement_de_jour(hass, freezer):
    set_usage(hass, PC, 190, day=D1)
    entry, runtime = await start_with(hass, freezer, [PC])
    await set_and_wait(hass, PC, 8, day=D2)
    assert runtime.wallet.weekly_credit == 240 - 8
    assert runtime.baselines[PC] == Baseline(8, D2)


@pytest.mark.requirement("ha-integration/Consommation automatique")
async def test_usage_superieur_au_credit(hass, freezer):
    set_usage(hass, PC, 0)
    entry, runtime = await start_with(hass, freezer, [PC])
    runtime.wallet.weekly_credit = 10
    await set_and_wait(hass, PC, 25)
    assert (runtime.wallet.weekly_credit, runtime.wallet.notes_capital) == (0, -15)


@pytest.mark.requirement("ha-integration/Consommation automatique")
async def test_etat_enregistre_apres_consommation(hass, freezer, hass_storage):
    set_usage(hass, PC, 10)
    entry, runtime = await start_with(hass, freezer, [PC])
    await set_and_wait(hass, PC, 25)
    data = stored(hass_storage, entry)
    assert data["weekly_credit"] == 225
    assert data["usage_baselines"][PC] == {"minutes": "25/1", "date": D1}


@pytest.mark.requirement("screen-time-wallet/Regroupement des consommations automatiques")
async def test_releves_successifs_regroupes_dans_le_journal(hass, freezer):
    set_usage(hass, PC, 0)
    entry, runtime = await start_with(hass, freezer, [PC])
    for minutes in (5, 8, 15):
        await set_and_wait(hass, PC, minutes)
    assert len(runtime.wallet.movements) == 1 and runtime.wallet.movements[0].weekly_change == -15


# --- Relevés de référence conservés ----------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Relevés de référence conservés")
async def test_redemarrage(hass, freezer, hass_storage):
    entry = make_entry(options={"usage_entities": [PC]})
    entry.add_to_hass(hass)
    preload(hass_storage, entry, {PC: Baseline(25, D1)})
    set_usage(hass, PC, 40)
    runtime = await start(hass, freezer, entry)
    assert runtime.wallet.weekly_credit == 240 - 15 and runtime.baselines[PC].minutes == 40


@pytest.mark.requirement("ha-integration/Relevés de référence conservés")
async def test_remise_a_zero_pendant_l_arret(hass, freezer, hass_storage):
    entry = make_entry(options={"usage_entities": [PC]})
    entry.add_to_hass(hass)
    preload(hass_storage, entry, {PC: Baseline(190, None)})
    set_usage(hass, PC, 12)
    runtime = await start(hass, freezer, entry)
    assert runtime.wallet.weekly_credit == 240 - 12


@pytest.mark.requirement("ha-integration/Relevés de référence conservés")
async def test_changement_de_jour_pendant_l_arret(hass, freezer, hass_storage):
    entry = make_entry(options={"usage_entities": [PC]})
    entry.add_to_hass(hass)
    preload(hass_storage, entry, {PC: Baseline(190, D1)})
    set_usage(hass, PC, 200, day=D2)
    runtime = await start(hass, freezer, entry)
    assert runtime.wallet.weekly_credit == 240 - 200


@pytest.mark.requirement("ha-integration/Relevés de référence conservés")
async def test_rechargement_par_les_options(hass, freezer, hass_storage):
    set_usage(hass, PC, 10)
    entry, runtime = await start_with(hass, freezer, [PC])
    await set_and_wait(hass, PC, 25)
    hass.config_entries.async_update_entry(entry, options={"usage_entities": [PC], "weekly_report": False})
    await hass.async_block_till_done()
    reloaded = entry.runtime_data
    assert reloaded is not runtime
    assert reloaded.wallet.weekly_credit == 225 and reloaded.baselines[PC].minutes == 25
    await set_and_wait(hass, PC, 30)
    assert reloaded.wallet.weekly_credit == 220


@pytest.mark.requirement("ha-integration/Relevés de référence conservés")
async def test_releve_de_reference_illisible_ignore(hass, freezer, hass_storage):
    entry = make_entry(options={"usage_entities": [PC]})
    entry.add_to_hass(hass)
    preload(hass_storage, entry, {})
    hass_storage[f"{DOMAIN}.{entry.entry_id}"]["data"]["usage_baselines"] = {PC: {"minutes": "abc"}}
    set_usage(hass, PC, 40)
    runtime = await start(hass, freezer, entry)
    assert runtime.wallet.weekly_credit == 240 and runtime.baselines[PC].minutes == 40
