"""Analyse pure des capteurs EcoleDirecte (spec ecoledirecte-source)."""

from fractions import Fraction

import pytest

from custom_components.screen_time_wallet.ecole_directe_source import parse_average, parse_notes
from custom_components.screen_time_wallet.engine.config import Config
from custom_components.screen_time_wallet.engine.grades import Grade
from real_notes import RAW, make


def entry(**changes):
    base = {
        "date": "2026-11-02", "matiere": "FRANCAIS", "commentaire": "Evaluation sommative séquence I",
        "note": "7", "sur": "20", "coefficient": "1", "non_significatif": False,
        "date_saisie": "2026-11-04", "elements_programme": [],
    }
    return {**base, **changes}


# --- Lecture des notes ------------------------------------------------------------------------

@pytest.mark.requirement("ecoledirecte-source/Lecture des notes")
def test_note_complete():
    (grade,) = parse_notes([entry()])
    assert grade == Grade("2026-11-02", "FRANCAIS", "Evaluation sommative séquence I", "7", "20", "1", False)
    assert grade.is_graded() and grade.on_20() == 7


@pytest.mark.requirement("ecoledirecte-source/Lecture des notes")
def test_virgule_decimale():
    (grade,) = parse_notes([entry(note="4,5", sur="5", coefficient="0,25")])
    assert grade.on_20() == 18
    assert grade.weight(Config()) == Fraction(3, 4)  # français (3) × coefficient 0,25


@pytest.mark.requirement("ecoledirecte-source/Lecture des notes")
def test_note_non_significative():
    (grade,) = parse_notes([entry(non_significatif=True)])
    assert grade.non_significant is True


@pytest.mark.requirement("ecoledirecte-source/Lecture des notes")
def test_valeur_non_numerique_transmise_telle_quelle():
    (grade,) = parse_notes([entry(note="Abs", sur="")])
    assert grade.value == "Abs" and grade.is_graded() is False


@pytest.mark.requirement("ecoledirecte-source/Lecture des notes")
@pytest.mark.parametrize("missing", ["matiere", "date"])
def test_entree_incomplete_ignoree(missing):
    assert parse_notes([entry(**{missing: ""}), entry(**{missing: None})]) == []


@pytest.mark.requirement("ecoledirecte-source/Lecture des notes")
def test_aucune_note():
    assert parse_notes([]) == []


@pytest.mark.requirement("ecoledirecte-source/Lecture des notes")
def test_dix_huit_notes_reelles_traduites():
    raw = [
        {"date": d, "matiere": m, "commentaire": c, "note": v, "sur": s, "coefficient": k,
         "non_significatif": ns, "date_saisie": saisie, "elements_programme": []}
        for d, saisie, m, c, v, s, k, ns in RAW
    ]
    assert parse_notes(raw) == [make(r) for r in RAW]


# --- Moyenne indisponible ---------------------------------------------------------------------------

@pytest.mark.requirement("ecoledirecte-source/Moyenne indisponible")
@pytest.mark.parametrize("state", ["unknown", "unavailable", "", "abc", "nan", "inf", None])
def test_etat_non_numerique_ignore(state):
    assert parse_average(state) is None


@pytest.mark.requirement("ecoledirecte-source/Moyenne indisponible")
def test_etat_numerique_lu():
    assert parse_average("13.85") == Fraction("13.85") and parse_average("13,85") == Fraction("13.85")
