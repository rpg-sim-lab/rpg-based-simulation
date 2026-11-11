---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261109-THE-FAST-STRATEGIC-PATH-SENDS-AN-ENTITY-TARGET-PURSUER-HOME-WITH-ITS-ITEMS
artifact_type: plan
phase: done
date: 2026-11-11
tags: []
---

# Plan

Written retroactively at close (2026-11-11). This records the work as done; it was not a pre-implementation artifact.

## A (the fix), as built
The guard became `if not lodged_stayer and not (active_obj and (getattr(active_obj, 'target_position', None) is not None or getattr(active_obj, 'target_entity_id', None) is not None))`. A point or an entity objective owns the direction, as on the slow path (~:663). Commits e3b3be09c then c78d4c4b0.

**Rejected form.** e3b3be09c used a tuple comparison `(pos, ent) != (None, None)`, chosen to keep cognitive complexity under the ratchet. rpg-planner rejected it as shaping code to the gate. c78d4c4b0 dropped three redundant operands (shown equivalent in the investigation) and used a plain `or`. That honest form still scores one higher.

**Ceiling.** `StrategicIntelligenceSystem.fused_strategic_pass` complexipy cognitive-complexity ceiling 437 to 438 (`codebase/baselines/code_health_exceptions.jsonl`, `value` unchanged). Owner-approved: #715 6776776165 (c1c762a46). No other ratchet edit.

## B (hygiene), as built (c7607b6da)
- The capacity block cites STRAT-006/STRAT-007 and says it runs on every slow-path evaluation; a fast-path hit skips it.
- The three bare excepts are line-for-line one-liners that catch only what they guard and log at debug via the module `logger`. A multi-line first version added 4 lines and tripped three code-health rows, so it was reshaped.
- 26ca2c77c: comment-only change on the :395 line, stating the guard does not check the objective's own status.

## Notes
Scope notes on TCK-20261101-CLEAR-TARGET-IS-NEVER-APPLIED (overwrite inconsistency) and TCK-20261101-FUSED-STRATEGIC-PASS-RESTRUCTURE (note D: folded into the next-gen contract after M1; plus the status-check line). Parity: COMB-329. Divergence: 2.68 gains one line (Bug Fix).
