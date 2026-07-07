"""Data coordinators for the Alstom P14x integration."""
from __future__ import annotations

import logging
import struct
from datetime import timedelta
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ENABLE_CB_STATUS,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL_FAST,
    CONF_SCAN_INTERVAL_MEDIUM,
    CONF_SCAN_INTERVAL_SLOW,
    CONF_SLAVE_ID,
    DEFAULT_SCAN_INTERVAL_FAST,
    DEFAULT_SCAN_INTERVAL_MEDIUM,
    DEFAULT_SCAN_INTERVAL_SLOW,
    DEFAULT_SLAVE_ID,
    DOMAIN,
    REG_3PH_VARS_IEEE,
    REG_3PH_WATTS_IEEE,
    REG_ALARM_STATUS_1,
    REG_ALARM_STATUS_2,
    REG_ALARM_STATUS_3,
    REG_CB_COMMAND,
    REG_CB_OPERATE_TIME,
    REG_CB_OPERATIONS,
    REG_DC_SUPPLY,
    REG_FAULT_CB_OPERATE_TIME,
    REG_FAULT_IA,
    REG_FAULT_IB,
    REG_FAULT_IC,
    REG_FAULT_RECORD_COUNT,
    REG_FAULTED_PHASE,
    REG_FREQUENCY,
    REG_IA_RMS,
    REG_IB_RMS,
    REG_IC_RMS,
    REG_IN_MEASURED,
    REG_OPTO_INPUT_STATUS,
    REG_PASSWORD,
    REG_PLANT_STATUS,
    REG_POWER_FACTOR,
    REG_RELAY_OUTPUT_STATUS,
    REG_THERMAL_STATE,
    REG_TRIP_ELEMENTS_1,
    REG_TRIP_ELEMENTS_2,
    REG_VAN_RMS,
    REG_VARH_FWD_IEEE,
    REG_VARH_REV_IEEE,
    REG_VBN_RMS,
    REG_VCN_RMS,
    REG_WH_FWD_IEEE,
    REG_WH_REV_IEEE,
)

_LOGGER = logging.getLogger(__name__)


def decode_courier_number(registers: list[int]) -> float | None:
    """Decode Alstom Courier Number format.

    Courier Number uses 2 registers:
    - Register 1: Signed 16-bit mantissa
    - Register 2: Signed 16-bit exponent (power of 10)
    Actual value = mantissa * 10^exponent
    """
    if len(registers) < 2:
        return None
    mantissa = registers[0]
    exponent = registers[1]
    # Convert to signed 16-bit
    if mantissa > 32767:
        mantissa -= 65536
    if exponent > 32767:
        exponent -= 65536
    try:
        return mantissa * (10**exponent)
    except (OverflowError, ValueError):
        return None


def decode_courier_single(register: int) -> float | None:
    """Decode a single-register Courier Number (scaled value).

    For frequency: value / 100
    For power factor: value / 1000
    For angles: value / 10
    For percentage: value / 10
    """
    if register > 32767:
        register -= 65536
    return register


def decode_ieee_float(registers: list[int]) -> float | None:
    """Decode IEEE 754 32-bit float from 2 Modbus registers."""
    if len(registers) < 2:
        return None
    try:
        # Big-endian: first register is high word
        raw = struct.pack(">HH", registers[0], registers[1])
        value = struct.unpack(">f", raw)[0]
        return round(value, 3)
    except (struct.error, ValueError):
        return None


class P14xBaseCoordinator(DataUpdateCoordinator):
    """Base coordinator with shared Modbus client logic."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        name: str,
        update_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{name}_{entry.entry_id}",
            update_interval=timedelta(seconds=update_interval),
        )
        self._host = entry.data[CONF_HOST]
        self._port = entry.data[CONF_PORT]
        self._slave_id = entry.data.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID)
        self._entry = entry
        self._client: AsyncModbusTcpClient | None = None

    async def _get_client(self) -> AsyncModbusTcpClient:
        """Get or create the Modbus TCP client."""
        if self._client is None or not self._client.connected:
            self._client = AsyncModbusTcpClient(
                host=self._host,
                port=self._port,
                timeout=5,
            )
            await self._client.connect()
            if not self._client.connected:
                raise UpdateFailed(
                    f"Failed to connect to {self._host}:{self._port}"
                )
        return self._client

    async def _read_input_registers(
        self, address: int, count: int
    ) -> list[int] | None:
        """Read input registers (function code 04)."""
        try:
            client = await self._get_client()
            result = await client.read_input_registers(
                address=address, count=count, slave=self._slave_id
            )
            if result.isError():
                _LOGGER.warning(
                    "Error reading input registers %d-%d: %s",
                    address,
                    address + count - 1,
                    result,
                )
                return None
            return result.registers
        except ModbusException as err:
            _LOGGER.error("Modbus exception: %s", err)
            self._client = None
            return None
        except Exception as err:
            _LOGGER.error("Unexpected error reading registers: %s", err)
            self._client = None
            return None

    async def _read_holding_registers(
        self, address: int, count: int
    ) -> list[int] | None:
        """Read holding registers (function code 03)."""
        try:
            client = await self._get_client()
            result = await client.read_holding_registers(
                address=address, count=count, slave=self._slave_id
            )
            if result.isError():
                _LOGGER.warning(
                    "Error reading holding registers %d-%d: %s",
                    address,
                    address + count - 1,
                    result,
                )
                return None
            return result.registers
        except ModbusException as err:
            _LOGGER.error("Modbus exception: %s", err)
            self._client = None
            return None
        except Exception as err:
            _LOGGER.error("Unexpected error reading registers: %s", err)
            self._client = None
            return None

    async def _write_register(self, address: int, value: int) -> bool:
        """Write a single holding register (function code 06)."""
        try:
            client = await self._get_client()
            result = await client.write_register(
                address=address, value=value, slave=self._slave_id
            )
            if result.isError():
                _LOGGER.error(
                    "Error writing register %d: %s", address, result
                )
                return False
            return True
        except ModbusException as err:
            _LOGGER.error("Modbus write exception: %s", err)
            self._client = None
            return False

    async def _write_registers(self, address: int, values: list[int]) -> bool:
        """Write multiple holding registers (function code 16)."""
        try:
            client = await self._get_client()
            result = await client.write_registers(
                address=address, values=values, slave=self._slave_id
            )
            if result.isError():
                _LOGGER.error(
                    "Error writing registers %d: %s", address, result
                )
                return False
            return True
        except ModbusException as err:
            _LOGGER.error("Modbus write exception: %s", err)
            self._client = None
            return False

    async def authenticate(self) -> bool:
        """Send password to relay for write access."""
        password = self._entry.data.get(CONF_PASSWORD, "")
        if not password:
            return True  # No password configured, skip auth

        # Convert password string to register values (2 chars per register)
        regs = []
        # Pad password to even length
        padded = password.ljust(4, "\x00")[:4]
        for i in range(0, len(padded), 2):
            high = ord(padded[i]) & 0xFF
            low = ord(padded[i + 1]) & 0xFF if i + 1 < len(padded) else 0
            regs.append((high << 8) | low)

        return await self._write_registers(REG_PASSWORD, regs)

    async def send_cb_command(self, command: int) -> bool:
        """Send a CB trip or close command."""
        # Authenticate first
        if not await self.authenticate():
            _LOGGER.error("Authentication failed, cannot send CB command")
            return False

        return await self._write_register(REG_CB_COMMAND, command)


class P14xFastCoordinator(P14xBaseCoordinator):
    """Coordinator for fast-polling data (CB status, alarms)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize fast coordinator."""
        interval = entry.data.get(
            CONF_SCAN_INTERVAL_FAST, DEFAULT_SCAN_INTERVAL_FAST
        )
        super().__init__(hass, entry, "fast", interval)
        self._previous_fault_count: int | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch fast-polling data."""
        data: dict[str, Any] = {}

        # Read Plant Status (CB position) - register 3x00002
        regs = await self._read_input_registers(REG_PLANT_STATUS, 1)
        if regs:
            data["plant_status"] = regs[0]
            data["cb_open"] = bool(regs[0] & 0x0001)
            data["cb_closed"] = bool(regs[0] & 0x0002)

        # Read Opto Input Status - register 3x00007
        regs = await self._read_input_registers(REG_OPTO_INPUT_STATUS, 1)
        if regs:
            data["opto_input_status"] = regs[0]

        # Read Relay Output Status - registers 3x00008-00009
        regs = await self._read_input_registers(REG_RELAY_OUTPUT_STATUS, 2)
        if regs:
            data["relay_output_status"] = (regs[1] << 16) | regs[0]

        # Read Alarm Status 1 - registers 3x00011-00012
        regs = await self._read_input_registers(REG_ALARM_STATUS_1, 2)
        if regs:
            data["alarm_status_1"] = (regs[1] << 16) | regs[0]

        # Read Alarm Status 2 - registers 3x00013-00014
        regs = await self._read_input_registers(REG_ALARM_STATUS_2, 2)
        if regs:
            data["alarm_status_2"] = (regs[1] << 16) | regs[0]

        # Read Alarm Status 3 - registers 3x00015-00016
        regs = await self._read_input_registers(REG_ALARM_STATUS_3, 2)
        if regs:
            data["alarm_status_3"] = (regs[1] << 16) | regs[0]

        # Read Fault Record Count - register 3x00100
        regs = await self._read_input_registers(REG_FAULT_RECORD_COUNT, 1)
        if regs:
            current_count = regs[0]
            data["fault_record_count"] = current_count

            # Detect new fault
            if self._previous_fault_count is None:
                self._previous_fault_count = current_count
                data["new_fault"] = False
            elif current_count > self._previous_fault_count:
                data["new_fault"] = True
                self._previous_fault_count = current_count
            else:
                data["new_fault"] = False

        if not data:
            raise UpdateFailed("Failed to read any fast-polling registers")

        return data


class P14xMediumCoordinator(P14xBaseCoordinator):
    """Coordinator for medium-polling data (measurements)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize medium coordinator."""
        interval = entry.data.get(
            CONF_SCAN_INTERVAL_MEDIUM, DEFAULT_SCAN_INTERVAL_MEDIUM
        )
        super().__init__(hass, entry, "medium", interval)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch measurement data."""
        data: dict[str, Any] = {}

        # IN Measured (3x00209-00210) - 2 registers
        regs = await self._read_input_registers(REG_IN_MEASURED, 2)
        if regs:
            data["in_measured"] = decode_courier_number(regs)

        # IA RMS (3x00224-00225) - 2 registers
        regs = await self._read_input_registers(REG_IA_RMS, 2)
        if regs:
            data["ia_rms"] = decode_courier_number(regs)

        # IB RMS (3x00226-00227) - 2 registers
        regs = await self._read_input_registers(REG_IB_RMS, 2)
        if regs:
            data["ib_rms"] = decode_courier_number(regs)

        # IC RMS (3x00228-00229) - 2 registers
        regs = await self._read_input_registers(REG_IC_RMS, 2)
        if regs:
            data["ic_rms"] = decode_courier_number(regs)

        # DC Supply (3x00239-00240) - 2 registers
        regs = await self._read_input_registers(REG_DC_SUPPLY, 2)
        if regs:
            data["dc_supply"] = decode_courier_number(regs)

        # VAN RMS (3x00257-00258) - 2 registers
        regs = await self._read_input_registers(REG_VAN_RMS, 2)
        if regs:
            data["van_rms"] = decode_courier_number(regs)

        # VBN RMS (3x00259-00260) - 2 registers
        regs = await self._read_input_registers(REG_VBN_RMS, 2)
        if regs:
            data["vbn_rms"] = decode_courier_number(regs)

        # VCN RMS (3x00261-00262) - 2 registers
        regs = await self._read_input_registers(REG_VCN_RMS, 2)
        if regs:
            data["vcn_rms"] = decode_courier_number(regs)

        # Frequency (3x00263) - 1 register
        regs = await self._read_input_registers(REG_FREQUENCY, 1)
        if regs:
            # Courier frequency: value / 100 to get Hz
            raw = decode_courier_single(regs[0])
            data["frequency"] = raw / 100.0 if raw is not None else None

        # Power Factor (3x00336) - 1 register
        regs = await self._read_input_registers(REG_POWER_FACTOR, 1)
        if regs:
            # Courier power factor: value / 1000
            raw = decode_courier_single(regs[0])
            data["power_factor"] = raw / 1000.0 if raw is not None else None

        # 3 Phase Watts IEEE (3x00406-00407) - 2 registers
        regs = await self._read_input_registers(REG_3PH_WATTS_IEEE, 2)
        if regs:
            data["three_phase_watts"] = decode_ieee_float(regs)

        # 3 Phase VArs IEEE (3x00408-00409) - 2 registers
        regs = await self._read_input_registers(REG_3PH_VARS_IEEE, 2)
        if regs:
            data["three_phase_vars"] = decode_ieee_float(regs)

        # Thermal State (3x00434) - 1 register
        regs = await self._read_input_registers(REG_THERMAL_STATE, 1)
        if regs:
            raw = decode_courier_single(regs[0])
            data["thermal_state"] = raw / 10.0 if raw is not None else None

        if not data:
            raise UpdateFailed("Failed to read any measurement registers")

        return data


class P14xSlowCoordinator(P14xBaseCoordinator):
    """Coordinator for slow-polling data (energy, fault records)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize slow coordinator."""
        interval = entry.data.get(
            CONF_SCAN_INTERVAL_SLOW, DEFAULT_SCAN_INTERVAL_SLOW
        )
        super().__init__(hass, entry, "slow", interval)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch energy and fault record data."""
        data: dict[str, Any] = {}

        # Energy - Watt Hours Forward IEEE (3x00412-00413)
        regs = await self._read_input_registers(REG_WH_FWD_IEEE, 2)
        if regs:
            data["wh_forward"] = decode_ieee_float(regs)

        # Energy - Watt Hours Reverse IEEE (3x00414-00415)
        regs = await self._read_input_registers(REG_WH_REV_IEEE, 2)
        if regs:
            data["wh_reverse"] = decode_ieee_float(regs)

        # Energy - VAr Hours Forward IEEE (3x00416-00417)
        regs = await self._read_input_registers(REG_VARH_FWD_IEEE, 2)
        if regs:
            data["varh_forward"] = decode_ieee_float(regs)

        # Energy - VAr Hours Reverse IEEE (3x00418-00419)
        regs = await self._read_input_registers(REG_VARH_REV_IEEE, 2)
        if regs:
            data["varh_reverse"] = decode_ieee_float(regs)

        # CB Operations count (3x00600) - 1 register
        regs = await self._read_input_registers(REG_CB_OPERATIONS, 1)
        if regs:
            data["cb_operations"] = regs[0]

        # CB Operate Time (3x00607) - 1 register
        regs = await self._read_input_registers(REG_CB_OPERATE_TIME, 1)
        if regs:
            raw = decode_courier_single(regs[0])
            # Time in ms typically
            data["cb_operate_time"] = raw

        # Fault record details (latest fault = select 0)
        # Read faulted phase
        regs = await self._read_input_registers(REG_FAULTED_PHASE, 1)
        if regs:
            phase_map = {0: "None", 1: "A", 2: "B", 3: "C", 4: "AB", 5: "BC", 6: "CA", 7: "ABC"}
            data["faulted_phase"] = phase_map.get(regs[0], f"Unknown ({regs[0]})")

        # Trip Elements 1 (3x00108-00109)
        regs = await self._read_input_registers(REG_TRIP_ELEMENTS_1, 2)
        if regs:
            data["trip_elements_1"] = (regs[1] << 16) | regs[0]

        # Trip Elements 2 (3x00110-00111)
        regs = await self._read_input_registers(REG_TRIP_ELEMENTS_2, 2)
        if regs:
            data["trip_elements_2"] = (regs[1] << 16) | regs[0]

        # Fault currents
        regs = await self._read_input_registers(REG_FAULT_IA, 2)
        if regs:
            data["fault_ia"] = decode_courier_number(regs)

        regs = await self._read_input_registers(REG_FAULT_IB, 2)
        if regs:
            data["fault_ib"] = decode_courier_number(regs)

        regs = await self._read_input_registers(REG_FAULT_IC, 2)
        if regs:
            data["fault_ic"] = decode_courier_number(regs)

        if not data:
            raise UpdateFailed("Failed to read any slow-polling registers")

        return data
