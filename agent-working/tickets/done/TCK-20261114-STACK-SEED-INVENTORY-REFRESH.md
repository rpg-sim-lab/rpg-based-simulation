---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261114-STACK-SEED-INVENTORY-REFRESH
phase: done
date: 2026-11-14
tags: [governance]
---

# TCK-20261114-STACK-SEED-INVENTORY-REFRESH

## Title
The tech-stack seed's inventory is refreshed to current main

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`agent-working/lead/stack_seed_review.md`'s "Inventory seed" was dated `main` 9a9058808 (2026-10-11). Its containers line (redis floating, prometheus v2.50.0, grafana 10.3.3, loki and promtail 3.0.0) and MCP line were long out of date, and u24's #903 had added one OpenTelemetry line to it (reviewed after the fact; lead-planner-u24 agreed the lead refreshes this file).

## Scope
Rewrite only the "Inventory seed" section from current `main` 96db1f5e8: Python code-health pins, the knowledge stack, OpenTelemetry, the three npm projects, the compose images, the MCP servers and the ubuntu host runtime. The dated findings table stays as a record.

## Out of Scope
Re-checking the 2026-10-11 findings table; creating `registries/tech_stack.yaml`.

## Acceptance Criteria
1. Every version in the section matches `pyproject.toml`, `requirements-knowledge.txt`, the three `package.json` files, `compose.yaml` and `.mcp.json` on `main` 96db1f5e8.
2. Frontmatter valid.

## Related Tickets
- TCK-20261009-EPIC-SESSION-LEAD-PLANNER (E6 seed review)

## Related Docs
- `agent-working/lead/stack_seed_review.md`

## Related Stored Artifacts
None.

## Related Code Areas
None.

## Assumptions / Open Questions
None.

## Implementation Notes
Values read with `git show origin/main:<file>`; the Dependabot coverage line was checked against `.github/dependabot.yml` (it watches `frontend/` and `website/`, not `dashboard-frontend/`).

## Test Summary
Frontmatter validated.

## Files Changed
- `agent-working/lead/stack_seed_review.md`

## Completion Summary
The inventory now reflects main 96db1f5e8. No code changed.
