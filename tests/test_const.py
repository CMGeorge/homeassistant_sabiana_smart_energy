"""Tests for const.py register definitions and device info (standalone version)."""

import ast
import os


def test_const_file_syntax():
    """Test that const.py has valid syntax."""
    const_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "sabiana_energy_smart",
        "const.py",
    )

    with open(const_path, encoding="utf-8") as f:
        content = f.read()

    try:
        ast.parse(content, const_path)
    except SyntaxError as e:
        raise AssertionError(f"Syntax error in const.py: {e}") from e


def test_const_has_required_definitions():
    """Test that const.py contains the expected definition structures."""
    const_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "sabiana_energy_smart",
        "const.py",
    )

    with open(const_path, encoding="utf-8") as f:
        content = f.read()

    # Check that required definition dictionaries are present
    required_definitions = [
        "SENSOR_DEFINITIONS_NEW",
        "REGISTER_DEFINITIONS",
        "SWITCH_DEFINITIONS",
        "BUTTON_DEFINITIONS",
        "SELECT_DEFINITIONS",
        "DIAGNOSTIC_DEFINITIONS",
    ]

    for definition in required_definitions:
        assert f"{definition} = " in content, f"Missing {definition} in const.py"


def test_const_domain_definition():
    """Test that DOMAIN is properly defined."""
    const_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "sabiana_energy_smart",
        "const.py",
    )

    with open(const_path, encoding="utf-8") as f:
        content = f.read()

    # Should have DOMAIN defined
    assert 'DOMAIN = "sabiana_energy_smart"' in content


def test_get_device_info_function_exists():
    """Test that get_device_info function is defined."""
    const_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "sabiana_energy_smart",
        "const.py",
    )

    with open(const_path, encoding="utf-8") as f:
        content = f.read()

    assert "def get_device_info(" in content


def test_register_definitions_structure():
    """Test register definitions have basic dictionary structure."""
    const_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "sabiana_energy_smart",
        "const.py",
    )

    with open(const_path, encoding="utf-8") as f:
        content = f.read()

    # Parse the AST to check structure
    tree = ast.parse(content)

    found_definitions = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id
                    if (
                        name.endswith("_DEFINITIONS")
                        or name == "SENSOR_DEFINITIONS_NEW"
                    ):
                        # Check that it's assigned a dictionary or list
                        if isinstance(node.value, (ast.Dict, ast.List)):
                            found_definitions[name] = True

    expected = [
        "SENSOR_DEFINITIONS_NEW",
        "REGISTER_DEFINITIONS",
        "SWITCH_DEFINITIONS",
        "BUTTON_DEFINITIONS",
        "SELECT_DEFINITIONS",
        "DIAGNOSTIC_DEFINITIONS",
    ]

    for def_name in expected:
        assert def_name in found_definitions, (
            f"Definition {def_name} not found as dictionary or list"
        )
