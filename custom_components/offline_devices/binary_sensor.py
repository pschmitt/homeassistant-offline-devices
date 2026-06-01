"""Binary sensor platform for the Offline Devices integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SCOPES
from .coordinator import OfflineDevicesCoordinator
from .entity import SCOPE_ICONS, SCOPE_LABELS, OfflineDevicesEntity

_DEVICE_SENSOR_PREFIX = "offline_devices_"
_DEVICE_SENSOR_SUFFIX = "_problem"


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

    # Per-device sensors: re-register any that were created in a previous run.
    dev_reg = dr.async_get(hass)
    entity_reg = er.async_get(hass)
    known_device_ids: set[str] = set()

    restore_entities: list[DeviceOfflineBinarySensor] = []
    for reg_entry in er.async_entries_for_config_entry(entity_reg, entry.entry_id):
        uid = reg_entry.unique_id or ""
        if uid.startswith(_DEVICE_SENSOR_PREFIX) and uid.endswith(_DEVICE_SENSOR_SUFFIX):
            device_id = uid[len(_DEVICE_SENSOR_PREFIX) : -len(_DEVICE_SENSOR_SUFFIX)]
            if device_id and device_id not in known_device_ids:
                dev_entry = dev_reg.async_get(device_id)
                if dev_entry is not None:
                    known_device_ids.add(device_id)
                    restore_entities.append(
                        DeviceOfflineBinarySensor(coordinator, dev_entry)
                    )
    if restore_entities:
        async_add_entities(restore_entities)

    # Dynamically add per-device sensors as new offline devices are discovered.
    @callback
    def _add_new_device_sensors() -> None:
        if coordinator.data is None:
            return
        new_entities: list[DeviceOfflineBinarySensor] = []
        for device in coordinator.data.devices:
            if device.device_id in known_device_ids:
                continue
            known_device_ids.add(device.device_id)
            dev_entry = dev_reg.async_get(device.device_id)
            if dev_entry is None:
                continue
            new_entities.append(DeviceOfflineBinarySensor(coordinator, dev_entry))
        if new_entities:
            async_add_entities(new_entities)

    entry.async_on_unload(coordinator.async_add_listener(_add_new_device_sensors))
    _add_new_device_sensors()


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

    Appears on the device's own page and turns on whenever the coordinator
    reports that device as fully unavailable.
    """

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
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
        self._attr_unique_id = (
            f"{_DEVICE_SENSOR_PREFIX}{dev_entry.id}{_DEVICE_SENSOR_SUFFIX}"
        )
        self._attr_device_info = DeviceInfo(identifiers=dev_entry.identifiers)

    @property
    def is_on(self) -> bool:
        """Return True when this device is currently offline."""
        if self.coordinator.data is None:
            return False
        return any(
            d.device_id == self._device_id for d in self.coordinator.data.devices
        )
