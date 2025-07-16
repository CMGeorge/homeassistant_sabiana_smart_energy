from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up integration from YAML (not supported)."""
    _LOGGER.debug("Nothing special here")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from config entry."""
    _LOGGER.debug("Setting up Sabaiana Entry: %s", entry.title)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward to sensor platform
    # hass.async_create_task(
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor","binary_sensor"])
    # )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""

    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    unload_binary = await hass.config_entries.async_forward_entry_unload(entry, "binary_sensor")
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
