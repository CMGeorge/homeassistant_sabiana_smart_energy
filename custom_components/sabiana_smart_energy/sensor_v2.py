from __future__ import annotations

import logging
from typing import Any

from pymodbus.client import ModbusTcpClient
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from datetime import timedelta
from .const import DOMAIN, CONF_SLAVE

_LOGGER = logging.getLogger(__name__)

SENSOR_DEFINITIONS = [
    {"name": "RVU Temp Probe 1", "address": 0x0100, "unit": "°C", "scale": 0.1, "precision": 1, "device_class": "temperature", "unique_id": "sabiana_sensor_probe_temp1"},
    {"name": "RVU Temp Probe 2", "address": 0x0101, "unit": "°C", "scale": 0.1, "precision": 1, "device_class": "temperature", "unique_id": "sabiana_sensor_probe_temp2"},
    {"name": "RVU Temp Probe 3", "address": 0x0102, "unit": "°C", "scale": 0.1, "precision": 1, "device_class": "temperature", "unique_id": "sabiana_sensor_probe_temp3"},
    {"name": "RVU Temp Probe 4", "address": 0x0103, "unit": "°C", "scale": 0.1, "precision": 1, "device_class": "temperature", "unique_id": "sabiana_sensor_probe_temp4"},
    {"name": "Fan 1 Speed RPM", "address": 0x010B, "unit": "rpm", "unique_id": "sabiana_sensor_fan1_speed_rpm"},
    {"name": "Fan 2 Speed RPM", "address": 0x010C, "unit": "rpm", "unique_id": "sabiana_sensor_fan2_speed_rpm"},
    {"name": "Fan 1 Duty %", "address": 0x010D, "unit": "%", "scale": 0.1, "precision": 1, "unique_id": "sabiana_sensor_fan1_speed_percent"},
    {"name": "Fan 2 Duty %", "address": 0x010E, "unit": "%", "scale": 0.1, "precision": 1, "unique_id": "sabiana_sensor_fan2_speed_percent"},
    {"name": "Preheater Duty %", "address": 0x010F, "unit": "%", "unique_id": "sabiana_sensor_preaheter_percent"},
    {"name": "Humidity Setpoint", "address": 0x0106, "unit": "%", "scale": 0.1, "precision": 1, "device_class": "humidity", "unique_id": "sabiana_sensor_humidity_setpoin"},
    {"name": "CO2 Level", "address": 0x0113, "unit": "ppm", "scale": 0.01, "precision": 2, "device_class": "carbon_dioxide", "unique_id": "sabiana_sensor_co2_level"},
    {"name": "RVU Operating Mode", "address": 0x0119, "unique_id": "sabiana_sensor_operation_mode"},
    {"name": "Party Mode Status", "address": 0x011A, "unique_id": "sabiana_sensor_partymode"},
    {"name": "Filter Alarm", "address": 0x0107, "unique_id": "sabiana_sensor_filter_alarm"},
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Modbus sensors from config entry."""
    _LOGGER.debug("Setting up Sabiana sensors...")
    coordinator = SabianaModbusCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    sensors = [
        SabianaModbusSensor(coordinator, definition)
        for definition in SENSOR_DEFINITIONS
    ]

    async_add_entities(sensors)


class SabianaModbusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.host = entry.data[CONF_HOST]
        self.port = entry.data[CONF_PORT]
        self.slave = entry.data[CONF_SLAVE]
        self.entry_id = entry.entry_id
        self.client = ModbusTcpClient(self.host, port=self.port)

        super().__init__(
            hass,
            _LOGGER,
            name="Sabiana Modbus Coordinator",
            update_interval=timedelta(seconds=3),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        results = {}
        try:
            self.client.connect()
            for sensor in SENSOR_DEFINITIONS:
                address = sensor["address"]
                result = self.client.read_holding_registers(address=address, count=1, slave=self.slave)
                if not result.isError():
                    raw_value = result.registers[0]
                    results[address] = raw_value
                else:
                    results[address] = None
            self.client.close()
        except Exception as e:
            _LOGGER.error("Error reading Modbus data: %s", e)
            self.client.close()
        return results


class SabianaModbusSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: SabianaModbusCoordinator, definition: dict[str, Any]) -> None:
        super().__init__(coordinator)
        self.definition = definition
        self._address = definition["address"]
        self._attr_name = definition["name"]
        self._attr_native_unit_of_measurement = definition.get("unit")
        self._scale = definition.get("scale", 1)
        self._precision = definition.get("precision", 0)
        self._attr_device_class = definition.get("device_class")
        self._attr_unique_id = definition["unique_id"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry_id)},
            name="Sabiana RVU",
            manufacturer="Sabiana",
            model="Smart Pro",
        )

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._address)
        if value is None:
            return None
        return round(value * self._scale, self._precision)