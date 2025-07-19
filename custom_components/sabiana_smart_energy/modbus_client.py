import logging
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

_LOGGER = logging.getLogger(__name__)

class SabianaModbusClient:
    """Handles persistent async Modbus TCP communication for Sabiana devices."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.client: AsyncModbusTcpClient | None = None

    async def ensure_connected(self) -> bool:
        """Ensure the Modbus client is connected, reconnect if needed."""
        if self.client is None:
            self.client = AsyncModbusTcpClient(self.host, port=self.port)

        if not self.client.connected:
            try:
                connected = await self.client.connect()
                if not connected:
                    _LOGGER.error(
                        "Failed to connect to Modbus server at %s:%s",
                        self.host,
                        self.port,
                    )
                    return False
            except Exception as e:
                _LOGGER.error("Modbus connection error: %s", e)
                return False

        return True

    async def read_register(
        self, address: int, count: int = 1, slave: int = 1
    ) -> list[int] | None:
        """Read holding registers from Modbus server."""
        if not await self.ensure_connected():
            return None

        try:
            result = await self.client.read_holding_registers(
                address=address, count=count, slave=slave
            )
            if result is None or result.isError():
                _LOGGER.warning("Read failed at address 0x%04X", address)
                return None
            return result.registers
        except ModbusException as me:
            _LOGGER.error("Modbus protocol error at 0x%04X: %s", address, me)
        except Exception as e:
            _LOGGER.error("Unexpected error reading 0x%04X: %s", address, e)

        return None

    async def write_register(
        self, address: int, value: int, slave: int = 1
    ) -> bool:
        """Write a value to a Modbus register."""
        if not await self.ensure_connected():
            return False

        try:
            result = await self.client.write_register(
                address=address, value=value, slave=slave
            )
            if result.isError():
                _LOGGER.warning("Write failed at 0x%04X: %s", address, result)
                return False
            return True
        except ModbusException as me:
            _LOGGER.error("Modbus write error at 0x%04X: %s", address, me)
        except Exception as e:
            _LOGGER.error("Unexpected error writing 0x%04X: %s", address, e)

        return False

    async def close(self) -> None:
        """Close the Modbus connection gracefully."""
        if self.client:
            try:
                await self.client.close()
            except Exception as e:
                _LOGGER.warning("Error while closing Modbus client: %s", e)
            finally:
                self.client = None
