# info_sensor.py

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from pymodbus.client import ModbusTcpClient

from .const import DOMAIN, CONF_SLAVE

_LOGGER = logging.getLogger(__name__)


class SabianaInfoCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.host = entry.data[CONF_HOST]
        self.port = entry.data[CONF_PORT]
        self.slave = entry.data[CONF_SLAVE]
        self.client = ModbusTcpClient(self.host, port=self.port)

        super().__init__(
            hass,
            _LOGGER,
            name="Sabiana Info Coordinator",
            update_interval=timedelta(hours=1),
        )

    async def _async_update_data(self) -> dict[str, str | int | None]:
        results = {}
        try:
            self.client.connect()

            result = self.client.read_holding_registers(0x0000, 7, slave=self.slave)
            if not result.isError():
                chars = ''.join(
                    chr((reg >> 8) & 0xFF) + chr(reg & 0xFF)
                    for reg in result.registers
                ).strip()
                results["serial"] = chars
            else:
                results["serial"] = None

            def read_register(addr, key):
                res = self.client.read_holding_registers(addr, 1, slave=self.slave)
                results[key] = res.registers[0] if not res.isError() else None

            read_register(0x000A, "model")
            read_register(0x000B, "fw_release")
            read_register(0x000C, "protocol_release")
            read_register(0x000D, "tep_release")

            self.client.close()
        except Exception as e:
            _LOGGER.error("Error reading device info: %s", e)
            self.client.close()
            return {
                "serial": None,
                "model": None,
                "fw_release": None,
                "protocol_release": None,
                "tep_release": None,
            }

        return results


class SabianaInfoSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, key, name, unit=None):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"sabiana_info_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "sabiana_info")},
            name="Sabiana RVU Info",
            manufacturer="Sabiana",
            model="Smart Pro"
        )

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)