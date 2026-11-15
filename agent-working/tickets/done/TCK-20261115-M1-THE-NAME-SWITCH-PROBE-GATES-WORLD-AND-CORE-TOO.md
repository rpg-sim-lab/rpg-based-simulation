---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261115-M1-THE-NAME-SWITCH-PROBE-GATES-WORLD-AND-CORE-TOO
phase: done
date: 2026-11-15
tags: [testing, architecture]
---

# TCK-20261115-M1-THE-NAME-SWITCH-PROBE-GATES-WORLD-AND-CORE-TOO

## Title
The name-switch probe gates `src/world` and `src/core` as well, so the 15 world switches it only reported now count against the ratchet

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
rpg-planner ruled on PR #918 (comment 6889044816, 2026-11-15) that all 15 report-only rows the M1 name-switch probe found are gating. They are all in `src/world`: boss and threat kind-name spawn control, calamity `'hero'`, creature_territory MONSTER, environment aura HERO_GUILD, the occupation density table, the region threat buckets, and the sovereignty tax and debuffs. `src/core` has no switch beyond the birth-record row in `core/builder.py`, which is already promoted. rpg-planner asked for a follow-on ticket so that #918's head does not move.

## Scope
1. In `tools/test_architecture/name_switch_scan.py`, move `world` and `core` from `REPORT_ONLY` to `SCAN`, leaving `REPORT_ONLY` empty (keep the list and its machinery).
2. Add the 15 world rows to `tests/architecture/name_switch_allowlist.yaml`. Each row cites TCK-20261109-M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES (105 → 120 rows).
3. Drop the `core/builder.py:690` entry from `PROMOTED_GATING`, because `core` now gates as a package. The allowlist row stays.
4. Update the counts and package lists in the scanner docstring and test docstrings to match.

## Out of Scope
- Any `src/` change. Retiring a switch belongs to the retire ticket (rpg).
- The content-alone probe (TCK-20261115-M1-A-TEST-KIND-DECLARED-ONLY-IN-CONTENT-PERCEIVES-EATS-AND-FIGHTS, HELD).
- Widening what the scanner detects (the known limits in #918 stand).

## Acceptance Criteria
1. The scan on the PR head gives 129 gating, 0 report-only and 10 excluded, and the ratchet test is green.
2. All 15 new rows cite the retire ticket. `check_rulings` reports no stale promotion, and `PROMOTED_GATING` no longer holds the builder row.
3. A perturbation (a new `kind == "hero"` compare in a `src/world` module, then restored) fails the test.
4. rpg-planner is sent the row diff and confirms it matches its 6889044816 list.

## Related Tickets
- TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE (the probe; PR #918)
- TCK-20261109-M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES (rows cite it)
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC

## Related Docs
- PR #918 rpg-planner ruling 6889044816; testing-planner review 6889031257; lead review 6889034477

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE/investigation.md (lists the 15 report-only rows)

## Related Code Areas
- tools/test_architecture/name_switch_scan.py
- tests/architecture/name_switch_allowlist.yaml
- tests/architecture/test_no_name_switches_in_decision_paths.py

## Assumptions / Open Questions
- This can only start after #918 merges, since the files are introduced there.
- 129 = 114 + 15. Re-count on the head at build time, because a src/ merge in between can move it.

## Implementation Notes
Dispatched by testing-planner (owner #715 6889056382). `world` and `core` moved from `REPORT_ONLY` to `SCAN`; `REPORT_ONLY` is `()` and `PROMOTED_GATING` is an empty frozenset (machinery kept; the tests that exercised it now pass an explicit `report_only=`). 15 `src/world` rows appended to the allowlist (105 → 120), each citing TCK-20261109-M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES; the `core/builder.py:690` row stays. Re-count on the head (origin/main b6ac7dabb): 139 switches = 129 gating, 0 report-only, 10 excluded, as the ticket predicted.

## Test Summary
`tests/architecture/test_no_name_switches_in_decision_paths.py` 58 passed; `check_rulings` returns no problems. Perturbation: a `kind == "hero"` compare appended to `src/world/threat.py` failed the ratchet test (new name switch); restored, 58 passed again.

## Files Changed
`tools/test_architecture/name_switch_scan.py`, `tests/architecture/name_switch_allowlist.yaml`, `tests/architecture/test_no_name_switches_in_decision_paths.py`.

## Completion Summary
The name-switch ratchet now gates `src/world` and `src/core`: 129 gating, 0 report-only, 10 excluded; 120 allowlist rows. AC4 (rpg-planner confirms the row diff against its 6889044816 list) is with testing-planner, who forwards the diff.
