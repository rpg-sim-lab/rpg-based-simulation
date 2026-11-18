---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261114-ROLE-CARDS-CITE-AMENDED-DECISIONS
phase: done
date: 2026-11-14
tags: [ai, governance, documentation]
---

# TCK-20261114-ROLE-CARDS-CITE-AMENDED-DECISIONS

## Title
The architecture and platform role cards cite decisions that the distributed-workers ADR amended

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
Finding from lead-planner (2026-11-14; the owner asked for it). On origin/main 4584e9145:
- `docs/guidelines/session_roles/domains/architecture.md` `## Card` says "Recorded decisions bind you: system_overview 'deliberately not distributed', the devops ADR and amendment, kernel_concurrency_design_philosophy, PERF-D1/D2". `docs/architecture/distributed_workers_adr.md` (accepted #715 6777076537, 2026-11-11) amends exactly that system_overview section and the devops amendment's "What stays from the ADR". `docs/architecture/next_generation_engine_adr.md` (accepted #715 6742854335) is not listed.
- `docs/guidelines/session_roles/domains/platform.md` `## Card` says "Engine stays one process". The same ADR adds an opt-in distributed-workers mode, and the owner said it may become the main mode (#715 6776564953).

## Scope
- Rewrite the decision list in the architecture card: system_overview as amended by distributed_workers_adr, the devops ADR and amendment (as amended), next_generation_engine_adr, kernel_concurrency_design_philosophy, PERF-D1/D2.
- Rewrite the platform card's "Engine stays one process" so it says one process by default plus the opt-in distributed-workers mode under distributed_workers_adr.
- Wording confirmed by architecture-planner (architecture card) and platform-planner (platform card) before commit.
- Regenerate `.claude/agents/` with `tools/sessions/generate_agents.py`; `--check` clean; card token tests pass.

## Out of Scope
- The citation index and check (TCK-20261114-ROLE-CARD-DECISION-CITATION-INDEX).
- asset ("live-app activation parked until the RPG core lands") and perf ("M0-M6") card lines: their owners confirm; a change rides here only if they report one.
- Relaunching seats (owner/lead action after merge).

## Acceptance Criteria
1. Neither card states a decision that a later accepted ADR amended without naming the amendment.
2. The architecture card lists next_generation_engine_adr and distributed_workers_adr.
3. `python3 tools/sessions/generate_agents.py --check` is clean and the session-card tests pass.
4. architecture-planner and platform-planner confirmed the wording (cited in Implementation Notes).

Owner approval to file and dispatch: #715 6873240715 (2026-11-14, via lead-planner). #1 dispatches once the wording is confirmed; #2 after agent-working-designer reviews the design.

## Related Tickets
- TCK-20261114-ROLE-CARD-DECISION-CITATION-INDEX (process fix)
- TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT

## Related Docs
- docs/architecture/distributed_workers_adr.md
- docs/architecture/next_generation_engine_adr.md
- docs/architecture/system_overview.md
- docs/guidelines/session_roles/domains/{architecture,platform}.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/sessions/generate_agents.py, .claude/agents/session-{architecture,platform}-*.md

## Assumptions / Open Questions
- After merge, the architecture and platform seats on both hosts see the change only at relaunch or /clear (lead to arrange).

## Implementation Notes
Agreed wording (2026-11-14, cross-session):
- architecture.md, replaces the "Recorded decisions bind you" sentence (architecture-planner OK; it checked that distributed_workers_adr section 5.2 marks the devops amendment applied):
  Recorded decisions bind you: system_overview ("deliberately not distributed", as amended by distributed_workers_adr), the devops ADR and amendment (also amended there), next_generation_engine_adr, kernel_concurrency_design_philosophy, PERF-D1/D2.

- platform.md, replaces "Engine stays one process;" (platform-planner OK; "follows" does not claim the mode is implemented):
  The engine runs as one process by default; the opt-in distributed-workers mode follows docs/architecture/distributed_workers_adr.md;
Applied as agreed; the two sentences are the only text edits (architecture-planner and platform-planner confirmed the wording, 2026-11-14, cross-session). Dispatch: agent-working-planner, owner approval #715 6873240715, claim 634#6873246700.

## Test Summary

`python3 -m tools.sessions.generate_agents --check`: OK, 0 drift. `tests/tools/test_session_cards.py`, `test_session_agent_generator.py`, `test_session_architecture_domain.py`, `test_session_platform_domain.py`, `test_session_u24_twins.py`, `test_session_route.py`, `test_session_roster.py`, `test_session_launch.py`, plus paths-guard and ci-workflow coverage: 293 passed. No test pins either sentence (grep of tests/ and tools/ for "Engine stays one process", "deliberately not distributed" and "Recorded decisions bind you" is empty). The old wording remains only in two closed tickets (TCK-20261013-PLATFORM-DOMAIN-SEATS, TCK-20261022-ARCHITECTURE-PLANNER-U24-SEAT), which are history.

## Files Changed

- docs/guidelines/session_roles/domains/architecture.md
- docs/guidelines/session_roles/domains/platform.md
- .claude/agents/session-architecture-{planner,implementer}{,-u24}.md (regenerated, 4 files)
- .claude/agents/session-platform-{planner,implementer}{,-u24}.md (regenerated, 4 files)

## Completion Summary

The architecture card now lists system_overview as amended by distributed_workers_adr, the devops ADR and amendment (also amended there) and next_generation_engine_adr; the platform card says the engine runs as one process by default and the opt-in distributed-workers mode follows distributed_workers_adr. Seats pick the change up only at relaunch or /clear (lead arranges). Asset and perf card lines were not changed: their owners reported no change.
