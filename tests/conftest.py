from collections import defaultdict


def requirements_of(item):
    """Exigences déclarées par les marqueurs `requirement` d'un test."""
    return [m.args[0] for m in item.iter_markers("requirement")]


def pytest_collection_modifyitems(config, items):
    by_requirement = defaultdict(list)
    for item in items:
        for name in requirements_of(item):
            by_requirement[name].append(item.name)
    config._requirement_map = by_requirement


def pytest_terminal_summary(terminalreporter, config):
    by_requirement = getattr(config, "_requirement_map", None)
    if not by_requirement:
        return
    terminalreporter.section("exigences vérifiées")
    for name in sorted(by_requirement):
        tests = by_requirement[name]
        terminalreporter.write_line(f"{name}  ({len(tests)} test(s))")
        for test in tests:
            terminalreporter.write_line(f"    - {test}")
