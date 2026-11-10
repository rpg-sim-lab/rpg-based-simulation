---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261110-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-NON-TOOL-SHARDS
phase: done
date: 2026-11-10
tags: [agent-monitoring, data-quality]
---

# TCK-20261110-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-NON-TOOL-SHARDS

## Title
Week close sweeps the main checkout's tool rows but not its manual_actions, reset_boundary or governing_edits rows, so nothing carries them

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Deep-retro finding by lead-planner-u24, narrowed by agent-working-designer-u24 (draft item 3, main checkout
`.claude/handover/drafts/retro-readers-join-on-a-null-run-id-2026-11-10.md`). Owner go: #715 6764924407 (A).
`main.tools.jsonl` is already swept into the canonical `tools.jsonl` by a week close run from a worktree on the same host
(TCK-20261021-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-TOOL-ROWS). `manual_actions.jsonl`, `reset_boundary.jsonl` and
`governing_edits.jsonl` written in the main checkout are not swept; they sit untracked or modified there.

## Scope
1. Extend the existing sweep in `tools/agent-monitoring/week_close.py` to those three append-only shard kinds, listed in one
   tuple, with the same full-row identity (de-dup) and read-only-source rules as the tool sweep.
2. Update the README "Main-checkout tool rows" passage to name the added kinds.

## Out of Scope
- The other host's main checkout (existing limit: close per host).
- Any change to how those shards are written.

## Acceptance Criteria
1. One test per added kind: swept once, de-duplicated against rows already on the branch, main-checkout file untouched.
2. The existing tool-row sweep tests pass unchanged.
3. Scoped tests only (week_close test file). Owner load rule: no pytest -n>1, no broad suites while lane C measures.

## Related Tickets
- TCK-20261021-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-TOOL-ROWS (done; the sweep this extends)
- TCK-20261110-RETRO-READERS-SELECT-TOOL-ROWS-BY-TS (same batch)

## Related Docs
- docs/agent-monitoring/README.md

## Related Stored Artifacts
- Designer draft (main checkout), item 3.

## Related Code Areas
- tools/agent-monitoring/week_close.py, tests/tools/

## Assumptions / Open Questions
- Simpler-fix check: reusing the existing sweep with a wider tuple is the smallest change; leaves out the other host.

## Implementation Notes
week_close.py: _sweep_file() factored out; sweep_main_checkout_append_only() sweeps manual_actions, reset_boundary and governing_edits (tuple MAIN_CHECKOUT_APPEND_ONLY_KINDS) with the tool sweep's rules; close_week result and CLI print one line per kind; README passage updated.

## Test Summary
5 new tests in tests/tools/test_week_close_main_checkout_sweep.py (per kind: swept once, deduped, main file untouched; absent kind skipped); 13 sweep tests plus test_week_close pass.

## Files Changed
tools/agent-monitoring/week_close.py; tests/tools/test_week_close_main_checkout_sweep.py; docs/agent-monitoring/README.md

## Completion Summary