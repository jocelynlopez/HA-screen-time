"""Fixtures des tests Home Assistant."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.screen_time_wallet.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Autorise le chargement de custom_components/ dans l'instance HA de test."""
    yield


def make_entry(name="Mael", options=None, entry_id=None):
    kwargs = {"entry_id": entry_id} if entry_id else {}
    return MockConfigEntry(
        domain=DOMAIN, title=name, data={"name": name}, options=options or {},
        unique_id=name.casefold(), **kwargs,
    )


@pytest.fixture
def entry(hass):
    entry = make_entry()
    entry.add_to_hass(hass)
    return entry


@pytest.fixture(autouse=True)
async def utc_timezone(hass):
    """Fuseau UTC : les lundis 00h00 des tests sont alors sans ambiguïté."""
    await hass.config.async_set_time_zone("UTC")
