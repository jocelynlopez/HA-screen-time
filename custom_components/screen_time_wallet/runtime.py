"""Objet d'exécution d'un portefeuille : état, stockage et opérations sérialisées."""

import asyncio
import logging
from datetime import datetime, timedelta

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    MAX_RETRIES,
    OPT_NOTES_ENTITY,
    OPT_NOTIFY_SERVICE,
    OPT_WEEKLY_REPORT,
    RETRY_DELAY_MINUTES,
    SIGNAL_UPDATE,
)
from .ecole_directe_source import EcoleDirecteSource
from .engine.wallet import Report, Wallet
from .options import with_defaults
from .report import render_anomalies, render_report, render_source_down
from .source import GradesSource, NullSource

_LOGGER = logging.getLogger(__name__)


def local_now() -> datetime:
    """Date et heure locales de HA, sans fuseau (le cœur raisonne en heure locale naïve)."""
    return dt_util.now().replace(tzinfo=None)


class WalletRuntime:
    """Détient le portefeuille d'une entrée ; toute modification est sérialisée puis enregistrée."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, store: Store, wallet: Wallet, source_entity: str = ""
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.store = store
        self.wallet = wallet
        self.lock = asyncio.Lock()
        self.source: GradesSource = NullSource()
        self.source_entity = source_entity  # capteur de notes déjà activé (enregistré avec l'état)
        self._retries = 0
        self._cancel_retry = None
        self.configure_source()

    def configure_source(self) -> None:
        """Source choisie dans les options : capteur de notes EcoleDirecte, ou source vide."""
        entity = self.notes_entity
        self.source = EcoleDirecteSource(self.hass, entity) if entity else NullSource()

    @property
    def notes_entity(self) -> str:
        return with_defaults(self.entry.options)[OPT_NOTES_ENTITY]

    @property
    def signal(self) -> str:
        return SIGNAL_UPDATE.format(entry_id=self.entry.entry_id)

    async def async_save(self) -> None:
        await self.store.async_save({**self.wallet.to_dict(), "source_entity": self.source_entity})

    def async_notify_entities(self) -> None:
        async_dispatcher_send(self.hass, self.signal)

    async def async_consume(self, minutes: int, reason: str = "") -> None:
        async with self.lock:
            self.wallet.consume(minutes, local_now(), reason)
            await self.async_save()
        self.async_notify_entities()

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
        return ok

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
        async with self.lock:
            if entity:
                try:
                    data = await self.source.async_fetch()
                except Exception as error:  # noqa: BLE001 - la source est un point d'extension
                    _LOGGER.warning("Activation reportée pour %s : %s", self.entry.title, error)
                    return False
                self.wallet.activate_source(now or local_now(), data.averages, data.notes)
            self.source_entity = entity
            await self.async_save()
        self.async_notify_entities()
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
            reports = self.wallet.settle(now, data.averages, data.notes)
            await self.async_save()
        persistent_notification.async_dismiss(self.hass, self._source_notification_id)
        self.async_notify_entities()
        await self._async_publish(reports)
        if out is not None:
            out.extend(reports)
        return True

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
