# Sabiana Smart Energy Integration for Home Assistant

A custom integration for Home Assistant that enables communication with **Sabiana Smart Energy** heat recovery units over **Modbus** (RTU or TCP).  
This integration provides access to diagnostic data, environmental sensors, fan status, and control over various operational parameters.

[![Validate](https://github.com/CMGeorge/homeassistant_sabiana_smart_energy/actions/workflows/validate.yml/badge.svg)](https://github.com/CMGeorge/homeassistant_sabiana_smart_energy/actions/workflows/validate.yml)
[![Lint](https://github.com/CMGeorge/homeassistant_sabiana_smart_energy/actions/workflows/lint.yml/badge.svg)](https://github.com/CMGeorge/homeassistant_sabiana_smart_energy/actions/workflows/lint.yml)
[![hassfest](https://github.com/CMGeorge/homeassistant_sabiana_smart_energy/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/CMGeorge/homeassistant_sabiana_smart_energy/actions/workflows/hassfest.yaml)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=CMGerorge&repository=https%3A%2F%2Fgithub.com%2FCMGeorge%2Fhomeassistant_sabiana_smart_energy&category=Integration)

---

## 🔧 Features

- 📡 Modbus communication support (TCP or RTU)
- 🌡️ Sensor readings: temperature, humidity, VOC, CO₂, differential pressure
- 💨 Fan control: speed settings, speed coefficients
- 🧠 Diagnostic registers and status bits
- 🛠️ Write support for supported registers (e.g. setpoint, thresholds)
- 🏠 Native integration with Home Assistant UI

---

## 🧪 Supported Devices

- Sabiana **RVU Smart Energy** ventilation units  
- Should also support other **Smart Energy** compatible models (via Modbus)

---

## 📦 Installation

### Option 1: HACS (Recommended)
1. In Home Assistant, go to **HACS → Integrations → Custom Repositories**
2. Add this repository: https://github.com/CMGeorge/homeassistant_sabiana_smart_energy
3. Choose category: **Integration**
4. Install and restart Home Assistant

### Option 2: Manual
1. Clone or download this repository: https://github.com/CMGeorge/homeassistant_sabiana_smart_energy
2. Copy the folder to: config/custom_components/sabiana_smart_energy

3. Restart Home Assistant

---

## ⚙️ Configuration

The integration uses the UI (no YAML required). After install:

1. Go to **Settings → Devices & Services**
2. Click **Add Integration** → Search for **Sabiana Smart Energy**
3. Enter the required connection details:
- Host or Serial port
- Modbus type (TCP/RTU)
- Unit ID
- Polling interval

---

## 🧾 Entities

- `sensor.sabiana_temperature`
- `sensor.sabiana_humidity`
- `sensor.sabiana_co2`
- `sensor.sabiana_differential_pressure`
- `binary_sensor.sabiana_filter_status`
- `number.sabiana_fan_speed_setpoint`
- And many more...

Entity categories (`diagnostic`, `config`) are used where appropriate.

---

## 🧑‍💻 Development / Contribute

You're welcome to open issues, pull requests, or discussions!

To test locally:

```bash
git clone https://github.com/CMGeorge/homeassistant_sabiana_smart_energy.git
cp -r homeassistant_sabiana_smart_energy/custom_components/sabiana_smart_energy \
~/.homeassistant/custom_components/

```

### 🧪 Development Setup

For development and contributing:

```bash
# Clone the repository
git clone https://github.com/CMGeorge/homeassistant_sabiana_smart_energy.git
cd homeassistant_sabiana_smart_energy

# Install development dependencies
pip install -r requirements-dev.txt

# Run linting and formatting
make check          # Run all checks (lint, format, test)
make lint           # Run linting only
make format         # Format code
make lint-fix       # Fix linting issues
make test           # Run tests
make test-cov       # Run tests with coverage

# Or use tools directly
ruff check .        # Check for issues
ruff check . --fix  # Fix issues automatically
ruff format .       # Format code
pytest              # Run tests
pytest --cov       # Run tests with coverage

# Set up pre-commit hooks (optional)
pre-commit install
```

### 🧪 Testing

The integration includes automated tests to ensure code quality and functionality:

**Test Categories:**
- **Manifest validation**: Ensures `manifest.json` is valid and contains required fields
- **Code structure tests**: Validates all Python files have correct syntax and structure
- **Configuration tests**: Tests config flow validation without requiring Home Assistant runtime
- **Register definitions**: Validates Modbus register definitions in `const.py`
- **Integration tests**: Checks file structure and imports

**Running Tests:**
```bash
# Run all tests
make test

# Run tests with coverage report
make test-cov

# Run tests directly with pytest
pytest
pytest -v  # verbose output
pytest tests/test_manifest.py  # run specific test file
```

**Test Structure:**
```
tests/
├── __init__.py
├── conftest.py              # Test configuration and fixtures
├── test_manifest.py         # Manifest.json validation tests
├── test_const.py           # Constants and register definition tests
├── test_config_flow.py     # Configuration flow tests
└── test_integration.py     # Integration and syntax tests
```

**Note**: These tests are designed to work without a full Home Assistant installation, focusing on static analysis, syntax validation, and structure verification.

📚 Modbus Register Map

This integration is based on Sabiana’s official Modbus documentation.
You can find/extend register definitions in: custom_components/sabiana_smart_energy/const.py


📜 License

MIT License © George Călugăr
Not affiliated with Sabiana S.p.A.







