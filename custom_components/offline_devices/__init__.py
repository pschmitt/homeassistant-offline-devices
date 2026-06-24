"""The Offline Devices integration.

Reports Home Assistant devices whose entities have all become unavailable,
broken down into a global scope plus ZHA and Matter scopes, and (optionally)
raises repair issues that link straight to the affected device.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, Event, HomeAssistant, callback
from homeassistant.helpers import label_registry as lr

from .const import (
    CONF_IGNORED_LABELS,
    DEFAULT_IGNORED_LABELS,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import OfflineDevicesCoordinator
from .repairs import async_sync_issues


@callback
def _ensure_labels_exist(hass: HomeAssistant, label_ids: list[str]) -> None:
    """Create any configured ignore-labels that do not exist yet.

    Labels are referenced by id; when one is missing we create it using the id
    as its name (HA derives the same slug back), so a fresh install gets a
    usable 'intermittent' label out of the box.
    """
    registry = lr.async_get(hass)
    for label_id in label_ids:
        if registry.async_get_label(label_id) is not None:
            continue
        try:
            registry.async_create(name=label_id)
        except ValueError:
            # A label with that name already exists under a different id.
            continue


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Offline Devices from a config entry."""
    _ensure_labels_exist(
        hass, entry.options.get(CONF_IGNORED_LABELS, DEFAULT_IGNORED_LABELS)
    )

    coordinator = OfflineDevicesCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    coordinator.async_setup_event_listeners()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    def _sync_repairs() -> None:
        async_sync_issues(hass, entry, coordinator.data)

    # Reconcile repair issues on every refresh, and once now.
    _sync_repairs()
    entry.async_on_unload(coordinator.async_add_listener(_sync_repairs))
    entry.async_on_unload(entry.add_update_listener(_async_reload_on_options))

    # Re-evaluate once everything has loaded. During startup many devices are
    # transiently unavailable, so the first post-start refresh is the first
    # trustworthy one.
    if hass.state is not CoreState.running:
        _started = False

        @callback
        def _refresh_on_started(_event: Event) -> None:
            nonlocal _started
            _started = True
            entry.async_create_task(
                hass,
                coordinator.async_request_refresh(),
                "offline_devices_started_refresh",
            )

        _cancel_started = hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED, _refresh_on_started
        )

        # Only cancel if the event has not yet fired. Calling the cancel after
        # homeassistant_started fires logs "Unable to remove unknown job listener".
        entry.async_on_unload(lambda: None if _started else _cancel_started())

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Offline Devices config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Clear any issues this entry raised so they do not linger.
        async_sync_issues(hass, entry, None)
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_reload_on_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
