---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: done
date: 2026-11-09
tags: []
---

# TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND

## Title
A well-fed creature with a mate of its kind nearby has young at a declared rate, for every living kind, and camps no longer spawn members from nothing (decisions 67, 70)

## Status
DONE

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

## Out of Scope
- §12.4 (packs, herds, territory), milestones 2 and 3, and any rule work not listed in §12.3 (owner ruling only).

## Acceptance Criteria
- Births happen only under the declared conditions, and the young eat.
- No camp spawns a member from nothing.
- The extinction line is read per §12.5.
- Tests for the new behaviour, plus the parity ledger and Bible updates in the same change.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC

## Related Docs
- docs/plans/systemic_world/roadmap.md (§12.3 milestone 1, §12.5 done criteria)
- docs/plans/systemic_world/owner_decision_memo.md

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/` (plan, investigation, test_plan, newborn_archetype_table, placement_packet)

## Related Code Areas
spawning and camp systems, content

## Assumptions / Open Questions
- Order (roadmap §12.5, memo rows 89/93/95): the v1-disclosure repairs, then D80C, then the decision-73 step (#781, the v1.1 record), then the §12.3 items. Starting this item needs the owner's dispatch yes, brought by rpg-planner via lead-planner-u24.
- Owner-level choices are asked when the milestone starts, not guessed here.

## Implementation Notes
- Carry-forward from kind=species step 4 (rpg-designer): this item's own-job counts include K6 (kind is a species at birth) and K8 (newborn kind = the parents' species), on a world/seed where births actually happen.
- Observation (BALANCE, Phase 3): 0 camp spawns and 0 respawns in 5000t in all 3 gate worlds at s42. Either the camps don't spawn in that horizon, or a spawn path is gated off (decision 70: camps refill only by births).

## Test Summary
- EXECUTED (gap on head 207788fce, after the merge of main ac759e0ba, host gated per chunk, summary /mnt/data2/rpg-measure/births2/summary_s10.txt, all rc 0): targeted 200 passed (access_audit pin, pregnancy state, death-ends-projects, births, gestation, mate gate, risen, newborn build, reproduction profiles, the reader row, 3 newborn integration tests); unit systems 18, progression 153, world 687, core 434, strategic 1102, entities 53, content 357, worldbuilding 436, domains 1148, engine 1438, tools 1455; integration world 24, content and worldassembly 220, scenarios and optimization 10; architecture 262; tests/tools chunks 0-7 (774, 782, 777, 647, 695, 1367, 724, 720). Static: code-health x3 rc 0, packages validate rc 0, import contracts rc 0, mypy baseline filter no output. `make docs-registry`: no diff.
- EXECUTED (own-job run, S9 #715 amendments GO 7234406943 (commands 0-1, head 2d52926ac, kit SUMS ffbf5a25) and GO 7238105313 (commands 2-3 after moving the head tree's data/runs out)): T0 canonical diff PASS in 3 gate worlds s42 (the only difference is the added `entities/<id>/properties/archetype_id`: 52 / 21 / 35 stamps, 0 other); births evidence on frontier_living_world s42 5000 t: 7 births (all spider, litter 7, 1 conception), every newborn role from the ARCHETYPE source, 0 other_no_archetype, masked REF hash equal (PASS), twin hashes equal, risings 0; coin/boss real and controls: verdict PASS. The designer's read: births bars PASS (corrected read v2 65d179f7, with H8/H9).
- PIN updates (changed existing expectations, rpg-planner rulings, each from the check's own output): completeness scope_files 393 to 398, unbound_files 272 to 276; genetics_aptitude row dropped from the state-caller pin; FIELD_RULES set; lifecycle access-audit declaration kept at ('entities', 'tick').
- NOT MEASURED: R1-R4 (undead risings) were NOT EXERCISED, so they are NOT MEASURED, and no rerun is asked: on the measured cell 34 of 62 bodies died (29 of them source-species corpses: human 20, goblin 9) and `risings_total` is 0, which content expects: `undead_rising` has `rise_chance_per_check` 0.002 per 30-tick check and a corpse decays 100 ticks after death, so each corpse gets 3-4 checks, about 0.2 expected risings on the cell, P(0) about 0.8 (corrected read v2, 65d179f7). They need a forced rise; follow-up `TCK-20261128-MEASURE-UNDEAD-RISINGS-ON-A-CELL-THAT-HAS-A-RISING-SOURCE` (a forced-rise integration test is preferred). Check 3 (combat cost of newborns) is NOT MEASURED as a cost finding: the kit's DeathWatch had a defect, and the recount from the final states (corrected read v2, 65d179f7) is: COMBAT deaths head 23 vs control 19; per 1000 live entity-ticks 0.140 vs 0.128 (ratio 1.10); 0 newborn victims; killer kinds NOT MEASURED. The kit (12 tools, 5 tests) is on `evidence/births-kit @ 2d52926ac` and is not in this PR.
- Rewritten tests: the two newborn-in-a-group integration tests read the kernel state through `tests/integration/world/group_window_reader.py` (C1 kept, C2 folded into C1, C3 tick-independent; designer-checked at 207788fce).

## Files Changed
- Source: src/content (archetype `newborn_role`, profile lookups, archetype-less breeder refusal), src/core (intent_result, spawn_errors, pregnancy, state), src/engine (rise_trigger, risen and corpse_goods moved from src/world, pipeline, resources phase, access_audit declaration), src/entities (archetype_factory newborn role), src/systems (lifecycle `_death_lifecycle`), src/world (births), src/worldbuilding (compiler stamps archetype_id), src/worldassembly, src/ai, src/domains.
- Data: data/content (entity archetypes with `newborn_role`, reproduction/risen profiles, species, world modules), data/worlds (resolved reports of the shipped worlds).
- Registries and docs: registries/mechanisms.yaml, docs/mechanics (01, 04, 05, 07, content usage matrix), docs/parity_ledger (social_narrative, world_dynamics), docs/guidelines/intentional_divergences.md (2.225), docs/engine (authoritative_pipeline, known_limitations), docs/brainstorm generated views.
- Tests: tests/unit (23 files), tests/integration (6 files), tests/architecture (1), tests/simulation_quality (1).
- Ticket and artifacts: `agent-working/tickets/done/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND.md`, `agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/`.
- (not in this PR) the own-job kit: `evidence/births-kit @ 2d52926ac`.

## Completion Summary
Every living kind with a mate of its kind now has young at its declared rate: `BirthService` births from the reproduction profiles (gestation, litter, mate gate), a newborn's role comes from its mother's archetype (`newborn_role`, declared in content, refused at load for a breeding archetype without it) and the classic world compiler stamps `archetype_id` so the gate worlds read the same declaration; camps spawn nothing from nothing (divergence 2.225 and the earlier camp removal). The risen path moved to src/engine with an injected generator so the registry layer order holds.

Acceptance: births under declared conditions and the young eat: met on the measured cell (7 spider births, ARCHETYPE role source, masked REF equal, T0 diff PASS, twin hashes equal); no camp spawns a member from nothing: met (no camp spawn path); extinction line read per 12.5 in the evidence block; tests plus ledger and Bible updated in the same change.

Limits (disclosed): R1-R4 (undead risings) were NOT EXERCISED, so they are NOT MEASURED, and no rerun is asked: on the measured cell 34 of 62 bodies died (29 of them source-species corpses: human 20, goblin 9) and `risings_total` is 0, which content expects: `undead_rising` has `rise_chance_per_check` 0.002 per 30-tick check and a corpse decays 100 ticks after death, so each corpse gets 3-4 checks, about 0.2 expected risings on the cell, P(0) about 0.8 (corrected read v2, 65d179f7). They need a forced rise; follow-up `TCK-20261128-MEASURE-UNDEAD-RISINGS-ON-A-CELL-THAT-HAS-A-RISING-SOURCE` (a forced-rise integration test is preferred). Check 3 (combat cost of newborns) is NOT MEASURED as a cost finding: the kit's DeathWatch had a defect, and the recount from the final states (corrected read v2, 65d179f7) is: COMBAT deaths head 23 vs control 19; per 1000 live entity-ticks 0.140 vs 0.128 (ratio 1.10); 0 newborn victims; killer kinds NOT MEASURED. Only one cell (frontier_living_world s42, 5000 t) had births in the own-job run, and it shows spiders only; humans do not conceive within the compressed windows (mate gate, divergence 2.225); the group-reader tests read progress from state, not applied updates (stated in the reader).
Hand-orchestrated close (rpg-implementer-3, at the planner's request). Written at close: the Test Summary, Files Changed and this Completion Summary of this ticket; the five stored artifacts (plan, investigation, test_plan, newborn_archetype_table, placement_packet) were written before and during the work and were only moved here, not rewritten.
