---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261118-REQUIRED-DURABLE-STATE-LIFECYCLE-CLOCKS-SECTION-IN-TICKETS-AND-PR-BODIES
artifact_type: investigation
tags: [skills, process-improvement]
---

# Investigation

- Router (`python3 -m tools.sessions.route`): owned by agent-working: `.claude/agents/ticket-scoper.md`, `docs/guidelines/session_roles/`, `tools/gate_checks/`, `tools/delivery/`. Unowned: `.agents/rules/ticket.md`, `.claude/workflows/create-tickets.js`, `.claude/skills/create-tickets/SKILL.md`, `tools/ticket_field_values.py`, `.github/pull_request_template.md`. The last two are named by the ticket's Related Code Areas and the dispatch, so they were changed; the first three are an ask.
- `check_ticket_field_values` returns one combined Tier/Priority/Disposition item; adding the lifecycle check as its own condition keeps its evidence readable. Precedent for raising the Part A count: tests/tools/test_done_checker_static.py (5 to 6 to 7 to 8).
- A PR-body line nested under `Known gaps`-style bullets collided with `_gap_lines` in the renderer tests (`  - TCK-...`); the line is one `- Durable state, lifecycle and clocks: <ticket>: <text>` per ticket instead.
- Planner cards: `agent-working-planner-u24` is 2 tokens under `CARD_BUDGET_TOKENS`; a one-clause card addition (7 to 16 tokens) fails `test_session_cards.py`, so the O5 line is outside the Card.
- `pr_body_lint.py` runs in CI with only that file checked out (stdlib only), so the lifecycle rule lives in it; `pr_render.py` imports `LIFECYCLE_LINE` from it, one definition.
- Dependabot and other bodies have no `## Tickets` heading; the lint skips them.
