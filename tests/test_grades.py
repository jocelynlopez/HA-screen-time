"""Tests de la spec grade-conversion. Chaque test déclare l'exigence qu'il vérifie."""

from fractions import Fraction

import pytest

from custom_components.screen_time_wallet.engine.config import Config
from custom_components.screen_time_wallet.engine.grades import Grade, InvalidGradeError
from real_notes import RAW, make

CFG = Config()


def grade(subject="MATHEMATIQUES", value=15, scale=20, coefficient=1, **kw):
    return Grade("2026-11-02", subject, "contrôle", value, scale, coefficient, **kw)


# --- Normalisation du barème -----------------------------------------------------

@pytest.mark.requirement("grade-conversion/Normalisation du barème")
def test_note_sur_10():
    assert grade(value=8, scale=10).on_20() == 16


@pytest.mark.requirement("grade-conversion/Normalisation du barème")
def test_note_sur_5_avec_virgule():
    assert grade(value="4,5", scale="5").on_20() == 18


@pytest.mark.requirement("grade-conversion/Normalisation du barème")
def test_note_sur_15():
    assert float(grade(value=2, scale=15).on_20()) == pytest.approx(2.67, abs=0.005)


# --- Multiplicateur par matière ----------------------------------------------------

@pytest.mark.requirement("grade-conversion/Multiplicateur par matière")
def test_matiere_classee():
    assert CFG.multiplier_for("HISTOIRE-GEOGRAPHIE") == 2


@pytest.mark.requirement("grade-conversion/Multiplicateur par matière")
def test_table_des_multiplicateurs():
    expected = {"MATHEMATIQUES": 3, "FRANCAIS": 3, "ANGLAIS LV1": 3, "ENS.INTEG.SC.&TECHNO": 3,
                "HISTOIRE-GEOGRAPHIE": 2, "EDUCATION MUSICALE": Fraction(1, 2),
                "ARTS PLASTIQUES": Fraction(1, 2), "ED PHYSIQUE & SPORT": Fraction(1, 2)}
    assert {name: CFG.multiplier_for(name) for name in expected} == expected


@pytest.mark.requirement("grade-conversion/Multiplicateur par matière")
def test_matiere_non_classee_est_signalee():
    assert CFG.multiplier_for("TECHNOLOGIE") == 0
    assert not CFG.is_known("TECHNOLOGIE")


@pytest.mark.requirement("grade-conversion/Multiplicateur par matière")
@pytest.mark.parametrize("name", ["Francais", "français", "FRANÇAIS", " Français "])
def test_matiere_sans_accent_ou_autre_casse(name):
    assert CFG.multiplier_for(name) == 3


@pytest.mark.requirement("grade-conversion/Multiplicateur par matière")
def test_table_modifiee():
    cfg = Config(subject_multipliers={**Config().subject_multipliers, "HISTOIRE-GEOGRAPHIE": 3})
    assert cfg.multiplier_for("HISTOIRE-GEOGRAPHIE") == 3


# --- Poids d'une note --------------------------------------------------------------

@pytest.mark.requirement("grade-conversion/Poids d'une note")
def test_poids_evaluation_principale():
    assert grade("FRANCAIS", coefficient=1).weight(CFG) == 3


@pytest.mark.requirement("grade-conversion/Poids d'une note")
def test_poids_faible_coefficient():
    assert grade("HISTOIRE-GEOGRAPHIE", coefficient="0,25").weight(CFG) == Fraction(1, 2)


@pytest.mark.requirement("grade-conversion/Poids d'une note")
def test_poids_matiere_inconnue():
    assert grade("TECHNOLOGIE").weight(CFG) == 0


# --- Note non numérique ------------------------------------------------------------

@pytest.mark.requirement("grade-conversion/Note non numérique")
@pytest.mark.parametrize("value", ["Abs", "Disp", "NE", "", None])
def test_valeur_non_numerique_est_non_notee(value):
    assert grade(value=value).is_graded() is False


@pytest.mark.requirement("grade-conversion/Note non numérique")
def test_valeur_avec_virgule_est_numerique():
    g = grade(value="7,5")
    assert g.is_graded() is True
    g.validate()  # aucune erreur


# --- Rejet des notes invalides -------------------------------------------------------

@pytest.mark.requirement("grade-conversion/Rejet des notes invalides")
def test_valeur_superieure_au_bareme():
    with pytest.raises(InvalidGradeError):
        grade(value=22).validate()


@pytest.mark.requirement("grade-conversion/Rejet des notes invalides")
def test_bareme_nul():
    with pytest.raises(InvalidGradeError):
        grade(value=10, scale=0).validate()


@pytest.mark.requirement("grade-conversion/Rejet des notes invalides")
def test_coefficient_negatif():
    with pytest.raises(InvalidGradeError):
        grade(coefficient=-1).validate()


# --- Clé d'une note (voir aussi screen-time-wallet) ------------------------------------

@pytest.mark.requirement("screen-time-wallet/Notes de la semaine")
def test_cles_des_18_notes_reelles_distinctes():
    keys = [make(r).key for r in RAW]
    assert len(keys) == 18 and len(set(keys)) == 18


@pytest.mark.requirement("screen-time-wallet/Notes de la semaine")
def test_la_cle_ignore_la_valeur_et_les_espaces_du_commentaire():
    a = Grade("2026-10-12", "Francais", "Dictée ", 2, 15, "0,75")
    b = Grade("2026-10-12", "FRANCAIS", "Dictée", 15, 15, 0.75)
    assert a.key == b.key
