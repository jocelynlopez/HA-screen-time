"""Ajout automatique des matières de la source et détection à la demande (spec ha-integration)."""

from unittest.mock import patch

import pytest
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.screen_time_wallet.engine.config import Config
from custom_components.screen_time_wallet.engine.credit import initial_credit

from conftest import make_entry
from ed_helpers import add_all_subjects, add_ed_entry, add_notes, add_subject
from test_options import open_step
from test_settlement import CREATE, MONDAY_9, WEDNESDAY, calls_by_kind, start, tick

NOTE = {"date": "2026-11-05", "matiere": "FRANCAIS", "commentaire": "Sommative", "note": "7",
        "sur": "20", "coefficient": "1", "non_significatif": False}


@pytest.fixture
async def ed(hass):
    entry = add_ed_entry(hass)
    add_all_subjects(hass, entry)
    return entry, add_notes(hass, entry, [NOTE])


def wallet_entry(ed, **options):
    entry = make_entry(options={"notes_entity": ed[1], **options})
    return entry


async def started(hass, freezer, ed, **options):
    entry = wallet_entry(ed, **options)
    entry.add_to_hass(hass)
    return entry, await start(hass, freezer, entry, when=WEDNESDAY)


def table(entry):
    return entry.options["multipliers"]


# --- Ajout automatique des matières ---------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Ajout automatique des matières")
async def test_matiere_detectee_dans_une_moyenne(hass, freezer, ed):
    add_subject(hass, ed[0], "ed_mael_lopez_technologie", "TECHNOLOGIE", "techno", "14")
    entry, runtime = await started(hass, freezer, ed)
    assert table(entry)["TECHNOLOGIE"] == 1
    averages = {"anglais lv1": "13.85", "arts plastiques": "17", "education musicale": "16",
                "ens.integ.sc.&techno": "18", "francais": "10.67", "histoire-geographie": "17.43",
                "mathematiques": "19.34", "TECHNOLOGIE": "14"}
    assert runtime.wallet.weekly_credit == initial_credit(averages, runtime.wallet.config)
    assert runtime.wallet.weekly_credit != initial_credit(averages, Config())  # sans la matière : autre crédit


@pytest.mark.requirement("ha-integration/Ajout automatique des matières")
async def test_matiere_detectee_dans_une_note(hass, freezer, ed):
    notes = add_notes(hass, ed[0], [NOTE, {**NOTE, "matiere": "LATIN", "commentaire": "version"}],
                      object_id="ed_mael_lopez_notes")
    entry, runtime = await started(hass, freezer, (ed[0], notes))
    assert table(entry)["LATIN"] == 1 and runtime.wallet.config.multiplier_for("LATIN") == 1


@pytest.mark.requirement("ha-integration/Ajout automatique des matières")
async def test_note_d_une_matiere_ajoutee_compte_au_bilan(hass, freezer, ed):
    entry, runtime = await started(hass, freezer, ed)
    hass.states.async_set(ed[1], "16", {"notes": [NOTE, {**NOTE, "matiere": "LATIN", "note": "20",
                                                         "commentaire": "version"}]})
    hass.config.language = "fr"
    with patch(CREATE) as create:
        await tick(hass, freezer, MONDAY_9)
    assert table(entry)["LATIN"] == 1
    (_, message), = calls_by_kind(create)["report"]
    assert "LATIN 20/20 : +" in message  # la note de latin à 20/20 compte


@pytest.mark.requirement("ha-integration/Ajout automatique des matières")
async def test_matiere_sans_moyenne(hass, freezer, ed):
    add_subject(hass, ed[0], "ed_mael_lopez_latin", "LATIN", "lat", "unknown")
    entry, runtime = await started(hass, freezer, ed)
    assert table(entry)["LATIN"] == 1


@pytest.mark.requirement("ha-integration/Ajout automatique des matières")
async def test_matiere_existante_inchangee(hass, freezer, ed):
    custom = {"HISTOIRE-GEOGRAPHIE": 2.0, "MUSIQUE": 0.0, "MATHEMATIQUES": 3.0}
    add_subject(hass, ed[0], "ed_mael_lopez_musique", "MUSIQUE", "mus", "12")
    entry, runtime = await started(hass, freezer, ed, multipliers=custom)
    assert table(entry)["MUSIQUE"] == 0 and table(entry)["HISTOIRE-GEOGRAPHIE"] == 2
    assert runtime.wallet.config.multiplier_for("MUSIQUE") == 0


@pytest.mark.requirement("ha-integration/Ajout automatique des matières")
async def test_orthographe_differente_non_dupliquee(hass, freezer, ed):
    add_subject(hass, ed[0], "ed_mael_lopez_techno", "Technologie", "techno", "14")
    entry, _ = await started(hass, freezer, ed, multipliers={"TECHNOLOGIE": 2.0, "FRANCAIS": 3.0})
    assert "Technologie" not in table(entry) and table(entry)["TECHNOLOGIE"] == 2


@pytest.mark.requirement("ha-integration/Ajout automatique des matières")
async def test_matiere_modifiable_ensuite(hass, freezer, ed):
    add_subject(hass, ed[0], "ed_mael_lopez_technologie", "TECHNOLOGIE", "techno", "14")
    entry, runtime = await started(hass, freezer, ed)
    form = await open_step(hass, entry, "matieres")
    await hass.config_entries.options.async_configure(
        form["flow_id"], {"subject": "TECHNOLOGIE", "multiplier": 2, "remove": False}
    )
    await hass.async_block_till_done()
    assert entry.runtime_data.wallet.config.multiplier_for("TECHNOLOGIE") == 2


@pytest.mark.requirement("ha-integration/Ajout automatique des matières")
async def test_notification_a_l_ajout(hass, freezer, ed):
    add_subject(hass, ed[0], "ed_mael_lopez_technologie", "TECHNOLOGIE", "techno", "14")
    add_subject(hass, ed[0], "ed_mael_lopez_latin", "LATIN", "lat", "unknown")
    hass.config.language = "fr"
    sent = async_mock_service(hass, "notify", "mobile_app_telephone")
    entry = wallet_entry(ed, notify_service="notify.mobile_app_telephone")
    entry.add_to_hass(hass)
    with patch(CREATE) as create:
        await start(hass, freezer, entry, when=WEDNESDAY)
    (title, message), = calls_by_kind(create)["subjects"]
    assert "TECHNOLOGIE" in message and "LATIN" in message and "Matières" in message
    assert [call.data["message"] for call in sent] == [message]
    assert "Table des matières :" in message and "- LATIN : 1" in message and "- MATHEMATIQUES : 3" in message


@pytest.mark.requirement("ha-integration/Table des matières visible")
async def test_notification_d_ajout_contient_la_table(hass, freezer, ed):
    add_subject(hass, ed[0], "ed_mael_lopez_technologie", "TECHNOLOGIE", "techno", "14")
    hass.config.language = "fr"
    entry = wallet_entry(ed)
    entry.add_to_hass(hass)
    with patch(CREATE) as create:
        await start(hass, freezer, entry, when=WEDNESDAY)
    (_, message), = calls_by_kind(create)["subjects"]
    assert "- EDUCATION MUSICALE : 0,5" in message and "- TECHNOLOGIE : 1" in message
    table = message.split("Table des matières :")[1]
    assert table.index("EDUCATION MUSICALE") < table.index("MATHEMATIQUES") < table.index("TECHNOLOGIE")


@pytest.mark.requirement("ha-integration/Ajout automatique des matières")
async def test_aucune_matiere_a_ajouter_aucune_notification(hass, freezer, ed):
    entry = wallet_entry(ed)
    entry.add_to_hass(hass)
    with patch(CREATE) as create:
        await start(hass, freezer, entry, when=WEDNESDAY)
    assert "subjects" not in calls_by_kind(create)
    assert "multipliers" not in entry.options  # options inchangées


async def test_ajout_sans_rechargement_de_l_entree(hass, freezer, ed):
    add_subject(hass, ed[0], "ed_mael_lopez_technologie", "TECHNOLOGIE", "techno", "14")
    entry, runtime = await started(hass, freezer, ed)
    await hass.async_block_till_done()
    assert entry.runtime_data is runtime  # même objet d'exécution : pas de rechargement


# --- Table des matières modifiable (suppression, exclusion) ------------------------------------------------

@pytest.mark.requirement("ha-integration/Table des matières modifiable")
async def test_matiere_supprimee_absente_de_la_source_n_est_pas_rajoutee(hass, freezer, ed):
    entry, runtime = await started(hass, freezer, ed, multipliers={"FRANCAIS": 3.0, "LATIN": 1.0})
    form = await open_step(hass, entry, "matieres")
    await hass.config_entries.options.async_configure(
        form["flow_id"], {"subject": "LATIN", "multiplier": 1, "remove": True}
    )
    await hass.async_block_till_done()
    assert "LATIN" not in entry.options["multipliers"]
    await tick(hass, freezer, MONDAY_9)
    assert "LATIN" not in entry.options["multipliers"]


@pytest.mark.requirement("ha-integration/Table des matières modifiable")
async def test_matiere_supprimee_mais_presente_dans_la_source_est_rajoutee(hass, freezer, ed):
    add_subject(hass, ed[0], "ed_mael_lopez_techno", "TECHNOLOGIE", "techno", "14")
    entry, runtime = await started(hass, freezer, ed)
    form = await open_step(hass, entry, "matieres")
    await hass.config_entries.options.async_configure(
        form["flow_id"], {"subject": "TECHNOLOGIE", "multiplier": 1, "remove": True}
    )
    await hass.async_block_till_done()
    assert "TECHNOLOGIE" not in entry.options["multipliers"]
    await tick(hass, freezer, MONDAY_9)
    assert entry.options["multipliers"]["TECHNOLOGIE"] == 1


@pytest.mark.requirement("ha-integration/Table des matières modifiable")
async def test_matiere_exclue_par_le_multiplicateur_zero(hass, freezer, ed):
    add_subject(hass, ed[0], "ed_mael_lopez_techno", "TECHNOLOGIE", "techno", "14")
    entry, runtime = await started(hass, freezer, ed)
    form = await open_step(hass, entry, "matieres")
    await hass.config_entries.options.async_configure(
        form["flow_id"], {"subject": "TECHNOLOGIE", "multiplier": 0, "remove": False}
    )
    await hass.async_block_till_done()
    await tick(hass, freezer, MONDAY_9)
    assert entry.options["multipliers"]["TECHNOLOGIE"] == 0
    assert entry.runtime_data.wallet.config.multiplier_for("TECHNOLOGIE") == 0


# --- Détection à la demande ---------------------------------------------------------------------------------

DETECT = {"subject": "", "multiplier": 1, "remove": False, "detect": True}


async def detect(hass, entry, **changes):
    form = await open_step(hass, entry, "matieres")
    result = await hass.config_entries.options.async_configure(form["flow_id"], {**DETECT, **changes})
    await hass.async_block_till_done()
    return result


@pytest.mark.requirement("ha-integration/Détection des matières à la demande")
async def test_detection_a_la_demande_ajoute_et_affiche(hass, freezer, ed):
    entry, runtime = await started(hass, freezer, ed)
    add_subject(hass, ed[0], "ed_mael_lopez_technologie", "TECHNOLOGIE", "techno", "14")
    credit = runtime.wallet.weekly_credit
    with patch(CREATE) as create:
        result = await detect(hass, entry)
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "subjects_added"
    assert result["description_placeholders"]["subjects"] == "TECHNOLOGIE"
    assert table(entry)["TECHNOLOGIE"] == 1 and entry.runtime_data.wallet.config.multiplier_for("TECHNOLOGIE") == 1
    assert not create.called  # pas de notification persistante
    assert entry.runtime_data is runtime and runtime.wallet.weekly_credit == credit  # ni rechargement ni recalcul


@pytest.mark.requirement("ha-integration/Détection des matières à la demande")
async def test_nom_non_exige_quand_la_case_est_cochee(hass, freezer, ed):
    entry, _ = await started(hass, freezer, ed)
    result = await detect(hass, entry, subject="")
    assert result["type"] is FlowResultType.ABORT


@pytest.mark.requirement("ha-integration/Détection des matières à la demande")
async def test_aucune_matiere_a_ajouter_affichee(hass, freezer, ed):
    entry, _ = await started(hass, freezer, ed)
    before = dict(entry.options)
    result = await detect(hass, entry)
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "no_new_subjects"
    assert dict(entry.options) == before


@pytest.mark.requirement("ha-integration/Détection des matières à la demande")
async def test_source_indisponible_message_et_options_inchangees(hass, freezer, ed):
    entry, _ = await started(hass, freezer, ed)
    before = dict(entry.options)
    hass.states.async_set(ed[1], "unavailable")
    result = await detect(hass, entry)
    assert result["type"] is FlowResultType.FORM and result["errors"] == {"base": "source_unavailable"}
    assert dict(entry.options) == before


@pytest.mark.requirement("ha-integration/Détection des matières à la demande")
async def test_aucune_source_choisie(hass, freezer):
    entry = make_entry()
    entry.add_to_hass(hass)
    await start(hass, freezer, entry)
    result = await detect(hass, entry)
    assert result["type"] is FlowResultType.FORM and result["errors"] == {"base": "no_source"}


@pytest.mark.requirement("ha-integration/Détection des matières à la demande")
async def test_case_decochee_le_nom_reste_obligatoire(hass, freezer, ed):
    entry, _ = await started(hass, freezer, ed)
    result = await detect(hass, entry, detect=False)
    assert result["type"] is FlowResultType.FORM and result["errors"] == {"subject": "subject_required"}


# --- Table des matières visible ----------------------------------------------------------------------------------

async def matieres_form(hass, entry):
    return await open_step(hass, entry, "matieres")


@pytest.mark.requirement("ha-integration/Table des matières visible")
async def test_ecran_des_matieres_affiche_la_table(hass, freezer, ed):
    hass.config.language = "fr"
    entry, _ = await started(hass, freezer, ed)
    form = await matieres_form(hass, entry)
    table = form["description_placeholders"]["table"]
    assert "- EDUCATION MUSICALE : 0,5" in table and "- MATHEMATIQUES : 3" in table
    assert table.index("EDUCATION MUSICALE") < table.index("MATHEMATIQUES")


@pytest.mark.requirement("ha-integration/Table des matières visible")
async def test_table_mise_a_jour_apres_modification(hass, freezer, ed):
    entry, _ = await started(hass, freezer, ed)
    form = await matieres_form(hass, entry)
    await hass.config_entries.options.async_configure(
        form["flow_id"], {"subject": "MATHEMATIQUES", "multiplier": 2, "remove": False, "detect": False}
    )
    await hass.async_block_till_done()
    form = await matieres_form(hass, entry)
    assert "- MATHEMATIQUES : 2" in form["description_placeholders"]["table"]


@pytest.mark.requirement("ha-integration/Table des matières visible")
async def test_detection_avec_ajout_affiche_la_nouvelle_ligne(hass, freezer, ed):
    entry, _ = await started(hass, freezer, ed)
    add_subject(hass, ed[0], "ed_mael_lopez_technologie", "TECHNOLOGIE", "techno", "14")
    result = await detect(hass, entry)
    assert result["description_placeholders"]["subjects"] == "TECHNOLOGIE"
    assert "- TECHNOLOGIE : 1" in result["description_placeholders"]["table"]


@pytest.mark.requirement("ha-integration/Table des matières visible")
async def test_aucune_nouvelle_matiere_rappelle_la_table(hass, freezer, ed):
    entry, _ = await started(hass, freezer, ed)
    result = await detect(hass, entry)
    assert result["reason"] == "no_new_subjects"
    assert "- MATHEMATIQUES : 3" in result["description_placeholders"]["table"]
