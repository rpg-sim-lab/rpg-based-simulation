---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261119-MCP-2X-MIGRATION-VISUAL-ASSETS-SEARCH-MCP-HEADROOM-AI
artifact_type: investigation
tags: [mcp]
---

# investigation — TCK-20261119-MCP-2X-MIGRATION-VISUAL-ASSETS-SEARCH-MCP-HEADROOM-AI

Measured 2026-11-19 on a trial port (WIP commit on branch agent-working-mcp2-migration, local, not pushed) against mcp 2.3.0 in a venv layered over the main env (`/data/vboxuser/aw-venv-mcp2`). The stdio tests spawn a subprocess that ignores PYTHONPATH, so a PYTHONPATH overlay is not a valid measurement for them (first attempt gave 38 false failures from a 1.x server with a 2.x client).

| item | status | finding |
|---|---|---|
| Server lifecycle | measured | unchanged: `MCPServer(...).run()` over stdio, same shape as FastMCP |
| Rename in `visual_assets/drawing/server/app.py` | measured | 2 lines: import `mcp.server.mcpserver.MCPServer`, constructor |
| `visual_assets/drawing/server/lowlevel_tools.py` | measured | 1 import move: `Image` now at `mcp.server.mcpserver.utilities.types` |
| `tools/search_mcp.py` | measured | 2 lines: import and constructor |
| Error contract (not a rename) | measured | 2.x wraps any exception except `ToolError`/`ResourceError`/`MCPError` as `UnexpectedToolError` with the message hidden ("Error executing tool X"). `app.py call()` and `store_readonly_tools.py _safe()` raised `ValueError(str(exc))`; both now raise `mcp.server.mcpserver.exceptions.ToolError`. Tests flipped: `test_tool_failures_are_plain_value_errors_...` (renamed to `..._are_tool_errors_...`, now expects ToolError) and `tests/visual_assets/store/unit/test_lock.py::test_the_mcp_submit_takes_the_lock` |
| Test client attributes | measured | camelCase to snake_case: `.isError`, `.inputSchema`, `.mimeType` -> `.is_error`, `.input_schema`, `.mime_type`; about 32 uses in 4 test files (test_server_stdio x2, test_store_root_stdio, test_store_tools_stdio, stdio_support) |
| `test_compose.py` | measured | `FastMCP("t")` -> `MCPServer("t")`; the private `srv._tool_manager._tools` still works on 2.3 |
| Result | measured | `tests/visual_assets/drawing` + `tests/tools/test_search_mcp.py`: 408 passed. Full `tests/visual_assets` + search_mcp: 2602 passed, 2 failed at the last full run (lock test, fixed since and passing alone: 38 passed; and the proof gate below). The full run was not repeated after the lock-test fix |
| Aseprite proof gate | measured, BLOCKER | `tests/visual_assets/test_aseprite_local_proof.py::test_the_guarded_files_still_match_the_committed_record` fails once `app.py`, `lowlevel_tools.py`, `store_readonly_tools.py` or the two edited stdio test files change. Only a real `make visual-assets-aseprite-local` run by the licence holder (ADR D10) rewrites `docs/assets/aseprite_local_proof.json`; never a hand edit |
| CI coupling | measured by reading | `tools/search_mcp.py` runs under the main env's mcp 1.x in CI while `pyproject.toml` stays `<2`; a 2.x-only port breaks CI, so the bump and the asset port land together |
| `.venv-knowledge` rebuild on 2.x, search_docs starting in a worktree on 2.x | unmeasured | needs `requirements-knowledge.txt` mcp pin and crash comment changed together |
| headroom-ai needing mcp 2.x | unmeasured | 0.43.1 needs `mcp>=2.2.0,<3` per the `requirements-knowledge.txt` comment (not re-verified) |
| `pyproject.toml` / `uv.lock` diff | not made | lead-planner gets the exact diff first |
