"""Lecture des exigences des specs OpenSpec : specs principales et deltas des changes actifs."""

import re
from pathlib import Path

REQUIREMENT = re.compile(r"^### Requirement: (.+?)\s*$", re.MULTILINE)
SECTION = re.compile(r"^## (ADDED|MODIFIED|REMOVED|RENAMED) Requirements\s*$", re.MULTILINE)


def requirement_names(text):
    return set(REQUIREMENT.findall(text))


def main_requirements(specs_root):
    found = set()
    for spec in Path(specs_root).glob("*/spec.md"):
        for name in requirement_names(spec.read_text(encoding="utf-8")):
            found.add(f"{spec.parent.name}/{name}")
    return found


def delta_requirements(changes_root):
    """(ajoutées ou modifiées, supprimées) par les deltas des changes actifs (hors archive)."""
    present, removed = set(), set()
    for spec in Path(changes_root).glob("*/specs/*/spec.md"):
        if "archive" in spec.relative_to(changes_root).parts:
            continue
        capability = spec.parent.name
        text = spec.read_text(encoding="utf-8")
        marks = list(SECTION.finditer(text))
        for i, mark in enumerate(marks):
            end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
            names = {f"{capability}/{n}" for n in requirement_names(text[mark.end():end])}
            if mark.group(1) == "REMOVED":
                removed |= names
            elif mark.group(1) in ("ADDED", "MODIFIED"):
                present |= names
    return present, removed


def effective_requirements(specs_root, changes_root):
    """Exigences en vigueur : principales, moins les supprimées, plus les ajoutées ou modifiées."""
    present, removed = delta_requirements(changes_root)
    return (main_requirements(specs_root) - removed) | present
