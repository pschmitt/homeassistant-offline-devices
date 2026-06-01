"""Binary sensor platform for the Offline Devices integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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

    # Scope-level aggregate sensors (all / zha / matter / zwave).
    async_add_entities(
        OfflineDevicesBinarySensor(coordinator, entry, scope) for scope in SCOPES
    )

    # Per-device sensors: one for every physical, non-disabled HA device so
    # automations can reference them before a device has ever gone offline.
    dev_reg = dr.async_get(hass)
    known_device_ids: set[str] = set()

    def _make_sensor(dev_entry: dr.DeviceEntry) -> DeviceOfflineBinarySensor | None:
        """Return a sensor for dev_entry, or None if it should be skipped."""
        if dev_entry.disabled_by is not None:
            return None
        if dev_entry.entry_type is not None:
            return None
        if dev_entry.id in known_device_ids:
            return None
        known_device_ids.add(dev_entry.id)
        return DeviceOfflineBinarySensor(coordinator, dev_entry)

    async_add_entities(
        sensor
        for dev in dev_reg.devices.values()
        if (sensor := _make_sensor(dev)) is not None
    )

    # Add sensors for devices that are registered after initial setup.
    @callback
    def _on_device_registry_updated(event: Event) -> None:
        if event.data.get("action") not in ("create", "update"):
            return
        device_id = event.data.get("device_id")
        if not device_id:
            return
        dev_entry = dev_reg.async_get(device_id)
        if dev_entry is None:
            return
        sensor = _make_sensor(dev_entry)
        if sensor is not None:
            async_add_entities([sensor])

    entry.async_on_unload(
        hass.bus.async_listen(
            dr.EVENT_DEVICE_REGISTRY_UPDATED, _on_device_registry_updated
        )
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


class DeviceOfflineBinarySensor(
    CoordinatorEntity[OfflineDevicesCoordinator], BinarySensorEntity
):
    """Problem binary sensor linked to a physical HA device.

    Always present (off = healthy, on = offline) so automations can reference
    it before the device has ever gone offline.
    """

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_name = "Offline"

    def __init__(
        self,
        coordinator: OfflineDevicesCoordinator,
        dev_entry: dr.DeviceEntry,
    ) -> None:
        """Initialize the per-device problem sensor."""
        super().__init__(coordinator)
        self._device_id = dev_entry.id
        self._attr_unique_id = f"offline_devices_{dev_entry.id}_problem"
        self._attr_device_info = DeviceInfo(identifiers=dev_entry.identifiers)

    @property
    def is_on(self) -> bool:
        """Return True when this device is currently offline."""
        if self.coordinator.data is None:
            return False
        return any(
            d.device_id == self._device_id for d in self.coordinator.data.devices
        )
