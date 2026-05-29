"""Constants for the Offline Devices integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "offline_devices"
PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]

# Scopes exposed as entities. "all" is the global scope; "zha" and "matter"
# are breakdowns for those radios.
SCOPE_ALL = "all"
SCOPE_ZHA = "zha"
SCOPE_MATTER = "matter"
SCOPES: tuple[str, ...] = (SCOPE_ALL, SCOPE_ZHA, SCOPE_MATTER)

# Device-registry identifier domains used to classify a device.
IDENTIFIER_DOMAIN_ZHA = "zha"
IDENTIFIER_DOMAIN_MATTER = "matter"

# A device carrying this label is treated as flaky and never reported as
# offline. Carried over from the previous shell-based implementation.
LABEL_INTERMITTENT = "intermittent"

# The state that marks an entity as unreachable.
STATE_UNAVAILABLE = "unavailable"

# Options.
CONF_SCAN_INTERVAL = "scan_interval"
CONF_ENABLE_REPAIRS = "enable_repairs"
CONF_IGNORED_NAMES = "ignored_names"

DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 10
DEFAULT_ENABLE_REPAIRS = False
DEFAULT_IGNORED_NAMES: list[str] = []

# Attributes exposed on the entities.
ATTR_COUNT = "count"
ATTR_DEVICES = "devices"
ATTR_DEVICE_IDS = "device_ids"
ATTR_MSG = "msg"
ATTR_PRIMARY_INFO = "primary_info"
ATTR_SECONDARY_INFO = "secondary_info"

# Frontend deep links used for repair issues.
URL_DEVICE_PAGE = "/config/devices/device/{device_id}"
URL_INTEGRATION_PAGE = "/config/integrations/integration/{domain}"
URL_ZHA_ADD = "/config/zha/add"

# Repair issue id prefix.
ISSUE_PREFIX = "device_offline_"
