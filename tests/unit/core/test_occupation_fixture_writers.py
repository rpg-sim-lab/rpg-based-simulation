"""K2 v1.1 for the scenario-fixture writers of `kind` in src/ (rpg-designer ruling (a), M1 step 2): src/certification/scenarios.py, src/perf/scenarios.py,
src/testing/scenario_runner.py. Every `V2EntityBuilder(...).kind(X)` chain in these files also sets `occupation` to the same expression, so step 3 stays neutral on them. One test per file
iterates all of its chains (statically, by the chain's own call list); the certification builders are also run and every entity they build is read.
Their `kind` literals ("HERO", "MONSTER") are not species ids: before step 4 the step-1 scan is re-run over these three directories (readers and writers), per the ruling.
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
def test_every_kind_chain_in_the_file_sets_occupation_to_the_same_expression(relpath):
    seen = 0
    for chain in _chains(relpath):
        kinds = [ast.unparse(c.args[0]) for c in chain if c.func.attr == "kind" and c.args]
        if not kinds:
            continue
        occupations = [ast.unparse(kw.value) for c in chain if c.func.attr == "identity" for kw in c.keywords if kw.arg == "occupation"]
        assert occupations == kinds, (relpath, chain[0].lineno, kinds, occupations)
        seen += 1
    assert seen > 0


@pytest.mark.parametrize("build", [
    lambda s: PressureInjector.inject_entities(s, 3),
    ArenaInjector.build_team_battle, ArenaInjector.build_progression_test, ArenaInjector.build_mortality_test, ArenaInjector.build_tactical_test,
    ArenaInjector.build_social_test, ArenaInjector.build_quest_battle, ArenaInjector.build_regional_control_test,
    GameplayInjector.build_movement_test, GameplayInjector.build_harvest_test, GameplayInjector.build_integrated_loop,
])
def test_the_certification_builders_give_every_entity_an_occupation_equal_to_its_kind(build):
    state = build(AuthoritativeState(tick=0, seed=1))
    assert state.entities
    assert all(e.identity.occupation == e.kind for e in state.entities.values())
