---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON

## Title
After a way-round give-up, the target choice picks the same target again within 200 ticks; add a typed give-up memory that target choice respects (F2)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by the STALEMATE fix's own-job run (S9 #715 6947037311, fixtree 08b9dcae8). After a way-round give-up, the given-up target is chosen again within 200 ticks:
- crowded_frontier: 17 of 17 subjects, 238 events;
- frontier_living_world: 37 of 38 subjects, 1093 events;
- urban_political: 20 of 20 subjects, 477 events.

The give-up clears the target, but nothing remembers that it was given up, so target choice picks it again. The rpg-designer ruling (draft .claude/handover/drafts/rpg-designer-stalemate-s3-ruling.md, sha prefix 82f62819) makes this F2: a separate Phase-1 liveness ticket in run 1. It was first filed as not gating the STALEMATE F1 PR, with one exception: any subject giving up the same anchor 5 or more times in 5000 ticks comes back to the designer before merge. UPDATE 2026-11-17 (designer ruling, draft section 06149efe): F1's own-job (S9 #715 6949902550) showed 30/39/17 subject-anchors with 5 or more give-ups, max 194 (frontier eid 42 at (140,40)). That is a never-exit loop, so F2 now GATES F1's merge, and F1+F2 land together.

## Scope
1. DESIGN: FINAL v2 by rpg-designer, main-checkout .claude/handover/drafts/rpg-designer-f2-giveup-memory.md (sha prefix 78152d88; the v2 section supersedes everything above it). In short:
   - NavigationComponent.giveup_records (typed, at most 4): movement appends at the give-up, and the next strategic pass consumes them.
   - Consuming files an ACCESS blocker on the current project through the churn lifecycle, with the subject from the shared access_subject(tile) helper.
   - destination_suppressed() is checked by both target writers. The tactical skip is the typed outcome OBJECTIVE_DESTINATION_SUPPRESSED, with no fall-through.
   - BLOCKER_TIMEOUT ends the project.
   Hard bars G1-G5 plus F1's S1-S3 are FIXED in v2.
   ORDER: N10 -> churn -> SPLIT-INTELLIGENCE-PY -> F1+F2. F2 adds nothing to intelligence.py before the split.
2. Implementation, tests and a measured rerun, after the design.

## Out of Scope
- F1, the way-round count anchoring (the STALEMATE fix PR).
- Blocker-churn work.

## Acceptance Criteria
- Set by the designer's design. At minimum: after the fix, the "give-up target re-chosen within 200 ticks" count falls by an agreed bar on the 3 standard cells, with no S1/S2/S3 regression.

## Related Tickets
- TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK (the STALEMATE fix lane; F1)
- TCK-20261117-A-BLOCKED-WALKER-HAS-NO-MEMORY-OF-ITS-DETOUR-HEADING (neighbouring memory gap)

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- the 2.213 amendment in the designer's draft

## Related Stored Artifacts
- /mnt/data2/rpg-measure/stalemate/cells_fix/ and cells_fix_v7/ (on the owner's delete list)

## Related Code Areas
- src/engine/patches.py (navigation apply), resolve_move, the target-choice path (to be located in the design)

## Assumptions / Open Questions
- Where the memory lives (NavigationComponent or cognition memory), its expiry and its scope (per tile, per anchor or per target kind): the designer decides.

## Implementation Notes
Parked: waits on TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK since 2026-11-19
- 2026-11-19 RELABELLED P0 -> P1 (owner, #715 7003889137, "Relabel P1, keep W1"). It is a liveness bug: every subject in the 3 gate worlds re-picks a given-up target, but nobody dies of it. It keeps its M1 place at W1, intelligence.py package step K1: after split Group 1, stacked on F1 (TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK).

### F2 v2.2a A'' + C disclosures (rpg-designer ruling on the v10.1 smoke, 2026-11-22; head 0bfa0f6bb)
- `src/systems/strategic_systems/work_queue.py` joins the F2 file set (tier 6b: a subject with a pending give-up record). Tier 6b is urgent, so it can shrink the background sweep's (tier 7) share when the urgent tiers together are fewer than the budget.
- The queue's per-tier served counts are NOT measured (the approved kit has no queue probe; not a bar).
- The A'' rule (a give-up's clear beats a same-update target set near its own anchor, `NavigationPatch.apply`) acts on ONE merged update only: a record and a set applied as two separate patches do not trigger it. The same-update `path_set` is dropped with the set (the update already carries `clear_path`; designer accepted).
- The fast path and the queue test the STORED record: a record staged this tick is consumed next tick.
- Kit note (rpg-designer 2026-11-22): the trace runner writes `__pycache__` into its tree (no PYTHONDONTWRITEBYTECODE unless the launcher exports it) and the kernel writes `data/runs` into its tree, so every run gets a fresh `git archive` and a tree that has been run in is never reused (fixtree_v10 and fixtree_v11 each held one smoke; the earlier smokes stand because their trees were clean at the start).
- Kit note (rpg-designer 2026-11-22, after the pairing run's busy_gate STOP, driver_rc 9): no pytest or other heavy job on the host while a measurement runs (busy_gate counts any pytest under the rpg paths as heavy and stops the run between processes). A stopped attempt's directory stays as its record (cells_v11_pair holds the crowded_frontier plain twin, final_hash 0f4c98e2..., equal to the v10.1 full run's plain: a determinism cross-check); a re-run uses a new directory through a launcher copy and a fresh tree.
- Kit note (rpg-designer 2026-11-22): `giveup_clear_beats_target` was removed from src; the pairing spy v11 imports it under try/except ImportError, so its a2_fires reads None on a tree without it (fine for the finished run). Any FUTURE rule-measuring spy must call `anchored_target` (`src/core/giveup_records.py`), at a new sha.

## Test Summary

## Files Changed

## Completion Summary
