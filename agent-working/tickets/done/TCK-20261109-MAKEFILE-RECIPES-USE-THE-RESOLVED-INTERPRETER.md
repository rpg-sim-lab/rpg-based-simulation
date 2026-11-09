---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261109-MAKEFILE-RECIPES-USE-THE-RESOLVED-INTERPRETER
phase: done
date: 2026-11-09
tags: [ai, setup]
---

# TCK-20261109-MAKEFILE-RECIPES-USE-THE-RESOLVED-INTERPRETER

## Title
Makefile recipes run a bare `python3` instead of the resolved `$(PYTHON3)`, so targets fail outside an activated venv

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Owner repro on main 03ad89589: `make test-collect` fails with `No module named 'pydantic'` when the venv is not activated.
`Makefile:51` defines `PYTHON3` as the first interpreter that can import pydantic (.venv first), and 38 recipe lines use
it. 77 recipe lines (79 commands; 325 and 328 have two each) still call a bare `python3` from PATH, which is the system
interpreter outside the venv. `test` (:219) and `test-cov` (:225) also point at `tests_v2/` and `--cov=src_v2`, which don't
exist on main, so they are broken whatever the interpreter.

Owner decision #715 6736552379 (via lead-planner-u24, 2026-11-09): the Makefile routes to domain lead (seat lead-planner,
ubuntu, off; the lead domain has no implementer), and the owner gave the build to the u24 agent-working seat.
agent-working-planner-u24 files it; agent-working-implementer-u24 builds it. Path-reason `owner_directed`, citing
6736552379 in `--path-note`.

Draft: agent-working-designer-u24, main checkout
`.claude/handover/drafts/makefile-recipes-use-the-resolved-interpreter-2026-11-09.md` (read the 2026-11-09 addendum; it
holds the guard test in full).

## Scope
1. Every bare `python3` command on a recipe line becomes `$(PYTHON3)`. A leading-only sed
   (`sed -E 's/^(\t@?)python3 /\1$(PYTHON3) /'`) catches most of them; fix these by hand:
   - line 183, `SIM_OBS_MODE=DEBUG python3 ...` (env prefix);
   - the second `python3` after the pipe on 325 and 328 (mypy | mypy_baseline).
   `uv run python3` (134, 137) stays: uv picks its own environment. `PYTHON_KNOWLEDGE` targets stay as they are.
2. `test` and `test-cov`: repoint to `tests/` and `--cov=src`, both with `-m "not slow"`. Repoint, not delete:
   CONTRIBUTING.md:21/27 documents both (lead-domain call). Update the two target descriptions (drop "(V2)").
3. Guard test `tests/tools/test_makefile_uses_resolved_python.py`, as written in the draft addendum: a real-Makefile check
   that fails on any tab-led recipe line running a bare `python3`, with a message naming `$(PYTHON3)`, plus a fixture test of
   each bare and allowed form.

## Out of Scope
- How `PYTHON3` is resolved (`Makefile:51`).
- CI changes. CI activates its own interpreter, which is why this only shows on hosts.
- CONTRIBUTING.md (the targets keep their names, so it stays accurate).
- `docs/plans/test_architecture/reference/current_test_system_overview.md:57` notes the broken `test-cov`; that's testing's
  doc and is not edited here. Mention the fix to testing-planner as an fyi.

## Acceptance Criteria
1. The guard test fails on main (77 lines) and passes after the change; its fixture test passes.
2. `env -i PATH=/usr/bin:/bin make test-collect` collects (no venv on PATH).
3. `make -n` on test-quick, test, test-cov, typecheck-py, docs-registry and monitoring-anomaly-validate prints the `.venv` interpreter
   on every python command (both sides of the typecheck pipe).
4. `pytest tests/tools/test_makefile_uses_resolved_python.py tests/tools/test_makefile_interpreter_selection.py
   tests/tools/test_dashboard_makefile_targets.py -q` is green.
5. Closed by hand-orchestration: `record_hand_orchestrated_closure.py --path-reason owner_directed --path-note "#715
   6736552379 ..."`, `done_checker_static.py --ticket-id`, mechanism-registry advisory; stage REGISTRY.yaml and the
   monitoring shards.

## Related Tickets
- TCK-20260914-VENV-NAMING-CI-PARITY-SWAP (done; defined `PYTHON3`'s venv order)
- TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT (done; find_spec probe; `test_makefile_interpreter_selection.py`)
- TCK-20261012-HOST-PATH-LITERALS-MAKEFILE-AND-MCP-LAUNCHERS (done)
- TCK-20261018-MAKE-AGENT-MONITORING-INDEX-WORKS-WITHOUT-LOCAL-VENV (done; same fix for one target)
- TCK-20261027-SESSION-ROUTE-OTHERS-OWNS-BEAT-CATCHALL-ROUTE (parked filing on main; not part of this work)

## Related Docs
- CONTRIBUTING.md (lines 21, 27)
- docs/guidelines/agent_working_environment.md (the two venvs)

## Related Stored Artifacts
- Designer draft (main checkout): `.claude/handover/drafts/makefile-recipes-use-the-resolved-interpreter-2026-11-09.md`

## Related Code Areas
- Makefile (domain lead; build handed to agent-working by #715 6736552379)
- tests/tools/ (agent-working)

## Assumptions / Open Questions
- Simpler-fix check (#715 6697776913): the mechanical swap is the simplest fix that covers every target. Fixing only
  `test-collect` would leave 76 other lines failing the same way. Cost is one Makefile edit and one millisecond test; no
  measurement runs.
- If `PYTHON3` resolves empty (no candidate imports pydantic), the swapped lines fail with `-m: not found`, where a bare
  `python3` would have run without pydantic. That's the same behaviour the 38 existing lines already have, and is accepted.

## Implementation Notes
Perl swap of every tab-led bare `python3` command word to `$(PYTHON3)` (79 commands, incl. line 183 env prefix and both sides of the mypy pipes); `uv run python3` left. `test`/`test-cov` repointed to tests/ and --cov=src with -m "not slow". Guard test copied from the designer draft.

## Test Summary
The three AC4 files: 15 passed. `env -i PATH=/usr/bin:/bin make test-collect`: 21595 collected (ran once, before the memory note arrived). `make -n` on test-quick, test, test-cov, typecheck-py, docs-registry, monitoring-anomaly-validate shows the .venv interpreter on every python command.

## Files Changed
Makefile; tests/tools/test_makefile_uses_resolved_python.py

## Completion Summary
Makefile recipes now run through the resolved interpreter; guard test prevents regression.
