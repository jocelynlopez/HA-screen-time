"""Objet d'exécution d'un portefeuille : état, stockage et opérations sérialisées."""

import asyncio
import logging
from datetime import datetime, timedelta

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_state_report_event,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    MAX_REPORTS,
    MAX_RETRIES,
    OPT_ALLOW_SWITCHES,
    OPT_LOCK_SWITCHES,
    OPT_MULTIPLIERS,
    OPT_NOTES_ENTITY,
    OPT_NOTIFY_SERVICE,
    OPT_USAGE_ENTITIES,
    OPT_WEEKLY_REPORT,
    RETRY_DELAY_MINUTES,
    SIGNAL_UPDATE,
)
from .ecole_directe_source import EcoleDirecteSource
from .engine.usage import Baseline, consumed_since, reading_minutes
from .engine.wallet import Report, Wallet, monday_midnight
from .options import build_config, with_defaults
from .report import (
    render_anomalies,
    render_blocking_failed,
    render_forecast,
    render_forecast_unavailable,
    render_report,
    render_source_down,
    render_subjects_added,
)
from .source import GradesSource, NullSource, SourceData

_LOGGER = logging.getLogger(__name__)


def local_now() -> datetime:
    """Date et heure locales de HA, sans fuseau (le cœur raisonne en heure locale naïve)."""
    return dt_util.now().replace(tzinfo=None)


class NoSourceError(Exception):
    """Aucun capteur de notes n'est choisi dans les options."""


class WalletRuntime:
    """Détient le portefeuille d'une entrée ; toute modification est sérialisée puis enregistrée."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        store: Store,
        wallet: Wallet,
        source_entity: str = "",
        baselines: dict[str, Baseline] | None = None,
        reports: list[dict] | None = None,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.store = store
        self.wallet = wallet
        self.lock = asyncio.Lock()
        self.source: GradesSource = NullSource()
        self.source_entity = source_entity  # capteur de notes déjà activé (enregistré avec l'état)
        self.baselines: dict[str, Baseline] = dict(baselines or {})  # relevé de référence de chaque capteur
        self.reports: list[dict] = list(reports or [])  # rapports du lundi : monday, title, message
        self.forecast_text = ""  # prévision du prochain bilan, jamais enregistrée
        self._forecast_generation = 0
        self._retries = 0
        self._cancel_retry = None
        self._own_options_update = False  # mise à jour des options faite par le runtime : pas de rechargement
        self._blocking_lock = asyncio.Lock()  # sérialise les basculements d'interrupteurs
        self._blocking_task: asyncio.Task | None = None
        self._blocking_requested = False
        self._blocking_failed: set[str] = set()  # interrupteurs dont le dernier basculement a échoué
        self.configure_source()

    def configure_source(self) -> None:
        """Source choisie dans les options : capteur de notes EcoleDirecte, ou source vide."""
        entity = self.notes_entity
        self.source = EcoleDirecteSource(self.hass, entity) if entity else NullSource()

    @property
    def notes_entity(self) -> str:
        return with_defaults(self.entry.options)[OPT_NOTES_ENTITY]

    def consume_own_options_update(self) -> bool:
        """Vrai (une seule fois) si la dernière mise à jour des options vient du runtime lui-même."""
        own, self._own_options_update = self._own_options_update, False
        return own

    @property
    def usage_entities(self) -> list[str]:
        return with_defaults(self.entry.options)[OPT_USAGE_ENTITIES]

    @property
    def blocking_switches(self) -> list[tuple[str, bool]]:
        """Interrupteurs pilotés, avec « vrai » quand l'état ON signifie bloqué."""
        options = with_defaults(self.entry.options)
        return [(e, True) for e in options[OPT_LOCK_SWITCHES]] + [(e, False) for e in options[OPT_ALLOW_SWITCHES]]

    @property
    def signal(self) -> str:
        return SIGNAL_UPDATE.format(entry_id=self.entry.entry_id)

    async def async_save(self) -> None:
        await self.store.async_save(
            {
                **self.wallet.to_dict(),
                "source_entity": self.source_entity,
                "usage_baselines": {entity: b.to_json() for entity, b in self.baselines.items()},
                "reports": self.reports,
            }
        )

    def async_notify_entities(self) -> None:
        async_dispatcher_send(self.hass, self.signal)
        self.async_schedule_blocking()  # le temps disponible a pu changer
        self.async_schedule_forecast()

    async def async_consume(self, minutes: int, reason: str = "") -> None:
        async with self.lock:
            self.wallet.consume(minutes, local_now(), reason)
            await self.async_save()
        self.async_notify_entities()

    async def async_recount_week(self) -> int:
        """Rend à compter au prochain bilan les notes de la semaine en cours ; renvoie leur nombre.

        Si la source est inaccessible, l'appel est refusé (ServiceValidationError) et rien n'est modifié."""
        try:
            data = await self.source.async_fetch()
        except Exception as error:  # noqa: BLE001 - la source est un point d'extension
            raise ServiceValidationError(f"Source des notes inaccessible : {error}") from error
        async with self.lock:
            count = self.wallet.recount_week(local_now(), data.notes)
            if count:
                await self.async_save()
        if count:
            self.async_notify_entities()
        return count

    async def async_adjust(self, minutes: int, reason: str = "") -> None:
        async with self.lock:
            self.wallet.adjust(minutes, local_now(), reason)
            await self.async_save()
        self.async_notify_entities()

    @property
    def _source_notification_id(self) -> str:
        return f"{DOMAIN}_{self.entry.entry_id}_source"

    def _notify_source_down(self, error: object) -> None:
        title, message = render_source_down(
            self.entry.title, self.notes_entity, str(error), self.hass.config.language
        )
        persistent_notification.async_create(
            self.hass, message, title=title, notification_id=self._source_notification_id
        )

    async def async_refresh(self, now: datetime | None = None) -> bool:
        """Active la source si besoin, puis effectue les bilans dus. Renvoie False si la source a échoué ;
        une nouvelle tentative est alors planifiée (3 au plus, remises à zéro par le déclencheur quotidien)."""
        now = now or local_now()
        ok = await self.async_activate(now)
        if ok:
            ok = await self._async_settle(now)
        elif self.wallet.pending_settlements(now) > 0:
            self._notify_source_down("source indisponible")
        if ok:
            self.async_cancel_retry()
            self._retries = 0
        else:
            self._schedule_retry()
        await self.async_sync_usage()  # après le bilan : l'usage d'un lundi manqué ne doit pas être effacé par lui
        return ok

    @callback
    def async_track_usage(self):
        """Suit les changements d'état des capteurs de temps d'écran choisis ; renvoie la fonction d'arrêt."""
        entities = self.usage_entities
        if not entities:
            return lambda: None

        async def _changed(event: Event) -> None:
            await self.async_sync_usage(event.data["entity_id"])

        # un relevé identique au précédent ne change pas l'état : il est signalé par l'événement « rapporté »
        unsubscribe_changes = async_track_state_change_event(self.hass, entities, _changed)
        unsubscribe_reports = async_track_state_report_event(self.hass, entities, _changed)

        def _unsubscribe() -> None:
            unsubscribe_changes()
            unsubscribe_reports()

        return _unsubscribe

    def _read_usage(self, entity: str):
        """(minutes, jour, nom) du capteur, ou None s'il est absent, indisponible ou inconnu."""
        state = self.hass.states.get(entity)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return None
        minutes = reading_minutes(state.state, state.attributes.get("total_seconds"))
        return minutes, state.attributes.get("date"), state.attributes.get("friendly_name") or entity

    async def async_sync_usage(self, only: str | None = None) -> None:
        """Consomme la différence de chaque capteur choisi (ou du seul `only`) depuis son relevé de référence.

        Les références des capteurs retirés des options sont oubliées. Rien n'est consommé tant qu'un bilan est dû."""
        now = local_now()
        async with self.lock:
            entities = self.usage_entities
            changed = False
            for stale in set(self.baselines) - set(entities):
                del self.baselines[stale]
                changed = True
            if self.wallet.pending_settlements(now) == 0:
                for entity in entities:
                    reading = self._read_usage(entity) if only in (None, entity) else None
                    if reading is None:
                        continue
                    minutes, day, name = reading
                    previous = self.baselines.get(entity)
                    consumed, baseline = consumed_since(previous, minutes, day)
                    if baseline is not None and baseline != previous:
                        self.baselines[entity] = baseline
                        changed = True
                    if consumed > 0:
                        self.wallet.consume(consumed, now, name, merge=True)
                        changed = True
            if changed:
                await self.async_save()
        if changed:
            self.async_notify_entities()  # demande aussi la remise en accord des interrupteurs
        else:
            self.async_schedule_blocking()  # à chaque relevé, même sans consommation : l'état est imposé

    def reset_retries(self) -> None:
        self._retries = 0

    def async_cancel_retry(self) -> None:
        if self._cancel_retry:
            self._cancel_retry()
            self._cancel_retry = None

    def _schedule_retry(self) -> None:
        self.async_cancel_retry()
        if self._retries >= MAX_RETRIES:
            return
        self._retries += 1

        async def _retry(_now) -> None:
            self._cancel_retry = None
            await self.async_refresh()

        self._cancel_retry = async_call_later(self.hass, timedelta(minutes=RETRY_DELAY_MINUTES), _retry)

    async def async_activate(self, now: datetime | None = None) -> bool:
        """Active le capteur de notes choisi s'il diffère de celui déjà activé. Renvoie False si la source échoue."""
        entity = self.notes_entity
        if entity == self.source_entity:
            return True
        added: list[str] = []
        async with self.lock:
            if entity:
                try:
                    data = await self.source.async_fetch()
                except Exception as error:  # noqa: BLE001 - la source est un point d'extension
                    _LOGGER.warning("Activation reportée pour %s : %s", self.entry.title, error)
                    return False
                added = self._adopt_subjects(data)
                self.wallet.activate_source(now or local_now(), data.averages, data.notes)
            self.source_entity = entity
            await self.async_save()
        self.async_notify_entities()
        await self._async_publish_subjects(added)
        return True

    async def async_settle(self, now: datetime | None = None) -> list[Report]:
        """Bilan des lundis écoulés ; renvoie les comptes rendus (vide si rien n'est dû ou si la source échoue)."""
        reports = []
        await self._async_settle(now or local_now(), reports)
        return reports

    async def _async_settle(self, now: datetime, out: list[Report] | None = None) -> bool:
        """Effectue les bilans dus. Si la source échoue, rien ne change : notification et nouvelle tentative."""
        async with self.lock:
            if self.wallet.pending_settlements(now) == 0:
                return True
            try:
                data = await self.source.async_fetch()
            except Exception as error:  # noqa: BLE001 - la source est un point d'extension
                _LOGGER.warning("Bilan reporté pour %s : source indisponible (%s)", self.entry.title, error)
                self._notify_source_down(error)
                return False
            added = self._adopt_subjects(data)
            reports = self.wallet.settle(now, data.averages, data.notes)
            self._keep_reports(reports)
            await self.async_save()
        persistent_notification.async_dismiss(self.hass, self._source_notification_id)
        self.async_notify_entities()
        await self._async_publish_subjects(added)
        await self._async_publish(reports)
        if out is not None:
            out.extend(reports)
        return True

    def _keep_reports(self, reports: list[Report]) -> None:
        """Ajoute chaque rapport du lundi à l'historique (52 au plus), qu'il soit notifié ou non."""
        language, name, config = self.hass.config.language, self.entry.title, self.wallet.config
        for report in reports:
            title, message = render_report([report], name, config, language)
            self.reports.append({"monday": report.monday.isoformat(), "title": title, "message": message})
        del self.reports[:-MAX_REPORTS]

    @callback
    def async_schedule_forecast(self) -> None:
        """Recalcule la prévision en tâche de fond ; un calcul plus récent remplace celui qui est en cours."""
        self._forecast_generation += 1
        self.entry.async_create_background_task(
            self.hass, self._async_forecast(self._forecast_generation), f"{DOMAIN}_forecast_{self.entry.entry_id}"
        )

    async def _async_forecast(self, generation: int) -> None:
        now = local_now()
        try:
            data = await self.source.async_fetch()
        except Exception:  # noqa: BLE001 - la source est un point d'extension ; le bilan réel signale l'erreur
            data = None
        if generation != self._forecast_generation:
            return
        language, config = self.hass.config.language, self.wallet.config
        if data is not None:
            text = render_forecast(self.wallet.forecast(now, data.averages, data.notes), config, language)
        else:
            monday = monday_midnight(now) + timedelta(weeks=1)
            manual, automatic = self.wallet.week_movements(monday)
            text = render_forecast_unavailable(Report(monday, 0, 0, manual=manual, automatic=automatic), language)
        if text != self.forecast_text:
            self.forecast_text = text
            async_dispatcher_send(self.hass, self.signal)

    @callback
    def async_track_notes(self):
        """Recalcule la prévision quand le capteur de notes change ; renvoie la fonction d'arrêt."""
        entity = self.notes_entity
        if not entity:
            return lambda: None

        async def _changed(_event: Event) -> None:
            self.async_schedule_forecast()

        return async_track_state_change_event(self.hass, [entity], _changed)

    @callback
    def async_schedule_blocking(self) -> None:
        """Demande de remettre les interrupteurs en accord avec le temps disponible, en tâche de fond.

        Le basculement peut durer une minute (Family Safety) : il n'attend jamais le verrou du portefeuille.
        Les demandes rapprochées sont regroupées."""
        if not self.blocking_switches:
            return
        self._blocking_requested = True
        if self._blocking_task is not None and not self._blocking_task.done():
            return
        self._blocking_task = self.entry.async_create_background_task(
            self.hass, self._async_blocking_loop(), f"{DOMAIN}_blocking_{self.entry.entry_id}"
        )

    async def _async_blocking_loop(self) -> None:
        while self._blocking_requested:
            self._blocking_requested = False
            await self.async_enforce_blocking()

    async def async_enforce_blocking(self) -> None:
        """Bloque les interrupteurs choisis quand le temps disponible est ≤ 0, les libère sinon.

        Ne change rien tant qu'un bilan est dû. Un interrupteur déjà dans l'état voulu, indisponible ou inconnu
        n'est pas appelé ; un basculement en échec est signalé et sera réessayé."""
        switches = self.blocking_switches
        if not switches:
            return
        async with self._blocking_lock:
            if self.wallet.pending_settlements(local_now()) > 0:
                return
            blocked = self.wallet.available <= 0
            for entity, on_means_blocked in switches:
                await self._async_set_switch(entity, want_on=(on_means_blocked == blocked))

    async def _async_set_switch(self, entity: str, want_on: bool) -> None:
        state = self.hass.states.get(entity)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return
        if (state.state == STATE_ON) == want_on:
            self._dismiss_blocking_failure(entity)
            return
        try:
            await self.hass.services.async_call(
                "switch", "turn_on" if want_on else "turn_off", {"entity_id": entity}, blocking=True
            )
        except Exception as error:  # noqa: BLE001 - le service appartient à une autre intégration
            _LOGGER.warning("Basculement de %s impossible pour %s : %s", entity, self.entry.title, error)
            self._blocking_failed.add(entity)
            title, message = render_blocking_failed(self.entry.title, entity, str(error), self.hass.config.language)
            persistent_notification.async_create(
                self.hass, message, title=title, notification_id=self._blocking_notification_id(entity)
            )
        else:
            self._dismiss_blocking_failure(entity)

    def _blocking_notification_id(self, entity: str) -> str:
        return f"{DOMAIN}_{self.entry.entry_id}_blocking_{entity}"

    def _dismiss_blocking_failure(self, entity: str) -> None:
        if entity in self._blocking_failed:
            self._blocking_failed.discard(entity)
            persistent_notification.async_dismiss(self.hass, self._blocking_notification_id(entity))

    def _adopt_subjects(self, data: SourceData) -> list[str]:
        """Ajoute à la table des options, avec le multiplicateur 1, les matières de la source qui n'y sont pas.

        La configuration du portefeuille est reconstruite pour le calcul en cours ; les options sont enregistrées
        sans recharger l'entrée. À appeler sous le verrou. Renvoie les matières ajoutées."""
        added = [name for name in data.all_subjects if not self.wallet.config.is_known(name)]
        if not added:
            return []
        table = {**with_defaults(self.entry.options)[OPT_MULTIPLIERS], **{name: 1 for name in added}}
        options = {**self.entry.options, OPT_MULTIPLIERS: table}
        self.wallet.config = build_config(options)
        self._own_options_update = True
        if not self.hass.config_entries.async_update_entry(self.entry, options=options):
            self._own_options_update = False
        return added

    async def async_detect_subjects(self) -> list[str]:
        """Détection à la demande : ajoute les matières de la source absentes de la table (sans notification).

        Lève NoSourceError s'il n'y a pas de capteur de notes, ou l'erreur de la source si elle est indisponible."""
        if not self.notes_entity:
            raise NoSourceError
        async with self.lock:
            data = await self.source.async_fetch()
            return self._adopt_subjects(data)

    async def _async_publish_subjects(self, added: list[str]) -> None:
        """Notification persistante (et service notify) des matières ajoutées automatiquement."""
        if not added:
            return
        table = with_defaults(self.entry.options)[OPT_MULTIPLIERS]  # déjà mise à jour par _adopt_subjects
        title, message = render_subjects_added(self.entry.title, added, table, self.hass.config.language)
        persistent_notification.async_create(
            self.hass, message, title=title, notification_id=f"{DOMAIN}_{self.entry.entry_id}_subjects"
        )
        await self._async_notify(with_defaults(self.entry.options)[OPT_NOTIFY_SERVICE], title, message)

    async def _async_publish(self, reports: list[Report]) -> None:
        """Notification d'anomalie et rapport hebdomadaire (persistants, plus service notify optionnel)."""
        options = with_defaults(self.entry.options)
        language, name, config = self.hass.config.language, self.entry.title, self.wallet.config
        messages = []
        anomalies = render_anomalies(reports, name, language)
        if anomalies:
            messages.append(("anomalies", *anomalies))
        if options[OPT_WEEKLY_REPORT] and reports:
            messages.append(("report", *render_report(reports, name, config, language)))
        for kind, title, message in messages:
            persistent_notification.async_create(
                self.hass, message, title=title, notification_id=f"{DOMAIN}_{self.entry.entry_id}_{kind}"
            )
            await self._async_notify(options[OPT_NOTIFY_SERVICE], title, message)

    async def _async_notify(self, service: str, title: str, message: str) -> None:
        if not service:
            return
        domain, _, name = service.partition(".")
        try:
            await self.hass.services.async_call(domain, name, {"title": title, "message": message}, blocking=False)
        except HomeAssistantError as error:
            _LOGGER.warning("Service de notification %s indisponible : %s", service, error)
