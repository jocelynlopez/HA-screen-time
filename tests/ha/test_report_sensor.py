"""Capteur « Rapport », historique des rapports du lundi et prévision (spec ha-integration)."""

from datetime import datetime
from unittest.mock import patch

import pytest

from custom_components.screen_time_wallet.const import DOMAIN
from custom_components.screen_time_wallet.source import SourceUnavailableError

from conftest import make_entry
from test_entities import state
from test_settlement import AP_FR, CREATE, MONDAY_9, SEVEN, FakeSource, preload, start, tick


async def settled(hass):
    await hass.async_block_till_done(wait_background_tasks=True)


async def running(hass, freezer, source=None, **options):
    hass.config.language = "fr"
    entry = make_entry(options=options)
    entry.add_to_hass(hass)
    runtime = await start(hass, freezer, entry, source=source)
    runtime.async_schedule_forecast()  # la source de test remplace celle du chargement
    await settled(hass)
    return entry, runtime


def dummy(day):
    return {"monday": datetime(2026, 1, day).isoformat(), "title": "T", "message": f"rapport {day}"}


# --- Capteur Rapport ---------------------------------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Capteur Rapport")
async def test_attributs_disponibles_apres_un_bilan(hass, freezer):
    entry, runtime = await running(hass, freezer, source=FakeSource(SEVEN, AP_FR))
    await tick(hass, freezer, MONDAY_9)
    await settled(hass)
    sensor = state(hass, entry, "report")
    assert sensor.state.startswith("2026-11-09T00:00:00")
    assert "lundi 09/11" in sensor.attributes["last_report"]
    assert "Prévision du lundi 16/11" in sensor.attributes["forecast"]


@pytest.mark.requirement("ha-integration/Capteur Rapport")
async def test_historique_expose_les_douze_rapports_precedents(hass, freezer):
    entry, runtime = await running(hass, freezer)
    runtime.reports = [dummy(day) for day in range(1, 16)]
    runtime.async_notify_entities()
    await settled(hass)
    attributes = state(hass, entry, "report").attributes
    assert attributes["last_report"] == "rapport 15"
    assert attributes["history"] == [f"rapport {day}" for day in range(14, 2, -1)]


@pytest.mark.requirement("ha-integration/Capteur Rapport")
async def test_avant_le_premier_bilan(hass, freezer):
    entry, runtime = await running(hass, freezer)
    sensor = state(hass, entry, "report")
    assert sensor.state == "unknown" and sensor.attributes["last_report"] == "Aucun rapport pour le moment."
    assert sensor.attributes["history"] == []


@pytest.mark.requirement("ha-integration/Capteur Rapport")
async def test_rapport_conserve_sans_notification(hass, freezer):
    entry, runtime = await running(hass, freezer, source=FakeSource(SEVEN, AP_FR), weekly_report=False)
    with patch(CREATE) as create:
        await tick(hass, freezer, MONDAY_9)
        await settled(hass)
    assert not create.called
    assert "lundi 09/11" in state(hass, entry, "report").attributes["last_report"]


# --- Historique des rapports -------------------------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Historique des rapports")
async def test_rapports_apres_redemarrage(hass, freezer):
    entry, runtime = await running(hass, freezer, source=FakeSource(SEVEN, AP_FR))
    await tick(hass, freezer, MONDAY_9)
    await settled(hass)
    before = state(hass, entry, "report").attributes["last_report"]
    assert await hass.config_entries.async_reload(entry.entry_id)
    await settled(hass)
    assert entry.runtime_data.reports == runtime.reports and len(runtime.reports) == 1
    assert state(hass, entry, "report").attributes["last_report"] == before


@pytest.mark.requirement("ha-integration/Historique des rapports")
async def test_lundis_rattrapes_tous_conserves(hass, freezer, hass_storage):
    hass.config.language = "fr"
    entry = make_entry()
    entry.add_to_hass(hass)
    preload(hass_storage, entry, datetime(2026, 10, 19))
    runtime = await start(hass, freezer, entry)  # les lundis 26/10 et 02/11 sont dus
    await settled(hass)
    assert [r["monday"] for r in runtime.reports] == ["2026-10-26T00:00:00", "2026-11-02T00:00:00"]
    assert state(hass, entry, "report").state.startswith("2026-11-02T00:00:00")


@pytest.mark.requirement("ha-integration/Historique des rapports")
async def test_historique_limite_a_52_rapports(hass, freezer):
    entry, runtime = await running(hass, freezer)
    runtime.reports = [dummy(day) for day in range(1, 29)] * 2  # 56 entrées
    runtime.reports = runtime.reports[:52]
    first = runtime.reports[0]
    await tick(hass, freezer, MONDAY_9)
    await settled(hass)
    assert len(runtime.reports) == 52 and runtime.reports[0] != first
    assert runtime.reports[-1]["monday"] == "2026-11-09T00:00:00"


@pytest.mark.requirement("ha-integration/Historique des rapports")
async def test_ancien_etat_sans_historique(hass, freezer, hass_storage):
    entry = make_entry()
    entry.add_to_hass(hass)
    preload(hass_storage, entry, datetime(2026, 11, 2))  # état sans clé « reports »
    runtime = await start(hass, freezer, entry)
    await settled(hass)
    assert runtime.reports == []
    assert state(hass, entry, "report").attributes["last_report"] == "No report yet."


@pytest.mark.requirement("ha-integration/Historique des rapports")
async def test_prevision_non_enregistree(hass, freezer, hass_storage):
    entry, runtime = await running(hass, freezer, source=FakeSource(SEVEN, AP_FR))
    await runtime.async_adjust(30, "devoirs")
    await settled(hass)
    assert "Prévision" in runtime.forecast_text
    saved = hass_storage[f"{DOMAIN}.{entry.entry_id}"]["data"]
    assert "forecast" not in saved and "Prévision" not in str(saved)


# --- Prévision du rapport ----------------------------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Prévision du rapport")
async def test_prevision_mise_a_jour_par_un_mouvement(hass, freezer):
    entry, runtime = await running(hass, freezer, source=FakeSource(SEVEN))
    await runtime.async_adjust(30, "aide aux devoirs")
    await settled(hass)
    forecast = state(hass, entry, "report").attributes["forecast"]
    assert "Si rien ne change d'ici là." in forecast and "+30 min · aide aux devoirs" in forecast
    assert "Temps disponible" in forecast


@pytest.mark.requirement("ha-integration/Prévision du rapport")
async def test_prevision_suit_le_capteur_de_notes(hass, freezer):
    source = FakeSource(SEVEN)
    hass.states.async_set("sensor.notes", "1")
    entry, runtime = await running(hass, freezer, source=source, notes_entity="sensor.notes")
    assert "FRANCAIS" not in runtime.forecast_text and "Complément moyenne générale" in runtime.forecast_text
    source.data = FakeSource(SEVEN, AP_FR).data  # une nouvelle note apparaît dans la source
    hass.states.async_set("sensor.notes", "2")
    await settled(hass)
    assert "FRANCAIS 7/20 : -" in state(hass, entry, "report").attributes["forecast"]


@pytest.mark.requirement("ha-integration/Prévision du rapport")
async def test_prevision_source_inaccessible(hass, freezer):
    source = FakeSource(SEVEN)
    entry, runtime = await running(hass, freezer, source=source)
    source.error = SourceUnavailableError("hors service")
    with patch(CREATE) as create:
        await runtime.async_adjust(-20, "dispute")
        await settled(hass)
    forecast = state(hass, entry, "report").attributes["forecast"]
    assert "Prévision indisponible" in forecast and "-20 min · dispute" in forecast
    assert "Temps disponible" not in forecast and not create.called


@pytest.mark.requirement("ha-integration/Prévision du rapport")
async def test_recalcul_sans_modifier_l_etat(hass, freezer):
    entry, runtime = await running(hass, freezer, source=FakeSource(SEVEN, AP_FR))
    before = runtime.wallet.to_dict()
    runtime.async_schedule_forecast()
    await settled(hass)
    assert runtime.wallet.to_dict() == before and runtime.wallet.last_settlement == datetime(2026, 11, 2)


# --- Action de recomptage des notes -----------------------------------------------------------------------------

async def activated_with_week_notes(hass, freezer):
    """Portefeuille activé avec l'ancienne règle : les notes de la semaine (français, arts) sont mémorisées sans effet."""
    from real_notes import RAW, make

    visible = [make(r) for r in RAW]
    source = FakeSource(SEVEN, visible)
    entry, runtime = await running(hass, freezer, source=source)
    runtime.wallet.seen_keys |= {g.key for g in visible}
    runtime.async_schedule_forecast()
    await settled(hass)
    return entry, runtime, source


async def recount(hass, entry):
    from custom_components.screen_time_wallet.const import DOMAIN as D
    from test_entities import entity_id

    await hass.services.async_call(
        D, "recount_week", {"entity_id": entity_id(hass, entry, "available")}, blocking=True
    )
    await settled(hass)


@pytest.mark.requirement("ha-integration/Action de recomptage des notes")
async def test_recomptage_affiche_les_notes_dans_la_prevision(hass, freezer):
    entry, runtime, _ = await activated_with_week_notes(hass, freezer)
    assert "FRANCAIS 7/20" not in runtime.forecast_text
    await recount(hass, entry)
    forecast = state(hass, entry, "report").attributes["forecast"]
    assert "FRANCAIS 7/20 : -" in forecast and "ARTS PLASTIQUES 18/20 : +" in forecast
    assert "HISTOIRE" not in forecast


@pytest.mark.requirement("ha-integration/Action de recomptage des notes")
async def test_recomptage_source_inaccessible(hass, freezer, hass_storage):
    from homeassistant.exceptions import ServiceValidationError

    entry, runtime, source = await activated_with_week_notes(hass, freezer)
    before = runtime.wallet.to_dict()
    source.error = SourceUnavailableError("hors service")
    with pytest.raises(ServiceValidationError):
        await recount(hass, entry)
    assert runtime.wallet.to_dict() == before


@pytest.mark.requirement("ha-integration/Action de recomptage des notes")
async def test_recomptage_sans_note_concernee(hass, freezer, hass_storage):
    entry, runtime = await running(hass, freezer, source=FakeSource(SEVEN, []))
    saved = dict(hass_storage[f"{DOMAIN}.{entry.entry_id}"]["data"])
    await recount(hass, entry)
    assert hass_storage[f"{DOMAIN}.{entry.entry_id}"]["data"] == saved


@pytest.mark.requirement("ha-integration/Action de recomptage des notes")
async def test_recomptage_ne_modifie_pas_credits_ni_journal(hass, freezer):
    entry, runtime, _ = await activated_with_week_notes(hass, freezer)
    await runtime.async_consume(20, "jeu")
    before = (runtime.wallet.weekly_credit, runtime.wallet.notes_capital, list(runtime.wallet.movements))
    await recount(hass, entry)
    assert (runtime.wallet.weekly_credit, runtime.wallet.notes_capital, runtime.wallet.movements) == before
