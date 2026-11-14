---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261112-OBSERVABILITY-SKILL-HARD-LAW-COUNT
phase: done
date: 2026-11-12
tags: [skills, observability]
---

# TCK-20261112-OBSERVABILITY-SKILL-HARD-LAW-COUNT

## Title
The observability skill and the skills index name all nine HardLawMonitor laws, not seven

## Status
DONE

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

`.claude/skills/observability/SKILL.md`: heading 7 to 9 laws; `LAW-POSITION-IN-WORLD` row inserted after `LAW-POSITION-FINITE` and `LAW-LODGER-INDOORS` row appended after `LAW-SPAWN-OCCUPANCY`, both worded from `docs/observability/hard_law_monitor.md` §1 (unchanged since 4eaab4d8b); "other six" became "other eight" and "all seven" became "all nine". The line "except the last, which is a one-time full scan" became "except `LAW-SPAWN-OCCUPANCY`, which is a one-time full scan", because the appended row made "the last" wrong. `docs/ai/skills.md:227`: 7 laws to 9 laws. `.agents/skills/observability/SKILL.md` (not in the ticket, unowned in the manifest): body synced from the `.claude` copy, because `tests/tools/test_observability_skill_content.py::test_agents_mirror_body_matches_claude_source` pins the two bodies as equal; the mirror's body had matched the old source exactly.

## Test Summary

`git grep -nE "7 (hard )?laws|seven laws|other six" -- .claude/skills/observability docs/ai/skills.md` prints nothing. The table has 9 `LAW-*` rows and their ids equal the 9 ids in `src/observability/hard_law_monitor.py`. `tests/tools/test_observability_skill_content.py`: 8 passed (the mirror test failed before the mirror was synced). `generate_registry --check`: in sync.

## Files Changed

- .claude/skills/observability/SKILL.md
- .agents/skills/observability/SKILL.md (mirror body, pinned by test)
- docs/ai/skills.md

## Completion Summary

The observability skill and the skills index now name all nine HardLawMonitor laws. Rode the pin-bump PR under the ride-along rule (#715 6793205403).
