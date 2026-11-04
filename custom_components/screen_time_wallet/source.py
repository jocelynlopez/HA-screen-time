"""Source branchable des moyennes par matière et des notes visibles."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from .engine.grades import Grade


@dataclass(frozen=True)
class SourceData:
    averages: Mapping[str, object]  # matière (nom EcoleDirecte) → moyenne sur 20
    notes: Sequence[Grade]


class GradesSource(Protocol):
    """Fournit les données d'un bilan. Peut lever une exception si la source est indisponible."""

    async def async_fetch(self) -> SourceData: ...


class NullSource:
    """Aucune source : le bilan utilise le crédit de repli et un crédit de semaine nul."""

    async def async_fetch(self) -> SourceData:
        return SourceData({}, [])
