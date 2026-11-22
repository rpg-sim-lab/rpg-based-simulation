"""Controls for the #992 wolf-starvation read kit (TCK-20261122-TRACE-WHY-TWO-WOLVES-STARVE-ON-THE-PREY-STRIKE-BACK-FIX) and the folded fixes of TCK-20261122-TRACE-KIT-CALENDAR-LOAD-WRITES-BYTECODE-INTO-A-FROZEN-TREE.

No world is run here: the fixtures are fake states (SimpleNamespace) and tmp trees; the real kernel is first met by the smoke under its own GO.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest

from tools.rpg_measure import pinned_check
from tools.rpg_measure import subject_trace_run as run
from tools.rpg_measure import subject_trace_spy as spy_module
from tools.rpg_measure import subject_trace_summary as summary

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "tools" / "rpg_measure"
WOLF_LAUNCH = KIT / "wolf_starve_launch.sh"
FF = "FRIENDLY_FIRE_ILLEGAL"


# --------------------------------------------------------------------------------------------- fakes
def body(eid: int, kind: str = "wolf", position: tuple = (0.0, 0.0), hp: int = 40, hunger: float = 10.0, alive: bool = True, last_hit: Optional[tuple] = None, death: Any = None,
         payload: Optional[Dict[str, Any]] = None, objective_target: Optional[int] = None) -> Any:
    last_hit = last_hit or (None, (), ())
    objective = {"id": 1, "target_entity_id": objective_target} if objective_target is not None else None
    project = SimpleNamespace(kind="HUNT", canonical_objectives=lambda: [objective] if objective else [], active_objective_id=1)
    return SimpleNamespace(
        id=eid, kind=kind, navigation=SimpleNamespace(position=position, target=None, path=[], movement_mode=SimpleNamespace(value="WANDER"), last_failure_reason=None, lodged_in=None, leash_radius=0, home_position=None),
        combat=SimpleNamespace(readiness=100.0, hp=hp, alive=alive, last_hit_tick=last_hit[0], last_hit_attackers=last_hit[1], last_hit_damages=last_hit[2]),
        task=SimpleNamespace(work_kind="ENTITY_ACT", payload=payload or {}),
        strategic=SimpleNamespace(current_project_id=1 if objective else None, current_objective_id=1 if objective else None, projects={1: project} if objective else {}),
        biological=SimpleNamespace(hunger=hunger, sleep_debt=1.0, rest_pressure=2.0, last_meal_tick=3, last_sleep_tick=4, well_rested_until=-1),
        lifecycle=SimpleNamespace(death_record=death, passive_death_cause=None, passive_death_cause_tick=None))


def world(tick: int, *entities: Any, corpses: Optional[Dict[int, Any]] = None) -> Any:
    return SimpleNamespace(tick=tick, entities={e.id: e for e in entities}, corpses=corpses or {})


def step(kind: str, available: bool = False, reason: str = "no", target: Optional[int] = None) -> Any:
    return SimpleNamespace(kind=kind, available=available, reason=reason, target_id=None if target is None else str(target), target_entity_id=target, target_pos=None)


def reads(ways: tuple = (), steps: Optional[List[Any]] = None, radius: float = 20.0) -> spy_module.WayReads:
    steps = steps if steps is not None else [step("FORAGE"), step("SCAVENGE"), step("HUNT")]
    return spy_module.WayReads(lambda e, s: ways, lambda e, s: frozenset(x.kind for x in steps if x.available and spy_module.kind_name(x.kind) in ("FORAGE", "SCAVENGE", "HUNT")), lambda e, s: steps,
                               lambda e, p: True, lambda e, item: item == "meat", radius)


def corpse(cid: int, position: tuple, of: int = 8, item: str = "meat") -> Any:
    return SimpleNamespace(id=cid, position=position, original_entity_id=of, items=[SimpleNamespace(quantity=1, item_id=item)])


class FakeApply:
    @staticmethod
    def apply_generation(prior, update, *args, **kwargs):
        return update


class FakeLegality:
    result = (False, SimpleNamespace(name=FF, value="friendly fire"))

    @staticmethod
    def verify_attack_legality(attacker, target, state_or_context, is_opportunity_attack=False, *, night=None):
        return FakeLegality.result


# --------------------------------------------------------------------------------------------- 1. the plan
def test_the_plan_round_trips_through_the_cli_and_pins_a_recomputable_sha256(tmp_path: Path) -> None:
    out = tmp_path / "subjects.json"
    done = subprocess.run([sys.executable, "-B", str(KIT / "subject_trace_run.py"), "plan", "--world", "frontier_living_world", "--subject", "42:47:2953:3653", "--subject", "45:49:3369:4069",
                           "--expect-death", "42:47:3553:STARVATION", "--expect-death", "45:49:3969:STARVATION", "--out", str(out)], capture_output=True, text=True, cwd=tmp_path, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0, done.stderr
    plan = json.loads(out.read_text(encoding="utf-8"))
    assert json.loads(done.stdout)["plan_sha256"] == plan["plan_sha256"]
    assert plan["subjects_by_seed"] == {"42": [{"id": 47, "roles": ["subject"], "windows": [[2953, 3653]], "counterparts": []}], "45": [{"id": 49, "roles": ["subject"], "windows": [[3369, 4069]], "counterparts": []}]}
    assert plan["seeds_with_subjects"] == [42, 45] and plan["way_reads"] is True and plan["derived_from"] == {} and plan["kind"] == run.WOLF_PLAN_KIND
    assert plan["expect_deaths"] == [{"seed": 42, "id": 47, "tick": 3553, "cause": "STARVATION"}, {"seed": 45, "id": 49, "tick": 3969, "cause": "STARVATION"}]
    assert run.plan_matches(plan)["ok"] and run.plan_matches(plan, plan["plan_sha256"])["ok"] and not run.plan_matches(plan, "0" * 64)["ok"]
    check = subprocess.run([sys.executable, "-B", str(KIT / "subject_trace_run.py"), "plan-check", "--plan", str(out), "--sha", plan["plan_sha256"]], capture_output=True, text=True, cwd=tmp_path)
    assert check.returncode == 0


def test_an_edited_plan_no_longer_matches_its_sha256_and_the_check_exits_non_zero(tmp_path: Path) -> None:
    plan = run.build_plan("w", [run.parse_subject("42:47:10:20")], [])
    plan["subjects_by_seed"]["42"][0]["windows"] = [[10, 21]]
    path = tmp_path / "p.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    assert not run.plan_matches(plan)["ok"]
    assert subprocess.run([sys.executable, "-B", str(KIT / "subject_trace_run.py"), "plan-check", "--plan", str(path)], capture_output=True, text=True).returncode == 1


@pytest.mark.parametrize("text", ["42:47:10", "42:47:20:10", "a:47:1:2", "42:47:-1:5", "42:47:1:2:3"])
def test_a_malformed_or_empty_subject_is_refused_not_guessed(text: str) -> None:
    with pytest.raises(ValueError):
        run.parse_subject(text)


def test_two_windows_of_one_subject_merge_and_a_counterpart_is_never_a_subject() -> None:
    plan = run.build_plan("w", [run.parse_subject("42:47:10:20"), run.parse_subject("42:47:15:30"), run.parse_subject("42:47:50:60")], [])
    assert plan["subjects_by_seed"]["42"] == [{"id": 47, "roles": ["subject"], "windows": [[10, 30], [50, 60]], "counterparts": []}]
    spy = spy_module.SubjectSpy(plan["subjects_by_seed"]["42"], ways=reads())       # the plan drives the spy as it is
    spy.observe(world(11, body(47), body(9, kind="deer")), world(12, body(47), body(9, kind="deer")))
    assert [r["id"] for r in spy.rows] == [47]                                       # the deer met in a legality call is a row's counterpart, not a subject


# --------------------------------------------------------------------------------------------- 2. every new field on a 300-tick fixture
def three_hundred_ticks() -> spy_module.SubjectSpy:
    """Wolf 47 for ticks 0-300: hunger rises, a deer 9 is hunted from tick 100, the deer strikes at 150 (hp 40 -> 36), a carcass lies 7 tiles away, the wolf's starvation record lands at tick 300."""
    from src.core.death_cause import DeathCause, DeathRecord

    spy = spy_module.SubjectSpy([{"id": 47, "roles": ["subject"], "windows": [[0, 300]], "counterparts": []}], ways=None)
    hunting = [step("FORAGE"), step("SCAVENGE"), step("HUNT", True, "", 9)]
    spy.ways = spy_module.WayReads(lambda e, s: ("SCAVENGE", "HUNT_EAT_RAW") if s.tick >= 100 else (), lambda e, s: frozenset({"SCAVENGE", "HUNT"}) if s.tick >= 100 else frozenset(),
                                   lambda e, s: hunting if s.tick >= 100 else [step("FORAGE"), step("SCAVENGE"), step("HUNT")], lambda e, p: p[0] < 50, lambda e, item: item == "meat", 20.0)
    spy.install(FakeApply, FakeLegality)
    try:
        for t in range(1, 301):
            hit = (150, (9,), (4,)) if t >= 150 else None
            hp = 36 if t >= 150 else 40
            death = DeathRecord(DeathCause.STARVATION, 300) if t == 300 else None
            wolf_before = body(47, hp=40 if t - 1 < 150 else 36, hunger=(t - 1) * 0.3, last_hit=(150, (9,), (4,)) if t - 1 >= 150 else None, payload={"target_id": 9} if t >= 100 else {}, objective_target=9 if t >= 100 else None)
            wolf_after = body(47, hp=hp, hunger=t * 0.3, last_hit=hit, death=death, alive=t != 300, payload={"target_id": 9} if t >= 100 else {}, objective_target=9 if t >= 100 else None)
            deer = body(9, kind="deer", position=(2.0, 1.0))
            carcasses = {5: corpse(5, (7.0, 0.0)), 6: corpse(6, (60.0, 0.0))}
            FakeLegality.verify_attack_legality(wolf_before, deer, world(t - 1, wolf_before, deer))
            spy.observe(world(t - 1, wolf_before, deer, body(8, kind="deer", position=(7.0, 0.0), alive=False), corpses=carcasses), world(t, wolf_after, deer, corpses=carcasses))
    finally:
        spy.restore()
    return spy


def test_each_new_field_is_present_on_a_300_tick_fixture() -> None:
    spy = three_hundred_ticks()
    assert len(spy.rows) == 300
    first, late = spy.rows[0], spy.rows[-1]
    assert first["after"]["needs"] == {"hunger": pytest.approx(0.3), "sleep_debt": 1.0, "rest_pressure": 2.0, "last_meal_tick": 3, "last_sleep_tick": 4, "well_rested_until": -1}      # the biological need fields
    assert first["ways"]["ways"] == [] and first["ways"]["open_food_steps"] == [] and spy.rows[120]["ways"]["ways"] == ["SCAVENGE", "HUNT_EAT_RAW"] and spy.rows[120]["ways"]["open_food_steps"] == ["HUNT", "SCAVENGE"]
    assert spy.rows[120]["ways"]["steps"]["HUNT"] == {"available": True, "reason": "", "target_id": "9", "target_entity_id": 9, "target_pos": None}
    assert first["ways"]["steps"]["FORAGE"]["reason"] == "no" and first["ways"]["steps_consistent"] is True and spy.rows[120]["ways"]["steps_consistent"] is False    # SCAVENGE is open in the ways but not in the fake steps list
    assert first["ways"]["carcasses"] == [{"id": 5, "tile": [7.0, 0.0], "distance": 7.0, "in_way_range": True, "edible": True, "own_species": False}]      # the carcass 60 tiles away is outside the radius 20
    assert spy.hits_taken == {47: [{"tick": 150, "hit_tick": 150, "attackers": [9], "damages": [4], "hp_delta": 4}]}                                       # hits taken: the source and the hp delta from the typed hit record
    assert spy.rows[149]["hit_taken"]["attackers"] == [9] and "hit_taken" not in spy.rows[150]
    assert spy.death_records[47]["record"] == {"cause": "STARVATION", "tick": 300, "last_attacker_id": None, "hazard_kind": None} and spy.death_records[47]["first_seen_tick"] == 300
    assert late["counterparts"]["9"]["alive"] is True and late["counterparts"]["9"]["manhattan"] == 3.0 and late["counterparts"]["9"]["kind"] == "deer"       # a body met is a row of the subject
    assert spy.rows[120]["legality_this_tick"] == [{"target_id": 9, "legal": False, "reason": FF}]
    assert spy.report()["hits_taken"]["47"] and spy.report()["way_reads"] is True


def test_the_reads_name_the_real_enums_by_name_not_by_their_lower_case_values() -> None:
    from src.ai.goals.base import OpeningStepKind
    from src.ai.goals.ways import WayKind

    steps = [step(OpeningStepKind.FORAGE), step(OpeningStepKind.SCAVENGE), step(OpeningStepKind.HUNT, True, "", 9), step(OpeningStepKind.EARN_THEN_BUY), step(OpeningStepKind.ASK)]
    result = reads((WayKind.HUNT_EAT_RAW,), steps).reads(world(1, body(47)), body(47))
    assert result["ways"] == ["HUNT_EAT_RAW"] and result["open_food_steps"] == ["HUNT"] and sorted(result["steps"]) == ["ASK", "EARN_THEN_BUY", "FORAGE", "HUNT", "SCAVENGE"] and result["steps_consistent"] is True
    row = wolf_row(100, hunting=9)
    row["ways"]["steps"] = result["steps"]
    row["before"]["payload"] = {"target_id": 9}
    assert summary.hunt_target(row) == 9                       # the summary reads the same names the spy writes


def test_a_dead_or_absent_subject_has_no_way_read_but_keeps_its_row() -> None:
    spy = spy_module.SubjectSpy([{"id": 47, "roles": ["subject"], "windows": [[0, 9]], "counterparts": []}], ways=reads())
    spy.observe(world(1, body(47, alive=False)), world(2, body(47, alive=False)))
    spy.observe(world(2, body(47, alive=False)), world(3))
    assert [r["ways"] for r in spy.rows] == [None, None] and spy.rows[1]["after"]["state"] == "ABSENT"


# --------------------------------------------------------------------------------------------- 2b. the reads are pure
def test_the_reads_run_on_a_copy_so_a_cache_write_never_reaches_the_kernels_state() -> None:
    from src.core.state import AuthoritativeState
    from src.engine.world_index import WorldIndexService

    kept = AuthoritativeState(tick=5, seed=1)
    assert kept.world_indexes is None
    WorldIndexService.get_indexes(spy_module.read_view(kept))                  # what a read like nearby_entities does
    assert kept.world_indexes is None                                          # the kernel's state is untouched
    WorldIndexService.get_indexes(kept)                                         # positive control: a direct call DOES write the cache onto the state
    assert kept.world_indexes is not None


def test_a_read_that_writes_to_a_body_would_raise_on_the_frozen_fixture_and_the_reads_do_not() -> None:
    @dataclass(frozen=True)
    class Frozen:
        position: tuple = (0.0, 0.0)

    frozen_wolf = body(47)
    frozen_wolf.navigation = Frozen()
    frozen_wolf.biological = SimpleNamespace(hunger=1.0, sleep_debt=0.0, rest_pressure=0.0, last_meal_tick=0, last_sleep_tick=0, well_rested_until=-1)
    result = reads().reads(world(1, frozen_wolf, corpses={1: corpse(1, (1.0, 1.0))}), frozen_wolf)
    assert result["carcasses"][0]["distance"] == 2.0
    with pytest.raises(Exception):
        frozen_wolf.navigation.position = (9, 9)                                # positive control: this fixture does reject a write


# --------------------------------------------------------------------------------------------- 3. the spy's VOID rules
def doc(arm: str = "new", final_hash: str = "h", ticks: int = 4100, plan_sha: str = "p", deaths: Optional[Dict[str, Any]] = None, rows: int = 5) -> Dict[str, Any]:
    return {"arm": arm, "final_hash": final_hash, "ticks": ticks, "plan_sha256": plan_sha, "row_count": rows, "legality_calls_in_window": 3, "death_records": deaths or {}, "offset_drift": False}


DEATH = {"47": {"first_seen_tick": 3553, "record": {"cause": "STARVATION", "tick": 3553, "last_attacker_id": None, "hazard_kind": None}}}
EXPECT = [{"seed": 42, "id": 47, "tick": 3553, "cause": "STARVATION"}]


def test_new_s42_wolf_dead_of_starvation_at_the_expected_tick_is_valid_and_base_alive_is_context() -> None:
    assert run.check_cell(doc(deaths=DEATH), doc(), "new", 42, "p", EXPECT, False)["valid"]
    assert run.check_cell(doc("base"), doc("base"), "base", 42, "p", EXPECT, False)["valid"]            # BASE alive: not judged


@pytest.mark.parametrize("deaths,fragment", [({}, "holds no death record"), ({"47": {"first_seen_tick": 3600, "record": {"cause": "STARVATION", "tick": 3599}}}, "STARVATION at t3599"),
                                             ({"47": {"first_seen_tick": 3553, "record": {"cause": "COMBAT", "tick": 3553}}}, "COMBAT at t3553")])
def test_new_s42_wolf_not_dead_of_starvation_at_t3553_is_void_with_what_the_run_holds(deaths: Dict[str, Any], fragment: str) -> None:
    verdict = run.check_cell(doc(deaths=deaths), doc(), "new", 42, "p", EXPECT, False)
    assert not verdict["valid"] and any(fragment in reason for reason in verdict["reasons"]), verdict


def test_a_plan_sha256_mismatch_a_twin_hash_mismatch_and_zero_rows_are_void_and_the_legacy_s42_legality_rule_is_off_for_this_plan() -> None:
    assert not run.check_cell(doc(plan_sha="x", deaths=DEATH), doc(), "new", 42, "p", EXPECT, False)["valid"]
    assert not run.check_cell(doc(final_hash="a", deaths=DEATH), doc(final_hash="b"), "new", 42, "p", EXPECT, False)["valid"]
    assert not run.check_cell(doc(rows=0, deaths=DEATH), doc(), "new", 42, "p", EXPECT, False)["valid"]
    no_calls = {**doc(deaths=DEATH), "legality_calls_in_window": 0}
    assert run.check_cell(no_calls, doc(), "new", 42, "p", EXPECT, False)["valid"] and not run.check_cell(no_calls, doc(), "new", 42, "p", EXPECT, True)["valid"]


def test_the_check_reads_the_same_runs_plain_twin_and_pins_the_plan(tmp_path: Path) -> None:
    plan = run.build_plan("w", [run.parse_subject("42:47:0:10")], EXPECT)
    for mode in ("plain", "spy"):
        (tmp_path / f"new__w__s42__{mode}.json").write_text(json.dumps(doc(deaths=DEATH if mode == "spy" else None, plan_sha=plan["plan_sha256"])), encoding="utf-8")
    items = [i for i in run.items_for("cells", "w", [42], 4100) if i["arm"] == "new"]
    assert run.check_all(tmp_path, tmp_path, "w", items, plan["plan_sha256"], plan["expect_deaths"], False)["all_valid"]
    assert not run.check_all(tmp_path, tmp_path, "w", items, "other", plan["expect_deaths"], False)["all_valid"]


def test_the_wolf_run_is_eight_processes_plain_then_spy_per_arm_and_seed_new_first() -> None:
    items = run.items_for("wolf", "w", [42, 45], 4100)
    assert [(i["arm"], i["seed"], i["mode"]) for i in items] == [("new", 42, "plain"), ("new", 42, "spy"), ("new", 45, "plain"), ("new", 45, "spy"),
                                                                ("base", 42, "plain"), ("base", 42, "spy"), ("base", 45, "plain"), ("base", 45, "spy")] and {i["ticks"] for i in items} == {4100}


# --------------------------------------------------------------------------------------------- 4. the summary: FRIENDLY_FIRE_ILLEGAL on NEW only
def legal_row(tick: int, target: int, reason: str, attacker: int = 47, legal: bool = False) -> Dict[str, Any]:
    return {"tick": tick, "attacker_id": attacker, "target_id": target, "legal": legal, "reason": reason}


def test_a_planted_new_only_friendly_fire_row_is_surfaced_with_what_base_holds_at_that_key() -> None:
    new = {"legality_rows": [legal_row(3000, 9, FF), legal_row(3001, 9, FF), legal_row(3002, 9, "OK", legal=True)]}
    base = {"legality_rows": [legal_row(3000, 9, "OK", legal=True), legal_row(3002, 9, "OK", legal=True)]}                  # BASE has a call at 3000, none at 3001
    result = summary.friendly_fire_new_only(new, base, 47)
    assert result["new_friendly_fire_rows"] == 2 and result["new_only_count"] == 2 and result["new_only_with_no_base_call_at_key"] == 1
    assert result["new_only"] == [{"tick": 3000, "target_id": 9, "base_at_key": [{"legal": True, "reason": "OK"}]}, {"tick": 3001, "target_id": 9, "base_at_key": []}]


def test_a_friendly_fire_row_that_base_also_has_at_the_same_target_and_tick_is_not_new_only() -> None:
    new = {"legality_rows": [legal_row(3000, 9, FF), legal_row(3005, 9, "OUT_OF_RANGE")]}                                    # one FF row; a different reason is no FF row at all
    base = {"legality_rows": [legal_row(3000, 9, FF)]}
    result = summary.friendly_fire_new_only(new, base, 47)
    assert result["new_friendly_fire_rows"] == 1 and result["new_only"] == [] and result["new_only_count"] == 0
    assert summary.friendly_fire_new_only({"legality_rows": [legal_row(1, 9, FF, attacker=12)]}, {"legality_rows": []}, 47)["new_friendly_fire_rows"] == 0      # another attacker's row is not the subject's


def spy_cell(arm: str, rows: List[Dict[str, Any]], legality: List[Dict[str, Any]], hits: Optional[Dict[str, Any]] = None, deaths: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"arm": arm, "rows": rows, "legality_rows": legality, "hits_taken": hits or {}, "death_records": deaths or {}, "final_hash": "h"}


def wolf_row(tick: int, hunger: float = 50.0, hp: int = 30, hunting: Optional[int] = None, ways: tuple = (), counter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    steps = {"FORAGE": {"available": False}, "SCAVENGE": {"available": False}, "HUNT": {"available": hunting is not None, "target_entity_id": hunting}}
    return {"tick": tick, "id": 47, "before": {"payload": {"target_id": hunting} if hunting is not None else {}, "strategic": {"objective": None}}, "after": {"present": True, "alive": True, "hp": hp, "needs": {"hunger": hunger}},
            "ways": {"ways": list(ways), "open_food_steps": ["HUNT"] if hunting is not None else [], "steps": steps, "carcasses": []}, "counterparts": counter or {}}


def test_the_summary_surfaces_the_planted_row_in_the_json_and_the_text_and_has_no_verdict_line(tmp_path: Path) -> None:
    plan = run.build_plan("w", [run.parse_subject("42:47:0:500")], [])
    rows = [wolf_row(t, hunting=9 if t >= 100 else None, ways=("HUNT_EAT_RAW",) if t >= 100 else ()) for t in range(90, 130)]
    (tmp_path / "new__w__s42__spy.json").write_text(json.dumps(spy_cell("new", rows, [legal_row(3000, 9, FF)])), encoding="utf-8")
    (tmp_path / "base__w__s42__spy.json").write_text(json.dumps(spy_cell("base", rows, [legal_row(3000, 9, "OK", legal=True)])), encoding="utf-8")
    document = summary.summarize(tmp_path, plan, "w")
    assert document["subjects"]["s42/47"]["friendly_fire"]["new_only_count"] == 1
    text = summary.render(document)
    assert "absent on BASE at the same (target, tick): 1" in text and "t3000 target 9 BASE at that key" in text
    assert "verdict" not in text.lower() and not any(word in text.lower() for word in ("reading (a)", "reading (b)", "exposed holds", "regression holds"))      # the only prose is the disclaimer


def test_ways_runs_curves_attempts_and_hits_by_source_are_computed_per_arm() -> None:
    rows = [wolf_row(t, hunger=t / 10, hp=40 if t < 120 else 36, hunting=9 if 100 <= t < 110 else None, ways=("HUNT_EAT_RAW",) if 100 <= t < 110 else ()) for t in range(90, 131)]
    legality = [legal_row(100, 9, FF), legal_row(101, 9, FF), legal_row(102, 9, "OUT_OF_RANGE"), legal_row(103, 9, "OK", legal=True), legal_row(104, 8, "OK", legal=True)]
    hits = {"47": [{"tick": 120, "hit_tick": 120, "attackers": [9], "damages": [4], "hp_delta": 4}, {"tick": 125, "hit_tick": 125, "attackers": [9, 8], "damages": [3, 1], "hp_delta": 4}]}
    view = summary.arm_view(spy_cell("new", rows, legality, hits), 47)
    assert [(r["from"], r["to"], r["value"]["ways"]) for r in view["ways"]] == [(90, 99, []), (100, 109, ["HUNT_EAT_RAW"]), (110, 130, [])]
    assert view["attempts"] == {"9": {"calls": 4, "legal": 1, "illegal": 3, "reasons": {FF: 2, "OUT_OF_RANGE": 1, "OK": 1}}, "8": {"calls": 1, "legal": 1, "illegal": 0, "reasons": {"OK": 1}}}
    assert view["hits_taken"] == {"9": {"hits": 2, "damage": 7, "first_tick": 120, "last_tick": 125}, "8": {"hits": 1, "damage": 1, "first_tick": 125, "last_tick": 125}}
    assert view["curves"]["hp_min"] == 36 and view["curves"]["hunger_max"] == 13.0 and view["curves"]["points"][0][0] == 90 and view["curves"]["points"][-1][0] == 130


# --------------------------------------------------------------------------------------------- 5. the hunt-end classifier
def hunt_rows(last: int = 110, target: int = 9, counter_after: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    rows = [wolf_row(t, hunting=target if t <= last else None, counter={str(target): {"present": True, "alive": True, "manhattan": 3.0}}) for t in range(90, 131)]
    for row in rows:
        if counter_after is not None and row["tick"] > last:
            row["counterparts"] = {str(target): counter_after}
    return rows


def test_hunt_end_prey_dead() -> None:
    verdict = summary.classify_hunt_end(hunt_rows(counter_after={"present": True, "alive": False, "manhattan": 0.0}), [], [], 47)
    assert (verdict["end"], verdict["last_hunt_tick"], verdict["target"]) == ("prey_dead", 110, 9)


def test_hunt_end_prey_removed_counts_as_dead_and_beats_a_refusal() -> None:
    verdict = summary.classify_hunt_end(hunt_rows(counter_after={"present": False}), [legal_row(108, 9, FF)], [], 47)
    assert verdict["end"] == "prey_dead" and verdict["flags"]["refused"] == [{"tick": 108, "reason": FF}]


def test_hunt_end_hunt_refused_when_the_last_call_at_the_target_is_illegal() -> None:
    verdict = summary.classify_hunt_end(hunt_rows(), [legal_row(104, 9, "OK", legal=True), legal_row(109, 9, FF)], [], 47)
    assert verdict["end"] == "hunt_refused" and verdict["flags"]["last_call_at_target"] == FF
    legal_last = summary.classify_hunt_end(hunt_rows(), [legal_row(105, 9, FF), legal_row(109, 9, "OK", legal=True)], [], 47)
    assert legal_last["end"] == "unknown"                                      # an earlier refusal followed by a legal call is not the end


def test_hunt_end_prey_struck_back_and_a_blow_outside_the_lookaround_does_not_count() -> None:
    hit = [{"tick": 112, "hit_tick": 112, "attackers": [9], "damages": [4], "hp_delta": 4}]
    assert summary.classify_hunt_end(hunt_rows(), [], hit, 47)["end"] == "prey_struck_back"
    far = [{"tick": 112 + summary.HUNT_LOOKAROUND + 1, "hit_tick": 1, "attackers": [9], "damages": [4], "hp_delta": 4}]
    assert summary.classify_hunt_end(hunt_rows(), [], far, 47)["end"] == "unknown"
    assert summary.classify_hunt_end(hunt_rows(), [], [{"tick": 112, "hit_tick": 112, "attackers": [8], "damages": [4], "hp_delta": 4}], 47)["end"] == "unknown"     # another body's blow


def test_hunt_end_out_of_range_or_fled_and_unknown() -> None:
    assert summary.classify_hunt_end(hunt_rows(counter_after={"present": True, "alive": True, "manhattan": summary.HUNT_RADIUS + 1}), [], [], 47)["end"] == "out_of_range_or_fled"
    assert summary.classify_hunt_end(hunt_rows(counter_after={"present": True, "alive": True, "manhattan": summary.HUNT_RADIUS}), [], [], 47)["end"] == "unknown"


def test_a_subject_that_never_hunted_has_no_hunt_rows_and_the_last_of_two_hunts_is_the_one_classified() -> None:
    assert summary.classify_hunt_end([wolf_row(t) for t in range(5)], [], [], 47)["end"] == "no_hunt_rows"
    rows = [wolf_row(t, hunting=9) for t in range(90, 100)] + [wolf_row(t, hunting=11) for t in range(100, 105)]
    assert summary.classify_hunt_end(rows, [], [], 47)["target"] == 11


def test_a_creature_the_hunt_step_names_but_the_task_does_not_target_is_not_a_hunt() -> None:
    row = wolf_row(100, hunting=9)
    row["before"]["payload"] = {"target_id": 4}
    assert summary.hunt_target(row) is None
    row["before"]["strategic"] = {"objective": {"target_entity_id": 9}}
    assert summary.hunt_target(row) == 9                                       # the objective names the same creature: a hunt


# --------------------------------------------------------------------------------------------- 6. the folded fixes
def make_tree(tmp_path: Path) -> Path:
    tree = tmp_path / "frozen"
    (tree / "src" / "core").mkdir(parents=True)
    (tree / "src" / "core" / "calendar.py").write_text("def is_night(world_time):\n    return world_time % 2 == 1\n", encoding="utf-8")
    return tree


def snapshot_tree(tree: Path) -> List[str]:
    return sorted(str(p.relative_to(tree)) for p in tree.rglob("*"))


LOAD = ("import sys\nfrom pathlib import Path\nfrom tools.rpg_measure import person_attack_summary as s\n"
        "assert sys.dont_write_bytecode is False, 'the control must start with bytecode writing ON'\n"
        "fn, sha = s.load_is_night(Path(sys.argv[1]) / 'src' / 'core' / 'calendar.py')\nassert fn(3) is True and len(sha) == 64\nassert sys.dont_write_bytecode is False, 'the caller value must be restored'\n")
PLAIN_LOAD = ("import importlib.util, sys\nfrom pathlib import Path\nassert sys.dont_write_bytecode is False\npath = Path(sys.argv[1]) / 'src' / 'core' / 'calendar.py'\n"
              "spec = importlib.util.spec_from_file_location('_plain_load', path)\nmodule = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(module)\n")


def caller_env() -> Dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
    return {**env, "PYTHONPATH": str(ROOT)}


def test_the_bytecode_control_the_environment_writes_a_pyc_when_a_plain_load_is_used(tmp_path: Path) -> None:      # the positive control: this is what the OLD loader did
    tree = make_tree(tmp_path)
    done = subprocess.run([sys.executable, "-c", PLAIN_LOAD, str(tree)], capture_output=True, text=True, env=caller_env())
    assert done.returncode == 0, done.stderr
    assert any(p.endswith(".pyc") for p in snapshot_tree(tree)), snapshot_tree(tree)


def test_load_is_night_leaves_the_frozen_tree_byte_identical_whatever_the_callers_bytecode_setting(tmp_path: Path) -> None:      # fails on the old loader (shown in the build report)
    tree = make_tree(tmp_path)
    before = snapshot_tree(tree)
    done = subprocess.run([sys.executable, "-c", LOAD, str(tree)], capture_output=True, text=True, env=caller_env())
    assert done.returncode == 0, done.stderr
    assert snapshot_tree(tree) == before and not list(tree.rglob("__pycache__"))


def test_the_spy_child_and_the_runner_never_let_a_pyc_land_in_a_frozen_tree() -> None:
    assert run.child_env(Path("/t"), Path("/o"))["PYTHONDONTWRITEBYTECODE"] == "1"
    source = (KIT / "subject_trace_spy.py").read_text(encoding="utf-8")
    assert source.index("sys.dont_write_bytecode = True") < source.index("from src.engine.checkpoint")        # set BEFORE the first import from the tree


def test_the_motive_reads_docstring_no_longer_says_source_is_never_passed() -> None:
    text = (KIT / "person_attack_spy.py").read_text(encoding="utf-8")
    assert "``source`` is never passed" not in text and "relation_source" in text


def test_the_end_wall_is_the_processs_own_time_in_both_launchers() -> None:
    for name in ("subject_trace_launch.sh", "wolf_starve_launch.sh"):
        text = (KIT / name).read_text(encoding="utf-8")
        assert 'wall=$(( $(date +%s)-P0 ))s' in text and "P0=$(date +%s)" in text and 'wall=$(( $(date +%s)-T0 ))s' not in text, name
    assert 'wall=$(( $(date +%s)-S0 ))s' in (KIT / "person_attack_launch.sh").read_text(encoding="utf-8")       # it was already per process there


# --------------------------------------------------------------------------------------------- 6b. the heavy check: pinned processes
def fake_proc(root: Path, pid: int, ppid: int, cpus: str, args: str) -> None:
    entry = root / str(pid)
    entry.mkdir(parents=True)
    (entry / "status").write_text(f"Name:\tx\nPPid:\t{ppid}\nCpus_allowed_list:\t{cpus}\n", encoding="utf-8")
    (entry / "cmdline").write_bytes(args.replace(" ", "\0").encode())


def test_the_pinned_check_catches_an_obs_cost_arm_shaped_process_and_ignores_the_rest(tmp_path: Path) -> None:
    root = tmp_path / "proc"
    root.mkdir()
    everything = set(range(6))
    fake_proc(root, 900, 1, "4-5", "/usr/bin/python3 /data/vboxuser/perf_runs/obs_kit/obs_cost_arm.py --arm a")          # the shape that slipped through the name check
    fake_proc(root, 901, 1, "0-5", "python3 something_unpinned.py")                                                      # runs anywhere: no claim on cpus 4-5
    fake_proc(root, 902, 1, "0-3", "python3 other_cpus.py")                                                               # pinned, but elsewhere
    fake_proc(root, 903, 2, "4", "kworker/4:0")                                                                           # a kernel thread (parent 2)
    fake_proc(root, 904, 1, "4-5", "")                                                                                    # no command line
    found = pinned_check.pinned_processes({4, 5}, proc_root=root, skip=[], everything=everything)
    assert [f["pid"] for f in found] == [900] and "obs_cost_arm.py" in found[0]["args"]


def test_the_pinned_check_skips_the_callers_own_shell_chain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "proc"
    root.mkdir()
    me = os.getpid()
    fake_proc(root, me, 700, "4-5", "python3 pinned_check.py")                                                          # this process, pinned like its launcher
    fake_proc(root, 700, 600, "4-5", "bash launcher.sh")                                                                 # its shell
    fake_proc(root, 600, 1, "4-5", "systemd-run --scope")                                                                # its ancestor
    fake_proc(root, 901, 1, "4-5", "python3 other.py")                                                                   # a stranger
    assert [f["pid"] for f in pinned_check.pinned_processes({4, 5}, proc_root=root, everything=set(range(6)))] == [901]


@pytest.mark.skipif(len(os.sched_getaffinity(0)) < 2, reason="needs two cpus to pin a child to a strict subset")
def test_the_pinned_check_sees_a_real_pinned_process_and_never_its_own_pinned_shell(tmp_path: Path) -> None:
    cpus = sorted(os.sched_getaffinity(0))
    target = cpus[-1]

    def pin() -> None:
        os.sched_setaffinity(0, {target})

    stranger = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", "obs_cost_arm.py"], preexec_fn=pin)
    try:
        time.sleep(0.3)
        found = subprocess.run([sys.executable, "-B", str(KIT / "pinned_check.py"), "--cpus", str(target)], capture_output=True, text=True)
        assert found.returncode == 1 and f"pid={stranger.pid} " in found.stdout and "obs_cost_arm.py" in found.stdout, found.stdout
        # the checker's own launcher shell is pinned to the same cpu: it is an ancestor, so it is never reported
        shell = subprocess.run(["bash", "-c", f'python3 -B "{KIT / "pinned_check.py"}" --cpus {target}; echo "SHELL=$$"'], capture_output=True, text=True, preexec_fn=pin)
        shell_pid = shell.stdout.split("SHELL=")[1].strip()
        assert f"pid={shell_pid} " not in shell.stdout and f"pid={stranger.pid} " in shell.stdout, shell.stdout
    finally:
        stranger.kill()
        stranger.wait()


def test_both_launchers_run_the_pinned_check_in_the_preflight_and_before_every_process() -> None:
    for name in ("subject_trace_launch.sh", "wolf_starve_launch.sh", "person_attack_launch.sh"):
        text = (KIT / name).read_text(encoding="utf-8")
        assert "pinned_check.py" in text and text.count("pinned_elsewhere &&") == 2, name


# --------------------------------------------------------------------------------------------- 7. the wolf launcher
def launcher_env(tmp_path: Path) -> Path:
    env = tmp_path / "record.env"
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(run.build_plan("w", [run.parse_subject("42:47:0:10"), run.parse_subject("45:49:0:10")], [])), encoding="utf-8")
    values = {"KIT": str(ROOT), "OUT_BASE": str(tmp_path / "out"), "PLAN_FILE": str(plan), "PLAN_FILE_SHA256": "0" * 64, "PLAN_SHA256": "0" * 64, "TREE_NEW": "/trees/new", "TREE_BASE": "/trees/base",
              "SHA_NEW": "n", "SHA_BASE": "b", "PY": sys.executable, "FREEZE_SHA": "f" * 64, "WORLD": "w", "SEEDS": '"42 45"', "TICKS": "4100", "SMOKE_TICKS": "300"}
    env.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    return env


def test_the_wolf_dry_run_prints_eight_processes_and_the_smoke_prints_two(tmp_path: Path) -> None:
    env = launcher_env(tmp_path)
    dry = {**os.environ, "LAUNCH_DRY_RUN": "1"}
    wolf = subprocess.run(["bash", str(WOLF_LAUNCH), str(env), "1", "wolf"], capture_output=True, text=True, env=dry, cwd=tmp_path, check=True).stdout.splitlines()
    smoke = subprocess.run(["bash", str(WOLF_LAUNCH), str(env), "1", "smoke"], capture_output=True, text=True, env=dry, cwd=tmp_path, check=True).stdout.splitlines()
    shape = lambda c: (c.split("--arm ")[1].split()[0], c.split("--seed ")[1].split()[0], c.split("--mode ")[1].split()[0], c.split("--ticks ")[1].split()[0])      # noqa: E731
    assert [shape(c) for c in wolf] == [("new", "42", "plain", "4100"), ("new", "42", "spy", "4100"), ("new", "45", "plain", "4100"), ("new", "45", "spy", "4100"),
                                        ("base", "42", "plain", "4100"), ("base", "42", "spy", "4100"), ("base", "45", "plain", "4100"), ("base", "45", "spy", "4100")]
    assert all("MemoryMax=3G" in c and "taskset -c 4-5" in c and "--plan " in c for c in wolf)
    assert [shape(c) for c in smoke] == [("new", "42", "plain", "300"), ("new", "42", "spy", "300")]


def test_the_wolf_launcher_refuses_a_plan_file_that_differs_from_the_record_before_any_process(tmp_path: Path) -> None:
    env = launcher_env(tmp_path)
    done = subprocess.run(["bash", str(WOLF_LAUNCH), str(env), "GO-1", "smoke"], capture_output=True, text=True, cwd=tmp_path)
    log = (tmp_path / "out" / "smoke" / "launcher.log").read_text(encoding="utf-8")
    assert done.returncode == 3 and "ABORT" in log and not (tmp_path / "out" / "smoke" / "cells").exists()


def test_every_kit_python_call_in_the_wolf_launcher_goes_through_kitpy_and_a_failed_record_is_never_complete() -> None:
    text = (KIT / "wolf_starve_launch.sh").read_text(encoding="utf-8")
    calls = [ln for ln in text.splitlines() if '"$PY"' in ln and not ln.lstrip().startswith("#") and "kitpy()" not in ln and "SCOPE_CMD=" not in ln and "uv pip freeze" not in ln and not ln.lstrip().startswith("kitpy ")]
    assert calls == [] and "RECORD_NOT_WRITTEN" in text and "RC=6" in text and "SUMMARY_NOT_WRITTEN" in text
