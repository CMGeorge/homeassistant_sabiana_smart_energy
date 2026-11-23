"""Data update coordinator for Sabiana Modbus devices."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    BLOCKED_FUNCTIONS_ADDRESS,
    CLOCK_DAY_ADDRESS,
    CLOCK_SYNC_THRESHOLD_MINUTES,
    CLOCK_TIME_ADDRESS,
    CONF_RETRIES,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_RETRIES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    LOGGER,
)
from .helpers import (
    clock_drift_minutes,
    decode_device_clock,
    encode_device_clock,
    format_device_clock,
    group_contiguous,
)
from .modbus_client import SabianaCommunicationError, SabianaModbusClient

VERIFY_DELAY = 1.0


class SabianaModbusCoordinator(DataUpdateCoordinator[dict[int, int | None]]):
    """Coordinator that polls only the Modbus addresses registered by entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict[str, Any],
        config_entry: ConfigEntry | None = None,
    ) -> None:
        options = config_entry.options if config_entry is not None else {}
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name="Sabiana Modbus Coordinator",
            update_interval=timedelta(
                seconds=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self._host = config["host"]
        self._port = config["port"]
        self._slave = config["slave"]
        self._client = SabianaModbusClient(
            self._host,
            self._port,
            timeout=options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            retries=options.get(CONF_RETRIES, DEFAULT_RETRIES),
        )
        self._active_addresses: set[int] = set()
        self._float32_bases: set[int] = set()
        self._cancel_verify: Callable[[], None] | None = None
        # Blocks the device refused (exception response) in one request; read
        # them register by register from then on. A timeout never lands here:
        # it says nothing about the block, only that the unit did not answer.
        self._split_blocks: set[tuple[int, int]] = set()
        # Set by the "Automatic clock sync" switch once its state is restored.
        # None means "not known yet": no automatic writes until then.
        self.clock_auto_sync: bool | None = None

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
        self._apply_written_values(address, [value])

    async def async_write_registers(self, address: int, values: list[int]) -> None:
        """Write contiguous registers in one request (FC16).

        Falls back to one FC6 write per register if the device rejects FC16.
        Raises HomeAssistantError on failure.
        """
        ok = await self._client.write_registers(
            address=address, values=values, slave=self._slave
        )
        if not ok and self._client.connected:
            LOGGER.debug(
                "Multi-register write at 0x%04X rejected; writing one by one",
                address,
            )
            ok = True
            for offset, value in enumerate(values):
                if not await self._client.write_register(
                    address=address + offset, value=value, slave=self._slave
                ):
                    ok = False
                    break
        if not ok:
            raise HomeAssistantError(
                f"Failed to write {values} to registers starting at "
                f"0x{address:04X} on {self._host}:{self._port}"
            )
        self._apply_written_values(address, values)

    @callback
    def _apply_written_values(self, address: int, values: list[int]) -> None:
        """Reflect written values immediately, then re-read from the device."""
        # Optimistic update for snappy UI
        new_data = dict(self.data or {})
        for offset, value in enumerate(values):
            new_data[address + offset] = value
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

    # --- Device clock ---------------------------------------------------------

    @property
    def device_clock(self) -> tuple[int, int, int] | None:
        """Return the device clock as (isoweekday, hour, minute), if known."""
        data = self.data or {}
        return decode_device_clock(
            data.get(CLOCK_TIME_ADDRESS), data.get(CLOCK_DAY_ADDRESS)
        )

    def clock_drift(self, now: datetime | None = None) -> int | None:
        """Return how many minutes the device clock is ahead of Home Assistant."""
        device = self.device_clock
        if device is None:
            return None
        now = now or dt_util.now()
        return clock_drift_minutes(device, (now.isoweekday(), now.hour, now.minute))

    async def async_sync_clock(self, now: datetime | None = None) -> None:
        """Set the device clock to Home Assistant's local time and weekday.

        The unit has no calendar or DST rules, so this is what keeps it right
        after daylight saving time changes. Raises HomeAssistantError on failure.
        """
        now = now or dt_util.now()
        values = encode_device_clock(now.hour, now.minute, now.isoweekday())
        try:
            await self.async_write_registers(CLOCK_TIME_ADDRESS, values)
        except HomeAssistantError as err:
            raise HomeAssistantError(
                f"{err}. If this keeps failing, check that 'Time/day change' is "
                f"not blocked on the unit (register 0x{BLOCKED_FUNCTIONS_ADDRESS:04X}"
                ", bit 5)"
            ) from err
        LOGGER.info(
            "Device clock set to %s",
            format_device_clock((now.isoweekday(), now.hour, now.minute)),
        )

    async def async_check_clock(self, now: datetime | None = None) -> None:
        """Re-sync the device clock if automatic sync is on and it has drifted.

        Runs from a timer, so failures are logged instead of raised.
        """
        if not self.clock_auto_sync:
            return
        now = now or dt_util.now()
        drift = self.clock_drift(now)
        if drift is None:
            LOGGER.debug("Device clock not read yet, skipping clock check")
            return
        if abs(drift) < CLOCK_SYNC_THRESHOLD_MINUTES:
            return
        LOGGER.info(
            "Device clock is %s (%+d min vs Home Assistant), syncing",
            format_device_clock(self.device_clock),
            drift,
        )
        try:
            await self.async_sync_clock(now)
        except HomeAssistantError as err:
            LOGGER.warning("Automatic clock sync failed: %s", err)

    async def _async_update_data(self) -> dict[int, int | None]:
        """Poll the registered Modbus addresses in contiguous blocks."""
        if not await self._client.ensure_connected():
            raise UpdateFailed(
                f"Cannot connect to Sabiana unit at {self._host}:{self._port}"
            )

        results: dict[int, int | None] = {}
        blocks = group_contiguous(self._active_addresses, pairs=self._float32_bases)

        try:
            for start, count in blocks:
                await self._async_read_block(start, count, results)
        except SabianaCommunicationError as err:
            # The unit (or the RS485 gateway) did not answer. Stop this poll
            # instead of sending the remaining requests into a link that is
            # not responding; the next poll tries again.
            raise UpdateFailed(
                f"No answer from Sabiana unit at {self._host}:{self._port}: {err}"
            ) from err

        if self._active_addresses and all(v is None for v in results.values()):
            raise UpdateFailed(
                f"No register could be read from {self._host}:{self._port}"
            )

        return results

    async def _async_read_block(
        self, start: int, count: int, results: dict[int, int | None]
    ) -> None:
        """Read one block into results.

        Raises SabianaCommunicationError if the unit does not answer.
        """
        if (start, count) not in self._split_blocks:
            values = await self._client.read_block(
                address=start, count=count, slave=self._slave
            )
            if values is not None and len(values) == count:
                for offset, value in enumerate(values):
                    results[start + offset] = value
                return

            # The unit answered but refused the block (some devices reject
            # reads that span unmapped registers): read it one value at a time
            # from now on.
            LOGGER.debug(
                "Block read 0x%04X+%d refused; reading registers one by one",
                start,
                count,
            )
            self._split_blocks.add((start, count))

        await self._async_read_block_fallback(start, count, results)

    async def _async_read_block_fallback(
        self, start: int, count: int, results: dict[int, int | None]
    ) -> None:
        """Read a block register by register (float32 pairs in one request).

        A register the unit refuses is stored as None. Raises
        SabianaCommunicationError if the unit does not answer.
        """
        address = start
        end = start + count
        while address < end:
            width = 2 if address in self._float32_bases else 1
            values = await self._client.read_block(
                address=address, count=width, slave=self._slave
            )
            for offset in range(width):
                value = values[offset] if values and len(values) == width else None
                results[address + offset] = value
                LOGGER.debug("Read 0x%04X → %s", address + offset, value)
            address += width
