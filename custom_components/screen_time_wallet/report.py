"""Mise en forme (fonctions pures) du rapport hebdomadaire et de la notification d'anomalie."""

from collections.abc import Mapping
from fractions import Fraction

from .engine.config import Config, normalize_subject, to_fraction
from .engine.wallet import Report

TEXTS = {
    "fr": {
        "report_title": "Bilan du portefeuille de {name}",
        "week_title": "Ton temps de la semaine (lundi {date}) :",
        "carried": "• Reporté des semaines précédentes : {minutes} min",
        "note_minutes": "• {subject} {value}/20 : {minutes} min",
        "complement": "• Complément moyenne générale ({average}) : {minutes} min",
        "available": "Temps disponible : {available} min",
        "initial_fallback": "Crédit initial : {minutes} min (crédit de repli : {count} matière(s) avec moyenne, {needed} requises)",
        "week_credit_fallback": "Crédit de semaine : 0 min (crédit de repli)",
        "totals": "Capital notes : {capital} min · Temps disponible : {available} min",
        "manual_header": "Mouvements manuels de la semaine :",
        "manual_line": "• {date} · {minutes} min · {reason}",
        "no_reason": "sans motif",
        "automatic_header": "Consommation automatique :",
        "automatic_line": "• {reason} : {minutes} min",
        "forecast_title": "Prévision du lundi {date}",
        "forecast_note": "Si rien ne change d'ici là.",
        "forecast_unavailable": "Prévision indisponible : source des notes inaccessible.",
        "no_report": "Aucun rapport pour le moment.",
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
        "week_title": "Your time this week (Monday {date}):",
        "carried": "• Carried over from previous weeks: {minutes} min",
        "note_minutes": "• {subject} {value}/20: {minutes} min",
        "complement": "• Overall average bonus ({average}): {minutes} min",
        "available": "Available time: {available} min",
        "initial_fallback": "Initial credit: {minutes} min (fallback credit: {count} subject(s) with an average, {needed} required)",
        "week_credit_fallback": "Week credit: 0 min (fallback credit)",
        "totals": "Notes capital: {capital} min · Available time: {available} min",
        "manual_header": "Manual movements this week:",
        "manual_line": "• {date} · {minutes} min · {reason}",
        "no_reason": "no reason",
        "automatic_header": "Automatic consumption:",
        "automatic_line": "• {reason}: {minutes} min",
        "forecast_title": "Forecast for Monday {date}",
        "forecast_note": "If nothing changes until then.",
        "forecast_unavailable": "Forecast unavailable: grades source unreachable.",
        "no_report": "No report yet.",
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


def render_report(reports: list[Report], name: str, config: Config, language: str) -> tuple[str, str]:
    """Titre et message du rapport hebdomadaire ; une section par lundi traité."""
    lang = _language(language)
    t = TEXTS[lang]
    sections = []
    for report in reports:
        lines = [t["week_title"].format(date=_date(report.monday, lang))]
        lines.extend(_report_lines(report, config, t, lang))
        sections.append("\n".join(lines))
    return t["report_title"].format(name=name), "\n\n".join(sections)


def render_forecast(report: Report, config: Config, language: str) -> str:
    """Prévision du bilan du prochain lundi : même détail que le rapport, titré comme une prévision."""
    lang = _language(language)
    t = TEXTS[lang]
    lines = [t["forecast_title"].format(date=_date(report.monday, lang)), t["forecast_note"]]
    lines.extend(_report_lines(report, config, t, lang))
    return "\n".join(lines)


def render_forecast_unavailable(report: Report, language: str) -> str:
    """Prévision sans la source des notes : seuls les mouvements de la semaine sont connus."""
    lang = _language(language)
    t = TEXTS[lang]
    lines = [t["forecast_title"].format(date=_date(report.monday, lang)), t["forecast_unavailable"]]
    lines.extend(_movement_lines(report, t, lang))
    return "\n".join(lines)


def render_no_report(language: str) -> str:
    return TEXTS[_language(language)]["no_report"]


def _report_lines(report: Report, config: Config, t: dict, lang: str) -> list[str]:
    """Bloc de l'enfant : temps reporté, minutes de chaque note, complément de la moyenne générale, temps disponible.

    Une semaine de crédit de repli garde les lignes de repli (pas de moyenne, donc ni notes ni complément)."""
    lines = []
    if report.fallback:
        lines.append(t["initial_fallback"].format(
            minutes=report.initial_credit, count=report.subjects_count, needed=config.min_subjects))
        lines.append(t["week_credit_fallback"])
        lines.append(t["totals"].format(capital=f"{report.notes_capital:+d}", available=report.available))
    else:
        if report.carried:
            lines.append(t["carried"].format(minutes=f"{report.carried:+d}"))
        for grade, minutes in report.note_minutes:
            lines.append(t["note_minutes"].format(
                subject=grade.subject, value=_number(grade.on_20(), lang, trim=True), minutes=f"{minutes:+d}"))
        lines.append(t["complement"].format(
            average=_number(report.general_average, lang), minutes=f"{report.complement:+d}"))
        lines.append(t["available"].format(available=report.available))
    lines.extend(_movement_lines(report, t, lang))
    return lines


def _movement_lines(report: Report, t: dict, lang: str) -> list[str]:
    """Mouvements manuels de la semaine puis consommation automatique ; vide s'il n'y en a pas."""
    lines = []
    if report.manual:
        lines.append(t["manual_header"])
        for movement in report.manual:
            lines.append(t["manual_line"].format(
                date=_date_time(movement.when, lang), minutes=f"{movement.weekly_change + movement.capital_change:+d}",
                reason=movement.reason or t["no_reason"]))
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

