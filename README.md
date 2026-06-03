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
`unavailable` for at least the configured minimum offline age. Meaningful
entities are:

- enabled (not disabled in the entity registry),
- not diagnostic/config entities (these are skipped — e.g. ZHA/HomeKit
  *identify* buttons that stay `unknown` rather than `unavailable`),
- not stateless `event.*` entities.

Devices are skipped when they are disabled, are helper/service devices, carry
the `intermittent` device-registry label, or match an ignored-name substring.

ZHA and Matter devices are recognized from their device-registry identifiers.

## Options

- **Update interval** — backstop poll interval (default 60 s). Detection is
  primarily **event-driven**: the integration re-evaluates immediately when an
  entity goes in/out of `unavailable` or when the device/entity registries
  change (debounced to coalesce bursts), so the poll is just a safety net.
- **Minimum offline age** — how long a device must stay fully unavailable before
  it is reported (default 3600 s). Increase this to suppress short offline flaps.
- **Create repair issues** — *off by default*. When on, one repair issue is
  raised per offline device, linking to the device page, its integration, and
  — for ZHA — the *add Zigbee device* screen for quick re-pairing. Issues clear
  automatically when the device comes back.
- **Ignored integrations** — devices owned by any of these integration domains
  are never reported.
- **Ignored device-name substrings** — case-insensitive names to never report.
- **Ignored device labels** — devices carrying any of these labels are never
  reported. Defaults to the `intermittent` label.

## Installation

### HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pschmitt&repository=homeassistant-offline-devices&category=integration)

1. Click the badge above, or open HACS and add `https://github.com/pschmitt/homeassistant-offline-devices` as a custom repository of type **Integration**.
2. Install **Offline Devices**.
3. Restart Home Assistant.
4. Add the integration from **Settings → Devices & services**.

### Manual

Copy `custom_components/offline_devices` into your `custom_components/`
directory and restart Home Assistant.

## Prior art

This integration supersedes a shell-based `command_line` implementation, kept
for reference under [`contrib/legacy-shell/`](contrib/legacy-shell/). The
"all entities unavailable" heuristic originated there.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
