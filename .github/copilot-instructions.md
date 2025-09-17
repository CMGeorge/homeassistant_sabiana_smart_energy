# Copilot Instructions for Sabiana Smart Energy Integration

## Project Overview
This is a Home Assistant custom integration for **Sabiana Smart Energy** heat recovery units that communicates over **Modbus** (RTU or TCP). The integration provides access to diagnostic data, environmental sensors, fan status, and control over various operational parameters.

## Architecture and Structure
- **Integration Type**: Hub integration with multiple entity platforms
- **Communication**: Modbus TCP/RTU using pymodbus library
- **Entity Platforms**: sensor, binary_sensor, number, select, switch, button
- **Configuration**: UI-based configuration flow (no YAML)

## Key Files and Their Purposes
- `__init__.py`: Main integration setup and coordinator initialization
- `config_flow.py`: UI configuration flow for device setup
- `const.py`: Register definitions and constants for Modbus communication
- `modbus_client.py`: Modbus communication wrapper
- `modbus_coordinator.py`: Data coordinator for polling and state management
- `sensor.py`, `binary_sensor.py`, `number.py`, etc.: Entity platform implementations
- `helpers.py`: Utility functions for data processing
- `manifest.json`: Integration metadata and dependencies

## Coding Standards and Patterns

### Home Assistant Conventions
- Follow Home Assistant core development standards
- Use async/await patterns for all I/O operations
- Implement proper entity categories (diagnostic, config)
- Use device classes for sensors when appropriate
- Follow naming conventions: `sabiana_<entity_type>_<key>`

### Code Quality
- Use ruff for linting and formatting
- Run `python3 -m ruff check .` and `python3 -m ruff format .` before commits
- Fix unused imports and follow Python best practices
- Use type hints with `from __future__ import annotations`

### Entity Implementation Patterns
- Inherit from appropriate Home Assistant base classes
- Use `CoordinatorEntity` for entities that update via the coordinator
- Implement `unique_id`, `device_info`, and `entity_category` appropriately
- Use proper device classes and units of measurement

### Modbus Communication
- All Modbus operations should be async
- Handle connection failures gracefully with retries
- Use the register definitions in `const.py` for consistency
- Scale values according to register definitions
- Always check for None/error conditions from Modbus operations

## Testing and Validation
- Use hassfest validation: Home Assistant's integration validator
- Use HACS validation for custom component standards
- Test with actual hardware when possible
- Validate entity states and attributes

## Dependencies
- Home Assistant >= 2025.4.0 (requires Python 3.13+)
- pymodbus >= 3.0.0 for Modbus communication
- Standard Home Assistant helper modules

## Common Tasks

### Adding New Entities
1. Define register in `const.py` with proper metadata
2. Add to appropriate entity platform file
3. Update platform list in `__init__.py` if needed
4. Test with actual device

### Modifying Modbus Communication
1. Update register definitions in `const.py`
2. Test read/write operations
3. Handle scaling and data type conversions
4. Update entity attributes if needed

### Configuration Changes
1. Modify `config_flow.py` for UI changes
2. Update validation logic
3. Handle migration if configuration schema changes
4. Test configuration flow in Home Assistant

## Development Environment
- Use devcontainer for consistent development environment
- Install dependencies with `poetry` or pip
- Use Home Assistant development environment for testing
- Test with real Sabiana devices when available

## Error Handling
- Use appropriate logging levels (DEBUG, INFO, WARNING, ERROR)
- Handle Modbus communication errors gracefully
- Provide meaningful error messages to users
- Implement proper connection retry logic

## Performance Considerations
- Use efficient polling intervals (default: reasonable for device type)
- Batch Modbus operations when possible
- Implement proper coordinator update patterns
- Avoid blocking the event loop

## Security
- Validate all user inputs in config flow
- Use secure Modbus communication practices
- Don't log sensitive information
- Follow Home Assistant security guidelines

## Code Examples and Patterns

### Adding a New Sensor Entity
```python
# In sensor.py
class SabianaSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, config, description):
        super().__init__(coordinator)
        self._config = config
        self._description = description
        self._attr_unique_id = f"sabiana_sensor_{description['key']}"
        self._attr_name = description["name"]
        self._attr_device_info = DeviceInfo(**get_device_info(config.entry_id))
```

### Register Definition Pattern
```python
# In const.py
REGISTER_DEFINITIONS = {
    0x0100: {
        "key": "temperature_probe_1",
        "name": "Temperature Probe 1",
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "device_class": "temperature",
        "readable": True,
    },
}
```

### Modbus Communication Pattern
```python
# Always handle errors and scaling
raw_value = await coordinator._client.read_register(address, 1, slave_id)
if raw_value is not None:
    scaled_value = raw_value[0] * scale_factor
    return round(scaled_value, precision)
return None
```

## Repository-Specific Notes
- The integration connects to Sabiana heat recovery units via Modbus
- Register map is comprehensive in `const.py` - reference it for available data points
- Entity categories are properly set (diagnostic for status info, config for settings)
- All entity names follow the pattern: `sabiana_<type>_<function>`
- Use the existing device info pattern for consistent device grouping
- Coordinator handles polling - entities should not directly poll the device

## Workflow Integration
This repository uses GitHub Actions for:
- **Lint**: Ruff for code quality and formatting
- **Validate**: hassfest for HA integration validation
- **HACS**: Validation for custom component distribution
- **Release**: Automated release process

Always ensure your code passes all checks:
```bash
python3 -m ruff check .
python3 -m ruff format .
```