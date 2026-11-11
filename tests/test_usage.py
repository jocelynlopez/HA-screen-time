"""Tests de la spec screen-time-usage (consommation entre deux relevés). Chaque test déclare son exigence."""

from fractions import Fraction

import pytest

from custom_components.screen_time_wallet.engine.usage import (
    Baseline,
    consumed_since,
    normalize_day,
    reading_minutes,
)

D1, D2 = "2026-11-04", "2026-11-05"


def base(minutes, day=None):
    return Baseline(Fraction(str(minutes)), day)


# --- Consommation entre deux relevés -----------------------------------------------------------

@pytest.mark.requirement("screen-time-usage/Consommation entre deux relevés")
def test_usage_normal():
    consumed, new = consumed_since(base(10), 25)
    assert (consumed, new.minutes) == (15, 25)


@pytest.mark.requirement("screen-time-usage/Consommation entre deux relevés")
def test_aucun_usage():
    assert consumed_since(base(25), 25)[0] == 0


@pytest.mark.requirement("screen-time-usage/Consommation entre deux relevés")
def test_minutes_fractionnaires():
    consumed, ref = consumed_since(base(10), "10,6")
    assert (consumed, ref.minutes) == (0, 10)
    consumed, ref = consumed_since(ref, "11.2")
    assert (consumed, ref.minutes) == (1, 11)


# --- Premier relevé ------------------------------------------------------------------------------

@pytest.mark.requirement("screen-time-usage/Premier relevé")
def test_premier_releve_en_cours_de_journee():
    consumed, ref = consumed_since(None, 87, D1)
    assert (consumed, ref) == (0, Baseline(Fraction(87), D1))


@pytest.mark.requirement("screen-time-usage/Premier relevé")
def test_releve_suivant_le_premier():
    _, ref = consumed_since(None, 87)
    assert consumed_since(ref, 92)[0] == 5


# --- Remise à zéro du compteur -------------------------------------------------------------------

@pytest.mark.requirement("screen-time-usage/Remise à zéro du compteur")
def test_changement_de_jour_sans_baisse():
    consumed, ref = consumed_since(base(190, D1), 200, D2)
    assert (consumed, ref) == (200, Baseline(Fraction(200), D2))


@pytest.mark.requirement("screen-time-usage/Remise à zéro du compteur")
def test_baisse_sans_date():
    consumed, ref = consumed_since(base(190), 12)
    assert (consumed, ref.minutes) == (12, 12)


@pytest.mark.requirement("screen-time-usage/Remise à zéro du compteur")
def test_remise_a_zero_exacte():
    consumed, ref = consumed_since(base(190), 0)
    assert (consumed, ref.minutes) == (0, 0)


@pytest.mark.requirement("screen-time-usage/Remise à zéro du compteur")
def test_meme_jour():
    assert consumed_since(base(12, D1), 30, D1)[0] == 18


@pytest.mark.requirement("screen-time-usage/Remise à zéro du compteur")
def test_baisse_persistante_le_meme_jour_ignoree():
    ref = base(190, D1)
    for reading in (12, 14):
        consumed, ref = consumed_since(ref, reading, D1)
        assert (consumed, ref) == (0, base(190, D1))


@pytest.mark.requirement("screen-time-usage/Remise à zéro du compteur")
def test_non_regression_compteur_oscillant_11_11():
    """Mercredi 11/11 : 23, 18, 18, 23, 18, 28… recomptait 18 puis 23 minutes (89 min au lieu de 38)."""
    ref, total = base(23, D1), 0
    for reading in (18, 18, 23, 18, 28):
        consumed, ref = consumed_since(ref, reading, D1)
        total += consumed
    assert (total, ref) == (5, base(28, D1))


@pytest.mark.requirement("screen-time-usage/Remise à zéro du compteur")
def test_non_regression_baisse_passagere_46_36_46():
    """Samedi 07/11 : un relevé transitoirement bas était recompté (−36 min)."""
    consumed, ref = consumed_since(base(46, D1), 36, D1)
    assert consumed == 0
    consumed, ref = consumed_since(ref, 46, D1)
    assert (consumed, ref) == (0, Baseline(Fraction(46), D1))


@pytest.mark.requirement("screen-time-usage/Remise à zéro du compteur")
def test_non_regression_releve_perime_a_minuit():
    """Samedi 00h00 : la date change avant les minutes, le total de la veille était recompté (−40 min)."""
    consumed, ref = consumed_since(base(40, D1), 40, D2)
    assert (consumed, ref) == (0, Baseline(Fraction(40), D2, True))
    consumed, ref = consumed_since(ref, 0, D2)
    assert (consumed, ref) == (0, Baseline(Fraction(0), D2))


@pytest.mark.requirement("screen-time-usage/Remise à zéro du compteur")
def test_remise_a_zero_apres_releve_perime():
    _, ref = consumed_since(base(40, D1), 40, D2)
    consumed, ref = consumed_since(ref, 3, D2)
    assert (consumed, ref) == (3, Baseline(Fraction(3), D2))


@pytest.mark.requirement("screen-time-usage/Remise à zéro du compteur")
def test_serialisation_du_doute():
    assert "suspect" not in base(5, D1).to_json()
    doubtful = Baseline(Fraction(5), D1, True)
    assert Baseline.from_json(doubtful.to_json()) == doubtful
    assert Baseline.from_json({"minutes": "5/1", "date": D1}) == base(5, D1)


@pytest.mark.requirement("screen-time-usage/Remise à zéro du compteur")
def test_reference_sans_date_compare_les_valeurs_puis_memorise_le_jour():
    consumed, ref = consumed_since(base(10), 25, D1)
    assert (consumed, ref.day) == (15, D1)


@pytest.mark.requirement("screen-time-usage/Remise à zéro du compteur")
def test_changement_de_jour_avec_fraction_reportee():
    consumed, ref = consumed_since(base("190.5", D1), "12,7", D2)
    assert (consumed, ref.minutes) == (12, 12)


# --- Relevé invalide ignoré ------------------------------------------------------------------------

@pytest.mark.requirement("screen-time-usage/Relevé invalide ignoré")
@pytest.mark.parametrize("reading", ["unavailable", "unknown", "", None, "abc", -5, "-5", True])
def test_releve_invalide_ignore(reading):
    ref = base(25, D1)
    assert consumed_since(ref, reading, D2) == (0, ref)


@pytest.mark.requirement("screen-time-usage/Relevé invalide ignoré")
def test_releve_invalide_sans_reference():
    assert consumed_since(None, "unavailable") == (0, None)


# --- Lecture du relevé et du jour (fonctions utilisées par la couche Home Assistant) ----------------------

@pytest.mark.requirement("ha-integration/Capteurs de temps d'écran")
def test_releve_en_secondes_prioritaire():
    assert reading_minutes("10", 660) == 11
    assert reading_minutes("10", "660") == 11


@pytest.mark.requirement("ha-integration/Capteurs de temps d'écran")
def test_repli_sur_l_etat():
    assert reading_minutes("10", None) == 10
    assert reading_minutes("10", "n/a") == 10


@pytest.mark.requirement("ha-integration/Capteurs de temps d'écran")
@pytest.mark.parametrize("state", ["unavailable", "unknown", None, "-3"])
def test_etat_invalide_sans_secondes(state):
    assert reading_minutes(state, None) is None


def test_jour_illisible_ignore():
    assert normalize_day("2026-11-04") == D1
    assert normalize_day("04/11/2026") is None
    assert normalize_day(None) is None


def test_aller_retour_json():
    ref = Baseline(Fraction(21, 2), D1)
    assert Baseline.from_json(ref.to_json()) == ref
    assert Baseline.from_json({"minutes": "5/1"}) == Baseline(Fraction(5), None)
