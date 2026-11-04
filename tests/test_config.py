"""Tests de la configuration et des taux (spec weekly-credit)."""

from fractions import Fraction

import pytest

from custom_components.screen_time_wallet.engine.config import Config, ConfigError


# --- Paramètres configurables ---------------------------------------------------

@pytest.mark.requirement("weekly-credit/Paramètres configurables")
def test_valeurs_par_defaut():
    c = Config()
    assert c.max_weekly_minutes == 1200
    assert c.notes_share == Fraction(3, 5)
    assert c.pivot == 12
    assert c.min_weight == 3
    assert c.min_subjects == 4
    assert c.fallback_credit == 240
    assert c.exclude_non_significant is False


@pytest.mark.requirement("weekly-credit/Paramètres configurables")
def test_parametre_modifie_demi_maximum():
    normal, reduced = Config(), Config(max_weekly_minutes=600)
    assert reduced.average_rate * 2 == normal.average_rate
    assert reduced.week_rate * 2 == normal.week_rate


@pytest.mark.requirement("weekly-credit/Paramètres configurables")
def test_les_nombres_decimaux_a_virgule_sont_acceptes():
    assert Config(pivot="11,5").pivot == Fraction(23, 2)


# --- Taux déduits du maximum et du ratio -----------------------------------------

@pytest.mark.requirement("weekly-credit/Taux déduits du maximum et du ratio")
def test_taux_par_defaut():
    c = Config()
    assert c.multiplier_total == Fraction(31, 2)
    assert float(c.average_rate) == pytest.approx(3.871, abs=0.001)
    assert float(c.week_rate) == pytest.approx(5.806, abs=0.001)


@pytest.mark.requirement("weekly-credit/Taux déduits du maximum et du ratio")
def test_maximum_atteint_a_20_sur_20():
    c = Config()
    initial = c.average_rate * c.multiplier_total * (20 - c.pivot)
    week = c.week_rate * c.multiplier_total * (20 - c.pivot)
    assert (initial, week, initial + week) == (480, 720, 1200)


@pytest.mark.requirement("weekly-credit/Taux déduits du maximum et du ratio")
def test_pivot_20_est_rejete():
    with pytest.raises(ConfigError):
        Config(pivot=20)


@pytest.mark.requirement("weekly-credit/Taux déduits du maximum et du ratio")
def test_somme_des_multiplicateurs_nulle_est_rejetee():
    with pytest.raises(ConfigError):
        Config(subject_multipliers={"MATHEMATIQUES": 0})
