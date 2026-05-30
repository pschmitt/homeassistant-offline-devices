"""Constants for the Offline Devices integration."""

from __future__ import annotations

from homeassistant.const import Platform

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

# The state that marks an entity as unreachable.
STATE_UNAVAILABLE = "unavailable"

# Options.
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MIN_OFFLINE_AGE = "min_offline_age"
CONF_ENABLE_REPAIRS = "enable_repairs"
CONF_IGNORED_NAMES = "ignored_names"
CONF_IGNORED_LABELS = "ignored_labels"

DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 10
DEFAULT_MIN_OFFLINE_AGE = 0
MIN_OFFLINE_AGE = 0
DEFAULT_ENABLE_REPAIRS = False
DEFAULT_IGNORED_NAMES: list[str] = []
# Devices carrying any of these labels are ignored. Defaults to the
# "intermittent" label to preserve the previous behavior.
DEFAULT_IGNORED_LABELS: list[str] = [LABEL_INTERMITTENT]

# Attributes exposed on the entities.
ATTR_COUNT = "count"
ATTR_DEVICES = "devices"
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
