"""Binary sensor platform for the Offline Devices integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SCOPES
from .coordinator import OfflineDevicesCoordinator
from .entity import SCOPE_ICONS, SCOPE_LABELS, OfflineDevicesEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the offline-device problem binary sensors."""
    coordinator: OfflineDevicesCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        OfflineDevicesBinarySensor(coordinator, entry, scope) for scope in SCOPES
    )


class OfflineDevicesBinarySensor(OfflineDevicesEntity, BinarySensorEntity):
    """Problem sensor that is on when any device in the scope is offline."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, entry, scope) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry, scope)
        self._attr_unique_id = f"{entry.entry_id}_{scope}_problem"
        self._attr_name = SCOPE_LABELS.get(scope, scope)
        self._attr_icon = SCOPE_ICONS.get(scope)

    @property
    def is_on(self) -> bool:
        """Return True when at least one device in this scope is offline."""
        return self._count > 0

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return details about the offline devices."""
        return self._build_attributes()
