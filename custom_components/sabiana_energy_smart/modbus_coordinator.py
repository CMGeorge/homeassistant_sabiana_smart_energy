"""Data update coordinator for Sabiana Modbus devices."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import LOGGER
from .helpers import group_contiguous
from .modbus_client import SabianaModbusClient

VERIFY_DELAY = 1.0


class SabianaModbusCoordinator(DataUpdateCoordinator[dict[int, int | None]]):
    """Coordinator that polls only the Modbus addresses registered by entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict[str, Any],
        config_entry: ConfigEntry | None = None,
    ) -> None:
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name="Sabiana Modbus Coordinator",
            update_interval=timedelta(seconds=3),
        )
        self._host = config["host"]
        self._port = config["port"]
        self._slave = config["slave"]
        self._client = SabianaModbusClient(self._host, self._port)
        self._active_addresses: set[int] = set()
        self._float32_bases: set[int] = set()
        self._cancel_verify: Callable[[], None] | None = None
        # Blocks the device refused to return in one request; read them
        # register by register from then on.
        self._split_blocks: set[tuple[int, int]] = set()

    def register_address(self, address: int) -> None:
        """Register a Modbus address to be polled."""
        if address not in self._active_addresses:
            self._active_addresses.add(address)
            LOGGER.debug("Registered address 0x%04X for polling", address)

    def register_float32(self, address: int) -> None:
        """Register a two-register value; both words are read in one request."""
        self._float32_bases.add(address)
        self.register_address(address)
        self.register_address(address + 1)

    async def async_setup(self) -> bool:
        """Connect the Modbus client. Return False if the device is unreachable."""
        return await self._client.ensure_connected()

    async def async_close(self) -> None:
        """Cancel pending work and close the Modbus client connection."""
        if self._cancel_verify is not None:
            self._cancel_verify()
            self._cancel_verify = None
        try:
            await self._client.close()
        except Exception as err:
            LOGGER.debug("Error closing Modbus client: %s", err)

    async def async_read_register(self, address: int) -> int:
        """Read one register directly from the device (bypassing the cache)."""
        value = await self._client.read_register(
            address=address, count=1, slave=self._slave
        )
        if not value:
            raise HomeAssistantError(
                f"Failed to read register 0x{address:04X} from {self._host}"
            )
        return value[0]

    async def async_write_register(self, address: int, value: int) -> None:
        """Write a register and optimistically update coordinator data.

        - Perform the Modbus write (raise HomeAssistantError on failure)
        - Immediately reflect the new raw value in coordinator.data
        - Schedule a short delayed refresh to reconcile with device
        """
        ok = await self._client.write_register(
            address=address, value=value, slave=self._slave
        )
        if not ok:
            raise HomeAssistantError(
                f"Failed to write value {value} to register 0x{address:04X} "
                f"on {self._host}:{self._port}"
            )

        # Optimistic update for snappy UI
        new_data = dict(self.data or {})
        new_data[address] = value
        self.async_set_updated_data(new_data)

        # Verify shortly after (device may clamp/adjust value)
        if self._cancel_verify is not None:
            self._cancel_verify()
        self._cancel_verify = async_call_later(
            self.hass, VERIFY_DELAY, self._async_verify
        )

    @callback
    def _async_verify(self, _now: Any) -> None:
        """Request a refresh after a write."""
        self._cancel_verify = None
        self.hass.async_create_task(self.async_request_refresh())

    async def _async_update_data(self) -> dict[int, int | None]:
        """Poll the registered Modbus addresses in contiguous blocks."""
        if not await self._client.ensure_connected():
            raise UpdateFailed(
                f"Cannot connect to Sabiana unit at {self._host}:{self._port}"
            )

        results: dict[int, int | None] = {}
        blocks = group_contiguous(self._active_addresses, pairs=self._float32_bases)

        for start, count in blocks:
            if (start, count) not in self._split_blocks:
                values = await self._client.read_register(
                    address=start, count=count, slave=self._slave
                )
                if values is not None and len(values) == count:
                    for offset, value in enumerate(values):
                        results[start + offset] = value
                    continue

                if not self._client.connected:
                    raise UpdateFailed(
                        f"Lost connection to Sabiana unit at {self._host}:{self._port}"
                    )

                # Some devices reject reads that span unmapped registers: read
                # this block one value at a time from now on.
                LOGGER.debug(
                    "Block read 0x%04X+%d failed; reading registers one by one",
                    start,
                    count,
                )
                self._split_blocks.add((start, count))

            await self._async_read_block_fallback(start, count, results)
            if not self._client.connected:
                raise UpdateFailed(
                    f"Lost connection to Sabiana unit at {self._host}:{self._port}"
                )

        if self._active_addresses and all(v is None for v in results.values()):
            raise UpdateFailed(
                f"No register could be read from {self._host}:{self._port}"
            )

        return results

    async def _async_read_block_fallback(
        self, start: int, count: int, results: dict[int, int | None]
    ) -> None:
        """Read a block register by register (float32 pairs in one request)."""
        address = start
        end = start + count
        while address < end:
            width = 2 if address in self._float32_bases else 1
            values = await self._client.read_register(
                address=address, count=width, slave=self._slave
            )
            for offset in range(width):
                value = values[offset] if values and len(values) == width else None
                results[address + offset] = value
                LOGGER.debug("Read 0x%04X → %s", address + offset, value)
            if values is None and not self._client.connected:
                return
            address += width
