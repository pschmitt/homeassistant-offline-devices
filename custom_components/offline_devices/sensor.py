"""Sensor platform for the Offline Devices integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SCOPES
from .coordinator import OfflineDevicesCoordinator
from .entity import OfflineDevicesEntity

_NAMES: dict[str, str] = {
    "all": "Offline Count",
    "zha": "ZHA Offline Count",
    "matter": "Matter Offline Count",
}
_ICONS: dict[str, str] = {
    "all": "mdi:devices",
    "zha": "mdi:zigbee",
    "matter": "mdi:matter",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the offline-device count sensors."""
    coordinator: OfflineDevicesCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        OfflineDevicesCountSensor(coordinator, entry, scope) for scope in SCOPES
    )


class OfflineDevicesCountSensor(OfflineDevicesEntity, SensorEntity):
    """Sensor whose state is the number of offline devices in a scope."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "devices"

    def __init__(self, coordinator, entry, scope) -> None:
        """Initialize the count sensor."""
        super().__init__(coordinator, entry, scope)
        self._attr_unique_id = f"{entry.entry_id}_{scope}_count"
        self._attr_name = _NAMES.get(scope, scope)
        self._attr_icon = _ICONS.get(scope)

    @property
    def native_value(self) -> int:
        """Return the offline-device count for this scope."""
        return self._count

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return details about the offline devices."""
        return self._build_attributes()
