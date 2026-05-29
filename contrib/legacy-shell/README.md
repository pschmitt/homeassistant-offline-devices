# Legacy shell implementation (archived)

Before this integration existed, offline-device detection was done with a
shell script driven by Home Assistant `command_line` sensors. These files are
kept here for reference and as a backup; they are **not** used by the
integration.

## Files

- `hass-ws.sh` — dispatches `zha | matter | generic | devices offline` (and an
  unrelated `restart-required`) subcommands, querying the HA WebSocket API and
  emitting a JSON summary (`count`, `devices`, `msg`, …).
- `hass_ws.py` — a tiny WebSocket client used by `hass-ws.sh` to call HA WS
  commands (`config/device_registry/list`, `zha/devices`, `get_states`, …).

## How it was wired

```yaml
# command_line sensor
- sensor:
    name: "ZHA Offline Devices"
    command: '/config/scripts/hass-ws.sh zha offline'
    value_template: '{{ value_json.count }}'
    json_attributes: [count, devices, msg, primary_info, secondary_info]
```

The integration replaces this with native device/entity-registry inspection:
a device is offline when all of its meaningful entities are `unavailable`.
The `generic`/`matter` cases here are where that "all entities unavailable"
heuristic originated.
