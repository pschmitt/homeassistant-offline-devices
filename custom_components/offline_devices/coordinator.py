"""Coordinator for the Offline Devices integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_IGNORED_LABELS,
    CONF_IGNORED_NAMES,
    CONF_SCAN_INTERVAL,
    DEFAULT_IGNORED_LABELS,
    DEFAULT_IGNORED_NAMES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    STATE_UNAVAILABLE,
)
from .models import OfflineDevice, OfflineReport

_LOGGER = logging.getLogger(__name__)


def _is_ignored(name: str, ignored_names: list[str]) -> bool:
    """Return True when a device name matches a configured ignore substring."""
    lowered = name.casefold()
    return any(token and token.casefold() in lowered for token in ignored_names)


def _meaningful_entities_by_device(
    entity_registry: er.EntityRegistry,
) -> dict[str, list[str]]:
    """Map device_id -> entity_ids that signal reachability.

    Mirrors the previous shell implementation: enabled entities only, no
    diagnostic/config entities (e.g. ZHA/HomeKit "identify" buttons that stay
    ``unknown`` rather than ``unavailable`` when a device drops off), and no
    stateless ``event.*`` entities.
    """
    result: dict[str, list[str]] = {}
    for entry in entity_registry.entities.values():
        if entry.device_id is None:
            continue
        if entry.disabled_by is not None:
            continue
        if entry.entity_category is not None:
            continue
        if entry.entity_id.startswith("event."):
            continue
        result.setdefault(entry.device_id, []).append(entry.entity_id)
    return result


class OfflineDevicesCoordinator(DataUpdateCoordinator[OfflineReport]):
    """Evaluate which Home Assistant devices are fully unavailable."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=timedelta(
                seconds=config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                )
            ),
        )

    @property
    def _ignored_names(self) -> list[str]:
        """Return the configured list of ignored device-name substrings."""
        return self.config_entry.options.get(
            CONF_IGNORED_NAMES, DEFAULT_IGNORED_NAMES
        )

    @property
    def _ignored_labels(self) -> set[str]:
        """Return the configured set of device label ids to ignore."""
        return set(
            self.config_entry.options.get(
                CONF_IGNORED_LABELS, DEFAULT_IGNORED_LABELS
            )
        )

    def _integration_domain(self, device: dr.DeviceEntry) -> str | None:
        """Return the owning integration domain from the device's config entry."""
        entry_id = device.primary_config_entry or next(
            iter(device.config_entries), None
        )
        if entry_id is None:
            return None
        entry = self.hass.config_entries.async_get_entry(entry_id)
        return entry.domain if entry else None

    async def _async_update_data(self) -> OfflineReport:
        """Recompute the offline-device report from the registries and states."""
        return self._compute()

    def _compute(self) -> OfflineReport:
        """Find every device whose meaningful entities are all unavailable."""
        device_registry = dr.async_get(self.hass)
        entity_registry = er.async_get(self.hass)
        area_registry = ar.async_get(self.hass)
        entities_by_device = _meaningful_entities_by_device(entity_registry)
        ignored_names = self._ignored_names
        ignored_labels = self._ignored_labels

        report = OfflineReport()
        for device in device_registry.devices.values():
            if device.disabled_by is not None:
                continue
            # Skip helper / service devices; only physical devices can go offline.
            if device.entry_type is not None:
                continue
            if ignored_labels and (device.labels or set()) & ignored_labels:
                continue

            name = device.name_by_user or device.name or device.id
            if _is_ignored(name, ignored_names):
                continue

            entity_ids = entities_by_device.get(device.id)
            if not entity_ids:
                continue

            states = [
                state
                for state in (self.hass.states.get(eid) for eid in entity_ids)
                if state is not None
            ]
            if not states:
                continue
            if not all(state.state == STATE_UNAVAILABLE for state in states):
                continue

            area_name: str | None = None
            if device.area_id:
                area = area_registry.async_get_area(device.area_id)
                area_name = area.name if area else None

            namespaces = tuple(
                sorted({identifier[0] for identifier in device.identifiers})
            )
            report.devices.append(
                OfflineDevice(
                    device_id=device.id,
                    name=name,
                    area=area_name,
                    namespaces=namespaces,
                    integration=self._integration_domain(device),
                )
            )

        report.devices.sort(key=lambda device: device.name.casefold())
        return report
