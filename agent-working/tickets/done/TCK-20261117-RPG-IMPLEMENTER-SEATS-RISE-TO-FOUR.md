---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261117-RPG-IMPLEMENTER-SEATS-RISE-TO-FOUR
phase: done
date: 2026-11-17
tags: []
---

# TCK-20261117-RPG-IMPLEMENTER-SEATS-RISE-TO-FOUR

## Title
The rpg-implementer role allows four sessions, so the owner's fourth RPG lane (rpg-implementer-4) can launch

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
The owner approved a fourth RPG implementer for M1 Phase 1, run 2's segment (#715 6937049127), after closing the 7 idle non-RPG seats on u24. The launcher refuses a fourth rpg-implementer session while `registries/session_roles.yaml` says `max_sessions: 3`. The main checkout carried the edit to 4 as a local, uncommitted change (lead-planner-u24); this ticket makes it a committed change.

## Scope
- `registries/session_roles.yaml` rpg-implementer placement: `max_sessions: 3` becomes `4`.

## Out of Scope
- Refreshing the shared implementer home `.claude/worktrees/rpg` to main. That is an owner ask, made when all 4 implementers are between tasks.
- Any other role's limit.

## Acceptance Criteria
- The registry says `max_sessions: 4` for rpg-implementer.
- `python3 -m tools.sessions.generate_agents --check` reports 0 drift.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC

## Related Docs
- docs/guidelines/session_roles/ (role registry)

## Related Stored Artifacts
- none

## Related Code Areas
- registries/session_roles.yaml

## Assumptions / Open Questions
- Memory: the 7 closed seats freed ~3.7 GB available, and one more seat is ~300-470 MB. Tests stay one at a time at ≥2.5 GB free.

## Implementation Notes
- A one-line edit, matching the main checkout's local edit.

## Test Summary
- `python3 -m tools.sessions.generate_agents --check`: OK, 0 drift findings.

## Files Changed
- registries/session_roles.yaml

## Completion Summary
rpg-implementer's max_sessions is 4. The generated cards don't change (0 drift). Owner approval #715 6937049127.
