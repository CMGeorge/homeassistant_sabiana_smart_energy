from __future__ import annotations

from datetime import timedelta
import asyncio
import logging
from typing import Any

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, CONF_SLAVE
from .info_sensor import SabianaInfoCoordinator, SabianaInfoSensor

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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    _LOGGER.debug("Set up the Modbus sensors from a config entry.")


    info_coordinator = SabianaInfoCoordinator(hass, entry)
    await info_coordinator.async_config_entry_first_refresh()

    info_sensors = [
        SabianaInfoSensor(info_coordinator, "serial", "RVU Serial Number", None, entry.entry_id),
        SabianaInfoSensor(info_coordinator, "model", "RVU Model", None, entry.entry_id),
        SabianaInfoSensor(info_coordinator, "fw_release", "Firmware Release", None, entry.entry_id),
        SabianaInfoSensor(info_coordinator, "protocol_release", "Protocol Release", None, entry.entry_id),
        SabianaInfoSensor(info_coordinator, "tep_release", "T-EP Firmware", None, entry.entry_id)
    ]
    async_add_entities(info_sensors)


    coordinator = SabianaModbusCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    sensors = [
        SabianaModbusSensor(
            coordinator=coordinator,
            name=definition["name"],
            address=definition["address"],
            unit=definition.get("unit"),
            scale=definition.get("scale", 1),
            precision=definition.get("precision", 0),
            device_class=definition.get("device_class"),
            unique_id=definition["unique_id"],
            entry_id=entry.entry_id,
        )
        for definition in SENSOR_DEFINITIONS
    ]

    async_add_entities(sensors)


class SabianaModbusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.host = entry.data[CONF_HOST]
        self.port = entry.data[CONF_PORT]
        self.slave = entry.data[CONF_SLAVE]
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
                value = None
                for attempt in range(3):
                    try:
                        result = self.client.read_holding_registers(
                            address=address,
                            count=1,
                            slave=self.slave
                        )
                        if not result.isError():
                            value = result.registers[0]
                            break
                    except ModbusIOException as e:
                        _LOGGER.warning("Retry %d failed for 0x%04X: %s", attempt+1, address, e)
                        await asyncio.sleep(0.2)
                    except Exception as e:
                        _LOGGER.error("Unexpected Modbus error: %s", e)
                        break
                results[address] = value
            self.client.close()
        except Exception as e:
            _LOGGER.error("Modbus global read error: %s", e)
            self.client.close()
            for sensor in SENSOR_DEFINITIONS:
                results[sensor["address"]] = None
        return results


class SabianaModbusSensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator: SabianaModbusCoordinator,
        name: str,
        address: int,
        unit: str | None,
        scale: float,
        precision: int,
        device_class: str | None,
        unique_id: str,
        entry_id: str,
    ):
        super().__init__(coordinator)
        self._attr_name = name
        self._address = address
        self._scale = scale
        self._precision = precision
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Sabiana RVU",
            manufacturer="Sabiana",
            model="Smart Pro",
        )

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.get(self._address)
        if raw is None:
            return None
        return round(raw * self._scale, self._precision)