# Offline detection

A device counts as offline when all its meaningful entities have been
`unavailable` for at least the configured minimum offline age. Only enabled,
non-diagnostic, non-configuration, stateful entities count. Stateless `event.*`
entities and diagnostic buttons that stay `unknown` do not prevent detection.
Disabled devices, helper/service devices, ignored integrations, devices with
ignored labels (by default `intermittent`) and devices matching ignored-name
substrings are excluded. ZHA and Matter devices are identified through their
device-registry identifiers.

Detection responds to entity-state and device/entity-registry changes with a
debounce. A 60-second poll by default serves as a backstop. The minimum
offline age defaults to one hour, suppressing brief outages.

## Entities

A single Offline Devices service device exposes:

| Entity | State |
|--------|-------|
| `binary_sensor.offline_devices_devices_offline` | Any device offline |
| `binary_sensor.offline_devices_zha_devices_offline` | ZHA device offline |
| `binary_sensor.offline_devices_matter_devices_offline` | Matter device offline |
| `binary_sensor.offline_devices_z_wave_devices_offline` | Z-Wave device offline |
| `sensor.offline_devices_offline_count` | Overall count |
| `sensor.offline_devices_zha_offline_count` | ZHA count |
| `sensor.offline_devices_matter_offline_count` | Matter count |
| `sensor.offline_devices_z_wave_offline_count` | Z-Wave count |

Each entity supplies `count`, device names in `devices`, names of all devices
unavailable right now in `offline_now_devices` (before the grace period),
`device_ids`, `msg`, `primary_info` and `secondary_info` attributes. The ZHA,
Matter and Z-Wave counts break down the overall set. The Matter entities use
the `cbi:matter` icon from
[custom-brand-icons](https://github.com/elax46/custom-brand-icons); install
that frontend module or change the entity icon if it is unavailable.

## Options and repairs

Set the update interval, minimum offline age, ignored integrations, ignored
device-name substrings and ignored labels in the integration options. Optional
per-device repair issues are off by default. When enabled, each issue links to
the device, its integration, and, for ZHA, the add-device screen; the issue
clears when the device returns.
