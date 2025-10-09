"""Configuration flow for Sabiana Smart Energy integration.

Handles the UI-based setup flow for adding Sabiana devices to Home Assistant.
Users provide connection details (host, port, slave ID) through a form.
"""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

from .const import CONF_SLAVE, DOMAIN


class MyModbusDeviceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sabiana Smart Energy.

    This flow collects the necessary information to connect to a Sabiana device:
    - Name: Friendly name for the device
    - Host: IP address or hostname for Modbus TCP
    - Port: TCP port (default 502)
    - Slave ID: Modbus slave/unit ID (default 1)
    """

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step of user configuration.

        Presents a form to the user and validates input. Prevents duplicate
        entries by checking if a device with the same host and port already exists.

        Args:
            user_input: Dictionary of user-provided values, or None for initial display

        Returns:
            FlowResult: Either shows the form or creates the config entry
        """
        if user_input is not None:
            existing = [
                entry
                for entry in self._async_current_entries()
                if entry.data[CONF_HOST] == user_input[CONF_HOST]
                and entry.data[CONF_PORT] == user_input[CONF_PORT]
            ]
            if existing:
                return self.async_abort(reason="already_configured")
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default="Sabiana HRV"): str,
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=502): int,
                    vol.Required(CONF_SLAVE, default=1): int,
                }
            ),
        )
