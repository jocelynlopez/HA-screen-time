"""Bout en bout : rejeu des 18 notes réelles, lundi par lundi, du 21/09 au 09/11."""

from datetime import date, datetime, timedelta
from fractions import Fraction

import pytest

from custom_components.screen_time_wallet.engine.config import to_fraction
from custom_components.screen_time_wallet.engine.wallet import Wallet
from real_notes import RAW, make

SENSOR_AVERAGES = {  # états actuels des capteurs de moyenne (09/11)
    "ANGLAIS LV1": "13.85", "ARTS PLASTIQUES": "17", "EDUCATION MUSICALE": "16",
    "ENS.INTEG.SC.&TECHNO": "18", "FRANCAIS": "10.67", "HISTOIRE-GEOGRAPHIE": "17.43",
    "MATHEMATIQUES": "19.34", "ED PHYSIQUE & SPORT": "",
}
FIRST_MONDAY = datetime(2026, 9, 21)
MONDAYS = [FIRST_MONDAY + timedelta(weeks=i) for i in range(8)]  # 21/09 … 09/11


def visible_before(monday):
    """Notes visibles au bilan : celles saisies avant ce lundi."""
    return [make(r) for r in RAW if date.fromisoformat(r[1]) < monday.date()]


def averages_before(monday):
    """Moyennes par matière comme EcoleDirecte les calcule : coefficients, notes non significatives exclues."""
    if monday == MONDAYS[-1]:
        return SENSOR_AVERAGES
    totals = {}
    for raw in RAW:
        grade = make(raw)
        if date.fromisoformat(raw[1]) < monday.date() and not grade.non_significant:
            coefficient = to_fraction(grade.coefficient)
            num, den = totals.get(grade.subject, (Fraction(0), Fraction(0)))
            totals[grade.subject] = (num + grade.on_20() * coefficient, den + coefficient)
    return {subject: num / den for subject, (num, den) in totals.items()}


@pytest.mark.requirement("screen-time-wallet/Bilan du lundi")
def test_rejeu_des_dix_huit_notes_reelles():
    wallet = Wallet.create(FIRST_MONDAY, {})
    assert wallet.weekly_credit == 240  # aucune moyenne : crédit de repli
    reports = []
    for monday in MONDAYS[1:]:
        reports += wallet.settle(monday, averages_before(monday), visible_before(monday))
    assert [r.week_credit for r in reports] == [0, 111, 459, -30, 317, 489, -374]
    assert [r.initial_credit for r in reports] == [240, 218, 252, 211, 211, 227, 228]
    assert wallet.notes_capital == 972
    assert wallet.weekly_credit == 228
    assert wallet.available == 1200
