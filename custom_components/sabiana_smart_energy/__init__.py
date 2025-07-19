import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .modbus_coordinator import SabianaModbusCoordinator
# from .info_sensor import SabianaInfoCoordinator

_LOGGER = logging.getLogger(__name__)

DOMAIN = "sabiana_energy_smart"
PLATFORMS = ["sensor","number","switch","binary_sensor","select"]
# , "number", "switch", "binary_sensor", "select"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sabiana Energy Smart from a config entry."""
    _LOGGER.debug("Initializing Sabiana integration")

    coordinator = SabianaModbusCoordinator(hass, entry.data)
    await coordinator.async_setup()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # info_coordinator = SabianaInfoCoordinator(hass, entry)
    # info = await info_coordinator._async_update_data()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("Sabiana Energy Smart integration initialized successfully")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator = hass.data[DOMAIN].pop(entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok
