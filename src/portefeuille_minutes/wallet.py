"""Portefeuille de minutes de temps d'écran (spec screen-time-wallet)."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta

from .config import Config
from .credit import initial_credit, week_credit
from .grades import Grade, InvalidGradeError


class InvalidConsumptionError(ValueError):
    """Consommation inférieure ou égale à 0."""


def monday_midnight(moment: datetime) -> datetime:
    """Lundi 00h00 de la semaine contenant `moment` (heure locale naïve)."""
    return datetime.combine(moment.date() - timedelta(days=moment.weekday()), time.min)


@dataclass
class Report:
    """Compte rendu du bilan d'un lundi."""

    monday: datetime
    initial_credit: int
    week_credit: int
    counted: list[Grade] = field(default_factory=list)
    rejected: list[tuple[Grade, str]] = field(default_factory=list)
    unknown_subjects: list[str] = field(default_factory=list)


@dataclass
class Wallet:
    weekly_credit: int  # remis à sa valeur chaque lundi, non cumulable
    notes_capital: int  # cumulé d'une semaine à l'autre, peut être négatif
    last_settlement: datetime  # dernier lundi 00h00 traité
    config: Config = field(default_factory=Config)
    seen_keys: set = field(default_factory=set)

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

    def settle(
        self, now: datetime, averages: Mapping[str, object], notes: Iterable[Grade]
    ) -> list[Report]:
        """Bilan de chaque lundi 00h00 écoulé depuis le dernier ; [] s'il n'y en a aucun."""
        weeks = (monday_midnight(now) - self.last_settlement).days // 7
        if weeks <= 0:
            return []
        pending = self._classify(notes)
        reports = []
        for step in range(1, weeks + 1):
            monday = self.last_settlement + timedelta(weeks=step)
            week_notes = pending.counted if step == 1 else []
            report = Report(
                monday=monday,
                initial_credit=initial_credit(averages, self.config),
                week_credit=week_credit(week_notes, averages, self.config),
                counted=list(week_notes),
                rejected=list(pending.rejected) if step == 1 else [],
                unknown_subjects=list(pending.unknown_subjects) if step == 1 else [],
            )
            self.weekly_credit = report.initial_credit
            self.notes_capital += report.week_credit
            reports.append(report)
        self.last_settlement += timedelta(weeks=weeks)
        self.seen_keys |= pending.seen
        return reports

    def consume(self, minutes: int) -> None:
        """Débite d'abord le crédit hebdomadaire, puis le capital notes (qui peut devenir négatif)."""
        if minutes <= 0:
            raise InvalidConsumptionError(f"consommation invalide : {minutes}")
        from_weekly = min(minutes, self.weekly_credit)
        self.weekly_credit -= from_weekly
        self.notes_capital -= minutes - from_weekly

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
