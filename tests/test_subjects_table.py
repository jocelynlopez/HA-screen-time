"""Mise en forme de la table des matières (spec ha-integration, Table des matières visible)."""

import pytest

from custom_components.screen_time_wallet.report import render_subjects_table


@pytest.mark.requirement("ha-integration/Table des matières visible")
def test_lignes_triees_sans_casse_ni_accents():
    table = {"MATHEMATIQUES": 3.0, "éducation musicale": 0.5, "ARTS PLASTIQUES": 0.5, "Technologie": 1.0}
    lines = render_subjects_table(table, "fr").splitlines()
    assert lines == ["- ARTS PLASTIQUES : 0,5", "- éducation musicale : 0,5", "- MATHEMATIQUES : 3",
                     "- Technologie : 1"]


@pytest.mark.requirement("ha-integration/Table des matières visible")
def test_ecriture_des_nombres_selon_la_langue():
    table = {"EDUCATION MUSICALE": 0.5, "MATHEMATIQUES": 3}
    assert render_subjects_table(table, "fr") == "- EDUCATION MUSICALE : 0,5\n- MATHEMATIQUES : 3"
    assert render_subjects_table(table, "en") == "- EDUCATION MUSICALE : 0.5\n- MATHEMATIQUES : 3"
    assert render_subjects_table({"LATIN": 0.0}, "fr") == "- LATIN : 0"


@pytest.mark.requirement("ha-integration/Table des matières visible")
def test_table_vide():
    assert render_subjects_table({}, "fr") == ""
