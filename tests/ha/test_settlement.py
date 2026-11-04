"""Source, bilan automatique, notifications et rapport hebdomadaire (spec ha-integration)."""

from datetime import datetime
from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed, async_mock_service

from custom_components.screen_time_wallet.const import DOMAIN
from custom_components.screen_time_wallet.engine.grades import Grade
from custom_components.screen_time_wallet.engine.wallet import Wallet
from custom_components.screen_time_wallet.source import SourceData

from conftest import make_entry

SEVEN = {
    "ANGLAIS LV1": "13.85", "ARTS PLASTIQUES": "17", "EDUCATION MUSICALE": "16",
    "ENS.INTEG.SC.&TECHNO": "18", "FRANCAIS": "10.67", "HISTOIRE-GEOGRAPHIE": "17.43",
    "MATHEMATIQUES": "19.34", "ED PHYSIQUE & SPORT": "",
}
CREATE = "custom_components.screen_time_wallet.runtime.persistent_notification.async_create"
WEDNESDAY = "2026-11-04 10:00:00+00:00"
MONDAY_9 = "2026-11-09 00:00:05+00:00"


def note(subject, value, scale=20, coefficient=1, comment="contrôle"):
    return Grade("2026-11-05", subject, comment, value, scale, coefficient)


AP_FR = [note("ARTS PLASTIQUES", 9, 10, "0,5", "Lotoportrait"), note("FRANCAIS", 7, comment="Sommative")]


class FakeSource:
    def __init__(self, averages=None, notes=(), error=None):
        self.data, self.error = SourceData(averages or {}, list(notes)), error

    async def async_fetch(self):
        if self.error:
            raise self.error
        return self.data


async def tick(hass, freezer, when):
    freezer.move_to(when)
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()


async def start(hass, freezer, entry, when=WEDNESDAY, source=None):
    freezer.move_to(when)
    assert await hass.config_entries.async_setup(entry.entry_id)
    if source:
        entry.runtime_data.source = source
    return entry.runtime_data


def preload(hass_storage, entry, last_settlement):
    key = f"{DOMAIN}.{entry.entry_id}"
    wallet = Wallet(weekly_credit=240, notes_capital=0, last_settlement=last_settlement)
    hass_storage[key] = {"version": 1, "minor_version": 1, "key": key, "data": wallet.to_dict()}


def calls_by_kind(mock):
    out = {}
    for args, kwargs in mock.call_args_list:
        out.setdefault(kwargs["notification_id"].rsplit("_", 1)[1], []).append((kwargs["title"], args[1]))
    return out


# --- Source de moyennes et de notes -------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Source de moyennes et de notes")
async def test_sans_source_credit_de_repli(hass, freezer, entry):
    runtime = await start(hass, freezer, entry)
    await tick(hass, freezer, MONDAY_9)
    assert (runtime.wallet.weekly_credit, runtime.wallet.notes_capital) == (240, 0)
    assert runtime.wallet.last_settlement == datetime(2026, 11, 9)


@pytest.mark.requirement("ha-integration/Source de moyennes et de notes")
async def test_source_disponible(hass, freezer, entry):
    runtime = await start(hass, freezer, entry, source=FakeSource(SEVEN, AP_FR))
    await tick(hass, freezer, MONDAY_9)
    assert (runtime.wallet.weekly_credit, runtime.wallet.notes_capital) == (228, -374)


@pytest.mark.requirement("ha-integration/Source de moyennes et de notes")
async def test_source_en_erreur_bilan_reporte_puis_retente(hass, freezer, entry):
    runtime = await start(hass, freezer, entry, source=FakeSource(error=RuntimeError("hors service")))
    await tick(hass, freezer, MONDAY_9)
    assert runtime.wallet.last_settlement == datetime(2026, 11, 2)  # rien n'a changé
    assert (runtime.wallet.weekly_credit, runtime.wallet.notes_capital) == (240, 0)
    runtime.source = FakeSource(SEVEN, AP_FR)  # la source revient
    await tick(hass, freezer, "2026-11-10 00:00:05+00:00")  # déclenchement suivant
    assert runtime.wallet.last_settlement == datetime(2026, 11, 9)
    assert runtime.wallet.notes_capital == -374


# --- Bilan automatique du lundi ------------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Bilan automatique du lundi")
async def test_lundi_a_minuit_bilan_et_enregistrement(hass, hass_storage, freezer, entry):
    await start(hass, freezer, entry, source=FakeSource(SEVEN, AP_FR))
    await tick(hass, freezer, "2026-11-09 00:00:00+00:00")
    stored = hass_storage[f"{DOMAIN}.{entry.entry_id}"]["data"]
    assert stored["last_settlement"].startswith("2026-11-09") and stored["notes_capital"] == -374


@pytest.mark.requirement("ha-integration/Bilan automatique du lundi")
async def test_autre_jour_aucun_bilan(hass, freezer, entry):
    runtime = await start(hass, freezer, entry, source=FakeSource(SEVEN, AP_FR))
    await tick(hass, freezer, "2026-11-05 00:00:05+00:00")  # jeudi
    assert runtime.wallet.last_settlement == datetime(2026, 11, 2)
    assert runtime.wallet.notes_capital == 0


@pytest.mark.requirement("ha-integration/Bilan automatique du lundi")
async def test_lundis_manques_pendant_un_arret(hass, hass_storage, freezer):
    entry = make_entry()
    entry.add_to_hass(hass)
    preload(hass_storage, entry, datetime(2026, 10, 19))  # arrêt depuis le 19/10
    runtime = await start(hass, freezer, entry, when="2026-11-02 08:00:00+00:00")
    assert runtime.wallet.last_settlement == datetime(2026, 11, 2)
    assert [m.kind for m in runtime.wallet.movements] == ["bilan", "bilan"]  # 26/10 et 02/11


# --- Notifications -----------------------------------------------------------------------------------------

UNKNOWN = [note("TECHNOLOGIE", 5)]
REJECTED = [note("FRANCAIS", 22, comment="invalide")]


@pytest.mark.requirement("ha-integration/Notifications")
async def test_matiere_inconnue_notifiee(hass, freezer, entry):
    await start(hass, freezer, entry, source=FakeSource(SEVEN, UNKNOWN))
    with patch(CREATE) as create:
        await tick(hass, freezer, MONDAY_9)
    (title, message), = calls_by_kind(create)["anomalies"]
    assert "TECHNOLOGIE" in message and "options" in message


@pytest.mark.requirement("ha-integration/Notifications")
async def test_note_rejetee_notifiee_avec_le_motif(hass, freezer, entry):
    await start(hass, freezer, entry, source=FakeSource(SEVEN, REJECTED))
    with patch(CREATE) as create:
        await tick(hass, freezer, MONDAY_9)
    (_, message), = calls_by_kind(create)["anomalies"]
    assert "FRANCAIS 22/20" in message and "hors du barème" in message


@pytest.mark.requirement("ha-integration/Notifications")
async def test_service_de_notification_configure(hass, freezer):
    entry = make_entry(options={"notify_service": "notify.mobile_app_telephone"})
    entry.add_to_hass(hass)
    sent = async_mock_service(hass, "notify", "mobile_app_telephone")
    await start(hass, freezer, entry, source=FakeSource(SEVEN, UNKNOWN))
    with patch(CREATE) as create:
        await tick(hass, freezer, MONDAY_9)
    persistent = {message for kinds in calls_by_kind(create).values() for _, message in kinds}
    assert {call.data["message"] for call in sent} == persistent  # anomalie et rapport


@pytest.mark.requirement("ha-integration/Notifications")
async def test_aucune_anomalie_aucune_notification_d_anomalie(hass, freezer, entry):
    await start(hass, freezer, entry, source=FakeSource(SEVEN, AP_FR))
    with patch(CREATE) as create:
        await tick(hass, freezer, MONDAY_9)
    assert "anomalies" not in calls_by_kind(create)


# --- Rapport hebdomadaire ---------------------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Rapport hebdomadaire")
async def test_contenu_du_rapport(hass, freezer, entry):
    hass.config.language = "fr"
    await start(hass, freezer, entry, source=FakeSource(SEVEN, AP_FR))
    with patch(CREATE) as create:
        await tick(hass, freezer, MONDAY_9)
    (title, message), = calls_by_kind(create)["report"]
    assert "Mael" in title and "Lundi 09/11/2026" in message
    for expected in (
        "Crédit initial : 228 min (moyenne générale 15,80 sur 7 matières)",
        "poids total 3,25", "ARTS PLASTIQUES : 18/20 (poids 0,25)", "FRANCAIS : 7/20 (poids 3)",
        "Moyenne de la semaine : 7,85", "Crédit de semaine : -374 min",
        "Capital notes : -374 min · Temps disponible : -146 min",
    ):
        assert expected in message


@pytest.mark.requirement("ha-integration/Rapport hebdomadaire")
async def test_semaine_sans_note(hass, freezer, entry):
    hass.config.language = "fr"
    await start(hass, freezer, entry, source=FakeSource(SEVEN, []))
    with patch(CREATE) as create:
        await tick(hass, freezer, MONDAY_9)
    (_, message), = calls_by_kind(create)["report"]
    assert "Aucune note cette semaine" in message and "Crédit de semaine : +342 min" in message


@pytest.mark.requirement("ha-integration/Rapport hebdomadaire")
async def test_credit_de_repli_dans_le_rapport(hass, freezer, entry):
    hass.config.language = "fr"
    await start(hass, freezer, entry)  # sans source
    with patch(CREATE) as create:
        await tick(hass, freezer, MONDAY_9)
    (_, message), = calls_by_kind(create)["report"]
    assert "crédit de repli" in message and "Crédit de semaine : 0 min" in message


@pytest.mark.requirement("ha-integration/Rapport hebdomadaire")
async def test_lundis_manques_un_seul_message(hass, hass_storage, freezer):
    hass.config.language = "fr"
    entry = make_entry()
    entry.add_to_hass(hass)
    preload(hass_storage, entry, datetime(2026, 10, 12))  # 19/10, 26/10 et 02/11 à rattraper
    with patch(CREATE) as create:
        await start(hass, freezer, entry, when="2026-11-02 08:00:00+00:00")
        await hass.async_block_till_done()
    (_, message), = calls_by_kind(create)["report"]
    assert message.count("Lundi ") == 3


@pytest.mark.requirement("ha-integration/Rapport hebdomadaire")
async def test_rapport_envoye_au_service_de_notification(hass, freezer):
    entry = make_entry(options={"notify_service": "notify.mobile_app_telephone"})
    entry.add_to_hass(hass)
    sent = async_mock_service(hass, "notify", "mobile_app_telephone")
    await start(hass, freezer, entry, source=FakeSource(SEVEN, AP_FR))
    with patch(CREATE) as create:
        await tick(hass, freezer, MONDAY_9)
    (_, report), = calls_by_kind(create)["report"]
    assert [call.data["message"] for call in sent] == [report]


@pytest.mark.requirement("ha-integration/Rapport hebdomadaire")
async def test_rapport_desactive_anomalies_conservees(hass, freezer):
    entry = make_entry(options={"weekly_report": False})
    entry.add_to_hass(hass)
    await start(hass, freezer, entry, source=FakeSource(SEVEN, UNKNOWN))
    with patch(CREATE) as create:
        await tick(hass, freezer, MONDAY_9)
    kinds = calls_by_kind(create)
    assert "report" not in kinds and "anomalies" in kinds
