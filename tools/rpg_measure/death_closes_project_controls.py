"""Death-closes-project kit controls (TCK-20261031-DEATH-CLOSES-NO-PROJECT; definition sha256 df2ba4b5...): m0 and the mutants m1-m7 on real-path FIXTURES, plus the three event-category controls.

Run with cwd = a FRESH scratch archive of the FIX head (f5a520daf) and PYTHONPATH = that archive:   python death_closes_project_controls.py [--only m0|m1|...|m7|e1|e2|e3]
The fixtures go through the REAL ``LifecycleSystem.resolve_lifecycle`` and ``ApplyPath.apply_generation``, and the observation is the SAME ``DeathTracker`` the spy uses. Each mutant is applied in memory (a monkeypatch undone after the control) and must turn its bar RED:
  m1 ``_end_projects_on_death`` is the identity (D1 red)        m2 only ACTIVE is ended, on a SUSPENDED fixture (D1 red)       m3 current_project_id is not cleared (D1 red from the current clause alone)
  m4 the records are removed instead of ended (D3 red)          m5 ended_tick = tick + 1 (D2 red)                              m6 a living body's field is touched on a death tick (D7 red)
  m7 the spy keys "dead" on combat.alive: on an old-age-only fixture under m1 the correct spy is D1 red and the alive-keyed spy is D1 green (the difference is shown)
  e1 a project event of a LIVING body is never dropped   e2 a non-project event of a dead body is kept   e3 a project event of a dead body is dropped   (the mask logic, given an EXPLICIT category argument; the run's own set is empty, so D7 compares the full stream)
m0 (the shipped tests pass) is run by the designer with pytest; here m0 is the UNMUTATED fixture, which must be green on D1/D2/D3 and equal to itself on D7.
Exit 0 only when every control behaves as stated (m0 green, every mutant red on its bar, e1-e3 hold).
"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace as NS
from typing import Any, Callable, Dict, List, Tuple

TICK = 100


def load_logic() -> Any:
    path = Path(__file__).resolve().with_name("death_closes_project_logic.py")
    spec = importlib.util.spec_from_file_location("_dcp_controls_logic", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["_dcp_controls_logic"] = module
    spec.loader.exec_module(module)
    return module


def fixtures(logic: Any, only_old_age: bool = False) -> Tuple[Any, Any, Any]:
    """(prior state, refined update, applied state). Body 1 is killed (ACTIVE current + SUSPENDED), body 2 lives (an ACTIVE project), body 3 dies of old age (combat.alive stays True, an ACTIVE project)."""
    from src.core.builder import V2EntityBuilder
    from src.core.state import AuthoritativeState
    from src.core.strategic import GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
    from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
    from src.engine.apply import ApplyPath
    from src.systems.lifecycle_systems.lifecycle import LifecycleSystem

    def project(pid, status=ProjectStatus.ACTIVE):
        objective = ObjectiveState(id=f"{pid}_o", kind=ObjectiveKind.REACH_LOCATION, target="town_center", status=ObjectiveStatus.ACTIVE)
        return ProjectState(id=pid, kind=GoalKind.HUNGER, status=status, objectives=[objective], active_objective_id=objective.id, suspended_since=50 if status == ProjectStatus.SUSPENDED else None)

    def body(eid, projects, current, age=0, max_age=100000):
        entity = V2EntityBuilder(eid).kind("hero").location(0.0, 0.0).lifecycle(age_ticks=age, max_age_ticks=max_age).build()
        return replace(entity, strategic=replace(entity.strategic, projects={p.id: p for p in projects}, current_project_id=current, current_objective_id=(f"{current}_o" if current else None)))

    entities = {}
    if not only_old_age:
        entities[1] = body(1, [project("a"), project("s", ProjectStatus.SUSPENDED)], "a")
        entities[2] = body(2, [project("living")], "living")
    entities[3] = body(3, [project("old")], "old", age=1000, max_age=1000)
    state = AuthoritativeState(tick=TICK, seed=1, entities=entities)
    kills = {} if only_old_age else {1: EntityUpdate(entity_id=1, combat=CombatUpdate(outcome_kind="KILL", alive_set=False))}
    refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate(entity_updates=kills))
    return state, refined, ApplyPath.apply_generation(state, refined, TICK + 1, TICK + 1)


def evaluate(logic: Any, only_old_age: bool = False, dead_key: str = "death_record") -> Dict[str, Any]:
    from src.engine.checkpoint import CanonicalStateHasher

    prior, _refined, new = fixtures(logic, only_old_age)
    tracker = logic.DeathTracker(dead_key)
    tracker.observe(int(new.tick), prior.entities, new.entities)
    rep = tracker.report()
    dead_ids = [eid for eid, e in new.entities.items() if logic.is_dead(e)]
    rep["living_digest"] = logic.living_projection_digest(CanonicalStateHasher.to_canonical_data(new), dead_ids)
    return rep


def mutate(mutant: str) -> Callable[[], None]:
    """Apply the mutant in memory; returns the undo."""
    from src.core.strategic import ProjectStatus, end_record
    from src.core.updates import EntityUpdate, StrategicUpdate
    from src.systems.lifecycle_systems import lifecycle as lc

    cls = lc.LifecycleSystem
    original_end = cls.__dict__["_end_projects_on_death"].__func__
    original_resolve = cls.__dict__["resolve_lifecycle"].__func__
    original_live = lc.end_live_on_death
    if mutant == "m1":
        cls._end_projects_on_death = staticmethod(lambda entity, ent_upd, tick: ent_upd)
    elif mutant == "m2":
        lc.end_live_on_death = lambda projects, staged, removed, tick: [p for p in original_live(projects, staged, removed, tick) if _was_active(projects, staged, p.id)]
    elif mutant == "m3":
        def keep_current(entity, ent_upd, tick):
            out = original_end(entity, ent_upd, tick)
            return out if out.strategic is None else replace(out, strategic=replace(out.strategic, current_project_id_set=None, current_objective_id_set=None))
        cls._end_projects_on_death = staticmethod(keep_current)
    elif mutant == "m4":
        def remove_instead(entity, ent_upd, tick):
            out = original_end(entity, ent_upd, tick)
            if out.strategic is None:
                return out
            ended = [p.id for p in out.strategic.projects_add_or_update if getattr(p.ended_by, "value", p.ended_by) == "DEATH"]
            kept = [p for p in out.strategic.projects_add_or_update if p.id not in ended]
            return replace(out, strategic=replace(out.strategic, projects_add_or_update=kept, projects_remove=list(out.strategic.projects_remove) + ended))
        cls._end_projects_on_death = staticmethod(remove_instead)
    elif mutant == "m5":
        cls._end_projects_on_death = staticmethod(lambda entity, ent_upd, tick: original_end(entity, ent_upd, tick + 1))
    elif mutant == "m6":
        def touch_living(state, update):
            refined = original_resolve(state, update)
            dying = any(getattr(getattr(eu, "lifecycle", None), "death_record_set", None) is not None for eu in refined.entity_updates.values())
            if not dying:
                return refined
            updates = dict(refined.entity_updates)
            for eid, ent in state.entities.items():
                if eid not in updates and ent.lifecycle.active and ent.combat.alive:
                    updates[eid] = EntityUpdate(entity_id=eid, strategic=StrategicUpdate(current_objective_id_set="touched_on_a_death_tick"))
            return replace(refined, entity_updates=updates)
        cls.resolve_lifecycle = staticmethod(touch_living)
    elif mutant in ("m0", "m7"):
        pass
    else:
        raise ValueError(f"unknown mutant {mutant}")

    def undo() -> None:
        cls._end_projects_on_death = staticmethod(original_end)
        cls.resolve_lifecycle = staticmethod(original_resolve)
        lc.end_live_on_death = original_live
    return undo


def _was_active(projects: Any, staged: Any, pid: str) -> bool:
    record = {p.id: p for p in staged}.get(pid) or projects.get(pid)
    return getattr(getattr(record, "status", None), "value", getattr(record, "status", None)) == "ACTIVE"


def bars(rep: Dict[str, Any]) -> Dict[str, bool]:
    """True = green."""
    return {"D1": rep["dwl_total_rows"] == 0, "D2": rep["d2_violations"] == 0, "D3": rep["d3_violations"] == 0}


def run_mutant(logic: Any, mutant: str, reference_digest: str) -> Tuple[bool, str]:
    undo = mutate(mutant)
    try:
        if mutant == "m7":
            correct, alive_keyed = evaluate(logic, True, "death_record"), evaluate(logic, True, "alive")
            red_correct, red_alive = not bars(correct)["D1"], not bars(alive_keyed)["D1"]
            return red_correct and not red_alive, f"old-age-only fixture under identity: correct spy D1 {'red' if red_correct else 'GREEN'}, alive-keyed spy D1 {'red' if red_alive else 'green'} (must be red / green)"
        rep = evaluate(logic)
    finally:
        undo()
    green = bars(rep)
    d7_green = rep["living_digest"] == reference_digest
    expect = {"m0": None, "m1": "D1", "m2": "D1", "m3": "D1", "m4": "D3", "m5": "D2", "m6": "D7"}[mutant]
    desc = f"D1={'green' if green['D1'] else 'RED'} D2={'green' if green['D2'] else 'RED'} D3={'green' if green['D3'] else 'RED'} D7={'green' if d7_green else 'RED'}"
    if expect is None:
        return all(green.values()) and d7_green, desc + " (all must be green)"
    observed_red = (not d7_green) if expect == "D7" else (not green[expect])
    others_ok = all(green[k] for k in green if k != expect) if expect != "D7" else all(green.values())
    return observed_red and others_ok and (d7_green or expect == "D7"), desc + f" ({expect} must be the red one)"


MASK = ("QUEST_COMPLETED", "QUEST_FAILED")      # explicit argument of the mask tests only


def event_controls(logic: Any) -> List[Tuple[str, bool, str]]:
    def ev(category: str, subject: str) -> Any:
        return NS(category=NS(value=category), subject=subject, region_id=None, severity=1.0, payload={}, tick=TICK)
    nothing = logic.living_event_digest([], [1], MASK)
    results = []
    living_kept = logic.living_event_digest([ev("QUEST_COMPLETED", "2")], [1], MASK) == logic.living_event_digest([ev("QUEST_COMPLETED", "2")], [], categories=())
    results.append(("e1 a project event of a LIVING body is never dropped", living_kept, "digest equals the no-drop digest"))
    kept = logic.living_event_digest([ev("FEEDING_KILL", "1")], [1], MASK) == logic.living_event_digest([ev("FEEDING_KILL", "1")], [], categories=()) != nothing
    results.append(("e2 a non-project event of a dead body is kept", kept, "digest equals the no-drop digest and differs from the empty one"))
    dropped = logic.living_event_digest([ev("QUEST_FAILED", "1")], [1], MASK) == nothing
    results.append(("e3 a project event of a dead body is dropped", dropped, "digest equals the empty stream's"))
    exact = logic.living_event_digest([ev("QUEST_COMPLETED_EXTRA", "1")], [1], MASK) != nothing
    results.append(("e3b a category that only CONTAINS a project name is not dropped (no substring match)", exact, "digest differs from the empty stream's"))
    return results


def main(argv: List[str]) -> int:
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    logic = load_logic()
    reference = evaluate(logic)["living_digest"]
    rows: List[Tuple[str, bool, str]] = []
    for mutant in ("m0", "m1", "m2", "m3", "m4", "m5", "m6", "m7"):
        if only in (None, mutant):
            ok, desc = run_mutant(logic, mutant, reference)
            rows.append((mutant, ok, desc))
    for name, ok, desc in event_controls(logic):
        if only in (None, name[:2]) or (only == "e3" and name.startswith("e3")):
            rows.append((name, ok, desc))
    for name, ok, desc in rows:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {desc}")
    bad = [n for n, ok, _ in rows if not ok]
    print(f"controls: {len(rows) - len(bad)}/{len(rows)} behave as stated" + (f"; FAILED: {bad}" if bad else ""))
    return 0 if rows and not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
