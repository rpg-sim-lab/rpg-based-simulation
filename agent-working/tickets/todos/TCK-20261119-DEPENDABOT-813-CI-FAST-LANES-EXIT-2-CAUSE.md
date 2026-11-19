---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261119-DEPENDABOT-813-CI-FAST-LANES-EXIT-2-CAUSE
phase: open
date: 2026-11-19
tags: [mcp]
---

# TCK-20261119-DEPENDABOT-813-CI-FAST-LANES-EXIT-2-CAUSE

## Title
Find the cause of the Migration lanes job "Fast lanes" exit 2 on the closed Dependabot #813 (duckdb, pyarrow, websockets)

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
On closed Dependabot #813 the Migration lanes job's "Fast lanes" step exited 2 and its logs were unavailable. Known suspects, no cause claimed: duckdb 1.5 -> 2.0, pyarrow 24 -> 26. Other bumps in #813: sentence-transformers 5.6 -> 6.2, websockets 16 -> 17. The mcp break is tracked in TCK-20261119-MCP-2X-MIGRATION-VISUAL-ASSETS-SEARCH-MCP-HEADROOM-AI.

## Scope
- Reproduce the Fast lanes step with each of duckdb 2.0, pyarrow 26 and websockets 17 alone (scoped, no heavy run without a go), and record which one fails, or that none does. A probe needs a positive control (the known-bad mcp 2.3 case).
- Report findings; any pin or ignore change goes to lead-planner as an exact diff first.

## Out of Scope
- Merging any bump; the mcp migration.

## Acceptance Criteria
1. The failing dependency is named with the command and output that show it, or the report says no single bump reproduces it.
2. Each of the three bumps has its own ran/passed/failed line.

## Related Tickets
- TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR (the 2026-10-14 close of the mcp 2.x and sentence-transformers 6 bumps)

## Related Docs
- `requirements-knowledge.txt` (mcp==1.30.0 pin and its crash comment)

## Related Stored Artifacts
- none yet

## Related Code Areas
- the Migration lanes CI job (`.github/workflows/`)
- `pyproject.toml`, `uv.lock`

## Assumptions / Open Questions
- #813 logs are unavailable; the check may need a fresh branch to reproduce.

## Durable state, lifecycle and clocks
N/A: no src change; dependency, tooling and CI work only.

## Implementation Notes
Filed by agent-working-planner on lead-planner's relay (owner-directed via lead-planner-u24, #715 7002590099). `pyproject.toml` and `uv.lock` are lead-owned (tech-stack registry): bring the exact diff to lead-planner before it is committed.

## Test Summary

## Files Changed

## Completion Summary
