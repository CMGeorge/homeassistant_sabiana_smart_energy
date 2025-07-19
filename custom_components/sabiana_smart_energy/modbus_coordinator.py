import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .modbus_client import SabianaModbusClient

_LOGGER = logging.getLogger(__name__)

class SabianaModbusCoordinator(DataUpdateCoordinator):
    """Coordinator that polls only the Modbus addresses registered by entities."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        super().__init__(
            hass,
            _LOGGER,
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
        _LOGGER.debug("Registered address 0x%04X for polling", address)

    async def async_setup(self) -> None:
        """Connect the Modbus client."""
        await self._client.ensure_connected()

    async def _async_update_data(self) -> dict[int, int | None]:
        """Poll only the registered Modbus addresses."""
        results: dict[int, int | None] = {}

        for addr in self._active_addresses:
            try:
                value = await self._client.read_register(address=addr, count=1, slave=self._slave)
                results[addr] = value[0] if value else None
                _LOGGER.debug("Read 0x%04X → %s", addr, results[addr])
            except Exception as err:
                _LOGGER.error("Error reading register 0x%04X: %s", addr, err)
                results[addr] = None

        return results
