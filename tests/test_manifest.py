"""Tests for the manifest.json and basic configuration validation."""

import json
import os


def test_manifest_json_valid():
    """Test that manifest.json is valid and contains required fields."""
    manifest_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "sabiana_energy_smart",
        "manifest.json",
    )

    assert os.path.exists(manifest_path), "manifest.json file does not exist"

    with open(manifest_path) as f:
        manifest = json.load(f)

    # Required fields
    required_fields = ["domain", "name", "version", "requirements", "dependencies"]
    for field in required_fields:
        assert field in manifest, f"Required field '{field}' missing from manifest.json"

    # Validate specific values
    assert manifest["domain"] == "sabiana_energy_smart"
    assert manifest["name"] == "Sabiana Energy Smart"
    assert "pymodbus" in str(manifest["requirements"])
    assert "modbus" in manifest["dependencies"]
    assert manifest["config_flow"] is True
    assert manifest["integration_type"] == "hub"


def test_version_format():
    """Test that version follows semantic versioning."""
    manifest_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "sabiana_energy_smart",
        "manifest.json",
    )

    with open(manifest_path) as f:
        manifest = json.load(f)

    version = manifest["version"]
    # Basic semver format check (x.y.z)
    parts = version.split(".")
    assert len(parts) == 3, f"Version {version} does not follow semver format"
    for part in parts:
        assert part.isdigit(), f"Version part '{part}' is not numeric"
