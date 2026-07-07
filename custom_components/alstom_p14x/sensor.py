"""Sensor platform for Alstom P14x integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfReactivePower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import P14xMediumCoordinator, P14xSlowCoordinator

# Trip element bit definitions for decoding
TRIP_ELEMENTS_1_MAP = {
    0: "I>1 Trip",
    1: "I>2 Trip",
    2: "I>3 Trip",
    3: "I>4 Trip",
    4: "I>5 Trip",
    5: "I>6 Trip",
    6: "IN>1 Trip",
    7: "IN>2 Trip",
    8: "IN>3 Trip",
    9: "IN>4 Trip",
    10: "ISEF>1 Trip",
    11: "ISEF>2 Trip",
    12: "I2> Trip",
    13: "Thermal Trip",
    14: "CB Fail Trip",
    15: "Broken Conductor",
    16: "REF Trip",
    17: "VN>1 Trip",
    18: "VN>2 Trip",
    19: "V<1 Trip",
    20: "V<2 Trip",
    21: "V>1 Trip",
    22: "V>2 Trip",
    23: "F<1 Trip",
    24: "F<2 Trip",
    25: "F>1 Trip",
    26: "F>2 Trip",
    27: "df/dt 1 Trip",
    28: "df/dt 2 Trip",
    29: "df/dt 3 Trip",
    30: "df/dt 4 Trip",
    31: "Negative Seq OV Trip",
}


def decode_trip_elements(value: int) -> str:
    """Decode trip elements bitmask to human-readable string."""
    if value == 0:
        return "None"
    elements = []
    for bit, name in TRIP_ELEMENTS_1_MAP.items():
        if value & (1 << bit):
            elements.append(name)
    return ", ".join(elements) if elements else "Unknown"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinators = hass.data[DOMAIN][entry.entry_id]
    medium: P14xMediumCoordinator = coordinators["medium"]
    slow: P14xSlowCoordinator = coordinators["slow"]

    entities: list[SensorEntity] = [
        # Current sensors (medium polling)
        P14xMeasurementSensor(
            medium, entry, "ia_rms", "IA RMS Current",
            UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT,
        ),
        P14xMeasurementSensor(
            medium, entry, "ib_rms", "IB RMS Current",
            UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT,
        ),
        P14xMeasurementSensor(
            medium, entry, "ic_rms", "IC RMS Current",
            UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT,
        ),
        P14xMeasurementSensor(
            medium, entry, "in_measured", "IN Measured Current",
            UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT,
        ),
        # Voltage sensors
        P14xMeasurementSensor(
            medium, entry, "van_rms", "VAN RMS Voltage",
            UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE,
        ),
        P14xMeasurementSensor(
            medium, entry, "vbn_rms", "VBN RMS Voltage",
            UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE,
        ),
        P14xMeasurementSensor(
            medium, entry, "vcn_rms", "VCN RMS Voltage",
            UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE,
        ),
        # Frequency
        P14xMeasurementSensor(
            medium, entry, "frequency", "Frequency",
            UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY,
        ),
        # Power
        P14xMeasurementSensor(
            medium, entry, "three_phase_watts", "3-Phase Active Power",
            UnitOfPower.WATT, SensorDeviceClass.POWER,
        ),
        P14xMeasurementSensor(
            medium, entry, "three_phase_vars", "3-Phase Reactive Power",
            UnitOfReactivePower.VOLT_AMPERE_REACTIVE, SensorDeviceClass.REACTIVE_POWER,
        ),
        # Power Factor
        P14xMeasurementSensor(
            medium, entry, "power_factor", "Power Factor",
            None, SensorDeviceClass.POWER_FACTOR,
        ),
        # Thermal
        P14xMeasurementSensor(
            medium, entry, "thermal_state", "Thermal State",
            "%", None,
            icon="mdi:thermometer",
        ),
        # DC Supply
        P14xMeasurementSensor(
            medium, entry, "dc_supply", "DC Supply Voltage",
            UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE,
        ),
        # Energy sensors (slow polling)
        P14xSlowSensor(
            slow, entry, "wh_forward", "Energy Forward",
            UnitOfEnergy.WATT_HOUR, SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        P14xSlowSensor(
            slow, entry, "wh_reverse", "Energy Reverse",
            UnitOfEnergy.WATT_HOUR, SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        P14xSlowSensor(
            slow, entry, "varh_forward", "Reactive Energy Forward",
            "VArh", None,
            state_class=SensorStateClass.TOTAL_INCREASING,
            icon="mdi:flash",
        ),
        P14xSlowSensor(
            slow, entry, "varh_reverse", "Reactive Energy Reverse",
            "VArh", None,
            state_class=SensorStateClass.TOTAL_INCREASING,
            icon="mdi:flash",
        ),
        # CB monitoring (slow polling)
        P14xSlowSensor(
            slow, entry, "cb_operations", "CB Operations Count",
            None, None,
            state_class=SensorStateClass.TOTAL_INCREASING,
            icon="mdi:counter",
        ),
        P14xSlowSensor(
            slow, entry, "cb_operate_time", "CB Operate Time",
            UnitOfTime.MILLISECONDS, None,
            icon="mdi:timer",
        ),
        # Fault record sensors
        P14xSlowSensor(
            slow, entry, "faulted_phase", "Last Faulted Phase",
            None, None,
            icon="mdi:flash-alert",
        ),
        P14xTripElementSensor(slow, entry),
        P14xSlowSensor(
            slow, entry, "fault_ia", "Fault Current IA",
            UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT,
        ),
        P14xSlowSensor(
            slow, entry, "fault_ib", "Fault Current IB",
            UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT,
        ),
        P14xSlowSensor(
            slow, entry, "fault_ic", "Fault Current IC",
            UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT,
        ),
    ]

    async_add_entities(entities)


class P14xMeasurementSensor(CoordinatorEntity, SensorEntity):
    """Sensor for medium-polling measurement data."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: P14xMediumCoordinator,
        entry: ConfigEntry,
        data_key: str,
        name: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
        icon: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_unique_id = f"{entry.entry_id}_{data_key}"
        if icon:
            self._attr_icon = icon
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
    def native_value(self) -> float | None:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._data_key)


class P14xSlowSensor(CoordinatorEntity, SensorEntity):
    """Sensor for slow-polling data."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: P14xSlowCoordinator,
        entry: ConfigEntry,
        data_key: str,
        name: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None = None,
        icon: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_unique_id = f"{entry.entry_id}_{data_key}"
        if icon:
            self._attr_icon = icon
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
    def native_value(self) -> float | str | None:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._data_key)


class P14xTripElementSensor(CoordinatorEntity, SensorEntity):
    """Sensor that decodes trip elements into readable text."""

    _attr_has_entity_name = True
    _attr_name = "Last Trip Element"
    _attr_icon = "mdi:shield-alert"

    def __init__(
        self,
        coordinator: P14xSlowCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_trip_element"
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
    def native_value(self) -> str | None:
        """Return decoded trip element text."""
        if self.coordinator.data is None:
            return None
        trip_1 = self.coordinator.data.get("trip_elements_1", 0)
        return decode_trip_elements(trip_1)
