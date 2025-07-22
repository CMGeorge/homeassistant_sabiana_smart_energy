import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    # CONF_IP_ADDRESS,
    # CONF_MODEL,
    # EVENT_HOMEASSISTANT_STOP,
    Platform,
)

from .modbus_coordinator import SabianaModbusCoordinator
from .const import LOGGER
# from .info_sensor import SabianaInfoCoordinator

# _LOGGER = logging.getLogger(__name__)

DOMAIN = "sabiana_energy_smart"

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    # Platform.BUTTON,
    # Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


# PLATFORMS = ["sensor"]
# PLATFORMS = ["sensor","number","switch","binary_sensor","select"]
# , "number", "switch", "binary_sensor", "select"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sabiana Energy Smart from a config entry."""
    LOGGER.debug("Initializing Sabiana integration")

    coordinator = SabianaModbusCoordinator(hass, entry.data)
    await coordinator.async_setup()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # info_coordinator = SabianaInfoCoordinator(hass, entry)
    # info = await info_coordinator._async_update_data()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    LOGGER.info("Sabiana Energy Smart integration initialized successfully")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator = hass.data[DOMAIN].pop(entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok
