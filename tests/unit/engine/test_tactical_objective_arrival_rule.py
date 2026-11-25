"""The three arrival sites of `tactical_objective.py` now ask `src/core/arrival.py` (`has_arrived`, Manhattan distance <= 1.0, boundary included) instead of the literal `> 1.0`: the decisions are the same at 0.5, 1.0 and 1.5. The reach-location
step walks (sets the nav target) only when NOT arrived; the source holds no literal arrival comparison any more."""
import ast
import itertools
from dataclasses import replace
from pathlib import Path

from src.core.arrival import has_arrived
from src.engine.tactical_objective import (
    ObjectiveDestinationSuppressed,
    pursue_objective,
)
from tests.unit.engine.test_objective_destination_suppressed import (
    TARGET,
    _resolve,
    _state,
    _subject,
)


def _at(entity, x, y):
    return replace(entity, navigation=replace(entity.navigation, position=(x, y)))


def test_the_reach_location_step_walks_only_when_not_arrived_at_0_5_1_0_and_1_5():
    # TARGET is (12.0, 5.0): positions at Manhattan 0.5, 1.0 (the boundary) and 1.5
    for x, arrived in ((11.5, True), (11.0, True), (10.5, False)):
        e = _at(_subject(), x, 5.0)
        out = pursue_objective(_state(e, 100), e, None, _resolve)
        assert not isinstance(out, ObjectiveDestinationSuppressed)
        if arrived:
            assert out.navigation is None  # arrived: no walk, as the literal `> 1.0` gave
        else:
            assert out.navigation is not None and tuple(out.navigation.target_set) == TARGET  # en route: the walk, as before


def test_has_arrived_equals_the_old_literal_over_a_grid_and_a_strict_rule_differs_exactly_at_the_boundary():
    pts = [(12.0 + x / 2.0, 5.0 + y / 2.0) for x, y in itertools.product(range(-6, 7), repeat=2)]  # a grid of half-tile steps around the target, the boundary (Manhattan 1.0) included
    for px, py in pts:
        old_arrived = not (abs(12.0 - px) + abs(5.0 - py) > 1.0)  # the old test: `_distance(...) > 1.0` is "not arrived"
        assert has_arrived((px, py), (12.0, 5.0)) == old_arrived
    assert any(abs(12.0 - px) + abs(5.0 - py) == 1.0 for px, py in pts) and any(abs(12.0 - px) + abs(5.0 - py) > 1.0 for px, py in pts)  # the grid really crosses the boundary
    boundary = (11.0, 5.0)  # Manhattan exactly 1.0
    assert has_arrived(boundary, (12.0, 5.0)) is True and (abs(12.0 - boundary[0]) + abs(5.0 - boundary[1]) < 1.0) is False  # the strict `< 1.0` of the strategic detour completion differs here, and is left alone


def test_no_literal_arrival_comparison_is_left_in_tactical_objective():
    src = Path("src/engine/tactical_objective.py").read_text()
    tree = ast.parse(src)
    literal = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Compare) and any(isinstance(c, ast.Constant) and c.value == 1.0 for c in n.comparators)]
    assert literal == []  # the three sites ask has_arrived
    calls = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "has_arrived"]
    assert len(calls) == 3
    # the failing control: the check finds a planted literal comparison
    planted = ast.parse("def f(d):\n    return d > 1.0\n")
    assert [n.lineno for n in ast.walk(planted) if isinstance(n, ast.Compare) and any(isinstance(c, ast.Constant) and c.value == 1.0 for c in n.comparators)] == [2]
