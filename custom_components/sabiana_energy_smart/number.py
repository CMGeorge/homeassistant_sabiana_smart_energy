"""Number platform for Sabiana Smart Energy (writable parameters)."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER, NUMBER_DEFINITIONS, get_device_info


class SabianaNumberEntity(CoordinatorEntity, NumberEntity):
    """Number entity representing a writable Modbus register."""

    def __init__(self, coordinator: CoordinatorEntity, reg: dict, entry: ConfigEntry):
        super().__init__(coordinator)
        self._reg = reg
        self._address = reg["address"]
        self._scale = reg.get("scale", 1.0)
        self._precision = reg.get("precision", 0)

        self._attr_name = reg["name"]
        self._attr_unique_id = f"{entry.entry_id}_{reg['unique_id']}"
        self._attr_native_min_value = reg["min"]
        self._attr_native_max_value = reg["max"]
        # One raw count is the smallest change the device can store.
        self._attr_native_step = self._scale if self._scale < 1 else 1
        self._attr_native_unit_of_measurement = reg["unit"] or None
        self._attr_device_info = DeviceInfo(
            **get_device_info(entry.entry_id, entry.title)
        )

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.get(self._address)
        if raw is None:
            return None

        # Handle signed 16-bit integers for temperature offsets
        # Check if this register expects negative values (min < 0)
        if self._attr_native_min_value < 0:
            # Convert unsigned to signed if necessary (two's complement)
            if raw > 0x7FFF:
                raw = raw - 0x10000

        return round(raw * self._scale, self._precision)

    async def async_set_native_value(self, value: float) -> None:
        """Write the value; raises HomeAssistantError if the write fails."""
        raw_value = round(value / self._scale)

        # Handle signed 16-bit integers for temperature offsets
        # Convert negative values to unsigned representation for Modbus
        if raw_value < 0:
            raw_value = raw_value + 0x10000

        await self.coordinator.async_write_register(self._address, raw_value)
        LOGGER.debug(
            "Wrote value %s (raw %d) to 0x%04X", value, raw_value, self._address
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SabianaNumberEntity] = []

    for reg in NUMBER_DEFINITIONS:
        coordinator.register_address(reg["address"])
        entities.append(SabianaNumberEntity(coordinator, reg, entry))

    async_add_entities(entities)
