# Agent instructions

## Project

This Home Assistant integration reports devices whose meaningful entities have all been unavailable for a configured period, with optional repair issues. Its code lives in `custom_components/offline_devices/`.

## Working in this repository

- Read `README.md` before changing what counts as offline or which devices and entities are excluded; those rules affect the reported device set.
- Keep entity and repair behavior aligned with the README, including the configurable grace period and ignored-device options.

## Validation

- Run `uvx ruff check .` and `uvx ruff format --check .` for Python changes.
- CI runs Hassfest and the shared Ruff checks; it currently has no test job.
- The shared Ruff action is maintained in [`pschmitt/ci-workflows`](https://github.com/pschmitt/ci-workflows).
