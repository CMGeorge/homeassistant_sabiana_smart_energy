from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, REGISTER_DEFINITIONS

_LOGGER = logging.getLogger(__name__)

class SabianaSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, props: dict, entry_id: str):
        super().__init__(coordinator)
        self._attr_name = props["name"]
        self._attr_unique_id = f"sabiana_switch_{props['key']}"
        self._address = props["address"]
        self._bit = props.get("bit")
        self._key = props["key"]
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Sabiana RVU",
            manufacturer="Sabiana",
            model="Smart Pro"
        )

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get(self._key)

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_write_register(self._address, 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_write_register(self._address, 0)
        await self.coordinator.async_request_refresh()

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    switches = [
        SabianaSwitch(coordinator, {**props, "address": address}, entry.entry_id)
        for address, props in REGISTER_DEFINITIONS.items()
        if props.get("type") == "switch"
    ]
    async_add_entities(switches)