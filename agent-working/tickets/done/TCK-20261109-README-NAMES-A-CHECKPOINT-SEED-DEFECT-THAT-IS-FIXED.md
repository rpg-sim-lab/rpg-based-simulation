---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20261109-README-NAMES-A-CHECKPOINT-SEED-DEFECT-THAT-IS-FIXED
phase: done
date: 2026-11-09
tags: []
---

# TCK-20261109-README-NAMES-A-CHECKPOINT-SEED-DEFECT-THAT-IS-FIXED

## Title
The README still lists the restored-checkpoint seed-0 defect as open, but #848 fixed it

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
`README.md:79` says one open defect isn't yet in `known_limitations.md`: restoring a scenario checkpoint rebuilds the RNG with base seed 0. #848 (merged 2026-11-08, 66d08dd56) closed TCK-20261107-A-RESTORED-SCENARIO-CHECKPOINT-DRAWS-FROM-SEED-0, so the sentence is now false. rpg-planner-ubuntu confirmed the fix had landed. The owner approved folding this into the website hotfix PR on 2026-11-09 (#715 comment 6724653808).

## Scope
- Remove the "One open defect not yet listed there: ..." sentence from `README.md:79`, keeping the link to `docs/engine/known_limitations.md`.

## Out of Scope
- Any other README change.
- Editing `docs/engine/known_limitations.md`.

## Acceptance Criteria
- `README.md` no longer says restoring a checkpoint draws from seed 0.
- The `known_limitations.md` link still resolves.

## Related Tickets
- TCK-20261107-A-RESTORED-SCENARIO-CHECKPOINT-DRAWS-FROM-SEED-0 (the fix, #848)
- TCK-20261109-WEBSITE-LOCKFILE-PINS-JOI-AND-FOLLOW-REDIRECTS-WITH-OPEN-HIGH-ALERTS (same PR)

## Related Docs
- docs/engine/known_limitations.md

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
README.md

## Assumptions / Open Questions
None.

## Implementation Notes
Removed the sentence from `README.md:79`. Before that, I checked the fix on main 8d9f3ebf3: `src/engine/scenario_checkpoint.py:92` builds `DeterministicRNG(base_seed=state.seed)`, and TCK-20261107-A-RESTORED-SCENARIO-CHECKPOINT-DRAWS-FROM-SEED-0 is in `agent-working/tickets/done/`.

## Test Summary
- `README.md:79` now reads only "Limits and known defects: [docs/engine/known_limitations.md](docs/engine/known_limitations.md)."
- `docs/engine/known_limitations.md` exists, so the link resolves.
- No tests reference the removed sentence (grepped tests/ for "base seed 0").

## Files Changed
- README.md

## Completion Summary
Done. The README no longer lists the fixed checkpoint-seed defect as open.
