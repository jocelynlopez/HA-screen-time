"""Chaque exigence des specs doit être vérifiée par au moins un test marqué."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "openspec" / "specs"
TESTS = ROOT / "tests"

REQUIREMENT_HEADING = re.compile(r"^### Requirement: (.+?)\s*$", re.MULTILINE)
MARKER = re.compile(r'requirement\(\s*"([^"]+)"\s*\)')


def spec_requirements():
    found = set()
    for spec in SPECS.glob("*/spec.md"):
        capability = spec.parent.name
        for name in REQUIREMENT_HEADING.findall(spec.read_text(encoding="utf-8")):
            found.add(f"{capability}/{name}")
    return found


def covered_requirements():
    found = set()
    for test_file in TESTS.glob("test_*.py"):
        if test_file.name == Path(__file__).name:
            continue
        found.update(MARKER.findall(test_file.read_text(encoding="utf-8")))
    return found


def test_every_requirement_is_covered():
    missing = spec_requirements() - covered_requirements()
    assert not missing, f"Exigences sans test : {sorted(missing)}"


def test_markers_reference_existing_requirements():
    unknown = covered_requirements() - spec_requirements()
    assert not unknown, f"Marqueurs vers des exigences inconnues : {sorted(unknown)}"
