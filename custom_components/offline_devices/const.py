"""Constants for the Offline Devices integration."""

from __future__ import annotations

from homeassistant.const import STATE_UNAVAILABLE, Platform

DOMAIN = "offline_devices"
PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]

# Scopes exposed as entities. "all" is the global scope; "zha", "matter" and
# "zwave" are per-radio breakdowns.
SCOPE_ALL = "all"
SCOPE_ZHA = "zha"
SCOPE_MATTER = "matter"
SCOPE_ZWAVE = "zwave"
SCOPES: tuple[str, ...] = (SCOPE_ALL, SCOPE_ZHA, SCOPE_MATTER, SCOPE_ZWAVE)

# Integration domains used to classify a device.
DOMAIN_ZHA = "zha"
DOMAIN_MATTER = "matter"
DOMAIN_ZWAVE = "zwave_js"

# Default label that marks a device as flaky so it is never reported as
# offline. Carried over from the previous shell-based implementation.
LABEL_INTERMITTENT = "intermittent"

# The state that marks an entity as unreachable (re-exported for local use).
__all__ = ["STATE_UNAVAILABLE"]

# Options.
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MIN_OFFLINE_AGE = "min_offline_age"
CONF_ENABLE_REPAIRS = "enable_repairs"
CONF_IGNORED_INTEGRATIONS = "ignored_integrations"
CONF_IGNORED_NAMES = "ignored_names"
CONF_IGNORED_LABELS = "ignored_labels"

DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 10
DEFAULT_MIN_OFFLINE_AGE = 3600
MIN_OFFLINE_AGE = 0
DEFAULT_ENABLE_REPAIRS = False

# Per-protocol offline age overrides (-1 = inherit the global min_offline_age).
CONF_MIN_OFFLINE_AGE_ZHA = "min_offline_age_zha"
CONF_MIN_OFFLINE_AGE_MATTER = "min_offline_age_matter"
CONF_MIN_OFFLINE_AGE_ZWAVE = "min_offline_age_zwave"
DEFAULT_MIN_OFFLINE_AGE_ZHA = -1
DEFAULT_MIN_OFFLINE_AGE_MATTER = -1
DEFAULT_MIN_OFFLINE_AGE_ZWAVE = -1
# Minimum allowed value for a protocol override (-1 = sentinel for "inherit").
MIN_OFFLINE_AGE_OVERRIDE = -1
DEFAULT_IGNORED_INTEGRATIONS: list[str] = []
DEFAULT_IGNORED_NAMES: list[str] = []
# Devices carrying any of these labels are ignored. Defaults to the
# "intermittent" label to preserve the previous behavior.
DEFAULT_IGNORED_LABELS: list[str] = [LABEL_INTERMITTENT]

CONF_MONITOR_SERVICE_DEVICES = "monitor_service_devices"
DEFAULT_MONITOR_SERVICE_DEVICES = False

# Attributes exposed on the entities.
ATTR_COUNT = "count"
ATTR_DEVICES = "devices"
# Devices currently fully unavailable, ignoring the min_offline_age grace
# period (i.e. the raw set before the duration filter is applied).
ATTR_OFFLINE_NOW_DEVICES = "offline_now_devices"
ATTR_DEVICE_IDS = "device_ids"
ATTR_OFFLINE_SINCE = "offline_since"
ATTR_MSG = "msg"
ATTR_PRIMARY_INFO = "primary_info"
ATTR_SECONDARY_INFO = "secondary_info"

# Frontend deep links used for repair issues.
URL_DEVICE_PAGE = "/config/devices/device/{device_id}"
URL_INTEGRATION_PAGE = "/config/integrations/integration/{domain}"
URL_ZHA_ADD = "/config/zha/add"

# Repair issue id prefix.
ISSUE_PREFIX = "device_offline_"
