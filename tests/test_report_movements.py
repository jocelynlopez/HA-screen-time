"""Section des mouvements manuels du rapport hebdomadaire (spec ha-integration, Mouvements manuels dans le rapport)."""

from datetime import datetime

import pytest

from custom_components.screen_time_wallet.engine.config import Config
from custom_components.screen_time_wallet.engine.wallet import Wallet
from custom_components.screen_time_wallet.report import render_report

MONDAY, NEXT_MONDAY = datetime(2026, 11, 2), datetime(2026, 11, 9)


def render(wallet, language="fr"):
    reports = wallet.settle(NEXT_MONDAY, {}, [])
    return render_report(reports, "Mael", Config(), language)[1]


@pytest.mark.requirement("ha-integration/Mouvements manuels dans le rapport")
def test_rapport_avec_mouvements_manuels():
    wallet = Wallet.create(MONDAY, {})
    wallet.adjust(30, datetime(2026, 11, 4, 18, 30), "aide aux devoirs")
    wallet.consume(45, datetime(2026, 11, 5, 20, 5), "jeu console")
    message = render(wallet)
    assert "Mouvements manuels de la semaine :" in message
    assert "• 04/11 18:30 · +30 min · aide aux devoirs" in message
    assert "• 05/11 20:05 · -45 min · jeu console" in message
    assert message.index("aide aux devoirs") < message.index("jeu console")


@pytest.mark.requirement("ha-integration/Mouvements manuels dans le rapport")
def test_mouvement_sans_motif():
    wallet = Wallet.create(MONDAY, {})
    wallet.adjust(15, datetime(2026, 11, 4, 18, 30))
    assert "+15 min · sans motif" in render(wallet)
    wallet = Wallet.create(MONDAY, {})
    wallet.adjust(15, datetime(2026, 11, 4, 18, 30))
    assert "+15 min · no reason" in render(wallet, "en")


@pytest.mark.requirement("ha-integration/Mouvements manuels dans le rapport")
def test_consommation_automatique_par_capteur():
    wallet = Wallet.create(MONDAY, {})
    wallet.consume(312, datetime(2026, 11, 4, 18), "PC de Mael", merge=True)
    message = render(wallet)
    assert "Consommation automatique :" in message and "• PC de Mael : 312 min" in message
    assert "Mouvements manuels" not in message


@pytest.mark.requirement("ha-integration/Mouvements manuels dans le rapport")
def test_aucun_mouvement_pas_de_section():
    message = render(Wallet.create(MONDAY, {}))
    assert "Mouvements manuels" not in message and "Consommation automatique" not in message


@pytest.mark.requirement("screen-time-wallet/Mouvements de la semaine dans le compte rendu")
def test_tous_les_mouvements_sont_listes():
    wallet = Wallet.create(MONDAY, {})
    for minute in range(45):
        wallet.adjust(1, datetime(2026, 11, 4, 8, minute), f"geste {minute}")
    message = render(wallet)
    assert message.count("• 04/11") == 45 and "autre(s)" not in message and "more" not in message
