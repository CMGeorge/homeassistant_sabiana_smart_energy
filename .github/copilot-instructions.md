# Sabiana Smart Energy Home Assistant Integration

This is a custom Home Assistant integration for monitoring and controlling Sabiana Smart Energy ventilation units via Modbus RTU or TCP. The integration provides sensors for air quality monitoring (CO₂, temperature, humidity, VOC, differential pressure), fan controls, operation modes, and diagnostic information.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Development Environment Setup
- Install Python 3.12+ (required for Home Assistant 2024.1+)
- Install development dependencies:
  ```bash
  python3 -m pip install ruff yamllint pymodbus>=3.0.0
  ```
- NEVER CANCEL: Package installation can take 2-5 minutes depending on dependencies.

### Linting and Code Quality 
- Run ruff linting (REQUIRED before committing):
  ```bash
  python3 -m ruff check .
  ```
  - Takes <1 second. NEVER CANCEL. Set timeout to 30+ seconds.
  - Fix issues with: `python3 -m ruff check . --fix`
  
- Run ruff formatting (REQUIRED before committing):
  ```bash
  python3 -m ruff format . --check
  ```
  - Takes <1 second. NEVER CANCEL. Set timeout to 30+ seconds.
  - Fix formatting with: `python3 -m ruff format .`

- Run YAML linting:
  ```bash
  yamllint .
  ```
  - Takes <1 second. NEVER CANCEL. Set timeout to 30+ seconds.

### Testing and Validation
- The integration does NOT have unit tests - it relies on Home Assistant integration testing
- Manual testing requires Home Assistant installation and Modbus device/simulator
- ALWAYS run linting and formatting before committing changes
- CI validation is done via GitHub Actions (.github/workflows/*)

## Repository Structure

### Key directories and files:
```
/
├── .github/
│   └── workflows/          # CI/CD pipelines (validate.yml, lint.yml, hassfest.yaml)
├── .devcontainer/          # VS Code dev container setup
├── custom_components/
│   └── sabiana_energy_smart/  # Main integration code
│       ├── __init__.py         # Integration setup and platform loading
│       ├── manifest.json       # Integration metadata
│       ├── config_flow.py      # Configuration UI flow
│       ├── const.py           # Constants and register definitions
│       ├── modbus_client.py   # Modbus communication layer
│       ├── modbus_coordinator.py  # Data coordination
│       ├── sensor.py          # Sensor entities
│       ├── binary_sensor.py   # Binary sensor entities  
│       ├── number.py          # Number entities (setpoints)
│       ├── select.py          # Select entities (modes)
│       ├── switch.py          # Switch entities
│       └── button.py          # Button entities
├── requirements.txt        # Python dependencies
├── .pylintrc              # Pylint configuration
├── .yamllint              # YAML linting rules
└── README.md              # Project documentation
```

### Important files to check after changes:
- `const.py` - Contains all Modbus register definitions and entity configurations
- `modbus_coordinator.py` - Handles data polling and caching logic
- `manifest.json` - Integration metadata and dependencies

## Validation

### ALWAYS run before committing:
1. **Code linting** (NEVER CANCEL - takes <1 second):
   ```bash
   python3 -m ruff check .
   python3 -m ruff format . --check
   ```

2. **YAML validation** (NEVER CANCEL - takes <1 second):
   ```bash
   yamllint .
   ```

3. **Integration structure validation** - Check imports, syntax, and manifest:
   ```bash
   python3 -c "
   import ast
   import sys
   import os
   import json
   import importlib.util
   
   def check_syntax(filepath):
       try:
           with open(filepath, 'r') as f:
               ast.parse(f.read(), filepath)
           return True
       except SyntaxError as e:
           print(f'Syntax error in {filepath}: {e}')
           return False
   
   def test_file_import(filepath):
       try:
           spec = importlib.util.spec_from_file_location('testmodule', filepath)
           return spec and spec.loader
       except Exception as e:
           print(f'Import test failed for {filepath}: {e}')
           return False
   
   def validate_manifest():
       try:
           with open('custom_components/sabiana_energy_smart/manifest.json', 'r') as f:
               manifest = json.load(f)
           required_fields = ['domain', 'name', 'version', 'requirements', 'dependencies']
           missing_fields = [field for field in required_fields if field not in manifest]
           if missing_fields:
               print(f'Missing required fields in manifest.json: {missing_fields}')
               return False
           print(f'✓ manifest.json valid (domain: {manifest[\"domain\"]}, version: {manifest[\"version\"]})')
           return True
       except Exception as e:
           print(f'Error reading manifest.json: {e}')
           return False
   
   success = True
   python_files = []
   
   # Check all Python files
   for root, dirs, files in os.walk('custom_components'):
       for file in files:
           if file.endswith('.py'):
               filepath = os.path.join(root, file)
               python_files.append(filepath)
               if not check_syntax(filepath) or not test_file_import(filepath):
                   success = False
   
   # Validate manifest
   if not validate_manifest():
       success = False
   
   if success:
       print(f'✓ All {len(python_files)} Python files and manifest are valid')
   else:
       print('✗ Validation failed')
   
   sys.exit(0 if success else 1)
   "
   ```
   - Takes <1 second. NEVER CANCEL. Set timeout to 30+ seconds.

### Manual Testing Scenarios:
Since this integration requires Home Assistant and Modbus hardware/simulation, most functional testing must be done in a live Home Assistant environment. However, you can validate code changes with these scenarios:

1. **Code Structure Validation** (can be done without Home Assistant):
   - Run the comprehensive validation script to ensure all imports resolve
   - Verify manifest.json contains correct domain and dependencies  
   - Check that all entity classes follow Home Assistant conventions
   - Validate Modbus register definitions in const.py are syntactically correct

2. **Integration Loading Test** (requires Home Assistant development environment):
   - Copy integration to Home Assistant custom_components folder
   - Start Home Assistant and check for loading errors in logs
   - Verify integration appears in Integrations UI
   - Test configuration flow without actual device (should show connection errors gracefully)

3. **Modbus Communication Test** (requires device or simulator):
   - Use Modbus TCP simulator or real device for testing
   - Configure integration with correct IP/port
   - Verify entities are created and show reasonable values
   - Test control entities (numbers, switches) can write to device
   - Monitor polling performance and connection stability

4. **Entity Behavior Test** (requires Home Assistant + device):
   - Check sensor values update at expected intervals (3 seconds default)
   - Verify binary sensor inversion flag (0x0104) affects sensor states correctly
   - Test diagnostic vs config entity categories are assigned properly
   - Confirm unique IDs and friendly names follow conventions

**Minimal validation for code changes**: Always run steps 1 and verify step 2 configuration flow loads without syntax errors.

## CI/CD Workflows

### GitHub Actions workflows (NEVER CANCEL - timing varies):

1. **Validate workflow** (`.github/workflows/validate.yml`):
   - Runs hassfest validation (Home Assistant integration checker)
   - Runs HACS validation  
   - Takes 2-5 minutes. NEVER CANCEL. Set timeout to 10+ minutes.

2. **Lint workflow** (`.github/workflows/lint.yml`):
   - Runs ruff check and format validation
   - Takes 1-3 minutes. NEVER CANCEL. Set timeout to 5+ minutes.

3. **Hassfest workflow** (`.github/workflows/hassfest.yaml`):
   - Home Assistant specific validation
   - Takes 1-2 minutes. NEVER CANCEL. Set timeout to 5+ minutes.

## Development Container

The repository includes a VS Code devcontainer setup:
- Uses Python 3.12-bullseye base image  
- Expects poetry for dependency management (note: current repo uses pip)
- Includes extensions for Python development and GitHub Actions

To use the devcontainer:
1. Open the repository in VS Code
2. Install the "Dev Containers" extension
3. Run "Dev Containers: Reopen in Container" from the command palette
4. NEVER CANCEL: Container build takes 3-10 minutes depending on network speed

## Common Development Tasks

### Full development workflow from fresh clone:
```bash
# 1. Install dependencies (NEVER CANCEL - takes 1-3 minutes)
python3 -m pip install ruff yamllint pymodbus>=3.0.0

# 2. Run full validation (takes <1 second)
python3 -m ruff check .
python3 -m ruff format . --check
yamllint .

# 3. Fix any issues
python3 -m ruff check . --fix
python3 -m ruff format .

# 4. Run comprehensive validation
python3 -c "[validation script from above]"
```

### Adding new Modbus registers:
1. Update `SENSOR_DEFINITIONS_NEW`, `NUMBER_DEFINITIONS`, etc. in `const.py`
2. Follow existing patterns for scaling, precision, and entity categories
3. Test register communication manually if possible
4. Update documentation if adding new entity types

### Modifying communication logic:
1. Check `modbus_client.py` for connection handling
2. Update `modbus_coordinator.py` for polling logic
3. Address registration system is in coordinator - entities register their addresses
4. Default polling interval is 3 seconds (configurable)

### Entity modifications:
1. Each platform file (sensor.py, number.py, etc.) handles entity setup
2. Entities inherit from appropriate Home Assistant base classes
3. Binary sensors support global inversion flag (0x0104 register)
4. Follow Home Assistant entity conventions for unique IDs and naming

## Troubleshooting

### Common issues:
1. **Import errors**: Integration requires Home Assistant runtime - static checks only work for syntax
2. **Linting failures**: Run `ruff check . --fix` to auto-fix most issues
3. **YAML lint errors**: Check indentation and line endings in workflow files
4. **CI failures**: Usually due to linting issues or manifest validation errors

### Development environment issues:
1. **Poetry vs pip**: Devcontainer expects poetry but repo uses pip - install dependencies manually
2. **Python version**: Ensure Python 3.12+ for latest Home Assistant compatibility  
3. **Home Assistant testing**: Requires full HA installation - use development instance for testing

## Performance Notes

- **Build times**: No compilation required - Python interpretation only
- **Linting**: <1 second for full codebase (13 Python files)
- **CI validation**: 2-5 minutes total across all workflows
- **Integration startup**: Depends on Modbus device response time
- **Polling impact**: 3-second default interval, configurable per installation
- **Full validation suite**: <1 second for complete syntax, import, and manifest checking

NEVER CANCEL long-running operations. If commands appear hung, wait at least 60 seconds before investigating alternatives.
