"""Paramètres modifiables du portefeuille (voir specs grade-conversion et screen-time-wallet)."""

import unicodedata
from dataclasses import dataclass, field
from fractions import Fraction


def normalize_subject(name: str) -> str:
    """Nom de matière sans accents, casse ni espaces superflus."""
    decomposed = unicodedata.normalize("NFD", name)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return " ".join(stripped.casefold().split())


DEFAULT_MULTIPLIERS = {
    "maths": Fraction(3),
    "français": Fraction(4),
    "histoire": Fraction(2),
    "anglais": Fraction(3),
    "eist": Fraction(3),
    "musique": Fraction(1, 2),
    "arts plastiques": Fraction(1, 2),
    "art plastique": Fraction(1, 2),
    "sport": Fraction(1, 2),
}


@dataclass(frozen=True)
class Config:
    base_rate: Fraction = Fraction(15)  # minutes par point d'écart
    pivot: Fraction = Fraction(12)  # note pivot, sur 20
    weekly_allocation: int = 240  # minutes créditées chaque lundi 00h00
    subject_multipliers: dict[str, Fraction] = field(
        default_factory=lambda: dict(DEFAULT_MULTIPLIERS)
    )

    def multiplier_for(self, subject: str) -> Fraction:
        """Multiplicateur de la matière ; 0 si elle n'est pas classée."""
        table = {normalize_subject(k): Fraction(v) for k, v in self.subject_multipliers.items()}
        return table.get(normalize_subject(subject), Fraction(0))
