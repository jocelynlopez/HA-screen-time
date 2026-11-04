"""Notes scolaires : normalisation sur 20, poids, validité et clé d'identification (spec grade-conversion)."""

from dataclasses import dataclass
from fractions import Fraction

from .config import Config, normalize_subject, to_fraction


class InvalidGradeError(ValueError):
    """Note numérique incohérente (barème, valeur ou coefficient invalide)."""


@dataclass(frozen=True)
class Grade:
    date: object  # date ou texte AAAA-MM-JJ
    subject: str
    comment: str
    value: object  # nombre ou texte (« 7 », « 4,5 », « Abs »…)
    scale: object = 20
    coefficient: object = 1
    non_significant: bool = False

    def is_graded(self) -> bool:
        """Vrai si la valeur est numérique (faux pour absent, dispensé, non noté, vide)."""
        return to_fraction(self.value) is not None

    @property
    def key(self) -> tuple:
        """Identité d'une note, sans sa valeur : EcoleDirecte n'expose pas d'identifiant."""
        scale, coefficient = to_fraction(self.scale), to_fraction(self.coefficient)
        return (
            str(self.date),
            normalize_subject(self.subject),
            self.comment.strip(),
            scale if scale is not None else str(self.scale),
            coefficient if coefficient is not None else str(self.coefficient),
        )

    def validate(self) -> None:
        """Lève InvalidGradeError si la note numérique est incohérente."""
        value, scale = to_fraction(self.value), to_fraction(self.scale)
        coefficient = to_fraction(self.coefficient)
        if value is None:
            raise InvalidGradeError(f"{self.subject} : valeur non numérique")
        if scale is None or scale <= 0:
            raise InvalidGradeError(f"{self.subject} : barème invalide ({self.scale!r})")
        if not 0 <= value <= scale:
            raise InvalidGradeError(f"{self.subject} : valeur {value} hors du barème {scale}")
        if coefficient is None or coefficient < 0:
            raise InvalidGradeError(f"{self.subject} : coefficient invalide ({self.coefficient!r})")

    def on_20(self) -> Fraction:
        """Valeur ramenée sur 20 (valide la note)."""
        self.validate()
        return to_fraction(self.value) * 20 / to_fraction(self.scale)

    def weight(self, config: Config) -> Fraction:
        """Poids : multiplicateur de la matière × coefficient."""
        self.validate()
        return config.multiplier_for(self.subject) * to_fraction(self.coefficient)


def key_to_json(key: tuple) -> list[str]:
    """Clé de note sous forme JSON : les fractions sont notées « F n/d », le reste « S texte »."""
    return [value if i < 3 else _encode_part(value) for i, value in enumerate(key)]


def key_from_json(parts: list[str]) -> tuple:
    return tuple(part if i < 3 else _decode_part(part) for i, part in enumerate(parts))


def _encode_part(value) -> str:
    if isinstance(value, Fraction):
        return f"F {value.numerator}/{value.denominator}"
    return f"S {value}"


def _decode_part(text: str):
    kind, _, body = text.partition(" ")
    if kind == "F":
        numerator, _, denominator = body.partition("/")
        return Fraction(int(numerator), int(denominator))
    return body
