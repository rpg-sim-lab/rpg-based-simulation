# Compliance IDs: WORLD-122
"""The births own-job instrument: its mechanical aggregations and the two positive controls (one known birth applies +1 to its region; one known combat death appears once)."""
import dataclasses


from src.core.builder import V2EntityBuilder
from src.core.death_cause import DeathCause, DeathRecord
from src.core.state import AuthoritativeState, RegionState
from src.engine.apply import ApplyPath
from src.world import births
from tools.rpg_measure import births_run
from tools.rpg_measure.births_spy import BirthSpy, CohortWatch, DeathWatch


def _human(entity_id, pos=(5.0, 5.0)):
    return V2EntityBuilder(entity_id).kind("human").location(*pos).build()


class _Certain:
    def __init__(self, real):
        self._real = real

    def get_reproduction_profile(self, profile_id):
        return self._real.get_reproduction_profile(profile_id).model_copy(update={"birth_chance_per_check": 1.0})

    def __getattr__(self, name):
        return getattr(self._real, name)


def _due(entity, father_id=2, due_tick=30, litter=1):
    """`entity` as a mother due at `due_tick`: a births check at that tick bears her litter."""
    from src.core.pregnancy import PregnancyState
    from src.systems.lifecycle_systems.genetics import GeneticProfile

    pregnancy = PregnancyState(father_entity_id=father_id, conceived_tick=due_tick - 2400, due_tick=due_tick, litter_size=litter, father_genetic_profile=GeneticProfile())
    return dataclasses.replace(entity, lifecycle=dataclasses.replace(entity.lifecycle, pregnancy=pregnancy))


def _generator(state):
    from src.systems.world_systems.generator import EntityGenerator

    generator = EntityGenerator(state.seed + state.tick)
    generator._last_id = state.next_entity_id - 1
    return generator


def test_positive_control_one_known_birth_applies_exactly_plus_one_to_its_region(monkeypatch):
    real = births.get_catalog()
    monkeypatch.setattr(births, "get_catalog", lambda: _Certain(real))
    region = RegionState(id="town", name="Town", kind="town", bounds=(0, 0, 100, 100), population_cohorts={})
    state = AuthoritativeState(tick=30, seed=42, regions={"town": region}, entities={1: _due(_human(1)), 2: _human(2)}, next_entity_id=3)
    spy = BirthSpy().install()
    try:
        update = births.BirthService.process_births(state, _generator(state))
        after = ApplyPath.apply_generation(state, update, 31, 31)
    finally:
        spy.restore()
    assert [(r["region"], r["written"], r["added"], r["mismatch"]) for r in spy.nudges] == [("town", 1, 1, 0)]
    assert births_run.mismatch_total(spy.nudges) == 0
    (applied,) = spy.applied_cohorts
    assert (applied["delta"], applied["before"], applied["after"], applied["exact"], applied["collision_with_rebuild"]) == (1, 0, 1, True, False)
    assert after.regions["town"].population_cohorts["young"].count == 1
    assert spy.regionless == []


def test_a_birth_outside_every_region_is_counted_regionless_with_its_tile_and_writes_no_nudge(monkeypatch):
    real = births.get_catalog()
    monkeypatch.setattr(births, "get_catalog", lambda: _Certain(real))
    region = RegionState(id="town", name="Town", kind="town", bounds=(0, 0, 10, 10), population_cohorts={})
    state = AuthoritativeState(tick=30, seed=42, regions={"town": region}, entities={1: _due(_human(1, (50.0, 50.0))), 2: _human(2, (50.0, 50.0))}, next_entity_id=3)
    spy = BirthSpy().install()
    try:
        births.BirthService.process_births(state, _generator(state))
    finally:
        spy.restore()
    assert spy.nudges == [] and len(spy.regionless) == 1 and len(spy.regionless[0]["tile"]) == 2


def _dead(entity, killer_id, tick):
    return dataclasses.replace(
        entity, combat=dataclasses.replace(entity.combat, alive=False),
        lifecycle=dataclasses.replace(entity.lifecycle, active=False, death_record=DeathRecord(cause=DeathCause.COMBAT, tick=tick, last_attacker_id=killer_id)),
    )


def test_positive_control_one_known_combat_death_appears_once_in_the_per_cause_table():
    killer, victim = _human(1), _human(2, (6.0, 5.0))
    start = AuthoritativeState(tick=0, seed=1, entities={1: killer, 2: victim}, next_entity_id=3)
    watch = DeathWatch(None, start)
    watch.after_tick(dataclasses.replace(start, tick=1))
    watch.after_tick(AuthoritativeState(tick=2, seed=1, entities={1: killer, 2: _dead(victim, 1, 2)}, next_entity_id=3))
    docs = {("w", 1, "spied"): {"deaths": watch.deaths, "live_entity_ticks": watch.live_entity_ticks}}
    table = births_run.death_tables({**docs, ("w", 1, "control"): {"deaths": [], "live_entity_ticks": 2}})
    assert table["per_cause"]["spied|w|COMBAT|1"]["deaths"] == 1
    assert table["kill_matrix"] == {"spied|human->human": 1}
    assert (watch.deaths[0]["killer"], watch.deaths[0]["victim_newborn"], watch.deaths[0]["killer_newborn"]) == (1, False, False)
    assert watch.deaths[0]["combatants_within_radius"] == 1 and watch.live_entity_ticks == 2 + 1


def test_cohort_watch_flags_a_cohort_that_rises_while_its_live_bodies_fall_to_zero():
    from src.domains.demographics.cohort import PopulationCohort

    def state(tick, young, entities):
        region = RegionState(id="r", name="R", kind="town", bounds=(0, 0, 100, 100), population_cohorts={"young": PopulationCohort(bracket="young", count=young)})
        return AuthoritativeState(tick=tick, seed=1, regions={"r": region}, entities=entities, next_entity_id=10)

    watch = CohortWatch(state(0, 1, {1: _human(1)}))
    watch.sample(state(2400, 5, {}))
    assert len(watch.rows) == 2 and len(watch.flags) == 1 and watch.flags[0]["live_total"] == 0


def test_the_mechanical_verdicts():
    assert births_run.mismatch_total([{"mismatch": 0}, {"mismatch": 1}, {"mismatch": -1}]) == 2
    assert births_run.ratio_verdict({1: 1.2, 2: 3.0}) == "holds"
    assert births_run.ratio_verdict({1: 1.2, 2: 1.0}) == "mixed" and births_run.ratio_verdict({1: 1.2, 2: None}) == "mixed" and births_run.ratio_verdict({}) == "mixed"
    assert births_run.rate_ratio(2.0, 1.0) == 2.0 and births_run.rate_ratio(1.0, 0) == float("inf") and births_run.rate_ratio(0, 0) is None
    assert births_run.bar_status(0, 0, {}, True, 0) == "STOP" and births_run.bar_status(5, 0, {}, True, 0) == "STOP"
    assert births_run.bar_status(5, 5, {"K6": 0}, True, 0) == "PASS"
    assert births_run.bar_status(5, 5, {"K6": 1}, True, 0) == "FAIL" and births_run.bar_status(5, 5, {}, False, 0) == "FAIL" and births_run.bar_status(5, 5, {}, True, 2) == "FAIL"
    a = [[[1, 0.0, 0.0], [2, 1.0, 1.0]], [[1, 0.0, 0.0], [2, 1.0, 1.0]], [[1, 0.0, 0.0], [2, 2.0, 1.0]]]
    b = [[[1, 0.0, 0.0], [2, 1.0, 1.0]], [[1, 0.0, 0.0], [2, 1.0, 1.0]], [[1, 0.0, 0.0], [2, 1.0, 1.0]]]
    assert births_run.first_position_divergence(a, b) == {"tick": 3, "ids": [2]} and births_run.first_position_divergence(a, a) is None


def test_a_newborn_placed_across_a_border_gives_mismatch_zero_and_one_crossing():
    from src.core.updates import StateUpdate, WorldUpdate

    a = RegionState(id="A", name="A", kind="town", bounds=(0, 0, 10, 10), population_cohorts={})
    b = RegionState(id="B", name="B", kind="town", bounds=(10, 0, 20, 10), population_cohorts={})
    mother, mate = _human(1, (9.5, 5.0)), _human(2, (9.0, 5.0))
    child = (
        V2EntityBuilder(3).kind("human").location(10.5, 5.0).birth_record(parent_a_entity_id=1, parent_b_entity_id=2, birth_tick=30).build()
    )
    state = AuthoritativeState(tick=30, seed=1, regions={"A": a, "B": b}, entities={1: mother, 2: mate}, next_entity_id=3)
    update = StateUpdate(entities_add=[child], world_updates={"A": WorldUpdate(region_id="A", population_young_births_delta=1)})
    spy = BirthSpy()
    spy._record_nudges(state, update)
    assert [(r["region"], r["written"], r["added"], r["mismatch"]) for r in spy.nudges] == [("A", 1, 1, 0)]
    assert births_run.mismatch_total(spy.nudges) == 0
    assert [(c["mother_region"], c["newborn_region"]) for c in spy.border_crossings] == [("A", "B")] and spy.regionless == []


def test_negative_control_a_births_write_to_a_region_other_than_the_mothers_gives_a_nonzero_mismatch():
    from src.core.updates import StateUpdate, WorldUpdate

    a = RegionState(id="A", name="A", kind="town", bounds=(0, 0, 10, 10), population_cohorts={})
    b = RegionState(id="B", name="B", kind="town", bounds=(10, 0, 20, 10), population_cohorts={})
    mother, mate = _human(1, (5.0, 5.0)), _human(2, (6.0, 5.0))
    child = V2EntityBuilder(3).kind("human").location(5.0, 5.0).birth_record(parent_a_entity_id=1, parent_b_entity_id=2, birth_tick=30).build()
    state = AuthoritativeState(tick=30, seed=1, regions={"A": a, "B": b}, entities={1: mother, 2: mate}, next_entity_id=3)
    wrong = StateUpdate(entities_add=[child], world_updates={"B": WorldUpdate(region_id="B", population_young_births_delta=1)})
    spy = BirthSpy()
    spy._record_nudges(state, wrong)
    assert {(r["region"], r["mismatch"]) for r in spy.nudges} == {("A", -1), ("B", 1)} and births_run.mismatch_total(spy.nudges) == 2
