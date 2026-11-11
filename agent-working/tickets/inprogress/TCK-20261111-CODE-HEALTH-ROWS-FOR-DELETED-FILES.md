---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261111-CODE-HEALTH-ROWS-FOR-DELETED-FILES
phase: open
date: 2026-11-11
tags: []
---

# TCK-20261111-CODE-HEALTH-ROWS-FOR-DELETED-FILES

## Title
Delete the 57 code-health exception rows that name 13 deleted source files

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
On origin/main 2ea0e4d8f, `python3 -m codebase.health validate` reports `codebase/baselines/code_health_exceptions.jsonl` INVALID with 57 problems (`file does not exist`), while `check` passes. Found by rpg-planner on u24 and relayed by lead-planner; the count was confirmed by lead-planner and by codebase-planner. Owner go: #715 comment 6785323244.

All 13 files were deleted outright, not moved (`git show -M` shows `D`, no `R`):
- #760 2afdba653: `src/systems/crafting.py`, `src/systems/economy_systems/{crafting,loot,town_service}.py`, `src/systems/guild_system.py`, `src/systems/loot_system.py`, `src/systems/quest_system.py`, `src/systems/social_systems/guilds.py`, `src/systems/town_service.py`, `src/systems/world_systems/quest_engine.py`
- #780 fdfc5f9fd: `src/core/recipes.py`, `src/town/blacksmith.py`
- 7b4bf7a30: `src/progression/skills.py`

So no row needs re-pointing, and no ceiling carries to a new path.

## Scope
Remove exactly the rows of `codebase/baselines/code_health_exceptions.jsonl` whose `file` is not in the tree, one `python3 -m codebase.health delete <file> <tool> <rule> [--symbol S]` call per row. Build the list from the file itself on the branch's base, not from this ticket. On 2ea0e4d8f the rows were 57, all ruff, complexipy and line_count rows of the 13 files above.

## Out of Scope
- `codebase.health tighten`, or any other ceiling change. Tighten would lower ceilings across the file, which is wider than this ticket.
- Any row whose file exists, including the `fused_strategic_pass` cognitive-complexity row. An owner-approved 437→438 raise (#715 6776776165) lands on that row with the next u24 RPG PR.
- Any `src/` change. Wiring `validate` into CI.

## Acceptance Criteria
- `python3 -m codebase.health validate` reports the registry valid (0 problems).
- `python3 -m codebase.health check` passes, with no new or worse finding.
- `git diff --stat` shows only deletions in `code_health_exceptions.jsonl`: exactly the counted gone rows removed, 0 lines added, all other rows byte-identical.
- `tests/codebase/` passes. Run the tests that read the registry at minimum (`tests/codebase/conftest.py` users and `test_code_health_ratchet_registry.py`).
- Gates run last, on the exact tree committed.

## Related Tickets
#760, #780 and 7b4bf7a30 (the deletions); TCK-20261009-RATCHET-TIGHTEN-AFTER-PAYDOWN (the earlier gone-row cleanup).

## Related Docs
docs/plans/codebase_health/python_code_craft_roadmap.md (section 6.3, code-health registry and ratchet)

## Related Stored Artifacts
None.

## Related Code Areas
codebase/baselines/code_health_exceptions.jsonl; codebase/health/registry.py; codebase/health/ratchet.py; codebase/health/__main__.py

## Assumptions / Open Questions
The ratchet runs with `check_files=False` and reports these rows as "gone", which never fails, so nothing is red today. If the u24 RPG PR with the 437→438 raise lands first, sync to main before the push. Those are separate lines, so no conflict is expected. #860 and #861 are ahead of this in the REGISTRY order. Owner rule #715 6785100551 (a ceiling raise names a paydown `retiring_ticket`) does not apply: this ticket raises nothing.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
