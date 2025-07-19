from __future__ import annotations
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, FIRMWARE_INFO, get_device_info
from .helpers import decode_modbus_value

_LOGGER = logging.getLogger(__name__)

SENSOR_DEFINITIONS = [
    {**reg, "address": addr}
    for addr, reg in FIRMWARE_INFO.items()
    if reg.get("readable")
]

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []

    for definition in SENSOR_DEFINITIONS:
        sensors.append(
            SabianaFirmwareSensor(coordinator._client, definition, entry.entry_id)
        )

    _LOGGER.debug("Adding %d firmware diagnostic sensors", len(sensors))
    async_add_entities(sensors)


class SabianaFirmwareSensor(SensorEntity):
    """Static diagnostic sensor for Sabiana RVU firmware info."""

    def __init__(
        self,
        client: Any,  # SabianaModbusClient
        reg: dict[str, Any],
        entry_id: str,
    ):
        self._client = client
        self._address = reg["address"]
        self._scale = reg.get("scale", 1)
        self._precision = reg.get("precision", 0)
        self._type = reg.get("type", "uns16")
        self._length = reg.get("dataLength", 1)
        self._raw_value: list[int] | None = None

        self._attr_name = reg["name"]
        self._attr_unique_id = f"sabiana_diag_{reg['key']}"
        self._attr_native_unit_of_measurement = reg.get("unit", "")
        self._attr_device_class = reg.get("device_class")
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = DeviceInfo(**get_device_info(entry_id))

    async def async_added_to_hass(self) -> None:
        """Read the value only once when the entity is added."""
        try:
            result = await self._client.read_register(
                address=self._address,
                count=self._length,
                slave=1  # or from config if needed
            )
            self._raw_value = result if isinstance(result, list) else [result]
            _LOGGER.debug(
                "%s read at 0x%04X → %s", self.name, self._address, self._raw_value
            )
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.warning("Failed to read diagnostic sensor %s: %s", self.name, e)

    @property
    def native_value(self) -> str | float | None:
        return decode_modbus_value(
            raw=self._raw_value,
            type_=self._type,
            data_length=self._length,
            scale=self._scale,
            precision=self._precision,
        )
