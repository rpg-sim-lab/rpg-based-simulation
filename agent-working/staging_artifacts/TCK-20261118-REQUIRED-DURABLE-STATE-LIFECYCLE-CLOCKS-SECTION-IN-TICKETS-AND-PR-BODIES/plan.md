---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261118-REQUIRED-DURABLE-STATE-LIFECYCLE-CLOCKS-SECTION-IN-TICKETS-AND-PR-BODIES
artifact_type: plan
tags: [skills, process-improvement]
---

# Plan

Scope items 1-6 of the ticket, minus the three steps the dispatch stopped (CLAUDE.md edit, O6 candidates 1/2/4, O6 time scan).

1. `tools/ticket_field_values.py`: `LIFECYCLE_SECTION`, `LIFECYCLE_SECTION_REQUIRED_FROM = 2026-11-19` (day after the landing day, so tickets already filed on 2026-11-18 stay grandfathered), `check_lifecycle_section(path)` (presence only; `N/A:` needs a non-empty reason).
2. `tools/gate_checks/done_checker_static.py`: adapter `check_ticket_lifecycle_section`, new blocking condition `ticket_lifecycle_section` (9th Part A check).
3. PR body: line `- Durable state, lifecycle and clocks:` in `.github/pull_request_template.md` and `pr_template_spec.json`; `pr_render.py` renders one line per ticket, `N/A: no src change` when the diff touches no `src/`; `pr_body_lint.py` fails a template-shaped body (has `## Tickets`) whose Verification lacks a non-empty line.
4. O5: advisory paragraph in `docs/guidelines/session_roles/functions/planner.md` outside the injected Card (planner cards are at the token budget).
5. Template sources: `.claude/agents/ticket-scoper.md` (router: agent-working). `.agents/rules/ticket.md`, `.claude/workflows/create-tickets.js`, `.claude/skills/create-tickets/SKILL.md` are router-unowned: filed as an ask with the exact text.
6. Tests: `tests/tools/test_lifecycle_section.py`; done-checker count 8 to 9. Fill-rate script `tools/gate_checks/lifecycle_section_fill_rate.py`, first output recorded in the ticket.
7. Docs: `docs/guides/delivery_process.md`.
