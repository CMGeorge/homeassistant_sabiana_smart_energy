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

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN, LOGGER, get_polled_addresses
from .modbus_coordinator import SabianaModbusCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,  # Status flags, alarms, configuration bits
    Platform.NUMBER,  # Writable parameters like setpoints, thresholds
    Platform.SELECT,  # Operating mode, timer program selection
    Platform.SENSOR,  # Temperature, humidity, CO2, pressure readings
    Platform.SWITCH,  # Power on/off control
    Platform.BUTTON,  # Mode activation buttons (Manual, Holiday, Party)
]

# Unique IDs created before config entry version 1.2 were not scoped to the
# config entry ("sabiana_sensor_probe_temp1"), so two units collided.
LEGACY_UNIQUE_ID_PREFIX = "sabiana_"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sabiana Energy Smart from a config entry.

    This function initializes the integration by:
    1. Creating a Modbus coordinator for communication
    2. Establishing connection to the device (retried by HA if unreachable)
    3. Performing initial data fetch
    4. Setting up all platform entities (sensors, switches, etc.)

    Args:
        hass: Home Assistant instance
        entry: Config entry containing connection parameters (host, port, slave ID)

    Returns:
        bool: True if setup was successful
    """
    LOGGER.debug("Initializing Sabiana integration")

    coordinator = SabianaModbusCoordinator(hass, entry.data, entry)
    addresses, float32_bases = get_polled_addresses()
    for address in addresses:
        coordinator.register_address(address)
    for address in float32_bases:
        coordinator.register_float32(address)

    if not await coordinator.async_setup():
        await coordinator.async_close()
        raise ConfigEntryNotReady(
            f"Cannot connect to Sabiana unit at "
            f"{entry.data['host']}:{entry.data['port']}"
        )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await coordinator.async_close()
        raise

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
    1. Unloading all platform entities
    2. Removing the coordinator from hass.data (only if unload succeeded)
    3. Closing the Modbus connection

    Args:
        hass: Home Assistant instance
        entry: Config entry to unload

    Returns:
        bool: True if unload was successful
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_close()
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries.

    1.1 -> 1.2: prefix entity unique IDs with the config entry ID so several
    units can be configured. Entity IDs, names and history are preserved.
    """
    LOGGER.debug(
        "Migrating config entry %s from version %s.%s",
        entry.entry_id,
        entry.version,
        entry.minor_version,
    )

    if entry.version > 1:
        # Downgraded from a future major version.
        return False

    if entry.version == 1 and entry.minor_version < 2:
        prefix = f"{entry.entry_id}_"

        @callback
        def _migrate_unique_id(
            entity_entry: er.RegistryEntry,
        ) -> dict[str, str] | None:
            unique_id = entity_entry.unique_id
            if unique_id.startswith(LEGACY_UNIQUE_ID_PREFIX):
                return {"new_unique_id": f"{prefix}{unique_id}"}
            return None

        await er.async_migrate_entries(hass, entry.entry_id, _migrate_unique_id)
        hass.config_entries.async_update_entry(entry, version=1, minor_version=2)
        LOGGER.info(
            "Migrated Sabiana entity unique IDs for config entry %s", entry.entry_id
        )

    return True
