---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE
phase: done
date: 2026-11-09
tags: [combat, determinism]
---

# TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE

## Title
A flight weighs the free swing it would take

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
A fighter in melee does not flee when the free swing it has felt would kill it (owner, #715 6735931881). Design: `.claude/handover/drafts/rpg-designer-flight-weighs-free-swing-design.md`. Dispatch: rpg-planner.

## Scope
1. Field and carrier: `CombatUpdate.hit_damage_set`, `CombatComponent.last_hit_damage`, digest scheme `flat-sha256-v4`, shared `is_evasive_flight`.
2. The guard `flight_weighs_free_swing` at every FLIGHT_REASONS emission site (later commits).
3. Docs: Bible 02 §7, CONFLICT-04 corollary, divergence 2.202, combat_movement parity entry.

## Out of Scope
KITING and KEEP_DISTANCE; non-flight moves off engagement (e24); the double resolve_attack per tick (filed P2); perf follow-ups (v1 base re-record under v4, ledger row, schema enum, hash_callsite_inventory wording).

## Acceptance Criteria
- Field commit: stripped-digest equivalence on crowded s42 (scheme label normalised and `last_hit_damage` dropped) equals base.
- The designer's 13 rows + 2 + coverage test pass; guard rows discriminate.

## Related Tickets
TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE; TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS

## Related Docs
docs/mechanics/02_combat_laws.md; docs/world_rules conflict-combat.md (CONFLICT-04); docs/engine/deterministic_execution.md

## Related Stored Artifacts
`agent-working/stored_artifacts/TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE/evidence/`: the arm wrapper `arm_child_flight.py`, the Tier 2 rows builder `flight_rows.py` (sha256 535897f5…) and the three Tier 2 row files `rows_crowded_42.json`, `rows_crowded_43.json`, `rows_urban_46.json`.

## Related Code Areas
src/core/state.py; src/core/updates.py; src/engine/patches.py; src/engine/combat.py; src/engine/movement.py; src/engine/checkpoint.py; src/perf/benchmark_record.py

## Assumptions / Open Questions
No committed baseline or benchmark record carries the scheme in a machine-checked form; re-recording the v1 base under v4, the ledger row, the schema enum and the inventory wording are perf follow-ups queued for the perf seat.

## Implementation Notes
Digest bump to v4 ruled by rpg-planner. docs/engine edits limited to deterministic_execution :85/:102, known_limitations :120, substrate_baseline_contract :68.

- Mechanism-registry advisory (rpg-planner, 2026-11-09): no `mechanisms.yaml` edit needed. Both extracts (`is_evasive_flight`, `live_action_style`) are behaviour-free, the guard adds no new mechanism identity, and it sits under `tactical_decision`.
- `live_action_style` landed in the guard commit, not the field commit, so the (i) stripped-digest check does not cover it; arm 1's 0-fire seeds do (stripped digest = base). A 0-fire seed whose stripped digest differs: suspect that extract first.
- Open design point with the designer: 2.202 item 5 (a flight whose target is the subject's own tile is left alone).
- Filed: TCK-20261109-RESOLVE-ATTACK-IS-CALLED-TWICE-PER-TICK-FOR-ONE-HIT-AND-ONLY-ONE-RESULT-REACHES-HP (P2).

## Test Summary
- New tests: 13 in `tests/unit/engine/test_last_hit_damage.py`, 20 in `tests/unit/tactical/test_flight_weighs_free_swing.py`, 3 kernel scenarios with a control arm in `tests/mechanic_scenarios/test_flight_weighs_free_swing_through_kernel.py`. Pinned digests moved by exactly the new key (FIXTURE_DIGEST_V4 added; the v3 form is reproduced by dropping `last_hit_damage`).
- Field commit `aacefef9c`: 136 passed at `-n1` in the scoped set. `pytest tests/unit/perf -q` on the final perf range: 431 passed.
- Equivalence (i): the field commit on crowded s42, 5000 ticks, stripped digest equals the base `6b17b470c66c5b0b538aeaf9c8976e6d7b680f5380067082bf4b05354e435565`. Plain vs spied runs give identical digests on crowded s42 and urban s42.
- Measurement (5 seeds x 5000, crowded and urban, paired): COMBAT meets Tier 1 in both worlds (crowded 86 to 114, urban 27 to 39, each up in 4 of 5 seeds), DEFEAT falls (57 to 31, 16 to 2), deaths fall overall (168 to 160, 55 to 54). Tier 2 trace (31 subjects): 0 FED; 5 RELABEL, 6 OUTLIVE, 2 diverged, 18 DRIFT. Owner ruled the crowded scout 1 to 0 as drift (#715 6747647902).
- Timing NOT MEASURED (perf pause).
- Known gaps: only PANIC_RETREAT is driven end to end; the other five sites are checked by a built update plus a source-level wiring test; SAFETY_PRESSURE_RETREAT and LEASH_RETURN never fired in the measured worlds, FLEE_THREAT was called but never fired; the broad `-n` sweep (unit, certification, mechanic_scenarios, codebase) was never completed on this branch (host-load order), so CI is the first full run.

## Files Changed
See commits `aacefef9c` (field, carrier, extracts), `e0931a3af` (guard), `93767933a` (P2 filing), `d606adf32`, `83004a122`, `fdc9fd981` (v4 pin in the long-run record test), `f57e15a16` (2.202 measurement and evidence).

## Completion Summary
A tactical flight is withheld when the last blow the subject felt (`CombatComponent.last_hit_damage`) came from a hostile still engaged with it and is at least its remaining health, unless the flight is an evasive retreat; the subject answers that hostile (ATTACK, else the held swing, else an in-place hold). The felt blow is typed state carried by `CombatUpdate.hit_damage_set`, in the proof digest `flat-sha256-v4`. Docs: Bible 02 section 7, CONFLICT-04 corollary, divergence 2.202 (with the Tier 1 COMBAT relabel and the Tier 2 NOT FED result), COMB-351 and the COMB-009 note. Owner: #715 6735931881 (decision), 6741709441 and 6741737668 (perf-pause exemption for the v4 lines), 6747647902 (scout ruled as drift), 6747660679 (push at f57e15a16). Filed: the double `resolve_attack` per tick (P2). The standard-tier staging artifacts (plan.md, investigation.md, test_plan.md) were written retroactively at close from the landed work, with no result or code changed; the two done_checker migration_complete verdicts (gv-749a9227c7db43c7, gv-072c167c55764266) are recorded as overridden.
