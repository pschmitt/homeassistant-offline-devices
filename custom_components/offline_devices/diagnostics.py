"""Diagnostics for the Offline Devices integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, SCOPES
from .coordinator import OfflineDevicesCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> dict:
    """Return diagnostics for a config entry."""
    coordinator: OfflineDevicesCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    report = coordinator.data

    scopes: dict[str, object] = {}
    for scope in SCOPES:
        devices = report.for_scope(scope) if report is not None else []
        scopes[scope] = {
            "count": len(devices),
            "devices": [
                {
                    "device_id": device.device_id,
                    "name": device.name,
                    "area": device.area,
                    "domains": list(device.domains),
                }
                for device in devices
            ],
        }

    return {
        "options": dict(config_entry.options),
        "scopes": scopes,
    }
