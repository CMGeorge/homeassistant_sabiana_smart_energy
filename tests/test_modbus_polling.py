"""Tests for Modbus polling: timeouts versus refused reads, and polling options."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from homeassistant.helpers.update_coordinator import UpdateFailed
from pymodbus.exceptions import ModbusIOException
import pytest

from custom_components.sabiana_energy_smart.config_flow import build_options_schema
from custom_components.sabiana_energy_smart.const import (
    CONF_RETRIES,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_RETRIES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
)
from custom_components.sabiana_energy_smart.modbus_client import (
    SabianaCommunicationError,
    SabianaModbusClient,
)
from custom_components.sabiana_energy_smart.modbus_coordinator import (
    SabianaModbusCoordinator,
)

ENTRY_DATA = {"host": "192.168.1.100", "port": 502, "slave": 1}


def _ok(registers: list[int]) -> SimpleNamespace:
    return SimpleNamespace(isError=lambda: False, registers=registers)


def _refused() -> SimpleNamespace:
    # What pymodbus returns for a Modbus exception response.
    return SimpleNamespace(isError=lambda: True, registers=[])


def _client_with(read: AsyncMock) -> SabianaModbusClient:
    client = SabianaModbusClient("192.168.1.100", 502)
    client.client = MagicMock(connected=True)
    client.client.read_holding_registers = read
    return client


# --- Client ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_read_block_returns_registers():
    client = _client_with(AsyncMock(return_value=_ok([1, 2])))
    assert await client.read_block(0x0100, count=2) == [1, 2]


@pytest.mark.asyncio
async def test_read_block_refused_returns_none():
    client = _client_with(AsyncMock(return_value=_refused()))
    assert await client.read_block(0x0100) is None


@pytest.mark.asyncio
async def test_read_block_timeout_raises():
    client = _client_with(
        AsyncMock(side_effect=ModbusIOException("No response received"))
    )
    with pytest.raises(SabianaCommunicationError):
        await client.read_block(0x0100)


@pytest.mark.asyncio
async def test_read_block_not_connected_raises():
    client = SabianaModbusClient("192.168.1.100", 502)
    client.ensure_connected = AsyncMock(return_value=False)
    with pytest.raises(SabianaCommunicationError):
        await client.read_block(0x0100)


@pytest.mark.asyncio
async def test_read_register_swallows_timeout():
    client = _client_with(
        AsyncMock(side_effect=ModbusIOException("No response received"))
    )
    assert await client.read_register(0x0100) is None


@pytest.mark.asyncio
async def test_client_passes_timeout_and_retries(monkeypatch):
    created = {}

    class FakeTcpClient:
        def __init__(self, host, **kwargs):
            created.update(kwargs, host=host)
            self.connected = True

    monkeypatch.setattr(
        "custom_components.sabiana_energy_smart.modbus_client.AsyncModbusTcpClient",
        FakeTcpClient,
    )
    client = SabianaModbusClient("10.0.0.5", 8899, timeout=5.0, retries=1)

    assert await client.ensure_connected()
    assert created == {"host": "10.0.0.5", "port": 8899, "timeout": 5.0, "retries": 1}


# --- Coordinator -------------------------------------------------------------


def _coordinator(options: dict | None = None) -> SabianaModbusCoordinator:
    entry = MagicMock(options=options or {})
    coordinator = SabianaModbusCoordinator(MagicMock(), ENTRY_DATA, entry)
    for address in (0x0100, 0x0101, 0x0102):
        coordinator.register_address(address)
    coordinator._client.ensure_connected = AsyncMock(return_value=True)
    return coordinator


@pytest.mark.asyncio
async def test_poll_reads_block():
    coordinator = _coordinator()
    coordinator._client.read_block = AsyncMock(return_value=[10, 11, 12])

    data = await coordinator._async_update_data()

    assert data == {0x0100: 10, 0x0101: 11, 0x0102: 12}
    coordinator._client.read_block.assert_awaited_once_with(
        address=0x0100, count=3, slave=1
    )


@pytest.mark.asyncio
async def test_timeout_fails_poll_without_splitting_block():
    """A timeout must not switch the block to one-by-one reads (the bug)."""
    coordinator = _coordinator()
    coordinator._client.read_block = AsyncMock(
        side_effect=SabianaCommunicationError("No response received")
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    assert coordinator._split_blocks == set()
    # One request, then the poll stops: no walk over every register.
    assert coordinator._client.read_block.await_count == 1

    # Next poll, the unit answers again: still one block request.
    coordinator._client.read_block = AsyncMock(return_value=[10, 11, 12])
    assert await coordinator._async_update_data() == {
        0x0100: 10,
        0x0101: 11,
        0x0102: 12,
    }
    coordinator._client.read_block.assert_awaited_once()


@pytest.mark.asyncio
async def test_refused_block_falls_back_to_single_reads():
    coordinator = _coordinator()
    # Block refused, then 0x0100 ok, 0x0101 refused (unmapped), 0x0102 ok.
    coordinator._client.read_block = AsyncMock(side_effect=[None, [10], None, [12]])

    data = await coordinator._async_update_data()

    assert data == {0x0100: 10, 0x0101: None, 0x0102: 12}
    assert coordinator._split_blocks == {(0x0100, 3)}


@pytest.mark.asyncio
async def test_timeout_during_single_reads_fails_poll():
    coordinator = _coordinator()
    coordinator._split_blocks.add((0x0100, 3))
    coordinator._client.read_block = AsyncMock(
        side_effect=[[10], SabianaCommunicationError("No response received")]
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    assert coordinator._client.read_block.await_count == 2


def test_default_options_keep_previous_behavior():
    coordinator = _coordinator()
    assert coordinator.update_interval == timedelta(seconds=DEFAULT_SCAN_INTERVAL)
    assert coordinator._client.timeout == DEFAULT_TIMEOUT
    assert coordinator._client.retries == DEFAULT_RETRIES
    assert (DEFAULT_SCAN_INTERVAL, DEFAULT_TIMEOUT, DEFAULT_RETRIES) == (3, 3.0, 3)


def test_options_are_applied():
    coordinator = _coordinator(
        {CONF_SCAN_INTERVAL: 15, CONF_TIMEOUT: 5.0, CONF_RETRIES: 1}
    )
    assert coordinator.update_interval == timedelta(seconds=15)
    assert coordinator._client.timeout == 5.0
    assert coordinator._client.retries == 1


# --- Options schema ----------------------------------------------------------


def test_options_schema_defaults_and_coercion():
    schema = build_options_schema({})
    assert schema({}) == {
        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        CONF_TIMEOUT: DEFAULT_TIMEOUT,
        CONF_RETRIES: DEFAULT_RETRIES,
    }
    assert schema({CONF_SCAN_INTERVAL: "10", CONF_TIMEOUT: "4", CONF_RETRIES: "1"}) == {
        CONF_SCAN_INTERVAL: 10,
        CONF_TIMEOUT: 4.0,
        CONF_RETRIES: 1,
    }


@pytest.mark.parametrize(
    "bad",
    [
        {CONF_SCAN_INTERVAL: 0},
        {CONF_TIMEOUT: 0.1},
        {CONF_RETRIES: -1},
        {CONF_RETRIES: 11},
    ],
)
def test_options_schema_rejects_out_of_range(bad):
    import voluptuous as vol

    with pytest.raises(vol.Invalid):
        build_options_schema({})(bad)


def test_options_schema_prefills_current_values():
    schema = build_options_schema(
        {CONF_SCAN_INTERVAL: 15, CONF_TIMEOUT: 5.0, CONF_RETRIES: 1}
    )
    assert schema({}) == {CONF_SCAN_INTERVAL: 15, CONF_TIMEOUT: 5.0, CONF_RETRIES: 1}
