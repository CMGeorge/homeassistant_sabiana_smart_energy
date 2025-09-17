# Sabiana Smart Energy Integration for Home Assistant

This is a custom Home Assistant integration that enables communication with Sabiana Smart Energy heat recovery units over Modbus (RTU or TCP). The integration provides access to diagnostic data, environmental sensors, fan status, and control over various operational parameters.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Setup
- Install Python 3.12+ (Python 3.13+ required for latest Home Assistant versions)
- Install basic dependencies: `pip install ruff pymodbus`
- **NOTE**: Full Home Assistant installation may fail due to network timeouts. Use dev container or manual setup when needed.

### Linting and Code Quality
- **ALWAYS** run these commands before committing changes:
  - `python3 -m ruff check . --fix` -- takes ~0.03 seconds. NEVER CANCEL.
  - `python3 -m ruff format .` -- takes ~0.03 seconds. NEVER CANCEL.
- Fix any remaining linting errors manually (e.g., unused imports that auto-fix cannot handle)
- Check Python syntax: `find . -name "*.py" -exec python3 -m py_compile {} \;` -- takes ~1 second. NEVER CANCEL.
- **NOTE**: Some unused imports may need manual removal (ruff will identify them)

### Development Container (Recommended)
- Use the provided devcontainer configuration for consistent development environment
- Container uses Python 3.12-bullseye with Poetry for dependency management
- Run: `poetry update && poetry run pre-commit install` in container

### Repository Structure
- `custom_components/sabiana_energy_smart/` -- Main integration code
- `.github/workflows/` -- CI/CD pipelines (validate, lint, hassfest)
- `config/` -- Sample Home Assistant configuration
- `requirements.txt` -- Base dependencies (homeassistant, pymodbus)

## Validation

### CI/CD Validation
The repository has GitHub Actions workflows that **MUST PASS**:
- **validate.yml**: Runs hassfest and HACS validation -- takes ~30 seconds. NEVER CANCEL.
- **lint.yml**: Runs ruff check and format validation -- takes ~15 seconds. NEVER CANCEL.
- **hassfest.yaml**: Home Assistant integration validation -- takes ~20 seconds. NEVER CANCEL.

### Manual Testing
- **ALWAYS** run the linting commands locally before pushing
- Compile all Python files to check for syntax errors
- **IMPORTANT**: The integration requires Home Assistant runtime for full testing
- Test the integration by copying to `~/.homeassistant/custom_components/` as shown in README
- **VALIDATION SCENARIO**: After making changes, test the complete workflow:
  1. Copy integration: `cp -r custom_components/sabiana_energy_smart ~/.homeassistant/custom_components/`
  2. The integration should load without import errors in Home Assistant
  3. Modbus configuration should be available in Settings → Devices & Services
- **NO AUTOMATED TESTS**: This repository has no test framework - manual validation required

### Code Quality Requirements
- All Python imports must be used (ruff will catch unused imports)
- Code must be formatted with ruff
- No syntax errors allowed
- Follow Home Assistant integration standards

## Common Tasks

### Making Code Changes
1. **ALWAYS** run linting first: `python3 -m ruff check . --fix && python3 -m ruff format .`
2. Check compilation: `find . -name "*.py" -exec python3 -m py_compile {} \;`
3. Test import of main module (will fail without Home Assistant but should show import path issues)
4. Commit changes only after passing all checks

### Key Files to Understand
- `custom_components/sabiana_energy_smart/const.py` -- Register definitions and constants
- `custom_components/sabiana_energy_smart/manifest.json` -- Integration metadata
- `custom_components/sabiana_energy_smart/__init__.py` -- Integration setup
- `custom_components/sabiana_energy_smart/modbus_coordinator.py` -- Data coordinator
- `custom_components/sabiana_energy_smart/sensor.py` -- Sensor entities
- Platform files: `binary_sensor.py`, `button.py`, `number.py`, `select.py`, `switch.py`

### Configuration Files
- `.pylintrc` -- Pylint configuration (disabled in favor of ruff)
- `.yamllint` -- YAML linting rules for workflows
- `hacs.json` -- HACS integration metadata
- `info.md` -- Integration description for HACS

## Important Notes

### Python Version Compatibility
- **CRITICAL**: Home Assistant 2025.x requires Python 3.13+
- This environment uses Python 3.12, which limits compatible HA versions
- For full development, use the devcontainer or upgrade Python version
- Basic linting and validation can be done with Python 3.12

### Network Issues
- **WARNING**: pip install for Home Assistant may timeout due to network restrictions
- Install only essential packages: `pip install ruff pymodbus`
- Use devcontainer for full Home Assistant development setup

### Home Assistant Integration Development
- This is a **custom integration** that extends Home Assistant
- It provides multiple platforms: sensor, binary_sensor, switch, number, select, button
- Uses Modbus communication (TCP/RTU) via pymodbus library
- Register definitions in `const.py` map Modbus addresses to Home Assistant entities

### Typical Development Workflow
1. Make code changes to integration files
2. Run `python3 -m ruff check . --fix` to fix linting issues
3. Run `python3 -m ruff format .` to format code
4. Verify compilation with `find . -name "*.py" -exec python3 -m py_compile {} \;`
5. Test integration by copying to Home Assistant custom_components directory
6. Commit changes after validation

### Troubleshooting
- **Linting errors**: Fix manually or use `--fix` flag
- **Import errors**: Usually indicates missing Home Assistant environment
- **Compilation errors**: Check Python syntax and imports
- **CI failures**: Check GitHub Actions logs for specific errors
- **Known Issues**: 
  - `pip install homeassistant` may timeout due to network restrictions
  - Some unused import warnings require manual fixes
  - Full integration testing requires Home Assistant runtime environment

### Expected Build/Test Times
- Ruff linting: ~0.03 seconds
- Ruff formatting: ~0.03 seconds  
- Python compilation check: ~1 second
- GitHub Actions workflows: 15-30 seconds each
- **NEVER CANCEL** any of these operations - they complete quickly

## Repository Quick Reference

### Directory Structure
```
.
├── README.md                           # Installation and usage guide
├── requirements.txt                    # Python dependencies  
├── hacs.json                          # HACS metadata
├── info.md                            # Integration description
├── config/configuration.yaml          # Sample HA configuration
├── .github/workflows/                 # CI/CD workflows
├── .devcontainer/                     # Development container config
└── custom_components/sabiana_energy_smart/  # Integration source code
    ├── __init__.py                    # Integration setup
    ├── manifest.json                  # Integration metadata
    ├── const.py                       # Constants and register definitions
    ├── config_flow.py                 # Configuration UI
    ├── modbus_coordinator.py          # Data coordinator
    ├── modbus_client.py               # Modbus communication
    ├── sensor.py                      # Sensor platform
    ├── binary_sensor.py               # Binary sensor platform
    ├── switch.py                      # Switch platform
    ├── number.py                      # Number platform
    ├── select.py                      # Select platform
    └── button.py                      # Button platform
```

### Common Commands Output
```bash
# Repository root files
$ ls -la
.devcontainer/    .github/    .gitignore    .pylintrc    .yamllint
LICENSE    README.md    config/    custom_components/    hacs.json
info.md    requirements.txt

# Python files count
$ find . -name "*.py" | wc -l
13

# Integration platforms
$ ls custom_components/sabiana_energy_smart/
__init__.py    binary_sensor.py    button.py    config_flow.py    const.py
helpers.py    icon.png    images/    info_sensor.py    manifest.json
modbus_client.py    modbus_coordinator.py    number.py    select.py
sensor.py    switch.py
```