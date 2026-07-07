"""Binary sensor platform for Alstom P14x integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ENABLE_CB_STATUS, DOMAIN
from .coordinator import P14xFastCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities."""
    coordinators = hass.data[DOMAIN][entry.entry_id]
    fast: P14xFastCoordinator = coordinators["fast"]

    entities: list[BinarySensorEntity] = []

    # CB Status binary sensors (if enabled)
    if entry.data.get(CONF_ENABLE_CB_STATUS, True):
        entities.extend([
            P14xCBOpenSensor(fast, entry),
            P14xCBClosedSensor(fast, entry),
        ])

    # Always include alarm and fault detection
    entities.extend([
        P14xNewFaultSensor(fast, entry),
        P14xAlarmSensor(fast, entry, 1),
        P14xAlarmSensor(fast, entry, 2),
        P14xAlarmSensor(fast, entry, 3),
    ])

    async_add_entities(entities)


class P14xCBOpenSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for CB Open status."""

    _attr_has_entity_name = True
    _attr_name = "Circuit Breaker Open"
    _attr_device_class = BinarySensorDeviceClass.OPENING
    _attr_icon = "mdi:electric-switch"

    def __init__(
        self, coordinator: P14xFastCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_cb_open"
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

    @property
    def is_on(self) -> bool | None:
        """Return true if CB is open."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("cb_open")


class P14xCBClosedSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for CB Closed status."""

    _attr_has_entity_name = True
    _attr_name = "Circuit Breaker Closed"
    _attr_device_class = BinarySensorDeviceClass.POWER
    _attr_icon = "mdi:electric-switch-closed"

    def __init__(
        self, coordinator: P14xFastCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_cb_closed"
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

    @property
    def is_on(self) -> bool | None:
        """Return true if CB is closed."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("cb_closed")


class P14xNewFaultSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that indicates a new protection fault has been recorded."""

    _attr_has_entity_name = True
    _attr_name = "New Fault Detected"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:shield-alert"

    def __init__(
        self, coordinator: P14xFastCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_new_fault"
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

    @property
    def is_on(self) -> bool | None:
        """Return true if a new fault has been detected."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("new_fault", False)

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        if self.coordinator.data is None:
            return {}
        return {
            "fault_record_count": self.coordinator.data.get("fault_record_count"),
        }


class P14xAlarmSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for alarm status registers."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:alarm-light"

    def __init__(
        self,
        coordinator: P14xFastCoordinator,
        entry: ConfigEntry,
        alarm_group: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._alarm_group = alarm_group
        self._attr_name = f"Alarm Status {alarm_group}"
        self._attr_unique_id = f"{entry.entry_id}_alarm_status_{alarm_group}"
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

    @property
    def is_on(self) -> bool | None:
        """Return true if any alarm bit is active."""
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get(f"alarm_status_{self._alarm_group}", 0)
        return value != 0

    @property
    def extra_state_attributes(self) -> dict:
        """Return the raw alarm value for debugging."""
        if self.coordinator.data is None:
            return {}
        value = self.coordinator.data.get(f"alarm_status_{self._alarm_group}", 0)
        return {
            "raw_value": value,
            "hex_value": f"0x{value:08X}" if isinstance(value, int) else None,
        }
