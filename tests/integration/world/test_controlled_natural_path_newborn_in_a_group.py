# Compliance IDs: WORLD-122
"""CONTROLLED NATURAL-PATH coverage (rpg-designer-ubuntu's ruling of 2026-11-18, Q-N1..Q-N4): a mother already in a live group, a pregnancy built by births' own conception code, and the birth,
and any group the newborn forms, and everything after, made by the ENGINE. It is not full lifecycle evidence and not the natural run (the S9 cells); the synthetic fallback is the CHILD-in-group test beside it.

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
A C3 is a BLOCK; a newborn C1/C2 in a group without a TYPED dissolution (dissolution_tick set) is a FINDING, and a newborn group that vanishes untyped is a FINDING.
C3 is read from the kernel state every tick for each newborn and each watched id, independent of group membership (the spy only has rows for members of a live group, so an ungrouped newborn has none):
hunger >= STARVING_LINE or death by STARVATION is a BLOCK; each newborn must have >= 201 reads or a typed death (its cause is reported). The checker is a pure function (``violations``) positive-controlled below with planted rows.

Natural-run in-group evidence is NOT this test: S9 cell 2 (s9-56dd071ea-002, urban_political s42 5000t) has the human CHILD 31 (mother 2) in 6 formation groups over 469 grouped ticks, no C1/C2/C3,
validated by rpg-planner-ubuntu's row cross-check. This test is the controlled arm only; it is not full lifecycle evidence. It stays a CONTROLLED NATURAL-PATH row, separate from the natural-run
evidence (owner rule, #715 6971915608).

Litter leg (rpg-designer-ubuntu, ruling (c) of 2026-11-18): at least one newborn must be ALIVE at the end with the full W+1 = 201 reads and no C3 (``litter_blocks``); a litter that all dies early by a
typed non-starvation death passes ``needs_blocks`` per newborn but FAILS this leg.

Guard leg, NOT claimed as tested coverage: the mother's-group leg has almost no data on this set-up. The parents 24 and 26 died of COMBAT at t124 and t122 (2 and 4 reads), so the watched-member check is
a guard, near-vacuous here. The deaths are disclosed, not called unrelated: a control without the pregnancy write (same kernel, world, seed, ticks) shows 24 and 26 still die of COMBAT to humans (t137, t126),
but the runs diverge from about t111, after the pregnancy write at t90, so the pregnancy shifts who kills the parents and when (an expected consequence: a pregnant body behaves differently and leaves the
pool). Evidence: /data/vboxuser/births-runs/control-combat-7a76f4a35/ with its SHA256SUMS. The watched members' read counts are printed in MEASURED.
Determinism: the WHOLE facts dict (final state hash, outcome, groups, needs reads, counts) is equal under PYTHONHASHSEED 0 and 1 (two subprocesses of ``scenario()``).
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


def read_needs(log, state, ids):
    """Pure per-tick C3 reader over the kernel state, independent of group membership. ``log`` maps eid -> {reads, max_hunger, c3, death}; a missing body is not a read."""
    for eid in ids:
        entry = log.setdefault(eid, {"reads": 0, "max_hunger": 0.0, "c3": None, "death": None})
        body = state.entities.get(eid)
        if body is None:
            continue
        record = body.lifecycle.death_record
        cause = None if record is None else getattr(record.cause, "value", str(record.cause))
        if record is not None:
            if entry["death"] is None:
                entry["death"] = {"tick": record.tick, "cause": cause}
                entry["c3"] = entry["c3"] or ({"tick": state.tick, "hunger": body.biological.hunger, "cause": cause} if cause == "STARVATION" else None)
            continue  # a dead body is not read again: its typed death replaces the reads
        entry["reads"] += 1
        entry["max_hunger"] = max(entry["max_hunger"], body.biological.hunger)
        if entry["c3"] is None and (body.biological.hunger >= STARVING_LINE or cause == "STARVATION"):
            entry["c3"] = {"tick": state.tick, "hunger": body.biological.hunger, "cause": cause}


def needs_blocks(log, newborn_ids, window=WINDOW + 1):
    """BLOCK for any C3 in the log; BLOCK-shaped gap for a newborn with fewer than ``window`` reads and no typed death."""
    out = [("BLOCK", eid, "C3") for eid, entry in sorted(log.items()) if entry["c3"] is not None]
    out += [("GAP", eid, "reads") for eid in sorted(newborn_ids) if log.get(eid, {}).get("reads", 0) < window and log.get(eid, {}).get("death") is None]
    return out


def litter_blocks(log, newborn_ids, window=WINDOW + 1):
    """Across the litter: at least one newborn is alive (no death record) with the full ``window`` reads and no C3; otherwise one ('LITTER', 'no newborn survived the window') entry."""
    alive = [eid for eid in newborn_ids if log.get(eid, {}).get("death") is None and log.get(eid, {}).get("reads", 0) >= window and log[eid]["c3"] is None]
    return [] if alive else [("LITTER", sorted(newborn_ids), "no newborn alive with the full reads")]


def violations(hits, newborn_ids, watched, newborn_groups, typed_dissolved):
    """Pure checker. Returns the list of failures: a C3 on the newborn or any watched member (BLOCK); a C1/C2 hit in a newborn group without a typed dissolution (FINDING)."""
    out = []
    for eid, found in hits.items():
        if "C3" in found and (eid in watched or eid in newborn_ids):
            out.append(("BLOCK", eid, "C3"))
        for kind in ("C1", "C2"):
            for h in found.get(kind, []):
                if h.get("group") in newborn_groups and h.get("group") not in typed_dissolved:
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
        newborn_groups, grouped_ticks, needs = set(), 0, {}
        read_needs(needs, now, set(newborn_ids) | watched)
        while kernel.state.tick < due + WINDOW + 1:
            kernel.tick_once()
            current = kernel.state
            read_needs(needs, current, set(newborn_ids) | watched)
            in_group = False
            for gid, g in current.groups.items():
                if getattr(g, "dissolution_tick", None) is None and any(i in g.member_ids for i in newborn_ids):
                    newborn_groups.add(gid)
                    watched |= set(g.member_ids)
                    in_group = True
            grouped_ticks += in_group
        final = kernel.state
        hits = hits_by_eid(spy.rows)
        typed = {gid for gid in newborn_groups if gid in final.groups and getattr(final.groups[gid], "dissolution_tick", None) is not None}
        untyped_vanished = sorted(gid for gid in newborn_groups if gid not in final.groups)
        reasons = {str(gid): spy.group_seen.get(gid, {}).get("dissolution_reason") for gid in sorted(typed)}
        facts.update({
            "outcome": "formed_group" if newborn_groups else "ungrouped", "newborn_groups": sorted(newborn_groups), "grouped_ticks": grouped_ticks, "typed_dissolved_groups": sorted(typed), "dissolution_reasons": reasons, "untyped_vanished_groups": untyped_vanished,
            "needs": {str(k): v for k, v in sorted(needs.items())}, "watched_reads": {str(k): needs[k]["reads"] for k in sorted(watched)},
            "watched": sorted(watched), "rows_members": sorted(spy.rows), "row_count": sum(len(r) for r in spy.rows.values()), "ticks_after_birth": final.tick - due,
            "hits": {str(k): sorted(v) for k, v in hits.items()}, "final_hash": CanonicalStateHasher.get_hash(final), "final_tick": final.tick,
            "_hits": hits, "_newborn_ids": set(newborn_ids), "_watched": watched, "_newborn_groups": newborn_groups, "_dissolved": typed, "_needs": needs,
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
    assert not facts["untyped_vanished_groups"], f"FINDING: a newborn group vanished without a typed dissolution: {facts['untyped_vanished_groups']}"
    blocks = needs_blocks(facts["_needs"], facts["_newborn_ids"])
    assert not blocks, f"{blocks}: {facts['needs']}"
    assert not litter_blocks(facts["_needs"], facts["_newborn_ids"]), f"no newborn alive at the end with the full reads: {facts['needs']}"
    deaths = {e: n["death"] for e, n in facts["_needs"].items() if n["death"] is not None}
    assert all(e not in facts["_newborn_ids"] or deaths[e]["cause"] != "STARVATION" for e in deaths), deaths
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


class _Body:
    def __init__(self, hunger, record=None):
        self.biological = type("B", (), {"hunger": hunger})()
        self.lifecycle = type("L", (), {"death_record": record})()


class _State:
    def __init__(self, tick, entities):
        self.tick, self.entities = tick, entities


def test_needs_reader_positive_controls_an_ungrouped_starving_newborn_blocks():
    log = {}
    for t in range(WINDOW + 1):
        read_needs(log, _State(t, {99: _Body(0.1), 1: _Body(0.1)}), {99, 1})
    assert needs_blocks(log, {99}) == [] and log[99]["reads"] == WINDOW + 1
    log = {}
    for t in range(WINDOW + 1):
        read_needs(log, _State(t, {99: _Body(STARVING_LINE if t == 50 else 0.1)}), {99})
    assert needs_blocks(log, {99}) == [("BLOCK", 99, "C3")] and log[99]["c3"]["tick"] == 50  # starving, ungrouped, no spy rows at all
    log = {}
    record = type("R", (), {"tick": 7, "cause": type("C", (), {"value": "STARVATION"})()})()
    read_needs(log, _State(7, {99: _Body(0.1, record)}), {99})
    assert needs_blocks(log, {99}) == [("BLOCK", 99, "C3")]  # death by starvation blocks
    log = {}
    for t in range(10):
        read_needs(log, _State(t, {99: _Body(0.1)}), {99})
    assert needs_blocks(log, {99}) == [("GAP", 99, "reads")]  # too few reads and no typed death: the check is not vacuous
    log = {}
    other = type("R", (), {"tick": 7, "cause": type("C", (), {"value": "OLD_AGE"})()})()
    read_needs(log, _State(7, {99: _Body(0.1, other)}), {99})
    assert needs_blocks(log, {99}) == [] and log[99]["death"]["cause"] == "OLD_AGE" and log[99]["reads"] == 0
    assert litter_blocks(log, {99}) != []  # the litter leg: every newborn dying early by a typed non-starvation death passes needs_blocks but FAILS here
    log = {}
    for t in range(WINDOW + 1):
        read_needs(log, _State(t, {98: _Body(0.1), 99: _Body(0.1, other if t > 5 else None)}), {98, 99})
    assert litter_blocks(log, {98, 99}) == [] and needs_blocks(log, {98, 99}) == []  # one survivor with the full reads, one early typed death: passes  # a typed non-starvation death ends the reads without a gap


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
