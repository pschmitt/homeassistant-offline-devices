"""Optional repair issues for offline devices.

Disabled by default. When enabled in the integration options, one repair
issue is raised per offline device, linking to the device page, its
integration, and (for ZHA) the "add Zigbee device" screen so a flaky device
can be re-paired in one click.
"""

from __future__ import annotations

import voluptuous as vol

from homeassistant.components.repairs import RepairsFlow
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import issue_registry as ir

from .const import (
    CONF_ENABLE_REPAIRS,
    DEFAULT_ENABLE_REPAIRS,
    DOMAIN,
    ISSUE_PREFIX,
    URL_DEVICE_PAGE,
    URL_INTEGRATION_PAGE,
    URL_ZHA_ADD,
)
from .models import OfflineDevice, OfflineReport


def _issue_id(device: OfflineDevice) -> str:
    """Return the repair-issue id for an offline device."""
    return f"{ISSUE_PREFIX}{device.device_id}"


def _translation_key(device: OfflineDevice) -> str:
    """Return the translation key matching the device kind."""
    if device.is_zha:
        return "zha_device_offline"
    if device.is_matter:
        return "matter_device_offline"
    return "device_offline"


def _placeholders(device: OfflineDevice) -> dict[str, str]:
    """Return translation placeholders, including frontend deep links."""
    placeholders = {
        "name": device.name,
        "area": device.area or "—",
        "device_link": URL_DEVICE_PAGE.format(device_id=device.device_id),
    }
    if device.primary_domain:
        placeholders["integration_link"] = URL_INTEGRATION_PAGE.format(
            domain=device.primary_domain
        )
    else:
        placeholders["integration_link"] = URL_DEVICE_PAGE.format(
            device_id=device.device_id
        )
    if device.is_zha:
        placeholders["zha_add_link"] = URL_ZHA_ADD
    return placeholders


@callback
def async_sync_issues(
    hass: HomeAssistant,
    entry: ConfigEntry,
    report: OfflineReport | None,
) -> None:
    """Create/clear repair issues to match the current offline report.

    Passing ``report=None`` (or having repairs disabled) clears every issue
    previously raised by this integration.
    """
    issue_registry = ir.async_get(hass)
    enabled = entry.options.get(CONF_ENABLE_REPAIRS, DEFAULT_ENABLE_REPAIRS)

    devices = report.devices if (report is not None and enabled) else []
    wanted: dict[str, OfflineDevice] = {_issue_id(device): device for device in devices}

    # Remove issues for devices that recovered (or when disabled/unloading).
    for issue in list(issue_registry.issues.values()):
        if issue.domain != DOMAIN:
            continue
        if not issue.issue_id.startswith(ISSUE_PREFIX):
            continue
        if issue.issue_id not in wanted:
            ir.async_delete_issue(hass, DOMAIN, issue.issue_id)

    # Create/refresh issues for currently-offline devices.
    for issue_id, device in wanted.items():
        learn_more_url = (
            URL_ZHA_ADD
            if device.is_zha
            else URL_DEVICE_PAGE.format(device_id=device.device_id)
        )
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=True,
            is_persistent=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=_translation_key(device),
            translation_placeholders=_placeholders(device),
            learn_more_url=learn_more_url,
            data={"device_id": device.device_id, "name": device.name},
        )


class OfflineDeviceRepairFlow(RepairsFlow):
    """Simple acknowledge flow for an offline-device issue."""

    def __init__(self, data: dict | None) -> None:
        """Store the issue data passed at creation time."""
        self._data = data or {}

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Entry point for the repair flow."""
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict | None = None) -> FlowResult:
        """Acknowledge the issue and dismiss it."""
        if user_input is not None:
            return self.async_create_entry(title="", data={})
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
        )


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict | None,
) -> RepairsFlow:
    """Create the repair fix flow for an offline-device issue."""
    del hass, issue_id
    return OfflineDeviceRepairFlow(data)
