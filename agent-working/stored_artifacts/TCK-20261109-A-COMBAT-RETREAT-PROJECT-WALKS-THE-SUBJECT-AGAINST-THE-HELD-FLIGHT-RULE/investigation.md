---
status: historical
layer: strategy
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE
phase: done
date: 2026-11-12
tags: []
---

# Investigation: does a stored target step while the subject is engaged?

Owner dispatch: #715 6813573421. Designer ruling: shape (iii), rpg-designer, 2026-11-12, session message.
Base for everything below: origin/main c73d76bad (S1 / divergence 2.204 included).

## Code read (file:line, main)

The movement phase asks `MovementCandidateSelector.movement_target` (src/engine/candidate_selector.py:152-179) for each candidate's target, then calls `MovementSystem.resolve_move` (src/engine/pipeline_phases/movement.py:234, 261).

`movement_target`:
- a target set this tick together with an ENTITY_MOVE task update is a decision and returns the target (line 167);
- an ENTITY_ACT task holding a payload returns None (line 172, `holds_action_task`, line 227-234; divergence 2.84);
- otherwise the stored or live-tracked target is returned unless `is_decided_flight` is false and `engaged_adjacent_hostile` is true (lines 176-178).

`engaged_adjacent_hostile` (candidate_selector.py:132-139) is `_adjacent_hostile(..., engaged=True)` (lines 112-129): an orthogonally adjacent entity with `hostility.is_engaged(entity, other)` and `perceived_hostile(entity, other)`. `is_engaged` (src/engine/hostility.py:41-43) is true only when either side's task payload `target_id` names the other.

Opportunity attacks do not use that test. `resolve_move` finds the swingers with `LegalityServiceV2.get_engaged_hostiles` (src/engine/legality.py:553-578: alive, active, orthogonally adjacent, `_is_engagement_hostile`). So two predicates describe "engaged": the gate needs target-naming, the swing does not.

Writers of the stored targets in the trace rows: `fused_strategic_pass` (src/systems/strategic_systems/intelligence.py:670, the active project's objective position, stored mode kept; :678, the town target with REGROUP; :649, a material lead; :400/:406), and `route_movement_intent` with the entity's stored WANDER mode (src/engine/pipeline_phases/movement.py:~258).

Readers of the gate predicate: candidate_selector.py:177 (the gate), :224 (`move_ends_here`, ends a held non-flight ENTITY_MOVE beside an engaged hostile so it does not stand frozen), scheduler.py:106 (`unengaged_adjacent_hostile`, the Decision-32 wake, which needs the unengaged meaning and must not change). Tests that hook it by name: tests/mechanic_scenarios/test_conflict04_movement_layer.py:81, 176-211; tests/unit/engine/test_diagonal_melee_pair_strikes.py:93; the unengaged wake is pinned by tests/unit/engine/test_notice_unengaged_hostile.py:65-68 and tests/mechanic_scenarios/test_decision32_notice_and_decide.py:101.

## Measurement (stored_target_spy.py sha256 8a122160…, args only, designer-approved)

Main 6e065265f, src/data/config identical to cd83111c5. Both cells hash-matched their plain twins (frontier_marches s42 908eb3bb1441, crowded_frontier s42 e0e20c2044d7); mt_exceptions and rm_exceptions 0. Outputs: /mnt/data2/rpg-measure/storedtarget/{frontier_marches,crowded_frontier}_42.json.

- frontier_marches s42: 1063 rows of an undecided call with a Legality-engaged hostile (299 stepped); 667 further calls where the gate returned None because an engaged adjacent hostile was present. Kept rows 400, all caller=movement_phase, 372 of them ENTITY_ACT with an empty payload. Of kept per-hostile records, 415 are not-engaged and perceived (266) or not-engaged and not perceived (149).
- crowded_frontier s42: 173 rows (80 stepped); 779 gate-None calls. All 173 kept, all movement_phase; 152 of the 153 ENTITY_ACT rows have an empty payload. Per-hostile records: 170 not-engaged and perceived, 5 engaged.
- Designer's reading of the stepped rows: a not-engaged but perceived adjacent hostile almost always swings (fm 63/64, crowded 75/75); a not-perceived one almost never does (fm 1/68). So the target-naming gap is the cost; the perception gap is not. Shapes (i) and (ii) are rejected; shape (iii) is ruled.

## Finding, not a ticket

4 crowded rows and 3 frontier_marches rows took swing damage while NOT stepping (the step failed with LEGAL, occupancy or exhaustion). The gate does not reach those, because there is no stored-target step to hold. Left as a finding.

## Shape (iii) and its outcome

The CONFLICT-04 movement gate counts an orthogonally adjacent, alive, active hostile the subject PERCEIVES as hostile, whether or not either side names the other. The decision branch (ENTITY_MOVE this tick) and the `is_decided_flight` exemption stay. It was built on the parked branch `rpg-stored-target-engaged-step` (ea6417079, never pushed) and measured; see `measurement.md`. The owner chose NO CHANGE (#715 6842890741, 2026-11-13): the freeze it was feared to cause returned. Nothing from that branch lands on main.
