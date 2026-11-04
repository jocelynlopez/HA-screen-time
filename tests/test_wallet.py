"""Tests de la spec screen-time-wallet. Chaque test déclare l'exigence qu'il vérifie."""

from datetime import date, datetime
from fractions import Fraction

import pytest

from portefeuille_minutes.config import Config
from portefeuille_minutes.grades import Grade, InvalidGradeError
from portefeuille_minutes.wallet import Wallet

LUNDI = datetime(2026, 11, 2)  # lundi 2 novembre 2026, 00h00


def grade(id="n-1", subject="maths", value=15, scale=20, coefficient=1):
    return Grade(id, subject, date(2026, 11, 4), value, scale, coefficient)


def wallet_with(balance):
    w = Wallet.create(LUNDI)
    w.balance = balance
    return w


# --- Solde en minutes entières ------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Solde en minutes entières")
def test_solde_negatif_autorise():
    # Config réglée pour obtenir exactement -50 min : 10 min/point × 1 × (7 − 12)
    config = Config(base_rate=Fraction(10), subject_multipliers={"maths": Fraction(1)})
    w = Wallet(balance=10, last_allocation=LUNDI, config=config)
    w.apply_grade(grade(value=7))
    assert w.balance == -40
    assert isinstance(w.balance, int)


# --- Allocation à la création -------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Allocation à la création")
def test_creation_en_milieu_de_semaine():
    assert Wallet.create(datetime(2026, 11, 4, 15, 30)).balance == 240  # mercredi


# --- Allocation hebdomadaire --------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Allocation hebdomadaire")
def test_passage_au_lundi():
    w = Wallet.create(LUNDI)
    assert w.update(datetime(2026, 11, 9, 0, 0)) == 240
    assert w.balance == 480


@pytest.mark.requirement("screen-time-wallet/Allocation hebdomadaire")
def test_avant_le_lundi():
    w = Wallet.create(LUNDI)
    assert w.update(datetime(2026, 11, 8, 23, 59)) == 0
    assert w.balance == 240


@pytest.mark.requirement("screen-time-wallet/Allocation hebdomadaire")
def test_plusieurs_semaines_manquees():
    w = Wallet.create(LUNDI)
    assert w.update(datetime(2026, 11, 23, 8, 0)) == 3 * 240
    assert w.balance == 4 * 240


@pytest.mark.requirement("screen-time-wallet/Allocation hebdomadaire")
def test_mise_a_jour_repetee():
    w = Wallet.create(LUNDI)
    w.update(datetime(2026, 11, 9, 10, 0))
    assert w.update(datetime(2026, 11, 9, 10, 0)) == 0
    assert w.balance == 480


# --- Report du solde ----------------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Report du solde")
def test_report_positif():
    w = wallet_with(100)
    w.update(datetime(2026, 11, 9))
    assert w.balance == 340


@pytest.mark.requirement("screen-time-wallet/Report du solde")
def test_report_negatif():
    w = wallet_with(-100)
    w.update(datetime(2026, 11, 9))
    assert w.balance == 140


# --- Application d'une note au solde -------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Application d'une note au solde")
def test_note_creditante():
    w = wallet_with(240)
    w.apply_grade(grade(value=15))
    assert w.balance == 375


@pytest.mark.requirement("screen-time-wallet/Application d'une note au solde")
def test_note_debitante():
    w = wallet_with(240)
    w.apply_grade(grade(subject="français", value=8))
    assert w.balance == 0


@pytest.mark.requirement("screen-time-wallet/Application d'une note au solde")
def test_note_sans_effet():
    w = wallet_with(240)
    w.apply_grade(grade(subject="technologie", value=5))
    assert w.balance == 240


# --- Pas de double traitement d'une note ---------------------------------------

@pytest.mark.requirement("screen-time-wallet/Pas de double traitement d'une note")
def test_note_recue_deux_fois():
    w = wallet_with(240)
    w.apply_grade(grade("n-42", value=15))
    w.apply_grade(grade("n-42", value=15))
    assert w.balance == 375


@pytest.mark.requirement("screen-time-wallet/Pas de double traitement d'une note")
def test_meme_identifiant_valeur_differente():
    w = wallet_with(240)
    w.apply_grade(grade("n-42", value=15))
    w.apply_grade(grade("n-42", subject="maths", value=8))
    assert w.balance == 375


# --- Note non numérique ignorée --------------------------------------------------

@pytest.mark.requirement("screen-time-wallet/Note non numérique ignorée")
@pytest.mark.parametrize("value", ["Abs", "Disp", "NE", "", None])
def test_eleve_absent(value):
    w = wallet_with(240)
    assert w.apply_grade(grade(value=value)) == 0
    assert w.balance == 240


@pytest.mark.requirement("screen-time-wallet/Note non numérique ignorée")
def test_valeur_fournie_apres_coup():
    w = wallet_with(240)
    w.apply_grade(grade("n-7", value="Abs"))
    w.apply_grade(grade("n-7", value=15))
    assert w.balance == 240 + 135


# --- Rejet atomique d'une note invalide -----------------------------------------

@pytest.mark.requirement("screen-time-wallet/Rejet atomique d'une note invalide")
def test_note_invalide_ne_change_rien():
    w = wallet_with(240)
    with pytest.raises(InvalidGradeError):
        w.apply_grade(grade("n-9", value=22))
    assert w.balance == 240
    assert "n-9" not in w.processed_ids
