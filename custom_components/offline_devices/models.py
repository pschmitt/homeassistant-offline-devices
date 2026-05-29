"""Data models for the Offline Devices integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .const import (
    DOMAIN_MATTER,
    DOMAIN_ZHA,
    DOMAIN_ZWAVE,
    SCOPE_ALL,
    SCOPE_MATTER,
    SCOPE_ZHA,
    SCOPE_ZWAVE,
)


@dataclass(frozen=True)
class OfflineDevice:
    """A single Home Assistant device whose entities are all unavailable."""

    device_id: str
    name: str
    area: str | None
    # Identifier namespaces from the device registry, e.g. ("zha",) or
    # ("homekit_controller:accessory-id",). Used to classify ZHA/Matter.
    namespaces: tuple[str, ...]
    # The owning integration domain, resolved from the device's config entry
    # (e.g. "homekit_controller", "shelly"). Used for the integration link.
    integration: str | None
    # When the device was last seen going fully offline (max last_changed of
    # its unavailable entities at detection time).
    offline_since: datetime | None

    @property
    def is_zha(self) -> bool:
        """Return True when this is a ZHA (Zigbee) device."""
        return DOMAIN_ZHA in self.namespaces or self.integration == DOMAIN_ZHA

    @property
    def is_matter(self) -> bool:
        """Return True when this is a Matter device."""
        return DOMAIN_MATTER in self.namespaces or self.integration == DOMAIN_MATTER

    @property
    def is_zwave(self) -> bool:
        """Return True when this is a Z-Wave device."""
        return DOMAIN_ZWAVE in self.namespaces or self.integration == DOMAIN_ZWAVE


@dataclass
class OfflineReport:
    """The full set of offline devices for one coordinator refresh."""

    devices: list[OfflineDevice] = field(default_factory=list)

    def for_scope(self, scope: str) -> list[OfflineDevice]:
        """Return the offline devices belonging to a given scope."""
        if scope == SCOPE_ALL:
            return list(self.devices)
        if scope == SCOPE_ZHA:
            return [device for device in self.devices if device.is_zha]
        if scope == SCOPE_MATTER:
            return [device for device in self.devices if device.is_matter]
        if scope == SCOPE_ZWAVE:
            return [device for device in self.devices if device.is_zwave]
        return []
