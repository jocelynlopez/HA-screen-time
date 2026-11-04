"""Lecture des capteurs EcoleDirecte : découverte des moyennes et indisponibilités (spec ecoledirecte-source)."""

from fractions import Fraction

import pytest

from custom_components.screen_time_wallet.ecole_directe_source import EcoleDirecteSource
from custom_components.screen_time_wallet.engine.config import Config
from custom_components.screen_time_wallet.source import SourceUnavailableError

from ed_helpers import add_all_subjects, add_ed_entry, add_notes, add_sensor, add_subject

NOTES = [{"date": "2026-11-02", "matiere": "FRANCAIS", "commentaire": "Sommative", "note": "7",
          "sur": "20", "coefficient": "1", "non_significatif": False}]


@pytest.fixture
async def mael(hass):
    ed = add_ed_entry(hass, "Mael")
    add_all_subjects(hass, ed)
    notes = add_notes(hass, ed, NOTES)
    add_sensor(hass, ed, "ed_mael_lopez_evaluations", "5", {"Evaluations": []})  # sans Nom ni Code
    return ed, notes


# --- Découverte des moyennes par matière ----------------------------------------------------------

@pytest.mark.requirement("ecoledirecte-source/Découverte des moyennes par matière")
async def test_sept_moyennes_par_nom_de_matiere(hass, mael):
    data = await EcoleDirecteSource(hass, mael[1]).async_fetch()
    assert data.averages == {
        "anglais lv1": Fraction("13.85"), "arts plastiques": Fraction(17), "education musicale": Fraction(16),
        "ens.integ.sc.&techno": Fraction(18), "francais": Fraction("10.67"),
        "histoire-geographie": Fraction("17.43"), "mathematiques": Fraction("19.34"),
    }
    assert len(data.notes) == 1 and data.notes[0].subject == "FRANCAIS"


@pytest.mark.requirement("ecoledirecte-source/Découverte des moyennes par matière")
async def test_capteurs_etrangers_ignores(hass, mael):
    other = add_ed_entry(hass, "Lena")  # autre enfant, autre entrée EcoleDirecte
    add_subject(hass, other, "ed_lena_sport", "sport lena", "eps", "9")
    data = await EcoleDirecteSource(hass, mael[1]).async_fetch()
    assert "sport lena" not in data.averages and len(data.averages) == 7


@pytest.mark.requirement("ecoledirecte-source/Découverte des moyennes par matière")
async def test_nom_du_sport_rattache_a_la_table(hass, mael):
    ed, notes = mael
    add_subject(hass, ed, "ed_mael_lopez_ed_physique_sport", "ed.physique & sport.", "eps", "12")
    data = await EcoleDirecteSource(hass, notes).async_fetch()
    assert data.averages["ed.physique & sport."] == 12
    assert Config().multiplier_for("ed.physique & sport.") == Fraction(1, 2)


@pytest.mark.requirement("ecoledirecte-source/Moyenne indisponible")
async def test_sport_sans_moyenne_absent_sans_erreur(hass, mael):
    data = await EcoleDirecteSource(hass, mael[1]).async_fetch()  # état du sport : unknown
    assert "ed.physique & sport." not in data.averages


# --- Capteur de notes indisponible --------------------------------------------------------------------

@pytest.mark.requirement("ecoledirecte-source/Capteur de notes indisponible")
@pytest.mark.parametrize("state", ["unavailable", "unknown"])
async def test_capteur_de_notes_indisponible(hass, mael, state):
    hass.states.async_set(mael[1], state, {"notes": NOTES})
    with pytest.raises(SourceUnavailableError):
        await EcoleDirecteSource(hass, mael[1]).async_fetch()


@pytest.mark.requirement("ecoledirecte-source/Capteur de notes indisponible")
async def test_capteur_de_notes_absent(hass):
    with pytest.raises(SourceUnavailableError):
        await EcoleDirecteSource(hass, "sensor.n_existe_pas").async_fetch()


@pytest.mark.requirement("ecoledirecte-source/Capteur de notes indisponible")
async def test_capteur_sans_attribut_notes(hass, mael):
    hass.states.async_set(mael[1], "15", {})
    with pytest.raises(SourceUnavailableError):
        await EcoleDirecteSource(hass, mael[1]).async_fetch()


@pytest.mark.requirement("ecoledirecte-source/Capteur de notes indisponible")
async def test_aucune_moyenne_decouverte(hass):
    ed = add_ed_entry(hass)
    notes = add_notes(hass, ed, NOTES)
    data = await EcoleDirecteSource(hass, notes).async_fetch()
    assert data.averages == {} and len(data.notes) == 1
