"""Config flow for zaparoo."""

import voluptuous as vol
from homeassistant import config_entries

from .const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
    }
)


class ZaparooConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zaparoo."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial UI step."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA)

        host = user_input[CONF_HOST].strip()
        port = int(user_input.get(CONF_PORT, DEFAULT_PORT))

        # No duplicates
        for entry in self._async_current_entries():
            if entry.data.get(CONF_HOST) == host and entry.data.get(CONF_PORT) == port:
                return self.async_abort(reason="already_configured")

        title = f"{host}:{port}"

        return self.async_create_entry(
            title=title, data={CONF_HOST: host, CONF_PORT: port}
        )
