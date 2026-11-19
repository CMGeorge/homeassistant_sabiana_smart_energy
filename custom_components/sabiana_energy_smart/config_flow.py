"""Configuration flow for Sabiana Smart Energy integration.

Handles the UI-based setup flow for adding Sabiana devices to Home Assistant.
Users provide connection details (host, port, slave ID) through a form.
"""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

from .const import CONF_SLAVE, DOMAIN, LOGGER
from .modbus_client import SabianaModbusClient

# Register read to check that a Sabiana unit answers (T1 temperature probe).
PROBE_ADDRESS = 0x0100

DEFAULT_NAME = "Sabiana HRV"
DEFAULT_PORT = 502
DEFAULT_SLAVE = 1


async def async_validate_connection(host: str, port: int, slave: int) -> bool:
    """Return True if a Modbus device answers at host:port with this slave ID."""
    client = SabianaModbusClient(host, port)
    try:
        result = await client.read_register(PROBE_ADDRESS, count=1, slave=slave)
        return result is not None
    finally:
        await client.close()


def _build_schema(user_input: dict[str, Any] | None) -> vol.Schema:
    defaults = user_input or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(
                CONF_HOST, default=defaults.get(CONF_HOST, vol.UNDEFINED)
            ): str,
            vol.Required(
                CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            vol.Required(
                CONF_SLAVE, default=defaults.get(CONF_SLAVE, DEFAULT_SLAVE)
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=247)),
        }
    )


class MyModbusDeviceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sabiana Smart Energy.

    This flow collects the necessary information to connect to a Sabiana device:
    - Name: Friendly name for the device
    - Host: IP address or hostname for Modbus TCP
    - Port: TCP port (default 502)
    - Slave ID: Modbus slave/unit ID (default 1)
    """

    VERSION = 1
    # 1.2: entity unique IDs are prefixed with the config entry ID
    MINOR_VERSION = 2

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step of user configuration.

        Presents a form to the user and validates input. Prevents duplicate
        entries by checking if a device with the same host and port already exists,
        and checks that the device answers before creating the entry.

        Args:
            user_input: Dictionary of user-provided values, or None for initial display

        Returns:
            FlowResult: Either shows the form or creates the config entry
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            existing = [
                entry
                for entry in self._async_current_entries()
                if entry.data[CONF_HOST] == user_input[CONF_HOST]
                and entry.data[CONF_PORT] == user_input[CONF_PORT]
            ]
            if existing:
                return self.async_abort(reason="already_configured")

            try:
                ok = await async_validate_connection(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_SLAVE],
                )
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected error validating Sabiana connection")
                errors["base"] = "unknown"
            else:
                if ok:
                    return self.async_create_entry(
                        title=user_input[CONF_NAME], data=user_input
                    )
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(user_input),
            errors=errors,
        )
