<p align="center">
  <img src="logo.png" width="128" alt="Offline Devices logo">
</p>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/marketplace_repository/?owner=pschmitt&amp;repository=homeassistant-offline-devices&amp;category=integration"><img src="https://my.home-assistant.io/badges/marketplace_repository.svg" alt="Open this integration in Home Assistant Marketplace"></a>
</p>

<h1 align="center">Offline Devices for Home Assistant</h1>

<p align="center">Find devices whose meaningful entities are all unavailable, with optional repairs.</p>

## Features

- **Device-wide detection:** Mark a device offline after all its meaningful entities remain unavailable for a configurable grace period. See [Offline detection](docs/detection.md).
- **Integration breakdowns:** Show overall, ZHA, Matter and Z-Wave counts and problem sensors.
- **Fast updates:** Re-evaluate on state or registry changes, with a polling backstop.
- **Optional repairs:** Create issues for offline devices, and exclude intermittent or ignored devices.

## Install

Use the Marketplace badge above on Home Assistant 2026.11 or later to add this
repository as a custom integration. On older versions, add it as a HACS
custom repository of type **Integration**. Install and restart Home Assistant.
The badge does not imply a public catalog listing. For manual installation,
copy `custom_components/offline_devices/` into Home Assistant's
`custom_components/` directory and restart.

## Quick start

1. Add **Offline Devices** under **Settings → Devices & services → Add integration**.
2. Set the minimum offline age and any integrations or labels to ignore.
3. Add the problem sensor or offline count to a dashboard; enable repair issues if useful.

## Documentation

| Topic | Description |
|-------|-------------|
| [Offline detection](docs/detection.md) | Detection criteria, entities, options and repairs |
| [Legacy shell detector](contrib/legacy-shell/) | Earlier command-line implementation |

## License

[GPL-3.0-or-later](LICENSE).
