"""Source branchable des moyennes par matière et des notes visibles."""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from .engine.config import normalize_subject
from .engine.grades import Grade


def distinct_subjects(names: Iterable[object]) -> list[str]:
    """Noms sans doublon à la normalisation (casse, accents, ponctuation) ; le premier nom rencontré est gardé."""
    found = {}
    for name in names:
        if isinstance(name, str) and (key := normalize_subject(name)):
            found.setdefault(key, name)
    return list(found.values())


@dataclass(frozen=True)
class SourceData:
    averages: Mapping[str, object]  # matière (nom EcoleDirecte) → moyenne sur 20
    notes: Sequence[Grade]
    subjects: Sequence[str] = ()  # matières publiées par la source, avec ou sans moyenne ni note

    @property
    def all_subjects(self) -> list[str]:
        """Toutes les matières des données : celles publiées, celles des moyennes et celles des notes."""
        return distinct_subjects([*self.subjects, *self.averages, *(g.subject for g in self.notes)])


class SourceUnavailableError(Exception):
    """La source ne peut pas fournir de données pour l'instant (capteur absent, indisponible…)."""


class GradesSource(Protocol):
    """Fournit les données d'un bilan. Peut lever une exception si la source est indisponible."""

    async def async_fetch(self) -> SourceData: ...


class NullSource:
    """Aucune source : le bilan utilise le crédit de repli et un crédit de semaine nul."""

    async def async_fetch(self) -> SourceData:
        return SourceData({}, [])
