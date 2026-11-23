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
- 🕒 Device clock sync from Home Assistant (handles daylight saving time changes)
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

### Polling options

**Settings → Devices & Services → Sabiana Energy Smart → Configure** sets how
the unit is polled. Saving reloads the integration.

| Option | Default | Range | What it does |
|--------|---------|-------|--------------|
| Polling interval | 3 s | 1–300 s | Time between polls |
| Answer timeout | 3 s | 0.5–30 s | How long to wait for each answer |
| Retries after a timeout | 3 | 0–10 | How many times a request is resent |

A request that gets no answer takes up to *timeout × (retries + 1)* seconds
(12 s with the defaults) before the poll is given up. If the logs show
`No response received after 3 retries` or `request ask for transaction_id=…
but got id=…` (answers arriving after the timeout), the link to the unit is
slow, which is common with RS485-to-Wi-Fi/Ethernet gateways: raise the polling
interval (e.g. 10–15 s) and the timeout (e.g. 5 s), and lower the retries
(e.g. 1).

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

### 🕒 Device clock and daylight saving time

The unit's clock only stores hour, minute and day of the week (registers
`0x0800`/`0x0801`). It has no date, so it **cannot switch to or from daylight
saving time by itself**, and weekly timer programs run an hour off after each
DST change. The integration handles this:

- **Device clock** (diagnostic sensor): the unit's time, e.g. `Mon 14:05`, with
  a `drift_minutes` attribute (difference from Home Assistant's local time;
  positive = unit ahead).
- **Sync clock with Home Assistant** (button): sets the unit to Home
  Assistant's current local time and weekday.
- **Automatic clock sync** (switch, on by default): every 5 minutes the unit's
  clock is compared with Home Assistant's. If it's 2 or more minutes off (DST
  change, drift, power cut), it's corrected automatically. One minute of
  difference is normal, because the unit doesn't keep seconds.

If writing the clock fails, check that "Time/day change" isn't blocked on the
unit (blocked-functions register `0x0226`, bit 5).

---

## ⚠️ Upgrade notes

### Next release

- **A poll with no answer now fails at once** and entities show `unavailable`
  until the next poll that succeeds. Before, a timeout was mistaken for a
  refused block: the integration switched that block to one-by-one reads for
  good (until a restart), and each unanswered register cost another full
  timeout. Startup could hang for minutes, and later polls sent many more
  requests to an already slow link.
- **One-by-one reads are now used only when the unit refuses a block** (Modbus
  exception response), as intended.
- **New polling options** (polling interval, answer timeout, retries); see
  [Polling options](#polling-options). The defaults are the previous values,
  so nothing changes until you set them.

### 1.1.0

This release changes behavior for **already-configured devices**. Read before
upgrading:

- **Entity unique IDs are migrated automatically.** They now include the config
  entry ID so you can add more than one unit. Entity IDs, names, history and
  customizations are kept. **Downgrading** to 1.0.x afterwards creates
  duplicate entities. Back up first if you might roll back.
- **Device name** changes from "Sabiana RVU" to the name you entered during
  setup (default "Sabiana HRV"). A name you set yourself in the UI is kept, and
  entity IDs don't change.
- **Offline unit → entities show `unavailable`** (previously `unknown`). Update
  automations or templates that check for `unknown`.
- **Unit offline when Home Assistant starts → setup is retried**
  ("Retrying setup") instead of loading with empty entities.
- **Failed writes now raise an error.** Changing a number, select or switch, or
  pressing a button while the unit is unreachable or rejects the value shows an
  error and stops the automation. Use `continue_on_error: true` if you want
  the old behavior.
- **Polling reads registers in blocks** (fewer, larger Modbus requests). If
  your unit rejects a block, the integration falls back to one-by-one reads.
- **Rho1–Rho4 air density sensors** now show 3 decimals (e.g. `1.204` instead
  of `1.2`). The value itself is unchanged.
- Number entities on 0.1-resolution registers (RH limits, temperature
  setpoints and offsets) can now be set in 0.1 steps.
- New setups test the connection before the entry is created.
- Requires `pymodbus>=3.10.0` (bundled with every supported Home Assistant
  release).
- **New device clock entities:** *Device clock* (sensor), *Sync clock with Home
  Assistant* (button) and *Automatic clock sync* (switch). See
  [Device clock and daylight saving time](#-device-clock-and-daylight-saving-time).
- **Automatic clock sync is on by default.** Home Assistant now **writes the
  unit's clock** whenever it's 2 or more minutes off Home Assistant's local
  time, for example right after upgrading if the unit is still on summer time,
  and after every DST change. Turn the *Automatic clock sync* switch off to keep
  the unit's own time.

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







