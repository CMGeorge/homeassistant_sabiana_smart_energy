from __future__ import annotations
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, SELECT_DEFINITIONS, LOGGER, get_device_info

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    selects = []

    for addr, reg in SELECT_DEFINITIONS.items():
        if reg.get("options") and reg.get("writable") and (not reg.get("entity_type") == "switch" and not reg.get("entity_type") == "button"):
            coordinator.register_address(addr)
            selects.append(
                SabianaModbusSelect(
                    coordinator=coordinator,
                    reg=reg,
                    address=addr,
                    entry_id=entry.entry_id,
                )
            )

    LOGGER.debug("Adding %d Modbus select entities", len(selects))
    async_add_entities(selects)


class SabianaModbusSelect(CoordinatorEntity, SelectEntity):
    """Select entity that maps values from Modbus register options."""

    def __init__(
        self,
        coordinator: CoordinatorEntity,
        reg: dict[str, Any],
        address: int,
        entry_id: str,
    ):
        super().__init__(coordinator)
        self._address = address
        self._options_map = reg["options"]
        self._reverse_map = {v: k for k, v in self._options_map.items()}

        self._attr_name = reg["name"]
        self._attr_unique_id = f"sabiana_select_{reg['key']}"
        self._attr_options = list(self._reverse_map.keys())
        self._attr_device_info = DeviceInfo(**get_device_info(entry_id))

        LOGGER.debug(
            "Initialized select '%s' with options: %s",
            self.name,
            self._attr_options,
        )

    @property
    def current_option(self) -> str | None:
        raw = self.coordinator.data.get(self._address)
        if raw is None:
            LOGGER.debug("No data at 0x%04X for select %s", self._address, self.name)
            return None

        val = raw[0] if isinstance(raw, list) else raw
        label = self._options_map.get(val)
        LOGGER.debug("%s: raw=%s → mapped='%s'", self.name, val, label)
        return label

    async def async_select_option(self, option: str) -> None:
        if option not in self._reverse_map:
            LOGGER.warning("Invalid selection '%s' for %s", option, self.name)
            return

        value = self._reverse_map[option]
        try:
            ok = await self.coordinator.async_write_register(self._address, value)
            if ok:
                LOGGER.debug("Wrote value %d to 0x%04X for option '%s'", value, self._address, option)
        except Exception as err:
            LOGGER.error("Failed to write option '%s' → 0x%04X: %s", option, self._address, err)
