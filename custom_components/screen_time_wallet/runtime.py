"""Objet d'exécution d'un portefeuille : état, stockage et opérations sérialisées."""

import asyncio
import logging
from datetime import datetime

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, OPT_NOTIFY_SERVICE, OPT_WEEKLY_REPORT, SIGNAL_UPDATE
from .engine.wallet import Report, Wallet
from .options import with_defaults
from .report import render_anomalies, render_report
from .source import GradesSource, NullSource

_LOGGER = logging.getLogger(__name__)


def local_now() -> datetime:
    """Date et heure locales de HA, sans fuseau (le cœur raisonne en heure locale naïve)."""
    return dt_util.now().replace(tzinfo=None)


class WalletRuntime:
    """Détient le portefeuille d'une entrée ; toute modification est sérialisée puis enregistrée."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, store: Store, wallet: Wallet) -> None:
        self.hass = hass
        self.entry = entry
        self.store = store
        self.wallet = wallet
        self.lock = asyncio.Lock()
        self.source: GradesSource = NullSource()

    @property
    def signal(self) -> str:
        return SIGNAL_UPDATE.format(entry_id=self.entry.entry_id)

    async def async_save(self) -> None:
        await self.store.async_save(self.wallet.to_dict())

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

    async def async_settle(self, now: datetime | None = None) -> list[Report]:
        """Bilan des lundis écoulés. Si la source échoue, rien ne change et le bilan sera retenté."""
        async with self.lock:
            now = now or local_now()
            if self.wallet.pending_settlements(now) == 0:
                return []
            try:
                data = await self.source.async_fetch()
            except Exception as error:  # noqa: BLE001 - la source est un point d'extension
                _LOGGER.warning("Bilan reporté pour %s : source indisponible (%s)", self.entry.title, error)
                return []
            reports = self.wallet.settle(now, data.averages, data.notes)
            await self.async_save()
        self.async_notify_entities()
        await self._async_publish(reports)
        return reports

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
