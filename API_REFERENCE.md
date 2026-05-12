# Sabiana Smart Energy - API Reference

Complete API reference for developers extending or integrating with the Sabiana Smart Energy integration.

## Table of Contents
- [Core Integration](#core-integration)
- [Configuration Flow](#configuration-flow)
- [Coordinator](#coordinator)
- [Modbus Client](#modbus-client)
- [Platform Entities](#platform-entities)
- [Helper Functions](#helper-functions)
- [Constants](#constants)

---

## Core Integration

### Module: `__init__.py`

#### `async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool`

Sets up the Sabiana Energy Smart integration from a config entry.

**Parameters:**
- `hass` (HomeAssistant): The Home Assistant instance
- `entry` (ConfigEntry): Configuration entry containing connection parameters

**Returns:**
- `bool`: True if setup was successful, False otherwise

**Raises:**
- May raise exceptions during coordinator setup or connection

**Example:**
```python
# Called automatically by Home Assistant when integration is added
success = await async_setup_entry(hass, config_entry)
```

**Process Flow:**
1. Creates `SabianaModbusCoordinator` from config data
2. Establishes Modbus connection via `coordinator.async_setup()`
3. Performs initial data refresh
4. Stores coordinator in `hass.data[DOMAIN][entry_id]`
5. Forwards setup to all platforms

---

#### `async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool`

Unloads the integration and cleans up resources.

**Parameters:**
- `hass` (HomeAssistant): The Home Assistant instance
- `entry` (ConfigEntry): Configuration entry to unload

**Returns:**
- `bool`: True if unload was successful

**Process Flow:**
1. Retrieves coordinator from `hass.data[DOMAIN]`
2. Unloads all platform entities
3. Closes Modbus connection via `coordinator.async_close()`
4. Removes coordinator from hass.data

---

## Configuration Flow

### Module: `config_flow.py`

#### Class: `MyModbusDeviceConfigFlow`

Configuration flow handler for UI-based setup.

**Inherits:** `config_entries.ConfigFlow`

**Attributes:**
- `VERSION` (int): Config flow schema version (currently 1)

---

#### `async_step_user(user_input: dict[str, Any] | None = None) -> FlowResult`

Handles the user configuration step.

**Parameters:**
- `user_input` (dict | None): User-provided configuration data, or None for initial display

**Returns:**
- `FlowResult`: Either displays form or creates config entry

**Form Schema:**
```python
{
    CONF_NAME: str,           # Device friendly name (default: "Sabiana HRV")
    CONF_HOST: str,           # IP address or hostname
    CONF_PORT: int,           # Modbus TCP port (default: 502)
    CONF_SLAVE: int,          # Modbus slave/unit ID (default: 1)
}
```

**Validation:**
- Checks for duplicate entries (same host + port)
- Aborts with "already_configured" if duplicate found

**Example Usage:**
```python
# Initial display (user_input is None)
result = await flow.async_step_user(None)
# Shows configuration form

# After user submits (user_input contains data)
result = await flow.async_step_user({
    "name": "Living Room HRV",
    "host": "192.168.1.100",
    "port": 502,
    "slave": 1
})
# Creates config entry
```

---

## Coordinator

### Module: `modbus_coordinator.py`

#### Class: `SabianaModbusCoordinator`

Data update coordinator for Modbus communication.

**Inherits:** `DataUpdateCoordinator`

**Attributes:**
- `_host` (str): Modbus device IP address
- `_port` (int): Modbus TCP port
- `_slave` (int): Modbus slave/unit ID
- `_client` (SabianaModbusClient): Modbus client instance
- `_active_addresses` (set[int]): Registered addresses to poll
- `update_interval`: Set to 3 seconds

---

#### `__init__(hass: HomeAssistant, config: dict[str, Any])`

Initialize the coordinator.

**Parameters:**
- `hass` (HomeAssistant): Home Assistant instance
- `config` (dict): Configuration containing host, port, slave

**Example:**
```python
coordinator = SabianaModbusCoordinator(hass, {
    "host": "192.168.1.100",
    "port": 502,
    "slave": 1
})
```

---

#### `register_address(address: int) -> None`

Register a Modbus address for polling.

**Parameters:**
- `address` (int): Modbus register address (e.g., 0x0100)

**Notes:**
- Addresses are stored in `_active_addresses` set
- Only registered addresses are polled during updates
- Should be called during entity initialization

**Example:**
```python
coordinator.register_address(0x0100)  # T1 temperature
coordinator.register_address(0x0101)  # T2 temperature
```

---

#### `async_setup() -> None`

Establish Modbus connection.

**Raises:**
- Connection errors if unable to connect

**Example:**
```python
await coordinator.async_setup()
```

---

#### `async_close() -> None`

Close Modbus connection and cleanup.

**Example:**
```python
await coordinator.async_close()
```

---

#### `async_write_register(address: int, value: int) -> bool`

Write a value to a Modbus register.

**Parameters:**
- `address` (int): Register address to write
- `value` (int): Value to write (raw, unscaled)

**Returns:**
- `bool`: True if write successful

**Features:**
- Performs optimistic update (immediately updates local data)
- Schedules delayed refresh (500ms) to verify device state
- Logs write operations

**Example:**
```python
# Set operating mode to Manual (3)
success = await coordinator.async_write_register(0x0307, 3)
if success:
    print("Mode changed successfully")
```

---

#### `_async_update_data() -> dict[int, int]`

Fetch data from device (called by coordinator).

**Returns:**
- `dict[int, int]`: Mapping of address to register value

**Notes:**
- Called automatically every 3 seconds
- Only polls registered addresses
- Handles connection errors and retries

**Internal Method** - Do not call directly

---

## Modbus Client

### Module: `modbus_client.py`

#### Class: `SabianaModbusClient`

Low-level Modbus TCP communication wrapper.

**Attributes:**
- `_host` (str): Device IP address
- `_port` (int): TCP port
- `_client` (ModbusTcpClient): PyModbus client instance

---

#### `__init__(host: str, port: int)`

Initialize Modbus client.

**Parameters:**
- `host` (str): IP address or hostname
- `port` (int): TCP port (typically 502)

**Example:**
```python
client = SabianaModbusClient("192.168.1.100", 502)
```

---

#### `ensure_connected() -> None`

Ensure connection is established, connect if needed.

**Raises:**
- Connection errors if unable to connect

**Example:**
```python
await client.ensure_connected()
```

---

#### `read_register(address: int, count: int = 1, slave: int = 1) -> list[int] | int`

Read Modbus register(s).

**Parameters:**
- `address` (int): Starting register address
- `count` (int): Number of registers to read (default: 1)
- `slave` (int): Modbus slave/unit ID (default: 1)

**Returns:**
- `int`: Single value if count == 1
- `list[int]`: List of values if count > 1

**Raises:**
- Connection errors
- Modbus exceptions

**Example:**
```python
# Read single register
temp = await client.read_register(0x0100, count=1, slave=1)
# Returns: 235 (raw value)

# Read multiple registers (for float32)
value = await client.read_register(0x0118, count=2, slave=1)
# Returns: [16234, 42341] (two register values)
```

---

#### `write_register(address: int, value: int, slave: int = 1) -> bool`

Write to a single Modbus register.

**Parameters:**
- `address` (int): Register address
- `value` (int): Value to write (raw, unscaled)
- `slave` (int): Modbus slave/unit ID (default: 1)

**Returns:**
- `bool`: True if write successful

**Example:**
```python
# Turn unit on (write 1 to 0x0300)
success = await client.write_register(0x0300, 1, slave=1)
```

---

#### `close() -> None`

Close Modbus connection.

**Example:**
```python
await client.close()
```

---

## Platform Entities

### Sensor Platform

#### Module: `sensor.py`

#### Class: `SabianaModbusSensor`

Sensor entity for read-only values.

**Inherits:** `CoordinatorEntity`, `SensorEntity`

**Attributes:**
- `_address` (int): Modbus register address
- `_scale` (float): Scaling factor
- `_precision` (int): Decimal places
- `_type` (str): Data type ("uint16", "int16", "float32")

---

#### `__init__(coordinator, reg: dict, entry_id: str)`

Initialize sensor entity.

**Parameters:**
- `coordinator`: Modbus coordinator instance
- `reg` (dict): Register definition with address, scale, unit, etc.
- `entry_id` (str): Config entry ID

**Register Definition Schema:**
```python
{
    "address": int,           # Modbus address
    "key": str,              # Unique identifier
    "name": str,             # Display name
    "unit": str,             # Unit of measurement
    "scale": float,          # Scaling factor
    "precision": int,        # Decimal places
    "device_class": str,     # HA device class (optional)
    "type": str,             # Data type (default: "uint16")
}
```

---

#### `native_value` (property) -> float | None

Returns scaled sensor value.

**Returns:**
- `float`: Scaled value
- `None`: If no data available

**Calculation:**
```python
raw_value = coordinator.data.get(address)
scaled_value = raw_value * scale
rounded_value = round(scaled_value, precision)
```

**Example:**
```python
# Raw value: 235, Scale: 0.1, Precision: 1
sensor.native_value  # Returns: 23.5
```

---

### Binary Sensor Platform

#### Module: `binary_sensor.py`

#### Class: `SabianaBinarySensor`

Binary sensor for status bits.

**Inherits:** `CoordinatorEntity`, `BinarySensorEntity`

**Attributes:**
- `_address` (int): Register address containing the bit
- `_bit_num` (int): Bit position (0-15)
- `_key` (str): Unique identifier

---

#### `__init__(coordinator, address: int, bit_num: int, key: str, name: str, entry_id: str, entity_category)`

Initialize binary sensor.

**Parameters:**
- `coordinator`: Modbus coordinator
- `address` (int): Register address
- `bit_num` (int): Bit number to extract (0-15)
- `key` (str): Unique identifier
- `name` (str): Display name
- `entry_id` (str): Config entry ID
- `entity_category`: Entity category (config, diagnostic, or None)

**Example:**
```python
sensor = SabianaBinarySensor(
    coordinator=coordinator,
    address=0x0105,
    bit_num=8,
    key="on_status",
    name="Unit ON",
    entry_id=entry.entry_id,
    entity_category=None
)
```

---

#### `is_on` (property) -> bool | None

Returns bit state with inversion support.

**Returns:**
- `bool`: True if bit is set (with inversion applied)
- `None`: If no data available

**Inversion Logic:**
- Reads global inversion flag from 0x0104 bit 0
- Applies XOR if flag is set and sensor is not the flag itself
- Used for reversed airflow configurations

---

### Number Platform

#### Module: `number.py`

#### Class: `SabianaModbusNumber`

Number entity for writable parameters.

**Inherits:** `CoordinatorEntity`, `NumberEntity`

**Attributes:**
- `_address` (int): Register address
- `_scale` (float): Scaling factor
- `_precision` (int): Decimal places
- `_attr_native_min_value` (float): Minimum value
- `_attr_native_max_value` (float): Maximum value

---

#### `async_set_native_value(value: float) -> None`

Set parameter value.

**Parameters:**
- `value` (float): New value (scaled)

**Process:**
1. Converts scaled value to raw integer
2. Writes to device via coordinator
3. Updates optimistically

**Example:**
```python
# Set summer temperature setpoint to 24.5°C
await number.async_set_native_value(24.5)
# Internally: writes int(24.5 / 0.1) = 245 to register
```

---

### Select Platform

#### Module: `select.py`

#### Class: `SabianaModbusSelect`

Select entity for option selection.

**Attributes:**
- `_address` (int): Register address
- `_options_map` (dict): Mapping of value to option name

---

#### `async_select_option(option: str) -> None`

Select an option.

**Parameters:**
- `option` (str): Option name to select

**Process:**
1. Looks up numeric value from options map
2. Writes value to register

**Example:**
```python
# Operating mode options: {0: "Holiday", 1: "Auto", 2: "Program", 3: "Manual", 4: "Party"}
await select.async_select_option("Manual")
# Writes value 3 to register 0x0307
```

---

### Switch Platform

#### Module: `switch.py`

#### Class: `SabianaModbusSwitch`

Switch entity for on/off control.

---

#### `async_turn_on() -> None`

Turn switch on (writes 1).

**Example:**
```python
await switch.async_turn_on()  # Writes 1 to 0x0300
```

---

#### `async_turn_off() -> None`

Turn switch off (writes 0).

---

### Button Platform

#### Module: `button.py`

#### Class: `SabianaModbusButton`

Button entity for triggering actions.

---

#### `async_press() -> None`

Press button (writes 1).

**Example:**
```python
await button.async_press()  # Activates manual mode
```

---

## Helper Functions

### Module: `helpers.py`

#### `decode_modbus_value(raw, type_: str, data_length: int, scale: float, precision: int) -> float | str | None`

Decode and scale raw Modbus value(s).

**Parameters:**
- `raw` (list[int] | int | None): Raw register value(s)
- `type_` (str): Data type ("uint16", "int16", "float32", "char")
- `data_length` (int): Number of registers
- `scale` (float): Scaling factor
- `precision` (int): Decimal places for rounding

**Returns:**
- `float`: Scaled numeric value
- `str`: String value (for char type)
- `None`: If raw is None

**Supported Types:**

**uint16:** Unsigned 16-bit integer (0 to 65535)
```python
decode_modbus_value(1234, "uint16", 1, 0.1, 1)  # Returns: 123.4
```

**int16:** Signed 16-bit integer (-32768 to 32767)
- Uses two's complement conversion
```python
decode_modbus_value(65500, "int16", 1, 0.1, 1)  # Returns: -3.6
```

**float32:** IEEE 754 single-precision float (2 registers)
```python
decode_modbus_value([16234, 42341], "float32", 2, 1.0, 2)  # Returns: 1.23
```

**char:** ASCII string
```python
decode_modbus_value([0x4142, 0x4344], "char", 2, 1, 0)  # Returns: "ABCD"
```

---

## Constants

### Module: `const.py`

#### Configuration Constants

```python
DOMAIN = "sabiana_energy_smart"      # Integration domain
CONF_SLAVE = "slave"                 # Config key for Modbus slave ID
```

#### Device Information

#### `get_device_info(entry_id: str) -> dict`

Returns device information dict for entity device linkage.

**Parameters:**
- `entry_id` (str): Config entry ID

**Returns:**
```python
{
    "identifiers": {(DOMAIN, entry_id)},
    "name": "Sabiana RVU",
    "manufacturer": "Sabiana",
    "model": "Smart Pro",
}
```

#### Register Definitions

**SENSOR_DEFINITIONS_NEW**: Read-only sensor registers
**REGISTER_DEFINITIONS**: Read/write parameter registers
**SWITCH_DEFINITIONS**: Switch control registers
**BUTTON_DEFINITIONS**: Button action registers
**SELECT_DEFINITIONS**: Select option registers
**DIAGNOSTIC_DEFINITIONS**: Binary sensor status bits

**Definition Schema:**
```python
{
    0xADDR: {
        "key": str,              # Unique identifier
        "name": str,             # Display name
        "unit": str,             # Unit of measurement
        "scale": float,          # Scaling factor
        "precision": int,        # Decimal places
        "type": str,             # Data type
        "device_class": str,     # HA device class (optional)
        "readable": bool,        # Can read
        "writable": bool,        # Can write (optional)
        "min": int,             # Min value (writable only)
        "max": int,             # Max value (writable only)
        "options": dict,        # Option map (selects only)
        "bits": dict,           # Bit definitions (diagnostics only)
    }
}
```

---

## Error Handling

### Common Exceptions

**ModbusException**: Modbus protocol errors
- Invalid address
- Invalid value
- Device busy

**ConnectionError**: Network/connection issues
- Device unreachable
- Connection timeout
- Connection closed unexpectedly

**ValueError**: Data validation errors
- Value out of range
- Invalid option

### Best Practices

1. **Always check return values** from write operations
2. **Handle coordinator.data.get() returning None** in entity properties
3. **Log errors** with appropriate severity
4. **Use try/except blocks** around Modbus operations

**Example:**
```python
try:
    success = await coordinator.async_write_register(address, value)
    if not success:
        _LOGGER.error("Failed to write register 0x%04X", address)
except Exception as err:
    _LOGGER.exception("Unexpected error writing register: %s", err)
```

---

## Type Conversions

### Raw to Scaled (Reading)

```python
def raw_to_scaled(raw: int, scale: float, precision: int) -> float:
    """Convert raw register value to scaled float."""
    return round(raw * scale, precision)
```

### Scaled to Raw (Writing)

```python
def scaled_to_raw(value: float, scale: float) -> int:
    """Convert scaled value to raw register value."""
    return int(value / scale)
```

### Two's Complement (int16)

```python
def twos_complement(value: int, bits: int = 16) -> int:
    """Convert unsigned int to signed int using two's complement."""
    if value >= 2 ** (bits - 1):
        return value - 2 ** bits
    return value
```

### Float32 Decoding

```python
def decode_float32(registers: list[int]) -> float:
    """Decode IEEE 754 float32 from two registers."""
    import struct
    # Combine two 16-bit registers into one 32-bit value
    combined = (registers[0] << 16) | registers[1]
    # Unpack as float
    return struct.unpack('>f', struct.pack('>I', combined))[0]
```

---

## Version History

- **v1.0.0**: Initial release
- Documentation covers all modules and functions

---

## Additional Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [PyModbus Documentation](https://pymodbus.readthedocs.io/)
- [Modbus Protocol Specification](http://www.modbus.org/)

---

*Generated: 2025*
