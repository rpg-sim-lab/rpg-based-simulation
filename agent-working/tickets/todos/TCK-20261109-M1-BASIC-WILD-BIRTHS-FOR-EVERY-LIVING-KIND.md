---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: open
date: 2026-11-09
tags: []
---

# TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND

## Title
A well-fed creature with a mate of its kind nearby has young at a declared rate, for every living kind, and camps no longer spawn members from nothing (decisions 67, 70)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Roadmap §12.3 milestone 1, decisions 67 and 70. Packs, herds and territory stay in §12.4.

Child of TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC.

Filed by rpg-planner on 2026-11-09 as a filing only (no code), on lead-planner-u24's go relaying the owner (#715 6731822583). This follows roadmap §12.5: "Each item becomes a ticket under the milestone 1 epic before work starts."

## Scope
1. Each kind declares its birth rate and conditions in content.
2. Young must eat. Camps stop spawning members from nothing.
3. Report survival by kind group (the standing check).
- Rule work before code (§12.3, "How the path runs"): the catalog text and kernel spec come first. Owner-level choices go to the owner as questions with options and a recommendation when the milestone starts. The forward design's proposed recommendations are not rulings.
- Measured as its own step, once at fold against its parent (decision 76), on the cumulative watch that restarts at v1.1, with the §12.5 per-step stop rules. Those rules and the watch are not trimmed without an owner ruling (#715 6731822583). The measurement tier is stated at dispatch under the standing depth rule (#715 6731764470). It is never below the floor (#715 6731822583): the paired default tier plus every world where an affected known entry lives. A hash-equal check alone proves only an observability change. Decision 76 (§12.3) sets a behaviour step at 3 worlds x 5 seeds x 5000 ticks per arm, and going below it needs an owner ruling.

### Re-scope 2026-11-17 (rpg-planner-ubuntu)
This follows the owner dispatch (#715 6943793433) and rpg-designer-ubuntu's rulings. The rulings are stored word for word in `agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/rpg_designer_ubuntu_births_rulings_2026-11-17.md` (body sha256 52ad1ea5; that file is the source; the lines below only point at it):
- Part A (binds now): Q1 to Q10.
- Part B (held until rpg-designer's yes): no code covers B1 to B5.
- Part C: the own-job bars.

The domain is M1 run 5 (births). It lands as its own Phase 1 segment, and the PR names the domain. Main base: 3aafdb383 or later.
1. Content: an optional `reproduction_profile` in `species.yaml`, and a new `data/content/living/reproduction_profiles.yaml` (Q1). The loader refuses, with a typed error, a profile on a kind whose hunger is "none".
2. One births system, unflagged, run on the 30-tick cadence, with a seeded draw keyed by (world seed, tick, mother id) and mothers visited in id order (Q2, Q3, Q9).
3. The mother pays `birth_hunger_cost`. The newborn is CHILD, at its kind's normal starting hunger, with no free meal (Q4).
4. The newborn's kind is `species_of(parents)`. Its occupation is None. The parent ids and `birth_tick` are set through `birth_record`. Faction and role are the mother's, except that HERO gives CITIZEN. That exception is interim and is a row for the name-branch item (Q5, Q8).
5. Fold `reproduction_humanoid.py` and the camp natural-creature path into the one system, and remove their old code. Retire nest spread. The flag entries leave `feature_flags.py` and `docs/guides/feature_flags.md` in the same change (Q5).
6. The pair interval uses the existing `LifecycleComponent.reproduction_cooldowns` (state.py:187). An entity is eligible when its largest expiry is at or before the current tick. A new durable field goes to rpg-designer first (Q3).
7. The own-job run follows Part C. It runs at the decision-76 tier (3 gate worlds x 5 seeds x 5000 ticks per arm), with the fix arm spied plus a plain twin. The counts K6, K6b, K8 and W1 to W5 must each be 0. Zero births in total is a STOP to rpg-designer-ubuntu. The spy and runner shas are sent to rpg-designer-ubuntu after each pin commit. The heavy run needs lead-planner's go for each run.

### Amendment 2026-11-17 (rpg-designer's answers and the owner's B2)
Source: `agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/rpg_designer_births_answers_2026-11-17.md` (body sha256 8c2c9fab). The owner's B2 ruling is #715 6950737100. Where this amendment differs from the re-scope above, the amendment wins.
- Item 4: a newborn's role is MONSTER when the mother is MONSTER, and CITIZEN otherwise. Faction is the mother's. This is an interim row of the name-branch item.
- Item 6: expired `reproduction_cooldowns` entries are pruned at the check. The field's doc and comment state its new meaning. A FIELD_RULES row is needed only if the field's shape changes.
- Item 7: the own-job is the fix arm (spied) plus its plain twin, with no base arm in Phase 1. Bars W1, W3, W4 and W5 are sharpened per Part C of the source file.
- B1: the rule is ECOL-06, "A new body is born, not made". The text belongs to rpg-designer. It enters `docs/world_rules/life-body/ecology-population.md` only through rpg-designer, never from this lane (v2 Part B1).
- B2 (owner): only kinds that eat get births. Undead, spirit, slime and dragonkin are excluded. The backlog ticket TCK-20261117-SLIME-AND-DRAGONKIN-NEED-A-NON-FOOD-BIRTH-CONDITION covers slime and dragonkin (not M1).
- B3: no kind is exempt from the extinction line. The undead decline is disclosed as BALANCE text.
- B4: ECOL-03 keeps statistical cohorts. The +1 real-birth nudge is generalised to every birth. The ECOL-03 status line reads "partly met". rpg-designer reviews that evidence text in the PR.
- B5: Bible ch05 gets the births law, and the reproduction parity rows move. One divergence entry, class Unified. The texts go to rpg-designer before the implementation PR.
- Item 5: rpg-designer reviews the `docs/guides/feature_flags.md` change.

### Amendment 2026-11-17 (v2 BINDING)
Source: `agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/rpg_designer_ubuntu_births_rulings_v2_2026-11-17.md` (body sha256 f1b332ba). v2 supersedes v1 (52ad1ea5). It folds in 8c2c9fab and B2. Where any section of this ticket differs from v2, v2 wins.
- Q11, the newborn body: built through the SAME species/archetype path as a t0 body of its species, with any seeded draw keyed by the newborn's id.
  - There is no CHILD scaling, so the newborn gets t0 values at full HP. The step report discloses "newborns have adult body stats". A CHILD body scale is backlog: TCK-20261117-A-NEWBORN-HAS-AN-ADULT-BODY-UNTIL-A-CHILD-BODY-SCALE-EXISTS.
  - age_ticks is 0 at birth; the old `short_clock_age` is not carried.
  - gold is 0 (decision 51).
  - Both parent ids are the real parents and never None. birth_tick is the birth tick.
- Q12, pruning: `LifecycleUpdate.reproduction_cooldowns_remove` (the partner ids) is a field on the typed update, not durable state. It needs no FIELD_RULES row or fingerprint entry.
  - ApplyPath applies remove, then add, within one update.
  - merge() unions the remove lists.
  - Removing an absent key is a no-op.
  - Unit tests cover all three, plus a serialise round trip if patches are serialised anywhere.
- rpg-designer acked v2 via lead-planner-u24 and lead-planner (relayed 2026-11-17, recorded with #715 6951051264). Q11 and Q12 bind. Q11 is an M1 interim, under two conditions:
  - (a) The ECOL-06 Bible ch05 text and the Unified divergence entry both state: "a newborn's body is its species' t0 body at life stage CHILD; no child stat scaling in M1".
  - (b) Every system that gates on LifeStage keeps gating newborns. No path may treat CHILD as ADULT to make births work. A later growth or stat law is a ch01 change and goes to rpg-designer.
  - Q12: a field on a typed update record is not durable state, and the prune runs only through the apply path.

### Amendment 2026-11-17 (v2.1: D1-D4 on plan 5241baac6)
Source: the same stored v2 file, now v2.1 (body sha256 009bc090; an append-only change from f1b332ba).
- D1: the profile values in plan §1 are APPROVED as fixed. The step report discloses three things:
  - each pair breeds at most once per run;
  - expect well under 0.4 births per eligible mother;
  - births are bounded by about half the adults of each kind (BALANCE).
- D2: the regional scarcity suppression is dropped.
  - Process call (rpg-planner-ubuntu): every deleted or rewritten assertion goes to the owner in one batched ask, via lead-planner, before the first code push. That includes the tests that pin only the removed OFF paths. Each assertion is named in the PR body.
- D3: a new `newborn_archetype: <id>` in species.yaml, required on every species with a `reproduction_profile`.
  - The loader refuses, with a typed error, a missing value, an unknown id, and an archetype whose species differs.
  - The newborn takes the BODY only: stats, attributes, body model, and the personality draw keyed by its own id. It takes no role, occupation, equipment, inventory or job traits. Inventory and equipment are empty, gold is 0, and traits = the species' `natural_traits`.
  - The PR lists the chosen ids in a table for rpg-designer-ubuntu's review.
  - The pre-code STOP stays.
  - The Q11 (a) Bible wording becomes "the species' declared newborn body (newborn_archetype)". That wording is a question for rpg-designer. Code may proceed.
- D4: disclosed in the step report and the ch05 placeholder. Backlog: TCK-20261117-A-NEWBORN-NEVER-GROWS-UP-INSIDE-A-RUN-NEEDS-A-MATURATION-CLOCK.
- Births ship unflagged, so every moved golden hash, baseline and regression reference row is listed, each one an owner ask.

### Amendment 2026-11-18 (v2.2, and lead-planner's routing)
Source: the same stored v2 file, now v2.2 (body sha256 d12d3498; append-only from 009bc090). rpg-designer acked v2.1.
- The text below is fixed word for word. It goes in the ch05/ECOL-06 placeholder, the Unified divergence entry and the step report: "A newborn's body is its species' declared newborn body (newborn_archetype) at life stage CHILD; no child stat scaling in M1. It can differ from the t0 population-profile stats of its parents."
- The personality draw is keyed by (world seed, newborn id). If the existing draw is already seeded per run, the PR says so and cites the line.
- `newborn_archetype` is required ONLY with a `reproduction_profile`. Every other species loads exactly as today, and a test pins that. The species.yaml schema doc is updated in the same PR. u24's content lanes get an fyi before the merge.
- Rows that move go four ways (lead-planner, relaying lead-planner-u24):
  - (1) Grade/corpus pins fall under rule (a), #715 6941107808. Send the rows, their attribution, rpg-designer-ubuntu's predicted direction and any flags (more than 2x the bar, or an unpredicted direction) to lead-planner. lead-planner passes them to lead-planner-u24, which verifies and records them on #715 before the push.
  - (2) Golden hashes, fixtures, asserts and gate baselines are test-expectation changes. rpg-designer-ubuntu rules on them first. Then they go to the owner as ONE ask via lead-planner, listing old, new and cause.
  - (3) Census pins (+1 per new file) fall under S8.
  - (4) A code-health ceiling raise is its own owner ask and names a retiring ticket.
  - A push carrying re-pinned grade rows waits for both records (the S10 record and lead-planner-u24's).
- Overlap with u24 PERC-02a (lane D, likely to merge first): it adds the compile check `require_declared_population_species` (a usable sense profile plus a declared diet). Each `newborn_archetype`'s species must pass that check. After PERC-02a lands, births resyncs on main and runs the check. A text conflict is only possible near the troll block in species.yaml.
- When the PR opens, its number and head go to lead-planner, which passes them to lead-planner-u24 to re-diff species.yaml against the u24 branches before the merge ask.

### Amendment 2026-11-18 (G1a and G1b)
Source: `agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/rpg_designer_ubuntu_births_rulings_g1_2026-11-18.md` (body sha256 0c8ea97d). It adds to v2.2 and changes nothing in it.
- G1a: the newborn copies the mother's `population_id` and `spawn_region`, both existing `properties` keys, written as archetype_factory.py:68-75 writes them. A key is omitted when the mother's value is None.
  - Disclosure: on a newborn, `spawn_region` names its population's declared region. The birth event records where the birth happened.
  - Test: provenance_lookup leaves a newborn id past the t0 count unresolved.
- G1b: no camp-membership field. Camp "refill" is reported spatially as BALANCE, not as a bar.
  - The measure is fixed in the runner before any data: bodies with `species_of()` exactly equal to `CampState.kind`, within a declared radius constant, sampled per day per seed and split into newborn and t0.
  - A camp whose kind is not a declared species is reported as unmapped. A world with no camps reports "0 camps".
  - The ch05 wording ("one generation of presence") goes with the open Q11/D3 Bible question. Superseded by A2 below.

### Amendment 2026-11-18 (G1 addendum: A1, A2)
Source: `agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/rpg_designer_ubuntu_births_rulings_g1_addendum_2026-11-18.md` (body sha256 4560ab2a). Where it differs from G1, the addendum wins.
- A1 covers the campaign reader of `population_id` (orchestrator.py ~1080-1093 → `WorldCompiler.resolve_pending_information`, first match in roster order). G1a stands.
  - Delivering to a surviving newborn is correct. The resolver is unchanged, and no t0-only filter is added.
  - Disclosed in the step report and in the field's doc line.
  - One test file covers three cases: (1) provenance leaves a newborn unresolved; (2) a roster with only a newborn of P resolves to the newborn; (3) a roster with a t0 member and a newborn of P resolves as the code orders it, with the order asserted (ascending id expected).
  - A different order is reported to rpg-designer-ubuntu before the PR, without changing the resolver.
- A2: Q11/D3 is closed. The camp-refill ch05 text is a new Bible item and goes with the B5 texts to rpg-designer before the implementation PR.

### Amendment 2026-11-18 (G1 addendum 2: Q13, Q14)
Source: `agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/rpg_designer_ubuntu_births_rulings_g1_addendum2_2026-11-18.md` (body sha256 6456fcb0). Where it differs from G1 or addendum 1, addendum 2 wins.
- Q13 (a): the resolver is unchanged. It takes the first match in roster insertion order; there is no id rule.
  - Case 3 asserts insertion order, and both orders are tested.
  - One real-flow test: a roster built through the carry-forward path, holding a surviving t0 member and a newborn of P, resolves to the t0 member.
  - The disclosure uses addendum 2's exact sentence.
  - Added by rpg-designer-ubuntu on 2026-11-18 from lead-planner's check, sent by message and recorded here; no other change to addendum 2:
    - The real-flow test must not hand-build the roster or the final state. It produces the newborn through the real births apply path in an episode, takes that episode's `final_state.entities`, and builds the next roster through `_extract_entity_carry_forwards` and `persistent_entities.update`.
    - It asserts three things: (1) every t0 id comes before the newborn id in `final_state.entities` iteration order; (2) the same holds in the rebuilt roster; (3) the response resolves to the surviving t0 member.
    - If (1) fails because the state rebuild reorders entities, STOP and report to rpg-designer-ubuntu before the PR.
  - Q15 (a), the restore-path ruling: rpg-designer-ubuntu, 2026-11-18, by message on lead-planner-u24's checkpoint-order check, recorded here. It replaces rpg-designer-ubuntu's earlier pre-ruling where they differ. The resolver is unchanged.
    - Add a round-trip case to the Q13 test file: a roster holding a t0 member and a newborn of P goes through `CampaignState.to_dict` → `json.dumps` → `json.loads` → `from_dict`. Use the dumps call an existing writer uses, or the plain default if none is found, and also a `sort_keys=True` variant. For each variant, assert the order that comes back and who the resolver picks. Pin what the code does; don't fix it.
    - The disclosure's last two sentences become: "Every t0 body enters the roster before any newborn within a campaign run. A CampaignState round trip through to_dict/from_dict rebuilds the roster in serialized key order (ascending id from a plain dump; lexicographic if the JSON is key-sorted, which can put a newborn first); no run path restores one today."
    - The P3 backlog ticket gets a scope line: "one declared order that survives a CampaignState round trip". No new ticket.
    - Grep src/, tools/ and frontend/ for callers of `CampaignState.from_dict`. tests/ may call it. If a run path in src/ or tools/ calls it, STOP and report to rpg-designer-ubuntu before the PR.
  - Backlog: TCK-20261118-RESOLVE-PENDING-INFORMATION-PICKS-BY-DICT-INSERTION-ORDER (pre-bind for rpg-designer).
- Q14 (a), fallback: the species schema doc is made of three parts:
  - the `SpeciesDefinition` `Field(description=...)` for `newborn_archetype` and `reproduction_profile`;
  - the regenerated `content_usage_matrix.md` living/species row;
  - one line in the PR body saying so.
  - No new doc. ch01 changes only through B5.

## Out of Scope
- §12.4 (packs, herds, territory), milestones 2 and 3, and any rule work not listed in §12.3 (owner ruling only).
- Calamity (magical/demonic), boss, lair and creature-territory spawns. These are arrivals or flagged-off spawns, so no code there moves (Q5, Q6). Q6 adds a backlog line for the territory spawn, which creates creatures with no parents.
- Deriving cohort counts from individual births and deaths (roadmap M2). Part B4 is pending.

## Acceptance Criteria
- Births happen only under the declared conditions (W1). The newborn has the ruled shape (W2). Nothing is created from nothing (W3). The mother pays (W4). No newborn gets a free meal (W5). K6, K6b and K8 each count 0 on the Part C tier, which contains at least one real birth.
- No camp spawns a member from nothing.
- The extinction line is read per §12.5, as Part B3 rules.
- Tests for the new behaviour. The Bible 05, parity ledger and divergence entries land in the same change, using the texts from Part B5.
- The PR body states what ran locally, under S10 (#715 6944269046 and 6944824176). Grade re-pins follow rule (a) (6941107808).

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC

## Related Docs
- docs/plans/systemic_world/roadmap.md (§12.3 milestone 1, §12.5 done criteria)
- docs/plans/systemic_world/owner_decision_memo.md

## Related Stored Artifacts
None.

## Related Code Areas
spawning and camp systems, content

## Assumptions / Open Questions
- Order (roadmap §12.5, memo rows 89/93/95): the v1-disclosure repairs, then D80C, then the decision-73 step (#781, the v1.1 record), then the §12.3 items. Starting this item needs the owner's dispatch yes, brought by rpg-planner via lead-planner-u24.
- Owner-level choices are asked when the milestone starts, not guessed here.
- 2026-11-17: the read-only map's claim that creature territory is ungated was wrong. `world_dynamics.py:286-287` runs it only with `ENABLE_CREATURE_TERRITORY_LIFECYCLE` ON (default OFF, `feature_flags.py:149`). Each claim taken from the map is to be re-verified against the code before the plan cites it.
- Part B1 to B5 were answered on 2026-11-17 (see the amendment above).
- Newborn body stats and cooldown pruning: answered as Q11 and Q12 in v2 (see the v2 amendment above).

## Implementation Notes
- Carry-forward from kind=species step 4 (rpg-designer): this item's own-job counts include K6 (kind is a species at birth) and K8 (newborn kind = the parents' species), on a world/seed where births actually happen.
- Observation (BALANCE, Phase 3): 0 camp spawns and 0 respawns in 5000t in all 3 gate worlds at s42. Either the camps don't spawn in that horizon, or a spawn path is gated off (decision 70: camps refill only by births).

## Test Summary

## Files Changed

## Completion Summary
