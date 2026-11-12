---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261112-OBSERVABILITY-SKILL-HARD-LAW-COUNT
phase: open
date: 2026-11-12
tags: [skills, observability]
---

# TCK-20261112-OBSERVABILITY-SKILL-HARD-LAW-COUNT

## Title
The observability skill and the skills index name all nine HardLawMonitor laws, not seven

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`src/observability/hard_law_monitor.py` on main 4eaab4d8b checks nine laws. `docs/observability/hard_law_monitor.md`
§1 already says "nine" and lists all nine. Two agent-facing files still say seven:
- `.claude/skills/observability/SKILL.md`: the heading "The 7 Hard Laws". Its table has 7 rows and is
  missing `LAW-POSITION-IN-WORLD` (added 2026-10-10) and `LAW-LODGER-INDOORS` (F3, divergence 2.155).
  It also says "the other six DirtySet-gated laws" and "all seven laws above".
- `docs/ai/skills.md:227`: "HardLawMonitor's 7 laws".
Owner OK to ride the next agent-working PR, 2026-11-12, AskUserQuestion to agent-working-planner, under the
ride-along rule (#715 6793205403). Both files are unowned in the routing manifest. agent-working takes them
here, as agent tooling docs.

## Scope
In `.claude/skills/observability/SKILL.md`:
1. `## The 7 Hard Laws (\`HardLawMonitor\`)` becomes `## The 9 Hard Laws (\`HardLawMonitor\`)`.
2. In the table, insert this row directly after the `LAW-POSITION-FINITE` row:
   `| \`LAW-POSITION-IN-WORLD\` | \`DirtySet.all_dirty_entities\` | Committed position of an active, alive entity lies inside the world extent (union of declared region bounds) | ERROR |`
3. Append this row after the `LAW-SPAWN-OCCUPANCY` row:
   `| \`LAW-LODGER-INDOORS\` | \`DirtySet.all_dirty_entities\` | An entity with \`navigation.lodged_in\` set stands on its building's tile and has no navigation target | ERROR |`
4. "the other six DirtySet-gated laws" becomes "the other eight DirtySet-gated laws".
5. "applies identically to all seven laws above" becomes "applies identically to all nine laws above".

In `docs/ai/skills.md:227`: "HardLawMonitor's 7 laws" becomes "HardLawMonitor's 9 laws".

Check the wording of the two new rows against `docs/observability/hard_law_monitor.md` §1 rows 25 and 28 on
the branch head. If §1 changed since 4eaab4d8b, follow §1.

## Out of Scope
- `docs/observability/hard_law_monitor.md` (already correct), and any code.
- Other skills or docs.

## Acceptance Criteria
1. `git grep -nE "7 (hard )?laws|seven laws|other six" -- .claude/skills/observability docs/ai/skills.md` prints nothing.
2. The SKILL.md table has 9 rows, and their ids match the `LAW-*` ids in `src/observability/hard_law_monitor.py`.
3. Run any test that pins skill or skills.md text: grep tests/ for "observability/SKILL.md" and "skills.md".
4. REGISTRY regenerated if docs/ changed; `generate_registry --check` passes.

## Related Tickets
- TCK-20260805-OBSERVABILITY-SKILL (created the skill)
- TCK-20260716-PLACELEGAL-HARDLAW (7th law)
- TCK-20261112-KNOWLEDGE-STACK-PIN-BUMPS (the PR this rides)

## Related Docs
- docs/observability/hard_law_monitor.md §1

## Related Stored Artifacts

## Related Code Areas
- src/observability/hard_law_monitor.py (read only)

## Assumptions / Open Questions

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
