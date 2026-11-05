"""Tests des ajouts au portefeuille : journal, ajustement, état sérialisable, compte rendu détaillé."""

import json
from datetime import datetime

import pytest

from custom_components.screen_time_wallet.engine.config import Config
from custom_components.screen_time_wallet.engine.grades import Grade
from custom_components.screen_time_wallet.engine.wallet import (
    InvalidAdjustmentError,
    Movement,
    Wallet,
    WalletStateError,
)

SEVEN = {
    "ANGLAIS LV1": "13.85", "ARTS PLASTIQUES": "17", "EDUCATION MUSICALE": "16",
    "ENS.INTEG.SC.&TECHNO": "18", "FRANCAIS": "10.67", "HISTOIRE-GEOGRAPHIE": "17.43",
    "MATHEMATIQUES": "19.34", "ED PHYSIQUE & SPORT": "",
}
TWO = {"MATHEMATIQUES": 15, "FRANCAIS": 14}
MONDAY = datetime(2026, 11, 2)
NEXT_MONDAY = datetime(2026, 11, 9)


def grade(subject, value, scale=20, coefficient=1, comment="contrôle"):
    return Grade("2026-11-04", subject, comment, value, scale, coefficient)


AP_FR = [grade("ARTS PLASTIQUES", 9, 10, "0,5", "Lotoportrait"), grade("FRANCAIS", 7, comment="Sommative")]


def fresh(averages=SEVEN):
    return Wallet.create(MONDAY, averages)


# --- Journal des mouvements ---------------------------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Journal des mouvements")
def test_bilan_journalise():
    # Huit moyennes à 15,6333 : crédit initial 218 ; un contrôle de maths à 13,2333/20 : crédit de semaine +111.
    averages = {m: "15.6333333" for m in Config().subject_multipliers}
    wallet = Wallet(weekly_credit=228, notes_capital=0, last_settlement=MONDAY)
    wallet.settle(NEXT_MONDAY, averages, [grade("MATHEMATIQUES", "13.2333")])
    assert wallet.movements[-1] == Movement("bilan", NEXT_MONDAY, -10, 111, "")


@pytest.mark.requirement("screen-time-wallet/Journal des mouvements")
def test_consommation_journalisee():
    wallet, now = fresh(), datetime(2026, 11, 4, 20, 0)
    wallet.consume(45, now, "jeu console")
    assert wallet.movements[-1] == Movement("consommation", now, -45, 0, "jeu console")


@pytest.mark.requirement("screen-time-wallet/Journal des mouvements")
def test_journal_borne_a_200_mouvements():
    wallet = fresh()
    for i in range(250):
        wallet.consume(1, reason=str(i))
    assert len(wallet.movements) == 200
    assert wallet.movements[0].reason == "50" and wallet.movements[-1].reason == "249"


# --- Regroupement des consommations automatiques ----------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Regroupement des consommations automatiques")
def test_trois_releves_dans_la_journee():
    wallet = fresh()
    for minutes, hour in ((5, 9), (3, 12), (7, 18)):
        wallet.consume(minutes, datetime(2026, 11, 4, hour), "PC de Mael", merge=True)
    assert len(wallet.movements) == 1
    assert wallet.movements[0] == Movement("consommation", datetime(2026, 11, 4, 18), -15, 0, "PC de Mael")
    assert wallet.weekly_credit == 213


@pytest.mark.requirement("screen-time-wallet/Regroupement des consommations automatiques")
def test_regroupement_a_cheval_sur_le_credit_et_le_capital():
    wallet = Wallet(weekly_credit=10, notes_capital=0, last_settlement=MONDAY)
    wallet.consume(8, datetime(2026, 11, 4, 9), "PC", merge=True)
    wallet.consume(7, datetime(2026, 11, 4, 10), "PC", merge=True)
    assert len(wallet.movements) == 1
    assert (wallet.movements[0].weekly_change, wallet.movements[0].capital_change) == (-10, -5)
    assert (wallet.weekly_credit, wallet.notes_capital) == (0, -5)


@pytest.mark.requirement("screen-time-wallet/Regroupement des consommations automatiques")
def test_jour_different_nouveau_mouvement():
    wallet = fresh()
    wallet.consume(5, datetime(2026, 11, 4, 22), "PC", merge=True)
    wallet.consume(5, datetime(2026, 11, 5, 8), "PC", merge=True)
    assert len(wallet.movements) == 2


@pytest.mark.requirement("screen-time-wallet/Regroupement des consommations automatiques")
def test_motif_different_nouveau_mouvement():
    wallet = fresh()
    wallet.consume(5, datetime(2026, 11, 4, 9), "PC", merge=True)
    wallet.consume(5, datetime(2026, 11, 4, 10), "Tablette", merge=True)
    assert [m.reason for m in wallet.movements] == ["PC", "Tablette"]


@pytest.mark.requirement("screen-time-wallet/Regroupement des consommations automatiques")
def test_consommation_manuelle_a_son_propre_mouvement():
    wallet = fresh()
    wallet.consume(5, datetime(2026, 11, 4, 9), "PC", merge=True)
    wallet.consume(10, datetime(2026, 11, 4, 10), "PC")
    assert [m.weekly_change for m in wallet.movements] == [-5, -10]


@pytest.mark.requirement("screen-time-wallet/Regroupement des consommations automatiques")
def test_apres_un_autre_mouvement_nouveau_mouvement():
    wallet = fresh()
    wallet.consume(5, datetime(2026, 11, 4, 9), "PC", merge=True)
    wallet.adjust(10, datetime(2026, 11, 4, 10), "bonus")
    wallet.consume(5, datetime(2026, 11, 4, 11), "PC", merge=True)
    assert [m.kind for m in wallet.movements] == ["consommation", "ajustement", "consommation"]


# --- Ajustement manuel -----------------------------------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Ajustement manuel")
def test_ajustement_positif():
    wallet = fresh()
    wallet.notes_capital = 100
    wallet.adjust(30, MONDAY, "aide aux devoirs")
    assert (wallet.notes_capital, wallet.weekly_credit) == (130, 228)
    assert wallet.movements[-1] == Movement("ajustement", MONDAY, 0, 30, "aide aux devoirs")


@pytest.mark.requirement("screen-time-wallet/Ajustement manuel")
def test_ajustement_negatif():
    wallet = fresh()
    wallet.notes_capital = 20
    wallet.adjust(-50)
    assert wallet.notes_capital == -30


@pytest.mark.requirement("screen-time-wallet/Ajustement manuel")
@pytest.mark.parametrize("minutes", [0, 1.5, True])
def test_ajustement_invalide(minutes):
    wallet = fresh()
    with pytest.raises(InvalidAdjustmentError):
        wallet.adjust(minutes)
    assert (wallet.weekly_credit, wallet.notes_capital, wallet.movements) == (228, 0, [])


# --- État sérialisable ---------------------------------------------------------------------------------

def used_wallet():
    wallet = fresh()
    wallet.settle(NEXT_MONDAY, SEVEN, AP_FR)
    wallet.consume(45, NEXT_MONDAY, "jeu console")
    wallet.adjust(30, NEXT_MONDAY, "bonus")
    return wallet


@pytest.mark.requirement("screen-time-wallet/État sérialisable")
def test_aller_retour():
    wallet = used_wallet()
    restored = Wallet.from_dict(json.loads(json.dumps(wallet.to_dict())))
    assert restored.weekly_credit == wallet.weekly_credit
    assert restored.notes_capital == wallet.notes_capital
    assert restored.last_settlement == wallet.last_settlement
    assert restored.seen_keys == wallet.seen_keys
    assert restored.movements == wallet.movements


@pytest.mark.requirement("screen-time-wallet/État sérialisable")
def test_notes_deja_vues_conservees_apres_restauration():
    restored = Wallet.from_dict(json.loads(json.dumps(used_wallet().to_dict())))
    reports = restored.settle(datetime(2026, 11, 16), SEVEN, AP_FR)
    assert reports[0].counted == []


@pytest.mark.requirement("screen-time-wallet/État sérialisable")
@pytest.mark.parametrize("data", [{"version": 99}, {}, {"version": 1}, None])
def test_etat_de_version_inconnue_ou_illisible(data):
    with pytest.raises(WalletStateError):
        Wallet.from_dict(data)


# --- Compte rendu du bilan (éléments du calcul) -----------------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Compte rendu du bilan")
def test_elements_du_calcul():
    report = fresh().settle(NEXT_MONDAY, SEVEN, AP_FR)[0]
    assert report.subjects_count == 7
    assert float(report.general_average) == pytest.approx(15.80, abs=0.005)
    assert float(report.week_weight) == 3.25
    assert float(report.week_average) == pytest.approx(7.85, abs=0.005)
    assert (report.initial_credit, report.week_credit) == (228, -374)
    assert (report.notes_capital, report.available) == (-374, -146)
    assert report.fallback is False


@pytest.mark.requirement("screen-time-wallet/Compte rendu du bilan")
def test_credit_de_repli_dans_le_compte_rendu():
    report = Wallet.create(MONDAY, TWO).settle(NEXT_MONDAY, TWO, AP_FR)[0]
    assert report.fallback is True
    assert report.general_average is None and report.week_average is None
    assert report.week_credit == 0 and report.initial_credit == 240


# --- Activation d'une source ---------------------------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Activation d'une source")
def test_notes_visibles_memorisees_a_l_activation():
    from real_notes import RAW, make

    visible = [make(r) for r in RAW]
    wallet = Wallet.create(MONDAY, {})  # sans source
    wallet.activate_source(datetime(2026, 11, 4), SEVEN, visible)
    reports = wallet.settle(NEXT_MONDAY, SEVEN, visible)
    assert len(visible) == 18 and reports[0].counted == []


@pytest.mark.requirement("screen-time-wallet/Activation d'une source")
def test_credit_hebdomadaire_remplace_capital_inchange():
    wallet = Wallet.create(MONDAY, {})
    wallet.notes_capital = 100
    now = datetime(2026, 11, 4)
    wallet.activate_source(now, SEVEN, [])
    assert (wallet.weekly_credit, wallet.notes_capital) == (228, 100)
    assert wallet.last_settlement == MONDAY
    assert wallet.movements[-1] == Movement("initialisation", now, -12, 0, "")
    assert wallet.movements[-1].detail == {"initial_credit": 228}


@pytest.mark.requirement("screen-time-wallet/Activation d'une source")
def test_activation_avec_moins_de_quatre_matieres():
    wallet = Wallet.create(MONDAY, {})
    wallet.activate_source(datetime(2026, 11, 4), TWO, [])
    assert wallet.weekly_credit == 240
