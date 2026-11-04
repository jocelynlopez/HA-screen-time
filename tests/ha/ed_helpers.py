"""Fabrique les entités d'une intégration `ecole_directe` simulée."""

from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

ED = "ecole_directe"


def add_ed_entry(hass, title="Mael"):
    entry = MockConfigEntry(domain=ED, title=title)
    entry.add_to_hass(hass)
    return entry


def add_sensor(hass, ed_entry, object_id, state, attributes=None):
    """Capteur rattaché à l'entrée EcoleDirecte ; renvoie son entity_id."""
    registry = er.async_get(hass)
    entity = registry.async_get_or_create(
        "sensor", ED, f"{ed_entry.entry_id}_{object_id}", config_entry=ed_entry, suggested_object_id=object_id
    )
    hass.states.async_set(entity.entity_id, state, attributes or {})
    return entity.entity_id


def add_subject(hass, ed_entry, object_id, name, code, state):
    return add_sensor(hass, ed_entry, object_id, state, {"Nom": name, "Code": code, "Moyenne classe": "12"})


def add_notes(hass, ed_entry, notes, object_id="ed_mael_lopez_notes", state="15"):
    return add_sensor(hass, ed_entry, object_id, state, {"notes": notes})


SUBJECTS = {  # capteur → (Nom, Code, état)
    "ed_mael_lopez_anglais_lv1": ("anglais lv1", "agl1", "13.85"),
    "ed_mael_lopez_arts_plastiques": ("arts plastiques", "ap", "17"),
    "ed_mael_lopez_education_musicale": ("education musicale", "em", "16"),
    "ed_mael_lopez_ens_integ_sc_techno": ("ens.integ.sc.&techno", "eist", "18"),
    "ed_mael_lopez_francais": ("francais", "fr", "10.67"),
    "ed_mael_lopez_histoire_geographie": ("histoire-geographie", "hg", "17.43"),
    "ed_mael_lopez_mathematiques": ("mathematiques", "mat", "19.34"),
    "ed_mael_lopez_ed_physique_sport": ("ed.physique & sport.", "eps", "unknown"),
}


def add_all_subjects(hass, ed_entry):
    return {oid: add_subject(hass, ed_entry, oid, *values) for oid, values in SUBJECTS.items()}
