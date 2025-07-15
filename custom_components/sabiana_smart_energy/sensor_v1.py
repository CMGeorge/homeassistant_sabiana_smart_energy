from __future__ import annotations

from pymodbus.client import ModbusTcpClient
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_SLAVE

import logging

_LOGGER = logging.getLogger(__name__)

SENSOR_DEFINITIONS = [
    {
        "name": "RVU Temp Probe 1",
        "address": 0x0100,
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "device_class": "temperature",
        "unique_id": "sabiana_sensor_probe_temp1"
    },
    {
        "name": "RVU Temp Probe 2",
        "address": 0x0101,
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "device_class": "temperature",
        "unique_id": "sabiana_sensor_probe_temp2"
    },
    {
        "name": "RVU Temp Probe 3",
        "address": 0x0102,
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "device_class": "temperature",
        "unique_id": "sabiana_sensor_probe_temp3"
    },
    {
        "name": "RVU Temp Probe 4",
        "address": 0x0103,
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "device_class": "temperature",
        "unique_id": "sabiana_sensor_probe_temp4"
    },
    {
        "name": "Fan 1 Speed RPM",
        "address": 0x010B,
        "unit": "rpm",
        "unique_id": "sabiana_sensor_fan1_speed_rpm"
    },
    {
        "name": "Fan 2 Speed RPM",
        "address": 0x010C,
        "unit": "rpm",
        "unique_id": "sabiana_sensor_fan2_speed_rpm"
    },
    {
        "name": "Fan 1 Duty %",
        "address": 0x010D,
        "unit": "%",
        "scale": 0.1,
        "precision": 1,
        "unique_id": "sabiana_sensor_fan1_speed_percent"
    },
    {
        "name": "Fan 2 Duty %",
        "address": 0x010E,
        "unit": "%",
        "scale": 0.1,
        "precision": 1,
        "unique_id": "sabiana_sensor_fan2_speed_percent"
    },
    {
        "name": "Preheater Duty %",
        "address": 0x010F,
        "unit": "%",
        "unique_id": "sabiana_sensor_preaheter_percent"
    },
    {
        "name": "Humidity Setpoint",
        "address": 0x0106,
        "unit": "%",
        "scale": 0.1,
        "precision": 1,
        "device_class": "humidity",
        "unique_id": "sabiana_sensor_humidity_setpoin"
    },
    {
        "name": "CO2 Level",
        "address": 0x0113,
        "unit": "ppm",
        "scale": 0.01,
        "precision": 2,
        "device_class": "carbon_dioxide",
        "unique_id": "sabiana_sensor_co2_level"
    },
    {
        "name": "RVU Operating Mode",
        "address": 0x0119,
        "unique_id": "sabiana_sensor_operation_mode"
    },
    {
        "name": "Party Mode Status",
        "address": 0x011A,
        "unique_id": "sabiana_sensor_partymode"
    },
    {
        "name": "Filter Alarm",
        "address": 0x0107,
        "unique_id": "sabiana_sensor_filter_alarm"
    }
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Modbus sensors from a config entry."""
    _LOGGER.debug("Set up the Modbus sensors from a config entry.")
    data = entry.data
    sensors = [
        SabianaModbusSensor(
            name=definition["name"],
            address=definition["address"],
            unit=definition.get("unit"),
            scale=definition.get("scale", 1),
            precision=definition.get("precision", 0),
            device_class=definition.get("device_class"),
            unique_id=definition["unique_id"],
            host=data[CONF_HOST],
            port=data[CONF_PORT],
            slave=data[CONF_SLAVE],
            entry_id=entry.entry_id,
        )
        for definition in SENSOR_DEFINITIONS
    ]

    async_add_entities(sensors, update_before_add=True)


class SabianaModbusSensor(SensorEntity):
    """Representation of a Modbus-based Sabiana sensor."""

    def __init__(self, name, address, unit, scale, precision, device_class, unique_id, host, port, slave, entry_id):
        self._host = host
        self._port = port
        self._slave = slave
        self._address = address
        self._scale = scale
        self._precision = precision
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_unique_id = unique_id
        self._entry_id = entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Sabiana RVU",
            manufacturer="Sabiana",
            model="Smart Pro"
        )

    def update(self):
        """Read data from Modbus register."""
        try:
            client = ModbusTcpClient(self._host, port=self._port)
            client.connect()
            result = client.read_holding_registers(self._address, 1, slave=self._slave)
            client.close()

            if result.isError():
                self._attr_native_value = None
            else:
                raw_value = result.registers[0]
                scaled = raw_value * self._scale
                self._attr_native_value = round(scaled, self._precision)
        except Exception as e:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {"error": str(e)}
