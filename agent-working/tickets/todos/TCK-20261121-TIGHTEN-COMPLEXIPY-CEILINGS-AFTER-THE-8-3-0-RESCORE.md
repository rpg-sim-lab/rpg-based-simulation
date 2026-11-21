---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261121-TIGHTEN-COMPLEXIPY-CEILINGS-AFTER-THE-8-3-0-RESCORE
phase: open
date: 2026-11-21
tags: [testing]
---

# TCK-20261121-TIGHTEN-COMPLEXIPY-CEILINGS-AFTER-THE-8-3-0-RESCORE

## Title
Lower the complexipy ceilings that the 8.3.0 rescore left with slack, and record that every complexipy bump needs a two-version score diff

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Dependabot #981 bumps complexipy 8.0.1 -> 8.3.0, a minor version, so the major-only Dependabot ignore does not hold it back. On 2026-11-21 codebase-planner ran both versions with uvx on the same src/ tree. Both see the same 4050 functions and no symbol changes name. 9 scores change, all of them down: EntityUpdate.is_noop 86->18, SemanticEntityIndexService.get_indexes 30->25, nearest_serving 10->8, DetourSuggestionSystem.suggest_detours 25->24, StrategicIntelligenceSystem.fused_strategic_pass 425->424, three Patch.is_noop methods 3-4->2, and _abandonment_events 5->4. CI stays green, but 4 rows in code_health_exceptions.jsonl (main c540a0b17) are left with a ceiling above the measured value: src/core/updates.py EntityUpdate.is_noop (86), get_indexes (30), suggest_detours (25) and fused_strategic_pass (438). A looser gate than the code is the ratchet loosening, so it is closed straight after the merge. lead-planner agreed this plan (#981 merges as-is; no push to the Dependabot PR).

## Scope
1. After #981 merges, on a tree synced to that main, run `python3 -m codebase.health tighten` with complexipy 8.3.0 (the locked version). Commit only what it lowers. Expect at least the 4 rows above. Any row that is lowered and not in this list gets a line in the Completion Summary.
2. Add a short note where the code-health tooling versions are documented (the code-health section of docs/guidelines/python_code_standard.md or the roadmap's tooling row): a complexipy bump, minor or patch included, is checked by scoring src/ with both versions and diffing per function before merge. A rise blocks the bump unless it is re-baselined with a reason. A fall is followed by `tighten`.

## Out of Scope
- Raising any row.
- The other tools' versions.
- Re-keying (see TCK-20261120-CODE-HEALTH-MOVE-CARRIES-RENAMED-SYMBOLS-AND-PARTIAL-ROW-SETS).

## Acceptance Criteria
- No complexipy row's ceiling is above its 8.3.0 measured value after the tighten, and no value or ceiling goes up.
- `python3 -m codebase.health check` is clean on the committed tree, run last.
- The two-version-diff rule is written in the doc named in Scope 2.

## Related Tickets
- TCK-20261120-CODE-HEALTH-MOVE-CARRIES-RENAMED-SYMBOLS-AND-PARTIAL-ROW-SETS
- TCK-20261120-PYREFLY-BASELINE-DRIFT-AFTER-THE-1-4-1-BUMP (the same tool-bump drift pattern, for pyrefly)

## Related Docs
- docs/guidelines/python_code_standard.md
- docs/plans/codebase_health/python_code_craft_roadmap.md

## Related Stored Artifacts

## Related Code Areas
- codebase/baselines/code_health_exceptions.jsonl
- codebase/health/ratchet.py (`tighten`)

## Assumptions / Open Questions
- Blocked on #981 merging (owner's merge).

## Durable state, lifecycle and clocks
No simulation state. code_health_exceptions.jsonl is written only by `codebase.health` (registry.py).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
