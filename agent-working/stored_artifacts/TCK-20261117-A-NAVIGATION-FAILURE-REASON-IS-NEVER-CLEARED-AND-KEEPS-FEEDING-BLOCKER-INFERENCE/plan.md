---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261117-A-NAVIGATION-FAILURE-REASON-IS-NEVER-CLEARED-AND-KEEPS-FEEDING-BLOCKER-INFERENCE
phase: done
artifact_type: plan
date: 2026-11-18
tags: []
---

# Plan: last_failure_reason lifecycle (divergence 2.215, COMB-357)

Designer rulings via rpg-planner (#715 6967356642, 6967398421).
1. `last_failure_reason` is the outcome of the LAST step: a typed `NavigationUpdate.failure_reason_clear` clears it; a bare None leaves the old value; a code beats a clear (`NavigationPatch.apply`).
2. Move law: any position change by the movement apply path (own step, swap, yield displacement; lodge entry and exit excluded) carries the clear and no code. YIELDING and POSITION_SWAP are no longer written.
3. Within movement routing a code the phase itself wrote for a body is dropped when that body is then displaced and the pre-phase code is restored (`_merge_move_update`); an earlier-phase (action) code survives; a later code wins.
4. `OCCUPANCY_CONFLICT` becomes a `ReasonCode` member with the same value.
5. Docs: divergence 2.215, COMB-357, Bible 04 `access`, information_contract `claim_failed_search`. Tests: lifecycle, move-law, four owner-approved assertion edits.
