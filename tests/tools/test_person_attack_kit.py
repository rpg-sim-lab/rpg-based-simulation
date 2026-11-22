"""Planted controls for the person-attack trace kit (tools/rpg_measure/person_attack_*): the engagement split at gaps 50 and 51, every rule R1-R7 with one firing and one non-firing case, the period
table (period_unknown is never defaulted), the spy seeing attacks (and its counting cross-check against the real ledger's own counting shape), the twin-hash check, the runner's plan and its interpreter
void, the frozen-tree proof, and the launcher's self-match-proof heavy check. Unit level only: no simulation is run."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest

from src.core.updates import StateUpdate
from tools.rpg_measure import person_attack_run as run
from tools.rpg_measure import person_attack_spy as spy_module
from tools.rpg_measure import person_attack_summary as summary
from tools.rpg_measure import person_attack_tree_check as tree_check

ROOT = Path(__file__).resolve().parents[2]
NIGHT = lambda world_time: world_time % 2400 >= 1800 or world_time % 2400 < 600  # noqa: E731  (the injected stand-in; the real one is loaded from calendar.py in a test below)
DAY_TICK, NIGHT_TICK = 1000, 2000


def row(tick: int, attacker: int = 1, victim: int = 100, hit: bool = True, species: str = "wolf", diet: Optional[List[str]] = None, group: Optional[str] = None, o3: bool = True, **kw: Any) -> Dict[str, Any]:
    diet = ["meat"] if diet is None else diet
    base = {
        "tick": tick, "world_time": kw.pop("world_time", tick), "attacker_id": attacker, "attacker_kind": species, "attacker_species": species, "attacker_group": group or "+".join(diet) or "none",
        "attacker_diet": diet, "attacker_person": 0, "in_o3_group": o3, "victim_id": victim, "victim_kind": "human", "victim_species": "human", "hit": hit, "hp_delta": -1 if hit else 0,
        "outcome_kind": "SURVIVE", "victim_alive_after": True, "victim_asleep_before": False, "victim_lodged_before": False, "victim_mode_before": "WANDER", "victim_mode_after": "WANDER",
        "victim_attacked_same_tick": False, "attacker_mode_after": "WANDER", "hit_attackers": [],
    }
    return {**base, **kw}


def engagements_of(rows: List[Dict[str, Any]], mode_rows: Optional[List[Dict[str, Any]]] = None, final_tick: int = 100_000) -> List[Dict[str, Any]]:
    return summary.build_engagements(rows, mode_rows or [], final_tick, NIGHT)


def filler(n: int = 10, start: int = 50_000) -> List[Dict[str, Any]]:
    """n single-hit engagements by n distinct day-active-in-night wolves (nocturnal, at a night tick) on n distinct victims, spread so no other rule is stressed."""
    return [row(start + i * 5000 + 2000 - (start + i * 5000) % 2400, attacker=500 + i, victim=600 + i) for i in range(n)]


def rules(rows: List[Dict[str, Any]], mode_rows: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Dict[str, Any]]:
    return summary.rules_for_cell(rows, mode_rows or [], engagements_of(rows, mode_rows))


# --------------------------------------------------------------------------------------------- engagement split
@pytest.mark.parametrize("second_tick,expected", [(50, 1), (51, 2)])
def test_engagement_gap_of_50_stays_and_51_opens_a_new_one(second_tick: int, expected: int) -> None:
    assert len(engagements_of([row(0), row(second_tick)])) == expected


def test_engagement_counts_hits_and_misses_apart_and_only_o3_rows() -> None:
    eng = engagements_of([row(0), row(10, hit=False), row(20), row(30, o3=False, attacker=9)])
    assert [(e["events"], e["hits"], e["misses"]) for e in eng] == [(3, 2, 1)]


def test_engagement_outcomes_and_the_run_end() -> None:
    assert engagements_of([row(0, victim_alive_after=False)])[0]["outcome"] == "victim_killed"
    assert engagements_of([row(0, victim_mode_after="RETREAT")])[0]["outcome"] == "victim_fled"
    assert engagements_of([row(0, attacker_mode_after="RETREAT")])[0]["outcome"] == "attacker_fled"
    assert engagements_of([row(0)], final_tick=30)[0]["outcome"] == "unresolved_at_end"
    assert engagements_of([row(0)], final_tick=10_000)[0]["outcome"] == "disengaged"
    assert engagements_of([row(0)], [{"tick": 40, "id": 100, "mode": "RETREAT", "first": False}])[0]["outcome"] == "victim_fled"


# --------------------------------------------------------------------------------------------- the period table and the night instrument
def test_period_mapping_and_period_unknown_is_never_defaulted() -> None:
    assert summary.inside_period("human", night=False) is True and summary.inside_period("human", night=True) is False
    assert summary.inside_period("wolf", night=True) is True and summary.inside_period("wolf", night=False) is False
    assert summary.inside_period("slime", night=False) is True and summary.inside_period("spirit", night=True) is True
    assert summary.inside_period("basilisk", night=True) is None


def test_the_real_night_instrument_is_loaded_from_a_calendar_file_by_path() -> None:
    is_night, sha = summary.load_is_night(ROOT / "src" / "core" / "calendar.py")
    assert len(sha) == 64
    assert [is_night(t) for t in (1799, 1800, 2399, 2400, 599, 600, 2400 + 1800, 2400 + 600)] == [False, True, True, True, True, False, True, False]


# --------------------------------------------------------------------------------------------- R1-R5 (one firing and one non-firing case each; >= 10 engagements so they apply)
def spaced(n: int, attacker: int = 1, species: str = "wolf", world_time_of: Any = None, diet: Optional[List[str]] = None, group: Optional[str] = None, victims: bool = True) -> List[Dict[str, Any]]:
    """n engagements of one attacker on n distinct victims, 3000 ticks apart (so no rolling-window or pair rule fires), each at a night tick unless world_time_of says otherwise."""
    return [row(i * 3000, attacker=attacker, victim=100 + (i if victims else 0), species=species, world_time=(world_time_of(i) if world_time_of else i * 3000 // 2400 * 2400 + NIGHT_TICK), diet=diet, group=group)
            for i in range(n)]


def test_R1_fires_when_a_meat_group_attacker_declares_no_meat_diet_and_passes_on_meat() -> None:
    bad = rules(spaced(10, diet=["plant"], group="meat"))["R1"]   # the group says meat, the declared diet does not
    assert (bad["result"], bad["attacker_ids"]) == ("FAIL", [1])
    assert rules(spaced(10))["R1"]["result"] == "PASS"
    assert rules(spaced(10, diet=["meat", "plant"], group="meat"))["R1"]["result"] == "FAIL"   # group and diet disagree: a metric-grouping finding


def test_R2_fires_above_half_of_the_engagements_and_passes_at_exactly_half() -> None:
    six = spaced(6, attacker=1) + spaced(4, attacker=2)
    five = spaced(5, attacker=1) + spaced(5, attacker=2)
    assert (rules(six)["R2"]["result"], rules(six)["R2"]["attacker_ids"]) == ("FAIL", [1])
    assert rules(five)["R2"]["result"] == "PASS"


def test_R3_fires_on_more_than_three_engagements_in_2400_ticks_and_passes_on_three() -> None:
    close = lambda n: [row(i * 200, victim=100 + i, world_time=2000 + i * 200) for i in range(n)]  # noqa: E731
    four = close(4) + spaced(6, attacker=2, world_time_of=lambda i: 10_000 + i * 3000 + 2000 - (10_000 + i * 3000) % 2400)
    three = close(3) + spaced(7, attacker=2, world_time_of=lambda i: 10_000 + i * 3000 + 2000 - (10_000 + i * 3000) % 2400)
    assert (rules(four)["R3"]["result"], rules(four)["R3"]["attacker_ids"]) == ("FAIL", [1])
    assert rules(three)["R3"]["result"] == "PASS"


def test_R4_fires_when_one_pair_has_five_engagements_and_passes_at_four() -> None:
    pair = lambda n: [row(i * 3000, victim=100, world_time=2000 + (i * 3000) // 2400 * 2400) for i in range(n)]  # noqa: E731
    assert rules(pair(5) + spaced(5, attacker=2))["R4"]["result"] == "FAIL"
    assert rules(pair(5) + spaced(5, attacker=2))["R4"]["pairs"] == [(1, 100, 5)]
    assert rules(pair(4) + spaced(6, attacker=2))["R4"]["result"] == "PASS"


def test_R5_fires_below_90_percent_inside_the_period_passes_above_and_reports_period_unknown_as_not_assessable() -> None:
    day = lambda i: i * 3000 // 2400 * 2400 + DAY_TICK  # noqa: E731  (wolf is nocturnal: a day tick is OUTSIDE)
    assert rules(spaced(10, world_time_of=day))["R5"]["result"] == "FAIL"
    assert rules(spaced(10, world_time_of=day))["R5"]["attacker_ids"] == [1]
    assert rules(spaced(10))["R5"]["result"] == "PASS"
    nine_in = spaced(9) + spaced(1, attacker=2, world_time_of=lambda i: DAY_TICK)  # 9 of 10 inside is exactly 90%: PASS
    assert rules(nine_in)["R5"]["result"] == "PASS"
    unknown = rules(spaced(10, species="basilisk"))["R5"]
    assert (unknown["result"], unknown["period_unknown"], unknown["species"]) == ("NOT_CLEARED", 10, ["basilisk"])
    miss = rules(spaced(10, world_time_of=day))["R5"]
    assert miss["tag"] == "SURV-08 law MISSING in code" and rules(spaced(10))["R5"]["tag"] == ""


def test_below_ten_engagements_the_share_rules_are_not_evaluated_and_the_other_rules_still_decide() -> None:
    out = rules(spaced(5, diet=["plant"], group="meat"))
    assert (out["R2"]["applies"], out["R2"]["result"], out["R2"]["if_applied"]) == (False, "NOT_EVALUATED (n<10)", "FAIL")      # one attacker, 100% of 5 engagements
    assert (out["R5"]["applies"], out["R5"]["result"]) == (False, "NOT_EVALUATED (n<10)")
    assert (out["R1"]["applies"], out["R1"]["result"]) == (True, "FAIL")        # held by construction, still checked and reported at any count
    pair = [row(i * 3000, victim=100, world_time=2000 + (i * 3000) // 2400 * 2400) for i in range(5)]   # 5 engagements: R4 must fail even though n < 10
    assert (rules(pair)["R4"]["applies"], rules(pair)["R4"]["result"]) == (True, "FAIL")
    close = [row(i * 200, victim=100 + i, world_time=2000 + i * 200) for i in range(4)]                     # 4 engagements inside 2400 ticks: R3 must fail at n < 10
    assert (rules(close)["R3"]["applies"], rules(close)["R3"]["result"]) == (True, "FAIL")


# --------------------------------------------------------------------------------------------- R6 (NEW vs BASE)
def eng_with_hits(*hit_counts: int, attacker: int = 1) -> List[Dict[str, Any]]:
    rows = []
    for i, n in enumerate(hit_counts):
        rows += [row(i * 3000 + k, attacker=attacker, victim=100 + i, world_time=2000) for k in range(n)]
    return engagements_of(rows)


def test_R6_fires_when_new_hits_per_engagement_exceed_twice_base_and_passes_inside_twice() -> None:
    base = eng_with_hits(1, 2, 2)  # median 2, max 2
    fire = summary.rule_r6(eng_with_hits(6, 5), base)
    ok = summary.rule_r6(eng_with_hits(4, 4, 4), base)
    assert (fire["result"], fire["attacker_ids"]) == ("FAIL", [1]) and fire["engagements"][0]["hits"] == 6
    assert ok["result"] == "PASS" and ok["applies"] is True


def test_R6_with_no_base_engagements_passes_up_to_ten_hits_and_fires_above() -> None:
    assert summary.rule_r6(eng_with_hits(10, 3), [])["result"] == "PASS"
    assert summary.rule_r6(eng_with_hits(11, 3), [])["result"] == "FAIL"


def test_R6_does_not_apply_below_ten_new_hits() -> None:
    out = summary.rule_r6(eng_with_hits(5, 4), eng_with_hits(1))
    assert (out["applies"], out["result"]) == (False, "NOT_APPLICABLE")


# --------------------------------------------------------------------------------------------- R7
def hits_on_one_victim(n: int, **kw: Any) -> List[Dict[str, Any]]:
    return [row(2000 + k, attacker=1 + (k % 2), victim=100, **kw) for k in range(n)]


def test_R7_fires_on_three_hits_while_asleep_or_lodged_and_passes_on_two() -> None:
    asleep3 = rules(hits_on_one_victim(3, victim_asleep_before=True) + filler())["R7"]
    lodged3 = rules(hits_on_one_victim(3, victim_lodged_before=True) + filler())["R7"]
    assert asleep3["result"] == "FAIL" and asleep3["attacker_ids"] == [1, 2] and lodged3["result"] == "FAIL"
    assert rules(hits_on_one_victim(2, victim_asleep_before=True) + filler())["R7"]["result"] == "PASS"
    woke = hits_on_one_victim(3, victim_asleep_before=True)
    woke[1] = {**woke[1], "victim_asleep_before": False, "victim_mode_before": "RETREAT"}
    assert rules(woke + filler())["R7"]["result"] == "PASS"


def test_R7_fires_on_five_consecutive_hits_with_no_decision_and_passes_on_four_or_with_a_decision() -> None:
    assert rules(hits_on_one_victim(5) + filler())["R7"]["result"] == "FAIL"
    assert rules(hits_on_one_victim(4) + filler())["R7"]["result"] == "PASS"
    assert rules(hits_on_one_victim(5) + filler(), [{"tick": 2002, "id": 100, "mode": "RETREAT", "first": False}])["R7"]["result"] == "PASS"
    fought = hits_on_one_victim(5)
    fought[2] = {**fought[2], "victim_attacked_same_tick": True}
    assert rules(fought + filler())["R7"]["result"] == "PASS"


def chain_rows(ticks: List[int], **kw: Any) -> List[Dict[str, Any]]:
    return [row(t, attacker=1, victim=100, **kw) for t in ticks]


def test_R7_chain_runs_on_while_every_gap_is_at_most_50_ticks_even_when_the_chain_is_long() -> None:        # C1, firing
    assert rules(chain_rows([2000, 2050, 2100, 2150, 2200]) + filler())["R7"]["result"] == "FAIL"
    assert rules(chain_rows([2000, 2050, 2100], victim_asleep_before=True) + filler())["R7"]["result"] == "FAIL"


def test_R7_chain_resets_on_a_gap_of_more_than_50_ticks_so_it_never_spans_two_engagements() -> None:     # C1, non-firing
    five_split = chain_rows([2000, 2010, 2020, 2071, 2081])                                             # gap 51 between the third and fourth hit: runs of 3 and 2
    assert rules(five_split + filler())["R7"]["result"] == "PASS"
    asleep_split = chain_rows([2000, 2010, 2061, 2071], victim_asleep_before=True)                      # asleep runs of 2 and 2 (would be 4 without the reset)
    assert rules(asleep_split + filler())["R7"]["result"] == "PASS"
    assert summary.hit_chains(chain_rows([2000, 2051]), [])["no_decision_run"]["run"] == 1


def test_R7_a_watched_attack_by_the_victim_is_a_fight_decision_and_an_attack_by_someone_else_is_not() -> None:  # C2, non-firing and firing
    hits = chain_rows([2000, 2010, 2020, 2030, 2040]) + filler()
    victim_fights = [{"tick": 2025, "attacker_id": 100, "victim_id": 1}]
    bystander_attacks = [{"tick": 2025, "attacker_id": 777, "victim_id": 1}]
    assert summary.rules_for_cell(hits, [], engagements_of(hits), attack_rows=victim_fights)["R7"]["result"] == "PASS"
    assert summary.rules_for_cell(hits, [], engagements_of(hits), attack_rows=bystander_attacks)["R7"]["result"] == "FAIL"
    assert summary.rules_for_cell(hits, [], engagements_of(hits), attack_rows=[])["R7"]["result"] == "FAIL"


def test_the_spy_records_an_attack_by_a_watched_id_on_anyone_and_none_by_an_unwatched_id() -> None:     # C2, spy side
    spy = fresh_spy()
    state = world_state(5, two_bodies())
    spy.observe(state, attack_update(3, 1), state)                 # id 3 is not watched yet: not recorded
    spy.observe(state, attack_update(1, 2), state)                 # wolf hits a person: ids 1 and 2 become watched
    spy.observe(state, attack_update(2, 3, hp_delta=0), state)     # the person fights back at a non-person, a miss: recorded as an attack by watched id 2
    assert [(a["attacker_id"], a["victim_id"]) for a in spy.attack_rows] == [(1, 2), (2, 3)]


def test_a_capped_attack_rows_list_marks_the_cell_invalid_and_an_uncapped_one_stays_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    def run_cell(limit: int) -> Dict[str, Any]:
        monkeypatch.setattr(spy_module, "ROW_LIMIT", limit)
        spy = fresh_spy()
        state = world_state(5, two_bodies())
        spy.observe(state, attack_update(1, 2), state)
        spy.observe(state, attack_update(2, 1, hp_delta=0), state)
        spy.observe(state, attack_update(2, 1, hp_delta=0), state)
        spy.finish(state)
        return spy.report()

    capped, roomy = run_cell(2), run_cell(1000)
    assert (capped["attack_rows_truncated"], capped["cell_valid"], capped["wiring"]) == (True, False, "WIRING_MISMATCH")
    assert (roomy["attack_rows_truncated"], roomy["cell_valid"], roomy["wiring"]) == (False, True, "OK")


def test_disk_floor_returns_none_with_room_and_a_stop_record_when_either_filesystem_is_short(tmp_path: Path) -> None:   # C3
    gib = 1024 ** 3
    usage = lambda by_path: (lambda path: SimpleNamespace(free=by_path.get(path, 100 * gib)))  # noqa: E731
    assert run.disk_stop(tmp_path, "cell", free=usage({})) is None
    assert run.disk_stop(tmp_path, "cell", free=usage({str(tmp_path): 2 * gib})) is None                      # exactly 2 GiB is enough
    short_out = run.disk_stop(tmp_path, "cell-a", free=usage({str(tmp_path): 2 * gib - 1}))
    assert short_out is not None and short_out["free_bytes"] == {str(tmp_path): 2 * gib - 1} and short_out["stopped_before"] == "cell-a"
    assert json.loads((tmp_path / run.DISK_STOP_FILE).read_text())["stopped_before"] == "cell-a"
    short_root = run.disk_stop(tmp_path, "cell-b", free=usage({"/": gib}))
    assert short_root is not None and list(short_root["free_bytes"]) == ["/"]


def test_disk_floor_stop_record_failure_is_reported_not_raised(tmp_path: Path) -> None:
    out = tmp_path / "missing_dir"
    stop = run.disk_stop(out, "cell", free=lambda path: SimpleNamespace(free=0))
    assert stop is not None and stop["record_not_written"] is True


def test_the_launcher_checks_the_disk_floor_before_the_start_and_before_every_cell() -> None:
    text = (ROOT / "tools" / "rpg_measure" / "person_attack_launch.sh").read_text(encoding="utf-8")
    assert text.index('disk_ok "the start"') < text.index("T0=$(date +%s)")
    assert text.index('disk_ok "$name"') < text.index("scope_command \"$arm\" \"$w\" \"$sd\" \"$mode\"\n  PAT=") and "STOPPED_DISK_FLOOR_BEFORE_" in text


# --------------------------------------------------------------------------------------------- the twin check and the summary switch
def cell(hash_: str, rows: Optional[List[Dict[str, Any]]] = None, **kw: Any) -> Dict[str, Optional[Dict[str, Any]]]:
    base = {"final_hash": hash_, "ticks": 5000, "runner": "PINNED", "logging_errors": []}
    spy = {**base, "wiring": "OK", "rows": rows or [], "mode_rows": [], "final_tick": 5000, "o3_total_spy": 0, "o3_total_ledger": 0, "o3_by_group_spy": {}, "control": None, **kw}
    return {"plain": dict(base), "spy": spy}


def test_twin_hashes_that_differ_invalidate_the_cell_and_equal_ones_do_not() -> None:
    assert summary.cell_validity(**cell("a"))["valid"] is True
    bad = cell("a")
    bad["spy"]["final_hash"] = "b"
    verdict = summary.cell_validity(**bad)
    assert verdict["valid"] is False and verdict["twin_hashes_equal"] is False and "twin hashes differ" in verdict["problems"]
    assert summary.cell_validity(None, cell("a")["spy"])["valid"] is False


def test_a_wiring_mismatch_or_a_control_file_invalidates_the_cell() -> None:
    assert summary.cell_validity(**cell("a", wiring="WIRING_MISMATCH"))["valid"] is False
    assert summary.cell_validity(**cell("a", control="inject_hit"))["valid"] is False


def unknown_mix(unknown: int, total: int) -> List[Dict[str, Any]]:
    """total engagements by distinct attackers at a night tick: ``unknown`` of them by a species not in the period table, the rest by wolves (nocturnal, inside)."""
    rows = []
    for i in range(total):
        rows.append(row(i * 3000, attacker=1000 + i, victim=2000 + i, species="basilisk" if i < unknown else "wolf", world_time=i * 3000 // 2400 * 2400 + NIGHT_TICK))
    return rows


def test_r5_not_assessable_threshold_9_9_percent_decides_on_the_rest_and_10_percent_is_not_cleared() -> None:
    below = rules(unknown_mix(10, 101))["R5"]      # 10 / 101 = 9.90%
    at = rules(unknown_mix(10, 100))["R5"]         # 10 / 100 = 10.00%
    assert (below["result"], round(below["unassessable_share"], 4), below["species"]) == ("PASS", 0.099, ["basilisk"])
    assert (at["result"], at["unassessable_share"], at["species"], at["note"]) == ("NOT_CLEARED", 0.10, ["basilisk"], "R5 not assessable: counts as HELD")
    outside = unknown_mix(10, 101) + [row(900_000 + i * 3000, attacker=3000 + i, victim=4000 + i, world_time=DAY_TICK) for i in range(20)]
    assert rules(outside)["R5"]["result"] == "FAIL"   # below 10%, R5 still decides on the rest, and a miss is a miss


def arm_cell(rows: List[Dict[str, Any]], hash_: str = "h") -> Dict[str, Optional[Dict[str, Any]]]:
    return cell(hash_, rows)


def clean(**kw: Any) -> List[Dict[str, Any]]:
    """10 engagements, two attackers of 5 each (R2 passes), 3000 ticks apart, distinct victims, inside their period: every rule passes."""
    return spaced(5, attacker=1, **kw) + spaced(5, attacker=2, **kw)


def verdict_of(new_rows: List[Dict[str, Any]], base_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return summary.summarize({("new", "w", 42): arm_cell(new_rows), ("base", "w", 42): arm_cell(base_rows)}, NIGHT)


def test_verdict_a_miss_on_new_only_is_attributed_and_a_miss_on_both_arms_is_pre_existing() -> None:
    quiet = clean()
    r4_miss = lambda: [row(i * 3000, victim=100, world_time=2000 + (i * 3000) // 2400 * 2400) for i in range(5)] + spaced(5, attacker=2)  # noqa: E731  (R4: one pair, 5 engagements)
    new_only = verdict_of(r4_miss(), quiet)
    both = verdict_of(r4_miss(), r4_miss())
    assert new_only["verdict"] == "BUG CANDIDATE, attributed"
    assert [(m["rule"], m["attribution"], m["attacker_ids"]) for m in new_only["verdict_detail"]["misses"] if m["rule"] == "R4"] == [("R4", "attributed", [1])]
    assert both["verdict"] == "BUG CANDIDATE, pre-existing (not attributed to #953/#954)"
    assert [m["attribution"] for m in both["verdict_detail"]["misses"] if m["rule"] == "R4"] == ["pre-existing (not attributed to #953/#954)"]
    assert both["verdict_detail"]["misses"][0]["base_attacker_ids"] == [1]


def test_verdict_a_base_only_miss_does_not_fail_new_and_a_clean_new_with_enough_engagements_is_cleared() -> None:
    r4_miss = [row(i * 3000, victim=100, world_time=2000 + (i * 3000) // 2400 * 2400) for i in range(5)] + spaced(5, attacker=2)
    out = verdict_of(clean(), r4_miss)
    assert out["verdict"] == "CLEARED" and out["verdict_detail"]["misses"] == [] and out["verdict_detail"]["evaluated_seeds"] == ["meat:w/s42"]


def test_verdict_held_outranks_intended_and_not_assessable_is_not_a_pass() -> None:
    out = verdict_of(clean(species="basilisk"), clean())
    assert out["verdict"] == "HELD" and out["verdict_detail"]["held"][0]["result"] == "NOT_CLEARED" and out["verdict_detail"]["held"][0]["species"] == ["basilisk"]
    twin_bad = {("new", "w", 42): cell("a", clean()), ("base", "w", 42): cell("b", clean())}
    twin_bad[("new", "w", 42)]["spy"]["final_hash"] = "other"       # an invalid NEW cell cannot be cleared
    assert summary.summarize(twin_bad, NIGHT)["verdict"] == "HELD"


def test_a_seed_under_ten_engagements_that_fails_r4_is_a_bug_candidate_and_one_that_passes_the_rest_is_cleared_with_the_run_line() -> None:
    pair = [row(i * 3000, victim=100, world_time=2000 + (i * 3000) // 2400 * 2400) for i in range(5)]       # n = 5 < 10, one pair five times: R4
    failing = verdict_of(pair, clean())
    assert failing["verdict"] == "BUG CANDIDATE, attributed" and "R4" in [m["rule"] for m in failing["verdict_detail"]["misses"]]
    assert failing["verdict_detail"]["run_line"].startswith("meat: R2/R5 NOT EVALUATED (n<10)")
    quiet = verdict_of(spaced(3), spaced(3))                                                                  # n = 3: R2/R5 not evaluated; R1, R3, R4, R7 pass; R6 not applicable
    assert quiet["verdict"] == "CLEARED" and quiet["verdict_detail"]["evaluated_seeds"] == []
    assert quiet["groups"]["meat"]["rules"]["R2"]["w"]["new"]["s42"]["result"] == "NOT_EVALUATED (n<10)" and quiet["verdict_detail"]["run_line"].startswith("meat: R2/R5 NOT EVALUATED (n<10)")
    enough = verdict_of(clean(), clean())
    assert enough["verdict"] == "CLEARED" and enough["verdict_detail"]["run_line"] == "meat: R2/R5 evaluated in: w/s42"


def test_a_miss_outranks_held_and_held_is_still_listed() -> None:
    both = verdict_of(clean(species="basilisk") + [row(900_000 + i * 200, attacker=9, victim=7000 + i, species="wolf", world_time=2000) for i in range(5)], clean())
    assert both["verdict"] == "BUG CANDIDATE, attributed" and both["verdict_detail"]["held"]       # a miss outranks HELD, and HELD is still listed


def other_group_rows() -> List[Dict[str, Any]]:
    """10 engagements by ONE attacker of the group meat+plant+prepared: against every rule if it were in scope (R2 100%, R3 many per window, R4 one pair five times)."""
    return [row(60_000 + i * 200, attacker=88, victim=89, diet=["meat", "plant", "prepared"], world_time=62_000 + i * 200) for i in range(10)]


def test_an_untied_o3_group_cannot_change_the_meat_verdict_and_is_reported_in_full_as_context_only() -> None:
    alone = verdict_of(clean(), clean())
    mixed = verdict_of(clean() + other_group_rows(), clean())
    assert alone["verdict"] == mixed["verdict"] == "CLEARED" and alone["verdict_detail"]["misses"] == mixed["verdict_detail"]["misses"] == []
    assert mixed["groups"]["meat"]["rules"]["R2"]["w"]["new"]["s42"] == alone["groups"]["meat"]["rules"]["R2"]["w"]["new"]["s42"]
    context = mixed["groups"]["meat+plant+prepared"]["cells"]["new/w/s42"]
    assert mixed["groups"]["meat+plant+prepared"]["tied"] is False and context["verdict"] is None and context["label"] == "context, no verdict" and context["engagements_count"] > 0
    assert context["rules_as_context"]["R4"]["result"] in ("FAIL", "PASS") and context["per_attacker"] and context["per_pair"] and "verdict_detail" not in mixed["groups"]["meat+plant+prepared"]
    assert mixed["tied_groups"] == ["meat"] and "meat+plant+prepared" not in alone["groups"]


def test_a_group_added_to_tied_groups_gets_its_own_verdict_and_its_r1_reads_the_exact_group(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(summary, "TIED_GROUPS", ("meat", "meat+plant+prepared"))
    out = verdict_of(clean() + other_group_rows(), clean())
    other = out["groups"]["meat+plant+prepared"]
    assert other["tied"] is True and other["verdict_detail"]["headline"].startswith("BUG CANDIDATE") and out["verdict"].startswith("BUG CANDIDATE") and out["verdict_detail"]["by_group"]["meat"] == "CLEARED"
    assert {m["group"] for m in out["verdict_detail"]["misses"]} == {"meat+plant+prepared"} and other["rules"]["R1"]["w"]["new"]["s42"]["result"] == "PASS"
    stray = [row(i * 3000, attacker=5, victim=100 + i, diet=["meat", "plant"], group="meat+plant", world_time=2000) for i in range(10)]
    r1 = rules_in_group(stray, "meat")
    assert r1["R1"]["result"] == "FAIL" and r1["R1"]["attacker_ids"] == [5]      # a counted attacker that is not in that exact group fails R1


def rules_in_group(rows: List[Dict[str, Any]], group: str) -> Dict[str, Dict[str, Any]]:
    return summary.rules_for_cell(rows, [], engagements_of(rows), rows, group)


def test_the_summary_carries_the_measurement_labels_and_the_pinned_period_quote_matches_the_rule_text() -> None:
    out = verdict_of(clean(), clean())
    assert any("BASE's agents never used it" in label for label in out["measurement_labels"])
    doc = (ROOT / "docs" / "world_rules" / "life-body" / "survival-needs.md").read_text(encoding="utf-8").splitlines()
    flat = lambda lines: " ".join(" ".join(lines).replace("> ", " ").split())  # noqa: E731
    assert summary.PERIODS_QUOTE in flat(doc[1041:1044])
    assert summary.MISSING_LAW_QUOTE in flat(doc[1044:1047])
    stated = {species for species, period in summary.PERIODS.items() if period == summary.DIURNAL}
    assert stated == {"human", "elf", "dwarf", "orc", "lizardfolk", "small_plant_eater", "dragonkin"}


def eng_hits_rows() -> List[Dict[str, Any]]:
    return [row(70_000 + k, attacker=77, victim=777, world_time=2000) for k in range(12)]


# --------------------------------------------------------------------------------------------- the spy (injected reads and a stand-in ledger with the real ledger's key shape)
def body(kind: str, group: str, person: int, diet: List[str], action: Optional[str] = None, mode: str = "WANDER", lodged: Optional[int] = None) -> Any:
    return SimpleNamespace(kind=kind, group=group, person=person, diet=diet, combat=SimpleNamespace(alive=True, last_hit_attackers=()), task=SimpleNamespace(payload={"action": action} if action else {}),
                           navigation=SimpleNamespace(movement_mode=mode, lodged_in=lodged))


def reads() -> spy_module.TreeReads:
    return spy_module.TreeReads(
        kind_group=lambda e: e.group, is_person=lambda e: bool(e.person), species_of=lambda e: e.kind, is_wild_meat_eater=lambda g, p: "meat" in g.split("+") and p != "1",
        declared_diet=lambda e: e.diet, is_asleep=lambda e: e.task.payload.get("action") in ("SLEEP", "REST"), is_lodged=lambda e: e.navigation.lodged_in is not None, split_key=lambda k, n: k.split("|"), make_key=lambda *parts: "|".join(str(x) for x in parts))


class StandInLedger:
    """The ledger's attack counting in its own key shape (run_ledger._count_attacks: attacker group | attacker person | victim person | hit or kill), with its liveness fields (_live, _header_sent,
    first_tick/last_tick in the tally payload) and the kernel-style reset the real one suffers (reset_run_state, then configure)."""
    attacks: Dict[str, int] = {}
    skip = False
    _live = False
    _header_sent = False
    _first_tick: Optional[int] = None
    _last_tick: Optional[int] = None
    stuck_off = False   # a ledger whose configure() never turns it on

    @classmethod
    def reset_run_state(cls) -> None:
        cls.attacks, cls._header_sent, cls._first_tick, cls._last_tick = {}, False, None, None

    @classmethod
    def configure(cls, live: bool) -> None:
        cls._live = False if cls.stuck_off else live

    @classmethod
    def observe(cls, prior: Any, current: Any, update: Any) -> list:
        if cls.skip or not cls._live:
            return []
        if not cls._header_sent:
            cls._header_sent, cls._first_tick = True, current.tick
        cls._last_tick = current.tick
        for eid, upd in (getattr(update, "entity_updates", None) or {}).items():
            combat = getattr(upd, "combat", None)
            attacker_id = getattr(combat, "attacker_id", None)
            if attacker_id is None or getattr(combat, "hp_delta", 0) >= 0:
                continue
            victim, attacker = current.entities.get(eid), prior.entities.get(attacker_id)
            if victim is None or attacker is None:
                continue
            key = f"{attacker.group}|{int(attacker.person)}|{int(victim.person)}|{'kill' if getattr(combat, 'outcome_kind', None) == 'KILL' else 'hit'}"
            cls.attacks[key] = cls.attacks.get(key, 0) + 1
        return []

    @classmethod
    def tally_event(cls) -> Any:
        return SimpleNamespace(payload={"attacks": dict(cls.attacks), "first_tick": cls._first_tick, "last_tick": cls._last_tick})


def world_state(tick: int, entities: Dict[int, Any]) -> Any:
    return SimpleNamespace(tick=tick, world_time=tick, entities=entities)


def attack_update(attacker: int, victim: int, hp_delta: int = -3) -> Any:
    return SimpleNamespace(entity_updates={victim: SimpleNamespace(combat=SimpleNamespace(attacker_id=attacker, hp_delta=hp_delta, outcome_kind="SURVIVE"))})


def fresh_spy(**kw: Any) -> spy_module.PersonAttackSpy:
    StandInLedger.skip = False
    StandInLedger.stuck_off = False
    return spy_module.PersonAttackSpy(reads(), StandInLedger, **kw).start_ledger()


def two_bodies() -> Dict[int, Any]:
    return {1: body("wolf", "meat", 0, ["meat"]), 2: body("human", "meat+plant+prepared", 1, ["meat", "plant", "prepared"], action="SLEEP"), 3: body("goat", "plant", 0, ["plant"])}


def test_the_spy_sees_a_hit_a_miss_and_agrees_with_the_ledgers_own_counting() -> None:
    spy = fresh_spy()
    state = world_state(5, two_bodies())
    spy.observe(state, attack_update(1, 2), state)                 # wolf hits a sleeping person
    spy.observe(state, attack_update(1, 2, hp_delta=0), state)      # a miss (no hp lost): recorded, not counted
    spy.observe(state, attack_update(3, 2), state)                 # a plant-eater hits a person: recorded, NOT in the O3 group
    spy.finish(state)
    doc = spy.report()
    assert [(r["hit"], r["in_o3_group"], r["victim_asleep_before"]) for r in doc["rows"]] == [(True, True, True), (False, True, True), (True, False, True)]
    assert doc["o3_total_spy"] == 1 == doc["o3_total_ledger"] and doc["o3_by_group_spy"] == {"meat": 1}
    assert doc["wiring"] == "OK" and doc["cell_valid"] is True and doc["row_count"] == 3


def test_the_spy_records_nothing_for_an_attack_on_a_non_person_and_marks_a_mode_change_of_a_watched_id() -> None:
    spy = fresh_spy()
    state = world_state(5, two_bodies())
    spy.observe(state, attack_update(1, 3), state)                 # victim 3 is not a person
    assert spy.rows == []
    spy.observe(state, attack_update(1, 2), state)
    later = {**two_bodies(), 2: body("human", "meat+plant+prepared", 1, ["meat"], mode="RETREAT")}
    spy.observe(world_state(6, later), SimpleNamespace(entity_updates={}), world_state(6, later))
    assert [(m["id"], m["mode"], m["first"]) for m in spy.mode_rows if m["id"] == 2] == [(2, "WANDER", True), (2, "RETREAT", False)]


def test_a_ledger_that_counts_differently_marks_the_cell_wiring_mismatch_and_exit_5() -> None:
    spy = fresh_spy()
    state = world_state(5, two_bodies())
    spy.observe(state, StateUpdate(), state)         # a quiet first tick opens the ledger (header sent), so it is live
    StandInLedger.skip = True                        # from here the ledger counts differently (nothing)
    spy.observe(state, attack_update(1, 2), state)
    spy.finish(state)
    doc = spy.report()
    assert (doc["o3_total_spy"], doc["o3_total_ledger"], doc["cell_valid"]) == (1, 0, False)
    assert doc["wiring"] == "WIRING_MISMATCH"
    assert spy_module.exit_status(doc)[0] == spy_module.EXIT_WIRING_MISMATCH
    StandInLedger.skip = False


def test_the_global_mode_leaving_off_is_a_breach_that_invalidates_the_cell() -> None:
    spy = fresh_spy(mode_getter=lambda: "FULL")
    state = world_state(5, two_bodies())
    spy.observe(state, attack_update(1, 2), state)
    spy.finish(state)
    assert spy.report()["wiring"] == "WIRING_MISMATCH" and spy.report()["mode_breach_count"] == 1


def test_inject_hit_control_makes_a_quiet_run_non_zero_and_both_counters_agree_and_the_file_is_never_valid() -> None:
    spy = fresh_spy(control="inject_hit", control_tick=5)
    state = world_state(5, two_bodies())
    spy.observe(state, StateUpdate(), state)       # a quiet tick: no real attack in it
    spy.finish(state)
    doc = spy.report()
    assert doc["o3_total_spy"] == 1 == doc["o3_total_ledger"] and doc["control_applied_count"] == 1 and doc["cell_valid"] is False
    assert (doc["rows"][0]["attacker_id"], doc["rows"][0]["victim_id"]) == (1, 2)
    assert spy_module.exit_status(doc) == (0, "")


def test_a_control_whose_tick_no_state_reaches_never_fires_and_exits_6() -> None:
    spy = fresh_spy(control="never_fire", control_tick=999_999)
    state = world_state(5, two_bodies())
    spy.observe(state, StateUpdate(), state)
    spy.finish(state)
    doc = spy.report()
    assert doc["control_applied_count"] == 0 and spy_module.exit_status(doc)[0] == spy_module.EXIT_CONTROL_NOT_APPLIED


def test_the_plain_mode_installs_nothing_the_spy_restores_the_apply_path() -> None:
    class FakeApply:
        @staticmethod
        def apply_generation(prior, update, *a, **k):
            return prior

    original = FakeApply.__dict__["apply_generation"]
    spy = fresh_spy().install(FakeApply)
    prior = world_state(1, two_bodies())
    assert FakeApply.apply_generation(prior, StateUpdate()) is prior   # the wrapper returns the original's result, the same object, untouched
    spy.restore()
    assert FakeApply.__dict__["apply_generation"].__func__ is original.__func__


def observe_ticks(spy: spy_module.PersonAttackSpy, ticks: List[int], attack_at: Optional[int] = None, between: Optional[Any] = None) -> None:
    state = world_state(ticks[0], two_bodies())
    for tick in ticks:
        current = world_state(tick, state.entities)
        if between is not None:
            between(tick)
        spy.observe(current, attack_update(1, 2) if tick == attack_at else StateUpdate(), current)


def test_finish_runs_before_the_kernel_shutdown_even_when_a_tick_raises() -> None:
    calls: List[str] = []

    class FakeKernel:
        state = world_state(3, two_bodies())

        def tick_once(self) -> None:
            calls.append("tick")
            if len(calls) == 3:
                raise RuntimeError("boom")

        def shutdown(self) -> None:
            calls.append("shutdown")

    class FakeSpy:
        def restore(self) -> None:
            calls.append("restore")

        def finish(self, final_state: Any) -> None:
            calls.append("finish")

    assert spy_module.run_ticks(FakeKernel(), 2, FakeSpy()) is FakeKernel.state
    assert calls == ["tick", "tick", "restore", "finish", "shutdown"]
    calls.clear()
    with pytest.raises(RuntimeError):
        spy_module.run_ticks(FakeKernel(), 5, FakeSpy())
    assert calls == ["tick", "tick", "tick", "restore", "finish", "shutdown"]
    calls.clear()
    spy_module.run_ticks(FakeKernel(), 1, None)       # the plain twin: no spy, same shutdown
    assert calls == ["tick", "shutdown"]


def test_a_kernel_style_switch_off_after_start_is_reasserted_the_spy_still_counts_and_records_it() -> None:
    spy = fresh_spy()
    spy.ledger.configure(False)                      # the kernel's own reset ran AFTER start_ledger(): the ledger is off
    observe_ticks(spy, [10, 11, 12], attack_at=11)
    spy.finish(world_state(12, two_bodies()))
    doc = spy.report()
    assert doc["ledger_evidence"]["reasserts"] == [10] and doc["ledger_evidence"]["first_observe"] == {"live": False, "header_sent": False}
    assert (doc["o3_total_spy"], doc["o3_total_ledger"], doc["wiring"]) == (1, 1, "OK") and doc["ledger_evidence"]["observe_calls"] == doc["ledger_evidence"]["apply_calls"] == 3


def test_a_reset_after_the_spy_started_fails_loudly_with_its_own_exit() -> None:
    spy = fresh_spy()
    observe_ticks(spy, [10, 11, 12, 13], attack_at=11, between=lambda tick: (spy.ledger.reset_run_state(), spy.ledger.configure(True)) if tick == 12 else None)   # the counters of ticks 10-11 are gone
    spy.finish(world_state(13, two_bodies()))
    doc = spy.report()
    assert doc["wiring"] == "LEDGER_NOT_LIVE" and doc["ledger_evidence"]["payload_ticks"]["first_tick"] == 12 and doc["ledger_evidence"]["spy_first_tick"] == 10
    assert spy_module.exit_status(doc)[0] == spy_module.EXIT_LEDGER_NOT_LIVE != spy_module.EXIT_WIRING_MISMATCH


def test_a_ledger_that_never_opens_fails_loudly_with_the_not_live_exit_and_the_evidence() -> None:
    StandInLedger.stuck_off = True
    spy = spy_module.PersonAttackSpy(reads(), StandInLedger).start_ledger()
    observe_ticks(spy, [10, 11], attack_at=11)
    spy.finish(world_state(11, two_bodies()))
    doc = spy.report()
    StandInLedger.stuck_off = False
    assert doc["wiring"] == "LEDGER_NOT_LIVE" and doc["ledger_evidence"]["finish"] == {"live": False, "header_sent": False} and doc["ledger_evidence"]["reasserts"] == [10, 11]
    assert doc["o3_total_spy"] == 1 and doc["o3_total_ledger"] == 0 and spy_module.exit_status(doc)[0] == 7


def test_inject_hit_raises_both_counters_by_exactly_one() -> None:
    base = fresh_spy()
    observe_ticks(base, [10, 11, 12], attack_at=11)
    base.finish(world_state(12, two_bodies()))
    injected = fresh_spy(control="inject_hit", control_tick=12)
    observe_ticks(injected, [10, 11, 12], attack_at=11)
    injected.finish(world_state(12, two_bodies()))
    a, b = base.report(), injected.report()
    assert (a["o3_total_spy"], a["o3_total_ledger"]) == (1, 1) and (b["o3_total_spy"], b["o3_total_ledger"]) == (2, 2) and b["wiring"] == "OK" and b["control_applied_count"] == 1


def real_gate_reads() -> spy_module.TreeReads:
    """The kit's reads with the REAL gate predicate, key maker and splitter of this tree (87792e3e8's, byte-equal in the head), and stand-in entity accessors."""
    from src.observability.rpg_gate_metrics import _is_wild_meat_eater, _split
    from src.observability.run_ledger import _key

    base = reads()
    return spy_module.TreeReads(base.kind_group, base.is_person, base.species_of, _is_wild_meat_eater, base.declared_diet, base.is_asleep, base.is_lodged, _split, _key)


@pytest.mark.parametrize("person_field", [1, "1"])
def test_a_person_attacker_arriving_as_int_one_or_str_one_is_rejected_as_o3_through_the_kits_own_call_path(person_field: Any) -> None:
    real = real_gate_reads()
    assert real.o3_label("meat", person_field) is False                       # the kit's labelling function normalises to the ledger key's string field
    assert real.o3_label("meat+plant+prepared", person_field) is False
    assert real.o3_label("meat", 0) is True and real.o3_label("meat", "0") is True and real.o3_label("plant", 0) is False


def test_the_raw_gate_predicate_accepts_an_int_one_which_is_why_the_kit_normalises_first() -> None:
    from src.observability.rpg_gate_metrics import _is_wild_meat_eater

    assert _is_wild_meat_eater("meat", 1) is True and _is_wild_meat_eater("meat", "1") is False   # the defect of the first preflight: 1 != "1"


def test_person_on_person_is_not_o3_and_a_non_person_meat_attacker_on_a_person_is_o3_with_the_real_gate_functions() -> None:
    spy = spy_module.PersonAttackSpy(real_gate_reads(), StandInLedger).start_ledger()
    bodies = {**two_bodies(), 4: body("goblin", "meat+plant+prepared", 1, ["meat", "plant", "prepared"])}     # a person goblin (coin-and-trade trait)
    state = world_state(5, bodies)
    spy.observe(state, attack_update(2, 4), state)     # person human hits person goblin: NOT O3
    spy.observe(state, attack_update(4, 2), state)     # person goblin hits person human: NOT O3
    spy.observe(state, attack_update(1, 2), state)     # non-person wolf (group meat) hits a person: O3
    spy.finish(state)
    doc = spy.report()
    assert [(r["attacker_id"], r["attacker_person"], r["in_o3_group"], r["ledger_key"]) for r in doc["rows"]] == [
        (2, 1, False, "meat+plant+prepared|1|1|hit"), (4, 1, False, "meat+plant+prepared|1|1|hit"), (1, 0, True, "meat|0|1|hit")]
    assert doc["o3_by_group_spy"] == doc["o3_by_group_ledger"] == doc["o3_by_group_rows"] == {"meat": 1} and doc["wiring"] == "OK" and doc["per_key_counts_equal"] is True
    assert doc["key_counts_spy"] == doc["key_counts_ledger"] == {"meat+plant+prepared|1|1|hit": 2, "meat|0|1|hit": 1}


def test_the_spy_counts_every_hit_per_ledger_key_not_only_hits_on_people() -> None:
    spy = fresh_spy()
    state = world_state(5, two_bodies())
    spy.observe(state, attack_update(1, 3), state)     # wolf hits a goat: not a person victim, still a ledger key
    spy.finish(state)
    doc = spy.report()
    assert doc["key_counts_spy"] == doc["key_counts_ledger"] == {"meat|0|0|hit": 1} and doc["rows"] == [] and doc["wiring"] == "OK"


def test_a_key_present_on_one_side_only_is_a_wiring_fail_even_when_the_o3_totals_agree() -> None:
    spy = fresh_spy()
    state = world_state(5, two_bodies())
    spy.observe(state, attack_update(1, 3), state)     # a non-O3 key (victim not a person): O3 is untouched
    spy.observe(state, attack_update(1, 2), state)     # the O3 key
    StandInLedger.attacks.pop("meat|0|0|hit")          # the ledger lacks the non-O3 key the spy has
    spy.finish(state)
    doc = spy.report()
    assert doc["per_group_counts_equal"] is True and doc["per_key_counts_equal"] is False and doc["wiring"] == "WIRING_MISMATCH" and doc["cell_valid"] is False
    assert doc["keys_only_in_spy"] == ["meat|0|0|hit"] and doc["keys_only_in_ledger"] == [] and doc["key_diffs"] == {"meat|0|0|hit": {"spy": 1, "ledger": None}}
    ledger_extra = fresh_spy()
    ledger_extra.observe(state, attack_update(1, 2), state)
    StandInLedger.attacks["plant|0|0|hit"] = 3         # the ledger has a key the spy never saw
    ledger_extra.finish(state)
    other = ledger_extra.report()
    assert other["keys_only_in_ledger"] == ["plant|0|0|hit"] and other["wiring"] == "WIRING_MISMATCH" and spy_module.exit_status(other)[0] == spy_module.EXIT_WIRING_MISMATCH


def test_the_declared_o3_groups_are_recorded_and_an_undeclared_group_is_listed() -> None:
    spy = fresh_spy(declared_o3_groups=["meat"])
    state = world_state(5, {**two_bodies(), 5: body("ogre", "meat+plant", 0, ["meat", "plant"])})
    spy.observe(state, attack_update(1, 2), state)
    spy.observe(state, attack_update(5, 2), state)
    spy.finish(state)
    doc = spy.report()
    assert doc["declared_o3_groups"] == ["meat"] and doc["undeclared_o3_groups"] == ["meat+plant"]


# --------------------------------------------------------------------------------------------- the runner
def test_the_plan_runs_the_plain_twin_before_the_spy_in_every_cell_and_never_starts_a_process_on_a_dry_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    items = run.plan(["new", "base"], ["w"], [42, 43], 5000)
    assert [i["name"] for i in items if i["arm"] == "new"] == ["new__w__s42__plain", "new__w__s42__spy", "new__w__s43__plain", "new__w__s43__spy"]
    assert len(items) == 8
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("a dry run started a process")))
    assert run.main(["--tree", "new=/t/n", "--tree", "base=/t/b", "--out", str(tmp_path / "o"), "--go", "x", "--world", "w", "--seed", "42", "--ticks", "5000", "--python", "py", "--dry-run"]) == 0
    assert "person_attack_spy.py" in capsys.readouterr().out and not (tmp_path / "o").exists()


def test_a_changed_interpreter_freeze_voids_the_run_and_skips_the_remaining_cells(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    
    import threading

    started: List[str] = []
    monkeypatch.setattr(run, "run_child", lambda python, tree, out, item: started.append(item["name"]) or {"returncode": 0})
    freezes = iter(["B"])  # the first read after a process differs from the "before" value A
    monkeypatch.setattr(run, "freeze_sha", lambda python: next(freezes, "B"))
    stop, results = threading.Event(), {}
    run.run_arm("new", run.plan(["new"], ["w"], [42, 43], 10), tmp_path, tmp_path, "py", "A", stop, results)
    assert started == ["new__w__s42__plain"] and stop.is_set()
    assert results["new__w__s42__plain"]["interpreter_changed"] == {"before": "A", "after": "B"} and results["new__w__s43__spy"] == {"skipped": "run voided"}


def test_freeze_sha_hashes_the_uv_output_and_fails_loudly() -> None:
    ok = lambda *a, **k: SimpleNamespace(returncode=0, stdout="a==1\n", stderr="")  # noqa: E731
    assert len(run.freeze_sha("py", runner=ok)) == 64
    with pytest.raises(RuntimeError):
        run.freeze_sha("py", runner=lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="boom"))


def test_the_runner_moves_the_trees_data_runs_out_and_never_overwrites(tmp_path: Path) -> None:
    tree, out = tmp_path / "tree", tmp_path / "out"
    (tree / "data" / "runs" / "r1").mkdir(parents=True)
    (tree / "data" / "runs" / "r1" / "x").write_text("1")
    moved = run.move_tree_runs(tree, out / "tree-data-runs" / "c")
    assert moved is not None and (moved / "r1" / "x").read_text() == "1" and not (tree / "data" / "runs").exists()
    assert run.move_tree_runs(tree, out / "tree-data-runs" / "d") is None
    (tree / "data" / "runs").mkdir()
    with pytest.raises(RuntimeError):
        run.move_tree_runs(tree, out / "tree-data-runs" / "c")


def test_twin_check_compares_final_hashes_and_reports_a_missing_file_as_none(tmp_path: Path) -> None:
    items = run.plan(["new"], ["w"], [42, 43], 10)
    (tmp_path / "new__w__s42__plain.json").write_text(json.dumps({"final_hash": "h"}))
    (tmp_path / "new__w__s42__spy.json").write_text(json.dumps({"final_hash": "h"}))
    (tmp_path / "new__w__s43__plain.json").write_text(json.dumps({"final_hash": "h"}))
    assert run.twin_check(tmp_path, items) == {"new/w/s42": True, "new/w/s43": None}
    (tmp_path / "new__w__s43__spy.json").write_text(json.dumps({"final_hash": "other"}))
    assert run.twin_check(tmp_path, items)["new/w/s43"] is False


# --------------------------------------------------------------------------------------------- the frozen-tree proof
def make_repo(tmp_path: Path) -> tuple:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.txt").write_text("one\n")
    (repo / "src").mkdir()
    (repo / "src" / "b.py").write_text("print(1)\n")
    for cmd in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "c"]):
        subprocess.run(["git", "-C", str(repo), *cmd], check=True, capture_output=True)
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    tree = tmp_path / "tree"
    tree.mkdir()
    archive = subprocess.run(["git", "-C", str(repo), "archive", sha], check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(tree)], input=archive, check=True)
    return repo, sha, tree


def test_tree_check_accepts_a_fresh_archive_and_rejects_a_changed_extra_missing_file_or_data_runs(tmp_path: Path) -> None:
    repo, sha, tree = make_repo(tmp_path)
    args = ["--repo", str(repo), "--sha", sha, "--tree", str(tree)]
    assert tree_check.main(args) == 0
    (tree / "a.txt").write_text("changed\n")
    assert tree_check.main(args) == 1
    (tree / "a.txt").write_text("one\n")
    (tree / "extra.txt").write_text("x")
    assert tree_check.main(args) == 1
    (tree / "extra.txt").unlink()
    (tree / "src" / "b.py").unlink()
    assert tree_check.main(args) == 1
    (tree / "src" / "b.py").write_text("print(1)\n")
    assert tree_check.main(args) == 0
    (tree / "data" / "runs").mkdir(parents=True)
    assert tree_check.main(args) == 1


# --------------------------------------------------------------------------------------------- the launcher
LAUNCHER = ROOT / "tools" / "rpg_measure" / "person_attack_launch.sh"


def test_the_launcher_parses_and_names_no_cell_command_on_its_own_command_line() -> None:
    assert subprocess.run(["bash", "-n", str(LAUNCHER)], capture_output=True).returncode == 0
    assert "person_attack_run" in LAUNCHER.read_text()


def test_the_heavy_check_ignores_a_shell_that_only_contains_the_words_and_sees_a_real_process(tmp_path: Path) -> None:
    """The four cases run inside ONE bash script (its own siblings, real sleeps), so the result does not depend on how the test runner parents its processes."""
    text = LAUNCHER.read_text(encoding="utf-8")
    fn = text[text.index("heavy_running() {"):text.index("HEAVY_WORDS=")]
    (tmp_path / "fakeheavyxyz.py").write_text("import time\ntime.sleep(30)\n")
    script = tmp_path / "cases.sh"
    script.write_text(f"""{fn}
W=fakeheavyxyz
heavy_running "$W"; echo "nothing_running=$?"
bash -c 'sleep 30' "python $W.py" & S=$!; sleep 1.5
heavy_running "$W"; echo "shell_that_contains_the_words=$?"; kill $S
{sys.executable} {tmp_path}/fakeheavyxyz.py & P=$!; sleep 1.5
heavy_running "$W"; echo "real_interpreter=$?"; kill $P
# ancestor text: python $W.py
heavy_running "$W"; echo "ancestor_text_only=$?"
""", encoding="utf-8")
    out = subprocess.run(["bash", str(script)], capture_output=True, text=True, timeout=60).stdout
    got = dict(line.split("=") for line in out.split())
    assert got == {"nothing_running": "1", "shell_that_contains_the_words": "1", "real_interpreter": "0", "ancestor_text_only": "1"}


def dry_run_lines(tmp_path: Path, seeds: str = "42 45 43") -> List[str]:
    env = tmp_path / "dry.env"
    env.write_text(f'KIT=/k\nOUT=/o\nTREE_NEW=/t/new\nTREE_BASE=/t/base\nPY=/p/python\nWORLDS="frontier_living_world"\nSEEDS="{seeds}"\nTICKS=5000\n', encoding="utf-8")
    proc = subprocess.run(["bash", str(LAUNCHER), str(env), "1"], capture_output=True, text=True, env={**os.environ, "LAUNCH_DRY_RUN": "1"}, timeout=30)
    assert proc.returncode == 0, proc.stderr
    return [line for line in proc.stdout.splitlines() if line.startswith("SCOPE ")]


def test_the_launcher_runs_twelve_processes_one_per_scope_in_strict_order_plain_before_spy(tmp_path: Path) -> None:
    lines = dry_run_lines(tmp_path)
    assert len(lines) == 12
    scope = "SCOPE systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 setsid -w <python -c one-process>"
    assert all(line.startswith(scope) for line in lines)                                      # every process has its own scope, on cores 4-5, 3G, no swap
    tail = [line.split("<python -c one-process> ")[1].split() for line in lines]                  # arm world seed ticks mode tree out python
    assert [(t[0], t[2], t[4]) for t in tail] == [(arm, seed, mode) for seed in ("42", "45", "43") for arm in ("new", "base") for mode in ("plain", "spy")]
    assert [t[5] for t in tail[:4]] == ["/t/new", "/t/new", "/t/base", "/t/base"] and all(t[3] == "5000" and t[6] == "/o/cells" for t in tail)
    for i in range(0, 12, 2):                                                                     # in each cell the plain twin comes first, then the spy of the SAME cell
        assert tail[i][4] == "plain" and tail[i + 1][4] == "spy" and tail[i][:3] == tail[i + 1][:3]


def test_the_launcher_has_one_scope_site_and_no_parallel_process_start() -> None:
    text = LAUNCHER.read_text(encoding="utf-8")
    code = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    assert sum("systemd-run --user" in line for line in code) == 1                                # one site builds every scope command
    assert sum("SCOPE_CMD[@]" in line for line in code) == 1 and any('"${SCOPE_CMD[@]}" >> ' in line and line.rstrip().endswith("2>&1)") for line in code)   # run in the foreground, never with a trailing &
    assert "PYTHONDONTWRITEBYTECODE=1" in text and "setsid -w" in text and 'person_attack_run.py"' not in text      # no whole-run runner call any more


def test_the_one_process_code_runs_one_child_records_its_exit_and_propagates_the_return_code(tmp_path: Path) -> None:
    text = LAUNCHER.read_text(encoding="utf-8")
    code = text[text.index("ONE_PROCESS='") + len("ONE_PROCESS='"):text.index("sys.exit(result[\"returncode\"])'") + len("sys.exit(result[\"returncode\"])")]
    tree, out = tmp_path / "tree", tmp_path / "cells"          # an empty tree: the child fails at its imports at once (no world is built), which proves the plumbing only
    tree.mkdir()
    proc = subprocess.run([sys.executable, "-c", code, "new", "w", "42", "10", "plain", str(tree), str(out), sys.executable], cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT)}, capture_output=True, text=True, timeout=60)
    exit_doc = json.loads((out / "new__w__s42__plain.exit.json").read_text(encoding="utf-8"))
    assert proc.returncode == exit_doc["returncode"] != 0 and "seconds" in exit_doc and not (tree / "data" / "runs").exists()
