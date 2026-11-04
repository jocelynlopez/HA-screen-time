"""Les 18 notes réelles du capteur EcoleDirecte (échantillon fourni), pour les tests."""

from custom_components.screen_time_wallet.engine.grades import Grade

# (date, date_saisie, matière, commentaire, note, sur, coefficient, non_significatif)
RAW = [
    ("2026-11-02", "2026-11-04", "FRANCAIS", "Evaluation sommative séquence I", "7", "20", "1", False),
    ("2026-11-03", "2026-11-03", "ARTS PLASTIQUES", "Lotoportrait (ressemblance, écart)", "9", "10", "0,5", False),
    ("2026-10-29", "2026-10-29", "HISTOIRE-GEOGRAPHIE", "histoire", "4,5", "5", "0,25", False),
    ("2026-10-29", "2026-10-29", "HISTOIRE-GEOGRAPHIE", "geographie", "19", "20", "1", False),
    ("2026-10-29", "2026-10-29", "HISTOIRE-GEOGRAPHIE", "histoire", "7", "10", "0,5", False),
    ("2026-10-12", "2026-10-16", "FRANCAIS", "Dictée", "2", "15", "0,75", False),
    ("2026-10-15", "2026-10-15", "EDUCATION MUSICALE", "Attitude", "7", "10", "1", True),
    ("2026-10-15", "2026-10-15", "EDUCATION MUSICALE", "Participation", "7", "10", "1", False),
    ("2026-10-15", "2026-10-15", "EDUCATION MUSICALE", "Chant classe", "9", "10", "1", False),
    ("2026-10-12", "2026-10-14", "ANGLAIS LV1", "Test vocabulaire", "4,5", "10", "0,5", False),
    ("2026-10-08", "2026-10-12", "ANGLAIS LV1", "Expression orale en interaction", "15", "15", "0,75", False),
    ("2026-10-05", "2026-10-05", "ENS.INTEG.SC.&TECHNO", "devoir n°1", "9", "10", "0,5", False),
    ("2026-09-29", "2026-10-01", "ANGLAIS LV1", "Test 1", "8", "20", "1", False),
    ("2026-09-27", "2026-10-01", "FRANCAIS", "Evaluation lecture", "4", "10", "0,5", False),
    ("2026-09-30", "2026-09-30", "ARTS PLASTIQUES", "Formes patatoïdales ", "16,5", "20", "1", False),
    ("2026-09-30", "2026-09-30", "ANGLAIS LV1", "Compréhension orale", "17,5", "20", "1", False),
    ("2026-09-28", "2026-09-29", "MATHEMATIQUES", "Automatismes N°1", "29", "30", "0,5", False),
    ("2026-09-23", "2026-09-25", "FRANCAIS", "Evaluation classes grammaticales", "18", "20", "1", False),
]


def make(raw):
    date, saisie, subject, comment, value, scale, coef, ns = raw
    return Grade(date, subject, comment, value, scale, coef, ns)


def grades(start=0, stop=None):
    return [make(r) for r in RAW[start:stop]]


def saisie_date(raw):
    return raw[1]
