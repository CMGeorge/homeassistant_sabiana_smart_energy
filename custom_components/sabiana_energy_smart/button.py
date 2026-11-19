from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BUTTON_DEFINITIONS, DOMAIN, LOGGER, get_device_info


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
            ok = await self.coordinator.async_write_register(self._address, 1)
            if ok:
                LOGGER.debug("Button pressed: wrote value 1 to 0x%04X", self._address)
        except Exception as err:
            LOGGER.error(
                "Failed to press button %s at 0x%04X: %s", self.name, self._address, err
            )


class SabianaSyncClockButton(CoordinatorEntity, ButtonEntity):
    """Set the unit's clock to Home Assistant's local time and weekday."""

    _attr_name = "Sync clock with Home Assistant"
    _attr_unique_id = "sabiana_button_sync_clock"
    _attr_icon = "mdi:clock-check-outline"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(**get_device_info(entry_id))

    async def async_press(self) -> None:
        if not await self.coordinator.async_sync_clock():
            raise HomeAssistantError("Could not write the clock to the Sabiana unit")


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    buttons = []
    for address, props in BUTTON_DEFINITIONS.items():
        if props.get("entity_type") == "button":
            coordinator.register_address(address)
            buttons.append(
                SabianaButton(
                    coordinator, {**props, "address": address}, entry.entry_id
                )
            )

    buttons.append(SabianaSyncClockButton(coordinator, entry.entry_id))

    LOGGER.debug("Adding %d buttons", len(buttons))
    async_add_entities(buttons)
