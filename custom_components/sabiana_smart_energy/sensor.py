from __future__ import annotations
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_DEFINITIONS_NEW, LOGGER, get_device_info


# Build sensor definitions from the new structure
SENSOR_DEFINITIONS = [
    {**reg, "address": addr}
    for addr, reg in SENSOR_DEFINITIONS_NEW.items()
    if not reg.get("entity_type")=="switch"
]

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sabiana Modbus sensors based on config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []
    for definition in SENSOR_DEFINITIONS:
        coordinator.register_address(definition["address"])
        if definition.get("type") == "float32":
            # For float32, we need to register both high and low addresses
            coordinator.register_address(definition["address"] + 1)
        sensors.append(
            SabianaModbusSensor(coordinator, definition, entry.entry_id)
        )
    #     SabianaModbusSensor(coordinator, definition, entry.entry_id)
    #     for definition in SENSOR_DEFINITIONS:
    #     coordinator.register_address(definition["address"])
    #     sensors.append(
    #         SabianaModbusSensor(coordinator, definition, entry.entry_id)
    #     )
    # ]

    LOGGER.debug("Adding %d Sabiana sensors", len(sensors))
    for sensor in sensors:
        LOGGER.debug("  • %s (address: 0x%04X)", sensor.name, sensor._address)

    async_add_entities(sensors)


class SabianaModbusSensor(CoordinatorEntity, SensorEntity):
    """Sensor entity for a Modbus register on the Sabiana device."""

    def __init__(
        self,
        coordinator: CoordinatorEntity,
        reg: dict[str, Any],
        entry_id: str,
    ):
        super().__init__(coordinator)
        self._address = reg["address"]
        self._scale = reg.get("scale", 1)
        self._precision = reg.get("precision", 0)

        self._attr_name = reg["name"]
        self._attr_native_unit_of_measurement = reg.get("unit")
        self._attr_device_class = reg.get("device_class")
        self._attr_unique_id = f"sabiana_sensor_{reg['key']}"
        self._type = reg.get("type", "uint16")
        self._attr_device_info = DeviceInfo(**get_device_info(entry_id))
    

        LOGGER.debug(
            "Initialized sensor %s (unique_id=%s) at address 0x%04X",
            self.name,
            self.unique_id,
            self._address,
        )

    @property
    def native_value(self) -> float | None:
        """Return the scaled value from the coordinator’s data and log it."""
        
        if self._type == "float32":
            raw_hi = self.coordinator.data.get(self._address)
            raw_lo = self.coordinator.data.get(self._address + 1)
            if raw_hi is None or raw_lo is None:
                LOGGER.debug(
                    "No data for %s at addresses 0x%04X/0x%04X", self.name, self._address, self._address + 1
                )
                return None

            import struct
            try:
                combined_bytes = struct.pack(">HH", raw_hi, raw_lo)
                value = struct.unpack(">f", combined_bytes)[0]
            except Exception as e:
                LOGGER.warning("Failed to decode float32 for %s: %s", self.name, e)
                return None

            scaled = round(value, self._precision)
            LOGGER.debug("%s: raw float32=(%s, %s) → %s", self.name, raw_hi, raw_lo, scaled)
            return scaled

        # default UInt16 logic
        raw = self.coordinator.data.get(self._address)
        if raw is None:
            LOGGER.debug(
                "No data for %s at address 0x%04X", self.name, self._address
            )
            return None

        scaled = round(raw * self._scale, self._precision)
        LOGGER.debug("%s: raw=%s → scaled=%s", self.name, raw, scaled)
        return scaled
    # @property
    # def native_value(self) -> float | None:
    #     """Return the scaled value from the coordinator’s data and log it."""
    #     raw = self.coordinator.data.get(self._address)
    #     if raw is None:
    #         LOGGER.debug(
    #             "No data for %s at address 0x%04X", self.name, self._address
    #         )
    #         return None

    #     scaled = round(raw * self._scale, self._precision)
    #     LOGGER.debug(
    #         "%s: raw=%s → scaled=%s", self.name, raw, scaled
    #     )
    #     return scaled
