"""Tests de la spec screen-time-wallet. Chaque test déclare l'exigence qu'il vérifie."""

from datetime import datetime

import pytest

from custom_components.screen_time_wallet.engine.config import Config
from custom_components.screen_time_wallet.engine.grades import Grade
from custom_components.screen_time_wallet.engine.wallet import InvalidConsumptionError, Wallet
from real_notes import RAW, make

SEVEN = {
    "ANGLAIS LV1": "13.85", "ARTS PLASTIQUES": "17", "EDUCATION MUSICALE": "16",
    "ENS.INTEG.SC.&TECHNO": "18", "FRANCAIS": "10.67", "HISTOIRE-GEOGRAPHIE": "17.43",
    "MATHEMATIQUES": "19.34", "ED PHYSIQUE & SPORT": "",
}
SIXTEEN = {m: "16.2" for m in Config().subject_multipliers}  # moyenne générale exactement 16,2
TWO = {"MATHEMATIQUES": 15, "FRANCAIS": 14}

MONDAY = datetime(2026, 11, 2)
WEDNESDAY = datetime(2026, 11, 4, 15, 30)
NEXT_MONDAY = datetime(2026, 11, 9)


def grade(subject="MATHEMATIQUES", value=15, scale=20, coefficient=1, comment="contrôle", date="2026-11-04"):
    return Grade(date, subject, comment, value, scale, coefficient)


AP_FR = [grade("ARTS PLASTIQUES", 9, 10, "0,5", comment="Lotoportrait"), grade("FRANCAIS", 7, comment="Sommative")]


def fresh(averages=SEVEN, notes=()):
    return Wallet.create(MONDAY, averages, notes)


# --- Deux compartiments ----------------------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Deux compartiments")
def test_capital_negatif_reduit_le_temps_disponible():
    w = fresh()
    w.notes_capital = -100
    assert (w.weekly_credit, w.available) == (228, 128)


@pytest.mark.requirement("screen-time-wallet/Deux compartiments")
def test_les_compartiments_sont_des_entiers():
    w = fresh()
    w.settle(NEXT_MONDAY, SEVEN, AP_FR)
    assert isinstance(w.weekly_credit, int) and isinstance(w.notes_capital, int)


# --- Initialisation du portefeuille -------------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Initialisation du portefeuille")
def test_creation_en_milieu_de_semaine():
    w = Wallet.create(WEDNESDAY, SEVEN)
    assert (w.weekly_credit, w.notes_capital, w.available) == (228, 0, 228)


@pytest.mark.requirement("screen-time-wallet/Initialisation du portefeuille")
def test_historique_visible_a_la_creation_sans_effet():
    visible = [make(r) for r in RAW[:15]]
    w = Wallet.create(MONDAY, SEVEN, visible)
    assert w.notes_capital == 0
    reports = w.settle(NEXT_MONDAY, SEVEN, visible)
    assert reports[0].counted == []  # ces notes ne sont comptées dans aucun bilan


@pytest.mark.requirement("screen-time-wallet/Initialisation du portefeuille")
def test_creation_avec_moins_de_quatre_matieres():
    assert Wallet.create(MONDAY, TWO).weekly_credit == 240


# --- Bilan du lundi ---------------------------------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Bilan du lundi")
def test_credit_hebdomadaire_non_cumulable():
    w = fresh()
    w.settle(NEXT_MONDAY, SEVEN, [])
    assert w.weekly_credit == 228


@pytest.mark.requirement("screen-time-wallet/Bilan du lundi")
def test_capital_cumule():
    w = fresh(SIXTEEN)
    w.notes_capital = 111
    w.settle(NEXT_MONDAY, SIXTEEN, [grade("ENS.INTEG.SC.&TECHNO", 9, 10, "0,5", comment="devoir")])
    assert w.notes_capital == 570


@pytest.mark.requirement("screen-time-wallet/Bilan du lundi")
def test_capital_qui_diminue():
    w = fresh()
    w.notes_capital = 1346
    w.settle(NEXT_MONDAY, SEVEN, AP_FR)
    assert w.notes_capital == 972


@pytest.mark.requirement("screen-time-wallet/Bilan du lundi")
def test_avant_le_lundi_aucun_bilan():
    w = fresh()
    assert w.settle(datetime(2026, 11, 8, 23, 59), SEVEN, AP_FR) == []
    assert w.notes_capital == 0


@pytest.mark.requirement("screen-time-wallet/Bilan du lundi")
def test_bilan_repete_ne_change_rien():
    w = fresh()
    assert len(w.settle(NEXT_MONDAY, SEVEN, AP_FR)) == 1
    snapshot = (w.weekly_credit, w.notes_capital)
    assert w.settle(NEXT_MONDAY, SEVEN, AP_FR) == []
    assert (w.weekly_credit, w.notes_capital) == snapshot


# --- Lundis manqués ----------------------------------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Lundis manqués")
def test_trois_lundis_manques():
    w = fresh()
    reports = w.settle(datetime(2026, 11, 23, 8, 0), SEVEN, AP_FR)
    assert [r.week_credit for r in reports] == [-374, 342, 342]
    assert w.notes_capital == -374 + 2 * 342
    assert w.weekly_credit == 228  # celui d'une seule semaine


# --- Notes de la semaine -------------------------------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Notes de la semaine")
def test_note_fournie_a_deux_releves_successifs():
    w = fresh()
    note = [grade("FRANCAIS", 7)]
    first = w.settle(NEXT_MONDAY, SEVEN, note)
    second = w.settle(datetime(2026, 11, 16), SEVEN, note)
    assert len(first[0].counted) == 1 and second[0].counted == []


@pytest.mark.requirement("screen-time-wallet/Notes de la semaine")
def test_valeur_corrigee_premiere_valeur_conservee():
    w = fresh()
    w.settle(NEXT_MONDAY, SEVEN, [grade("MATHEMATIQUES", 15, comment="n-42")])
    capital = w.notes_capital
    reports = w.settle(datetime(2026, 11, 16), SEVEN, [grade("MATHEMATIQUES", 8, comment="n-42")])
    assert reports[0].counted == []
    assert w.notes_capital == capital + reports[0].week_credit  # semaine sans note : crédit neutre


@pytest.mark.requirement("screen-time-wallet/Notes de la semaine")
def test_deux_notes_proches_distinguees_par_le_commentaire():
    w = fresh()
    attitude = grade("EDUCATION MUSICALE", 7, 10, 1, "Attitude", "2026-10-15")
    participation = grade("EDUCATION MUSICALE", 7, 10, 1, "Participation", "2026-10-15")
    reports = w.settle(NEXT_MONDAY, SEVEN, [attitude, participation])
    assert len(reports[0].counted) == 2


@pytest.mark.requirement("screen-time-wallet/Notes de la semaine")
def test_note_publiee_en_retard_comptee_au_bilan_suivant():
    w = fresh()
    late = grade("FRANCAIS", 7, date="2026-11-01")  # saisie la semaine précédente
    w.settle(NEXT_MONDAY, SEVEN, [])
    reports = w.settle(datetime(2026, 11, 16), SEVEN, [late])
    assert reports[0].counted == [late]


# --- Notes écartées ou signalées --------------------------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Notes écartées ou signalées")
def test_eleve_absent_sans_effet_ni_erreur():
    w = fresh()
    reports = w.settle(NEXT_MONDAY, SEVEN, [grade(value="Abs")])
    assert reports[0].counted == [] and reports[0].rejected == []


@pytest.mark.requirement("screen-time-wallet/Notes écartées ou signalées")
def test_valeur_fournie_apres_coup_comptee_au_bilan_suivant():
    w = fresh()
    w.settle(NEXT_MONDAY, SEVEN, [grade(value="Abs", comment="n-7")])
    reports = w.settle(datetime(2026, 11, 16), SEVEN, [grade(value=15, comment="n-7")])
    assert len(reports[0].counted) == 1


@pytest.mark.requirement("screen-time-wallet/Notes écartées ou signalées")
def test_note_invalide_ne_bloque_pas_le_bilan():
    w = fresh()
    bad, good = grade(value=22, comment="invalide"), grade("FRANCAIS", 7)
    reports = w.settle(NEXT_MONDAY, SEVEN, [bad, good])
    assert reports[0].counted == [good]
    assert [g for g, _ in reports[0].rejected] == [bad]
    assert bad.key not in w.seen_keys


@pytest.mark.requirement("screen-time-wallet/Notes écartées ou signalées")
def test_matiere_inconnue_sans_effet_marquee_vue_et_signalee():
    w = fresh()
    unknown = grade("TECHNOLOGIE", 5)
    reports = w.settle(NEXT_MONDAY, SEVEN, [unknown])
    assert reports[0].counted == [] and reports[0].unknown_subjects == ["TECHNOLOGIE"]
    assert reports[0].week_credit == 342  # comme une semaine sans note
    assert unknown.key in w.seen_keys


# --- Compte rendu du bilan --------------------------------------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Compte rendu du bilan")
def test_compte_rendu_complet():
    w = fresh()
    bad = grade(value=22, comment="invalide")
    unknown = grade("TECHNOLOGIE", 5)
    report = w.settle(NEXT_MONDAY, SEVEN, AP_FR + [bad, unknown])[0]
    assert report.counted == AP_FR
    assert [g for g, _ in report.rejected] == [bad]
    assert report.unknown_subjects == ["TECHNOLOGIE"]
    assert (report.initial_credit, report.week_credit) == (228, -374)
    assert report.monday == NEXT_MONDAY


# --- Consommation -------------------------------------------------------------------------------------------

def with_capital(capital):
    w = fresh()
    w.notes_capital = capital
    return w


@pytest.mark.requirement("screen-time-wallet/Consommation")
def test_consommation_couverte_par_le_credit_hebdomadaire():
    w = with_capital(100)
    w.consume(100)
    assert (w.weekly_credit, w.notes_capital) == (128, 100)


@pytest.mark.requirement("screen-time-wallet/Consommation")
def test_consommation_qui_entame_le_capital():
    w = with_capital(100)
    w.consume(300)
    assert (w.weekly_credit, w.notes_capital) == (0, 28)


@pytest.mark.requirement("screen-time-wallet/Consommation")
def test_capital_qui_devient_negatif():
    w = with_capital(0)
    w.consume(300)
    assert (w.weekly_credit, w.notes_capital) == (0, -72)


@pytest.mark.requirement("screen-time-wallet/Consommation")
@pytest.mark.parametrize("minutes", [0, -5])
def test_consommation_invalide(minutes):
    w = with_capital(100)
    with pytest.raises(InvalidConsumptionError):
        w.consume(minutes)
    assert (w.weekly_credit, w.notes_capital) == (228, 100)
