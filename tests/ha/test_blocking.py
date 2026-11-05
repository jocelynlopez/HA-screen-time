"""Blocage automatique par interrupteurs quand le temps disponible est épuisé (spec ha-integration)."""

from datetime import datetime
from unittest.mock import patch

import pytest
from homeassistant.exceptions import HomeAssistantError

from conftest import make_entry
from test_settlement import CREATE, MONDAY_9, WEDNESDAY, start, tick
from test_usage_wiring import PC, set_and_wait, set_usage

LOCK = "switch.mael_lock"  # ON = bloqué
ALLOW = "switch.mael_internet"  # OFF = bloqué
DISMISS = "custom_components.screen_time_wallet.runtime.persistent_notification.async_dismiss"


class Switches:
    """Services switch.turn_on / turn_off simulés : ils changent l'état et gardent la trace des appels."""

    def __init__(self, hass, fail=False):
        self.hass, self.fail, self.calls = hass, fail, []
        hass.services.async_register("switch", "turn_on", self._handler("on"))
        hass.services.async_register("switch", "turn_off", self._handler("off"))

    def _handler(self, state):
        async def handle(call):
            entity = call.data["entity_id"]
            self.calls.append((state, entity))
            if self.fail:
                raise HomeAssistantError("api indisponible")
            self.hass.states.async_set(entity, state)

        return handle


async def settled(hass):
    await hass.async_block_till_done(wait_background_tasks=True)


async def started(hass, freezer, lock=(), allow=(), usage=(), weekly_credit=None, states=None):
    options = {"lock_switches": list(lock), "allow_switches": list(allow), "usage_entities": list(usage)}
    entry = make_entry(options=options)
    entry.add_to_hass(hass)
    for entity, state in (states or {}).items():
        hass.states.async_set(entity, state)
    runtime = await start(hass, freezer, entry, when=WEDNESDAY)
    if weekly_credit is not None:
        runtime.wallet.weekly_credit = weekly_credit
    return entry, runtime


# --- Blocage automatique ---------------------------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Blocage automatique")
async def test_temps_epuise_bloque_l_interrupteur_de_verrouillage(hass, freezer):
    switches = Switches(hass)
    entry, runtime = await started(hass, freezer, lock=[LOCK], states={LOCK: "off"}, weekly_credit=5)
    await runtime.async_consume(5)
    await settled(hass)
    assert switches.calls == [("on", LOCK)] and hass.states.get(LOCK).state == "on"


@pytest.mark.requirement("ha-integration/Blocage automatique")
async def test_interrupteur_d_autorisation_coupe_quand_le_temps_est_epuise(hass, freezer):
    switches = Switches(hass)
    entry, runtime = await started(hass, freezer, allow=[ALLOW], states={ALLOW: "on"}, weekly_credit=0)
    await runtime.async_consume(1)
    await settled(hass)
    assert switches.calls == [("off", ALLOW)] and hass.states.get(ALLOW).state == "off"


@pytest.mark.requirement("ha-integration/Blocage automatique")
async def test_temps_rendu_par_un_ajustement_debloque(hass, freezer):
    switches = Switches(hass)
    entry, runtime = await started(hass, freezer, lock=[LOCK], allow=[ALLOW], states={LOCK: "off", ALLOW: "on"},
                                   weekly_credit=0)
    await runtime.async_consume(1)
    await settled(hass)
    assert (hass.states.get(LOCK).state, hass.states.get(ALLOW).state) == ("on", "off")
    await runtime.async_adjust(30)
    await settled(hass)
    assert (hass.states.get(LOCK).state, hass.states.get(ALLOW).state) == ("off", "on")


@pytest.mark.requirement("ha-integration/Blocage automatique")
async def test_recharge_du_lundi_debloque(hass, freezer):
    switches = Switches(hass)
    entry, runtime = await started(hass, freezer, lock=[LOCK], states={LOCK: "on"}, weekly_credit=0)
    await runtime.async_consume(1)  # temps épuisé avant le lundi
    await settled(hass)
    assert runtime.wallet.available < 0 and hass.states.get(LOCK).state == "on"
    runtime.wallet.notes_capital = 0
    await tick(hass, freezer, MONDAY_9)  # bilan : crédit de repli de 240 minutes
    await settled(hass)
    assert runtime.wallet.available > 0 and hass.states.get(LOCK).state == "off"


@pytest.mark.requirement("ha-integration/Blocage automatique")
async def test_deblocage_manuel_annule_au_releve_suivant(hass, freezer):
    switches = Switches(hass)
    set_usage(hass, PC, 0)
    entry, runtime = await started(hass, freezer, lock=[LOCK], usage=[PC], states={LOCK: "off"}, weekly_credit=5)
    await set_and_wait(hass, PC, 5)  # le relevé consomme 5 minutes : temps épuisé
    await settled(hass)
    assert hass.states.get(LOCK).state == "on"
    hass.states.async_set(LOCK, "off")  # le parent débloque à la main sans ajouter de temps
    await set_and_wait(hass, PC, 5)  # relevé identique au précédent : rien à consommer, état imposé quand même
    await settled(hass)
    assert hass.states.get(LOCK).state == "on"
    assert [c[0] for c in switches.calls] == ["on", "on"]  # reverrouillé sans nouvelle consommation


@pytest.mark.requirement("ha-integration/Blocage automatique")
async def test_plusieurs_interrupteurs_en_sens_opposes(hass, freezer):
    switches = Switches(hass)
    entry, runtime = await started(hass, freezer, lock=[LOCK], allow=[ALLOW], states={LOCK: "off", ALLOW: "on"},
                                   weekly_credit=3)
    await runtime.async_consume(3)
    await settled(hass)
    assert sorted(switches.calls) == [("off", ALLOW), ("on", LOCK)]


@pytest.mark.requirement("ha-integration/Blocage automatique")
async def test_interrupteur_deja_dans_l_etat_voulu_non_appele(hass, freezer):
    switches = Switches(hass)
    entry, runtime = await started(hass, freezer, lock=[LOCK], states={LOCK: "off"}, weekly_credit=100)
    await runtime.async_consume(10)  # reste du temps : l'interrupteur est déjà libre
    await settled(hass)
    assert switches.calls == []


@pytest.mark.requirement("ha-integration/Blocage automatique")
@pytest.mark.parametrize("unusable", ["unavailable", "unknown"])
async def test_interrupteur_indisponible_ignore(hass, freezer, unusable):
    switches = Switches(hass)
    entry, runtime = await started(hass, freezer, lock=[LOCK], states={LOCK: unusable}, weekly_credit=2)
    with patch(CREATE) as create:
        await runtime.async_consume(2)
        await settled(hass)
    assert switches.calls == [] and not create.called


@pytest.mark.requirement("ha-integration/Blocage automatique")
async def test_aucun_changement_tant_qu_un_bilan_est_du(hass, freezer):
    switches = Switches(hass)
    entry, runtime = await started(hass, freezer, lock=[LOCK], states={LOCK: "off"}, weekly_credit=0)
    runtime.wallet.last_settlement = datetime(2026, 10, 19)  # bilans dus que la source n'a pas pu faire
    await runtime.async_enforce_blocking()
    assert switches.calls == []


@pytest.mark.requirement("ha-integration/Blocage automatique")
async def test_aucune_liste_aucun_pilotage(hass, freezer):
    switches = Switches(hass)
    entry, runtime = await started(hass, freezer, states={LOCK: "off"}, weekly_credit=0)
    await runtime.async_consume(1)
    await settled(hass)
    assert switches.calls == [] and runtime.blocking_switches == []


# --- Échec du blocage signalé -------------------------------------------------------------------------------------

@pytest.mark.requirement("ha-integration/Échec du blocage signalé")
async def test_echec_notifie_puis_reessaye_au_releve_suivant(hass, freezer):
    switches = Switches(hass, fail=True)
    set_usage(hass, PC, 0)
    entry, runtime = await started(hass, freezer, lock=[LOCK], usage=[PC], states={LOCK: "off"}, weekly_credit=5)
    with patch(CREATE) as create:
        await set_and_wait(hass, PC, 5)
        await settled(hass)
    (args, kwargs), = [(c.args, c.kwargs) for c in create.call_args_list]
    assert LOCK in args[1] and "api indisponible" in args[1] and kwargs["notification_id"].endswith(LOCK)
    assert hass.states.get(LOCK).state == "off"
    switches.fail = False  # l'API répond de nouveau
    with patch(DISMISS) as dismiss:
        await set_and_wait(hass, PC, 5)  # relevé identique, sans consommation
        await settled(hass)
    assert hass.states.get(LOCK).state == "on"
    assert any(LOCK in str(call) for call in dismiss.call_args_list)
    assert len(switches.calls) == 2


@pytest.mark.requirement("ha-integration/Échec du blocage signalé")
async def test_notification_supprimee_quand_l_etat_est_corrige_a_la_main(hass, freezer):
    switches = Switches(hass, fail=True)
    entry, runtime = await started(hass, freezer, lock=[LOCK], states={LOCK: "off"}, weekly_credit=1)
    with patch(CREATE):
        await runtime.async_consume(1)
        await settled(hass)
    hass.states.async_set(LOCK, "on")  # le parent verrouille à la main
    with patch(DISMISS) as dismiss:
        await runtime.async_enforce_blocking()
    assert dismiss.called
