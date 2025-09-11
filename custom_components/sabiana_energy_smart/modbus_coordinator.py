import logging
import asyncio
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .modbus_client import SabianaModbusClient
from .const import LOGGER
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
        self._active_addresses: set[int] = set()

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
        """Write a register and optimistically update coordinator data.

        - Perform the Modbus write
        - Immediately reflect the new raw value in coordinator.data
        - Schedule a short delayed refresh to reconcile with device
        """
        ok = await self._client.write_register(address=address, value=value, slave=self._slave)
        if ok:
            # Optimistic update for snappy UI
            new_data = dict(self.data or {})
            new_data[address] = value
            self.async_set_updated_data(new_data)

            # Verify shortly after (device may clamp/adjust value)
            async def _verify():
                await asyncio.sleep(1.0)
                await self.async_request_refresh()

            self.hass.async_create_task(_verify())

        return ok

    async def _async_update_data(self) -> dict[int, int | None]:
        """Poll only the registered Modbus addresses."""
        results: dict[int, int | None] = {}

        for addr in self._active_addresses:
            try:
                value = await self._client.read_register(address=addr, count=1, slave=self._slave)
                results[addr] = value[0] if value else None
                LOGGER.debug("Read 0x%04X → %s", addr, results[addr])
            except Exception as err:
                LOGGER.error("Error reading register 0x%04X: %s", addr, err)
                results[addr] = None

        return results
