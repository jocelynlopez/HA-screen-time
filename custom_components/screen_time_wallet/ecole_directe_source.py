"""Source de données : capteurs de l'intégration Home Assistant `ecole_directe` (hacf-fr/hass-ecoledirecte).

Aucun appel réseau : on lit les entités déjà publiées par cette intégration.
"""

import logging
from collections.abc import Iterable, Mapping
from fractions import Fraction

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .engine.config import to_fraction
from .engine.grades import Grade
from .source import SourceData, SourceUnavailableError

_LOGGER = logging.getLogger(__name__)

ATTR_NOTES = "notes"
ATTR_SUBJECT_NAME = "Nom"
ATTR_SUBJECT_CODE = "Code"


def parse_notes(raw: Iterable[Mapping]) -> list[Grade]:
    """Traduit l'attribut `notes` en notes du portefeuille ; ignore les entrées sans date ou sans matière."""
    grades = []
    for entry in raw:
        if not isinstance(entry, Mapping) or not entry.get("date") or not entry.get("matiere"):
            continue
        grades.append(
            Grade(
                date=entry["date"],
                subject=entry["matiere"],
                comment=entry.get("commentaire") or "",
                value=entry.get("note"),
                scale=entry.get("sur"),
                coefficient=entry.get("coefficient"),
                non_significant=bool(entry.get("non_significatif")),
            )
        )
    return grades


def parse_average(state: str | None) -> Fraction | None:
    """Moyenne lue dans l'état d'un capteur de matière ; None si inconnu, indisponible, vide ou non numérique."""
    if state in (None, STATE_UNKNOWN, STATE_UNAVAILABLE):
        return None
    return to_fraction(state)


class EcoleDirecteSource:
    """Lit le capteur de notes d'un enfant et les capteurs de moyenne de la même entrée EcoleDirecte."""

    def __init__(self, hass: HomeAssistant, notes_entity_id: str) -> None:
        self.hass = hass
        self.notes_entity_id = notes_entity_id

    async def async_fetch(self) -> SourceData:
        state = self.hass.states.get(self.notes_entity_id)
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            raise SourceUnavailableError(f"capteur de notes indisponible : {self.notes_entity_id}")
        raw = state.attributes.get(ATTR_NOTES)
        if not isinstance(raw, list):
            raise SourceUnavailableError(f"{self.notes_entity_id} n'a pas d'attribut « {ATTR_NOTES} »")
        return SourceData(self._discover_averages(), parse_notes(raw))

    def _discover_averages(self) -> dict[str, Fraction]:
        """Moyennes des capteurs de matière (attributs Nom et Code) de la même entrée EcoleDirecte."""
        registry = er.async_get(self.hass)
        notes_entry = registry.async_get(self.notes_entity_id)
        if notes_entry is None or notes_entry.config_entry_id is None:
            _LOGGER.warning("%s n'est pas rattaché à une entrée de configuration : aucune moyenne", self.notes_entity_id)
            return {}
        averages = {}
        for entry in er.async_entries_for_config_entry(registry, notes_entry.config_entry_id):
            if entry.domain != "sensor" or entry.entity_id == self.notes_entity_id:
                continue
            state = self.hass.states.get(entry.entity_id)
            if state is None or ATTR_SUBJECT_NAME not in state.attributes or ATTR_SUBJECT_CODE not in state.attributes:
                continue
            average = parse_average(state.state)
            if average is not None:
                averages[state.attributes[ATTR_SUBJECT_NAME]] = average
        return averages
