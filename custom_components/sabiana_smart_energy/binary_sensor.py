from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from pymodbus.client import ModbusTcpClient

from .const import DOMAIN, CONF_SLAVE

_LOGGER = logging.getLogger(__name__)

# Define diagnostics map: register -> key info
DIAGNOSTIC_DEFINITIONS = {
    0x0104: {
        "type": "uint16",
        "bits": {
            0: {"key": "cfg_inverted", "name": "Config Inverted"},
            1: {"key": "cfg_preheating", "name": "Preheating Present"},
            2: {"key": "cfg_preheating_h2o", "name": "Preheating with Water"},
            3: {"key": "cfg_post_treatment", "name": "Post Treatment ON"},
            4: {"key": "cfg_post_summer", "name": "Post Treatment Summer"},
            5: {"key": "cfg_rl5_iaq", "name": "Relay 5 IAQ or Fault"},
            6: {"key": "cfg_pre_treatment", "name": "Pre Treatment"},
            7: {"key": "cfg_boiler_pboost", "name": "Boiler Pressure Boost"},
            8: {"key": "cfg_post_ext_he", "name": "Post Treatment Ext. HE"},
            9: {"key": "cfg_uart_highspd", "name": "UART High Speed"},
        }
    },
    0x0105: {
        "type": "uint16",
        "bits": {
            0: {"key": "remote_off", "name": "Remote OFF Active"},
            1: {"key": "bypass_active", "name": "Bypass Active"},
            2: {"key": "elec_preheat_active", "name": "Electric Preheater Active"},
            3: {"key": "water_preheat_active", "name": "Water Preheater Active"},
            4: {"key": "boost_active", "name": "Boost Active"},
            5: {"key": "defrost_cycle_active", "name": "Defrost Cycle Active"},
            7: {"key": "party_mode_active", "name": "Party Mode Active"},
            8: {"key": "on_status", "name": "Unit ON"},
            11: {"key": "winter_setting", "name": "Winter Setting"},
        }
    },
    0x0109: {
        "type": "uint8",
        "bits": {
            0: {"key": "relay_iaq_fault", "name": "IAQ Fault Relay ON"},
            1: {"key": "relay_preheat", "name": "Preheat Relay ON"},
            2: {"key": "relay_postheat", "name": "Postheat Relay ON"},
            3: {"key": "relay_fans", "name": "Fans Relay ON"},
            4: {"key": "relay_postcool", "name": "Postcool/Heat2 Relay ON"},
        }
    }
}


class SabianaDiagnosticsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.host = entry.data[CONF_HOST]
        self.port = entry.data[CONF_PORT]
        self.slave = entry.data[CONF_SLAVE]
        self.client = ModbusTcpClient(self.host, port=self.port)

        super().__init__(
            hass,
            _LOGGER,
            name="Sabiana Diagnostics",
            update_interval=timedelta(minutes=5),
        )

    async def _async_update_data(self) -> dict[str, bool | None]:
        """Fetch diagnostic flags (from both uint16 and uint8 registers)."""
        data = {}
        try:
            self.client.connect()
            for address, entry in DIAGNOSTIC_DEFINITIONS.items():
                reg_type = entry.get("type", "uint16")
                bits = entry["bits"]

                result = self.client.read_holding_registers(address=address, count=1, slave=self.slave)
                if result.isError():
                    _LOGGER.warning("Could not read diagnostic register 0x%04X", address)
                    for bit in bits.values():
                        data[bit["key"]] = None
                    continue

                raw_value = result.registers[0]
                value = raw_value & 0xFF if reg_type == "uint8" else raw_value

                for bit_num, bit in bits.items():
                    data[bit["key"]] = bool((value >> bit_num) & 1)

            self.client.close()
        except Exception as e:
            _LOGGER.error("Error reading diagnostic info: %s", e)
            self.client.close()
        return data


class SabianaDiagnosticBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """A binary sensor representing a diagnostic bit."""

    def __init__(self, coordinator: SabianaDiagnosticsCoordinator, key: str, name: str, entry_id: str):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"sabiana_diagnostic_{key}"
        self._attr_device_class = "problem"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Sabiana RVU",
            manufacturer="Sabiana",
            model="Smart Pro"
        )

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get(self._key)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up diagnostic binary sensors."""
    coordinator = SabianaDiagnosticsCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    sensors = []
    for def_entry in DIAGNOSTIC_DEFINITIONS.values():
        for bit in def_entry["bits"].values():
            sensors.append(
                SabianaDiagnosticBinarySensor(coordinator, key=bit["key"], name=bit["name"], entry_id=entry.entry_id)
            )

    async_add_entities(sensors)