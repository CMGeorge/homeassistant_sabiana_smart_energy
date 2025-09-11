from __future__ import annotations
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, NUMBER_DEFINITIONS, get_device_info, LOGGER


class SabianaNumberEntity(CoordinatorEntity, NumberEntity):
    """Number entity representing a writable Modbus register."""

    def __init__(self, coordinator: CoordinatorEntity, reg: dict, entry_id: str):
        super().__init__(coordinator)
        self._reg = reg
        self._address = reg["address"]
        self._scale = reg.get("scale", 1.0)
        self._precision = reg.get("precision", 0)

        self._attr_name = reg["name"]
        self._attr_unique_id = reg["unique_id"]
        self._attr_native_min_value = reg["min"]
        self._attr_native_max_value = reg["max"]
        self._attr_native_unit_of_measurement = reg["unit"]
        self._attr_device_info = DeviceInfo(**get_device_info(entry_id))

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.get(self._address)
        if raw is None:
            return None
        return round(raw * self._scale, self._precision)

    async def async_set_native_value(self, value: float) -> None:
        raw_value = round(value / self._scale)
        try:
            await self.coordinator._client.write_register(address = self._address, 
                                                  value = raw_value,
                                                  slave=self.coordinator._slave)
            LOGGER.debug("Wrote value %d to 0x%04X", value, self._address)
            # Refresh coordinator to update state, not need waiting for next update
            await self.coordinator.async_request_refresh()

        except Exception as err:
            LOGGER.error("Failed to write value %s to 0x%04X: %s", value, self._address, err)
            return
        
    
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
        
    for reg in NUMBER_DEFINITIONS:
        coordinator.register_address(reg["address"])
        entities.append(
            SabianaNumberEntity(coordinator, reg, entry.entry_id)
        )
    async_add_entities(entities)
