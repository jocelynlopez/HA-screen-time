"""Tests de la spec grade-conversion. Chaque test déclare l'exigence qu'il vérifie."""

from datetime import date
from fractions import Fraction

import pytest

from portefeuille_minutes.config import Config
from portefeuille_minutes.grades import Grade, InvalidGradeError, convert

CFG = Config()


def grade(subject="maths", value=15, scale=20, coefficient=1):
    return Grade("n-1", subject, date(2026, 11, 4), value, scale, coefficient)


# --- Formule de conversion -------------------------------------------------

@pytest.mark.requirement("grade-conversion/Formule de conversion")
def test_note_au_dessus_du_pivot():
    assert convert(grade("maths", 15), CFG) == 135


@pytest.mark.requirement("grade-conversion/Formule de conversion")
def test_note_en_dessous_du_pivot():
    assert convert(grade("français", 8), CFG) == -240


@pytest.mark.requirement("grade-conversion/Formule de conversion")
def test_note_egale_au_pivot():
    assert convert(grade("maths", 12), CFG) == 0


# --- Note pivot ------------------------------------------------------------

@pytest.mark.requirement("grade-conversion/Note pivot")
def test_pivot_modifie():
    assert convert(grade("maths", 15), Config(pivot=Fraction(10))) == 225


# --- Normalisation du barème -----------------------------------------------

@pytest.mark.requirement("grade-conversion/Normalisation du barème")
def test_note_sur_10():
    assert convert(grade("maths", 8, scale=10), CFG) == 180


# --- Multiplicateur par matière ---------------------------------------------

@pytest.mark.requirement("grade-conversion/Multiplicateur par matière")
def test_matiere_classee():
    assert convert(grade("histoire", 14), CFG) == 60


@pytest.mark.requirement("grade-conversion/Multiplicateur par matière")
def test_matiere_non_classee():
    assert convert(grade("technologie", 5), CFG) == 0


@pytest.mark.requirement("grade-conversion/Multiplicateur par matière")
@pytest.mark.parametrize("subject", ["Francais", "français", "FRANÇAIS", " Français "])
def test_matiere_sans_accent_ou_autre_casse(subject):
    assert convert(grade(subject, 8), CFG) == -240


@pytest.mark.requirement("grade-conversion/Multiplicateur par matière")
@pytest.mark.parametrize(
    "subject, expected",
    [("maths", 3), ("français", 4), ("histoire", 2), ("anglais", 3), ("eist", 3),
     ("musique", Fraction(1, 2)), ("arts plastiques", Fraction(1, 2)),
     ("art plastique", Fraction(1, 2)), ("sport", Fraction(1, 2))],
)
def test_table_des_multiplicateurs(subject, expected):
    assert CFG.multiplier_for(subject) == expected


# --- Taux de base ------------------------------------------------------------

@pytest.mark.requirement("grade-conversion/Taux de base")
def test_taux_de_base_par_defaut():
    assert CFG.base_rate == 15


@pytest.mark.requirement("grade-conversion/Taux de base")
def test_taux_de_base_modifie():
    assert convert(grade("maths", 15), Config(base_rate=Fraction(10))) == 90


# --- Coefficient ------------------------------------------------------------

@pytest.mark.requirement("grade-conversion/Coefficient")
def test_fort_coefficient():
    assert convert(grade("maths", 15, coefficient=3), CFG) == 405


@pytest.mark.requirement("grade-conversion/Coefficient")
def test_coefficient_decimal():
    assert convert(grade("maths", 15, coefficient=0.5), CFG) == 68


# --- Arrondi -----------------------------------------------------------------

@pytest.mark.requirement("grade-conversion/Arrondi")
def test_demi_minute_positive():
    assert convert(grade("sport", 13), CFG) == 8


@pytest.mark.requirement("grade-conversion/Arrondi")
def test_demi_minute_negative():
    assert convert(grade("sport", 11), CFG) == -8


# --- Rejet des notes invalides ------------------------------------------------

@pytest.mark.requirement("grade-conversion/Rejet des notes invalides")
def test_valeur_superieure_au_bareme():
    with pytest.raises(InvalidGradeError):
        convert(grade("maths", 22), CFG)


@pytest.mark.requirement("grade-conversion/Rejet des notes invalides")
def test_bareme_nul():
    with pytest.raises(InvalidGradeError):
        convert(grade("maths", 10, scale=0), CFG)


@pytest.mark.requirement("grade-conversion/Rejet des notes invalides")
def test_valeur_negative():
    with pytest.raises(InvalidGradeError):
        convert(grade("maths", -1), CFG)


@pytest.mark.requirement("grade-conversion/Rejet des notes invalides")
def test_coefficient_negatif():
    with pytest.raises(InvalidGradeError):
        convert(grade("maths", 15, coefficient=-1), CFG)
