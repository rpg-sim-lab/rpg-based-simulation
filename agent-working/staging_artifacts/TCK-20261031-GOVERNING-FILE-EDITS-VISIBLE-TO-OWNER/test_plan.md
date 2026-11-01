---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-GOVERNING-FILE-EDITS-VISIBLE-TO-OWNER
artifact_type: test_plan
tags: [governance, delivery, agent-monitoring]
---

# Test plan

No test has been run. The planner asks the lead for the slot (own allowance for this ticket).

## New tests (acceptance map)
- AC1 `tests/tools/test_delivery_pr_render.py`: section present with the touched governing paths when the diff has one (CLAUDE.md, a workflow, guard.py); absent when none; limit sentence present; `--check` passes with it present and absent; ticketless path.
- AC2 `tests/tools/test_session_guard.py`: Edit, Write and Bash on a governing path each write exactly one row to a tmp data dir and the call still exits 0 with no output; a failing writer (unwritable dir, patched `write_line` raising) leaves exit 0 and no output; unresolved caller still logs with seat `unresolved`; Bash fast path covers the new names.
- AC3 same file: existing allow-with-no-output cases unchanged (the current parametrized tests stay as-is); a non-governing edit and a read-only Bash mention write no row.
- AC4 pr_render test above asserts the sentence.
- AC5 `tests/tools/test_session_layer_measures.py`: attempts vs merged commits, unmatched path flagged, dark-family note, empty period.
- New `tests/tools/test_governing_paths.py`: `governing_paths_in` table (positives, negatives such as `tools/sessions/guard_x.py`, `docs/.github/workflows`-like lookalikes), `GOVERNING_FILES` subset of `GOVERNING_PATHS`.
- Existing, rerun unchanged: `test_session_classify.py`, `test_session_boundary.py`, `test_pr_body_lint.py`, `test_pr_body_lint_workflow_pinned.py`, `test_delivery_pr_status.py`.

## Slot request (for the planner to relay)
Set: `tests/tools/test_session_classify.py test_session_guard.py test_session_boundary.py test_session_layer_measures.py test_delivery_pr_render.py test_pr_body_lint.py test_pr_body_lint_workflow_pinned.py test_governing_paths.py`, plus `python3 -m tools.generate_registry --check`. Cores 4-5, systemd-run MemoryMax=1G, `-n 1`. Estimate 5-10 min, unmeasured (I have no timing for these files; will report the real figure). Needed twice at most: once after step 4 and once final. Full `tests/tools` is not requested unless the planner wants it before the push (needs MemAvailable >= 3.5 GB, detached, duration unknown to me).
Nothing runs on 4-5 until the lead says rpg's groups runs have ended.

## Amendments (planner review)
- Added to the slot set: `test_delivery_pr_status.py`, `tests/tools/test_agent_working_paths_guard*.py`, and every test file touched for the schema.md/validate/week_close checks. Final: full `tests/tools` + `tests/docs` once at the final SHA before the push ask (separate slot).
- New tests: `basis` path vs mention; `frontend/src/hooks/x.ts` negative; `.claude/hooks/`, `tools/hooks/`, `codebase/hooks/` positives; absolute path in a linked worktree resolves to repo-relative; path outside repo writes no row; row from text holds only the matched token; guard test file redirects data dir (autouse) and one test asserts the real week dir is untouched; Bash mention of guard.py alone gives identical (empty) output to today; session_authority.yaml in the list with action unchanged.
