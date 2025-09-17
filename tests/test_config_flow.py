"""Tests for config flow without requiring Home Assistant runtime."""

import ast
import os

import pytest
import voluptuous as vol


def test_config_flow_file_syntax():
    """Test that config_flow.py has valid syntax."""
    config_flow_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "sabiana_energy_smart",
        "config_flow.py"
    )

    with open(config_flow_path, encoding='utf-8') as f:
        content = f.read()

    try:
        ast.parse(content, config_flow_path)
    except SyntaxError as e:
        raise AssertionError(f"Syntax error in config_flow.py: {e}") from e


def test_config_flow_class_defined():
    """Test that config flow class is defined."""
    config_flow_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "sabiana_energy_smart",
        "config_flow.py"
    )

    with open(config_flow_path, encoding='utf-8') as f:
        content = f.read()

    assert "class MyModbusDeviceConfigFlow" in content
    assert "VERSION = 1" in content


def test_config_schema_validation():
    """Test that the config schema validates expected input."""
    # Test basic voluptuous validation patterns similar to config flow

    # Simple schema similar to what's used in the config flow
    test_schema = vol.Schema({
        vol.Required("name", default="Sabiana HRV"): str,
        vol.Required("host"): str,
        vol.Required("port", default=502): int,
        vol.Required("slave", default=1): int,
    })

    # Test valid input
    valid_data = {
        "name": "Test Sabiana",
        "host": "192.168.1.100",
        "port": 502,
        "slave": 1,
    }

    validated = test_schema(valid_data)
    assert validated["name"] == "Test Sabiana"
    assert validated["host"] == "192.168.1.100"
    assert validated["port"] == 502
    assert validated["slave"] == 1

    # Test invalid input - missing required field
    with pytest.raises(vol.MultipleInvalid):
        test_schema({
            "name": "Test",
            # Missing host
            "port": 502,
            "slave": 1,
        })

    # Test invalid input - wrong type
    with pytest.raises(vol.Invalid):
        test_schema({
            "name": "Test",
            "host": "192.168.1.100",
            "port": "not_a_number",  # Should be int
            "slave": 1,
        })


def test_config_flow_imports():
    """Test that config flow file has expected imports."""
    config_flow_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "sabiana_energy_smart",
        "config_flow.py"
    )

    with open(config_flow_path, encoding='utf-8') as f:
        content = f.read()

    # Check for key imports
    assert "import voluptuous as vol" in content
    assert "from homeassistant import config_entries" in content
    assert "from .const import" in content
