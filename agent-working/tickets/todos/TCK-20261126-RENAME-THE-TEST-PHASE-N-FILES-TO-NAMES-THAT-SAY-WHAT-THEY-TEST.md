---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261126-RENAME-THE-TEST-PHASE-N-FILES-TO-NAMES-THAT-SAY-WHAT-THEY-TEST
phase: open
date: 2026-11-26
tags: []
---

# TCK-20261126-RENAME-THE-TEST-PHASE-N-FILES-TO-NAMES-THAT-SAY-WHAT-THEY-TEST

## Title
Rename the `test_phase<N>_*` files (and the other bare-code file names) to names that say what they test

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Owner direction #715 7181423761: file names say what they do, with no bare internal codes. `tests/tools/test_file_names_carry_meaning.py` (landed with the K3 PR) fails on a NEW offender and lists the existing ones in `KNOWN_OFFENDERS`. Scan of the K3 branch (rule: a whole token `k<N>`, `phase<N>`, `step<N>`, `s<N>`, `f<N>`, `m<N>` or a leading `v<N>` in a `.py` or `.sh` basename under tools/ or tests/): 199 files, of which 191 are `test_phase<N>_*` and 8 others (`tests/integration/kernel/test_substrate_freeze_m1.py`, `tests/integration/observability/test_v1_counts_an_unbacked_hunger_drop_through_the_real_kernel.py`, `.../test_v4_counts_a_forbidden_meal_through_the_real_kernel.py`, `tests/simulation_quality/rpg_gate/test_v8_fires.py`, `tests/tools/test_step0_ts_orchestrator.py`, `tests/unit/social/test_contract_lifecycle_phase7.py`, `tests/unit/social/test_social_phase7.py`, `tests/visual_assets/test_v2_terrain_aliases.py`).

## Scope
Rename the files in batches (git mv, no logic or assertion change), updating every reference (imports, CI workflows, ticket-owned doc paths that are not history), and remove each renamed file from `KNOWN_OFFENDERS` in the same batch. Proposed batches: by directory (tests/certification, tests/integration, tests/unit, tests/tools, others). The new name says what the file tests, read from the file.

## Out of Scope
Archive docs, closed tickets, stored artifacts and monitoring shards (history). Any change to what a test asserts. Data files (`.json`, `.yaml`) and `v<N>` version suffixes that come after a name.

## Acceptance Criteria
- `KNOWN_OFFENDERS` is empty and the name-check test passes with an empty list.
- No behaviour change: the renamed tests pass as before; the CI workflows and Makefile targets that name a file still resolve.

## Related Tickets
- TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH (landed the rule and the kit renames)

## Related Docs
- docs/engine/architecture_reference.md section 9.1a
- tools/rpg_measure/README.md ("Old names")

## Related Stored Artifacts

## Related Code Areas
- tests/ and tools/ (file names only); tests/tools/test_file_names_carry_meaning.py

## Assumptions / Open Questions
Not dispatched. Owner of testing paths (tests/architecture, docs/plans/test_architecture) is testing-planner; the batches that touch `tests/certification` and other testing-authority paths need the lead's testing-authority yes first.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
