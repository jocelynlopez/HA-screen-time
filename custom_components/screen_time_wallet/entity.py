"""Éléments communs aux entités du portefeuille : appareil de l'enfant et identifiants."""

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .runtime import WalletRuntime


def wallet_device_info(runtime: WalletRuntime) -> DeviceInfo:
    """Appareil de l'enfant, partagé par les capteurs, l'entité numérique et les boutons."""
    return DeviceInfo(
        identifiers={(DOMAIN, runtime.entry.entry_id)}, name=runtime.entry.title, manufacturer="Screen Time Wallet"
    )


def wallet_unique_id(runtime: WalletRuntime, key: str) -> str:
    return f"{runtime.entry.entry_id}_{key}"
