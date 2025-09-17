from __future__ import annotations
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DIAGNOSTIC_DEFINITIONS, get_device_info

_LOGGER = logging.getLogger(__name__)

INVERSION_FLAG_ADDRESS = 0x0104  # CFG_Inverted


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []

    # Always register the inversion flag address
    coordinator.register_address(INVERSION_FLAG_ADDRESS)

    for addr, reg in DIAGNOSTIC_DEFINITIONS.items():
        entity_category = reg.get("entity_category", None)
        for bit_num, bit_def in reg.get("bits", {}).items():
            coordinator.register_address(addr)
            sensors.append(
                SabianaBinarySensor(
                    coordinator=coordinator,
                    address=addr,
                    bit_num=bit_num,
                    key=bit_def["key"],
                    name=bit_def["name"],
                    entry_id=entry.entry_id,
                    entity_category=entity_category,
                )
            )

    _LOGGER.debug("Adding %d binary sensors with inversion logic", len(sensors))
    async_add_entities(sensors)


class SabianaBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor with support for global inversion flag at 0x0104."""

    def __init__(
        self,
        coordinator: CoordinatorEntity,
        address: int,
        bit_num: int,
        key: str,
        name: str,
        entry_id: str,
        entity_category=None,
    ):
        super().__init__(coordinator)
        self._address = address
        self._bit_num = bit_num

        self._attr_name = name
        self._attr_unique_id = f"sabiana_bin_{key}"
        self._attr_device_info = DeviceInfo(**get_device_info(entry_id))
        self._attr_entity_category = entity_category
        _LOGGER.debug(
            "Initialized binary sensor %s (bit %d @ 0x%04X)", name, bit_num, address
        )

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get(self._address)

        if raw is None:
            _LOGGER.debug("No data at 0x%04X for %s", self._address, self.name)
            return None

        bit_value = bool((raw >> self._bit_num) & 1)

        # ✅ Skip inversion logic if this sensor is the inversion flag itself
        if self._address == INVERSION_FLAG_ADDRESS and self._bit_num == 0:
            _LOGGER.debug(
                "%s: raw=0x%04X → bit[%d]=%s (inversion flag, no flip)",
                self.name,
                raw,
                self._bit_num,
                bit_value,
            )
            return bit_value

        # Apply global inversion if flag is set
        inversion = self.coordinator.data.get(INVERSION_FLAG_ADDRESS)
        if inversion is not None and (inversion & 0x01):
            bit_value = not bit_value
            _LOGGER.debug(
                "%s: raw=0x%04X → bit[%d]=%s (inverted)",
                self.name,
                raw,
                self._bit_num,
                bit_value,
            )
        else:
            _LOGGER.debug(
                "%s: raw=0x%04X → bit[%d]=%s (normal)",
                self.name,
                raw,
                self._bit_num,
                bit_value,
            )

        return bit_value
