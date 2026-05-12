# Sabiana Smart Energy Integration - Technical Documentation

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Modbus Register Map](#modbus-register-map)
- [Module Reference](#module-reference)
- [Entity Types](#entity-types)
- [Development Guide](#development-guide)

---

## Overview

The Sabiana Smart Energy integration provides comprehensive support for Sabiana heat recovery ventilation units via Modbus communication. It implements a coordinator-based architecture for efficient polling and supports multiple entity types for monitoring and control.

### Key Features
- **Modbus TCP/RTU Support**: Connect via network or serial connection
- **Efficient Polling**: Only polls registers needed by active entities
- **Comprehensive Entities**: Sensors, switches, numbers, selects, buttons, and binary sensors
- **Diagnostic Information**: Status flags, alarms, and configuration bits
- **Write Support**: Control fan speeds, setpoints, and operating modes

---

## Architecture

### Component Structure

```
custom_components/sabiana_energy_smart/
├── __init__.py              # Integration setup and platform loading
├── config_flow.py           # UI configuration flow
├── const.py                 # Register definitions and constants
├── modbus_coordinator.py    # Data coordinator for Modbus polling
├── modbus_client.py         # Modbus communication layer
├── helpers.py               # Utility functions for data conversion
├── sensor.py                # Temperature, humidity, CO2, etc.
├── binary_sensor.py         # Status flags and diagnostic bits
├── number.py                # Writable parameters (setpoints, thresholds)
├── select.py                # Mode and program selection
├── switch.py                # Power on/off
└── button.py                # Mode activation (Manual, Holiday, Party)
```

### Data Flow

```
┌─────────────────┐
│  Home Assistant │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ SabianaModbusCoord  │ ◄── Polls every 3 seconds
│ (DataUpdateCoord)   │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ SabianaModbusClient │ ◄── Manages TCP connection
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Sabiana Device     │
│  (Modbus TCP)       │
└─────────────────────┘
```

### Coordinator Pattern

The integration uses Home Assistant's `DataUpdateCoordinator` pattern:

1. **Address Registration**: Each entity registers the Modbus addresses it needs
2. **Efficient Polling**: Coordinator only polls registered addresses
3. **Shared Updates**: All entities receive updates simultaneously
4. **Optimistic Updates**: Write operations immediately update local state

---

## Modbus Register Map

### Temperature Sensors (Read-Only)

| Address | Name | Unit | Scale | Description |
|---------|------|------|-------|-------------|
| 0x0100 | T1 - External Air | °C | 0.1 | Outside air temperature |
| 0x0101 | T2 - Intake Air | °C | 0.1 | Fresh air intake temperature |
| 0x0102 | T3 - Extracted Air | °C | 0.1 | Stale air from building |
| 0x0103 | T4 - Exhaust Air | °C | 0.1 | Expelled air temperature |

### Environmental Sensors (Read-Only)

| Address | Name | Unit | Scale | Description |
|---------|------|------|-------|-------------|
| 0x0106 | Humidity Setpoint | % | 0.1 | Current humidity setpoint |
| 0x0113 | CO2 Level | ppm | 1 | CO2 concentration |
| 0x0114 | VOC Level | - | 1 | Volatile organic compounds |
| 0x0115 | Humidity Level | % | 0.1 | Relative humidity |

### Fan Control (Read-Only Status)

| Address | Name | Unit | Scale | Description |
|---------|------|------|-------|-------------|
| 0x010B | Fan 1 Speed | RPM | 1 | Supply fan speed |
| 0x010C | Fan 2 Speed | RPM | 1 | Extract fan speed |
| 0x010D | Fan 1 Duty | % | 0.01 | Supply fan duty cycle |
| 0x010E | Fan 2 Duty | % | 0.01 | Extract fan duty cycle |

### Configuration Parameters (Read/Write)

| Address | Name | Unit | Range | Description |
|---------|------|------|-------|-------------|
| 0x0213 | Speed 1 % | % | 0-35 | First speed level |
| 0x0214 | Speed 2 % | % | 35-70 | Second speed level |
| 0x0215 | Speed 3 % | % | 45-100 | Third speed level |
| 0x0216 | Speed 4 % | % | 100-110 | Fourth speed level |
| 0x0217 | Boost Speed % | % | 110-130 | Boost mode speed |

### Control Registers (Write)

| Address | Name | Values | Description |
|---------|------|--------|-------------|
| 0x0300 | Power On/Off | 0/1 | Main power switch |
| 0x0301 | Manual Mode | - | Activate manual mode |
| 0x0302 | Holiday Mode | - | Activate holiday mode |
| 0x0303 | Party Mode | - | Activate party mode |
| 0x0307 | Operating Mode | 0-4 | 0=Holiday, 1=Auto, 2=Program, 3=Manual, 4=Party |

### Diagnostic Registers (Read-Only, Bit-Mapped)

| Address | Bit | Name | Description |
|---------|-----|------|-------------|
| 0x0104 | 0 | Config Inverted | Flow direction inverted |
| 0x0104 | 1 | Preheating Present | Preheater installed |
| 0x0105 | 0 | Remote OFF | Remote off command active |
| 0x0105 | 1 | Bypass Active | Bypass damper open |
| 0x0105 | 8 | Unit ON | Unit is powered on |
| 0x0110 | 0-11 | Alarms | Various alarm conditions |

---

## Module Reference

### `__init__.py`
Main integration entry point.

**Functions:**
- `async_setup_entry(hass, entry) -> bool`: Initialize integration
- `async_unload_entry(hass, entry) -> bool`: Cleanup on removal

**Key Variables:**
- `PLATFORMS`: List of supported platform types
- `DOMAIN`: Integration domain name ("sabiana_energy_smart")

### `modbus_coordinator.py`
Manages Modbus communication and data updates.

**Class: `SabianaModbusCoordinator`**

Inherits from `DataUpdateCoordinator`.

**Methods:**
- `register_address(address: int)`: Register an address for polling
- `async_setup()`: Establish Modbus connection
- `async_close()`: Close connection
- `async_write_register(address: int, value: int) -> bool`: Write to device

**Update Interval:** 3 seconds

### `modbus_client.py`
Low-level Modbus TCP communication.

**Class: `SabianaModbusClient`**

**Methods:**
- `ensure_connected()`: Connect if not already connected
- `read_register(address, count, slave) -> list[int]`: Read registers
- `write_register(address, value, slave) -> bool`: Write single register
- `close()`: Close connection

### `sensor.py`
Sensor platform implementation.

**Class: `SabianaModbusSensor`**

Represents a read-only sensor value.

**Supported Data Types:**
- `uint16`: Unsigned 16-bit integer
- `int16`: Signed 16-bit integer (two's complement)
- `float32`: IEEE 754 floating point (spans 2 registers)

**Properties:**
- `native_value`: Scaled sensor value
- `device_class`: Home Assistant device class
- `unit_of_measurement`: Unit string

### `number.py`
Number platform for writable parameters.

**Class: `SabianaModbusNumber`**

Provides slider controls for setpoints and thresholds.

**Features:**
- Min/max validation
- Automatic scaling
- Optimistic updates

### `binary_sensor.py`
Binary sensor platform for status flags.

**Class: `SabianaBinarySensor`**

Represents individual bits from diagnostic registers.

**Features:**
- Global inversion support (for reversed airflow)
- Entity categories (config, diagnostic)
- Bit extraction from multi-bit registers

### `select.py`
Select platform for mode selection.

**Class: `SabianaModbusSelect`**

Dropdown selection for operating modes and programs.

**Examples:**
- Operating Mode: Holiday, Auto, Program, Manual, Party
- Timer Program: Program 1-8

### `switch.py`
Switch platform for on/off control.

**Class: `SabianaModbusSwitch`**

Binary control entities.

**Example:**
- Power On/Off (0x0300)

### `button.py`
Button platform for actions.

**Class: `SabianaModbusButton`**

One-time action triggers.

**Examples:**
- Activate Manual Mode
- Activate Holiday Mode
- Activate Party Mode

---

## Entity Types

### Sensors (Platform: `sensor`)
**Read-only** entities that display measured values.

**Categories:**
- Temperature (T1-T4)
- Humidity and CO2
- Fan speeds (RPM and %)
- Pressure differentials
- Air coefficients

**Example Entity IDs:**
- `sensor.sabiana_external_air_temperature`
- `sensor.sabiana_co2_level`
- `sensor.sabiana_fan_1_speed_rpm`

### Binary Sensors (Platform: `binary_sensor`)
**Read-only** on/off indicators from status bits.

**Categories:**
- Configuration flags
- Operational status
- Alarms

**Example Entity IDs:**
- `binary_sensor.sabiana_unit_on`
- `binary_sensor.sabiana_bypass_active`
- `binary_sensor.sabiana_t1_probe_failure_alarm`

### Numbers (Platform: `number`)
**Writable** numeric parameters with sliders.

**Categories:**
- Temperature setpoints
- Speed percentages
- Thresholds

**Example Entity IDs:**
- `number.sabiana_summer_t_setpoint`
- `number.sabiana_speed_1_percent`
- `number.sabiana_co2_ppm_max`

### Selects (Platform: `select`)
**Writable** dropdown selections.

**Options:**
- Operating Mode: Holiday, Auto, Program, Manual, Party
- Timer Program: Program 1-8

**Example Entity IDs:**
- `select.sabiana_operating_mode`
- `select.sabiana_timer_program`

### Switches (Platform: `switch`)
**Writable** binary controls.

**Example Entity IDs:**
- `switch.sabiana_power_on_off`

### Buttons (Platform: `button`)
**Writable** action triggers.

**Example Entity IDs:**
- `button.sabiana_manual_mode`
- `button.sabiana_holiday_mode`
- `button.sabiana_party_mode`

---

## Development Guide

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/CMGeorge/homeassistant_sabiana_smart_energy.git
cd homeassistant_sabiana_smart_energy

# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
ruff check .

# Format code
ruff format .

# Run tests
pytest
pytest --cov  # With coverage
```

### Adding a New Sensor

1. **Define in `const.py`:**
```python
SENSOR_DEFINITIONS_NEW = {
    0x0XXX: {
        "key": "my_sensor",
        "name": "My Sensor",
        "unit": "unit",
        "scale": 1.0,
        "precision": 1,
        "device_class": "temperature",  # or other appropriate class
        "readable": True,
    },
}
```

2. **Test:**
The sensor will automatically be created by the sensor platform.

3. **Document:**
Add to this file and update README.md.

### Adding a New Writable Parameter

1. **Define in `const.py`:**
```python
REGISTER_DEFINITIONS = {
    0x0XXX: {
        "key": "my_parameter",
        "name": "My Parameter",
        "unit": "unit",
        "scale": 1.0,
        "precision": 1,
        "min": 0,
        "max": 100,
        "readable": True,
        "writable": True,
    },
}
```

2. **Automatically appears as Number entity**

### Testing Without Hardware

Use a Modbus simulator or create mock responses in `modbus_client.py` for development.

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to all public functions and classes
- Keep explanatory comments for complex logic
- Run `ruff check .` before committing

### Debugging

Enable debug logging in Home Assistant's `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.sabiana_energy_smart: debug
```

---

## API Reference

### Helper Functions (`helpers.py`)

#### `decode_modbus_value(raw, type_, data_length, scale, precision)`
Converts raw Modbus register values to scaled numeric values.

**Parameters:**
- `raw`: Raw register value(s) as list or int
- `type_`: Data type ("uint16", "int16", "float32", "char")
- `data_length`: Number of registers
- `scale`: Scaling factor
- `precision`: Decimal places

**Returns:** Scaled value or string (for char type)

**Example:**
```python
# Temperature reading: raw value 235 with scale 0.1
value = decode_modbus_value([235], "int16", 1, 0.1, 1)
# Returns: 23.5
```

---

## Troubleshooting

### Connection Issues

**Problem:** "Failed to connect to Modbus device"

**Solutions:**
1. Verify IP address and port (default 502)
2. Check firewall rules
3. Ensure device is on same network
4. Verify Modbus slave ID (usually 1)

### No Data Updates

**Problem:** Sensors show "Unavailable"

**Solutions:**
1. Check Modbus connection in logs
2. Verify device is powered on and responding
3. Check coordinator update interval (default 3s)
4. Review entity definitions in `const.py`

### Write Operations Fail

**Problem:** Unable to change setpoints or modes

**Solutions:**
1. Verify register is writable in device documentation
2. Check value is within min/max range
3. Ensure device is not in protected/locked mode
4. Review Modbus write permissions

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

---

## License

MIT License - See LICENSE file for details

## Support

- **Issues**: https://github.com/CMGeorge/homeassistant_sabiana_smart_energy/issues
- **Discussions**: https://github.com/CMGeorge/homeassistant_sabiana_smart_energy/discussions

---

*Last updated: 2025*
