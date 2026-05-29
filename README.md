# Offline Devices for Home Assistant

`offline_devices` is a Home Assistant custom integration that reports devices
whose entities have **all** become `unavailable` — i.e. the device has dropped
off the network — and surfaces that as a handful of tidy entities plus optional
repair issues.

It replaces ad-hoc `command_line` + template-sensor setups with a single,
integration-agnostic detector.

## What it creates

A single **Offline Devices** service device with these entities:

| Entity | Type | Meaning |
| --- | --- | --- |
| `binary_sensor.offline_devices_devices_offline` | problem | **any** device offline |
| `binary_sensor.offline_devices_zha_devices_offline` | problem | a ZHA device offline |
| `binary_sensor.offline_devices_matter_devices_offline` | problem | a Matter device offline |
| `binary_sensor.offline_devices_z_wave_devices_offline` | problem | a Z-Wave device offline |
| `sensor.offline_devices_offline_count` | count | number of offline devices (all) |
| `sensor.offline_devices_zha_offline_count` | count | number of offline ZHA devices |
| `sensor.offline_devices_matter_offline_count` | count | number of offline Matter devices |
| `sensor.offline_devices_z_wave_offline_count` | count | number of offline Z-Wave devices |

Every entity exposes the same attributes: `count`, `devices` (names),
`device_ids`, `msg`, `primary_info`, `secondary_info` — convenient for
Lovelace and notifications.

The global scope counts **all** offline devices; `zha`, `matter` and `zwave`
are breakdowns of that same set.

> The Matter entities use the `cbi:matter` icon from the
> [custom-brand-icons](https://github.com/elax46/custom-brand-icons) frontend
> module. Install it (e.g. via HACS) for the icon to render; otherwise change
> the icon in the entity settings.

## How "offline" is decided

A device is considered offline when **all** of its *meaningful* entities are
`unavailable`. Meaningful entities are:

- enabled (not disabled in the entity registry),
- not diagnostic/config entities (these are skipped — e.g. ZHA/HomeKit
  *identify* buttons that stay `unknown` rather than `unavailable`),
- not stateless `event.*` entities.

Devices are skipped when they are disabled, are helper/service devices, carry
the `intermittent` device-registry label, or match an ignored-name substring.

ZHA and Matter devices are recognized from their device-registry identifiers.

## Options

- **Update interval** — how often the detector re-evaluates (default 60 s).
- **Create repair issues** — *off by default*. When on, one repair issue is
  raised per offline device, linking to the device page, its integration, and
  — for ZHA — the *add Zigbee device* screen for quick re-pairing. Issues clear
  automatically when the device comes back.
- **Ignored device-name substrings** — case-insensitive names to never report.
  The `intermittent` label is always honored as well.

## Installation

### HACS

1. Open HACS.
2. Add `https://github.com/pschmitt/homeassistant-offline-devices` as a custom
   repository of type **Integration**.
3. Install **Offline Devices** and restart Home Assistant.
4. Add the integration from **Settings → Devices & services**.

### Manual

Copy `custom_components/offline_devices` into your `custom_components/`
directory and restart Home Assistant.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
