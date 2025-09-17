"""Test configuration and pytest fixtures for Sabiana Energy Smart integration."""

import pytest


@pytest.fixture
def mock_entry_data():
    """Mock config entry data."""
    return {
        "host": "192.168.1.100",
        "port": 502,
        "slave": 1,
        "name": "Test Sabiana HRV",
    }


@pytest.fixture
def mock_sabiana_data():
    """Mock Sabiana device data for testing."""
    return {
        0x0101: 23.5,  # Temperature
        0x0102: 45.2,  # Humidity
        0x0103: 850,  # CO2
        0x0104: 0,  # Binary inversion flag
        0x0105: 1,  # Filter status
        0x0201: 250,  # Fan speed setpoint
        0x0211: 350,  # Airflow
    }
