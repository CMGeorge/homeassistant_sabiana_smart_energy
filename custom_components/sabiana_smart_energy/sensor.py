from __future__ import annotations
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_DEFINITIONS_NEW

_LOGGER = logging.getLogger(__name__)

# Build sensor definitions from the new structure
SENSOR_DEFINITIONS = [
    {**reg, "address": addr}
    for addr, reg in SENSOR_DEFINITIONS_NEW.items()
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

    _LOGGER.debug("Adding %d Sabiana sensors", len(sensors))
    for sensor in sensors:
        _LOGGER.debug("  • %s (address: 0x%04X)", sensor.name, sensor._address)

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
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Sabiana RVU",
            manufacturer="Sabiana",
            model="Smart Pro",
        )

        _LOGGER.debug(
            "Initialized sensor %s (unique_id=%s) at address 0x%04X",
            self.name,
            self.unique_id,
            self._address,
        )

    @property
    def native_value(self) -> float | None:
        """Return the scaled value from the coordinator’s data and log it."""
        raw = self.coordinator.data.get(self._address)
        if raw is None:
            _LOGGER.debug(
                "No data for %s at address 0x%04X", self.name, self._address
            )
            return None

        scaled = round(raw * self._scale, self._precision)
        _LOGGER.debug(
            "%s: raw=%s → scaled=%s", self.name, raw, scaled
        )
        return scaled
