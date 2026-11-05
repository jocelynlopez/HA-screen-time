"""Mise en forme (fonctions pures) du rapport hebdomadaire et de la notification d'anomalie."""

from collections.abc import Mapping
from fractions import Fraction

from .engine.config import Config, normalize_subject, to_fraction
from .engine.wallet import Report

TEXTS = {
    "fr": {
        "report_title": "Bilan du portefeuille de {name}",
        "week_title": "Lundi {date}",
        "initial": "Crédit initial : {minutes} min (moyenne générale {average} sur {count} matières)",
        "initial_fallback": "Crédit initial : {minutes} min (crédit de repli : {count} matière(s) avec moyenne, {needed} requises)",
        "notes_header": "Notes de la semaine (poids total {weight}) :",
        "note_line": "• {subject} : {value}/20 (poids {weight})",
        "no_notes": "Aucune note cette semaine : la moyenne générale sert de moyenne de la semaine.",
        "week_average": "Moyenne de la semaine : {average}",
        "week_credit": "Crédit de semaine : {minutes} min",
        "week_credit_fallback": "Crédit de semaine : 0 min (crédit de repli)",
        "totals": "Capital notes : {capital} min · Temps disponible : {available} min",
        "manual_header": "Mouvements manuels de la semaine :",
        "manual_line": "• {date} · {minutes} min · {reason}",
        "manual_more": "… et {count} autre(s)",
        "no_reason": "sans motif",
        "automatic_header": "Consommation automatique :",
        "automatic_line": "• {reason} : {minutes} min",
        "anomaly_title": "Portefeuille de {name} : à vérifier",
        "blocking_title": "Portefeuille de {name} : blocage impossible",
        "blocking_failed": "Le basculement de {entity} a échoué : {error}. Il sera réessayé au prochain relevé. Vérifiez l'intégration concernée, ou videz les interrupteurs de blocage dans les options pour reprendre la main.",
        "table_header": "Table des matières :",
        "subjects_title": "Portefeuille de {name} : matières ajoutées",
        "subjects_added": "Matières ajoutées automatiquement avec le multiplicateur 1 : {subjects}. Réglez leur multiplicateur dans les options de l'intégration, étape « Matières » (0 pour les exclure du calcul).",
        "rejected_note": "Note rejetée : {subject} {value}/{scale} du {date} ({reason})",
        "source_title": "Portefeuille de {name} : source indisponible",
        "source_message": "Le bilan du lundi n'a pas pu être effectué : {error}. Il sera retenté automatiquement. Vérifiez l'intégration EcoleDirecte et le capteur {entity}.",
    },
    "en": {
        "report_title": "{name}'s wallet report",
        "week_title": "Monday {date}",
        "initial": "Initial credit: {minutes} min (overall average {average} over {count} subjects)",
        "initial_fallback": "Initial credit: {minutes} min (fallback credit: {count} subject(s) with an average, {needed} required)",
        "notes_header": "This week's grades (total weight {weight}):",
        "note_line": "• {subject}: {value}/20 (weight {weight})",
        "no_notes": "No grade this week: the overall average is used as the week average.",
        "week_average": "Week average: {average}",
        "week_credit": "Week credit: {minutes} min",
        "week_credit_fallback": "Week credit: 0 min (fallback credit)",
        "totals": "Notes capital: {capital} min · Available time: {available} min",
        "manual_header": "Manual movements this week:",
        "manual_line": "• {date} · {minutes} min · {reason}",
        "manual_more": "… and {count} more",
        "no_reason": "no reason",
        "automatic_header": "Automatic consumption:",
        "automatic_line": "• {reason}: {minutes} min",
        "anomaly_title": "{name}'s wallet: needs attention",
        "blocking_title": "{name}'s wallet: blocking failed",
        "blocking_failed": "Switching {entity} failed: {error}. It will be retried at the next reading. Check the related integration, or clear the blocking switches in the options to take control back.",
        "table_header": "Subjects table:",
        "subjects_title": "{name}'s wallet: subjects added",
        "subjects_added": "Subjects added automatically with multiplier 1: {subjects}. Set their multiplier in the integration options, \"Subjects\" step (0 to exclude them from the calculation).",
        "rejected_note": "Rejected grade: {subject} {value}/{scale} of {date} ({reason})",
        "source_title": "{name}'s wallet: source unavailable",
        "source_message": "The Monday settlement could not be done: {error}. It will be retried automatically. Check the EcoleDirecte integration and the sensor {entity}.",
    },
}


def _language(language: str) -> str:
    return "fr" if language.lower().startswith("fr") else "en"


def _number(value: Fraction, language: str, decimals: int = 2, trim: bool = False) -> str:
    text = f"{float(value):.{decimals}f}"
    if trim and "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.replace(".", ",") if language == "fr" else text


def _date(moment, language: str) -> str:
    return moment.strftime("%d/%m/%Y") if language == "fr" else moment.strftime("%Y-%m-%d")


def _date_time(moment, language: str) -> str:
    return moment.strftime("%d/%m %H:%M") if language == "fr" else moment.strftime("%m-%d %H:%M")


MAX_MANUAL_LINES = 30


def render_report(reports: list[Report], name: str, config: Config, language: str) -> tuple[str, str]:
    """Titre et message du rapport hebdomadaire ; une section par lundi traité."""
    lang = _language(language)
    t = TEXTS[lang]
    sections = []
    for report in reports:
        lines = [t["week_title"].format(date=_date(report.monday, lang))]
        if report.fallback:
            lines.append(t["initial_fallback"].format(
                minutes=report.initial_credit, count=report.subjects_count, needed=config.min_subjects))
        else:
            lines.append(t["initial"].format(
                minutes=report.initial_credit, average=_number(report.general_average, lang),
                count=report.subjects_count))
        if report.counted:
            lines.append(t["notes_header"].format(weight=_number(report.week_weight, lang, trim=True)))
            for grade in report.counted:
                lines.append(t["note_line"].format(
                    subject=grade.subject, value=_number(grade.on_20(), lang, trim=True),
                    weight=_number(grade.weight(config), lang, trim=True)))
        elif not report.fallback:
            lines.append(t["no_notes"])
        if report.fallback:
            lines.append(t["week_credit_fallback"])
        else:
            lines.append(t["week_average"].format(average=_number(report.week_average, lang)))
            lines.append(t["week_credit"].format(minutes=f"{report.week_credit:+d}"))
        lines.append(t["totals"].format(capital=f"{report.notes_capital:+d}", available=report.available))
        lines.extend(_movement_lines(report, t, lang))
        sections.append("\n".join(lines))
    return t["report_title"].format(name=name), "\n\n".join(sections)


def _movement_lines(report: Report, t: dict, lang: str) -> list[str]:
    """Mouvements manuels de la semaine (30 lignes au plus) puis consommation automatique ; vide s'il n'y en a pas."""
    lines = []
    if report.manual:
        lines.append(t["manual_header"])
        for movement in report.manual[:MAX_MANUAL_LINES]:
            lines.append(t["manual_line"].format(
                date=_date_time(movement.when, lang), minutes=f"{movement.weekly_change + movement.capital_change:+d}",
                reason=movement.reason or t["no_reason"]))
        if len(report.manual) > MAX_MANUAL_LINES:
            lines.append(t["manual_more"].format(count=len(report.manual) - MAX_MANUAL_LINES))
    if report.automatic:
        lines.append(t["automatic_header"])
        lines.extend(t["automatic_line"].format(reason=reason, minutes=minutes)
                     for reason, minutes in report.automatic.items())
    return lines


def render_source_down(name: str, entity: str, error: str, language: str) -> tuple[str, str]:
    """Titre et message de la notification de source indisponible."""
    t = TEXTS[_language(language)]
    return t["source_title"].format(name=name), t["source_message"].format(error=error, entity=entity)


def render_anomalies(reports: list[Report], name: str, language: str) -> tuple[str, str] | None:
    """Titre et message des notes rejetées ; None s'il n'y a rien à signaler."""
    lang = _language(language)
    t = TEXTS[lang]
    rejected = [item for r in reports for item in r.rejected]
    if not rejected:
        return None
    lines = []
    for grade, reason in rejected:
        lines.append(t["rejected_note"].format(
            subject=grade.subject, value=grade.value, scale=grade.scale, date=grade.date, reason=reason))
    return t["anomaly_title"].format(name=name), "\n".join(lines)


def render_subjects_table(table: Mapping[str, object], language: str) -> str:
    """Table des matières en liste Markdown : une ligne par matière avec son multiplicateur, triée sans casse ni accents."""
    lang = _language(language)
    lines = []
    for subject in sorted(table, key=normalize_subject):
        multiplier = to_fraction(table[subject])
        lines.append(f"- {subject} : {_number(multiplier, lang, trim=True) if multiplier is not None else table[subject]}")
    return "\n".join(lines)


def render_subjects_added(name: str, subjects: list[str], table: Mapping[str, object], language: str) -> tuple[str, str]:
    """Titre et message de la notification des matières ajoutées automatiquement, avec la table courante."""
    t = TEXTS[_language(language)]
    message = t["subjects_added"].format(subjects=", ".join(subjects))
    return t["subjects_title"].format(name=name), f"{message}\n\n{t['table_header']}\n{render_subjects_table(table, language)}"


def render_blocking_failed(name: str, entity: str, error: str, language: str) -> tuple[str, str]:
    """Titre et message de la notification d'un basculement d'interrupteur en échec."""
    t = TEXTS[_language(language)]
    return t["blocking_title"].format(name=name), t["blocking_failed"].format(entity=entity, error=error)

