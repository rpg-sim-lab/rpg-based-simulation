---
status: active
layer: world
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: open
date: 2026-11-18
tags: []
---

# Births PR: the first non-birth origin, undead risen from a corpse (rpg-designer-ubuntu, 2026-11-18, DRAFT)
- **Basis:**
  - owner direction (#715 6966949325): one basic non-birth origin for undead in the M1 births PR; simple foundation; balancing deferred;
  - rpg-designer's non-binding guardrails 1-6 (relayed by lead-planner).
- **Status:** a design position for rpg-planner-ubuntu's scoping. The Rule ID, catalog, ch05 and roadmap texts are PRE-BIND and go to rpg-designer as questions (§6).
- **Code facts at 02d327ba6:**
  - `CorpseState` (world_records.py:12) is a typed record: id, original_entity_id, position, items, decay_tick, gold.
  - Decay (world_dynamics.py:345-360 `_decay_corpses`) removes a body at `tick+1 >= decay_tick`. Its gold becomes a ground purse (EXCH-02), and its raw meat leaves through the typed MEAT_DECAYED sink (decision 44).
  - `SpawnKind` has INITIAL, BIRTH and AUTHORED_ARRIVAL (spawn_source.py:13).
  - The undead species exists (species.yaml:192; need profile `hunger: "none"`, so no births: B2).
  - No graveyard-type place kind exists in content or src, and no necromancy or summoning mechanism exists (supernatural-transformation.md, note under STR-02).
- **Catalog rule that governs:** STR-02 (accepted). Where undeath is modelled, a corpse becoming undead is a NEW subject, not the original revived, and the original's death stays a historical fact. It needs its own declared process.

## 1. One origin: a corpse rises (guardrails 1, 6)
- **Source:** an existing `CorpseState`, and nothing else.
- **Deferred to a backlog row on TCK-20261118-BIRTHS-BALANCING-PASS (or a sibling ticket):**
  - **graveyard place:** no place kind exists, and adding one is content scope;
  - **dark magic:** no caster mechanism exists.
  - Neither is needed for "one basic origin".
- **The check:**
  - every `check_interval_ticks` on the absolute tick, as births does;
  - every corpse not yet at its decay tick, whose `original_entity_id`'s species is in the declaring profile's `source_species`, gets one keyed draw, `get_float(Domain.SPAWN, tick, corpse.id, sub_id=RISE_DRAW_SUB_ID)`;
  - it rises when the draw is below `rise_chance_per_check`.
  - The draw is stateless, so chance 0 perturbs nothing (the same property as births' control arm).
- **Corpse order:** by corpse id. There is at most one rising per corpse by construction (§3).

## 2. Declared in content, never by kind name (guardrail 4)
- A new `risen_profile` field on a species, read like `reproduction_profile`. Only species that declare it get the origin. In M1 that is `undead`, the one content row.
- **Profile fields:**
  - `source_species` (the list of species whose corpses can rise as this species);
  - `check_interval_ticks`;
  - `rise_chance_per_check`;
  - `risen_archetype` (the body, like `newborn_archetype`, D3).
- **Each value states its source in content, as births' rates do.** The rates are provisional and BALANCE (guardrail 6).
- **Typed content refusals:**
  - a `source_species` that isn't a declared species;
  - a `risen_profile` on a species that also has a `reproduction_profile`;
  - a profile on a species whose need profile has hunger. Risen is for kinds that don't eat. This mirrors B2 and keeps the two origins disjoint per species in M1.

## 3. The risen body: a new subject (STR-02)
- **A new entity id** from `generator.get_next_id()`.
  - The original entity stays dead, and its `death_record` is unchanged.
  - Its memories, relationships, goods, faction, home and genetics do not pass to the risen body.
- **Fields:**
  - `kind` = the declaring species (`undead`);
  - `occupation` = None;
  - `life_stage` = ADULT, since a risen body is not a child;
  - no parent ids;
  - `birth_tick` = the rise tick (the arrival tick; the field name is unchanged);
  - faction: the risen archetype's declared faction, never the dead body's.
- **Position:** the corpse's position.
- **SpawnSource (guardrail 3):** a new kind `RISEN`, carrying `source_corpse_id` and `original_entity_id`. It is required, like `parent_ids` for BIRTH. Typed refusal if either is missing.
- **The corpse is consumed in the same typed update:** `corpses_remove=[corpse.id]`.
- **Its goods follow the existing decay path exactly:**
  - gold becomes a ground purse with the corpse's id and `source_entity_id`;
  - raw meat goes out through MEAT_DECAYED;
  - other items are handled the way decay handles them.
  - So rising adds no new conservation branch: it is "decays early, and a body arrives".
  - **If decay loses any non-meat item today, that is a pre-existing gap. It is disclosed, not fixed here. I haven't verified it; scoping checks it.**
- **Population nudge:** none. Undead have no cohort births delta, so the risen body is a named entity only, the way calamity sends no nudge. That is a BALANCE note, not a 6a row.

## 4. HARD rows, fixed before data (each is a count that must be 0, or a pass/fail)
- **R1 one corpse, one body, once:**
  - RISEN adds whose `source_corpse_id` was not a corpse in the prior state;
  - plus corpse ids appearing in more than one RISEN source in the run;
  - plus RISEN adds whose source corpse is still present after the apply. **= 0.**
- **R2 goods conserved:** for every rising, the corpse's gold equals the purse gold that appears, and its raw meat equals the MEAT_DECAYED quantity. The existing conservation audit passes. **Mismatches = 0.**
- **R3 the kind is declared:** RISEN adds whose kind does not declare a `risen_profile`, or whose dead body's species is not in that profile's `source_species`. **= 0.**
- **R4 the risen body is a new subject:**
  - RISEN adds with id == `original_entity_id`;
  - or an original whose `alive` or `death_record` changes after the rising;
  - or a risen body with an occupation, parent ids, or a faction different from the archetype's. **= 0.**
- **W3:** `RISEN` joins `DECLARED_ARRIVAL_SOURCES` only with its source corpse id present. Otherwise it is a W3 fail.
- **K6, K6b** apply to risen bodies unchanged. **K8 stays births-only** (it is about parent species), and R3/R4 cover risen bodies. That's my reading, and rpg-designer may rule otherwise (§6).
- **Determinism:** the twin hash, and the second-hash-seed test on the rise path.
- **Not vacuous:** 0 risings in the tier is a STOP to me, not a pass. Then a focused scenario (a world with an eligible corpse) is allowed, with its runner approved by sha. A rule that can't fire in the corpus is a finding in itself.

## 5. BALANCE (report only)
- Risings per world × seed × source species.
- Risen bodies alive at the end.
- Deaths caused by risen bodies.
- The undead count over time. This replaces "the undead decline" disclosure: undead now have an inflow.
- The extinction line keeps undead with no exemption, as B3.

## 6. Pre-bind: QUESTIONS for rpg-designer
- **Q-R1, the Rule ID and text:** a sibling Domain Rule beside ECOL-06 in ecology-population.md, e.g. "A risen body is made from a corpse, never from nothing", with evidence R1-R4. The ID and text are rpg-designer's.
- **Q-R2, the roadmap item 2 wording:** guardrail 5's "births, declared world creation or a declared non-birth origin". I agree; confirm it.
- **Q-R3, the STR-02 identity choices in §3:**
  - nothing of the dead passes on;
  - the faction comes from the archetype;
  - life_stage ADULT;
  - `birth_tick` holds the arrival tick.
- **Q-R4:** K8 stays births-only, with R3/R4 for risen bodies. Or does rpg-designer want K8 widened?
- **Q-R5:** the deferral of the graveyard place and dark magic to backlog rows. That needs the owner's OK on the wording, because the owner named them.

## 7. Revision 2 (2026-11-18): the owner's answer and the scoping facts
- **Q-R5 is answered by the OWNER**, directly in this session (AskUserQuestion): "Corpse only, defer rest". The graveyard place and dark magic become backlog rows on TCK-20261118-BIRTHS-BALANCING-PASS. lead-planner logs this on #715.
- **The goods (scoping fact 1: decay drops non-meat items with no record today, a pre-existing leak).** My position is (b), not (a), and rpg-designer rules it (Q-R6).
  - A rising sends gold to the purse (as decay does) and raw meat to MEAT_DECAYED (as decay does). Every other ItemStack becomes a ground item at the corpse position, carrying `source_entity_id`. The purse already is a `GroundItemState`, so this is the same record type.
  - **Why (b):** guardrail 2 says the goods are "never vanishing", and rpg-designer ruled with 6a that a conservation law sits inside the simple foundation. Building a new origin on a known leak would make R2 a bar that knowingly passes a loss.
  - **The decay leak itself** is pre-existing and stays unchanged here. It is disclosed, with a backlog row: "a decayed body loses its non-meat items".
  - **R2 is measured by the spy directly:** corpse gold = purse gold, raw meat = MEAT_DECAYED, and each other item and quantity = the new ground items. It doesn't rely on the conservation audit's coverage of corpses.
- **Eligibility uses decay's own rule:** a corpse can rise only if `tick + 1 < decay_tick`, and the rise check excludes this tick's decay set. So no corpse both decays and rises (no double purse).
- **Same-tick eating:** a corpse whose meat is taken in the same tick must not be counted twice. The plan states the phase order. R2 counts at apply, so any double count fails it.
- **The dead body's species** = `species_of(state.entities[corpse.original_entity_id])` (the dead entity stays in state).
- **Faction** = the risen archetype's (undead_sentinel: `undead_remnants`).
- **The build site** carries `entity_spawn_sources` (test_spawn_sites_declare_source).
- **ECOL-06 is not in the catalog on any branch.** Q-R1 becomes: write ECOL-06 and its risen sibling together.

## 8. Revision 3 (2026-11-18): rpg-designer's rulings. Where this section differs from §1-§7, it wins.
- **ECOL-07** (Q-R1) goes directly after ECOL-06 in life-body/ecology-population.md, with evidence R1-R4. Its text: "**ECOL-07: A risen body is made from a corpse, never from nothing: a declared kind may rise from a corpse the world holds, and each corpse raises at most one body, once.**" The catalog text rides B5 together with ECOL-06.
- **Roadmap item 2** (Q-R2): "creatures come only from births, declared world creation or a declared non-birth origin, for every kind".
- **Identity** (Q-R3): confirmed as §3, with two additions:
  - position = the corpse's tile, or free_spawn_position from it, and any count uses the corpse's region, computed by the spy itself (as for 6a);
  - birth_tick holds the arrival tick only if the field's doc line reads "birth or arrival tick", with SpawnSource RISEN telling them apart. There is no second field.
- **K8 stays births-only** (Q-R4). R3/R4 cover risen bodies, and K6/K6b apply to both.
- **Goods** (Q-R6): **(b) is FINAL** (rpg-designer, relayed by lead-planner as a correction). It supersedes the "(a) plus exact decay path" relay, which crossed with it. §7 stands.
  - Gold goes to the purse, and raw meat to MEAT_DECAYED.
  - Every other ItemStack becomes a ground item at the corpse tile, with its source entity and tick.
  - **R2 bars all three exactly, per corpse.**
  - The drop is ONE shared helper. The u24 decay ticket TCK-20261118-A-DECAYING-CORPSE-DESTROYS-EVERY-ITEM-EXCEPT-GOLD-AND-MEAT-WITH-NO-SINK (P1) reuses it, so decay and rising stay one law.
  - Until that ticket lands, the decay loss is disclosed with a reference to it.
- **Q-R5 (OWNER):** corpse only. The graveyard place and dark magic go on the balancing-pass backlog.
- **The shared helper's call rule (2026-11-18, raised by rpg-planner u24):** `corpse_remains()` (the shared drop of purse, raw meat sink and ground items) is called ONLY after decay's post-transfer filter (economy.py `_without_decay_of_looted_bodies`), on corpses that leave this tick by the applied outcome. It is never called at world_dynamics time.
  - **Reason:** decay is computed before the transfers, and a body looted or re-added by a meal must not also drop its goods. Otherwise goods are duplicated.
  - **In M1 births:** rising already calls it from the end of phase 28 (placement B). No world_dynamics call to the helper exists. A guard test and a re-added-body test pin this.
  - **For the u24 decay ticket:** reusing the helper means either a post-transfer drop (matching rising) or an undo path for the ground items like the MEAT_DECAYED undo. That is that ticket's design, bound by this call rule.
- **The cadence (plan at impl 36ecbb3bf §11, accepted):** the rise cadence is `cadence.rises` (default 30) in src/engine/cadence.py, mirroring `cadence.births`. The profile has NO `check_interval_ticks`, which supersedes §1 and §2. The profile fields are `source_species`, `rise_chance_per_check` and `risen_archetype`.
