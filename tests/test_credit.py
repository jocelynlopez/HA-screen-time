"""Tests de la spec weekly-credit (crédits). Chaque test déclare l'exigence qu'il vérifie."""

from fractions import Fraction

import pytest

from custom_components.screen_time_wallet.engine.config import Config
from custom_components.screen_time_wallet.engine.credit import (
    general_average,
    initial_credit,
    week_average,
    week_credit,
)
from custom_components.screen_time_wallet.engine.grades import Grade

CFG = Config()

# Moyennes actuelles du capteur EcoleDirecte (sport sans moyenne).
SEVEN = {
    "ANGLAIS LV1": "13.85", "ARTS PLASTIQUES": "17", "EDUCATION MUSICALE": "16",
    "ENS.INTEG.SC.&TECHNO": "18", "FRANCAIS": "10.67", "HISTOIRE-GEOGRAPHIE": "17.43",
    "MATHEMATIQUES": "19.34", "ED PHYSIQUE & SPORT": "",
}
GENERAL = general_average(SEVEN, CFG)


def grade(subject, value, scale=20, coefficient=1, non_significant=False):
    return Grade("2026-11-02", subject, "contrôle", value, scale, coefficient, non_significant)


# --- Moyenne générale pondérée ---------------------------------------------------

@pytest.mark.requirement("weekly-credit/Moyenne générale pondérée")
def test_sept_matieres_avec_moyenne():
    assert float(GENERAL) == pytest.approx(15.80, abs=0.005)


@pytest.mark.requirement("weekly-credit/Moyenne générale pondérée")
def test_matiere_sans_moyenne_est_ignoree():
    without_sport = {k: v for k, v in SEVEN.items() if k != "ED PHYSIQUE & SPORT"}
    assert general_average(without_sport, CFG) == GENERAL


@pytest.mark.requirement("weekly-credit/Moyenne générale pondérée")
def test_matiere_de_multiplicateur_nul_est_ignoree():
    assert general_average({**SEVEN, "TECHNOLOGIE": "2"}, CFG) == GENERAL


# --- Crédit initial ----------------------------------------------------------------

@pytest.mark.requirement("weekly-credit/Crédit initial")
def test_credit_initial_sept_matieres():
    assert initial_credit(SEVEN, CFG) == 228


@pytest.mark.requirement("weekly-credit/Crédit initial")
def test_credit_initial_maximum():
    assert initial_credit({m: 20 for m in CFG.subject_multipliers}, CFG) == 480


@pytest.mark.requirement("weekly-credit/Crédit initial")
@pytest.mark.parametrize("average", [12, 10])
def test_credit_initial_plancher_a_zero(average):
    assert initial_credit({m: average for m in CFG.subject_multipliers}, CFG) == 0


@pytest.mark.requirement("weekly-credit/Crédit initial")
def test_credit_initial_repli_sous_le_minimum():
    three = {"MATHEMATIQUES": 15, "FRANCAIS": 14, "ANGLAIS LV1": 16}
    assert initial_credit(three, CFG) == 240


@pytest.mark.requirement("weekly-credit/Crédit initial")
def test_credit_initial_au_minimum_de_matieres():
    four = {m: 14 for m in ("MATHEMATIQUES", "FRANCAIS", "ANGLAIS LV1", "ENS.INTEG.SC.&TECHNO")}
    assert initial_credit(four, CFG) == 120


# --- Moyenne de la semaine -------------------------------------------------------------

AP_FR = [grade("ARTS PLASTIQUES", 9, 10, "0,5"), grade("FRANCAIS", 7)]


@pytest.mark.requirement("weekly-credit/Moyenne de la semaine")
def test_poids_suffisant():
    assert float(week_average(AP_FR, GENERAL, CFG)) == pytest.approx(7.85, abs=0.005)


@pytest.mark.requirement("weekly-credit/Moyenne de la semaine")
def test_semaine_sans_note():
    assert week_average([], GENERAL, CFG) == GENERAL


@pytest.mark.requirement("weekly-credit/Moyenne de la semaine")
def test_note_de_faible_poids_completee_par_la_moyenne_generale():
    light = [grade("HISTOIRE-GEOGRAPHIE", "4,5", 5, "0,25")]
    assert float(week_average(light, GENERAL, CFG)) == pytest.approx(16.16, abs=0.005)


# --- Crédit de semaine --------------------------------------------------------------------

@pytest.mark.requirement("weekly-credit/Crédit de semaine")
def test_semaine_sans_note_credit_neutre():
    assert week_credit([], SEVEN, CFG) == 342


@pytest.mark.requirement("weekly-credit/Crédit de semaine")
def test_mauvaise_semaine():
    assert week_credit(AP_FR, SEVEN, CFG) == -374


@pytest.mark.requirement("weekly-credit/Crédit de semaine")
def test_une_seule_tres_mauvaise_note():
    assert week_credit([grade("FRANCAIS", 7)], SEVEN, CFG) == -450


@pytest.mark.requirement("weekly-credit/Crédit de semaine")
def test_une_seule_excellente_note():
    assert week_credit([grade("MATHEMATIQUES", 20)], SEVEN, CFG) == 720


@pytest.mark.requirement("weekly-credit/Crédit de semaine")
def test_le_volume_ne_gonfle_pas_le_credit():
    five = [grade("MATHEMATIQUES", 14) for _ in range(5)]
    assert week_credit(five, SEVEN, CFG) == 180
    assert week_credit(five, SEVEN, CFG) < week_credit([grade("MATHEMATIQUES", 20)], SEVEN, CFG)


@pytest.mark.requirement("weekly-credit/Crédit de semaine")
def test_repli_credit_de_semaine_nul():
    assert week_credit(AP_FR, {"MATHEMATIQUES": 15, "FRANCAIS": 14}, CFG) == 0


# --- Arrondi des crédits ---------------------------------------------------------------------

ROUNDING = Config(
    max_weekly_minutes=8, notes_share=1, min_weight=1, min_subjects=1,
    subject_multipliers={"MATIERE": 1},
)


@pytest.mark.requirement("weekly-credit/Arrondi des crédits")
def test_demi_minute_positive():
    assert week_credit([grade("MATIERE", "12,5")], {"MATIERE": 12}, ROUNDING) == 1


@pytest.mark.requirement("weekly-credit/Arrondi des crédits")
def test_demi_minute_negative():
    assert week_credit([grade("MATIERE", "11,5")], {"MATIERE": 12}, ROUNDING) == -1


# --- Notes non significatives -------------------------------------------------------------------

NS = grade("EDUCATION MUSICALE", 7, 10, 1, non_significant=True)


@pytest.mark.requirement("weekly-credit/Notes non significatives")
def test_option_desactivee_la_note_compte():
    notes_only = Config(min_weight=Fraction(1, 2))
    assert float(week_average([NS], GENERAL, notes_only)) == pytest.approx(14, abs=0.001)


@pytest.mark.requirement("weekly-credit/Notes non significatives")
def test_option_activee_la_note_est_exclue():
    cfg = Config(min_weight=Fraction(1, 2), exclude_non_significant=True)
    assert week_average([NS], GENERAL, cfg) == GENERAL
