---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261113-PRE-PUSH-CHECKS-HAND-EDITED-PARITY-LEDGER-SHARDS
phase: done
date: 2026-11-13
tags: [delivery, process-improvement]
---

# TCK-20261113-PRE-PUSH-CHECKS-HAND-EDITED-PARITY-LEDGER-SHARDS

## Title
A hand-edited `docs/parity_ledger/*.yaml` shard that doesn't parse, or breaks the ledger rules, reaches CI with no local warning

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Finding by lead-planner-u24 (2026-11-12/13). On u24, rpg lanes A and B both edited docs/parity_ledger/*.yaml by hand instead of
using the mandated `tools/parity_ledger_writer.py` (owner #715 6525197149). Lane B's edit put an unescaped apostrophe inside a
single-quoted `support_boundary` (COMB-342), so `combat_movement.yaml` stopped parsing. #902 went red on 3 CI lanes and was fixed
by S7 6843557542. Scoped by agent-working-planner-u24 as option (A). Lead go: S4 dispatch, #715 6843638391. Option (B), a
blocking prek pre-commit entry owned by codebase, is skipped for now.

## Scope
1. **`tools/parity_ledger_writer.py --check <file>...`:** a small CLI that yaml.safe_loads each file and runs the existing
   `validate_entry()` on every entry. It prints one line per problem (`<file>: <id or line>: <reason>`) and exits non-zero on
   any problem. It writes nothing. It reuses the writer's own rules; no second copy of them.
2. **Pre-push advisory check G in `tools/delivery/pre_push_advisory_hook.py`:** for every docs/parity_ledger/*.yaml in
   `git diff --name-only origin/main...HEAD`, run the same check, in-process, through the writer's functions.
   - On any problem it warns with the file, the id and the reason, plus "edit ledger entries with
     tools/parity_ledger_writer.py".
   - Warn-only, the same as A-F. Any internal error says nothing. With no ledger files changed it does nothing.
3. **Tests, 4 in total:**
   - CLI on a shard with an unescaped apostrophe in a single-quoted value: non-zero, and the problem names the file.
   - CLI on a valid shard: zero.
   - Check G on a diff with a bad ledger shard: warns, naming the writer.
   - Check G with no ledger change, or a valid one: silent.

## Out of Scope
- Making seats use the writer. A valid hand edit can't be told apart from a writer write. The warning text names the writer.
- Option (B), the blocking prek pre-commit entry. That's codebase's `.pre-commit-config.yaml`; raise it if hand edits still
  reach CI after this.
- Pushes made outside Claude Code (the advisory is a Claude hook). Rebase and cherry-pick results are checked only at push or
  in CI.
- Any change to the ledger shards themselves.

## Acceptance Criteria
1. The 4 tests pass. Existing `tests/tools/test_parity_ledger_writer.py`, `test_parity_ledger_schema.py` and
   `test_delivery_pre_push_advisory.py` pass unchanged.
2. `python3 tools/parity_ledger_writer.py --check docs/parity_ledger/*.yaml` exits 0 on current main.
3. Check G stays inside the hook's 60 s budget: no model loads, and only the changed ledger files.
4. Scoped tests only.

## Where it rides
This is code, so it stands alone (#715 6793205403), or it rides any agent-working implementation PR that opens first.

## Related Tickets
- TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL (done; the writer and validate_entry)
- TCK-20261024-PRE-PUSH-WARNS-ON-A-STALE-DOCS-REGISTRY (check E, same pattern)
- TCK-20261112-REGISTRY-REGEN-SKIPPED-BY-A-STALE-HOOK-OR-AN-UNTRACKED-DOC (check F)

## Related Docs
- docs/parity_ledger/README.md
- docs/guides/delivery_process.md (pre-push advisory)

## Related Stored Artifacts
- none

## Related Code Areas
- tools/parity_ledger_writer.py (`validate_entry`), tools/delivery/pre_push_advisory_hook.py, tests/tools/

## Assumptions / Open Questions
- Simpler-fix check (6698958617): reusing validate_entry in a warn-only pre-push check is the cheapest local signal. Cost: about
  40 lines and 4 tests, with no measurement runs. It leaves out a hard block, and it doesn't make seats use the writer.

## Implementation Notes
- Scope change agreed with the planner (the ticket was written without sweeping main): validate_entry runs only on new or changed entries; legacy entries are exempt per its own docstring. A sweep of main found 1428 of 2307 entries failing validate_entry (1424 null test_path, 4 unparseable test_path), so a full sweep could never meet AC 2.
- `parity_ledger_writer.py --check <files>`: structural only (parses, list of mappings, string id; a parse error names its YAML line). `--check --base <ref> <files>` (opt-in, no default) also runs validate_entry on entries new or whose parsed dict differs from the same id at the ref. Writes nothing.
- Check G in `pre_push_advisory_hook.py`: reads each changed docs/parity_ledger/*.yaml from HEAD with git show, compares against origin/main, warn-only, silent on any error; the warning names tools/parity_ledger_writer.py.


## Test Summary
89 passed: the new tests/tools/test_parity_ledger_check.py (5 tests) plus the unchanged test_parity_ledger_writer.py, test_parity_ledger_schema.py and test_delivery_pre_push_advisory.py (-p no:randomly). `python3 tools/parity_ledger_writer.py --check docs/parity_ledger/*.yaml` exits 0 on main (57481677a).

## Files Changed
tools/parity_ledger_writer.py, tools/delivery/pre_push_advisory_hook.py, tests/tools/test_parity_ledger_check.py.

## Completion Summary
A hand-edited parity ledger shard that does not parse (the COMB-342 apostrophe case) now fails `--check` locally and warns at pre-push before CI. Option (B), a blocking prek entry, stays codebase's.
