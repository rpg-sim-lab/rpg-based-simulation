"""The births spy (M1 births own-job instrument, rulings v2 Part C): counts K6, K6b, K8 and W1-W5 from the typed updates and the per-tick state, and writes the BALANCE facts.

It observes only: it wraps ``BirthService.process_births`` and ``ApplyPath.apply_generation`` to RECORD what they return and never changes an argument or a result, so the spied
run must hash equal to its plain twin. Every bar is a count that must be 0; the thresholds are fixed here, before any data, and are never judged after.

Limits stated up front (the run report repeats them): W4 is checked on the typed hunger update the births system returns (``hunger_delta == min(cost, 100 - hunger)``), not on the
mother's hunger after the tick, because other phases move hunger on the same tick; W5 treats a newborn's hunger drop as typed only when that tick's applied update held a
negative ``hunger_delta`` or a ``hunger_set`` for that newborn, and names the tick and id of every other drop.

Checks 3 and 6 (owner request, rulings 046589d5), BALANCE rows plus one bar:
- ``DeathWatch`` (check 3): every death with its typed cause, killer, kinds (``species_of``, never occupation), newborn flags, and the probes (live bodies and combatants
  within COMBAT_PROBE_RADIUS_TILES at the victim, births in the victim's or killer's region in the last BIRTH_WINDOW_TICKS), plus live entity-ticks and per-tick position digests.
- ``BirthSpy.nudges`` / ``BirthSpy.regionless`` / ``BirthSpy.applied_cohorts`` (check 6a): per (region, tick) the births system's own population_young_births_delta against
  the newborns it added in that region (the bar: total mismatch == 0), the regionless births with their tile (BALANCE), and the apply-side young-count change per applied nudge.
- ``CohortWatch`` (check 6b): per region per day the cohort counts, live bodies per kind, their difference and the divergence flags (BALANCE).
Calamity sends no nudge by design (calamity.py:57); it is a note in the output, not a miss.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from src.core.species import NON_LIVING_KIND_ALLOWLIST, species_of
from src.core.state import LifeStage
from src.engine.apply import ApplyPath
from src.engine.behavior_consumers import get_catalog
from src.engine.spatial_query import SpatialQueryService
from src.world.births import BirthService

DECLARED_ARRIVAL_SOURCES = frozenset({"AUTHORED_ARRIVAL"})  # W3: spawn-source kinds that count as a declared arrival; fixed before the run
CAMP_COUNT_RADIUS_TILES = 15.0  # G1b: a fixed stated value (no place declares a size the camp census can use); counted in Chebyshev tiles around CampState.position
DAY_TICKS = 2400
COMBAT_PROBE_RADIUS_TILES = 10.0  # check 3 probe (a): combatants counted within this Chebyshev radius of the victim; a fixed stated value
BIRTH_WINDOW_TICKS = 30  # check 3 probe (c): a birth in the victim's or killer's region within this many ticks before the death
CALAMITY_NOTE = "calamity sends no population nudge by design (src/world/calamity.py:57); not counted as a miss"


def region_id_at(state, position) -> Optional[str]:
    """The id of the region containing ``position``, or None (the births system's own rule for its nudge)."""
    region = SpatialQueryService.get_region_at(state, position)
    return region.id if region is not None else None


class BirthSpy:
    """Record-only wrapper over the births system and the apply path; ``install()`` patches, ``restore()`` undoes."""

    def __init__(self) -> None:
        self.fails: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.births: List[Dict[str, Any]] = []
        self.arrivals: Dict[int, str | None] = {}
        self.applied_hunger: Dict[int, Dict[int, bool]] = {}  # tick -> entity id -> a typed consume update was applied
        self.nudges: List[Dict[str, Any]] = []  # check 6a: per (tick, region) the births system's write against the newborns it added there
        self.regionless: List[Dict[str, Any]] = []  # check 6a BALANCE: births whose mother stood in no region (no nudge is written), with the newborn's tile
        self.applied_cohorts: List[Dict[str, Any]] = []  # check 6: the apply-side young-count change of every applied births nudge
        self._patched: List[tuple] = []

    def install(self) -> "BirthSpy":
        original_births = BirthService.__dict__["process_births"].__func__
        original_apply = ApplyPath.__dict__["apply_generation"].__func__

        def process_births(state, generator):
            update = original_births(state, generator)
            self._check_births(state, update)
            return update

        def apply_generation(prior_state, update, *args, **kwargs):
            for entity in update.entities_add:
                source = update.entity_spawn_sources.get(entity.id)
                self.arrivals[entity.id] = None if source is None else getattr(source.kind, "value", str(source.kind))
            consumed = {
                eid: True for eid, upd in update.entity_updates.items()
                if upd.biological is not None and (upd.biological.hunger_delta < 0 or upd.biological.hunger_set is not None)
            }
            self.applied_hunger[prior_state.tick] = consumed
            new_state = original_apply(prior_state, update, *args, **kwargs)
            self._record_cohort_application(prior_state, update, new_state)
            return new_state

        for owner, name, original, replacement in (
            (BirthService, "process_births", original_births, process_births),
            (ApplyPath, "apply_generation", original_apply, apply_generation),
        ):
            setattr(owner, name, staticmethod(replacement))
            self._patched.append((owner, name, original))
        return self

    def restore(self) -> None:
        for owner, name, original in reversed(self._patched):
            setattr(owner, name, staticmethod(original))
        self._patched.clear()

    # ---- per check -------------------------------------------------------------------------------------------------------------------------------
    def _check_births(self, state, update) -> None:
        catalog = get_catalog()
        parents_seen: Dict[int, int] = defaultdict(int)
        for child in update.entities_add:
            a, b = child.lifecycle.parent_a_entity_id, child.lifecycle.parent_b_entity_id
            row = {"tick": state.tick, "child": child.id, "mother": a, "mate": b, "kind": child.kind, "region": region_id_at(state, child.navigation.position)}
            self.births.append(row)
            if child.identity.occupation is not None or child.identity.life_stage != LifeStage.CHILD or a is None or b is None or child.lifecycle.birth_tick != state.tick:
                self.fails["W2"].append(row)
            mother, mate = state.entities.get(a), state.entities.get(b)
            if mother is None or mate is None:
                self.fails["W1"].append({**row, "why": "parent not in state"})
                continue
            for parent_id in (a, b):
                parents_seen[parent_id] += 1
            species = catalog.get_species(species_of(mother))
            profile = catalog.get_reproduction_profile(species.reproduction_profile) if species and species.reproduction_profile else None
            why = _w1_failures(state, mother, mate, profile)
            if why:
                self.fails["W1"].append({**row, "why": why})
            elif child.kind != species_of(mother) or species_of(mate) != species_of(mother):
                self.fails["K8"].append(row)
            hunger = update.entity_updates.get(a).biological.hunger_delta if update.entity_updates.get(a) and update.entity_updates[a].biological else None
            if profile is not None and hunger != min(profile.birth_hunger_cost, 100.0 - mother.biological.hunger):
                self.fails["W4"].append({**row, "typed_hunger_delta": hunger})
        for parent_id, n in parents_seen.items():
            if n > 1:
                self.fails["W1"].append({"tick": state.tick, "parent": parent_id, "why": "parent in more than one birth in one check"})
        self._record_nudges(state, update)

    def _record_nudges(self, state, update) -> None:
        """Check 6a: the births system's own write per region against the newborns it added in that region at this tick, from the returned update only."""
        written = {rid: wu.population_young_births_delta for rid, wu in update.world_updates.items() if wu.population_young_births_delta}
        added: Counter = Counter()
        for child in update.entities_add:
            rid = region_id_at(state, child.navigation.position)
            if rid is not None:
                added[rid] += 1
            mother = state.entities.get(child.lifecycle.parent_a_entity_id)
            if mother is not None and region_id_at(state, mother.navigation.position) is None:
                x, y = child.navigation.position
                self.regionless.append({"tick": state.tick, "child": child.id, "tile": [int(x), int(y)]})
        for rid in sorted(set(written) | set(added)):
            self.nudges.append({"tick": state.tick, "region": rid, "written": written.get(rid, 0), "added": added.get(rid, 0), "mismatch": written.get(rid, 0) - added.get(rid, 0)})

    def _record_cohort_application(self, prior_state, update, new_state) -> None:
        """Check 6 exactness, apply side: young count after - before for every applied births nudge, with the same-tick population_cohorts_set collision kept apart."""
        for rid, wu in update.world_updates.items():
            delta = wu.population_young_births_delta
            if not delta:
                continue
            before = _young_count(prior_state.regions.get(rid))
            after = _young_count(new_state.regions.get(rid))
            rebuilt = wu.population_cohorts_set
            base = before if rebuilt is None else (rebuilt["young"].count if "young" in rebuilt else 0)
            self.applied_cohorts.append({
                "tick": prior_state.tick, "region": rid, "delta": delta, "before": before, "after": after,
                "collision_with_rebuild": rebuilt is not None, "exact": after == base + delta,
            })


def _w1_failures(state, mother, mate, profile) -> List[str]:
    why: List[str] = []
    if profile is None:
        return ["species declares no profile"]
    for name, body in (("mother", mother), ("mate", mate)):
        if not (body.combat.alive and body.lifecycle.active and body.identity.life_stage == LifeStage.ADULT):
            why.append(f"{name} not an alive active ADULT")
        if max(body.lifecycle.reproduction_cooldowns.values(), default=0) > state.tick:
            why.append(f"{name} not past its interval")
    if mother.biological.hunger > profile.fed_line:
        why.append("mother above fed_line")
    if species_of(mate) != species_of(mother):
        why.append("mate of another species")
    (mx, my), (tx, ty) = mother.navigation.position, mate.navigation.position
    if max(abs(mx - tx), abs(my - ty)) > profile.mate_radius_tiles:
        why.append("mate out of range")
    return why


# ---- per tick, called by the runner after every kernel tick ------------------------------------------------------------------------------------------
class TickWatch:
    """K6, K6b, W3, W5 and the census facts, read from the state after each tick."""

    def __init__(self, spy: BirthSpy, start_state) -> None:
        self.spy, self.catalog = spy, get_catalog()
        self.allowed = set(self.catalog.species) | set(NON_LIVING_KIND_ALLOWLIST)
        self.t0_ids = set(start_state.entities)
        self.kind_at_first_sight = {e.id: e.kind for e in start_state.entities.values()}
        self.fails: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.newborn_hunger: Dict[int, float] = {}
        self.max_entity_id = max(start_state.entities, default=0)
        self.census: List[Dict[str, Any]] = []
        self.population: List[Dict[str, Any]] = []
        self._species_of = species_of
        self.sample(start_state)

    def after_tick(self, state) -> None:
        tick = state.tick
        self.max_entity_id = max(self.max_entity_id, max(state.entities, default=0))
        for e in state.entities.values():
            first = self.kind_at_first_sight.setdefault(e.id, e.kind)
            if first != e.kind:
                self.fails["K6b"].append({"tick": tick, "id": e.id, "from": first, "to": e.kind})
            if e.id not in self.t0_ids and e.id not in self.newborn_hunger and e.id in self.spy.arrivals:
                source = self.spy.arrivals[e.id]
                if e.kind not in self.allowed:
                    self.fails["K6"].append({"tick": tick, "id": e.id, "kind": e.kind})
                is_birth = source == "BIRTH" and e.lifecycle.parent_a_entity_id is not None and e.lifecycle.parent_b_entity_id is not None
                if not is_birth and source not in DECLARED_ARRIVAL_SOURCES:
                    self.fails["W3"].append({"tick": tick, "id": e.id, "kind": e.kind, "source": source})
                if is_birth:
                    self.newborn_hunger[e.id] = e.biological.hunger
                else:
                    self.newborn_hunger[e.id] = float("nan")
        consumed = self.spy.applied_hunger.get(tick - 1, {})
        for eid, before in list(self.newborn_hunger.items()):
            body = state.entities.get(eid)
            if body is None or before != before:
                continue
            if body.biological.hunger < before and not consumed.get(eid):
                self.fails["W5"].append({"tick": tick, "id": eid, "from": before, "to": body.biological.hunger, "path": "no typed hunger update applied for this newborn"})
            self.newborn_hunger[eid] = body.biological.hunger
        if tick % DAY_TICKS == 0:
            self.sample(state)

    def sample(self, state) -> None:
        by_kind: Dict[str, Dict[str, int]] = defaultdict(lambda: {"t0": 0, "newborn": 0})
        for e in state.entities.values():
            if e.combat.alive:
                by_kind[e.kind]["t0" if e.id in self.t0_ids else "newborn"] += 1
        self.population.append({"tick": state.tick, "alive_by_kind": {k: v for k, v in sorted(by_kind.items())}})
        self.census.append({"tick": state.tick, "camps": camp_census(state, self.t0_ids, self.catalog)})


def camp_census(state, t0_ids, catalog) -> Any:
    """G1b, fixed before any data: per camp, the bodies whose species equals CampState.kind exactly within CAMP_COUNT_RADIUS_TILES (Chebyshev) of its position, split newborn / t0. A camp whose kind is not a declared species is "unmapped"; a world with no camps is "0 camps"."""
    from src.core.species import species_of

    if not state.camps:
        return "0 camps"
    rows = {}
    for camp_id, camp in sorted(state.camps.items()):
        if catalog.get_species(camp.kind) is None:
            rows[camp_id] = "unmapped"
            continue
        near = [
            e for e in state.entities.values()
            if e.combat.alive and species_of(e) == camp.kind
            and max(abs(e.navigation.position[0] - camp.position[0]), abs(e.navigation.position[1] - camp.position[1])) <= CAMP_COUNT_RADIUS_TILES
        ]
        rows[camp_id] = {"kind": camp.kind, "t0": sum(1 for e in near if e.id in t0_ids), "newborn": sum(1 for e in near if e.id not in t0_ids)}
    return rows


def _young_count(region) -> int:
    cohort = region.population_cohorts.get("young") if region is not None else None
    return cohort.count if cohort is not None else 0


def _live(state):
    return [e for e in state.entities.values() if e.combat.alive]


# ---- check 3: deaths --------------------------------------------------------------------------------------------------------------------------------
class DeathWatch:
    """Check 3 (BALANCE): every death of this run with its cause, killer and the mechanism probes; live entity-ticks; per-tick original-body positions for the divergence probe."""

    def __init__(self, spy: Optional[BirthSpy], start_state) -> None:
        self.spy = spy
        self.t0_ids = set(start_state.entities)
        self.deaths: List[Dict[str, Any]] = []
        self.live_entity_ticks = 0
        self.positions: List[List[Any]] = []  # per tick: [[id, x, y], ...] of original (non-newborn) live bodies
        self._seen: set = set()
        self._prev = start_state

    def after_tick(self, state) -> None:
        prev = self._prev
        self.live_entity_ticks += len(_live(state))
        self.positions.append([[e.id, round(e.navigation.position[0], 3), round(e.navigation.position[1], 3)] for e in sorted(_live(state), key=lambda x: x.id) if e.id in self.t0_ids])
        births = self.spy.births if self.spy is not None else []
        for e in state.entities.values():
            record = e.lifecycle.death_record
            if record is None or record.tick != state.tick or e.id in self._seen:
                continue
            self._seen.add(e.id)
            killer = state.entities.get(record.last_attacker_id) if record.last_attacker_id is not None else None
            before = prev.entities.get(e.id)
            where = before.navigation.position if before is not None else e.navigation.position
            victim_region = region_id_at(state, where)
            killer_region = region_id_at(state, killer.navigation.position) if killer is not None else None
            near = sum(
                1 for o in _live(prev)
                if o.id != e.id and max(abs(o.navigation.position[0] - where[0]), abs(o.navigation.position[1] - where[1])) <= COMBAT_PROBE_RADIUS_TILES
            )
            recent = lambda region: region is not None and any(b["region"] == region and state.tick - BIRTH_WINDOW_TICKS <= b["tick"] <= state.tick for b in births)
            self.deaths.append({
                "tick": state.tick, "victim": e.id, "victim_kind": species_of(e), "cause": record.cause.value, "killer": record.last_attacker_id,
                "killer_kind": species_of(killer) if killer is not None else None,
                "victim_newborn": e.id not in self.t0_ids, "killer_newborn": record.last_attacker_id is not None and record.last_attacker_id not in self.t0_ids,
                "live_before": len(_live(prev)), "combatants_within_radius": near,
                "victim_region": victim_region, "killer_region": killer_region,
                "birth_in_victim_region_recent": recent(victim_region), "birth_in_killer_region_recent": recent(killer_region),
            })
        self._prev = state


# ---- check 6b: cohort count against real bodies -------------------------------------------------------------------------------------------------------
class CohortWatch:
    """Check 6b (BALANCE): per region per day, the cohort counts, live bodies per kind in that region, their difference and the divergence flags."""

    def __init__(self, start_state) -> None:
        self.rows: List[Dict[str, Any]] = []
        self.flags: List[Dict[str, Any]] = []
        self._last: Dict[str, Dict[str, int]] = {}
        self.sample(start_state)

    def after_tick(self, state) -> None:
        if state.tick % DAY_TICKS == 0:
            self.sample(state)

    def sample(self, state) -> None:
        bodies: Dict[str, Counter] = defaultdict(Counter)
        for e in _live(state):
            rid = region_id_at(state, e.navigation.position)
            if rid is not None:
                bodies[rid][species_of(e)] += 1
        for rid, region in sorted(state.regions.items()):
            cohort_total = sum(c.count for c in region.population_cohorts.values())
            live = sum(bodies[rid].values())
            row = {"tick": state.tick, "region": rid, "cohort_total": cohort_total, "cohort_young": _young_count(region), "live_by_kind": dict(sorted(bodies[rid].items())), "live_total": live, "difference": cohort_total - live}
            self.rows.append(row)
            last = self._last.get(rid)
            if last is not None and ((cohort_total > last["cohort"] and live == 0) or (cohort_total == 0 and live > last["live"])):
                self.flags.append({**row, "prev_cohort_total": last["cohort"], "prev_live_total": last["live"]})
            self._last[rid] = {"cohort": cohort_total, "live": live}
