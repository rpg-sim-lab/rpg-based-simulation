---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING
phase: done
date: 2026-11-10
tags: []
---

# TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING

## Title
A subject with no flight decision moves off engagement and walks into a free swing it has felt will finish it (the CONFLICT-04 "neither" shape)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Requested by rpg-designer on 2026-11-09/10, in its def2 and flight Tier 2 rulings.

The flight guard (TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE, divergence 2.202) weighs the felt free swing only at the 6 flight sites. Some subjects have no decision on the death tick and an ENTITY_ACT task at tick start, yet they still leave engagement and take a lethal movement opportunity attack (DEFEAT). The guard never reaches them. This is the old "moved with no move task" class, and rpg-designer reads it as the CONFLICT-04 "neither" defect still standing.

Evidence (pinned traces; each hash-matches its cell):
- Flight Tier 2, fix arm on 83004a122. Each row: opp=True call on the death tick, no decision that tick, ENTITY_ACT task, call lethal flag false.
  - crowded s42 #14: t323, hp 6, swing 11, attacker 34, DEFEAT.
  - crowded s42 #3: t2050, hp 26, swing 40, attackers 30 and 38, DEFEAT.
  - crowded s42 #12: t4971, hp 2, swing 21, attacker 30, DEFEAT.
  - crowded s43 #37: t1632, hp 11, swing 12, attacker 30, DEFEAT.
  - crowded s43 #12: t3053, hp 13, swing 21, attacker 30, DEFEAT.
  - urban s46: no rows.
- Hardening def2, fix arm 3300928e88c4: crowded s43 #1 and #8, crowded s45 #5, all with no decision on t, an ENTITY_ACT task, and the OA.
- Hit-wake trace, urban s46 (B e755dc3d1 vs W aa209f2d6; defeat_{B,W}_5000.json in /mnt/data2/scratch-c3/): subject e24's fatal move off engagement was an engage BRACKETING step into the free swing, not a flight. So the same shape also arises from an engage move, not only from a no-decision ENTITY_ACT.
- Attacker 30 lands most of these blows. Across def2, killer 30 landed 8 of 10 fatal swings.
- Rows are in /mnt/data2/rpg-measure/flight/rows/*.json and /mnt/data2/scratch-c3/def2/rows.txt. They are copied into this ticket's evidence at scoping.

## Scope
1. Investigate first: which code path moves an ENTITY_ACT subject with no decision on the tick (a carried move task, a nav continuation, or a group or bracketing move), and why the movement OA fires on it. Name the writer.
2. Then rpg-designer rules on the fix: extend the felt-swing weighing to that path, or stop the move, without stacking more tactical goal scoring.
3. Tests: a kernel row reproducing one evidence case; a unit row for the named path.
4. A paired measurement on the pinned runner, after the current heads. rpg-designer sets the bar.

## Out of Scope
- The 6 flight sites already guarded (2.202).
- Swaps off engagement being free (rpg-designer's parked tension; urban swaps 23→53 under the guard).
- Hazard-cluster bracketing (TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER), related but a different harm.

## Acceptance Criteria
- The moving writer is named, with a trace row.
- Tests in Scope 3 pass, and the measurement passes rpg-designer's bar or goes to the owner.
- Bible 02 §7 / CONFLICT-04 text, the parity ledger and a divergence entry (u24 block) are updated.
- Hot-loop: maybe. Timing is NOT MEASURED under the perf pause (#715 6556861718).

## Related Tickets
- TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE
- TCK-20261103-NEAR-DEATH-HARDENING-FIRES-WITH-NOTHING-HITTING-THE-SUBJECT (def2 evidence)
- TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER (related)

## Related Docs
- docs/mechanics/02_combat_laws.md §7; docs/guidelines/intentional_divergences.md 2.202

## Related Stored Artifacts
- Pending: the flight ticket's evidence (Tier 2 rows).

## Related Code Areas
- src/engine/movement.py (opportunity attack, :324)
- src/engine/tactical.py, src/engine/tactical_flight_guard.py

## Assumptions / Open Questions
- rpg-designer, 2026-11-10: the BRACKETING ticket TCK-20261020 is related only (a different harm). The hit-wake subject e24's bracketing step is an evidence row here.
- rpg-designer, 2026-11-10, priority: not dispatchable until its design is done. The response for a non-flight move (hold the move, swap the target?) is open. It drafts the design after the owner's scout ruling and the hit-wake re-measure, since hit-wake changes how often engaged hit subjects re-decide. Queue: after flight, hardening and hit-wake, ahead of the rejection-count fix (it's on the death path). The measurement is a separate run on its own base, under the same bar.
- rpg-planner, 2026-11-10, place: after next-gen child 2's cells and A+B. Both are already queued, and this ticket's design lands later anyway. It sits ahead of TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME.

## Implementation Notes
Scope 1 trace done (read-only, 5 hash-matched runs): see agent-working/staging_artifacts/TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING/investigation.md (writer lines, run table, writer diffs vs 5c6990e51). No fix code until rpg-designer rules.

## Test Summary
- New unit rows: `tests/unit/movement/test_felt_lethal_free_swing_step.py` (8 rows: held, reposition held, under-hp taken, not-engaged taken, no felt blow taken, evasive unaffected, held equals the blocked-step shape, cache untouched). New kernel rows: `tests/mechanic_scenarios/test_engaged_subject_does_not_walk_a_stored_target_through_kernel.py` (main plus control).
- Edited: `test_flight_weighs_free_swing_through_kernel.py`. Its 2.202 control now switches off both guards (the new step guard also holds that flight, which changes the control's premise; rpg-designer approved the edit, and the test file also gains a backstop row, `test_with_only_the_flight_guard_off_the_step_guard_holds_the_flight`). This is a premise change, not a gate pass. Completeness pins in `test_mechanism_registry_completeness_check.py` moved 361→362 and 255→256 from the check's own output.
- Run so far: the unit directories above, the mypy gate and the code-health check were green. `tests/architecture` (153 passed), code-health and the mypy gate ran green on 9c0b93b4e; the scoped set was 228 passed, 1 xfailed; the final head is re-run. The corpus DEFEAT test was re-pointed to frontier_marches s43 (see Known gaps).
- Measurement: `agent-working/stored_artifacts/TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING/measurement.md` (22 runs; three plain-twin hash checks MATCH; no world × cause tripped under rpg-designer's ruling).

## Files Changed
- src: `src/engine/felt_swing.py` (new; `felt_lethal_attacker` moved unchanged from the flight guard), `src/engine/movement.py` (held-step check in `resolve_move`, helpers `_held_by_felt_lethal_swing`, `_store_plan`, `_evasive_escape`), `src/engine/tactical_flight_guard.py` (import), `src/core/enums.py` (`FELT_LETHAL_FREE_SWING`).
- tests: the four files listed under Test Summary.
- docs: `docs/mechanics/02_combat_laws.md` (§7), `docs/parity_ledger/combat_movement.yaml` (COMB-352), `docs/guidelines/intentional_divergences.md` (2.204 with the Measured figures).
- tickets: the two TCK-20261111 todo tickets (stored REGROUP oscillation, hold-mode step) and `TCK-20261111-FELT-LETHAL-MEMORY-HAS-NO-RECENCY-WINDOW.md` filed unchanged; widen note on the COMBAT-RETREAT-PROJECT ticket.

## Completion Summary
Rule S1 (divergence 2.204): `MovementSystem.resolve_move` now holds a step off engagement when an engaged hostile is the subject's felt-lethal attacker, unless the step is an evasive retreat. The held step is the blocked-step shape with the typed `FELT_LETHAL_FREE_SWING` reason; target, position, stamina and cache are untouched. The Scope 1 trace named the writer (the movement phase walking a stored target, plus one decided BRACKETING step).
Measured on main 5c6990e51 against fix 824483949 (crowded and urban, s42-46, 5000 ticks): crowded COMBAT 118→125, DEFEAT 26→16, HAZARD 16→17, STARVATION 0→2, all 160→160; urban hash-identical to base. Under rpg-designer's ruling nothing tripped (COMBAT +7 against a bar of 12; STARVATION +2 with 2 of 5 seeds up), so Tier 2 tested no subject.
Known gap: 1 held-linked death where base survives (untested, below the bar): s45 e11, held t1926, dies COMBAT t1935, base alive at the end; its base death tick was not looked up.
Known gap: pins of 50+ ticks beside a non-striking hostile are S1's cost. P2 cells: s42 e3 held 71 ticks and survives, s43 e33 held 65 ticks and dies COMBAT 1261 ticks later. frontier_marches s42 e31 is the longest: 511 held ticks across t1500-2371, 461 of them consecutive, hp never falls (1→4, 10 at t2371), then DEFEAT at t2407; TCK-20261111-FELT-LETHAL-MEMORY-HAS-NO-RECENCY-WINDOW was later ruled NO CHANGE (rpg-designer, 2026-11-12): the hold was correct, because a sleeping or collapsed hostile still lands the free swing; it reopens only on a traced hold where the swing would not have been lethal.
Known gap: the stop rule changed after the designer reviewed the first two pins.
Known gap: s45 e5 (held 2117-2150, STARVATION t2161) was cited for TCK-20261111-FELT-LETHAL-MEMORY-HAS-NO-RECENCY-WINDOW, later ruled NO CHANGE (a correct hold; rpg-designer, 2026-11-12).
Known gap: the shaman goes from 1 alive to 0 on the frontier_marches 5-seed sums (s44 e47); rpg-designer classed it DRIFT (2026-11-12, session message); owner ruling #715 6812076549.
Known gap: the corpus DEFEAT test moved from frontier_marches s42 to s43 (window kept at 400) because S1 removes the early s42 DEFEATs; the old figure of 8 by t400 was stale (2 measured at base).
Gates (tests/architecture 153 passed, code-health, mypy gate, scoped set 228 passed 1 xfailed) ran green on 9c0b93b4e; the final head is re-run.
Known gap: timing is NOT MEASURED (perf pause, #715 6556861718).
