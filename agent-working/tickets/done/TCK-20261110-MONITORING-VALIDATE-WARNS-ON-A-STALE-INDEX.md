---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261110-MONITORING-VALIDATE-WARNS-ON-A-STALE-INDEX
phase: done
date: 2026-11-10
tags: [agent-monitoring, data-quality]
---

# TCK-20261110-MONITORING-VALIDATE-WARNS-ON-A-STALE-INDEX

## Title
`make agent-monitoring-validate` validates a stale index without saying so

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Deep-retro finding by lead-planner-u24, drafted by agent-working-designer-u24 (draft item 2, main checkout
`.claude/handover/drafts/retro-readers-join-on-a-null-run-id-2026-11-10.md`). Owner go: #715 6764924407 (A).
`tools/agent-monitoring/validate.py` reads the index db (`open_index`) and never compares it with the JSONL shards. The
lead saw 2,596 runs in the index against 2,676 raw: 80 batch-shard runs went unvalidated with no warning.

## Scope
1. Before validating, compare the db's mtime with the newest `data/**/*.jsonl` mtime. If any shard is newer, print
   `WARNING: index older than <n> shard file(s); run make agent-monitoring-index` and carry on.
2. A `--rebuild` flag runs `build_index.py` first.

## Out of Scope
- Making the Make target depend on `agent-monitoring-index` (always rebuilds; the Makefile is lead-owned).
- Changing exit codes: the warning does not fail validation.

## Acceptance Criteria
1. An index older than a shard gets the warning with the shard count; a fresh index gets none.
2. `--rebuild` calls the builder (injected in the test).
3. Scoped tests only (the validate test file). Owner load rule: no pytest -n>1, no broad suites while lane C measures.

## Related Tickets
- TCK-20261110-RETRO-READERS-SELECT-TOOL-ROWS-BY-TS (same batch)

## Related Docs
- docs/agent-monitoring/README.md

## Related Stored Artifacts
- Designer draft (main checkout), item 2.

## Related Code Areas
- tools/agent-monitoring/validate.py, tools/agent-monitoring/build_index.py, tests/tools/

## Assumptions / Open Questions
- Simpler-fix check: a warning plus an opt-in flag is the cheaper of the two options; it leaves a stale run possible if the
  warning is ignored.

## Implementation Notes
validate.py: stale_shard_count() compares the db mtime with runs/events/tools shards (shared shard_paths resolver), warns on stderr with the count, and --rebuild runs build_index.py first (subprocess; validate.py is guarded against referencing RUNS_FILE). generate_retro._index_is_stale answers yes/no only, so the count is computed separately instead of importing generate_retro.

## Test Summary
3 new tests in tests/tools/test_validate_agent_monitoring.py (warning with count, fresh index silent, --rebuild calls builder); the file's 48 tests and test_build_index pass.

## Files Changed
tools/agent-monitoring/validate.py; tests/tools/test_validate_agent_monitoring.py

## Completion Summary