---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261119-MCP-2X-MIGRATION-VISUAL-ASSETS-SEARCH-MCP-HEADROOM-AI
phase: open
date: 2026-11-19
tags: [mcp]
---

# TCK-20261119-MCP-2X-MIGRATION-VISUAL-ASSETS-SEARCH-MCP-HEADROOM-AI

## Title
Migrate to mcp 2.x: visual_assets drawing server, tools/search_mcp and headroom-ai

## Status
BLOCKED

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Dependabot #813 (uv-major) was closed unmerged on 2026-11-19 by the owner. Its mcp 1.30 -> 2.3 bump breaks `visual_assets/drawing/server/app.py:5` (`from mcp.server.fastmcp import FastMCP`; FastMCP was renamed in 2.x), so every `tests/visual_assets/drawing` stdio test fails (ModuleNotFoundError or "MCPError Connection closed"). `tools/search_mcp.py` and `visual_assets/drawing/server/highlevel_tools.py` also import mcp. Dependabot widened `mcp>=1.30.0,<2` to `<3` and its find-and-replace rewrote the `requirements-knowledge.txt` comment about the mcp==1.30.0 crash so it names the wrong version. headroom-ai is held because it needs mcp 2.x. Precedent: the 2026-10-14 close of the earlier mcp 2.x bump (TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR); the knowledge stack is bumped by hand (#882).

## Scope
- Port `visual_assets/drawing/server/{app,highlevel_tools}.py` and `tools/search_mcp.py` to the mcp 2.x API; the search_docs MCP must keep starting in a worktree.
- Bump `mcp` in `pyproject.toml` (both lines) and `requirements-knowledge.txt` together, refresh `uv.lock`, fix the crash comment's version.
- Decide whether headroom-ai can be unheld once mcp 2.x is in.
- Propose a Dependabot ignore for mcp majors until this lands (decision for lead-planner).

## Out of Scope
- sentence-transformers, duckdb, pyarrow and websockets bumps (separate ticket for the CI cause).
- Changing the tool surface of any MCP server.

## Acceptance Criteria
1. `tests/visual_assets/drawing` stdio tests pass on mcp 2.x.
2. search_docs MCP starts and answers in a worktree on mcp 2.x.
3. One mcp version is named consistently in `pyproject.toml`, `requirements-knowledge.txt` and its comment.
4. CO-OWNER: asset-planner is named co-owner for `visual_assets/**`; it has no live session on this host, so this ticket carries the co-ownership and the asset-side change needs its confirmation before merge.
5. Scoped tests only; no heavy runs without a lead-planner go.

## Related Tickets
- TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR (the 2026-10-14 close of the mcp 2.x and sentence-transformers 6 bumps)

## Related Docs
- `requirements-knowledge.txt` (mcp==1.30.0 pin and its crash comment)

## Related Stored Artifacts
- none yet

## Related Code Areas
- `visual_assets/drawing/server/app.py`, `visual_assets/drawing/server/highlevel_tools.py`
- `tools/search_mcp.py`
- `pyproject.toml`, `uv.lock`, `requirements-knowledge.txt`
- `tests/visual_assets/drawing/`

## Assumptions / Open Questions
- Whether the mcp 2.x migration is mechanical (rename) or changes the server lifecycle: unmeasured.
- Whether headroom-ai has a release that supports mcp 2.x: unchecked.

## Durable state, lifecycle and clocks
N/A: no src change; dependency, tooling and CI work only.

## Implementation Notes
BLOCKED and parked (planner decision 2026-11-19): the ticket is not split. It waits for the coin fix and #965 to merge, and for a licence-holder `make visual-assets-aseprite-local` run that rewrites `docs/assets/aseprite_local_proof.json` (ADR D10, never a hand edit). The measurement is in `agent-working/staging_artifacts/TCK-20261119-MCP-2X-MIGRATION-VISUAL-ASSETS-SEARCH-MCP-HEADROOM-AI/investigation.md` (each row marked measured or unmeasured). Summary: a rename-sized port (app.py 2 lines, lowlevel_tools.py 1 import, search_mcp.py 2 lines) plus one behaviour change (`ToolError` replaces `ValueError`, flipping two tests) and about 32 snake_case test-client uses in 4 files; 408 passed on mcp 2.3 in the scoped set. Trial edits are in a local WIP commit on branch agent-working-mcp2-migration, not pushed. The migration PR must also remove the Dependabot mcp-major ignore entry the planner added to `.github/dependabot.yml`.
Filed by agent-working-planner on lead-planner's relay (owner-directed via lead-planner-u24, #715 7002590099). `pyproject.toml` and `uv.lock` are lead-owned (tech-stack registry): bring the exact diff to lead-planner before it is committed.

## Test Summary

## Files Changed

## Completion Summary
