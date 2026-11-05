"""Flux de configuration (un portefeuille par enfant) et flux d'options."""

import re

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    OPT_EXCLUDE_NS,
    OPT_FALLBACK,
    OPT_MAX_HOURS,
    OPT_MIN_SUBJECTS,
    OPT_MIN_WEIGHT,
    OPT_MULTIPLIERS,
    OPT_NOTES_ENTITY,
    OPT_NOTES_SHARE,
    OPT_NOTIFY_SERVICE,
    OPT_PIVOT,
    OPT_USAGE_ENTITIES,
    OPT_WEEKLY_REPORT,
)
from .engine.config import ConfigError, normalize_subject
from .options import build_config, with_defaults
from .report import render_subjects_table
from .runtime import NoSourceError

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
            # un champ d'entité vidé est absent des données reçues : on le lit comme « aucun capteur »
            notes_entity = user_input.get(OPT_NOTES_ENTITY) or ""
            candidate[OPT_NOTES_ENTITY] = notes_entity
            # idem pour les capteurs de temps d'écran : aucun capteur
            usage_entities = list(dict.fromkeys(user_input.get(OPT_USAGE_ENTITIES) or []))
            candidate[OPT_USAGE_ENTITIES] = usage_entities
            if service and not NOTIFY_SERVICE.match(service):
                errors[OPT_NOTIFY_SERVICE] = "invalid_notify_service"
            elif notes_entity and not self._entity_exists(notes_entity):
                errors[OPT_NOTES_ENTITY] = "unknown_entity"
            elif not all(self._entity_exists(entity) for entity in usage_entities):
                errors[OPT_USAGE_ENTITIES] = "unknown_entity"
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
                vol.Optional(
                    OPT_NOTES_ENTITY, description={"suggested_value": current[OPT_NOTES_ENTITY] or None}
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor", integration="ecole_directe")
                ),
                vol.Optional(
                    OPT_USAGE_ENTITIES, description={"suggested_value": current[OPT_USAGE_ENTITIES] or None}
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", multiple=True)),
            }
        )
        return self.async_show_form(step_id="parametres", data_schema=schema, errors=errors)

    def _entity_exists(self, entity_id: str) -> bool:
        return self.hass.states.get(entity_id) is not None or er.async_get(self.hass).async_get(entity_id) is not None

    async def async_step_matieres(self, user_input: dict | None = None) -> ConfigFlowResult:
        current = with_defaults(self.config_entry.options)
        errors = {}
        if user_input is not None and user_input.get("detect"):
            result = await self._async_detect_subjects(errors)
            if result is not None:
                return result
        elif user_input is not None:
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
                vol.Optional("subject", default=""): str,  # facultatif quand « détecter » est coché
                vol.Required("multiplier", default=1): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Required("remove", default=False): bool,
                vol.Required("detect", default=False): bool,
            }
        )
        return self.async_show_form(
            step_id="matieres", data_schema=schema, errors=errors,
            description_placeholders={"table": self._subjects_table()},
        )

    def _subjects_table(self) -> str:
        """Table courante des matières, en texte, pour les écrans et les messages de fin."""
        table = with_defaults(self.config_entry.options)[OPT_MULTIPLIERS]
        return render_subjects_table(table, self.hass.config.language)

    async def _async_detect_subjects(self, errors: dict) -> ConfigFlowResult | None:
        """Détection à la demande : le résultat est affiché par une fenêtre de fin ; None si elle a échoué (erreur)."""
        runtime = getattr(self.config_entry, "runtime_data", None)
        if runtime is None:
            errors["base"] = "source_unavailable"
            return None
        try:
            added = await runtime.async_detect_subjects()
        except NoSourceError:
            errors["base"] = "no_source"
            return None
        except Exception:  # noqa: BLE001 - la source est un point d'extension
            errors["base"] = "source_unavailable"
            return None
        if added:
            return self.async_abort(
                reason="subjects_added",
                description_placeholders={"subjects": ", ".join(added), "table": self._subjects_table()},
            )
        return self.async_abort(reason="no_new_subjects", description_placeholders={"table": self._subjects_table()})
