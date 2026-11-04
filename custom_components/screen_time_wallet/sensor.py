"""Capteurs du portefeuille et services d'entité (consommation, ajustement)."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

import voluptuous as vol
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import WalletConfigEntry
from .const import DOMAIN
from .engine.wallet import InvalidAdjustmentError, InvalidConsumptionError, Movement, Wallet
from .runtime import WalletRuntime

EXPOSED_MOVEMENTS = 20


@dataclass(frozen=True, kw_only=True)
class WalletSensorDescription(SensorEntityDescription):
    value_fn: Callable[[Wallet], int | datetime | None]


def _last_bilan(wallet: Wallet) -> Movement | None:
    return next((m for m in reversed(wallet.movements) if m.kind == "bilan"), None)


def _last_settlement(wallet: Wallet) -> datetime:
    return wallet.last_settlement.replace(tzinfo=dt_util.get_default_time_zone())


_MINUTES = dict(
    device_class=SensorDeviceClass.DURATION,
    native_unit_of_measurement=UnitOfTime.MINUTES,
    state_class=SensorStateClass.MEASUREMENT,
)

DESCRIPTIONS = (
    WalletSensorDescription(key="available", translation_key="available", value_fn=lambda w: w.available, **_MINUTES),
    WalletSensorDescription(key="weekly_credit", translation_key="weekly_credit", value_fn=lambda w: w.weekly_credit, **_MINUTES),
    WalletSensorDescription(key="notes_capital", translation_key="notes_capital", value_fn=lambda w: w.notes_capital, **_MINUTES),
    WalletSensorDescription(
        key="last_settlement", translation_key="last_settlement",
        device_class=SensorDeviceClass.TIMESTAMP, value_fn=_last_settlement,
    ),
)

CONSUME_SCHEMA = {
    vol.Required("minutes"): vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Optional("reason", default=""): cv.string,
}
ADJUST_SCHEMA = {
    vol.Required("minutes"): vol.All(vol.Coerce(int), vol.NotIn([0])),
    vol.Optional("reason", default=""): cv.string,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: WalletConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runtime = entry.runtime_data
    async_add_entities(WalletSensor(runtime, description) for description in DESCRIPTIONS)

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service("consume", CONSUME_SCHEMA, "async_consume")
    platform.async_register_entity_service("adjust", ADJUST_SCHEMA, "async_adjust")


class WalletSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    entity_description: WalletSensorDescription

    def __init__(self, runtime: WalletRuntime, description: WalletSensorDescription) -> None:
        self.runtime = runtime
        self.entity_description = description
        self._attr_unique_id = f"{runtime.entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, runtime.entry.entry_id)}, name=runtime.entry.title,
            manufacturer="Screen Time Wallet",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(self.hass, self.runtime.signal, self.async_write_ha_state))

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.runtime.wallet)

    @property
    def extra_state_attributes(self) -> dict | None:
        if self.entity_description.key != "last_settlement":
            return None
        wallet = self.runtime.wallet
        last = _last_bilan(wallet)
        detail = last.detail if last else {}
        return {
            "initial_credit": detail.get("initial_credit"),
            "week_credit": detail.get("week_credit"),
            "movements": [m.to_dict() for m in reversed(wallet.movements[-EXPOSED_MOVEMENTS:])],
        }

    async def async_consume(self, minutes: int, reason: str = "") -> None:
        try:
            await self.runtime.async_consume(minutes, reason)
        except InvalidConsumptionError as error:
            raise ServiceValidationError(str(error)) from error

    async def async_adjust(self, minutes: int, reason: str = "") -> None:
        try:
            await self.runtime.async_adjust(minutes, reason)
        except InvalidAdjustmentError as error:
            raise ServiceValidationError(str(error)) from error
