"""Options modifiables et table des matières (spec ha-integration)."""

from fractions import Fraction

import pytest
from homeassistant.data_entry_flow import FlowResultType, InvalidData

from custom_components.screen_time_wallet.const import DOMAIN, OPT_MULTIPLIERS
from custom_components.screen_time_wallet.engine.config import Config
from custom_components.screen_time_wallet.options import DEFAULT_OPTIONS, build_config

PARAMS = {
    "max_hours": 20, "notes_share_percent": 60, "pivot": 12, "min_weight": 3, "min_subjects": 4,
    "fallback_credit": 240, "exclude_non_significant": False, "weekly_report": True, "notify_service": "",
}


async def open_step(hass, entry, step):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    return await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": step})


async def save_params(hass, entry, **changes):
    form = await open_step(hass, entry, "parametres")
    assert form["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(form["flow_id"], {**PARAMS, **changes})
    await hass.async_block_till_done()
    return result


async def edit_subject(hass, entry, subject, multiplier=1, remove=False):
    form = await open_step(hass, entry, "matieres")
    result = await hass.config_entries.options.async_configure(
        form["flow_id"], {"subject": subject, "multiplier": multiplier, "remove": remove}
    )
    await hass.async_block_till_done()
    return result


@pytest.fixture
async def loaded(hass, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    return entry


def config_of(entry):
    return entry.runtime_data.wallet.config


# --- Options modifiables dans l'interface -----------------------------------------------------

@pytest.mark.requirement("ha-integration/Options modifiables dans l'interface")
def test_conversion_heures_en_minutes():
    assert build_config({"max_hours": 10}).max_weekly_minutes == 600


@pytest.mark.requirement("ha-integration/Options modifiables dans l'interface")
def test_conversion_pourcentage_en_fraction():
    assert build_config({"notes_share_percent": 70}).notes_share == Fraction(7, 10)


@pytest.mark.requirement("ha-integration/Options modifiables dans l'interface")
async def test_temps_maximal_en_heures_via_l_interface(hass, loaded):
    result = await save_params(hass, loaded, max_hours=10)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_of(loaded).max_weekly_minutes == 600


@pytest.mark.requirement("ha-integration/Options modifiables dans l'interface")
async def test_part_des_notes_en_pourcentage_via_l_interface(hass, loaded):
    await save_params(hass, loaded, notes_share_percent=70)
    assert config_of(loaded).notes_share == Fraction(7, 10)


@pytest.mark.requirement("ha-integration/Options modifiables dans l'interface")
async def test_pivot_incoherent_refuse(hass, loaded):
    result = await save_params(hass, loaded, pivot=20)
    assert result["type"] is FlowResultType.FORM and result["errors"] == {"base": "invalid_config"}
    assert config_of(loaded).pivot == 12


@pytest.mark.requirement("ha-integration/Options modifiables dans l'interface")
async def test_part_des_notes_hors_limites_refusee(hass, loaded):
    form = await open_step(hass, loaded, "parametres")
    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(form["flow_id"], {**PARAMS, "notes_share_percent": 120})
    assert config_of(loaded).notes_share == Fraction(3, 5)


@pytest.mark.requirement("ha-integration/Options modifiables dans l'interface")
async def test_service_de_notification_invalide_refuse(hass, loaded):
    result = await save_params(hass, loaded, notify_service="pas un service")
    assert result["errors"] == {"notify_service": "invalid_notify_service"}


@pytest.mark.requirement("ha-integration/Options modifiables dans l'interface")
async def test_etat_conserve_apres_modification(hass, loaded):
    runtime = loaded.runtime_data
    runtime.wallet.notes_capital = 570
    await runtime.async_save()
    await save_params(hass, loaded, max_hours=10)
    assert loaded.runtime_data.wallet.notes_capital == 570


@pytest.mark.requirement("ha-integration/Options modifiables dans l'interface")
async def test_valeurs_par_defaut_affichees(hass, loaded):
    form = await open_step(hass, loaded, "parametres")
    schema = {str(key): key for key in form["data_schema"].schema}
    defaults = {name: key.default() for name, key in schema.items() if name != "notes_entity"}
    assert defaults == PARAMS
    assert schema["notes_entity"].description["suggested_value"] is None  # aucun capteur de notes
    assert DEFAULT_OPTIONS["weekly_report"] is True and DEFAULT_OPTIONS["notify_service"] == ""


# --- Table des matières modifiable -----------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Table des matières modifiable")
async def test_ajout_d_une_matiere(hass, loaded):
    assert not config_of(loaded).is_known("TECHNOLOGIE")
    await edit_subject(hass, loaded, "TECHNOLOGIE", 1)
    assert config_of(loaded).is_known("TECHNOLOGIE")
    assert config_of(loaded).multiplier_for("TECHNOLOGIE") == 1


@pytest.mark.requirement("ha-integration/Table des matières modifiable")
async def test_modification_d_un_multiplicateur(hass, loaded):
    await edit_subject(hass, loaded, "histoire-geographie", 3)  # casse et accents ignorés
    assert config_of(loaded).multiplier_for("HISTOIRE-GEOGRAPHIE") == 3
    assert sum(1 for k in loaded.options[OPT_MULTIPLIERS] if "HISTOIRE" in k) == 1


@pytest.mark.requirement("ha-integration/Table des matières modifiable")
async def test_suppression_d_une_matiere(hass, loaded):
    await edit_subject(hass, loaded, "ED PHYSIQUE & SPORT", remove=True)
    assert not config_of(loaded).is_known("ED PHYSIQUE & SPORT")


@pytest.mark.requirement("ha-integration/Table des matières modifiable")
async def test_table_vide_refusee(hass, loaded):
    only = {**{k: 0.0 for k in Config().subject_multipliers}, "MATHEMATIQUES": 3.0}
    hass.config_entries.async_update_entry(loaded, options={OPT_MULTIPLIERS: only})
    await hass.async_block_till_done()
    result = await edit_subject(hass, loaded, "MATHEMATIQUES", remove=True)
    assert result["type"] is FlowResultType.FORM and result["errors"] == {"base": "empty_table"}


@pytest.mark.requirement("ha-integration/Table des matières modifiable")
async def test_table_par_defaut_preremplie(hass, loaded):
    assert set(config_of(loaded).subject_multipliers) == set(Config().subject_multipliers)


# --- Capteur de notes EcoleDirecte (option) ----------------------------------------------------------

@pytest.mark.requirement("ha-integration/Options modifiables dans l'interface")
async def test_choix_du_capteur_de_notes(hass, loaded):
    hass.states.async_set("sensor.ed_mael_lopez_notes", "0", {"notes": []})
    result = await save_params(hass, loaded, notes_entity="sensor.ed_mael_lopez_notes")
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert loaded.options["notes_entity"] == "sensor.ed_mael_lopez_notes"
    assert loaded.runtime_data.notes_entity == "sensor.ed_mael_lopez_notes"


@pytest.mark.requirement("ha-integration/Options modifiables dans l'interface")
async def test_capteur_de_notes_inexistant_refuse(hass, loaded):
    result = await save_params(hass, loaded, notes_entity="sensor.n_existe_pas")
    assert result["type"] is FlowResultType.FORM and result["errors"] == {"notes_entity": "unknown_entity"}
    assert loaded.options.get("notes_entity", "") == ""


@pytest.mark.requirement("ha-integration/Options modifiables dans l'interface")
async def test_retour_sans_source_quand_le_capteur_est_vide(hass, loaded):
    hass.states.async_set("sensor.ed_mael_lopez_notes", "0", {"notes": []})
    await save_params(hass, loaded, notes_entity="sensor.ed_mael_lopez_notes")
    await save_params(hass, loaded)  # champ vidé : absent des données reçues
    assert loaded.options["notes_entity"] == "" and loaded.runtime_data.notes_entity == ""
