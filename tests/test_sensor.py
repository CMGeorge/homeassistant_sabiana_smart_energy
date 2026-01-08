"""Tests for sensor.py signed integer handling."""

import ast
import os


def test_sensor_file_syntax():
    """Test that sensor.py has valid syntax."""
    sensor_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "sabiana_energy_smart",
        "sensor.py",
    )

    with open(sensor_path, encoding="utf-8") as f:
        content = f.read()

    try:
        ast.parse(content, sensor_path)
    except SyntaxError as e:
        raise AssertionError(f"Syntax error in sensor.py: {e}") from e


def test_signed_integer_conversion_logic():
    """Test the signed integer conversion logic matches expected behavior."""

    # This is the conversion logic used in sensor.py
    def convert_to_signed(raw):
        """Convert unsigned 16-bit int to signed 16-bit int."""
        if raw > 0x7FFF:
            return raw - 0x10000
        return raw

    # Test negative temperature: -3.5°C = -35 raw value
    # In unsigned representation: 65501
    unsigned_neg = 65501
    signed_neg = convert_to_signed(unsigned_neg)
    assert signed_neg == -35, f"Expected -35, got {signed_neg}"
    temp_neg = signed_neg * 0.1
    assert temp_neg == -3.5, f"Expected -3.5°C, got {temp_neg}°C"

    # Test positive temperature: 23.5°C = 235 raw value
    unsigned_pos = 235
    signed_pos = convert_to_signed(unsigned_pos)
    assert signed_pos == 235, f"Expected 235, got {signed_pos}"
    temp_pos = signed_pos * 0.1
    assert temp_pos == 23.5, f"Expected 23.5°C, got {temp_pos}°C"

    # Test edge cases
    # Test 0°C
    assert convert_to_signed(0) == 0
    # Test max positive (32767 / 10 = 3276.7°C)
    assert convert_to_signed(0x7FFF) == 32767
    # Test max negative (-32768 / 10 = -3276.8°C)
    assert convert_to_signed(0x8000) == -32768
    # Test -0.1°C (raw = -1)
    assert convert_to_signed(65535) == -1


def test_temperature_sensors_have_int16_type():
    """Test that all temperature probe sensors have int16 type defined."""
    const_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "sabiana_energy_smart",
        "const.py",
    )

    with open(const_path, encoding="utf-8") as f:
        content = f.read()

    # Check that temperature probes have int16 type
    temp_probes = [
        "probe_temp1",
        "probe_temp2",
        "probe_temp3",
        "probe_temp4",
    ]

    for probe in temp_probes:
        # Find the probe definition block
        probe_index = content.find(f'"key": "{probe}"')
        assert probe_index != -1, f"Probe {probe} not found in const.py"

        # Find the next closing brace after this probe
        next_section = content[probe_index : probe_index + 500]

        # Check if int16 type is defined
        assert (
            '"type": "int16"' in next_section
        ), f"Probe {probe} does not have int16 type defined"


def test_sensor_handles_int16_type():
    """Test that sensor.py code handles int16 and sig16 types."""
    sensor_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "sabiana_energy_smart",
        "sensor.py",
    )

    with open(sensor_path, encoding="utf-8") as f:
        content = f.read()

    # Check that the code handles int16 and sig16 types
    assert 'if self._type in ("int16", "sig16")' in content, (
        "sensor.py does not check for int16/sig16 types"
    )

    # Check that it performs two's complement conversion
    assert "if raw > 0x7FFF:" in content, (
        "sensor.py does not check for negative values"
    )
    assert "raw = raw - 0x10000" in content, (
        "sensor.py does not perform two's complement conversion"
    )
