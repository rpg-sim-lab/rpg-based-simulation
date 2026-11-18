---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261118-REQUIRED-DURABLE-STATE-LIFECYCLE-CLOCKS-SECTION-IN-TICKETS-AND-PR-BODIES
artifact_type: test_plan
tags: [skills, process-improvement]
---

# Test plan

Scoped, no heavy runs: `tests/tools/test_lifecycle_section.py` (new: absent, empty, `N/A` with and without reason, grandfathered, no date, corpus guard over existing tickets, done-checker adapter and wiring, CLI, renderer with and without src change, ticketless body, lint pass/fail/skip/placeholder/CLI, raw template fails, fill-rate), plus the existing suites for the touched tools: `test_done_checker_static.py`, `test_delivery_pr_render.py`, `test_pr_body_lint.py`, `test_pr_body_lint_workflow_pinned.py`, `test_ticket_field_values.py`, `test_session_cards.py`, `test_session_agent_generator.py`, `test_session_card_citations.py`, `test_ci_workflow_test_coverage.py`, `tests/integrity/test_no_duplicate_content_blocks.py`, `tests/tools/test_generate_registry.py`.
