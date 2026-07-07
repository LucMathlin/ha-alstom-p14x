"""Button platform for Alstom P14x integration."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CB_COMMAND_CLOSE,
    CB_COMMAND_TRIP,
    CONF_ENABLE_CB_CONTROL,
    DOMAIN,
)
from .coordinator import P14xFastCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    if not entry.data.get(CONF_ENABLE_CB_CONTROL, False):
        return

    coordinators = hass.data[DOMAIN][entry.entry_id]
    fast: P14xFastCoordinator = coordinators["fast"]

    entities = [
        P14xCBTripButton(fast, entry),
        P14xCBCloseButton(fast, entry),
    ]

    async_add_entities(entities)


class P14xCBTripButton(ButtonEntity):
    """Button to send CB Trip command."""

    _attr_has_entity_name = True
    _attr_name = "CB Trip"
    _attr_icon = "mdi:electric-switch-closed"
    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(
        self, coordinator: P14xFastCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the button."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_cb_trip"
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"P14x Relay ({self._entry.data.get('host', 'unknown')})",
            manufacturer="Alstom / GE / Schneider Electric",
            model="P14x Series",
        )

    async def async_press(self) -> None:
        """Handle the button press - send trip command."""
        _LOGGER.warning(
            "CB Trip command issued for relay at %s (slave %s)",
            self._entry.data.get("host"),
            self._entry.data.get("slave_id"),
        )
        success = await self._coordinator.send_cb_command(CB_COMMAND_TRIP)
        if not success:
            _LOGGER.error("Failed to send CB Trip command")


class P14xCBCloseButton(ButtonEntity):
    """Button to send CB Close command."""

    _attr_has_entity_name = True
    _attr_name = "CB Close"
    _attr_icon = "mdi:electric-switch"

    def __init__(
        self, coordinator: P14xFastCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the button."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_cb_close"
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"P14x Relay ({self._entry.data.get('host', 'unknown')})",
            manufacturer="Alstom / GE / Schneider Electric",
            model="P14x Series",
        )

    async def async_press(self) -> None:
        """Handle the button press - send close command."""
        _LOGGER.warning(
            "CB Close command issued for relay at %s (slave %s)",
            self._entry.data.get("host"),
            self._entry.data.get("slave_id"),
        )
        success = await self._coordinator.send_cb_command(CB_COMMAND_CLOSE)
        if not success:
            _LOGGER.error("Failed to send CB Close command")
