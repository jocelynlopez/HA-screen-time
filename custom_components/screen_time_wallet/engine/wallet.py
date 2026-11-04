"""Portefeuille de minutes de temps d'écran (spec screen-time-wallet)."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from fractions import Fraction

from .config import Config
from .credit import WeekDetails, initial_credit, week_details
from .grades import Grade, InvalidGradeError, key_from_json, key_to_json

STATE_VERSION = 1
MAX_MOVEMENTS = 200


class InvalidConsumptionError(ValueError):
    """Consommation inférieure ou égale à 0."""


class InvalidAdjustmentError(ValueError):
    """Ajustement nul ou non entier."""


class WalletStateError(ValueError):
    """État sérialisé illisible ou de version inconnue."""


def monday_midnight(moment: datetime) -> datetime:
    """Lundi 00h00 de la semaine contenant `moment` (heure locale naïve)."""
    return datetime.combine(moment.date() - timedelta(days=moment.weekday()), time.min)


@dataclass
class Movement:
    """Une ligne du journal : bilan, consommation ou ajustement."""

    kind: str  # "bilan", "consommation" ou "ajustement"
    when: datetime | None
    weekly_change: int
    capital_change: int
    reason: str = ""
    detail: dict = field(default_factory=dict, compare=False)  # ex. crédit initial d'un bilan

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "when": self.when.isoformat() if self.when else None,
            "weekly_change": self.weekly_change,
            "capital_change": self.capital_change,
            "reason": self.reason,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Movement":
        when = data.get("when")
        return cls(
            data["kind"], datetime.fromisoformat(when) if when else None,
            int(data["weekly_change"]), int(data["capital_change"]), data.get("reason", ""),
            dict(data.get("detail", {})),
        )


@dataclass
class Report:
    """Compte rendu du bilan d'un lundi, avec les éléments du calcul."""

    monday: datetime
    initial_credit: int
    week_credit: int
    counted: list[Grade] = field(default_factory=list)
    rejected: list[tuple[Grade, str]] = field(default_factory=list)
    unknown_subjects: list[str] = field(default_factory=list)
    subjects_count: int = 0
    general_average: Fraction | None = None
    week_weight: Fraction = Fraction(0)
    week_average: Fraction | None = None
    fallback: bool = False
    notes_capital: int = 0  # après le bilan
    available: int = 0  # après le bilan


@dataclass
class Wallet:
    weekly_credit: int  # remis à sa valeur chaque lundi, non cumulable
    notes_capital: int  # cumulé d'une semaine à l'autre, peut être négatif
    last_settlement: datetime  # dernier lundi 00h00 traité
    config: Config = field(default_factory=Config)
    seen_keys: set = field(default_factory=set)
    movements: list[Movement] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        now: datetime,
        averages: Mapping[str, object],
        visible_notes: Iterable[Grade] = (),
        config: Config | None = None,
    ) -> "Wallet":
        """Portefeuille neuf : crédit initial de la semaine en cours, historique mémorisé sans effet."""
        config = config or Config()
        return cls(
            weekly_credit=initial_credit(averages, config),
            notes_capital=0,
            last_settlement=monday_midnight(now),
            config=config,
            seen_keys={g.key for g in visible_notes},
        )

    @property
    def available(self) -> int:
        return self.weekly_credit + self.notes_capital

    def pending_settlements(self, now: datetime) -> int:
        """Nombre de lundis 00h00 écoulés depuis le dernier bilan."""
        return max(0, (monday_midnight(now) - self.last_settlement).days // 7)

    def settle(
        self, now: datetime, averages: Mapping[str, object], notes: Iterable[Grade]
    ) -> list[Report]:
        """Bilan de chaque lundi 00h00 écoulé depuis le dernier ; [] s'il n'y en a aucun."""
        weeks = self.pending_settlements(now)
        if weeks <= 0:
            return []
        pending = self._classify(notes)
        reports = []
        for step in range(1, weeks + 1):
            monday = self.last_settlement + timedelta(weeks=step)
            week_notes = pending.counted if step == 1 else []
            details = week_details(week_notes, averages, self.config)
            initial = initial_credit(averages, self.config)
            weekly_change = initial - self.weekly_credit
            self.weekly_credit = initial
            self.notes_capital += details.credit
            self._record(Movement("bilan", monday, weekly_change, details.credit, "",
                                  {"initial_credit": initial, "week_credit": details.credit}))
            reports.append(self._report(monday, initial, details, week_notes, pending, step == 1))
        self.last_settlement += timedelta(weeks=weeks)
        self.seen_keys |= pending.seen
        return reports

    def consume(self, minutes: int, now: datetime | None = None, reason: str = "") -> None:
        """Débite d'abord le crédit hebdomadaire, puis le capital notes (qui peut devenir négatif)."""
        if minutes <= 0:
            raise InvalidConsumptionError(f"consommation invalide : {minutes}")
        from_weekly = min(minutes, self.weekly_credit)
        self.weekly_credit -= from_weekly
        self.notes_capital -= minutes - from_weekly
        self._record(Movement("consommation", now, -from_weekly, -(minutes - from_weekly), reason))

    def adjust(self, minutes: int, now: datetime | None = None, reason: str = "") -> None:
        """Ajoute au capital notes un nombre de minutes non nul, positif ou négatif."""
        if isinstance(minutes, bool) or not isinstance(minutes, int) or minutes == 0:
            raise InvalidAdjustmentError(f"ajustement invalide : {minutes!r}")
        self.notes_capital += minutes
        self._record(Movement("ajustement", now, 0, minutes, reason))

    def activate_source(self, now: datetime, averages: Mapping[str, object], notes: Iterable[Grade]) -> None:
        """Active une source : notes visibles mémorisées sans effet, crédit hebdomadaire = crédit initial."""
        initial = initial_credit(averages, self.config)
        change = initial - self.weekly_credit
        self.weekly_credit = initial
        self.seen_keys |= {g.key for g in notes}
        self._record(Movement("initialisation", now, change, 0, "", {"initial_credit": initial}))

    def to_dict(self) -> dict:
        """État compatible JSON (la configuration n'en fait pas partie : ce sont les options)."""
        return {
            "version": STATE_VERSION,
            "weekly_credit": self.weekly_credit,
            "notes_capital": self.notes_capital,
            "last_settlement": self.last_settlement.isoformat(),
            "seen_keys": sorted(key_to_json(k) for k in self.seen_keys),
            "movements": [m.to_dict() for m in self.movements],
        }

    @classmethod
    def from_dict(cls, data: dict, config: Config | None = None) -> "Wallet":
        if not isinstance(data, dict) or data.get("version") != STATE_VERSION:
            raise WalletStateError(f"version d'état inconnue : {data.get('version') if isinstance(data, dict) else data!r}")
        try:
            return cls(
                weekly_credit=int(data["weekly_credit"]),
                notes_capital=int(data["notes_capital"]),
                last_settlement=datetime.fromisoformat(data["last_settlement"]),
                config=config or Config(),
                seen_keys={key_from_json(k) for k in data["seen_keys"]},
                movements=[Movement.from_dict(m) for m in data["movements"]],
            )
        except (KeyError, TypeError, ValueError) as error:
            raise WalletStateError(f"état illisible : {error}") from error

    def _record(self, movement: Movement) -> None:
        self.movements.append(movement)
        del self.movements[:-MAX_MOVEMENTS]

    def _report(self, monday, initial, details: WeekDetails, week_notes, pending, first) -> Report:
        return Report(
            monday=monday,
            initial_credit=initial,
            week_credit=details.credit,
            counted=list(week_notes),
            rejected=list(pending.rejected) if first else [],
            unknown_subjects=list(pending.unknown_subjects) if first else [],
            subjects_count=details.subjects_count,
            general_average=details.general_average,
            week_weight=details.weight,
            week_average=details.week_average,
            fallback=details.fallback,
            notes_capital=self.notes_capital,
            available=self.available,
        )

    def _classify(self, notes: Iterable[Grade]) -> "_Pending":
        pending = _Pending()
        batch = set()
        for grade in notes:
            if grade.key in self.seen_keys or grade.key in batch:
                continue
            if not grade.is_graded():
                continue  # absent, dispensé… : ni compté ni marqué comme vu
            try:
                grade.validate()
            except InvalidGradeError as error:
                pending.rejected.append((grade, str(error)))
                continue
            batch.add(grade.key)
            pending.seen.add(grade.key)
            if not self.config.is_known(grade.subject):
                if grade.subject not in pending.unknown_subjects:
                    pending.unknown_subjects.append(grade.subject)
                continue
            pending.counted.append(grade)
        return pending


@dataclass
class _Pending:
    counted: list[Grade] = field(default_factory=list)
    rejected: list[tuple[Grade, str]] = field(default_factory=list)
    unknown_subjects: list[str] = field(default_factory=list)
    seen: set = field(default_factory=set)
