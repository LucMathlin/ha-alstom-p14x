"""Alstom P14x Protection Relay integration for Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import (
    P14xFastCoordinator,
    P14xMediumCoordinator,
    P14xSlowCoordinator,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alstom P14x from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    fast_coordinator = P14xFastCoordinator(hass, entry)
    medium_coordinator = P14xMediumCoordinator(hass, entry)
    slow_coordinator = P14xSlowCoordinator(hass, entry)

    await fast_coordinator.async_config_entry_first_refresh()
    await medium_coordinator.async_config_entry_first_refresh()
    await slow_coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "fast": fast_coordinator,
        "medium": medium_coordinator,
        "slow": slow_coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
