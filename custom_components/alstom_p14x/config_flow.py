"""Config flow for Alstom P14x integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from pymodbus.client import AsyncModbusTcpClient

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import (
    CONF_ENABLE_CB_CONTROL,
    CONF_ENABLE_CB_STATUS,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL_FAST,
    CONF_SCAN_INTERVAL_MEDIUM,
    CONF_SCAN_INTERVAL_SLOW,
    CONF_SLAVE_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL_FAST,
    DEFAULT_SCAN_INTERVAL_MEDIUM,
    DEFAULT_SCAN_INTERVAL_SLOW,
    DEFAULT_SLAVE_ID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): vol.All(
            int, vol.Range(min=1, max=247)
        ),
        vol.Optional(CONF_PASSWORD, default=""): str,
        vol.Required(
            CONF_SCAN_INTERVAL_FAST, default=DEFAULT_SCAN_INTERVAL_FAST
        ): vol.All(int, vol.Range(min=1, max=60)),
        vol.Required(
            CONF_SCAN_INTERVAL_MEDIUM, default=DEFAULT_SCAN_INTERVAL_MEDIUM
        ): vol.All(int, vol.Range(min=5, max=300)),
        vol.Required(
            CONF_SCAN_INTERVAL_SLOW, default=DEFAULT_SCAN_INTERVAL_SLOW
        ): vol.All(int, vol.Range(min=30, max=600)),
        vol.Required(CONF_ENABLE_CB_STATUS, default=True): bool,
        vol.Required(CONF_ENABLE_CB_CONTROL, default=False): bool,
    }
)


async def validate_connection(host: str, port: int, slave_id: int) -> str | None:
    """Validate that we can connect to the relay."""
    try:
        client = AsyncModbusTcpClient(host=host, port=port, timeout=5)
        await client.connect()
        if not client.connected:
            return "cannot_connect"

        # Try reading the model number register to verify communication
        result = await client.read_input_registers(
            address=19, count=16, slave=slave_id  # 3x00020 Model Number
        )
        await client.close()

        if result.isError():
            return "cannot_communicate"

        return None
    except Exception as err:
        _LOGGER.error("Connection validation failed: %s", err)
        return "cannot_connect"


class AlstomP14xConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Alstom P14x."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate CB control requires CB status
            if user_input.get(CONF_ENABLE_CB_CONTROL) and not user_input.get(
                CONF_ENABLE_CB_STATUS
            ):
                errors["base"] = "cb_control_requires_status"
            else:
                # Validate connection
                error = await validate_connection(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_SLAVE_ID],
                )
                if error:
                    errors["base"] = error
                else:
                    # Create unique ID from host and slave
                    await self.async_set_unique_id(
                        f"{user_input[CONF_HOST]}_{user_input[CONF_SLAVE_ID]}"
                    )
                    self._abort_if_unique_id_configured()

                    title = f"P14x Relay ({user_input[CONF_HOST]}:{user_input[CONF_SLAVE_ID]})"
                    return self.async_create_entry(
                        title=title, data=user_input
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
