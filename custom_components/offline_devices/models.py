"""Data models for the Offline Devices integration."""

from __future__ import annotations

from dataclasses import dataclass, field

from .const import SCOPE_ALL, SCOPE_MATTER, SCOPE_ZHA


@dataclass(frozen=True)
class OfflineDevice:
    """A single Home Assistant device whose entities are all unavailable."""

    device_id: str
    name: str
    area: str | None
    # Integration domains taken from the device registry identifiers,
    # e.g. ("zha",) or ("homekit_controller",).
    domains: tuple[str, ...]

    @property
    def is_zha(self) -> bool:
        """Return True when this is a ZHA (Zigbee) device."""
        return "zha" in self.domains

    @property
    def is_matter(self) -> bool:
        """Return True when this is a Matter device."""
        return "matter" in self.domains

    @property
    def primary_domain(self) -> str | None:
        """Return the first integration domain, if any."""
        return self.domains[0] if self.domains else None


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
        return []
