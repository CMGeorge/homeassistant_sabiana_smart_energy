from __future__ import annotations

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

from .const import CONF_SLAVE, DOMAIN



class MyModbusDeviceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for My Modbus Device."""

    VERSION = 1

    def __init__(self):
        self._errors = {}

    async def async_step_user(self, user_input=None) -> FlowResult:
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
            errors=self._errors,
        )
