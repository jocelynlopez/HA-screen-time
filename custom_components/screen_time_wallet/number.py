"""Entité numérique « Minutes » : valeur utilisée par les boutons d'ajout et de retrait de temps."""

from homeassistant.components.number import NumberDeviceClass, NumberMode, RestoreNumber
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import WalletConfigEntry
from .const import CONTROL_MINUTES_MAX, CONTROL_MINUTES_MIN, CONTROL_MINUTES_STEP
from .entity import wallet_device_info, wallet_unique_id
from .runtime import WalletRuntime


async def async_setup_entry(
    hass: HomeAssistant, entry: WalletConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([MinutesNumber(entry.runtime_data)])


class MinutesNumber(RestoreNumber):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = "minutes"
    _attr_device_class = NumberDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_native_min_value = CONTROL_MINUTES_MIN
    _attr_native_max_value = CONTROL_MINUTES_MAX
    _attr_native_step = CONTROL_MINUTES_STEP
    _attr_mode = NumberMode.BOX

    def __init__(self, runtime: WalletRuntime) -> None:
        self.runtime = runtime
        self._attr_unique_id = wallet_unique_id(runtime, "minutes")
        self._attr_device_info = wallet_device_info(runtime)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_number_data()
        if last is not None and last.native_value is not None:
            self.runtime.control_minutes = int(last.native_value)

    @property
    def native_value(self) -> float:
        return self.runtime.control_minutes

    async def async_set_native_value(self, value: float) -> None:
        self.runtime.control_minutes = int(value)
        self.async_write_ha_state()
