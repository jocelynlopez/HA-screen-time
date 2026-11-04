"""Chaque exigence en vigueur des specs doit être vérifiée par au moins un test marqué."""

import re
from pathlib import Path

from spec_reader import effective_requirements

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "openspec" / "specs"
CHANGES = ROOT / "openspec" / "changes"
TESTS = ROOT / "tests"

MARKER = re.compile(r'requirement\(\s*"([^"]+)"\s*\)')
SELF = {Path(__file__).name, "test_spec_reader.py"}


def covered_requirements():
    found = set()
    for test_file in TESTS.rglob("test_*.py"):
        if test_file.name in SELF:
            continue
        found.update(MARKER.findall(test_file.read_text(encoding="utf-8")))
    return found


def test_every_requirement_is_covered():
    missing = effective_requirements(SPECS, CHANGES) - covered_requirements()
    assert not missing, f"Exigences sans test : {sorted(missing)}"


def test_markers_reference_existing_requirements():
    unknown = covered_requirements() - effective_requirements(SPECS, CHANGES)
    assert not unknown, f"Marqueurs vers des exigences inconnues : {sorted(unknown)}"
