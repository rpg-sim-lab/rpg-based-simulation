"""Divergence 2.214: every production site that ends a project passes the tick it ends at (`ProjectState.ended_tick`), and every site that can end a resolve_blocker writes the blocker's
`last_project_end_tick` in the same update. A site that forgot the tick would write ``ended_tick`` None, which the quiet spell reads as no hold. Source scans over src/ (tests may omit the tick)."""
from __future__ import annotations

import ast
import pathlib

SRC = pathlib.Path(__file__).resolve().parents[3] / "src"
#: callee -> (positional index of the tick, keyword name)
TICKED = {"end_record": (3, "tick"), "supersede_record": (1, "tick"), "supersede_on_win": (3, "tick"), "way_closed_end": (2, "tick"), "refuse_rest": (1, "tick"), "_refused": (2, "tick")}


def _calls() -> list[tuple[str, str, ast.Call]]:
    out = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else None
                if name in TICKED or name in ("expire_suspended", "typed_completion"):
                    out.append((str(path.relative_to(SRC)), name, node))
    return out


def test_every_production_call_that_ends_a_project_passes_a_tick():
    missing = []
    for rel, name, node in _calls():
        if name not in TICKED:
            continue
        index, keyword = TICKED[name]
        if len(node.args) <= index and keyword not in {k.arg for k in node.keywords}:
            missing.append(f"{rel}:{node.lineno} {name}")
    assert missing == []


def test_the_files_that_end_a_project_are_the_known_ones():
    """A new production caller of `end_record` must be added here on purpose; a resolve_blocker-capable one must also stamp the blocker (next test)."""
    callers = {rel for rel, name, _ in _calls() if name == "end_record"}
    assert callers == {
        "core/strategic.py", "engine/building_arrival.py", "engine/lodging.py",
        "systems/strategic_systems/entity_target_objective.py", "systems/strategic_systems/intelligence.py",
    }


def test_every_site_that_can_end_a_resolve_blocker_stamps_the_blocker_in_the_same_update():
    text = {rel: (SRC / rel).read_text(encoding="utf-8") for rel in ("systems/strategic_systems/intelligence.py", "ai/goals/live_record_route.py")}
    assert "last_project_end_tick=current_tick" in text["systems/strategic_systems/intelligence.py"]          # the 50-tick timeout
    assert "ended_blocker_stamps(entity.strategic.blockers, written)" in text["systems/strategic_systems/intelligence.py"]  # the suspension expiry pass
    assert "ended_blocker_stamps(blockers or {}, [ended])" in text["ai/goals/live_record_route.py"]            # the supersede on a win
    expire_callers = {rel for rel, name, _ in _calls() if name == "expire_suspended"}
    supersede_callers = {rel for rel, name, _ in _calls() if name == "supersede_record"}
    assert expire_callers == {"systems/strategic_systems/intelligence.py"} and supersede_callers == {"ai/goals/live_record_route.py", "core/strategic.py"}
