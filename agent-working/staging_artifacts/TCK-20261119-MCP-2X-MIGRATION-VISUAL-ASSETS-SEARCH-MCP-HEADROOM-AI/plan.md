---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261119-MCP-2X-MIGRATION-VISUAL-ASSETS-SEARCH-MCP-HEADROOM-AI
artifact_type: plan
tags: [mcp]
---

# plan — TCK-20261119-MCP-2X-MIGRATION-VISUAL-ASSETS-SEARCH-MCP-HEADROOM-AI

Ticket is BLOCKED and parked (planner, 2026-11-19): it waits for the coin fix and #965 to merge, and for a licence-holder `make visual-assets-aseprite-local` run. Do not split it: the search_mcp/requirements side cannot land alone.
When unparked: (1) the app/lowlevel/store_readonly/search_mcp edits in the WIP commit; (2) exact `pyproject.toml` (both mcp lines) and `uv.lock` diff to lead-planner BEFORE committing; (3) `requirements-knowledge.txt` pin and its crash comment in one commit; (4) remove the Dependabot mcp-major ignore entry in `.github/dependabot.yml` that the planner added (5 lines); (5) licence holder re-runs the local proof; (6) measure the unmeasured rows of investigation.md; (7) the PR body states that asset-planner's co-owner confirmation is pending.
