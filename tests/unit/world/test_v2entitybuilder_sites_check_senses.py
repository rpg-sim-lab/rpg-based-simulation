"""PERC-02a source scan: every non-test ``V2EntityBuilder(...)`` construction site under src/ either calls the sense check on its path or is named in the allowlist with a reason.

A new site fails this test until it calls ``require_species_sense_profile`` or is added below with a one-line reason."""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[3] / "src"

CHECKED = {  # the file calls require_species_sense_profile on the path that builds the body
    "worldassembly/entity_spawner.py",
    "entities/archetype_factory.py",
    "worldbuilding/compiler.py",
    "domains/campaigns/orchestrator.py",
    "domains/campaigns/runner.py",
}

ALLOWLIST = {
    "certification/scenarios.py": "certification fixtures: fixed human/monster bodies of a test world, not content-driven",
    "testing/scenario_runner.py": "test harness runner; its bodies are fixture kinds",
    "observability/readiness/harness.py": "readiness probe building a fixed human body",
    "perf/scenarios.py": "performance benchmark fixtures",
    "systems/world_systems/generator.py": "mid-run spawners; TCK-20261118-MID-RUN-SPAWNED-BODIES-SKIP-THE-SENSES-CHECK owns the check",
}


def _sites():
    found = {}
    for path in SRC.rglob("*.py"):
        rel = path.relative_to(SRC).as_posix()
        if rel == "core/builder.py":
            continue  # the builder itself is generic and is NOT hooked (rpg-designer)
        text = path.read_text()
        if re.search(r"\bV2EntityBuilder\(", text):
            found[rel] = text
    return found


def test_every_builder_site_calls_the_check_or_is_allowlisted():
    sites = _sites()
    unlisted = sorted(rel for rel in sites if rel not in CHECKED and rel not in ALLOWLIST)
    assert not unlisted, f"V2EntityBuilder site(s) neither checking senses nor allowlisted with a reason: {unlisted}"
    for rel in CHECKED:
        assert "require_species_sense_profile(" in sites[rel] or "require_declared_population_species(" in sites[rel], f"{rel} is listed as checked but does not call the check"


def test_the_lists_hold_no_stale_entry():
    sites = _sites()
    stale = sorted(rel for rel in (*CHECKED, *ALLOWLIST) if rel not in sites)
    assert not stale, f"listed file(s) no longer construct a V2EntityBuilder: {stale}"
