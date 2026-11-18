# Compliance IDs: WORLD-122
"""CONTROLLED NATURAL-PATH coverage (rpg-designer-ubuntu's ruling of 2026-11-18, Q-N1..Q-N4): a mother already in a live group, a pregnancy built by births' own conception code, and the birth,
the newborn's join of a group and everything after made by the ENGINE. It is not full lifecycle evidence and not the natural run (the S9 cells); the synthetic fallback is the CHILD-in-group test beside it.

Set-up (crowded_frontier, seed 42, the pinned kernel): the engine's own cooperation phase forms the groups; at the first check tick (a multiple of 30, from 90) at which a live group holds a
goblin ADULT mother with an eligible mate, ONE PregnancyState is written. It is built by ``births._conceive`` itself, called on a read-only earlier-tick VIEW of the state
(``replace(state, tick=due - gestation_ticks)``, used only as _conceive's input) and applied UNMODIFIED through ``ApplyPath.apply_generation`` at the real set-up tick; the applied record is
asserted equal to the returned one field for field. The deliberate departure from a natural conception: ``conceived_tick`` is ``due - gestation_ticks`` and PREDATES the run, and the father's
interval expiry runs from that tick. ``due = set-up + 30``. The litter is drawn at conceived_tick with the profile's keyed draw, as at a natural conception. The reachability guard runs on the
REAL set-up state and asks births' own code (``_candidates``, the fed line, ``_past_interval``, ``_find_mate`` with ``passes_mate_gate``) exactly as a conception would. No bond, no group and no
body is edited by hand; the one hand step is assigning the apply path's result back as the kernel state.

Species and group (rpg-designer-ubuntu Q-N5 (a)): the goblin pair 24/26 in crowded_frontier's live group 10004, mate_gate none. DISCLOSURE, word for word: "the controlled natural-path test does not
cover human newborns in groups: no human pair's mutual SocialBond reaches the mate gate (FRIEND, 0.8) within the set-up window (best 0.2 at t120 in the read-only probes); the S9 5000t cell is the
natural-run row for humans." (Q-N6: a human bond cannot reach 0.8 early, so the goblin pair is the arm.)

Passes when (rpg-designer-ubuntu Read 2 (b), 2026-11-18): BirthService bears the newborn at due (G1), born + unplaced = the litter (G2), at life stage CHILD; then, for W+1 = 201 ticks after the
birth, the newborn EITHER forms a group through the engine path (GroupSystem formation) OR stays ungrouped - both outcomes pass, and the test does NOT assert a join into the mother's existing group
(no join-existing path has been seen: TCK-20261118-A-RECRUIT-OR-A-NEWBORN-NEVER-JOINS-AN-EXISTING-GROUP). In either case: no member has C3 (the newborn, and every member of the mother's group
or of any group the newborn is in), and every group the newborn is in either dissolves through its typed dissolution or has no member with C1/C2 (s9_spy's detectors, imported unchanged).
A C3 is a BLOCK; a newborn C1/C2 in a non-dissolved group is a FINDING. The checker is a pure function (``violations``) positive-controlled below with planted rows.

Natural-run in-group evidence is NOT this test: S9 cell 2 (s9-56dd071ea-002, urban_political s42 5000t) has the human CHILD 31 (mother 2) in 6 formation groups over 469 grouped ticks, no C1/C2/C3,
validated by rpg-planner-ubuntu's row cross-check. This test is the controlled arm only; it is not full lifecycle evidence.
Determinism: the final state hash is equal under PYTHONHASHSEED 0 and 1 (two subprocesses of ``scenario()``).
Budget: see the measured time in the report; marked slow if the determinism pair exceeds 60 s.
"""
import dataclasses
import json
import os
import subprocess
import sys

import pytest

from src.core.species import species_of
from src.core.state import LifeStage
from src.engine.apply import ApplyPath
from src.engine.behavior_consumers import get_catalog
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.starvation import STARVING_LINE
from src.systems.world_systems.generator import EntityGenerator
from src.world import births
from tools.rpg_measure import s9_spy
from tools.rpg_measure.s9_spy import GroupSpy, hits_by_eid
from tools.test_architecture.rpg_gate_run import build_kernel

WORLD, SEED = "crowded_frontier", 42
N_TICKS = 30  # due = set-up + N; a multiple of the 30-tick births check, <= 60
WINDOW = s9_spy.WINDOW
FIRST_SETUP_TICK, LAST_SETUP_TICK = 90, 270


TARGET_GROUP, TARGET_PAIR = 10004, (24, 26)  # crowded_frontier s42: the goblin pair in live group 10004 from tick 80 (rpg-designer-ubuntu, Q-N5 (a))


def _find_pair(state, catalog):
    """The required pair, asserted on the REAL state with births' own code: the target group is live and holds both goblins, the mother passes the fed line and the interval, and
    ``_find_mate`` (which applies W1's range, eligibility and ``passes_mate_gate``) returns the other member. Returns None when the target group is not yet live."""
    group = state.groups.get(TARGET_GROUP)
    if group is None or getattr(group, "dissolution_tick", None) is not None:
        return None
    assert set(TARGET_PAIR) <= set(group.member_ids), f"group {TARGET_GROUP} does not hold {TARGET_PAIR}: {sorted(group.member_ids)}"
    profiles = births._Profiles(catalog)
    candidates = births._candidates(state, profiles)
    for mother_id in TARGET_PAIR:
        mother = candidates.get(mother_id)
        profile = profiles.of(species_of(mother)) if mother is not None else None
        if profile is None or species_of(mother) != "goblin" or mother.biological.hunger > profile.fed_line or not births._past_interval(mother, state.tick):
            continue
        father = births._find_mate(state, mother, candidates, set(), profile)
        if father is not None and father.id in TARGET_PAIR:
            return group, mother, father, profile
    return None


def _build_pregnancy(state, mother, father, profile, catalog):
    """births._conceive on a read-only earlier-tick view; returns its update, unmodified."""
    due = state.tick + N_TICKS
    view = dataclasses.replace(state, tick=due - profile.gestation_ticks)
    check = births._Check(view, EntityGenerator.for_state(view), catalog)
    update = births._conceive(check, mother, father, profile)
    return update, update.entity_updates[mother.id].lifecycle.pregnancy_set, due


def violations(hits, newborn_ids, watched, newborn_groups, dissolved_groups):
    """Pure checker. Returns the list of failures: a C3 on the newborn or any watched member (BLOCK); a C1/C2 hit in a newborn group that did not dissolve (FINDING)."""
    out = []
    for eid, found in hits.items():
        if "C3" in found and (eid in watched or eid in newborn_ids):
            out.append(("BLOCK", eid, "C3"))
        for kind in ("C1", "C2"):
            for h in found.get(kind, []):
                if h.get("group") in newborn_groups and h.get("group") not in dissolved_groups:
                    out.append(("FINDING", eid, kind))
    return out


def scenario():
    catalog = get_catalog()
    kernel = build_kernel(WORLD, SEED, "controlled_natural_path")
    facts = {}
    spy = None
    try:
        while kernel.state.tick < FIRST_SETUP_TICK:
            kernel.tick_once()
        found = _find_pair(kernel.state, catalog)
        while found is None and kernel.state.tick < LAST_SETUP_TICK:
            for _ in range(30):
                kernel.tick_once()
            found = _find_pair(kernel.state, catalog)
        assert found is not None, f"goblin pair {TARGET_PAIR} was not a reachable mother/father in live group {TARGET_GROUP} at a check tick between 90 and 270"
        state = kernel.state
        group, mother, father, profile = found
        assert state.tick % 30 == 0
        update, pregnancy, due = _build_pregnancy(state, mother, father, profile, catalog)
        assert (pregnancy.due_tick, pregnancy.father_entity_id) == (due, father.id) and pregnancy.conceived_tick == due - profile.gestation_ticks
        assert pregnancy.litter_size in profile.litter_weights
        applied = ApplyPath.apply_generation(state, update, state.tick, state.world_time)
        assert applied.entities[mother.id].lifecycle.pregnancy == pregnancy, "the applied PregnancyState equals the one births built, field for field"
        kernel._state = applied
        spy = GroupSpy(applied).install()
        facts.update({"setup_tick": state.tick, "due": due, "mother": mother.id, "father": father.id, "group": group.id, "litter": pregnancy.litter_size, "species": species_of(mother)})
        for _ in range(due - state.tick + 1):
            kernel.tick_once()
        now = kernel.state
        newborn_ids = sorted(e.id for e in now.entities.values() if e.lifecycle.parent_a_entity_id == mother.id and e.id not in applied.entities)
        facts["newborn_ids"] = newborn_ids
        assert newborn_ids, "BirthService bore no newborn at the due tick"
        assert all(now.entities[i].identity.life_stage == LifeStage.CHILD and now.entities[i].lifecycle.birth_tick == due for i in newborn_ids), "newborns are CHILD born at due_tick (G1)"
        assert all(now.entities[i].lifecycle.parent_b_entity_id == father.id for i in newborn_ids)
        assert len(newborn_ids) <= pregnancy.litter_size
        watched = set(group.member_ids)  # the mother's group at set-up; newborn groups' members are added as they appear
        newborn_groups, grouped_ticks = set(), 0
        while kernel.state.tick < due + WINDOW + 1:
            kernel.tick_once()
            current = kernel.state
            in_group = False
            for gid, g in current.groups.items():
                if getattr(g, "dissolution_tick", None) is None and any(i in g.member_ids for i in newborn_ids):
                    newborn_groups.add(gid)
                    watched |= set(g.member_ids)
                    in_group = True
            grouped_ticks += in_group
        final = kernel.state
        hits = hits_by_eid(spy.rows)
        dissolved = {gid for gid in newborn_groups if gid not in final.groups or getattr(final.groups[gid], "dissolution_tick", None) is not None}
        facts.update({
            "outcome": "formed_group" if newborn_groups else "ungrouped", "newborn_groups": sorted(newborn_groups), "grouped_ticks": grouped_ticks, "dissolved_groups": sorted(dissolved),
            "watched": sorted(watched), "rows_members": sorted(spy.rows), "row_count": sum(len(r) for r in spy.rows.values()), "ticks_after_birth": final.tick - due,
            "hits": {str(k): sorted(v) for k, v in hits.items()}, "final_hash": CanonicalStateHasher.get_hash(final), "final_tick": final.tick,
            "_hits": hits, "_newborn_ids": set(newborn_ids), "_watched": watched, "_newborn_groups": newborn_groups, "_dissolved": dissolved,
        })
    finally:
        if spy is not None:
            spy.restore()
        kernel.shutdown()
    return facts


def test_the_engine_bears_the_newborn_and_it_forms_a_group_or_stays_ungrouped_with_no_c3():
    facts = scenario()
    assert facts["ticks_after_birth"] >= WINDOW + 1
    assert facts["outcome"] in ("formed_group", "ungrouped")
    assert facts["row_count"] > 0, "the spy recorded no member rows: the checker would pass vacuously"
    bad = violations(facts["_hits"], facts["_newborn_ids"], facts["_watched"], facts["_newborn_groups"], facts["_dissolved"])
    assert not bad, f"{bad}: {facts['hits']}"
    print("MEASURED", {k: v for k, v in facts.items() if not k.startswith("_")})


def _rows(eid, group, n, progress, hunger=0.1, start=1000):
    return [{"tick": start + i, "group": group, "goal_changed": False, "task_changed": False, "moved": progress, "completed": 0, "consumed": False, "attacked": False, "failed": [],
             "hunger": hunger, "starved": False, "life_stage": "CHILD"} for i in range(n)]


def _check(rows_by_eid, dissolved=()):
    hits = hits_by_eid(rows_by_eid)
    return violations(hits, {99}, {1, 2, 99}, {7}, set(dissolved)), hits


def test_checker_positive_controls_planted_failures_fail_and_clean_or_dissolved_pass():
    ok, hits = _check({99: _rows(99, 7, 201, True), 1: _rows(1, 7, 201, True)})
    assert ok == [] and hits == {}
    c3, hits = _check({1: _rows(1, 7, 5, True, hunger=STARVING_LINE)})  # a planted starving mother's-group member
    assert ("BLOCK", 1, "C3") in c3, hits
    c3n, _ = _check({99: _rows(99, 7, 5, True, hunger=STARVING_LINE)})  # a planted starving newborn
    assert ("BLOCK", 99, "C3") in c3n
    stuck, hits = _check({1: _rows(1, 7, 201, False)})  # a planted non-progressing member for 201 ticks
    assert ("FINDING", 1, "C1") in stuck, hits
    assert _check({1: _rows(1, 7, 201, False)}, dissolved=[7])[0] == []  # same rows, group dissolved typed: passes
    assert _check({1: _rows(1, 8, 201, False)})[0] == []  # a stuck member in a group the newborn is not in is out of this check's scope
    assert _check({1: _rows(1, 7, 199, False)})[0] == []  # one short of the window: no hit
    print("POSITIVE-CONTROL c3_block=%d stuck_finding=%d" % (len(c3), len(stuck)))


@pytest.mark.slow
def test_the_scenario_is_deterministic_under_two_python_hash_seeds():
    code = "import json; from tests.integration.world.test_controlled_natural_path_newborn_in_a_group import scenario; f = scenario(); print(json.dumps({k: v for k, v in f.items() if not k.startswith('_')}, sort_keys=True))"
    outs = []
    for seed in ("0", "1"):
        proc = subprocess.run([sys.executable, "-c", code], env={**os.environ, "PYTHONHASHSEED": seed, "PYTHONPATH": os.getcwd()}, capture_output=True, text=True, cwd=os.getcwd())
        assert proc.returncode == 0, proc.stderr[-600:]
        outs.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    assert outs[0] == outs[1], f"scenario facts differ between PYTHONHASHSEED 0 and 1: {outs[0]} vs {outs[1]}"
    print("DETERMINISM", outs[0]["final_hash"], outs[0]["outcome"])
