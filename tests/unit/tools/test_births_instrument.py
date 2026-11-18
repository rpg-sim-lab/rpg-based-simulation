# Compliance IDs: WORLD-122
"""The births own-job instrument, M1 reproduction rows: one positive control per row (a hand-built wrong tick the row must flag) beside the clean twin it must not, the trigger shims, and the pure reports."""
import dataclasses

import pytest

from src.core.builder import V2EntityBuilder
from src.core.models.inventory import ItemStack
from src.core.models.world_records import CorpseState
from src.core.pregnancy import PregnancyState
from src.core.spawn_source import SpawnKind, SpawnSource
from src.core.state import AuthoritativeState, SocialBond
from src.core.updates import EntityUpdate, LifecycleUpdate, StateUpdate
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
from src.engine.apply import ApplyPath
from src.engine.cadence import SystemCadence
from src.engine.phase_graph import PhaseDependencyGraph
from src.systems.lifecycle_systems.genetics import GeneticProfile
from src.systems.world_systems.generator import EntityGenerator, NoFreeSpawnTileError
from src.world import births, risen
from tools.rpg_measure import births_run
from tools.rpg_measure.births_spy import BirthSpy, TickWatch, _ReadCounter
from tools.rpg_measure.births_trigger import TriggerShim


def _body(entity_id, kind="human", pos=(5.0, 5.0), **kw):
    return V2EntityBuilder(entity_id).kind(kind).location(*pos).build()


def _preg(father=2, conceived=0, due=30, litter=1):
    return PregnancyState(father_entity_id=father, conceived_tick=conceived, due_tick=due, litter_size=litter, father_genetic_profile=GeneticProfile())


def _with_pregnancy(body, pregnancy):
    return dataclasses.replace(body, lifecycle=dataclasses.replace(body.lifecycle, pregnancy=pregnancy))


def _with_bonds(body, bonds):
    return dataclasses.replace(body, social=dataclasses.replace(body.social, bonds=bonds))


def _state(*bodies, tick=30, corpses=()):
    return AuthoritativeState(tick=tick, seed=42, entities={b.id: b for b in bodies}, corpses={c.id: c for c in corpses}, next_entity_id=max(b.id for b in bodies) + 1)


def _conception(mother_id=1, **kw):
    return StateUpdate(entity_updates={mother_id: EntityUpdate(entity_id=mother_id, lifecycle=LifecycleUpdate(pregnancy_set=_preg(**{"conceived": 30, "due": 2430, **kw})))})


def _check(spy, state, update):
    catalog = births.get_catalog()
    spy._check_conceptions(state, update, catalog)
    return {k: len(v) for k, v in spy.fails.items()}


# ---- conception rows -------------------------------------------------------------------------------------------------------------------------------
def test_g5_a_bond_conception_needs_a_marriage_or_both_sentiments_and_a_clean_pair_has_no_fail():
    fond = lambda i, j, v: _with_bonds(_body(i), {j: SocialBond(target_id=j, sentiment=v)})
    assert _check(BirthSpy(), _state(_body(1), _body(2)), _conception()) == {"G5": 1}
    assert _check(BirthSpy(), _state(fond(1, 2, 0.8), fond(2, 1, 0.8)), _conception()) == {}
    assert _check(BirthSpy(), _state(fond(1, 2, 0.8), fond(2, 1, 0.79)), _conception()) == {"G5": 1}


def test_g3_a_pregnant_mother_or_mate_and_a_wrong_due_tick_are_flagged():
    fond = lambda i, j: _with_bonds(_body(i), {j: SocialBond(target_id=j, sentiment=0.9)})
    pregnant_mother = _with_pregnancy(fond(1, 2), _preg(father=9))
    assert _check(BirthSpy(), _state(pregnant_mother, fond(2, 1)), _conception()) == {"G3": 1}
    pregnant_mate = _with_pregnancy(fond(2, 1), _preg(father=9))
    assert _check(BirthSpy(), _state(fond(1, 2), pregnant_mate), _conception()) == {"G3": 1}
    assert _check(BirthSpy(), _state(fond(1, 2), fond(2, 1)), _conception(due=2431)) == {"G3": 1}


def test_k8_and_the_litter_table_at_conception():
    wolf = lambda i: _body(i, kind="wolf")
    human = _with_bonds(_body(2), {1: SocialBond(target_id=1, sentiment=0.9)})
    flags = _check(BirthSpy(), _state(wolf(1), human), _conception())
    assert flags.get("K8") == 1 and flags.get("W1") == 1
    assert _check(BirthSpy(), _state(wolf(1), wolf(2)), _conception(due=1230, litter=9)) == {"G2": 1}, "a litter of 9 is not in the wolf table"
    assert _check(BirthSpy(), _state(wolf(1), wolf(2)), _conception(due=1230, litter=5)) == {}


def test_g5_a_none_species_makes_no_social_read_and_the_counting_proxy_sees_a_read_if_one_happens():
    spy = BirthSpy()
    proxy = _ReadCounter(_body(1, kind="wolf"), spy)
    assert proxy.id == 1 and proxy.navigation is not None
    assert spy.none_gate_reads == 0
    proxy.social
    assert spy.none_gate_reads == 1


# ---- births at term --------------------------------------------------------------------------------------------------------------------------------
class _Certain:
    def __init__(self, real):
        self._real = real

    def get_reproduction_profile(self, profile_id):
        return self._real.get_reproduction_profile(profile_id).model_copy(update={"birth_chance_per_check": 1.0, "mate_gate": "none", "min_mutual_sentiment": None, "litter_weights": {1: 1.0}})

    def __getattr__(self, name):
        return getattr(self._real, name)


def _term_run(monkeypatch, state, generator_hook=None, spy=None):
    real = births.get_catalog()
    monkeypatch.setattr(births, "get_catalog", lambda: _Certain(real))
    generator = EntityGenerator(state.seed + state.tick)
    generator._last_id = state.next_entity_id - 1
    if generator_hook:
        generator_hook(generator)
    spy = spy or BirthSpy().install()
    try:
        update = births.BirthService.process_births(state, generator)
    finally:
        spy.restore()
    return spy, update


def test_a_clean_birth_at_term_has_no_fail_and_g1_flags_a_birth_at_another_tick(monkeypatch):
    spy, update = _term_run(monkeypatch, _state(_with_pregnancy(_body(1), _preg(due=30)), _body(2)))
    assert update.entities_add and not spy.fails and len(spy.births) == 1
    spy, _ = _term_run(monkeypatch, _state(_with_pregnancy(_body(1), _preg(due=20)), _body(2)))
    assert {k: len(v) for k, v in spy.fails.items()} == {"G1": 1}


def test_g2_born_plus_unplaced_is_the_litter_and_an_unplaceable_litter_is_not_a_fail_but_a_missing_newborn_is(monkeypatch):
    def no_tile(generator):
        generator.free_spawn_position = lambda pos, st: (_ for _ in ()).throw(NoFreeSpawnTileError("none"))
    spy, update = _term_run(monkeypatch, _state(_with_pregnancy(_body(1), _preg(due=30)), _body(2)), generator_hook=no_tile)
    assert not update.entities_add and len(spy.unplaced) == 1 and not spy.fails
    state = _state(_with_pregnancy(_body(1), _preg(due=30, litter=2)), _body(2))
    clean = BirthSpy()
    clean._check_births_at_term(state, StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, lifecycle=LifecycleUpdate(pregnancy_clear=True))}), births.get_catalog())
    assert {k: len(v) for k, v in clean.fails.items()} == {"G2": 1}


def test_g4_a_second_birth_for_one_pregnancy_and_a_pregnancy_left_set_are_flagged(monkeypatch):
    state = _state(_with_pregnancy(_body(1), _preg(due=30)), _body(2))
    spy, update = _term_run(monkeypatch, state)
    spy._check_births_at_term(state, update, births.get_catalog())
    assert [r["why"] for r in spy.fails["G4"]] == ["a second birth for one pregnancy"]
    uncleared = BirthSpy()
    child = update.entities_add[0]
    uncleared._check_births_at_term(state, StateUpdate(entities_add=[child]), births.get_catalog())
    assert any("not cleared" in r["why"] for r in uncleared.fails["G4"])


def test_a_dead_father_at_term_is_counted_balance_and_a_bond_toward_him_is_a_g1_row(monkeypatch):
    father = dataclasses.replace(_body(2), combat=dataclasses.replace(_body(2).combat, alive=False))
    spy, update = _term_run(monkeypatch, _state(_with_pregnancy(_body(1), _preg(due=30)), father))
    assert spy.father_dead_at_term == 1 and not spy.fails
    assert 2 not in update.entity_updates or update.entity_updates[2].social is None


def test_w4_a_cost_with_no_newborn_born_is_flagged():
    from src.core.updates import BiologicalUpdate

    state = _state(_with_pregnancy(_body(1), _preg(due=30)), _body(2))
    spy = BirthSpy()
    spy._check_births_at_term(state, StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, lifecycle=LifecycleUpdate(pregnancy_clear=True), biological=BiologicalUpdate(hunger_delta=25.0))},
                                                 world_events_add=[WorldEvent(category=WorldEventCategory.NEWBORN_UNPLACED, tick=30, subject="1", payload={"litter_slot": 0})]), births.get_catalog())
    assert [r.get("why") for r in spy.fails["W4"]] == ["a cost with no newborn born"]


# ---- G6 ---------------------------------------------------------------------------------------------------------------------------------------------
def test_g6_a_dead_body_holding_a_pregnancy_is_flagged_once_and_a_pregnancy_ended_after_a_birth_is_flagged():
    dead = dataclasses.replace(_with_pregnancy(_body(1), _preg()), combat=dataclasses.replace(_body(1).combat, alive=False))
    spy = BirthSpy()
    watch = TickWatch(spy, _state(_body(2), tick=0))
    watch.after_tick(_state(dead, _body(2), tick=5))
    watch.after_tick(_state(dead, _body(2), tick=6))
    assert len(watch.fails["G6"]) == 1
    state = _state(_with_pregnancy(_body(1), _preg(due=30)), _body(2))
    spy._born_by[30].add(1)
    spy._record_pregnancy_ended(state, StateUpdate(world_events_add=[WorldEvent(category=WorldEventCategory.PREGNANCY_ENDED, tick=30, subject="1", payload={"reason": "MOTHER_DIED", "litter_size": 1})]))
    assert len(spy.fails["G6"]) == 1 and len(spy.ended) == 1
    clean = BirthSpy()
    clean._record_pregnancy_ended(state, StateUpdate(world_events_add=[WorldEvent(category=WorldEventCategory.PREGNANCY_ENDED, tick=30, subject="1", payload={"reason": "MOTHER_DIED", "litter_size": 1})]))
    assert not clean.fails and len(clean.ended) == 1


# ---- risen ------------------------------------------------------------------------------------------------------------------------------------------
GOODS = [ItemStack(item_id="raw_meat", quantity=3), ItemStack(item_id="iron_sword", quantity=1), ItemStack(item_id="potion", quantity=2)]


class _Rise:
    def __init__(self, real):
        self._real = real

    def get_risen_profile(self, profile_id):
        return self._real.get_risen_profile(profile_id).model_copy(update={"rise_chance_per_check": 1.0})

    def __getattr__(self, name):
        return getattr(self._real, name)


def _rise_state():
    dead = dataclasses.replace(_body(1), combat=dataclasses.replace(_body(1).combat, alive=False))
    corpse = CorpseState(id=1000001, original_entity_id=1, position=(5.0, 5.0), items=list(GOODS), decay_tick=400, gold=7)
    return _state(dead, tick=60, corpses=[corpse])


def _rise_run(monkeypatch, tamper=None):
    real = risen.get_catalog()
    monkeypatch.setattr(risen, "get_catalog", lambda: _Rise(real))
    if tamper is not None:
        tamper(monkeypatch)
    state = _rise_state()
    spy = BirthSpy().install()
    try:
        update = risen.RisenService.process_rises(state, StateUpdate(), SystemCadence())
        ApplyPath.apply_generation(state, update, 61, 61)
    finally:
        spy.restore()
    return spy


def test_r1_to_r4_a_clean_rising_has_no_fail_and_each_tampered_rising_is_flagged(monkeypatch):
    clean = _rise_run(monkeypatch)
    assert len(clean.risings) == 1 and not clean.fails and clean.risen_ok == {clean.risings[0]["risen"]: True}

    def drop_items(mp):
        original = risen.corpse_remains
        mp.setattr(risen, "corpse_remains", lambda corpse, tick, next_id: dataclasses.replace(original(corpse, tick, next_id), ground_items=()))
    assert [r["why"] if "why" in r else "R2" for r in _rise_run(monkeypatch, drop_items).fails["R2"]] == ["R2"]

    def with_job(mp):
        from src.entities.archetype_factory import ArchetypeEntityFactory
        original = ArchetypeEntityFactory.build_risen
        mp.setattr(ArchetypeEntityFactory, "build_risen", lambda self, *a, **k: (lambda b: dataclasses.replace(b, identity=dataclasses.replace(b.identity, occupation="guard")))(original(self, *a, **k)))
    assert len(_rise_run(monkeypatch, with_job).fails["R4"]) == 1


def test_r1_a_corpse_risen_from_twice_and_a_source_that_never_existed_are_flagged():
    spy = BirthSpy()
    state = _rise_state()
    body = _body(5, kind="undead")
    update = StateUpdate(entities_add=[body], entity_spawn_sources={5: SpawnSource(SpawnKind.RISEN, source_corpse_id=1000001, original_entity_id=1)})
    new_state = dataclasses.replace(state, entities={**state.entities, 5: body}, corpses={})
    spy._check_risings(state, update, new_state)
    spy._check_risings(state, update, new_state)
    assert len(spy.fails["R1"]) == 1, "the second rising from the same corpse"
    ghost = StateUpdate(entities_add=[body], entity_spawn_sources={5: SpawnSource(SpawnKind.RISEN, source_corpse_id=999, original_entity_id=1)})
    other = BirthSpy()
    other._check_risings(state, ghost, new_state)
    assert len(other.fails["R1"]) == 1 and other.risen_ok == {5: False}


# ---- the trigger shims ------------------------------------------------------------------------------------------------------------------------------
def _trigger_inputs():
    state = _rise_state()
    from src.core.dirty import DirtySetBuilder

    update = StateUpdate(dirty_set=DirtySetBuilder().build())
    return state, update, SystemCadence()


def test_the_off_shim_never_fires_on_a_corpse_at_a_rise_check_and_the_on_shim_counts_one_firing_and_one_extra_run():
    state, update, cadence = _trigger_inputs()
    baseline = PhaseDependencyGraph.should_run_phase("resource_transactions", state, update, cadence)
    assert baseline is True, "the real trigger makes the phase run on a rise check with a corpse"
    off = TriggerShim().install("off")
    try:
        assert PhaseDependencyGraph.should_run_phase("resource_transactions", state, update, cadence) is False
        assert off.counts() == {"firings": 0, "extra_phase_runs": 0, "first_firing_tick": None}
    finally:
        off.restore()
    on = TriggerShim().install("on")
    try:
        assert PhaseDependencyGraph.should_run_phase("resource_transactions", state, update, cadence) is True
        assert on.counts() == {"firings": 1, "extra_phase_runs": 1, "first_firing_tick": 60}
    finally:
        on.restore()
    assert PhaseDependencyGraph.should_run_phase("resource_transactions", state, update, cadence) is True
    from src.engine import phase_graph
    assert phase_graph.rise_triggers_phase is risen.rise_triggers_phase, "restored"


# ---- the pure reports -------------------------------------------------------------------------------------------------------------------------------
def _arm(final="h", events="e", metrics="m", firings=3, extra=3, corpses=0, ticks=1000):
    return {"final_hash": final, "event_digest": events, "metrics_digest": metrics, "trigger": {"firings": firings, "extra_phase_runs": extra, "first_firing_tick": 90}, "corpses_at_t0": corpses, "ticks": ticks}


def test_trigger_cell_pass_fail_vacuous_and_the_control_that_cannot_fail():
    on, off = _arm(), _arm(firings=0, extra=0)
    pos = _arm(final="other")
    assert births_run.trigger_cell(on, off, pos)["verdict"] == "PASS"
    assert births_run.trigger_cell(_arm(metrics="x"), off, pos)["verdict"] == "FAIL"
    assert births_run.trigger_cell(_arm(final="x"), off, pos)["verdict"] == "FAIL"
    assert births_run.trigger_cell(on, _arm(firings=1, extra=0), pos)["verdict"] == "FAIL", "OFF must fire 0 times"
    assert births_run.trigger_cell(on, off, _arm())["verdict"] == "FAIL", "a positive control equal to OFF cannot fail"
    assert births_run.trigger_cell(_arm(extra=0), off, pos)["verdict"] == "FAIL", "ON ran no extra phase run"
    assert births_run.trigger_cell(_arm(corpses=1), off, pos)["verdict"] == "FAIL"
    assert births_run.trigger_cell(_arm(firings=0, extra=0), off, pos)["verdict"] == "VACUOUS"


def test_trigger_report_stops_a_world_with_no_firing_cell():
    docs = {("w", 42, "trigger_on"): _arm(firings=0, extra=0), ("w", 42, "trigger_off"): _arm(firings=0, extra=0), ("w", 42, "trigger_pos"): _arm(final="o")}
    report = births_run.trigger_report(docs)
    assert report["worlds_with_no_firing"] == ["w"] and report["verdict"] == "STOP"


def _costs(per_tick, live=50, n=100, spike=None):
    rows = [[t, per_tick, per_tick, per_tick, per_tick, per_tick * 4, live] for t in range(1, n + 1)]
    if spike:
        rows[spike][5] = per_tick * 400
    return rows


def test_stage_stats_drop_stall_ticks_and_report_the_cost_per_entity_tick():
    stats = births_run.stage_stats(_costs(2.0, spike=10), 1)
    assert stats["stall_ticks_dropped"] == 1 and stats["median_ms"] == 2.0 and stats["ms_per_entity_tick"] == pytest.approx(2.0 / 50)
    assert births_run.stage_stats([], 1) == {"ticks": 0}


def _cost_doc(per_tick):
    return {"phase_costs": _costs(per_tick), "host": [{"tick": 0, "loadavg": ["0.1", "0", "0"], "steal_jiffies": 0, "mem_available_kb": 5}]}


def test_cost_report_flags_a_single_cell_jump_and_a_jump_held_across_cells_and_stays_quiet_on_noise():
    quiet = {}
    for world in ("a", "b", "c"):
        quiet[(world, 42, "plain")], quiet[(world, 42, "plain_r2")] = _cost_doc(2.0), _cost_doc(2.02)
        quiet[(world, 42, "main")], quiet[(world, 42, "main_r2")] = _cost_doc(2.0), _cost_doc(2.0)
    report = births_run.cost_report(quiet)
    assert report["single_cell_jumps"] == [] and report["jumps_held_across_cells"] == {}
    jump = {k: (_cost_doc(3.2) if k[2].startswith("plain") else d) for k, d in quiet.items() if k[0] == "a"}
    assert births_run.cost_report(jump)["single_cell_jumps"], "a 60 percent jump in one cell is flagged"
    held = {k: (_cost_doc(2.4) if k[2].startswith("plain") else d) for k, d in quiet.items()}
    assert births_run.cost_report(held)["jumps_held_across_cells"].get("economy"), "a 20 percent gap in all three cells is held across cells"


def test_bar_status_stops_on_zero_risings_and_the_summary_keeps_the_new_bars():
    assert births_run.bar_status(5, 5, {"R1": 0}, True, 0, risings=0) == "STOP"
    assert births_run.bar_status(5, 5, {"R1": 0}, True, 0, risings=2) == "PASS"
    assert births_run.bar_status(5, 5, {"G6": 1}, True, 0, risings=2) == "FAIL"
    assert {"G1", "G2", "G3", "G4", "G5", "G6", "R1", "R2", "R3", "R4"} <= set(births_run.BARS)


def test_obs_check_judge_passes_only_when_both_arms_equal_and_the_write_control_differs():
    from tools.rpg_measure import births_obs_check

    row = lambda h: {"final_hash": h}
    assert births_obs_check.judge({"recording_on": row("a"), "no_replay": row("a"), "obs_off": row("a"), "write_control": row("b")})["verdict"] == "PASS"
    assert births_obs_check.judge({"recording_on": row("a"), "no_replay": row("x"), "obs_off": row("a"), "write_control": row("b")})["verdict"] == "FAIL"
    assert births_obs_check.judge({"recording_on": row("a"), "no_replay": row("a"), "obs_off": row("a"), "write_control": row("a")})["verdict"] == "FAIL", "a control that does not differ cannot fail"
