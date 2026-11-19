"""Sabiana Smart Energy Integration for Home Assistant.

This integration provides support for Sabiana Smart Energy heat recovery units
via Modbus (TCP/RTU) communication. It enables monitoring and control of:
- Temperature sensors (T1-T4)
- Humidity and CO2 levels
- Fan speeds and operational modes
- Diagnostic information
- Configuration parameters

The integration uses a coordinator pattern for efficient Modbus polling,
registering only the addresses needed by active entities.
"""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN, LOGGER
from .modbus_coordinator import SabianaModbusCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,  # Status flags, alarms, configuration bits
    Platform.NUMBER,  # Writable parameters like setpoints, thresholds
    Platform.SELECT,  # Operating mode, timer program selection
    Platform.SENSOR,  # Temperature, humidity, CO2, pressure readings
    Platform.SWITCH,  # Power on/off control
    Platform.BUTTON,  # Mode activation buttons (Manual, Holiday, Party)
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sabiana Energy Smart from a config entry.

    This function initializes the integration by:
    1. Creating a Modbus coordinator for communication
    2. Establishing connection to the device
    3. Performing initial data fetch
    4. Setting up all platform entities (sensors, switches, etc.)

    Args:
        hass: Home Assistant instance
        entry: Config entry containing connection parameters (host, port, slave ID)

    Returns:
        bool: True if setup was successful
    """
    LOGGER.debug("Initializing Sabiana integration")

    coordinator = SabianaModbusCoordinator(hass, entry.data)
    await coordinator.async_setup()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # The unit only knows hour/minute/weekday (no date, no DST rules), so it
    # never adjusts for daylight saving time by itself. Every 5 minutes compare
    # it with Home Assistant's local time and correct it if it has drifted
    # (only while the "Automatic clock sync" switch is on). Running just after
    # the minute rolls over keeps the written time accurate to a few seconds.
    async def _async_check_clock(now) -> None:
        await coordinator.async_check_clock(now)

    entry.async_on_unload(
        async_track_time_change(hass, _async_check_clock, minute="/5", second=2)
    )

    LOGGER.info("Sabiana Energy Smart integration initialized successfully")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Cleanly shuts down the integration by:
    1. Removing the coordinator from hass.data
    2. Unloading all platform entities
    3. Closing the Modbus connection

    Args:
        hass: Home Assistant instance
        entry: Config entry to unload

    Returns:
        bool: True if unload was successful
    """
    coordinator = hass.data[DOMAIN].pop(entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await coordinator.async_close()
    return unload_ok
