"""Activation de la source, nouvelles tentatives et notification de panne (spec ha-integration)."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from homeassistant.util import dt as dt_util

from custom_components.screen_time_wallet.const import DOMAIN
from custom_components.screen_time_wallet.ecole_directe_source import EcoleDirecteSource
from custom_components.screen_time_wallet.engine.wallet import Wallet
from custom_components.screen_time_wallet.runtime import WalletRuntime
from custom_components.screen_time_wallet.source import SourceUnavailableError

from conftest import make_entry
from ed_helpers import add_all_subjects, add_ed_entry, add_notes
from real_notes import RAW
from test_options import save_params
from test_settlement import CREATE, calls_by_kind

DISMISS = "custom_components.screen_time_wallet.runtime.persistent_notification.async_dismiss"
WEDNESDAY = "2026-11-04 10:00:00+00:00"
MONDAY_2 = "2026-11-02 08:00:00+00:00"
NOTES = [
    {"date": d, "matiere": m, "commentaire": c, "note": v, "sur": s, "coefficient": k, "non_significatif": ns}
    for d, _saisie, m, c, v, s, k, ns in RAW
]


@pytest.fixture
async def ed(hass):
    """Intégration EcoleDirecte simulée : huit capteurs de matière et le capteur de notes (18 notes)."""
    entry = add_ed_entry(hass)
    add_all_subjects(hass, entry)
    return entry, add_notes(hass, entry, NOTES, state="18")


def initialisations(runtime):
    return [m for m in runtime.wallet.movements if m.kind == "initialisation"]


def stored(hass_storage, entry):
    return hass_storage[f"{DOMAIN}.{entry.entry_id}"]["data"]


async def advance(hass, freezer, **delta):
    freezer.tick(timedelta(**delta))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()


async def start(hass, freezer, entry, when=WEDNESDAY):
    freezer.move_to(when)
    assert await hass.config_entries.async_setup(entry.entry_id)
    return entry.runtime_data


# --- Activation de la source ---------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Activation de la source")
async def test_premiere_selection(hass, hass_storage, freezer, entry, ed):
    runtime = await start(hass, freezer, entry)
    assert runtime.wallet.weekly_credit == 240  # repli : aucune source
    await save_params(hass, entry, notes_entity=ed[1])
    runtime = entry.runtime_data
    assert runtime.wallet.weekly_credit == 228 and runtime.wallet.notes_capital == 0
    assert len(initialisations(runtime)) == 1
    assert stored(hass_storage, entry)["source_entity"] == ed[1]
    # les 18 notes visibles n'ont aucun effet au bilan suivant
    await advance(hass, freezer, days=5, hours=14)  # lundi 9/11 00h00 passé
    assert [m.capital_change for m in runtime.wallet.movements if m.kind == "bilan"] == [342]


@pytest.mark.requirement("ha-integration/Activation de la source")
async def test_changement_de_capteur(hass, freezer, entry, ed):
    other = add_ed_entry(hass, "Lena")
    add_all_subjects(hass, other)
    other_notes = add_notes(hass, other, [], object_id="ed_lena_notes", state="0")
    await start(hass, freezer, entry)
    await save_params(hass, entry, notes_entity=ed[1])
    await save_params(hass, entry, notes_entity=other_notes)
    assert len(initialisations(entry.runtime_data)) == 2


@pytest.mark.requirement("ha-integration/Activation de la source")
async def test_rechargement_sans_changement(hass, freezer, entry, ed):
    await start(hass, freezer, entry)
    await save_params(hass, entry, notes_entity=ed[1])
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert len(initialisations(entry.runtime_data)) == 1


@pytest.mark.requirement("ha-integration/Activation de la source")
async def test_source_pas_prete_activation_retentee(hass, freezer, ed):
    entry = make_entry(options={"notes_entity": ed[1]})
    entry.add_to_hass(hass)
    hass.states.async_set(ed[1], "unavailable", {})
    runtime = await start(hass, freezer, entry)
    assert initialisations(runtime) == [] and runtime.wallet.weekly_credit == 240  # inchangé en attendant
    hass.states.async_set(ed[1], "18", {"notes": NOTES})  # la source devient prête
    await advance(hass, freezer, minutes=5)
    assert len(initialisations(runtime)) == 1 and runtime.wallet.weekly_credit == 228


# --- Nouvelles tentatives ----------------------------------------------------------------------------

def preload_due(hass_storage, entry, entity):
    """Portefeuille déjà activé sur `entity`, dont le dernier bilan date du lundi 26/10."""
    key = f"{DOMAIN}.{entry.entry_id}"
    wallet = Wallet(weekly_credit=240, notes_capital=0, last_settlement=datetime(2026, 10, 26))
    hass_storage[key] = {"version": 1, "minor_version": 1, "key": key,
                         "data": {**wallet.to_dict(), "source_entity": entity}}


@pytest.mark.requirement("ha-integration/Source de moyennes et de notes")
async def test_nouvelle_tentative_apres_5_minutes(hass, hass_storage, freezer, ed):
    entry = make_entry(options={"notes_entity": ed[1]})
    entry.add_to_hass(hass)
    preload_due(hass_storage, entry, ed[1])
    hass.states.async_set(ed[1], "unavailable", {})
    runtime = await start(hass, freezer, entry, MONDAY_2)
    assert runtime.wallet.last_settlement == datetime(2026, 10, 26)  # bilan reporté
    hass.states.async_set(ed[1], "18", {"notes": NOTES})
    await advance(hass, freezer, minutes=5)
    assert runtime.wallet.last_settlement == datetime(2026, 11, 2)


@pytest.mark.requirement("ha-integration/Source de moyennes et de notes")
async def test_tentatives_epuisees_attente_du_declencheur_quotidien(hass, hass_storage, freezer, ed):
    entry = make_entry(options={"notes_entity": ed[1]})
    entry.add_to_hass(hass)
    preload_due(hass_storage, entry, ed[1])
    down = AsyncMock(side_effect=SourceUnavailableError("hors service"))
    with patch.object(EcoleDirecteSource, "async_fetch", down), patch.object(
        WalletRuntime, "async_schedule_forecast"  # la prévision lit aussi la source : on ne compte que les bilans
    ):
        runtime = await start(hass, freezer, entry, MONDAY_2)
        assert down.await_count == 1  # tentative au démarrage
        for _ in range(3):
            await advance(hass, freezer, minutes=5)
        assert down.await_count == 4  # 3 nouvelles tentatives
        await advance(hass, freezer, minutes=5)
        await advance(hass, freezer, minutes=5)
        assert down.await_count == 4  # plus rien avant le déclencheur quotidien
        await advance(hass, freezer, days=1)  # 00h00 : le compteur repart
        assert down.await_count >= 5
    assert runtime.wallet.last_settlement == datetime(2026, 10, 26)


@pytest.mark.requirement("ha-integration/Source de moyennes et de notes")
async def test_source_ecole_directe_alimente_le_bilan(hass, freezer, entry, ed):
    runtime = await start(hass, freezer, entry)
    await save_params(hass, entry, notes_entity=ed[1])
    runtime = entry.runtime_data
    hass.states.async_set(ed[1], "19", {"notes": [*NOTES, {
        "date": "2026-11-05", "matiere": "MATHEMATIQUES", "commentaire": "Contrôle", "note": "20",
        "sur": "20", "coefficient": "1", "non_significatif": False}]})
    await advance(hass, freezer, days=5, hours=14)
    assert [m.capital_change for m in runtime.wallet.movements if m.kind == "bilan"] == [720]  # un seul 20/20


# --- Source indisponible signalée ------------------------------------------------------------------------

async def due_with_source_down(hass, hass_storage, freezer, ed, steps=None):
    entry = make_entry(options={"notes_entity": ed[1]})
    entry.add_to_hass(hass)
    preload_due(hass_storage, entry, ed[1])
    hass.states.async_set(ed[1], "unavailable", {})
    return entry


@pytest.mark.requirement("ha-integration/Source indisponible signalée")
async def test_premier_echec_notifie(hass, hass_storage, freezer, ed):
    hass.config.language = "fr"
    entry = await due_with_source_down(hass, hass_storage, freezer, ed)
    with patch(CREATE) as create:
        await start(hass, freezer, entry, MONDAY_2)
    (title, message), = calls_by_kind(create)["source"]
    assert "source indisponible" in title and ed[1] in message


@pytest.mark.requirement("ha-integration/Source indisponible signalée")
async def test_echecs_repetes_une_seule_notification(hass, hass_storage, freezer, ed):
    entry = await due_with_source_down(hass, hass_storage, freezer, ed)
    with patch(CREATE) as create:
        await start(hass, freezer, entry, MONDAY_2)
        for _ in range(3):
            await advance(hass, freezer, minutes=5)
    ids = {kwargs["notification_id"] for _, kwargs in create.call_args_list}
    assert len(create.call_args_list) == 4 and len(ids) == 1  # mises à jour d'une même notification


@pytest.mark.requirement("ha-integration/Source indisponible signalée")
async def test_notification_supprimee_au_bilan_reussi(hass, hass_storage, freezer, ed):
    entry = await due_with_source_down(hass, hass_storage, freezer, ed)
    with patch(CREATE), patch(DISMISS) as dismiss:
        await start(hass, freezer, entry, MONDAY_2)
        assert not dismiss.called
        hass.states.async_set(ed[1], "18", {"notes": NOTES})
        await advance(hass, freezer, minutes=5)
    assert dismiss.call_args.args[1].endswith("_source")


@pytest.mark.requirement("ha-integration/Source indisponible signalée")
async def test_aucun_bilan_du_aucune_notification(hass, freezer, ed):
    entry = make_entry(options={"notes_entity": ed[1]})
    entry.add_to_hass(hass)
    hass.states.async_set(ed[1], "unavailable", {})
    with patch(CREATE) as create:
        await start(hass, freezer, entry)  # portefeuille neuf : aucun bilan dû
    assert "source" not in calls_by_kind(create)
