from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER, SWITCH_DEFINITIONS, get_device_info



class SabianaSwitch(CoordinatorEntity, SwitchEntity):
    """Modbus-based switch entity for Sabiana."""

    def __init__(self, coordinator, props: dict, entry_id: str):
        super().__init__(coordinator)
        self._address = props["address"]
        self._bit = props.get("bit")
        self._key = props["key"]

        self._attr_name = props["name"]
        self._attr_unique_id = f"sabiana_switch_{self._key}"
        # self._attr_entity_category = EntityCategory.CONFIG
        self._attr_device_info = DeviceInfo(**get_device_info(entry_id))

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get(self._address)
        if raw is None:
            return None

        if self._bit is not None:
            return bool((raw >> self._bit) & 1)
        return bool(raw)

    async def async_turn_on(self, **kwargs):
        try:
            ok = await self.coordinator.async_write_register(self._address, 1)
            if ok:
                LOGGER.debug("Wrote value 1 to 0x%04X", self._address)
        except Exception as err:
            LOGGER.error(
                "Failed to turn ON %s at 0x%04X: %s", self.name, self._address, err
            )

    async def async_turn_off(self, **kwargs):
        try:
            ok = await self.coordinator.async_write_register(self._address, 0)
            if ok:
                LOGGER.debug("Wrote value 0 to 0x%04X", self._address)
        except Exception as err:
            LOGGER.error(
                "Failed to turn OFF %s at 0x%04X: %s", self.name, self._address, err
            )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    switches = []

    for address, props in SWITCH_DEFINITIONS.items():
        if props.get("entity_type") == "switch":
            coordinator.register_address(address)
            switches.append(
                SabianaSwitch(
                    coordinator, {**props, "address": address}, entry.entry_id
                )
            )

    LOGGER.debug("Adding %d switches", len(switches))
    async_add_entities(switches)
