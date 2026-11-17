---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261026-CLI-ENTITIES-FLAG-IS-PARSED-BUT-NEVER-READ
phase: open
date: 2026-10-26
tags: []
---

# TCK-20261026-CLI-ENTITIES-FLAG-IS-PARSED-BUT-NEVER-READ

## Title
Remove the cli --entities flag: it is parsed but never read, and serve has no such flag (#617)

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
#617 (lead-planner ubuntu; README side fixed by #741): `src/cli/entry.py` parses `--entities`, but nothing reads `args.entities`. `serve` has no `--entities` argument, so the old README server example exited 2. The sandbox world sets its own population (24). rpg-planner ruled on 2026-10-26 (#593 issuecomment-6406593752): REMOVE the flag. A real population override would be a world-config feature, not a CLI flag.

## Scope
Drop `--entities` from the cli parser and its help text, and from any docs or tests that pass it. Close #617 when this lands.

## Out of Scope
A population-override feature.

## Acceptance Criteria
- `python -m src cli --help` no longer lists `--entities`; no src, test or doc references remain; cli tests pass.

## Related Tickets
#617; #741.

## Related Docs
README.md (already fixed); docs/observability/how_to_run_simulation.md (check).

## Related Stored Artifacts

## Related Code Areas
src/cli/entry.py

## Assumptions / Open Questions

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
