"""Intégration Home Assistant « Portefeuille de minutes » (screen_time_wallet)."""

import logging
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store

from .const import DOMAIN, MAX_REPORTS, STORAGE_VERSION
from .engine.config import ConfigError
from .engine.usage import Baseline
from .engine.wallet import Wallet, WalletStateError
from .options import build_config
from .runtime import WalletRuntime, local_now

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

# Entités créées par la v0.5.0 puis retirées : (domaine, clé de l'identifiant unique)
RETIRED_ENTITIES = (("number", "minutes"), ("button", "add_time"), ("button", "remove_time"))

type WalletConfigEntry = ConfigEntry[WalletRuntime]


async def async_setup_entry(hass: HomeAssistant, entry: WalletConfigEntry) -> bool:
    """Charge le portefeuille de l'entrée : état enregistré, ou portefeuille neuf."""
    try:
        config = build_config(entry.options)
    except ConfigError as error:
        raise ConfigEntryError(f"Options incohérentes : {error}") from error

    store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
    data = await store.async_load()
    is_new = data is None
    if is_new:
        wallet = Wallet.create(local_now(), {}, [], config)
    else:
        try:
            wallet = Wallet.from_dict(data, config)
        except WalletStateError as error:
            _LOGGER.error("État illisible pour %s, entrée non chargée : %s", entry.title, error)
            raise ConfigEntryError(f"État enregistré illisible : {error}") from error

    _remove_retired_entities(hass, entry)
    runtime = WalletRuntime(
        hass, entry, store, wallet, (data or {}).get("source_entity", ""), _load_baselines(data or {}),
        _load_reports(data or {}),
    )
    if is_new:
        await runtime.async_save()
    entry.runtime_data = runtime
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    async def _daily(_now) -> None:
        runtime.reset_retries()
        await runtime.async_refresh()  # le cœur décide s'il y a un lundi à traiter

    entry.async_on_unload(async_track_time_change(hass, _daily, hour=0, minute=0, second=0))
    entry.async_on_unload(runtime.async_cancel_retry)
    entry.async_on_unload(runtime.async_track_usage())
    entry.async_on_unload(runtime.async_track_notes())
    await runtime.async_refresh()  # activation de la source et rattrapage des lundis manqués
    runtime.async_schedule_forecast()
    return True


def _remove_retired_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Supprime du registre les entités des versions précédentes, pour ne pas laisser d'entités indisponibles."""
    registry = er.async_get(hass)
    for domain, key in RETIRED_ENTITIES:
        entity_id = registry.async_get_entity_id(domain, DOMAIN, f"{entry.entry_id}_{key}")
        if entity_id:
            registry.async_remove(entity_id)


def _load_baselines(data: dict) -> dict[str, Baseline]:
    """Relevés de référence enregistrés ; une entrée illisible est ignorée (le capteur repart d'un nouveau relevé)."""
    baselines = {}
    for entity, raw in (data.get("usage_baselines") or {}).items():
        try:
            baselines[entity] = Baseline.from_json(raw)
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            _LOGGER.warning("Relevé de référence illisible pour %s, ignoré", entity)
    return baselines


def _load_reports(data: dict) -> list[dict]:
    """Rapports du lundi enregistrés ; une entrée illisible est ignorée."""
    reports = []
    for raw in data.get("reports") or []:
        try:
            datetime.fromisoformat(raw["monday"])
            reports.append({"monday": raw["monday"], "title": str(raw["title"]), "message": str(raw["message"])})
        except (KeyError, TypeError, ValueError):
            _LOGGER.warning("Rapport enregistré illisible, ignoré")
    return reports[-MAX_REPORTS:]


async def async_unload_entry(hass: HomeAssistant, entry: WalletConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_options_updated(hass: HomeAssistant, entry: WalletConfigEntry) -> None:
    """Recharge l'entrée quand les options changent ; l'état est restauré depuis le stockage.

    Un ajout automatique de matières, déjà pris en compte par le runtime, ne recharge pas l'entrée."""
    if entry.runtime_data.consume_own_options_update():
        return
    await hass.config_entries.async_reload(entry.entry_id)
