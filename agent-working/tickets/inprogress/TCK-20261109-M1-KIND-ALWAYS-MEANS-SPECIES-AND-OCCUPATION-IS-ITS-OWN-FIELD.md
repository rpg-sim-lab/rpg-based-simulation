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

#### (copied verbatim from the designer's step-1 rulings, sha256 665b97185fab88b8d5c00553669f150f1e88f81c413bad48e0af87bee0ca4c40; placed here next to the base counts)
### Amendment to the counts, v1.1, before any step-4 data
- **K6b, kind never changes in a run:** entities whose `kind` at any tick differs from their `kind` at birth or t0: **0**.
  - The base ruling relies on D79, but lane C found the `kind_set` plumbing live, and an observability comment (event_shapers.py:1065) says EvolutionSystem writes it.
  - At step 4, a `kind_set` that changes a species is refused in the apply path (typed), and K6b counts it.
  - This is added before any step-4 data, so it is not a rewrite.
- **K10 rows added (reported):**
  - goblin gear assignments by tier (row 8);
  - quest kill credits by target_kind (row 9);
  - humanoid pairings by species and occupation, base vs fix (row 24).

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

- 2026-11-16 (rpg-planner relay of rpg-designer): the designer's step-1 rulings on the inventory, FINAL. Copied verbatim from `.claude/handover/drafts/rpg-designer-kind-is-species-step1-rulings.md` (sha256 665b97185fab88b8d5c00553669f150f1e88f81c413bad48e0af87bee0ca4c40); heading levels lowered by two.


- Ticket: TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD.
- Base ruling: drafts/rpg-designer-kind-is-species-ruling.md, 67cc6f6d.
- Evidence ruled on: lane C commit 00d68bd57, stored_artifacts/.../evidence/step1_kind_inventory.md (tables A, A2, B, C).

#### The one principle these rulings apply
**Step 3 moves every LABEL compare to `occupation`, with the same string. Step 4 changes only what is truly SPECIES.**

- Step 2 makes `occupation` equal today's `kind` string on every entity.
- So any reader that compares `kind` against a label moves to `occupation` with the same literal in step 3, and stays behaviour-neutral. Labels include:
  - jobs;
  - compounds like goblin_raider and goblin_warrior;
  - boss labels like world_boss and ancient_sentinel;
  - structures like stronghold.
- Only readers that mean species stay on `kind`, through `species_of()`. They change behaviour at step 4, when `kind` becomes the species.
- No label string is renamed in this item. Cleaning labels up is the name-branch retirement item's job.

#### Table A: readers
| Row | Ruling | Step |
|---|---|---|
| 1-7, 14 (display, export, hash, fingerprint, plumbing, events) | stay on `kind`. They show or serialise both fields where a payload has room (presenter rows 1, export row 2). Events keep `kind` and add `occupation` only where the shaper already emits identity | 2 (presenter), else none |
| 8 evolution.py:100-104 | the "goblin" substring means species → `species_of(e) == "goblin"`. The tier-digit branches ("1"/"2" in kind) are UNREACHABLE: no writer in A2 produces a digit. They are removed, and the default tier kept. This is a behaviour change, since on the gate worlds `kind` is never "goblin" today, so goblins start getting goblin gear at step 4. It is reported under K10 | 4 |
| 9 quest kill credit | species; stays on `kind`. "wolf" quests start crediting wolf kills at step 4. Reported under K10 | 4 |
| 10-13 (party roles, hero compares) | occupation, same strings | 3 |
| 15 event_shapers.py:1189 goblin_raider | label compare → `occupation == "goblin_raider"`, same string | 3 |
| 16, 17 (BOSS_ENTITY_KINDS, SPAWN_CADENCE_EXCLUDED_KINDS) | label sets → read `occupation`, same members. None stays a member | 3 |
| 18, 19, 21 (world_boss) | label → `occupation == "world_boss"` | 3 |
| 20 boss.py:217 dragonkin | the lair-occupant LABEL → `occupation == "dragonkin"`. Its spawner (boss.py:259) writes occupation "dragonkin" and, at step 4, kind "dragonkin", which is a species id | 3 (read), 4 (kind) |
| 22 environment.py:86 stronghold | label → `occupation == "stronghold"` at step 3. At step 4 its `kind` goes on the named non-living allowlist (below) | 3, 4 |
| 23 creature_territory.py:52, 63 | the rate lookup is keyed by the label → `occupation` (B1), same keys. The respawn at :63 passes BOTH the parent's species and occupation | 3 (lookup), 4 (respawn species) |
| 24 reproduction_humanoid.py:57, 89 | species: pairs by `species_of`; the newborn's kind = the parents' species; its occupation = None | 4 |
| 25 generator.py:67 / B4 | keyed by the spawn LABEL → stays a label table, read with the spawner's occupation argument | 3 |

#### Table A2: writers, all at step 4 unless marked
- **Every writer writes two values:** `kind` = a species id from species.yaml, and `occupation` = the label it writes today. No code default species is allowed: no `or "human"`, no `or "entity"`, no `"monster"` default.
- **Where the species comes from**, in this order:
  1. the population or profile's declared species_id;
  2. the archetype of the same id in entities/entity_archetypes.yaml, if it declares a species_id;
  3. a declared content mapping, label → species, added in content, never in code.
- **If none exists, it's a typed refusal at build or spawn,** except for the named allowlist below. Lane C lists every label that falls through, with which spawner and which worlds or tests reach it.
- **compiler.py:766:** kind = properties species_id (all gate populations have one); occupation = `pop_spec.role.lower()`.
- **entity_spawner.py:130 (finding 2):** the `"human"` default goes. A profile with no species_id is a typed refusal. Lane C lists every content profile that would fail, and each gets its species declared in content.
- **generator.py:139 "hero":** occupation "hero"; species from step (2) or (3), never chosen by code.
- **generator.py:165/204/238/284:** the functions take `species` and `occupation` as separate arguments, and each caller passes both.
- **generator.py:321 "goblin":** kind "goblin", occupation None. There's no label today, so none is invented.
- **orchestrator.py:820, survivor rebuild:** carries kind and occupation as saved. The `or "entity"` fallback becomes a typed error, since a survivor with no kind is a defect.
- **campaigns/runner.py:69:** occupation = role; species via (1)-(3).
- **camp.py:** already species (wolf, spider, troll, slime). Occupation None. No change beyond passing both.

#### Table B: constants
| Row | Ruling |
|---|---|
| B1 TERRITORY_MATURITY_RATES | keyed by occupation, same keys; the default is unchanged (step 3) |
| B2 SPAWN_CADENCE_EXCLUDED_KINDS, B3 BOSS_ENTITY_KINDS | membership by occupation, same members. Rename the constants to `…_OCCUPATIONS` (a name only, step 3) |
| B4 SPAWN_KIND_CATALOG_FACTION | keyed by the spawn label (occupation), same keys. bandit, bear, harpy and golem have no species: they fall through to the A2 rule at step 4 (refusal unless content declares one) |
| B5 goblin_raider branch | as row 15 |
| B6 quests/generator.py:83 "wolf" | species; unchanged. The comment becomes true on every path at step 4 |
| B7 certification/scenarios.py:297 "GOBLIN" | change it to "goblin" at step 4. It never matched, which is a latent defect. If any certification expectation relied on it never matching, lane C reports that to rpg-planner first, since it's a test-expectation change |
| B8 evolution | as row 8 |
| B9 PartyRole by kind | occupation, same strings (step 3) |
| B10 boss and dragonkin compares | as rows 18-21 |
| B11 stronghold | as row 22 |
| B12 hero compares | occupation (step 3). Retiring them is the hero-as-work item |
| B13 | not an entity kind; no change |

#### Table C: findings
1. **YES, in step 2.** Survivor reconstruction (orchestrator.py:544, 820) and the archetype copies (archetype_factory.py:142, 168) carry `occupation`.
   - Add a step-2 test: a survivor rebuilt from a run, and a copied entity, keep `occupation` equal to the source's (ID-02's survivor-equivalence rule).
2. As A2, entity_spawner.py:130: the default goes at step 4, and the content gets declared.
3. As row 8: the digit branches are unreachable and are removed, with a static proof in the step-4 report (no A2 writer produces a digit).
4. As B7.
5. **dragonkin is a species and also the lair label**: it's written as both. world_boss and ancient_sentinel are labels only, so their species comes via A2 (2)/(3), else the allowlist with a ticket. stronghold, bandit, bear, harpy and golem: as A2 / B4.

#### The non-living allowlist (step 4)
- A named list in the ticket of kind values allowed that are NOT species ids, each with its owning ticket and a reason.
- Expected candidates: stronghold (a structure as an entity), plus any boss label that content can't give a species to yet.
- K6 counts against this list only. An entry with no owning ticket is a K6 failure.

#### Amendment to the counts, v1.1, before any step-4 data
- **K6b, kind never changes in a run:** entities whose `kind` at any tick differs from their `kind` at birth or t0: **0**.
  - The base ruling relies on D79, but lane C found the `kind_set` plumbing live, and an observability comment (event_shapers.py:1065) says EvolutionSystem writes it.
  - At step 4, a `kind_set` that changes a species is refused in the apply path (typed), and K6b counts it.
  - This is added before any step-4 data, so it is not a rewrite.
- **K10 rows added (reported):**
  - goblin gear assignments by tier (row 8);
  - quest kill credits by target_kind (row 9);
  - humanoid pairings by species and occupation, base vs fix (row 24).

- 2026-11-16 (rpg-planner relay of rpg-designer): the designer's step-2 review, FINAL; it amends the base ruling and the step-1 rulings on one point before any data. Copied verbatim from `.claude/handover/drafts/rpg-designer-kind-is-species-step2-review.md` (sha256 39dcca3d5bf88e2f76a747d0e9a3f6c9d685ccbe667a804b3799a212983e0232); heading levels lowered.


- Reviewed: lane C step 2 at fdfa1bb5b, the src diff /mnt/data2/rpg-measure/m1step2/step2_src.diff (sha 91a38249), plus generator.py read at fdfa1bb5b :195-210 and :276-300.
- Base rulings: 67cc6f6d (the plan), 665b9718 (step 1).
- This note amends both on one point, before any step-2 or step-3 data.

##### The change needed: step 2 copies `kind` into `occupation` on EVERY writer
- Step 3's claim is "neutral by construction, because occupation == today's kind". That holds only if every writer of `kind` writes the same string into `occupation`.
- fdfa1bb5b breaks it on four writers:
  1. **generator.py:204** (camp or natural offspring) writes `kind=kind` and no occupation, so None.
  2. **generator.py:284** (humanoid newborn) writes `kind=kind`, the parent's role string on the classic path, and no occupation, so None.
     - After step 3, a newborn "worker" stops counting as SUPPORT in party_composition, because occupation is None.
     - So step 3 would change behaviour on every birth.
  3. **archetype_factory.py:106** writes `occupation = role_id or profession_id`, while `kind` there is the species.
     - After step 3, `occupation == "hero"` would match archetype-path heroes that `kind == "hero"` never matched. That's a behaviour change inside a "neutral" step.
  4. **entity_spawner.py:144** writes `occupation = profile.role_id`, while `kind` = the species. Same problem as 3.
- **Ruling (amends 67cc6f6d's "on the archetype path it comes from role_id" and 665b9718's A2 occupation values):**
  - In step 2, every writer sets `occupation` = the exact string it writes to `kind`, including :204 and :284 and the archetype and spawner paths.
  - The TRUE labels move to step 4, which is the measured behaviour step:
    - role_id or profession_id on the archetype and spawner paths;
    - None for newborns;
    - None for generator.py:321 "goblin" and for camp offspring.
  - Step 4's disclosure names them.
- The rest of the diff is as ruled and APPROVED:
  - `IdentityComponent.occupation` appended last and None-omitted;
  - the EntityState view copy;
  - the apply.py:704 hand-copy fix (a good catch);
  - FIELD_RULES None;
  - campaign carry-forward (serialise when set, from_dict);
  - the orchestrator rebuild;
  - runner.py occupation=role (already equal to its kind);
  - the generator :139 / :165 / :238 / :321 copies;
  - the compiler;
  - the presenter;
  - `species_of`.

##### K2 tightened (before any data)
- K2 as written ("at t0 over paired.WORLDS") can't see births or spawns.
- **K2 v1.1:** for every writer of `kind` in src (table A2 plus :204 and :284), a unit test builds one entity through that path and asserts `occupation == kind`: **0** failures.
- The t0 test over paired.WORLDS stays alongside it.

##### Answers on the runner (16dc9031, 1bccef76)
- **K1 includes `dists` and `final`. YES:** compare everything except the top-level start_hash and final_hash, as compare_projection.py already does.
  - `final` rows carry kind, which step 2 doesn't change.
  - `dists` must be equal, since it's one venv.
  - A difference in either is a K1 failure, not noise.
- Both scripts read in full: runner 16dc9031 and comparer 1bccef76 are fine as drafted.
  - The gate's word list should match lib/busy_gate.sh v2 f35f1f91, i.e. add `keep_events_child`.
  - Send the final shas after the pin commit that carries the change above. I approve those shas, not these.

- 2026-11-16 (rpg-planner judgment, relayed): mechanism-registry changed-code advisory on step 2 (7 findings: attributes_biology/apply.py, personality, buildings and city/state.py, campaigns/orchestrator.py, world_compilation/compiler.py, camp/state.py and generator.py): no `registries/mechanisms.yaml` edit. Each is one-field identity plumbing (a carry, copy or write of `occupation`) that does not change what any mechanism does.

- 2026-11-16 (rpg-planner relay of rpg-designer's ruling (a), on lane C's finding that the step-1 scan skipped src/certification, src/perf and src/testing): the 25 scenario-fixture `V2EntityBuilder(...).kind(...)` chains (certification/scenarios.py 18, perf/scenarios.py 6, testing/scenario_runner.py 1) each also set `occupation` to the same expression as `kind`. K2 v1.1 is one per-file test iterating that file's chains (tests/unit/core/test_occupation_fixture_writers.py). STOP condition: a certification, arena or perf test that pins a state hash or canonical dict the field moves is reported before it is changed; a certification expectation change needs the owner's OK. None moved in the step-2 run (certification 86 passed, arena 4 passed under the not-slow filter, perf 501 passed, scenario API 20 passed). **Recorded for step 4 (not blocking steps 2-3):** before step 4, re-run the step-1 scan over src/certification, src/perf and src/testing (readers AND writers) and bring the rows to the designer, because their kind literals ("HERO", "MONSTER", "actor", "GOBLIN") are not species ids.

## Test Summary

## Files Changed

## Completion Summary
