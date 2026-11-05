"""Boutons « Ajouter du temps » et « Retirer du temps » (mêmes effets que les actions adjust et consume)."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import WalletConfigEntry
from .engine.wallet import InvalidAdjustmentError, InvalidConsumptionError
from .entity import wallet_device_info, wallet_unique_id
from .report import button_reason
from .runtime import WalletRuntime


@dataclass(frozen=True, kw_only=True)
class WalletButtonDescription(ButtonEntityDescription):
    press_fn: Callable[[WalletRuntime, int, str], Awaitable[None]]


DESCRIPTIONS = (
    WalletButtonDescription(
        key="add_time", translation_key="add_time", press_fn=lambda runtime, minutes, reason: runtime.async_adjust(minutes, reason)
    ),
    WalletButtonDescription(
        key="remove_time", translation_key="remove_time", press_fn=lambda runtime, minutes, reason: runtime.async_consume(minutes, reason)
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: WalletConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(WalletButton(entry.runtime_data, description) for description in DESCRIPTIONS)


class WalletButton(ButtonEntity):
    _attr_has_entity_name = True
    entity_description: WalletButtonDescription

    def __init__(self, runtime: WalletRuntime, description: WalletButtonDescription) -> None:
        self.runtime = runtime
        self.entity_description = description
        self._attr_unique_id = wallet_unique_id(runtime, description.key)
        self._attr_device_info = wallet_device_info(runtime)

    async def async_press(self) -> None:
        reason = button_reason(self.hass.config.language)
        try:
            await self.entity_description.press_fn(self.runtime, self.runtime.control_minutes, reason)
        except (InvalidAdjustmentError, InvalidConsumptionError) as error:
            raise ServiceValidationError(str(error)) from error
