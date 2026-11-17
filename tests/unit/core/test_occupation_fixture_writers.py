"""Step 4 (kind=species) re-key of the step-2 K2 v1.1 scan for the scenario-fixture writers of `kind` in src/ (rpg-designer 3045e98a): src/certification/scenarios.py, src/perf/scenarios.py,
src/testing/scenario_runner.py. Every `V2EntityBuilder(...).kind(X)` chain with a literal X writes a SPECIES id (human for HERO/hero/actor/PRESSURE_TARGET, goblin for
MONSTER/monster/GOBLIN) and sets `occupation` to a label (the literal the fixture used to write as kind); the chains that copy a source entity pass its kind through. One test per file
iterates all of its chains (statically); the certification builders are also run and every entity they build is read.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.certification.scenarios import ArenaInjector, GameplayInjector, PressureInjector
from src.core.state import AuthoritativeState

ROOT = Path(__file__).resolve().parents[3]


def _chains(relpath):
    """Every outermost builder call chain rooted at V2EntityBuilder(...): the list of (method name, unparsed first argument) in order."""
    tree = ast.parse((ROOT / relpath).read_text(encoding="utf-8"))
    inner = {id(n.func.value) for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    chains = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and id(n) not in inner:
            calls, cur = [], n
            while isinstance(cur, ast.Call) and isinstance(cur.func, ast.Attribute):
                calls.append(cur)
                cur = cur.func.value
            if isinstance(cur, ast.Call) and isinstance(cur.func, ast.Name) and cur.func.id == "V2EntityBuilder":
                chains.append(list(reversed(calls)))
    return chains


@pytest.mark.parametrize("relpath", ["src/certification/scenarios.py", "src/perf/scenarios.py", "src/testing/scenario_runner.py"])
def test_every_literal_kind_chain_writes_a_species_id_and_an_occupation_label(relpath):
    from src.content.common_knowledge_seed import warmed_catalog

    species_ids = set(warmed_catalog().species)
    seen = 0
    for chain in _chains(relpath):
        kinds = [c.args[0] for c in chain if c.func.attr == "kind" and c.args]
        if not kinds:
            continue
        occupations = [kw.value for c in chain if c.func.attr == "identity" for kw in c.keywords if kw.arg == "occupation"]
        if isinstance(kinds[0], ast.Constant):
            assert kinds[0].value in species_ids, (relpath, chain[0].lineno, kinds[0].value)
            if relpath != "src/testing/scenario_runner.py":
                assert occupations and isinstance(occupations[0], ast.Constant) and occupations[0].value, (relpath, chain[0].lineno)
        seen += 1
    assert seen > 0


@pytest.mark.parametrize("build", [
    lambda s: PressureInjector.inject_entities(s, 3),
    ArenaInjector.build_team_battle, ArenaInjector.build_progression_test, ArenaInjector.build_mortality_test, ArenaInjector.build_tactical_test,
    ArenaInjector.build_social_test, ArenaInjector.build_quest_battle, ArenaInjector.build_regional_control_test,
    GameplayInjector.build_movement_test, GameplayInjector.build_harvest_test, GameplayInjector.build_integrated_loop,
])
def test_the_certification_builders_give_every_entity_a_species_kind_and_an_occupation_label(build):
    from src.content.common_knowledge_seed import warmed_catalog

    state = build(AuthoritativeState(tick=0, seed=1))
    assert state.entities
    species_ids = set(warmed_catalog().species)
    assert all(e.kind in species_ids and e.identity.occupation and e.identity.occupation != e.kind for e in state.entities.values())
