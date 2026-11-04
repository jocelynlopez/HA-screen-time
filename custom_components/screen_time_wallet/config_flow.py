"""Flux de configuration (un portefeuille par enfant) et flux d'options."""

import re

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_NAME

from .const import (
    DOMAIN,
    OPT_EXCLUDE_NS,
    OPT_FALLBACK,
    OPT_MAX_HOURS,
    OPT_MIN_SUBJECTS,
    OPT_MIN_WEIGHT,
    OPT_MULTIPLIERS,
    OPT_NOTES_SHARE,
    OPT_NOTIFY_SERVICE,
    OPT_PIVOT,
    OPT_WEEKLY_REPORT,
)
from .engine.config import ConfigError, normalize_subject
from .options import build_config, with_defaults

NOTIFY_SERVICE = re.compile(r"^notify\.[a-z0-9_]+$")


class ScreenTimeWalletConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> "ScreenTimeWalletOptionsFlow":
        return ScreenTimeWalletOptionsFlow()

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            if not name:
                errors[CONF_NAME] = "name_required"
            else:
                await self.async_set_unique_id(name.casefold())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=name, data={CONF_NAME: name})
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required(CONF_NAME): str}), errors=errors
        )


class ScreenTimeWalletOptionsFlow(OptionsFlow):
    """Options d'un portefeuille : paramètres de calcul, puis table des matières."""

    async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        return self.async_show_menu(step_id="init", menu_options=["parametres", "matieres"])

    async def async_step_parametres(self, user_input: dict | None = None) -> ConfigFlowResult:
        current = with_defaults(self.config_entry.options)
        errors = {}
        if user_input is not None:
            candidate = {**current, **user_input}
            service = candidate.get(OPT_NOTIFY_SERVICE, "").strip()
            candidate[OPT_NOTIFY_SERVICE] = service
            if service and not NOTIFY_SERVICE.match(service):
                errors[OPT_NOTIFY_SERVICE] = "invalid_notify_service"
            else:
                try:
                    build_config(candidate)
                except ConfigError:
                    errors["base"] = "invalid_config"
            if not errors:
                return self.async_create_entry(data=candidate)
            current = candidate
        schema = vol.Schema(
            {
                vol.Required(OPT_MAX_HOURS, default=current[OPT_MAX_HOURS]): vol.All(
                    vol.Coerce(float), vol.Range(min=0.5, max=168)
                ),
                vol.Required(OPT_NOTES_SHARE, default=current[OPT_NOTES_SHARE]): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=100)
                ),
                vol.Required(OPT_PIVOT, default=current[OPT_PIVOT]): vol.Coerce(float),
                vol.Required(OPT_MIN_WEIGHT, default=current[OPT_MIN_WEIGHT]): vol.All(
                    vol.Coerce(float), vol.Range(min=0)
                ),
                vol.Required(OPT_MIN_SUBJECTS, default=current[OPT_MIN_SUBJECTS]): vol.All(
                    vol.Coerce(int), vol.Range(min=1)
                ),
                vol.Required(OPT_FALLBACK, default=current[OPT_FALLBACK]): vol.All(
                    vol.Coerce(int), vol.Range(min=0)
                ),
                vol.Required(OPT_EXCLUDE_NS, default=current[OPT_EXCLUDE_NS]): bool,
                vol.Required(OPT_WEEKLY_REPORT, default=current[OPT_WEEKLY_REPORT]): bool,
                vol.Optional(OPT_NOTIFY_SERVICE, default=current[OPT_NOTIFY_SERVICE]): str,
            }
        )
        return self.async_show_form(step_id="parametres", data_schema=schema, errors=errors)

    async def async_step_matieres(self, user_input: dict | None = None) -> ConfigFlowResult:
        current = with_defaults(self.config_entry.options)
        errors = {}
        if user_input is not None:
            table = dict(current[OPT_MULTIPLIERS])
            subject = user_input["subject"].strip()
            existing = next((k for k in table if normalize_subject(k) == normalize_subject(subject)), None)
            if not subject:
                errors["subject"] = "subject_required"
            elif user_input.get("remove"):
                if existing is None:
                    errors["subject"] = "unknown_subject"
                else:
                    del table[existing]
            else:
                table[existing or subject] = user_input["multiplier"]
            candidate = {**current, OPT_MULTIPLIERS: table}
            if not errors:
                try:
                    build_config(candidate)
                except ConfigError:
                    errors["base"] = "empty_table"
            if not errors:
                return self.async_create_entry(data=candidate)
        schema = vol.Schema(
            {
                vol.Required("subject"): str,
                vol.Required("multiplier", default=1): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Required("remove", default=False): bool,
            }
        )
        return self.async_show_form(step_id="matieres", data_schema=schema, errors=errors)
