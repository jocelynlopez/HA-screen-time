"""Mise en forme (fonctions pures) du rapport hebdomadaire et de la notification d'anomalie."""

from fractions import Fraction

from .engine.config import Config
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
        "anomaly_title": "Portefeuille de {name} : à vérifier",
        "unknown_subjects": "Matières inconnues (sans effet) : {subjects}. Ajoutez-les avec leur multiplicateur dans les options de l'intégration, étape « Matières ».",
        "rejected_note": "Note rejetée : {subject} {value}/{scale} du {date} ({reason})",
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
        "anomaly_title": "{name}'s wallet: needs attention",
        "unknown_subjects": "Unknown subjects (no effect): {subjects}. Add them with their multiplier in the integration options, \"Subjects\" step.",
        "rejected_note": "Rejected grade: {subject} {value}/{scale} of {date} ({reason})",
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
        sections.append("\n".join(lines))
    return t["report_title"].format(name=name), "\n\n".join(sections)


def render_anomalies(reports: list[Report], name: str, language: str) -> tuple[str, str] | None:
    """Titre et message des matières inconnues et notes rejetées ; None s'il n'y a rien à signaler."""
    lang = _language(language)
    t = TEXTS[lang]
    unknown = [s for r in reports for s in r.unknown_subjects]
    rejected = [item for r in reports for item in r.rejected]
    if not unknown and not rejected:
        return None
    lines = []
    if unknown:
        lines.append(t["unknown_subjects"].format(subjects=", ".join(dict.fromkeys(unknown))))
    for grade, reason in rejected:
        lines.append(t["rejected_note"].format(
            subject=grade.subject, value=grade.value, scale=grade.scale, date=grade.date, reason=reason))
    return t["anomaly_title"].format(name=name), "\n".join(lines)
