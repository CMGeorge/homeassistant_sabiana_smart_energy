from __future__ import annotations
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.components.button import ButtonEntity

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, BUTTON_DEFINITIONS, LOGGER, get_device_info

class SabianaButton(CoordinatorEntity, ButtonEntity):
    """Modbus-based button entity for Sabiana."""

    def __init__(self, coordinator, props: dict, entry_id: str):
        super().__init__(coordinator)
        self._address = props["address"]
        self._key = props["key"]
        self._attr_name = props["name"]
        self._attr_unique_id = f"sabiana_button_{self._key}"
        self._attr_device_info = DeviceInfo(**get_device_info(entry_id))

    async def async_press(self) -> None:
        try:
            # Write '1' to the register on button press
            await self.coordinator._client.write_register(
                address=self._address,
                value=1,
                slave=self.coordinator._slave
            )
            LOGGER.debug("Button pressed: wrote value 1 to 0x%04X", self._address)
            # Refresh data from coordinator after write
            await self.coordinator.async_request_refresh()
        except Exception as err:
            LOGGER.error("Failed to press button %s at 0x%04X: %s", self.name, self._address, err)
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    buttons = []
    for address, props in BUTTON_DEFINITIONS.items():
        if props.get("entity_type") == "button":
            coordinator.register_address(address)
            buttons.append(
                SabianaButton(coordinator, {**props, "address": address}, entry.entry_id)
            )

    LOGGER.debug("Adding %d buttons", len(buttons))
    async_add_entities(buttons)
