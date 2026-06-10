"""Coordinator for the Offline Devices integration."""

from __future__ import annotations

import logging
import re
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_IGNORED_INTEGRATIONS,
    CONF_IGNORED_LABELS,
    CONF_IGNORED_NAMES,
    CONF_MIN_OFFLINE_AGE,
    CONF_MIN_OFFLINE_AGE_MATTER,
    CONF_MIN_OFFLINE_AGE_ZHA,
    CONF_MIN_OFFLINE_AGE_ZWAVE,
    CONF_SCAN_INTERVAL,
    DEFAULT_IGNORED_INTEGRATIONS,
    DEFAULT_IGNORED_LABELS,
    DEFAULT_IGNORED_NAMES,
    DEFAULT_MIN_OFFLINE_AGE,
    DEFAULT_MIN_OFFLINE_AGE_MATTER,
    DEFAULT_MIN_OFFLINE_AGE_ZHA,
    DEFAULT_MIN_OFFLINE_AGE_ZWAVE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    DOMAIN_MATTER,
    DOMAIN_ZHA,
    DOMAIN_ZWAVE,
    STATE_UNAVAILABLE,
)
from .models import OfflineDevice, OfflineReport

_LOGGER = logging.getLogger(__name__)

# Matches labels like "offline_24h" or "offline_2d" (case-insensitive).
_LABEL_OFFLINE_AGE_RE = re.compile(r"^offline_(\d+)([hd])$", re.IGNORECASE)


def _label_min_offline_age(labels: set[str]) -> int | None:
    """Return a per-device min offline age in seconds from a label, or None.

    Recognises labels of the form ``offline_<N>h`` (hours) and
    ``offline_<N>d`` (days).  The first matching label wins.
    """
    for label in labels:
        m = _LABEL_OFFLINE_AGE_RE.match(label)
        if m:
            value = int(m.group(1))
            unit = m.group(2).lower()
            return value * (3600 if unit == "h" else 86400)
    return None


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

    @callback
    def async_setup_event_listeners(self) -> None:
        """Refresh promptly on relevant state and registry changes.

        The poll (``update_interval``) stays on as a backstop, but these
        listeners make detection effectively instant. The coordinator's
        built-in request-refresh debouncer coalesces bursts (e.g. all of a
        device's entities flipping at once), so a flood of state changes still
        results in at most one recompute per cooldown window.
        """

        @callback
        def _schedule_refresh() -> None:
            # async_request_refresh() is a coroutine; from a @callback we must
            # schedule it rather than call it un-awaited. The coordinator's
            # request-refresh debouncer coalesces the bursts these produce.
            self.config_entry.async_create_task(
                self.hass,
                self.async_request_refresh(),
                "offline_devices_event_refresh",
            )

        @callback
        def _on_state_change(event: Event) -> None:
            # Only an entity toggling in/out of "unavailable" can change which
            # devices are fully offline; ignore every other state change.
            old = event.data.get("old_state")
            new = event.data.get("new_state")
            old_unavailable = old is not None and old.state == STATE_UNAVAILABLE
            new_unavailable = new is not None and new.state == STATE_UNAVAILABLE
            if old_unavailable != new_unavailable:
                _schedule_refresh()

        @callback
        def _on_registry_change(_event: Event) -> None:
            # Devices/entities added, removed, enabled, relabelled, etc.
            _schedule_refresh()

        entry = self.config_entry
        entry.async_on_unload(
            self.hass.bus.async_listen(EVENT_STATE_CHANGED, _on_state_change)
        )
        entry.async_on_unload(
            self.hass.bus.async_listen(
                dr.EVENT_DEVICE_REGISTRY_UPDATED, _on_registry_change
            )
        )
        entry.async_on_unload(
            self.hass.bus.async_listen(
                er.EVENT_ENTITY_REGISTRY_UPDATED, _on_registry_change
            )
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

    @property
    def _ignored_integrations(self) -> set[str]:
        """Return the configured set of integration domains to ignore."""
        return {
            domain.casefold()
            for domain in self.config_entry.options.get(
                CONF_IGNORED_INTEGRATIONS, DEFAULT_IGNORED_INTEGRATIONS
            )
            if domain
        }

    @property
    def _min_offline_age(self) -> int:
        """Return the global minimum unavailable age before a device is reported."""
        return self.config_entry.options.get(
            CONF_MIN_OFFLINE_AGE, DEFAULT_MIN_OFFLINE_AGE
        )

    def _effective_min_offline_age(
        self, integration_domains: tuple[str, ...], namespaces: tuple[str, ...]
    ) -> int:
        """Return the effective min_offline_age for a device.

        Checks per-protocol overrides first. Any override of -1 means
        'inherit the global setting'.
        """
        global_age = self._min_offline_age
        if DOMAIN_MATTER in namespaces or DOMAIN_MATTER in integration_domains:
            override = self.config_entry.options.get(
                CONF_MIN_OFFLINE_AGE_MATTER, DEFAULT_MIN_OFFLINE_AGE_MATTER
            )
        elif DOMAIN_ZHA in namespaces or DOMAIN_ZHA in integration_domains:
            override = self.config_entry.options.get(
                CONF_MIN_OFFLINE_AGE_ZHA, DEFAULT_MIN_OFFLINE_AGE_ZHA
            )
        elif DOMAIN_ZWAVE in namespaces or DOMAIN_ZWAVE in integration_domains:
            override = self.config_entry.options.get(
                CONF_MIN_OFFLINE_AGE_ZWAVE, DEFAULT_MIN_OFFLINE_AGE_ZWAVE
            )
        else:
            return global_age
        return override if override >= 0 else global_age

    def _integration_domains(self, device: dr.DeviceEntry) -> tuple[str, ...]:
        """Return all owning integration domains from the device's config entries."""
        domains = {
            entry.domain
            for entry_id in device.config_entries
            if (entry := self.hass.config_entries.async_get_entry(entry_id)) is not None
        }
        return tuple(sorted(domains))

    def _integration_domain(self, device: dr.DeviceEntry) -> str | None:
        """Return the preferred integration domain for links and reporting."""
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
        ignored_integrations = self._ignored_integrations
        ignored_names = self._ignored_names
        ignored_labels = self._ignored_labels
        now = dt_util.utcnow()

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
            integration_domains = self._integration_domains(device)
            if ignored_integrations and any(
                domain.casefold() in ignored_integrations
                for domain in integration_domains
            ):
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
            label_age = _label_min_offline_age(device.labels or set())
            effective_min_age = (
                label_age
                if label_age is not None
                else self._effective_min_offline_age(integration_domains, namespaces)
            )
            offline_since = max(
                (s.last_changed for s in states if s.last_changed is not None),
                default=None,
            )
            if (
                effective_min_age > 0
                and offline_since is not None
                and now - offline_since < timedelta(seconds=effective_min_age)
            ):
                continue
            report.devices.append(
                OfflineDevice(
                    device_id=device.id,
                    name=name,
                    area=area_name,
                    namespaces=namespaces,
                    integration=self._integration_domain(device),
                    offline_since=offline_since,
                )
            )

        report.devices.sort(key=lambda device: device.name.casefold())
        return report
