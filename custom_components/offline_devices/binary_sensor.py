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
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_MONITOR_SERVICE_DEVICES,
    DEFAULT_MONITOR_SERVICE_DEVICES,
    DOMAIN,
    SCOPES,
    STATE_UNAVAILABLE,
)
from .coordinator import OfflineDevicesCoordinator, _meaningful_entities_by_device
from .entity import SCOPE_ICONS, SCOPE_LABELS, OfflineDevicesEntity


def _should_skip_device(
    dev_entry: dr.DeviceEntry, *, monitor_service_devices: bool = False
) -> bool:
    """Return True for devices that should not get a per-device reachable sensor."""
    if dev_entry.disabled_by is not None:
        return True
    if dev_entry.entry_type is not None and not monitor_service_devices:
        return True
    return False


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

    # Per-device sensors: one for every eligible HA device so automations can
    # reference them before a device has ever gone offline.
    monitor_service = entry.options.get(
        CONF_MONITOR_SERVICE_DEVICES, DEFAULT_MONITOR_SERVICE_DEVICES
    )
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    known_device_ids: set[str] = set()

    def _make_sensor(dev_entry: dr.DeviceEntry) -> DeviceOfflineBinarySensor | None:
        """Return a sensor for dev_entry, or None if it should be skipped."""
        if _should_skip_device(dev_entry, monitor_service_devices=monitor_service):
            return None
        if dev_entry.id in known_device_ids:
            return None
        entity_ids = _meaningful_entities_by_device(er.async_get(hass)).get(dev_entry.id)
        if not entity_ids:
            return None
        known_device_ids.add(dev_entry.id)
        return DeviceOfflineBinarySensor(coordinator, dev_entry)

    # Remove stale per-device sensor entries whose device no longer qualifies
    # (e.g. service devices when the monitor_service_devices option is off).
    for ent_entry in ent_reg.entities.get_entries_for_config_entry_id(entry.entry_id):
        if not ent_entry.unique_id.startswith("offline_devices_") or not ent_entry.unique_id.endswith("_problem"):
            continue
        # Extract device_id from unique_id: "offline_devices_{device_id}_problem"
        device_id = ent_entry.unique_id[len("offline_devices_"):-len("_problem")]
        dev_entry = dev_reg.async_get(device_id)
        if dev_entry is None or _should_skip_device(
            dev_entry, monitor_service_devices=monitor_service
        ):
            ent_reg.async_remove(ent_entry.entity_id)
            if dev_entry is not None:
                dev_reg.async_update_device(
                    dev_entry.id, remove_config_entry_id=entry.entry_id
                )

    # Also sweep the device registry for any external device that still lists
    # this config entry but should no longer have a per-device sensor (e.g.
    # the entity was already removed in a prior restart but the config-entry
    # association was never cleaned up).
    # Skip the integration's own device (identifiers contain DOMAIN).
    for dev in dev_reg.devices.get_devices_for_config_entry_id(entry.entry_id):
        if any(ns == DOMAIN for ns, _ in dev.identifiers):
            continue
        if _should_skip_device(dev, monitor_service_devices=monitor_service):
            dev_reg.async_update_device(dev.id, remove_config_entry_id=entry.entry_id)

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

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_name = "Reachable"

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
        """Return True when this device is currently reachable.

        Checks raw entity states directly so that ignored devices (e.g. those
        labelled 'intermittent') still reflect their actual connectivity.
        """
        entity_registry = er.async_get(self.hass)
        entity_ids = _meaningful_entities_by_device(entity_registry).get(
            self._device_id, []
        )
        if not entity_ids:
            return True
        states = [
            s for eid in entity_ids if (s := self.hass.states.get(eid)) is not None
        ]
        if not states:
            return True
        return not all(s.state == STATE_UNAVAILABLE for s in states)
