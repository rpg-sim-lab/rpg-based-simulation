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

M1 reproduction rows (rulings of 2026-11-18, fixed before any data; every count must be 0):
- conception (at the check): W1 as re-stated, G3 (a pregnant mother or a pregnant mate; ``due_tick != conceived + gestation``), G5 (the gate, re-derived here from the accepted marriage and
  the two directed sentiments, never from the gate code; plus every social read on a ``none`` species), K8 (same species), the litter size drawn from the declared table (G2);
- birth (at term): G1 (born at ``due_tick`` by the recorded father), G2 (born + unplaced == the litter drawn), G4 (cleared with the birth, one birth per pregnancy), W1 at birth (mother alive
  and active only), W4 (cost once per birth event), K8 (child kind == the mother's species), 6a (the MOTHER's region at the birth tick, from her position in the state the births call reads);
- G6 (no PregnancyState on a dead body, read from the state after every tick) and the PREGNANCY_ENDED events (none for a mother who bore on the same tick);
- risen R1-R4 (the corpse existed and is consumed once; the goods leave exactly, read from the APPLIED state; the kind declares the profile and the dead body's species is a source; a new subject).
"""
from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from src.core.species import NON_LIVING_KIND_ALLOWLIST, species_of
from src.core.state import LifeStage
from src.core.strategic import MarriageStatus
from src.domains.world_emergence.schema import WorldEventCategory
from src.engine.apply import ApplyPath
from src.engine.behavior_consumers import get_catalog
from src.engine.spatial_query import SpatialQueryService
from src.systems.social_systems.relationships import RelationshipService
from src.world import births as births_module
from src.world.births import BirthService

DECLARED_ARRIVAL_SOURCES = frozenset({"AUTHORED_ARRIVAL"})  # W3: spawn-source kinds that count as a declared arrival; fixed before the run (RISEN counts only with its source corpse present)
FRIEND_LINE = RelationshipService.FRIEND_SENTIMENT_THRESHOLD  # G5: the named sentiment line of the bond gate, read from its own module, not from the gate code
RAW_MEAT = "raw_meat"
CAMP_COUNT_RADIUS_TILES = 15.0  # G1b: a fixed stated value (no place declares a size the camp census can use); counted in Chebyshev tiles around CampState.position
DAY_TICKS = 2400
COMBAT_PROBE_RADIUS_TILES = 10.0  # check 3 probe (a): combatants counted within this Chebyshev radius of the victim; a fixed stated value
BIRTH_WINDOW_TICKS = 30  # check 3 probe (c): a birth in the victim's or killer's region within this many ticks before the death
CALAMITY_NOTE = "calamity sends no population nudge by design (src/world/calamity.py:57); not counted as a miss"


def region_id_at(state, position) -> Optional[str]:
    """The id of the region containing ``position``, or None (the births system's own rule for its nudge)."""
    region = SpatialQueryService.get_region_at(state, position)
    return region.id if region is not None else None


class _ReadCounter:
    """A transparent proxy over a body that counts reads of its social and strategic components (G5's second clause: a ``none`` gate must read no social state); the result is unchanged."""

    def __init__(self, body: Any, spy: "BirthSpy") -> None:
        object.__setattr__(self, "_body", body)
        object.__setattr__(self, "_spy", spy)

    def __getattr__(self, name: str) -> Any:
        if name in ("social", "strategic"):
            self._spy.none_gate_reads += 1
        return getattr(self._body, name)


class BirthSpy:
    """Record-only wrapper over the births system and the apply path; ``install()`` patches, ``restore()`` undoes."""

    def __init__(self) -> None:
        self.fails: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.births: List[Dict[str, Any]] = []
        self.conceptions: List[Dict[str, Any]] = []
        self.unplaced: List[Dict[str, Any]] = []  # BALANCE: newborns of a litter that found no free tile (tick, mother, slot)
        self.ended: List[Dict[str, Any]] = []  # PREGNANCY_ENDED events (tick, mother, litter size)
        self.risings: List[Dict[str, Any]] = []  # one row per rising (tick, risen id, corpse, original, goods read on the applied state)
        self.father_dead_at_term = 0  # BALANCE: births whose recorded father was dead at term
        self.none_gate_reads = 0  # G5: social/strategic reads made for a species whose gate is "none" (must be 0)
        self.arrivals: Dict[int, str | None] = {}
        self.risen_ok: Dict[int, bool] = {}  # W3: a RISEN arrival counts as declared only with its source corpse present in the prior state
        self.applied_hunger: Dict[int, Dict[int, bool]] = {}  # tick -> entity id -> a typed consume update was applied
        self.nudges: List[Dict[str, Any]] = []  # check 6a: per (tick, region) the births system's write against the newborns it added there
        self.regionless: List[Dict[str, Any]] = []  # check 6a BALANCE: births whose mother stood in no region (no nudge is written), with the newborn's tile
        self.border_crossings: List[Dict[str, Any]] = []  # check 6a BALANCE: a newborn placed outside its mother's region (tick, child, both regions, tile)
        self.applied_cohorts: List[Dict[str, Any]] = []  # check 6: the apply-side young-count change of every applied births nudge
        self._born_by: Dict[int, set] = defaultdict(set)  # tick -> mothers who bore on that tick (a PREGNANCY_ENDED for one of them is a G6 row)
        self._birthed_pregnancies: set = set()  # (mother, conceived_tick) already delivered (G4: one birth per pregnancy)
        self._risen_corpses: set = set()
        self._events = hashlib.sha256()  # the neutrality arms compare the typed world-event stream of two runs by this digest
        self._patched: List[tuple] = []

    def install(self) -> "BirthSpy":
        original_births = BirthService.__dict__["process_births"].__func__
        original_apply = ApplyPath.__dict__["apply_generation"].__func__
        original_gate = births_module.passes_mate_gate

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
            self._check_risings(prior_state, update, new_state)
            self._digest_events(prior_state.tick, update)
            self._record_pregnancy_ended(prior_state, update)
            return new_state

        def passes_mate_gate(mother, mate, profile):
            if profile.mate_gate == "none":
                return original_gate(_ReadCounter(mother, self), _ReadCounter(mate, self), profile)
            return original_gate(mother, mate, profile)

        for owner, name, original, replacement in (
            (BirthService, "process_births", original_births, process_births),
            (ApplyPath, "apply_generation", original_apply, apply_generation),
        ):
            setattr(owner, name, staticmethod(replacement))
            self._patched.append((owner, name, original))
        births_module.passes_mate_gate = passes_mate_gate
        self._patched.append((births_module, "passes_mate_gate", original_gate))
        return self

    def restore(self) -> None:
        for owner, name, original in reversed(self._patched):
            setattr(owner, name, original if owner is births_module else staticmethod(original))
        self._patched.clear()

    # ---- per check -------------------------------------------------------------------------------------------------------------------------------
    def _check_births(self, state, update) -> None:
        catalog = get_catalog()
        self._check_conceptions(state, update, catalog)
        self._check_births_at_term(state, update, catalog)
        self._record_nudges(state, update)

    def _check_conceptions(self, state, update, catalog) -> None:
        """Conception rows: W1 at conception, G3, G5, K8 and the litter table, from the typed pregnancy the births system returns and the state it read."""
        parents_seen: Dict[int, int] = defaultdict(int)
        for mother_id, upd in sorted(update.entity_updates.items()):
            pregnancy = upd.lifecycle.pregnancy_set if upd.lifecycle is not None else None
            if pregnancy is None:
                continue
            mother, mate = state.entities.get(mother_id), state.entities.get(pregnancy.father_entity_id)
            row = {"tick": state.tick, "mother": mother_id, "father": pregnancy.father_entity_id, "due": pregnancy.due_tick, "litter": pregnancy.litter_size}
            self.conceptions.append(row)
            if mother is None or mate is None:
                self.fails["W1"].append({**row, "why": "parent not in state"})
                continue
            for parent_id in (mother_id, mate.id):
                parents_seen[parent_id] += 1
            profile = _profile_of(catalog, mother)
            why = _w1_failures(state, mother, mate, profile)
            if why:
                self.fails["W1"].append({**row, "why": why})
            if species_of(mate) != species_of(mother):
                self.fails["K8"].append({**row, "at": "conception"})
            if profile is None:
                continue
            if mother.lifecycle.pregnancy is not None or mate.lifecycle.pregnancy is not None:
                self.fails["G3"].append({**row, "why": "pregnant mother" if mother.lifecycle.pregnancy is not None else "pregnant mate"})
            if pregnancy.conceived_tick != state.tick or pregnancy.due_tick != state.tick + profile.gestation_ticks:
                self.fails["G3"].append({**row, "why": "due != conceived + gestation_ticks", "conceived": pregnancy.conceived_tick})
            if pregnancy.litter_size not in profile.litter_weights:
                self.fails["G2"].append({**row, "why": "litter size not in the declared table"})
            if not _gate_holds(mother, mate, profile):
                self.fails["G5"].append({**row, "why": "bond gate: no accepted marriage and not both sentiments at the line"})
        for parent_id, n in parents_seen.items():
            if n > 1:
                self.fails["W1"].append({"tick": state.tick, "parent": parent_id, "why": "parent in more than one conception in one check"})

    def _check_births_at_term(self, state, update, catalog) -> None:
        """Birth rows: G1, G2 (born + unplaced == the litter drawn), G4, W1 at birth, W2 shape, K8, W4, per mother who was due."""
        born: Dict[int, List[Any]] = defaultdict(list)
        for child in update.entities_add:
            if child.lifecycle.parent_a_entity_id is not None:
                born[child.lifecycle.parent_a_entity_id].append(child)
        unplaced = Counter(int(e.subject) for e in update.world_events_add if e.category == WorldEventCategory.NEWBORN_UNPLACED)
        for mother_id, n in unplaced.items():
            self.unplaced.extend({"tick": state.tick, "mother": mother_id, "slot": i} for i in range(n))
        due = [m for m in state.entities.values() if m.lifecycle.pregnancy is not None and m.lifecycle.pregnancy.due_tick <= state.tick and m.combat.alive and m.lifecycle.active]
        for mother in sorted(due, key=lambda m: m.id):
            pregnancy = mother.lifecycle.pregnancy
            kids = born.pop(mother.id, [])
            row = {"tick": state.tick, "mother": mother.id, "father": pregnancy.father_entity_id, "due": pregnancy.due_tick, "litter": pregnancy.litter_size}
            self.births.extend(self._birth_row(state, child, mother, pregnancy) for child in kids)
            if kids:
                self._born_by[state.tick].add(mother.id)
            if pregnancy.due_tick != state.tick:
                self.fails["G1"].append({**row, "why": "born at a tick other than due_tick"})
            if len(kids) + unplaced.get(mother.id, 0) != pregnancy.litter_size:
                self.fails["G2"].append({**row, "born": len(kids), "unplaced": unplaced.get(mother.id, 0)})
            key = (mother.id, pregnancy.conceived_tick)
            if key in self._birthed_pregnancies:
                self.fails["G4"].append({**row, "why": "a second birth for one pregnancy"})
            self._birthed_pregnancies.add(key)
            mother_update = update.entity_updates.get(mother.id)
            if mother_update is None or mother_update.lifecycle is None or not mother_update.lifecycle.pregnancy_clear:
                self.fails["G4"].append({**row, "why": "the pregnancy was not cleared with the birth"})
            father = state.entities.get(pregnancy.father_entity_id)
            if father is not None and not father.combat.alive:
                self.father_dead_at_term += 1
                dead_update = update.entity_updates.get(father.id)
                if dead_update is not None and dead_update.social is not None:
                    self.fails["G1"].append({**row, "why": "a parent bond was written toward a dead father"})
            self._check_term_children(state, update, catalog, mother, kids, row)
        for mother_id, kids in born.items():
            for child in kids:
                self.births.append(self._birth_row(state, child))
                self.fails["G1"].append({"tick": state.tick, "mother": mother_id, "child": child.id, "why": "a birth with no due pregnancy"})

    def _birth_row(self, state, child, mother=None, pregnancy=None) -> Dict[str, Any]:
        """One newborn. `born_tick` is the tick it was added; `species` is the MOTHER's species (`species_of`), and `conceived_tick` / `due_tick` are her pregnancy's, all None when no due pregnancy accompanied the birth (a G1 row)."""
        return {"tick": state.tick, "child": child.id, "mother": child.lifecycle.parent_a_entity_id, "mate": child.lifecycle.parent_b_entity_id, "kind": child.kind,
                "region": region_id_at(state, child.navigation.position), "born_tick": state.tick,
                "species": species_of(mother) if mother is not None else None,
                "conceived_tick": pregnancy.conceived_tick if pregnancy is not None else None,
                "due_tick": pregnancy.due_tick if pregnancy is not None else None}

    def _check_term_children(self, state, update, catalog, mother, kids, row) -> None:
        profile = _profile_of(catalog, mother)
        pregnancy = mother.lifecycle.pregnancy
        for child in kids:
            if child.identity.occupation is not None or child.identity.life_stage != LifeStage.CHILD or child.lifecycle.birth_tick != state.tick or child.lifecycle.parent_b_entity_id is None:
                self.fails["W2"].append({**row, "child": child.id})
            if child.lifecycle.parent_b_entity_id != pregnancy.father_entity_id:
                self.fails["G1"].append({**row, "child": child.id, "why": "parent_b is not the recorded father"})
            if child.kind != species_of(mother):
                self.fails["K8"].append({**row, "child": child.id, "at": "birth"})
        hunger_update = update.entity_updates.get(mother.id)
        typed = hunger_update.biological.hunger_delta if hunger_update is not None and hunger_update.biological is not None else None
        if kids and profile is not None and typed != min(profile.birth_hunger_cost, 100.0 - mother.biological.hunger):
            self.fails["W4"].append({**row, "typed_hunger_delta": typed})
        if not kids and typed:
            self.fails["W4"].append({**row, "typed_hunger_delta": typed, "why": "a cost with no newborn born"})

    def _digest_events(self, tick, update) -> None:
        for event in update.world_events_add:
            self._events.update(repr((tick, getattr(event.category, "value", str(event.category)), event.subject, sorted((event.payload or {}).items()))).encode())

    @property
    def event_digest(self) -> str:
        return self._events.hexdigest()

    def _record_pregnancy_ended(self, prior_state, update) -> None:
        for event in update.world_events_add:
            if event.category != WorldEventCategory.PREGNANCY_ENDED:
                continue
            row = {"tick": prior_state.tick, "mother": int(event.subject), "litter": event.payload.get("litter_size"), "reason": event.payload.get("reason")}
            self.ended.append(row)
            if row["mother"] in self._born_by.get(prior_state.tick, ()) or prior_state.entities.get(row["mother"], None) is None or prior_state.entities[row["mother"]].lifecycle.pregnancy is None:
                self.fails["G6"].append({**row, "why": "PREGNANCY_ENDED for a mother who bore this tick or held no pregnancy"})

    def _check_risings(self, prior_state, update, new_state) -> None:
        """R1-R4 for every RISEN add, with the goods (R2) read on the APPLIED state, not on the update."""
        catalog = get_catalog()
        bodies = {b.id: b for b in update.entities_add}
        for eid, source in sorted(update.entity_spawn_sources.items()):
            if getattr(source.kind, "value", str(source.kind)) != "RISEN":
                continue
            body, cid, original = bodies[eid], source.source_corpse_id, source.original_entity_id
            corpse = prior_state.corpses.get(cid)
            row = {"tick": prior_state.tick, "risen": eid, "corpse": cid, "original": original}
            self.risings.append(row)
            self.risen_ok[eid] = corpse is not None
            if corpse is None or cid in self._risen_corpses or cid in new_state.corpses:
                self.fails["R1"].append({**row, "why": "corpse absent before, risen from twice, or still present after"})
            self._risen_corpses.add(cid)
            if corpse is not None:
                self._check_goods(prior_state, update, new_state, corpse, row)
            species = catalog.get_species(body.kind)
            profile = catalog.get_risen_profile(species.risen_profile) if species is not None and species.risen_profile else None
            dead = prior_state.entities.get(original)
            if profile is None or dead is None or species_of(dead) not in profile.source_species:
                self.fails["R3"].append({**row, "kind": body.kind})
            archetype = catalog.entity_archetypes.get(profile.risen_archetype) if profile is not None else None
            after = new_state.entities.get(original)
            if (eid == original or after is None or dead is None or after.combat.alive != dead.combat.alive or after.lifecycle.death_record != dead.lifecycle.death_record
                    or body.identity.occupation is not None or body.lifecycle.parent_a_entity_id is not None or body.lifecycle.parent_b_entity_id is not None
                    or (archetype is not None and body.identity.properties.get("faction_id") != archetype.faction)):
                self.fails["R4"].append(row)

    def _check_goods(self, prior_state, update, new_state, corpse, row) -> None:
        """R2 per corpse, on the applied outcome: gold == the purse, raw meat == the MEAT_DECAYED quantity (cause "risen"), every other (item, quantity) == the ground items it left."""
        meat = float(sum(st.quantity for st in corpse.items if st.item_id == RAW_MEAT))
        events = [e for e in update.world_events_add if e.category == WorldEventCategory.MEAT_DECAYED and e.subject == str(corpse.id)]
        sunk = sum(float(e.payload.get("quantity", 0.0)) for e in events)
        purse = new_state.ground_items.get(corpse.id)
        got_gold = purse.gold if purse is not None and purse.source_entity_id == corpse.original_entity_id and purse.dropped_tick == prior_state.tick + 1 else 0
        expected_items = Counter((st.item_id, st.quantity) for st in corpse.items if st.item_id != RAW_MEAT and st.quantity > 0)
        got_items = Counter(
            (g.item_id, g.quantity) for g in new_state.ground_items.values()
            if g.item_id and g.source_entity_id == corpse.original_entity_id and g.dropped_tick == prior_state.tick + 1 and tuple(g.position) == tuple(corpse.position)
        )
        wrong_cause = [e for e in events if e.payload.get("cause") != "risen"]
        if sunk != meat or got_gold != corpse.gold or got_items != expected_items or wrong_cause:
            self.fails["R2"].append({**row, "gold": [corpse.gold, got_gold], "meat": [meat, sunk], "items": [sorted(expected_items.items()), sorted(got_items.items())], "wrong_cause": len(wrong_cause)})

    def _record_nudges(self, state, update) -> None:
        """Check 6a: the births system's own write per region against the newborns it added, both read from the MOTHER's region (the state births reads); a newborn placed in another region is a border crossing (BALANCE)."""
        written = {rid: wu.population_young_births_delta for rid, wu in update.world_updates.items() if wu.population_young_births_delta}
        added: Counter = Counter()
        for child in update.entities_add:
            mother = state.entities.get(child.lifecycle.parent_a_entity_id)
            mother_region = region_id_at(state, mother.navigation.position) if mother is not None else None
            newborn_region = region_id_at(state, child.navigation.position)
            x, y = child.navigation.position
            if mother_region is None:
                self.regionless.append({"tick": state.tick, "child": child.id, "tile": [int(x), int(y)]})
                continue
            added[mother_region] += 1
            if newborn_region != mother_region:
                self.border_crossings.append({"tick": state.tick, "child": child.id, "mother_region": mother_region, "newborn_region": newborn_region, "tile": [int(x), int(y)]})
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


def _profile_of(catalog, mother):
    species = catalog.get_species(species_of(mother))
    return catalog.get_reproduction_profile(species.reproduction_profile) if species and species.reproduction_profile else None


def _gate_holds(mother, mate, profile) -> bool:
    """G5, re-derived: ``none`` always holds; ``bond`` needs an ACCEPTED marriage between the two (held by either) or both directed sentiments at the named friend line."""
    if profile.mate_gate == "none":
        return True
    pair = {mother.id, mate.id}
    for holder in (mother, mate):
        if any(m.status == MarriageStatus.ACCEPTED and {m.proposer_entity_id, m.target_entity_id} == pair for m in holder.strategic.marriages.values()):
            return True
    toward_mate, toward_mother = mother.social.bonds.get(mate.id), mate.social.bonds.get(mother.id)
    return toward_mate is not None and toward_mother is not None and toward_mate.sentiment >= FRIEND_LINE and toward_mother.sentiment >= FRIEND_LINE


def _w1_failures(state, mother, mate, profile) -> List[str]:
    """W1 at conception: both alive, active ADULTs past their intervals, the mother at or below the fed line, same species, in range."""
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
        self._g6_seen: set = set()
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
                is_risen = source == "RISEN" and self.spy.risen_ok.get(e.id, False)
                if not is_birth and not is_risen and source not in DECLARED_ARRIVAL_SOURCES:
                    self.fails["W3"].append({"tick": tick, "id": e.id, "kind": e.kind, "source": source})
                if is_birth:
                    self.newborn_hunger[e.id] = e.biological.hunger
                else:
                    self.newborn_hunger[e.id] = float("nan")
            if not e.combat.alive and e.lifecycle.pregnancy is not None and e.id not in self._g6_seen:
                self._g6_seen.add(e.id)
                self.fails["G6"].append({"tick": tick, "id": e.id, "why": "a dead body holds a PregnancyState"})
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
