import asyncio
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CLOCK_DAY_ADDRESS,
    CLOCK_SYNC_THRESHOLD_MINUTES,
    CLOCK_TIME_ADDRESS,
    LOGGER,
)
from .helpers import (
    clock_drift_minutes,
    decode_device_clock,
    encode_device_clock,
    format_device_clock,
)
from .modbus_client import SabianaModbusClient


class SabianaModbusCoordinator(DataUpdateCoordinator):
    """Coordinator that polls only the Modbus addresses registered by entities."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        super().__init__(
            hass,
            LOGGER,
            name="Sabiana Modbus Coordinator",
            update_interval=timedelta(seconds=3),
        )
        self._host = config["host"]
        self._port = config["port"]
        self._slave = config["slave"]
        self._client = SabianaModbusClient(self._host, self._port)
        # The device clock is always polled: it is needed for automatic sync.
        self._active_addresses: set[int] = {CLOCK_TIME_ADDRESS, CLOCK_DAY_ADDRESS}
        # Set by the "Automatic clock sync" switch once its state is restored.
        # None means "not known yet": no automatic writes until then.
        self.clock_auto_sync: bool | None = None

    def register_address(self, address: int) -> None:
        """Register a Modbus address to be polled."""
        self._active_addresses.add(address)
        LOGGER.debug("Registered address 0x%04X for polling", address)

    async def async_setup(self) -> None:
        """Connect the Modbus client."""
        await self._client.ensure_connected()

    async def async_close(self) -> None:
        """Close the Modbus client connection."""
        try:
            await self._client.close()
        except Exception as err:
            LOGGER.debug("Error closing Modbus client: %s", err)

    async def async_write_register(self, address: int, value: int) -> bool:
        """Write a single register and optimistically update coordinator data."""
        ok = await self._client.write_register(
            address=address, value=value, slave=self._slave
        )
        if ok:
            self._apply_written_values(address, [value])
        return ok

    async def async_write_registers(self, address: int, values: list[int]) -> bool:
        """Write contiguous registers in one request and update coordinator data."""
        ok = await self._client.write_registers(
            address=address, values=values, slave=self._slave
        )
        if ok:
            self._apply_written_values(address, values)
        return ok

    def _apply_written_values(self, address: int, values: list[int]) -> None:
        """Reflect written values immediately, then re-read from the device.

        - Immediately reflect the new raw values in coordinator.data
        - Schedule a short delayed refresh to reconcile with device
        """
        # Optimistic update for snappy UI
        new_data = dict(self.data or {})
        for offset, value in enumerate(values):
            new_data[address + offset] = value
        self.async_set_updated_data(new_data)

        # Verify shortly after (device may clamp/adjust value)
        async def _verify():
            await asyncio.sleep(1.0)
            await self.async_request_refresh()

        self.hass.async_create_task(_verify())

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

    async def async_sync_clock(self, now: datetime | None = None) -> bool:
        """Set the device clock to Home Assistant's local time (and weekday).

        The unit has no calendar or DST rules, so this is what keeps it right
        after daylight saving time changes.
        """
        now = now or dt_util.now()
        values = encode_device_clock(now.hour, now.minute, now.isoweekday())
        ok = await self.async_write_registers(CLOCK_TIME_ADDRESS, values)
        if ok:
            LOGGER.info(
                "Device clock set to %s",
                format_device_clock((now.isoweekday(), now.hour, now.minute)),
            )
        else:
            LOGGER.warning(
                "Could not set the device clock. If this keeps failing, check "
                "that 'Time/day change' is not blocked (register 0x0226, bit 5)"
            )
        return ok

    async def async_check_clock(self, now: datetime | None = None) -> None:
        """Re-sync the device clock if automatic sync is on and it has drifted."""
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
        await self.async_sync_clock(now)

    async def _async_update_data(self) -> dict[int, int | None]:
        """Poll only the registered Modbus addresses."""
        results: dict[int, int | None] = {}

        for addr in self._active_addresses:
            try:
                value = await self._client.read_register(
                    address=addr, count=1, slave=self._slave
                )
                results[addr] = value[0] if value else None
                LOGGER.debug("Read 0x%04X → %s", addr, results[addr])
            except Exception as err:
                LOGGER.error("Error reading register 0x%04X: %s", addr, err)
                results[addr] = None

        return results
