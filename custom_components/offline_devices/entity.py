"""Shared entity helpers for the Offline Devices integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_COUNT,
    ATTR_DEVICE_IDS,
    ATTR_DEVICES,
    ATTR_OFFLINE_NOW_DEVICES,
    ATTR_OFFLINE_SINCE,
    ATTR_MSG,
    ATTR_PRIMARY_INFO,
    ATTR_SECONDARY_INFO,
    DOMAIN,
    SCOPE_ALL,
    SCOPE_MATTER,
    SCOPE_ZHA,
    SCOPE_ZWAVE,
)
from .coordinator import OfflineDevicesCoordinator
from .models import OfflineDevice

# Human-readable labels for each scope, used in names and messages.
SCOPE_LABELS: dict[str, str] = {
    SCOPE_ALL: "Devices Offline",
    SCOPE_ZHA: "ZHA Devices Offline",
    SCOPE_MATTER: "Matter Devices Offline",
    SCOPE_ZWAVE: "Z-Wave Devices Offline",
}
SCOPE_NOUNS: dict[str, str] = {
    SCOPE_ALL: "devices",
    SCOPE_ZHA: "ZHA devices",
    SCOPE_MATTER: "Matter devices",
    SCOPE_ZWAVE: "Z-Wave devices",
}
# Icons shared by the binary sensor and count sensor of each scope.
SCOPE_ICONS: dict[str, str] = {
    SCOPE_ALL: "mdi:devices",
    SCOPE_ZHA: "mdi:zigbee",
    SCOPE_MATTER: "cbi:matter",
    SCOPE_ZWAVE: "mdi:z-wave",
}


class OfflineDevicesEntity(CoordinatorEntity[OfflineDevicesCoordinator]):
    """Base entity bound to the integration's single service device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OfflineDevicesCoordinator,
        entry: ConfigEntry,
        scope: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._scope = scope
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Offline Devices",
            manufacturer="pschmitt",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _offline_devices(self) -> list[OfflineDevice]:
        """Return the offline devices for this entity's scope."""
        if self.coordinator.data is None:
            return []
        return self.coordinator.data.for_scope(self._scope)

    @property
    def _count(self) -> int:
        """Return the number of offline devices for this scope."""
        return len(self._offline_devices)

    @property
    def _offline_now_devices(self) -> list[OfflineDevice]:
        """Return devices currently offline for this scope, ignoring duration."""
        if self.coordinator.data is None:
            return []
        return self.coordinator.data.offline_now_for_scope(self._scope)

    def _build_attributes(self) -> dict[str, object]:
        """Return shared state attributes describing the offline devices."""
        devices = self._offline_devices
        names = [device.name for device in devices]
        noun = SCOPE_NOUNS.get(self._scope, "devices")
        if names:
            joined = ", ".join(names)
            msg = f"{len(names)} {noun} offline: {joined}"
            primary = f"{len(names)} {noun} offline"
        else:
            joined = ""
            msg = f"All {noun} online"
            primary = f"All {noun} online"
        return {
            ATTR_COUNT: len(names),
            ATTR_DEVICES: names,
            ATTR_OFFLINE_NOW_DEVICES: [
                device.name for device in self._offline_now_devices
            ],
            ATTR_DEVICE_IDS: [device.device_id for device in devices],
            ATTR_OFFLINE_SINCE: [
                device.offline_since.isoformat() if device.offline_since else None
                for device in devices
            ],
            ATTR_MSG: msg,
            ATTR_PRIMARY_INFO: primary,
            ATTR_SECONDARY_INFO: joined,
        }
