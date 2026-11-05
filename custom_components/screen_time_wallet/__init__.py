"""Intégration Home Assistant « Portefeuille de minutes » (screen_time_wallet)."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_VERSION
from .engine.config import ConfigError
from .engine.usage import Baseline
from .engine.wallet import Wallet, WalletStateError
from .options import build_config
from .runtime import WalletRuntime, local_now

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

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

    runtime = WalletRuntime(
        hass, entry, store, wallet, (data or {}).get("source_entity", ""), _load_baselines(data or {})
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
    await runtime.async_refresh()  # activation de la source et rattrapage des lundis manqués
    return True


def _load_baselines(data: dict) -> dict[str, Baseline]:
    """Relevés de référence enregistrés ; une entrée illisible est ignorée (le capteur repart d'un nouveau relevé)."""
    baselines = {}
    for entity, raw in (data.get("usage_baselines") or {}).items():
        try:
            baselines[entity] = Baseline.from_json(raw)
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            _LOGGER.warning("Relevé de référence illisible pour %s, ignoré", entity)
    return baselines


async def async_unload_entry(hass: HomeAssistant, entry: WalletConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_options_updated(hass: HomeAssistant, entry: WalletConfigEntry) -> None:
    """Recharge l'entrée quand les options changent ; l'état est restauré depuis le stockage."""
    await hass.config_entries.async_reload(entry.entry_id)
