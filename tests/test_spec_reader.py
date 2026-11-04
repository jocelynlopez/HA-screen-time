"""Tests du lecteur d'exigences, sur des specs temporaires."""

from spec_reader import effective_requirements


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_tree(tmp_path):
    specs, changes = tmp_path / "specs", tmp_path / "changes"
    write(specs / "cap" / "spec.md", "## Requirements\n\n### Requirement: Garde\n\n### Requirement: Retire\n\n### Requirement: Modifie\n")
    write(
        changes / "chg" / "specs" / "cap" / "spec.md",
        "## MODIFIED Requirements\n\n### Requirement: Modifie\n\n"
        "## ADDED Requirements\n\n### Requirement: Nouveau\n\n"
        "## REMOVED Requirements\n\n### Requirement: Retire\n",
    )
    write(changes / "archive" / "vieux" / "specs" / "cap" / "spec.md", "## ADDED Requirements\n\n### Requirement: Archive\n")
    return specs, changes


def test_main_requirements_are_kept(tmp_path):
    specs, changes = make_tree(tmp_path)
    assert {"cap/Garde", "cap/Modifie"} <= effective_requirements(specs, changes)


def test_added_requirements_of_active_changes_are_included(tmp_path):
    specs, changes = make_tree(tmp_path)
    assert "cap/Nouveau" in effective_requirements(specs, changes)


def test_removed_requirements_are_dropped(tmp_path):
    specs, changes = make_tree(tmp_path)
    assert "cap/Retire" not in effective_requirements(specs, changes)


def test_archived_changes_are_ignored(tmp_path):
    specs, changes = make_tree(tmp_path)
    assert "cap/Archive" not in effective_requirements(specs, changes)
