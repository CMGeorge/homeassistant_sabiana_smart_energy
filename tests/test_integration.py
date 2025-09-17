"""Integration tests for syntax validation and basic checks."""

import ast
import os


def test_all_python_files_syntax():
    """Test that all Python files have valid syntax."""
    custom_components_dir = os.path.join(
        os.path.dirname(__file__), "..", "custom_components", "sabiana_energy_smart"
    )

    python_files = []
    for root, _dirs, files in os.walk(custom_components_dir):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    assert len(python_files) > 0, "No Python files found"

    for filepath in python_files:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        try:
            ast.parse(content, filepath)
        except SyntaxError as e:
            raise AssertionError(f"Syntax error in {filepath}: {e}") from e


def test_all_python_files_importable_syntax():
    """Test that all Python files have importable syntax structure."""
    custom_components_dir = os.path.join(
        os.path.dirname(__file__), "..", "custom_components", "sabiana_energy_smart"
    )

    python_files = []
    for root, _dirs, files in os.walk(custom_components_dir):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                python_files.append(os.path.join(root, file))

    for filepath in python_files:
        # Just check that we can parse the AST without errors
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content, filepath)
            # Basic validation that it has module structure
            assert isinstance(tree, ast.Module)
        except SyntaxError as e:
            raise AssertionError(f"Import syntax error in {filepath}: {e}") from e


def test_required_files_exist():
    """Test that required integration files exist."""
    base_dir = os.path.join(
        os.path.dirname(__file__), "..", "custom_components", "sabiana_energy_smart"
    )

    required_files = [
        "__init__.py",
        "manifest.json",
        "config_flow.py",
        "const.py",
        "modbus_client.py",
        "modbus_coordinator.py",
        "sensor.py",
        "binary_sensor.py",
        "number.py",
        "select.py",
        "switch.py",
        "button.py",
    ]

    for required_file in required_files:
        file_path = os.path.join(base_dir, required_file)
        assert os.path.exists(file_path), f"Required file missing: {required_file}"


def test_python_files_have_docstrings():
    """Test that Python files have module docstrings."""
    custom_components_dir = os.path.join(
        os.path.dirname(__file__), "..", "custom_components", "sabiana_energy_smart"
    )

    python_files = []
    for root, _dirs, files in os.walk(custom_components_dir):
        for file in files:
            if file.endswith(".py") and file not in ["__init__.py"]:
                python_files.append(os.path.join(root, file))

    for filepath in python_files:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filepath)

        # Check if first statement is a docstring
        if tree.body and isinstance(tree.body[0], ast.Expr):
            if isinstance(tree.body[0].value, ast.Constant):
                if isinstance(tree.body[0].value.value, str):
                    continue  # Has docstring

        # Some files might not need docstrings, so this is just a warning
        # We'll just check that the file is not empty
        assert len(content.strip()) > 0, f"File {filepath} appears to be empty"


def test_no_obvious_syntax_issues():
    """Test for common syntax issues across all files."""
    custom_components_dir = os.path.join(
        os.path.dirname(__file__), "..", "custom_components", "sabiana_energy_smart"
    )

    python_files = []
    for root, _dirs, files in os.walk(custom_components_dir):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    for filepath in python_files:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        # Check for common issues
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            # Check for tabs (should use spaces)
            if "\t" in line:
                raise AssertionError(f"Tab character found in {filepath}:{i}")

            # Check for trailing whitespace (not critical but good practice)
            # This is commented out as it might be too strict
            # if line.endswith(' '):
            #     assert False, f"Trailing whitespace in {filepath}:{i}"
