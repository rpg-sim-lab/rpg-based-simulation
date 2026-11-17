---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, roadmap]
last_verified: "2026-11-17"
---

# Milestone 1 kernel spec: items 2-6

Items: bands and appraisal, honest perception, places, activity period and hazard tolerance, name-branch retirement.

Written by rpg-designer on 2026-11-17, before the items' code (roadmap §12.3, "How the path runs").
- **Source draft:** `.claude/handover/drafts/rpg-designer-m1-items-2-6-rule-text.md` (sha256 800027b5).
- **Owner answers:** the owner answered the draft's question batch in one sitting, taking the recommended option on every question (#715 6937049127; memo row 98).
- **Where the rule text lives:** the world-rules catalog holds the catalog text:
  - PERC-02;
  - KNOW-05 and the KNOW-04 amendment;
  - SURV-08 and the SURV-06 home-range amendment;
  - BODY-08;
  - the CONFLICT-03 appraisal amendment.
- **What this file holds:** the kernel spec, plus each item's own-job counts, fixed before data.
- **Order and measurement:** ordered by the domain boundaries of #715 6936842047, and measured in Phase 3 (#715 6936893143). Every PR passes CI and the hard checks, the fix's own job included.

**Binding for every item:**
- Species are read via `species_of()` and labels via `occupation_of()`, never via `kind`.
- Every new durable field is typed and appended last. It is None-omitted where it can be None, and has a FIELD_RULES fill and a fingerprint entry (#942).
- Content values are generic coarse bands (decision 50).

# RUN 2: how subjects see and find things

## Item 3. Honest perception: each kind perceives by its own senses, and signals follow the body

### Catalog text (new PERC-02, under PERC-01 in knowledge-agency/perception.md)
> **PERC-02: A subject perceives another body or a place only through a sense its kind has, against a signal that body or place gives off; a decision may act on another body or place only if the subject perceives it now, remembers it, or was told of it.**
> - **Senses** are declared per kind (species `sense_profile`).
> - **Signals** follow the body: its size, whether it moves, whether it lives. A thing no sense of the subject can reach is not perceived, however close it is.
> - **The gate is a rule, not a convenience:** a decision that reads another body's or place's true state without this gate, memory or a report breaks this rule.
> - **What a subject can read:** what it can see or sense, such as position, size, visible wounds, what the other is visibly doing, and whether it is coming closer. It can never read the other's intentions (its task or target).

- **Disposition:** ACCEPT (RULED), implementing PERC-01's "bounded by declared constraints" for M1.
- **Repository evidence today:** CONFLICTING.
  - The senses are declared but never wired in compiled worlds: `sense_profile_id` is set only by ArchetypeEntityFactory.
  - No body emits a signal other than the defaults.
  - About 13 decision paths read other bodies without the gate.
  - appraisal `_coming_for` reads the other's `task.payload["target_id"]`.

### Kernel spec
1. **Senses wired.**
   - At build, on every path, the body's sense profile is its species' `sense_profile` (read via `species_of`).
   - It's a typed field, `PerceptionComponent.sense_profile_id`, or the existing properties key promoted to typed. The implementer picks which, and says so.
   - No body falls back to `baseline_humanoid` silently: a species with no profile is a content error (typed).
2. **Signals from the body (content plus one rule).**
   - `body_models.yaml` gains coarse `signals`: visibility, noise, scent, vibration, life. The bands are the gate's levels.
   - Generic defaults derived from the body:
     - visibility: by size (small → low, medium → medium, large → high);
     - noise and vibration: medium while moving, low while still, very_low while asleep or lodged;
     - scent: medium for living bodies;
     - life: medium for living, none for undead or spirit bodies.
   - The movement and sleep modifiers are applied in one function, `emitted_signals(entity)`, which replaces `get_entity_signals`' property reads.
3. **One perceived-neighbours query.**
   - `perceived_neighbours(subject, state)` = the radius pre-filter (the existing 10-tile constant stays as the outer bound; it's engineering) → the sense gate → the saliency top-k.
   - EVERY decision read of another body uses it:
     - perceived_hostiles, perceived_threats, CombatEngage and CombatRetreat scorers, filter_saliency;
     - entity_target_objective's hold;
     - intelligence.py's radius scans;
     - work_wake, worker_logic, actions.py:283, domain/cognition.py:58;
     - adventure and occupation-change whole-world scans, which become perceived or remembered (Item 4).
   - The run-ledger sampler uses it too, so "perception samples" measures the gate.
4. **A gate error is not perception.**
   - Today a gate failure counts as perceived (appraisal.py:54). It becomes NOT perceived, with an ERROR log record.
   - Run-time logging_errors = 0 is the HARD evidence check, so any gate error shows up.
5. **Observable intent only.**
   - `_coming_for` (appraisal.py:112) drops the task-payload read. "Coming for me" = it closed the distance on its last step, or it hit me within the hit window.
6. **Night** (owner Q2(a), #715 6937049127):
   - At night, by the fixed night helper (Item 5), vision counts two levels lower unless the sense profile declares `night_vision: true`. Other senses are unchanged.
7. **Out of scope:** stealth and concealment (scope boundary), and weather's perception multiplier (unread today; it stays unread).

### Own-job counts (HARD; fixed before data; 3 gate worlds × s42, spied plus twin)
- **P1:** decision-path reads of another entity that bypass `perceived_neighbours`: 0. Static: a test lists the allowed query and forbids `get_neighbor_view` and true-position scans in the decision dirs.
- **P2:** bodies whose sense profile ≠ their species' declared profile: 0, at t0 and at spawn.
- **P3:** perceptions granted where the gate's score is below the threshold: 0. This is the spy, re-scoring each granted pair.
- **P4:** a "coming for me" verdict that read another body's task: 0. Static, plus the spy.
- **Reported:** perceived pairs by sense channel; hostile sightings; flee episodes. These are BALANCE, Phase 3.

## Item 4. Places are found from perception, memory and what the subject was told (decision 56)

### Catalog text (new KNOW-05 in knowledge-information.md; SURV-06's "within reach" reads it)
> **KNOW-05: A subject finds a place (food, a bed, a shop, work, a safe refuge) only from what it perceives now, what it remembers having perceived, what it was told, or what its kind knows in common.**
> - **Memory** keeps where the place was and what was visible of it when last seen. It is revised by seeing the place again or by arriving.
> - **What a place's interior holds** (a shop's purse, a node's remaining yield, an employer's pay) is known only on arrival, or by a report. What shows at the door (an inn, a shop that is open) is known when the place is perceived.
> - **Vague leads stay vague:** a vague report names an area, never exact coordinates.
> - **Starting knowledge:** a subject starts knowing only what is declared for it (owner Q3(a), #715 6937049127).

- **Disposition:** ACCEPT (RULED), applying decision 56, KNOW-02 ("ground truth is never injected") and the Uncertainty Rule.
- **Evidence today:** CONFLICTING.
  - Every place-finding site reads the true map: nearest_building and nearest_resource_node over the whole world, forage over all nodes, scavenge over all corpses, and nearest_sale / nearest_work reading true purses and pay.
  - SpatialMemory.known_resource_sites has no writer or reader.
  - A VAGUE lead carries exact x,y.
  - The starvation record's "judged" column equals the true map by construction.

### Kernel spec
1. **Places are perceivable.**
   - Buildings, resource nodes and carcasses are perceived by the same gate. They're static, with visibility by size: a building is high, a node medium, a carcass low visibility and medium scent.
   - They're perceived within the radius, on the subject's perception cadence.
2. **Typed place memory.**
   - `KnownPlace(place_id, place_kind, position, last_seen_tick, seen_state)`, where seen_state is observable only: "has food visible", "open", "depleted when arrived".
   - Stored in `SpatialMemory.known_places`, bounded per place_kind to the K most recent (K = 8; engineering).
   - Written on perception and on arrival; replaced on re-sight.
   - This item's own writer is always on. It doesn't depend on the ENABLE_MEMORY_UPDATE flag, and the flag's other memory stays as is.
3. **Readers move.**
   - Every place-finding site in the notes uses `known_place_of(subject, place_kind, need)`: the nearest known place by remembered position, within range (the leash or home range, and bed_reach), whose seen_state isn't excluded.
   - The true-map helpers stay only for building the world and for arrival.
   - Re-reads of a CHOSEN target's true state (intelligence.py :1290, :1415, :1500) move to arrival:
     - on arrival, the true state is read and the memory updated;
     - a depleted or refused place is remembered with the tick;
     - it's retried only after a recheck window (engineering, e.g. 200 ticks).
4. **What is told.**
   - A report writes a lead with its certainty. A VAGUE lead carries a region id; APPROXIMATE carries an area (center plus radius band); only PRECISE carries x,y.
   - GuildAction.visit stops deriving coordinates from the true map. It gives region-level VAGUE leads for the veins the guild has a record of. Until records exist, that means the veins in the guild's own region.
5. **Starting knowledge** (owner Q3(a), #715 6937049127):
   - A person starts knowing every building of the settlement it is placed in, as remembered places seen at t0.
   - A creature with a home range starts knowing the food places inside it.
   - Nothing else.
6. **Service at the door** (owner Q4(a), #715 6937049127):
   - Whether an inn serves, a shop buys, or work is offered is known when the building is perceived (a "sign at the door") or remembered.
   - The purse and pay are read only on arrival; a refusal is remembered.
7. **The starvation record:** column a (judged) = the ways from known places plus current perception; column b (true) unchanged. H6 then judges column a, as memo row 56 says. The test pinning a == b is replaced by one pinning a ⊆ known.
8. **Town center:** `state.town_center` and town tiles are read only by subjects for whom that town is a known place, under starting knowledge (a).

### Own-job counts (HARD)
- **F1:** decision-path place lookups that read the true map, i.e. calls of the true-map helpers outside world build and arrival: 0. Static allowlist test.
- **F2:** a chosen place the subject neither perceived, remembered nor was told of: 0. Spy: every chosen target place is in known_places or the current perception at choice time.
- **F3:** a VAGUE or APPROXIMATE lead carrying exact coordinates: 0.
- **F4:** known_places over its bound: 0.
- **Reported:** starvation-record a vs b per death (memo row 56: unknown ways are reported, never a failure); meals by way; refusals remembered.

## Item 5. Activity period per kind, hazard tolerance per body (A' folds in)

### Prerequisite: the night check
- TCK-20261115-THE-NIGHT-CHECK-READS-RAW-WORLD-TIME… is fixed first, as one helper, `time_of_day(state)` = `world_time % TICKS_PER_DAY`. Every night reader uses it.
  - Ruled 2026-11-17 (rpg-designer R1): the signature is `time_of_day(world_time: int)` (not `(state)`); `is_night(world_time: int)` is provided beside it in `src/core/calendar.py`.
- It changes behaviour (today every tick after 1800 is "night"), so the owner approved it (Q1(a), #715 6937049127).
- raid.py's own TICKS_PER_DAY (retired raids) is deleted with the dead code.

### Catalog text
> **SURV-08: Each kind declares when it is active (by day, by night, or at any hour). A subject prefers to rest outside its active period; this is a pull on its choice, never a schedule that overrides a pressing need or a present threat.** (new, life-body/survival-needs.md)
>
> **BODY-08: Each body declares, per hazard kind, whether it endures it (no harm), resists it (reduced harm) or has no protection. A body's tolerance is its own, never its faction's or role's.** (amends BODY-07 / ENV-02's "immunity" check, life-body/body-condition.md)

- **Disposition:** both ACCEPT (RULED), implementing §12.2 "activity period" and "hazard tolerance".
- **Evidence:** MISSING (activity); CONFLICTING (tolerance is per faction: factions.yaml hazard_immunities).

### Kernel spec
1. **Activity period.**
   - `species.activity_period ∈ {diurnal, nocturnal, cathemeral}`, required, and validated.
   - Values per species: owner Q5(a), #715 6937049127 (memo row 98).
   - Readers:
     - SleepScorer's +30 "at night" becomes +30 "outside the kind's active period", where cathemeral = never;
     - routine sleep urgency +0.3 becomes the same.
   - No other reader in M1.
   - The dead raw-time paths (intelligence.py:912, :1005-1016; routine boosts keyed on "sleep" / "eating" that never match a GoalKind) are deleted, not wired.
2. **Hazard tolerance.**
   - `body_models.hazard_tolerance: {<hazard_kind>: endures | resists | none}`, where an absent key = none.
   - The drain (environment.py) multiplies by 0 (endures), 0.5 (resists) or 1 (none).
   - `FactionDefinition.hazard_immunities` is retired, with its readers (environment.py:31, faction.py:153).
   - Body values: owner Q6(a), #715 6937049127 (memo row 98).
3. **A'** (TCK-20261030-SLEEP-WINS-OVER-STARVING-HUNGER-WHEN-NO-BED) keeps its own ruling (held_for HUNGER_WAKE, five points). It lands in this run because it reads the same sleep pull.
   - Its own counts stay as written in that ticket.
4. **Out of scope:** hazard-aware pathing (frozen, memo row 7, ENV-08).

### Own-job counts (HARD)
- **T1:** night readers not using `time_of_day`: 0 (static).
- **T2:** with the night fix, the share of ticks counted as night is 50% ± 0 over each whole day (the spy, per tick, on the 3 worlds). Ruled 2026-11-17 (rpg-designer R2): a unit test over a full 2400-tick day replaces the spy; it is arithmetic on world_time.
- **T3:** the outside-period sleep bonus applied inside a kind's active period: 0.
- **T4:** hazard damage that differs from the body's declared multiplier: 0.
- **T5:** readers of faction hazard immunities: 0 (static).
- **Reported:** HAZARD deaths per world × kind; sleep episodes by time of day. These are BALANCE.

## Item 6, stage R1 (run 2). The camp tether becomes a home range (decision 57)

### Catalog text (amends SURV-06's tether sentence)
> **A kind that keeps a home keeps to a home range its kind declares (small, medium or large). A subject strays from it for a need or a chase and drifts back when nothing pulls it away; there is no fixed leash, and a role never sets the range.**

- **Disposition:** ACCEPT (RULED), applying memo row 57.
- **Evidence:** CONFLICTING. The leash is hardcoded per spawn function (10, or 8 for goblins). LEASH_RETURN snaps home every tick and hovers at the edge (22 → 1,665, SURV-06 :1001).

### Kernel spec
1. **Content.** `species.home_range ∈ {none, small, medium, large}`.
   - Generic: people none; pack and camp kinds medium; grazers large; spiders small.
   - The band → tiles table is one engine constant: small 6, medium 12, large 24. That's engineering and can be retuned.
2. **Where home is.** `navigation.home_position` = the camp or den position at build or spawn. Compiled creatures placed with a camp get it too; today only generator spawns do.
3. **The pull replaces the snap.**
   - `leash_return_update`'s every-tick tactical move is retired.
   - A strategic `RETURN_TO_RANGE` goal has low utility, scaled by the distance beyond range. It wins only when nothing else pulls. That keeps Strategy/Tactics separation: the return is direction, not a tactical override.
   - Pursuit gives up past 1.5× range (`should_give_up_chase`, re-keyed to the band).
4. **Range readers** (way_in_range, ways, sleep, opening steps, camp_food) read the home range, plus known places (Item 4).

### Own-job counts (HARD)
- **R1a:** leash radii set by spawn path or role: 0 (static).
- **R1b:** a RETURN_TO_RANGE choice while a need or threat outranks it: 0 (the spy).
- **R1c:** a subject beyond 1.5× range while chasing, for more than one strategic cadence: 0.
- **Reported:** LEASH_RETURN or RETURN_TO_RANGE episodes; time outside range; creature deaths.

---

# RUN 3: who fights whom

## Item 2. Coarse property bands and the one appraisal

### Catalog text (amends CONFLICT-03's appraisal amendment and KNOW-04; conflict-combat.md, knowledge-information.md)
> **The appraisal: a subject judges another body by what it perceives of it.**
> - **Can I eat it:** my diet against its edible body.
> - **Can it eat me:** the same, the other way round.
> - **Can I overcome it:** my power and condition against its apparent power and condition, counting the others visibly with it.
>
> The estimate is only as good as the subject's wits. A low-wits subject goes by the other's apparent size and its kind's common belief; a higher-wits subject that has watched or fought the other reads its true power band. The common belief is a weak prior: a decisive encounter with a member of a kind moves the subject's belief about that kind. The same appraisal serves hunting, wariness, flight and engagement.

- **Disposition:** ACCEPT (RULED), applying memo rows 46-50, KNOW-04's "experience outweighs it", and KNOW-02's objection to apparent_power reading true stats.
- **Evidence:** PARTLY.
  - can_overcome compares 3 bands against 4 belief levels, and a tie means no.
  - It reads none of the other's power, condition or allies, and no wits.
  - CombatPosture and AGENCY-07 read true atk, def and max_hp.
  - The wolf-vs-wounded-person strict xfail waits on this item.

### Kernel spec
1. **One scale.**
   - Power and believed danger map onto one integer scale: small/low 0, medium 1, large/high 2, extreme 3.
   - The 4 KNOW-04 levels map one-to-one, and an undeclared belief = medium (1), as today.
2. **Bands added to content (§12.2):**
   - a true `danger` band per species (separate from the folk belief), defaulting to the power band;
   - `speed` band;
   - `temperament` (timid / steady / aggressive);
   - `group_habit` (solitary / group / pack);
   - plus Item 5's two fields and R1's home_range.
   - Generic values, with the validator extended. Only the readers named here read them in M1.
3. **Perceived power** of another body, `perceived_power(observer, other)`:
   - **base:** the other's true power band if observer wits ≥ medium AND (the observer has perceived the other for ≥ 1 strategic cadence, or has fought it); else the observer's belief about the other's kind;
   - **condition:** −1 if the other visibly has under half its hp;
   - **company:** +1 if 2 or more bodies that the observer appraises as on the other's side stand within 4 tiles of it.
4. **can_overcome** = own effective power (own band, −1 if own hp is under half) > perceived_power.
   - A tie is no: the wolf (1) against a person it believes medium (1), wounded (−1 → 0), gives yes, so the xfail is removed as fixed.
   - Owner Q10(a), #715 6937049127: a tie means cannot overcome.
5. **Experience.**
   - A typed per-kind fact, `KindExperience(species, outcome, tick)`, is recorded on a decisive encounter: a kill, or a loss of more than half one's hp to it.
   - Each one moves the subject's belief about that kind by one level, toward what happened, clamped to the scale.
   - Provenance is "experience", which outweighs "common knowledge" (KNOW-04).
   - It's bounded: one fact per species, the latest.
   - That is the mechanism TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER found missing, so that ticket closes into this item.
6. **Engagement reads the appraisal.**
   - CombatPosture's opponent estimate and AGENCY-07 OUTMATCHED use `perceived_power` (scaled to the observer's own numbers by the band difference), never the target's true atk, def or max_hp.
   - The visible hp fraction and armed-or-not stay, since they're observable.
   - TCK-20260915 (3× mismatch) is re-read after this, and closes if the first-contact verdict now refuses.
7. **Name branches this replaces** (run 3, with why-it-fights): hostility.py's same-faction no-predation, and the faction-first ordering for monsters.
   - Faction keeps deciding for PEOPLE (memo row 47: "faction for people").

### Own-job counts (HARD)
- **B1:** appraisals that read another body's true atk, def, max_hp or power band when the observer's wits or exposure doesn't permit it: 0. The spy checks the inputs.
- **B2:** can_overcome verdicts that differ from the spec recomputed from the logged inputs: 0.
- **B3:** belief shifts not caused by a decisive encounter, or beyond one level per encounter: 0.
- **B4:** the strict xfail test passes, and is removed with this ticket.
- **Reported:** hunts, flights, wary avoidance and engagements by kind pair; deaths by cause. BALANCE.

## Item 6, stage R2 (run 3). Faction and monster names retire

### Catalog text (extends CONFLICT-03's row-62 interim)
> **Hostility between kinds comes from each kind's declared reason to fight (why-it-fights) and from the appraisal; between people, from declared faction relations keyed by id. No decision guesses an allegiance from the spelling of a name.**

### Kernel spec
1. **The legacy substring bucket goes.** `get_legacy_faction_bucket` (faction.py:114-132) and its uses retire. A faction id missing from the catalog is a typed content error at build.
2. **The MONSTER family** (probe allowlist rows) moves to declared data:
   - faction.py:144/:173;
   - region_threat_classifier :158/:162 (by alignment_bucket);
   - regional_sovereignty :88;
   - creature_territory :45 ("anchored" = has a home range and a home position, not the MONSTER role);
   - the adventure MONSTER defaults (an entity with no identity is a defect, not a monster);
   - `SPAWN_KIND_CATALOG_FACTION` (moves to content: a spawn label → faction id table).
3. **Region-owner assignment** (world_dynamics :155/:159, influence.py:63) writes faction ids from content, not `Faction.HERO_GUILD` / `MONSTER_HORDE` literals.
4. **The kill reward** (combat_rewards.py): owner Q8(a), #715 6937049127.
- **Counts:** the probe's allowlist rows for these families are 0. The ratchet test enforces it.

---

# RUN 4: identity

## Item 6, stage R3 (run 4). Hero and occupation names retire (with hero-as-work, decision 63, and kind=species step 4)

### Kernel spec (the catalog text is ID-02's existing decision-63 amendment, which already states the rule)
1. **The three-category inventory** (the closed de-hero epic's method, which has no stored inventory yet) is done as step 1 of this stage, over the probe's HERO and CITIZEN, WORKER, GUARD, SHOPKEEPER rows. The categories are: privilege to remove / capability to re-ground on real state / harmless naming.
2. **My category rulings for the rows already known:**
   - **Movement priority** (legality.py:525, occupancy_snapshot.py:33; HERO 100, MONSTER 50): category 1, removed. Equal priority with the deterministic id tie-break (owner Q9(a), #715 6937049127).
   - **Hero-only AP and skills on level-up** (evolution.py:109): category 2, re-grounded. Every subject that levels gains AP. Skills are learned from its occupation's taught crafts (LEARN-03).
   - **Hero-only tax and the conquered debuff** (sovereignty :48, :82): category 1, removed. Tax is EXCH-02's share on income, for everyone.
   - **Stronghold aura for HERO_GUILD** (environment.py:83): dead branch (no stronghold writer since D71), removed.
   - **Calamity on a hero death** (calamity.py:99): category 2, re-grounded to "a subject of standing dies" (reputation ≥ a band). Until standing exists, it's removed.
   - **Adventure capability matching for heroes only** (scoring :229, :456): category 2. Re-grounded to the occupation "adventurer" plus skills (decision 63).
   - **The routine role boosts** (routine.py:130-147): only WORKER/HARVESTING can match a goal, and it re-keys to occupation "worker". The rest are dead and deleted.
   - **Birth combat lean when both parents are heroes** (builder.py:692): category 1, removed.
   - **`_PERSON_ROLES`** (biological_needs.py:38): category 2. Re-grounded to `is_person` (keeps_coin, decision 43).
   - **Occupation change and coming of age** (occupation_change_scorer, coming_of_age, lifecycle :215, intelligence :1454): these write and read `occupation`, not EntityRole. Destination occupations come from content.
3. **The `tactical_role` strings** (VANGUARD, PROTECTOR…) are a chosen combat stance, not a being's name: outside the probe's scope, with an allowlist row giving the reason. If any is DERIVED from EntityRole, that derivation is a row here.
4. **EntityRole's end state:** once the rows are 0, EntityRole stays only as build-time classification, read by no decision path, or it's deleted if nothing reads it. The inventory answers which.
- **Counts:** the probe allowlist rows for these families are 0 (ratchet), plus the hero-as-work ticket's own counts.

---
