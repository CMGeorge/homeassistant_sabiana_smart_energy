"""Switch platform for Sabiana Smart Energy (power on/off)."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER, SWITCH_DEFINITIONS, get_device_info
from .helpers import set_bit


class SabianaSwitch(CoordinatorEntity, SwitchEntity):
    """Modbus-based switch entity for Sabiana."""

    def __init__(self, coordinator, props: dict, entry: ConfigEntry):
        super().__init__(coordinator)
        self._address = props["address"]
        self._bit = props.get("bit")
        self._key = props["key"]

        self._attr_name = props["name"]
        self._attr_unique_id = f"{entry.entry_id}_sabiana_switch_{self._key}"
        # self._attr_entity_category = EntityCategory.CONFIG
        self._attr_device_info = DeviceInfo(
            **get_device_info(entry.entry_id, entry.title)
        )

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get(self._address)
        if raw is None:
            return None

        if self._bit is not None:
            return bool((raw >> self._bit) & 1)
        return bool(raw)

    async def _async_write_state(self, on: bool) -> None:
        """Write the switch state; raises HomeAssistantError on failure."""
        if self._bit is None:
            value = 1 if on else 0
        else:
            # Only touch our bit: read the current register value from the
            # device and write it back with the bit changed.
            current = await self.coordinator.async_read_register(self._address)
            value = set_bit(current, self._bit, on)
        await self.coordinator.async_write_register(self._address, value)
        LOGGER.debug("Wrote value %d to 0x%04X", value, self._address)

    async def async_turn_on(self, **kwargs):
        await self._async_write_state(True)

    async def async_turn_off(self, **kwargs):
        await self._async_write_state(False)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    switches = []

    for address, props in SWITCH_DEFINITIONS.items():
        if props.get("entity_type") == "switch":
            coordinator.register_address(address)
            switches.append(
                SabianaSwitch(coordinator, {**props, "address": address}, entry)
            )

    LOGGER.debug("Adding %d switches", len(switches))
    async_add_entities(switches)
