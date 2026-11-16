---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261115-SPECIES-HOSTILITY-TEST-EDITS-A-TRACKED-DATA-FILE-IN-PLACE
phase: open
date: 2026-11-15
tags: []
---

# TCK-20261115-SPECIES-HOSTILITY-TEST-EDITS-A-TRACKED-DATA-FILE-IN-PLACE

## Title
The slow species-hostility metamorphic test rewrites the tracked data/content/social/species_relations.yaml in place, so a killed run leaves the repo dirty and breaks the next run

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found by platform-implementer during the world-farm runs (2026-11-15) and relayed by platform-planner. Checked by rpg-planner-ubuntu on origin/main.

tests/integration/lab/test_species_relations_metamorphic_validation.py::test_species_hostility_increase_does_not_decrease_combat_engagement_rate (@pytest.mark.slow) reads SPECIES_RELATIONS_PATH (l.38, 146), writes a temporary human<->human row into the tracked file (l.198), and restores it in a `finally` (l.240-246). A killed run, by SIGKILL, a timeout reaper or session close, skips the `finally`. The tracked file stays modified, and the next run fails the test's non-vacuity guard. While it runs, any other test or process reading that file in the same checkout sees the mutated row. That covers xdist workers in a slow lane, and another session in the main checkout.

Not a regression: it passes on origin/main (about 298 s).

## Scope
1. Make the variant without touching the tracked file. Either copy the content tree, or the one file, to tmp_path and point the loader at it, or monkeypatch the species-relations loader or its path. Do it the same way the repo's other content-variant tests do, if any exist.
2. Keep the test's meaning: the same two variants, the same assertion, and the same non-vacuity guard.
3. Remove the restore-in-finally, since nothing is left to restore, and add an assert that the tracked file is byte-identical before and after.

## Out of Scope
The species-relations content itself, and any other test.

## Acceptance Criteria
1. After the change, `git status data/` is clean during the run and after a forced kill: start the test, kill it mid-run, then check `git status`.
2. The test's verdict is unchanged on origin/main, shown by one run before and one after.
3. No other test edits a tracked file under data/ in place. Grep tests/ for open(..., "w") on data/ paths, and list any others found as separate todos.

## Related Tickets
TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING (where it surfaced).

## Related Docs
docs/testing/test_taxonomy.md

## Related Stored Artifacts
None.

## Related Code Areas
tests/integration/lab/test_species_relations_metamorphic_validation.py; the species-relations content loader (src/content/).

## Assumptions / Open Questions
Q1: does the lab orchestrator take a content root, or only read repo-relative paths? That decides between the temp-copy and monkeypatch approaches.

## Implementation Notes
Slow test, about 5 min per run, so verifying it needs a slot: cores 4-5 under the usual run rules. Unscheduled; dispatch needs a go.

## Test Summary
(not started)

## Files Changed
(not started)

## Completion Summary
(not started)
