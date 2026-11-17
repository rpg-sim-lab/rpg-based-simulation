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
- Open, held: Part B1 to B5 (catalog Rule ID, which kinds count as living, extinction line, ECOL-03, Bible/parity/divergence texts). They are with rpg-designer via lead-planner.

## Implementation Notes
- Carry-forward from kind=species step 4 (rpg-designer): this item's own-job counts include K6 (kind is a species at birth) and K8 (newborn kind = the parents' species), on a world/seed where births actually happen.
- Observation (BALANCE, Phase 3): 0 camp spawns and 0 respawns in 5000t in all 3 gate worlds at s42. Either the camps don't spawn in that horizon, or a spawn path is gated off (decision 70: camps refill only by births).

## Test Summary

## Files Changed

## Completion Summary
