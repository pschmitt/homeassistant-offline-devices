"""Config flow for the Offline Devices integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    LabelSelector,
    LabelSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_ENABLE_REPAIRS,
    CONF_IGNORED_INTEGRATIONS,
    CONF_IGNORED_LABELS,
    CONF_IGNORED_NAMES,
    CONF_MIN_OFFLINE_AGE,
    CONF_SCAN_INTERVAL,
    DEFAULT_ENABLE_REPAIRS,
    DEFAULT_IGNORED_INTEGRATIONS,
    DEFAULT_IGNORED_LABELS,
    DEFAULT_IGNORED_NAMES,
    DEFAULT_MIN_OFFLINE_AGE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_OFFLINE_AGE,
    MIN_SCAN_INTERVAL,
)

TITLE = "Offline Devices"


class OfflineDevicesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Offline Devices."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OfflineDevicesOptionsFlow:
        """Return the options flow."""
        return OfflineDevicesOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the single-instance setup step."""
        # Only one instance makes sense: it already inspects every device.
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title=TITLE,
                data={},
                options={
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                    CONF_MIN_OFFLINE_AGE: DEFAULT_MIN_OFFLINE_AGE,
                    CONF_ENABLE_REPAIRS: DEFAULT_ENABLE_REPAIRS,
                    CONF_IGNORED_INTEGRATIONS: DEFAULT_IGNORED_INTEGRATIONS,
                    CONF_IGNORED_NAMES: DEFAULT_IGNORED_NAMES,
                    CONF_IGNORED_LABELS: DEFAULT_IGNORED_LABELS,
                },
            )

        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))


class OfflineDevicesOptionsFlow(OptionsFlow):
    """Handle options for Offline Devices."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        integration_domains = sorted(
            {
                entry.domain
                for entry in self.hass.config_entries.async_entries()
                if entry.domain != DOMAIN
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            mode=NumberSelectorMode.BOX,
                            step=1,
                            unit_of_measurement="s",
                        )
                    ),
                    vol.Required(
                        CONF_MIN_OFFLINE_AGE,
                        default=options.get(
                            CONF_MIN_OFFLINE_AGE, DEFAULT_MIN_OFFLINE_AGE
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_OFFLINE_AGE,
                            mode=NumberSelectorMode.BOX,
                            step=1,
                            unit_of_measurement="s",
                        )
                    ),
                    vol.Required(
                        CONF_ENABLE_REPAIRS,
                        default=options.get(
                            CONF_ENABLE_REPAIRS, DEFAULT_ENABLE_REPAIRS
                        ),
                    ): BooleanSelector(),
                    vol.Optional(
                        CONF_IGNORED_INTEGRATIONS,
                        default=options.get(
                            CONF_IGNORED_INTEGRATIONS,
                            DEFAULT_IGNORED_INTEGRATIONS,
                        ),
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=integration_domains,
                            multiple=True,
                            custom_value=True,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                    vol.Optional(
                        CONF_IGNORED_NAMES,
                        default=options.get(
                            CONF_IGNORED_NAMES, DEFAULT_IGNORED_NAMES
                        ),
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=[],
                            multiple=True,
                            custom_value=True,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                    vol.Optional(
                        CONF_IGNORED_LABELS,
                        default=options.get(
                            CONF_IGNORED_LABELS, DEFAULT_IGNORED_LABELS
                        ),
                    ): LabelSelector(LabelSelectorConfig(multiple=True)),
                }
            ),
        )
