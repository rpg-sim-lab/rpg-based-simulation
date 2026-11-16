---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD
phase: open
date: 2026-11-09
tags: []
---

# TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD

## Title
`kind` always means species, and occupation is a separate field

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Roadmap §12.3 milestone 1: "`kind` always means species, and occupation is a separate field."

Child of TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC.

Filed by rpg-planner on 2026-11-09 as a filing only (no code), on lead-planner-u24's go relaying the owner (#715 6731822583). This follows roadmap §12.5: "Each item becomes a ticket under the milestone 1 epic before work starts."

## Scope
1. Find every place `kind` carries an occupation or role meaning, and every reader of it.
2. Add occupation as its own typed field. Then move each reader to the field that matches its meaning.
- Rule work before code (§12.3, "How the path runs"): the catalog text and kernel spec come first. Owner-level choices go to the owner as questions with options and a recommendation when the milestone starts. The forward design's proposed recommendations are not rulings.
- Measured as its own step, once at fold against its parent (decision 76), on the cumulative watch that restarts at v1.1, with the §12.5 per-step stop rules. Those rules and the watch are not trimmed without an owner ruling (#715 6731822583). The measurement tier is stated at dispatch under the standing depth rule (#715 6731764470). It is never below the floor (#715 6731822583): the paired default tier plus every world where an affected known entry lives. A hash-equal check alone proves only an observability change. Decision 76 (§12.3) sets a behaviour step at 3 worlds x 5 seeds x 5000 ticks per arm, and going below it needs an owner ruling.

## Out of Scope
- §12.4 (packs, herds, territory), milestones 2 and 3, and any rule work not listed in §12.3 (owner ruling only).

## Acceptance Criteria
- No reader treats `kind` as an occupation (a test or probe shows this).
- Occupation is a typed, durable field, visible in the read model, with tests (CLAUDE.md durable state rule).
- Tests for the new behaviour, plus the parity ledger and Bible updates in the same change.

### Ruling, staged plan and own-job counts (rpg-designer, 2026-11-16, v1; owner dispatch #715 6920334481, M1 pace 6912138476)
Copied verbatim from `.claude/handover/drafts/rpg-designer-kind-is-species-ruling.md` (sha256 67cc6f6dd151afcb34ed68252182048ba714881085b4427b9e77860589fbd4fb); only the heading levels are lowered by one so the ticket's section order holds.


- Ticket: TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD.
- The owner dispatched it with rule work first (#715 6920334481). M1 pace (a): 6912138476.
- Rules it follows:
  - roadmap §12.2 (decision 50: "Role names stay as display labels only"; kinds are generic archetypes);
  - decision 42 (rules cover every living kind, sized by the kind);
  - decision 43 (a person is an authored species trait);
  - decision 63 / ID-02 (a hero is a person doing work).
- Facts read on main (the inventory, with my own checks):
  - **Two build paths disagree.**
    - The classic world compiler, which builds the 3 gate worlds (`tools/test_architecture/rpg_gate_run.py:57-61` → `WorldCompiler.compile`), sets `kind` = the population ROLE string (`src/worldbuilding/compiler.py:766`, `.kind(pop_spec.role.lower())`).
    - The archetype path sets `kind` = species (`src/entities/contract_builder.py:41`).
  - **Species already exists**, as `identity.properties["species_id"]` (`compiler.py:760-761`). Every population of the 3 gate worlds has one in compile_context.json: human, goblin, orc, spider, wolf, undead, small_plant_eater. All of them are declared in `data/content/living/species.yaml`.
  - **`identity.role`** (EntityRole int: HERO, SHOPKEEPER, MONSTER, CITIZEN, WORKER, GUARD) is a separate, coarse field with about 53 readers. It's written by the occupation-change and coming-of-age paths (`IdentityUpdate(role_set=…)`).
  - **Entity-kind readers in src**, by the meaning they use:
    - species or creature type: about 11;
    - occupation: 4 (`party_composition.py:52-66`, `world/calamity.py:99`, `observability/extraction/combat.py:82`, `event_shapers.py:337`);
    - faction: 0;
    - display or copy: about 17;
    - unclear: 3 (`reproduction_humanoid.py:57,89` mates and children by kind; `world/environment.py:86` "stronghold").
    - Lane C redoes this per reader in step 1. This list is only the starting point.
  - **Hashes:** `kind` and `properties` are in `EntityState.to_canonical_dict`, and `kind` is in the replay fingerprint.

### The ruling

#### Where each meaning lives
- **`EntityState.kind`: the species id.**
  - It must be an id in `data/content/living/species.yaml`.
  - It's set once at build from the population's declared species, and is never renamed in a run (D79 already forbids renaming).
  - Newborns inherit their parents' kind, which is now their species.
  - It's the source of truth for species. `properties["species_id"]` stays as a mirror, written from the same value at build, until its readers move. Once nothing reads it, it's removed in a later step.
- **New `IdentityComponent.occupation: Optional[str]`: the role label the content gave the body.**
  - Its value is the string `kind` holds today on the classic path: `pop_spec.role.lower()`, e.g. worker, guard, merchant, blacksmith, scout, hero, raider, leader, alpha, predator_hunter, sentinel, wild_creature.
  - On the archetype path it comes from `properties["role_id"]`, or `profession_id` if there's no role_id. On the generator and calamity spawners, it's the literal they pass today (e.g. "world_boss", "hero").
  - Newborns get None, since they have no job yet.
  - **Meaning:** a label, per decision 50. In this item it only takes over the occupation readers of `kind`. Removing decisions that branch on it is the name-branch retirement item, not this one.
  - It's appended last to IdentityComponent, omitted from the canonical dict while None, and has a FIELD_RULES fill of None. Checkpoints already carry a fingerprint (#942), so an old shape is refused, not shifted.
- **`identity.role` (EntityRole): unchanged in this item.**
  - It's a coarse enum with its own writers and about 53 readers. Folding it into `occupation` would rewrite all of them, and it isn't needed for "kind means species".
  - Its HERO value retires in the hero-as-work item; MONSTER and the rest retire in the name-branch stages.
- **Why a new string field, not a reuse of EntityRole:**
  - EntityRole can't hold the labels `kind` carries today (merchant, blacksmith, scout, raider, alpha…).
  - Mapping them into 6 enum values would lose information and change behaviour in this item.
  - This is my RPG-track ruling (6734312437), not an owner question. The owner's rule ("display labels only") already fixes what the field is for.

#### The staged plan
Each step is one commit, measured once at fold, against its parent.

- **Step 1: rule work, no code.**
  - The catalog and Bible text: Bible 01 entity anatomy (the identity fields: kind = species, occupation = label, role = coarse enum, being retired) and the world-rules ID-02 repository evidence.
  - Lane C's per-reader inventory of every entity-kind reader in src, classed species / occupation / faction / display / unclear. Every unclear row is ruled by me before step 3.
  - A table of every kind-keyed constant or table, e.g.:
    - `creature_territory.py:22-25` rates keyed goblin_warrior/orc_warrior;
    - `entity_kind_constants.py` SPAWN_CADENCE_EXCLUDED_KINDS (goblin_raider…);
    - BOSS_ENTITY_KINDS;
    - `quests/generator.py:83` target_kind;
    - `evolution.py:100-104` "goblin" substring;
    - world_boss/dragonkin/stronghold.
  - For each one, I rule whether it re-keys to a species, to occupation, or stays (with a reason), before step 4.
- **Step 2: THE OCCUPATION FIELD IS ADDED. This is the step ubuntu's births code waits on.**
  - Add `IdentityComponent.occupation`, written at build on every path (above).
  - Add one species helper, `species_of(entity) -> str`. In this step it returns `properties["species_id"]`, falling back to `kind` on the archetype path. Every new species reader uses it, births included.
  - Nothing reads `occupation` yet, except tests and the presenter, which shows both fields.
  - The proof is neutral by projection: fates and counters are identical to the parent, and only the state hash moves, by the added field.
  - **Births:** ubuntu's births code can start once step 2 is on main, reading species ONLY through `species_of`. Step 4 then changes what the helper reads, without touching births.
- **Step 3: the occupation readers move from `kind` to `occupation`** (the 4 known, plus any lane C finds).
  - Behaviour-neutral by construction: on every built entity, `occupation` equals the old `kind` string.
  - The proof is whole-doc IDENTICAL against step 2 on the gate worlds. No state changes, so the hash is equal too.
- **Step 4: `kind` becomes the species. This is the behaviour step.**
  - The classic compiler sets `.kind(species_id)`, and refuses a population with no declared species (typed error).
  - Every other spawner writes a species id plus its occupation, e.g. calamity's "world_boss" becomes kind = its declared species and occupation = "world_boss".
  - `species_of` reads `kind`.
  - The step-1 table's re-keyings are applied.
  - `reproduction_humanoid.py` now pairs and inherits by species, and stops pairing by occupation.
  - A non-living entity with a kind (e.g. "stronghold") is listed in a named allowlist in the ticket, each one with an owning ticket. It is never silently accepted.
  - Measured: own-job counts (below), plus the M1 cadence reading against M1-base.
- **Step 5: the mirror goes.** Readers of `properties["species_id"]` (`get_species_id_str`, KNOW-04 seed, needs, diet, camp) move to `species_of`, and the mirror stops being written. The proof is IDENTICAL fates and counters (projection).

#### Content changes
- None are needed for the gate worlds: every population declares a species, and all 7 species exist in species.yaml.
- Step 4's compile refusal makes "a population with no species" a content error everywhere. Lane C lists any world under data/worlds that would fail, and each one gets its species declared in content, never a code default.
- No role labels change. They move to `occupation`, unchanged.

#### Docs and parity, in each step that changes meaning
- Bible 01 (identity fields);
- docs/core/entities.md;
- the parity rows for entity identity (substrate.yaml);
- a divergence entry at step 4 (rationale class Unified: one meaning for `kind`), with the reproduction pairing change named in it;
- world_rules ID-02 repository evidence.

### Own-job counts (HARD; fixed before data, never rewritten)
Every run: the 3 gate worlds of paired.WORLDS, s42, 5000 ticks.

- **Step 2 (neutral by projection; 3 PLAIN runs vs its parent).**
  - **K1, fates and counters equal:** whole-doc equal except start_hash/final_hash: **0** differing fields.
  - **K2, occupation was copied faithfully:** at t0, entities whose `occupation` differs from their pre-step `kind` string: **0**. Read at build by a test over the 3 gate worlds, not by a spy.
  - **K3, nobody reads the new field yet:** static. Production readers of `occupation` other than the presenter: **0**.
- **Step 3 (IDENTICAL; 3 PLAIN runs vs step 2).**
  - **K4:** whole-doc equal, hashes included: **0** differences.
  - **K5, no occupation reader left on `kind`:** static. Every row lane C classed as occupation reads `occupation`: **0** left.
- **Step 4 (behaviour; fix arm spied plus a plain twin, 6 processes).** The spy prints inputs and I class them.
  - **K6, kind is a species:** at t0 and at every birth, entities whose kind is not a species id, minus the named allowlist: **0**.
  - **K7, the mirror agrees:** entities where kind ≠ `properties["species_id"]`, where that is set: **0**.
  - **K8, births follow species:** births whose parents differ in species, or whose child's kind ≠ the parents' species: **0**.
  - **K9, no lost labels:** entities whose `occupation` ≠ their step-3 value: **0**. kind moved; the label must not.
  - **K10 (reported):** quest kill credits by target_kind; creature_territory spawns by kind; party-composition role counts. Base vs fix, so the behaviour shift is visible.
  - **Not vacuous:** K6 and K7 cover every entity at t0, so they can't be vacuous. If K8 sees 0 births in the 3 worlds, it is reported, not a trip, and the unit and integration tests carry it, since births are ubuntu's later item.
  - **BALANCE (reported):** deaths by world × cause, flee/hold counts, SimQ, D76, per-seed extinction, all against M1-base. A pooled extinction line trip goes to the owner, as always.
- **Step 5 (IDENTICAL fates and counters; 3 PLAIN runs).**
  - **K11:** fates and counters equal: **0** differences.
  - **K12:** production readers of `properties["species_id"]`: **0**.
- **HARD evidence, every run:**
  - spied == plain hash;
  - exceptions and logging_errors empty, and every runner keeps child stderr or a logging count (the M1 rule);
  - spy and runner pinned at the shas I approve;
  - no crash or ENOMEM.

### Simpler option
Do it in one step: flip `kind` and move the readers in a single commit.
- Cost:
  - There's no neutral proof separating the plumbing from the behaviour change.
  - Ubuntu's births wait for the whole item instead of for step 2.
  - A reader that was missed shows up only as an unexplained behaviour delta.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC
- TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY (done; the terminology rename)

## Related Docs
- docs/plans/systemic_world/roadmap.md (§12.3 milestone 1, §12.5 done criteria)
- docs/plans/systemic_world/owner_decision_memo.md

## Related Stored Artifacts
None.

## Related Code Areas
src/core/ (entity identity), content schemas

## Assumptions / Open Questions
- Order (roadmap §12.5, memo rows 89/93/95): the v1-disclosure repairs, then D80C, then the decision-73 step (#781, the v1.1 record), then the §12.3 items. Starting this item needs the owner's dispatch yes, brought by rpg-planner via lead-planner-u24.
- Owner-level choices are asked when the milestone starts, not guessed here.

## Implementation Notes
None yet.

## Test Summary

## Files Changed

## Completion Summary
