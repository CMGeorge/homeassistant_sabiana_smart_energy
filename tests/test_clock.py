"""Tests for the device clock helpers and sync logic (registers 0x0800/0x0801)."""

from datetime import datetime
import importlib.util
from pathlib import Path

import pytest

HELPERS_PATH = (
    Path(__file__).parent.parent
    / "custom_components"
    / "sabiana_energy_smart"
    / "helpers.py"
)
_spec = importlib.util.spec_from_file_location("sabiana_helpers", HELPERS_PATH)
helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(helpers)


def test_encode_device_clock():
    # 14:05 -> MSB 14 (0x0E), LSB 5; Wednesday = 3
    assert helpers.encode_device_clock(14, 5, 3) == [0x0E05, 3]
    assert helpers.encode_device_clock(0, 0, 1) == [0x0000, 1]
    assert helpers.encode_device_clock(23, 59, 7) == [0x173B, 7]


@pytest.mark.parametrize(
    ("hour", "minute", "day"), [(24, 0, 1), (0, 60, 1), (0, 0, 0), (0, 0, 8)]
)
def test_encode_device_clock_rejects_invalid(hour, minute, day):
    with pytest.raises(ValueError):
        helpers.encode_device_clock(hour, minute, day)


def test_decode_device_clock():
    assert helpers.decode_device_clock(0x0E05, 3) == (3, 14, 5)
    assert helpers.decode_device_clock(None, 3) is None
    assert helpers.decode_device_clock(0x0E05, None) is None
    assert helpers.decode_device_clock(0x1800, 1) is None  # hour 24
    assert helpers.decode_device_clock(0x003C, 1) is None  # minute 60
    assert helpers.decode_device_clock(0x0E05, 0) is None  # day 0
    assert helpers.decode_device_clock(0xFFFF, 0xFFFF) is None


def test_encode_decode_roundtrip():
    for day in range(1, 8):
        for hour in (0, 3, 12, 23):
            for minute in (0, 30, 59):
                raw = helpers.encode_device_clock(hour, minute, day)
                assert helpers.decode_device_clock(*raw) == (day, hour, minute)


def test_clock_drift_dst_end():
    # After DST ends the device is one hour ahead of local time
    assert helpers.clock_drift_minutes((7, 4, 10), (7, 3, 10)) == 60


def test_clock_drift_dst_start():
    # After DST starts the device is one hour behind
    assert helpers.clock_drift_minutes((7, 3, 10), (7, 4, 10)) == -60


def test_clock_drift_wraps_over_week_boundary():
    # Device Mon 00:01, HA Sun 23:59 -> device 2 minutes ahead
    assert helpers.clock_drift_minutes((1, 0, 1), (7, 23, 59)) == 2
    assert helpers.clock_drift_minutes((7, 23, 59), (1, 0, 1)) == -2


def test_clock_drift_wrong_weekday():
    assert helpers.clock_drift_minutes((2, 10, 0), (1, 10, 0)) == 24 * 60


def test_clock_drift_in_sync():
    assert helpers.clock_drift_minutes((3, 14, 5), (3, 14, 5)) == 0


def test_format_device_clock():
    assert helpers.format_device_clock((1, 9, 5)) == "Mon 09:05"
    assert helpers.format_device_clock((7, 23, 59)) == "Sun 23:59"


# --- Coordinator logic (needs Home Assistant installed) -----------------------


class _FakeClient:
    def __init__(self, ok=True):
        self.ok = ok
        self.writes = []

    async def write_registers(self, address, values, slave=1):
        self.writes.append((address, values, slave))
        return self.ok


def _make_coordinator(device_time_raw, device_day_raw, client):
    pytest.importorskip("homeassistant")
    from custom_components.sabiana_energy_smart.modbus_coordinator import (
        SabianaModbusCoordinator,
    )

    coordinator = SabianaModbusCoordinator.__new__(SabianaModbusCoordinator)
    coordinator._client = client
    coordinator._slave = 1
    coordinator.clock_auto_sync = True
    coordinator.data = {0x0800: device_time_raw, 0x0801: device_day_raw}
    coordinator._apply_written_values = lambda address, values: None
    return coordinator


# Sunday 2026-10-25 03:10 (local) — just after DST ended in Europe
NOW = datetime(2026, 10, 25, 3, 10, 2)


@pytest.mark.asyncio
async def test_check_clock_syncs_after_dst_change():
    client = _FakeClient()
    coordinator = _make_coordinator(0x040A, 7, client)  # device: Sun 04:10
    assert coordinator.clock_drift(NOW) == 60

    await coordinator.async_check_clock(NOW)

    assert client.writes == [(0x0800, [0x030A, 7], 1)]


@pytest.mark.asyncio
async def test_check_clock_ignores_one_minute_difference():
    client = _FakeClient()
    coordinator = _make_coordinator(0x0309, 7, client)  # device: Sun 03:09

    await coordinator.async_check_clock(NOW)

    assert client.writes == []


@pytest.mark.asyncio
@pytest.mark.parametrize("auto_sync", [False, None])
async def test_check_clock_respects_switch(auto_sync):
    client = _FakeClient()
    coordinator = _make_coordinator(0x040A, 7, client)
    coordinator.clock_auto_sync = auto_sync

    await coordinator.async_check_clock(NOW)

    assert client.writes == []


@pytest.mark.asyncio
async def test_check_clock_skips_unknown_device_clock():
    client = _FakeClient()
    coordinator = _make_coordinator(None, None, client)

    await coordinator.async_check_clock(NOW)

    assert client.writes == []


@pytest.mark.asyncio
async def test_sync_clock_reports_failure():
    client = _FakeClient(ok=False)
    coordinator = _make_coordinator(0x040A, 7, client)

    assert await coordinator.async_sync_clock(NOW) is False
