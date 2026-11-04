"""Création des entrées et persistance de l'état (spec ha-integration)."""

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.data_entry_flow import FlowResultType

from custom_components.screen_time_wallet.const import DOMAIN

from conftest import make_entry


async def _add(hass, name):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.FORM
    return await hass.config_entries.flow.async_configure(result["flow_id"], {"name": name})


# --- Un portefeuille par entrée de configuration -----------------------------------------------

@pytest.mark.requirement("ha-integration/Un portefeuille par entrée de configuration")
async def test_creation_d_un_portefeuille(hass):
    result = await _add(hass, "Mael")
    assert result["type"] is FlowResultType.CREATE_ENTRY
    (entry,) = hass.config_entries.async_entries(DOMAIN)
    assert entry.state is ConfigEntryState.LOADED
    wallet = entry.runtime_data.wallet
    assert (wallet.weekly_credit, wallet.notes_capital) == (240, 0)


@pytest.mark.requirement("ha-integration/Un portefeuille par entrée de configuration")
@pytest.mark.parametrize("second", ["Mael", " mael ", "MAEL"])
async def test_nom_en_double_refuse(hass, second):
    await _add(hass, "Mael")
    result = await _add(hass, second)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


@pytest.mark.requirement("ha-integration/Un portefeuille par entrée de configuration")
async def test_nom_vide_refuse(hass):
    result = await _add(hass, "   ")
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"name": "name_required"}


@pytest.mark.requirement("ha-integration/Un portefeuille par entrée de configuration")
async def test_deux_enfants_independants(hass):
    await _add(hass, "Mael")
    await _add(hass, "Lena")
    runtimes = {e.title: e.runtime_data for e in hass.config_entries.async_entries(DOMAIN)}
    mael, lena = runtimes["Mael"], runtimes["Lena"]
    await mael.async_consume(60)
    assert mael.wallet.weekly_credit == 180
    assert lena.wallet.weekly_credit == 240


# --- Persistance de l'état -------------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Persistance de l'état")
async def test_redemarrage_restaure_l_etat(hass, hass_storage, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = entry.runtime_data
    runtime.wallet.weekly_credit, runtime.wallet.notes_capital = 128, 100
    await runtime.async_save()
    await hass.config_entries.async_unload(entry.entry_id)

    assert await hass.config_entries.async_setup(entry.entry_id)  # « redémarrage »
    wallet = entry.runtime_data.wallet
    assert (wallet.weekly_credit, wallet.notes_capital) == (128, 100)


@pytest.mark.requirement("ha-integration/Persistance de l'état")
async def test_premier_demarrage_cree_et_enregistre(hass, hass_storage, entry):
    key = f"{DOMAIN}.{entry.entry_id}"
    assert key not in hass_storage
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert hass_storage[key]["data"]["weekly_credit"] == 240


@pytest.mark.requirement("ha-integration/Persistance de l'état")
async def test_stockage_illisible_ne_charge_pas_et_n_ecrase_pas(hass, hass_storage, entry, caplog):
    key = f"{DOMAIN}.{entry.entry_id}"
    bad = {"version": 1, "minor_version": 1, "key": key, "data": {"version": 99}}
    hass_storage[key] = bad
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert hass_storage[key]["data"] == {"version": 99}  # non écrasé
    assert "État illisible" in caplog.text
