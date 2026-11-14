---
status: historical
layer: strategy
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE
phase: done
date: 2026-11-12
tags: []
---

# Plan (shape iii, rpg-designer 2026-11-12; owner dispatch #715 6813573421)

1. Gate. In src/engine/candidate_selector.py make the CONFLICT-04 movement gate count an orthogonally adjacent, alive, active hostile the subject perceives as hostile (`perceived_hostile`), whether or not either side names the other. Decision branch and `is_decided_flight` exemption unchanged. `move_ends_here` (line 224) flips with the gate unless the designer rules otherwise. The Decision-32 wake (`unengaged_adjacent_hostile`, scheduler.py:106) is not changed. No edit in intelligence.py. WAITING for the designer's answers (move_ends_here, name) before any src edit.
2. Tests: perceived-adjacent with no naming is held; not perceived walks; a decided ENTITY_MOVE steps; a decided flight steps; 2.84 and 2.204 unchanged.
3. Docs: Bible 02 §7 (replace the parenthetical "The movement phase still walks a stored target while engaged when no blow is felt-lethal"), new divergence 2.206 (cross-citing 2.84, 2.86/2.87, 2.204), the COMB parity-ledger entries.
4. Measurement (after the build, under HOST FREE): crowded_frontier, urban_political, frontier_marches, s42-46, 5000 ticks, base = main at dispatch vs the fix head: 30 runs, one at a time. Bars: Tier 1/Tier 2 and the extinction stop on 5-seed sums, plus the S1 pin rules. Plain-twin check for every spied cell. A new fix spy, sent to rpg-planner for designer approval before any run. Expected direction, stated before the data: undecided free-swing damage falls to near 0 in frontier_marches and crowded_frontier, and DEFEAT falls; any COMBAT or STARVATION rise goes through the bar.
5. The corpus test test_defeat_deaths_are_recorded_in_unscripted_corpus_play rests on frontier_marches s43's t110 DEFEAT. If S2 removes it, re-size from measured cells per the 2026-11-12 ruling; never delete it or script the DEFEAT.
6. Nothing is pushed; the push is a separate owner ask.

## Outcome

The build and the first S2 fix cell were done on the parked branch; S2 stopped by the freeze bar in its first fix cell (frontier_marches s42). The owner chose NO CHANGE (#715 6842890741). Steps 3 to 5 above (docs, the 30-cell measurement, the corpus-test re-size) were not carried out, and nothing from the branch lands. See `measurement.md`.
