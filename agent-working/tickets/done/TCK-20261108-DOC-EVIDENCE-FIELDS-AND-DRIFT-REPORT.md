---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT
phase: done
date: 2026-11-08
tags: [ai, documentation, governance, frontmatter, agent-monitoring]
---

# TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT

## Title
Behaviour docs can carry evidence and a verification baseline, and an advisory drift report says which ones need re-verifying.

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Batch C, plus E2 and Q5 (plan origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR), P1, P5 "When code is read" and "Critical invariants", acceptance criteria 2 and 3, owner question Q5). Owner approval #715 6720445592 ("approve full plan staged, J pilot only, yes to all three"); lead-planner finding 2026-11-08; owner dispatch of PR 1 in the agent-working-planner session 2026-11-08. Lands in PR 2, after PR 1 (batch B) merges.

## Scope
1. P1 frontmatter fields (all optional): `evidence_paths` (files, not directories), `verified_by` (ticket or PR), `verified_at` (code SHA read), plus `reviewed_by` (batch J: triaged, no staleness found; weaker than verified, never shown as verified). Add them to `docs/guidelines/frontmatter_schema.md` and `tools/validate_frontmatter.py` (shape checks: paths exist at write time, SHA shape, ticket ID shape).
2. Drift report tool, reusing the `tools/mechanism_registry/mechanism_registry_changed_code_check.py` pattern and the shared search from batch B. Baseline: the commit that last changed the doc's `verified_by` line (or `reviewed_by`), derived from git history so it survives squash merges. Flags "needs re-verify" when an evidence path changed, was deleted or renamed after the baseline, or the doc's own text changed after it. Lists unverified, reviewed_by, verified_by and needs-re-verify states. No stored state besides the fields.
3. Runs at close: pipeline Finalize (`implement-ticket.js`) and the hand-close checklist, advisory, never blocks.
4. Q5: the weekly run is a script step inside `tools/agent-monitoring/week_close.py` (called by `make agent-monitoring-close-week`), report-only; the retro gets 2-3 spot checks (a retro-template line; the retro itself is u24's).
5. E2: delivery_process.md gains the P5 rules that cite P1 (the "when code is read" triggers on verified_by and drift; critical invariants need a verified doc plus an independent test).

## Out of Scope
- Setting verified_by on any doc (batch H). AC 2 of the plan: no seed doc gets the fields without a ticket that records the claims checked.
- The J1 detection mode (TCK-20261108-STALE-DOC-DETECTION-PILOT), though it reuses this tool.
- Any blocking behaviour.

## Acceptance Criteria
1. Plan AC 2: a doc without verified_by shows as unverified in the report (test).
2. Plan AC 3: a changed, deleted or renamed evidence path, and a doc-text edit after the baseline, each produce "needs re-verify" in a test fixture; the baseline survives a squash-merged fixture history.
3. validate_frontmatter rejects malformed fields and accepts docs without them.
4. week_close.py runs the report without changing its own exit behaviour (test).
5. tests/tools/ passes in a lead slot; paths-guard tests run before push.

## Related Tickets
- TCK-20261108-EPIC-DOCS-AS-REVIEW-SOURCE
- TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH (shared search)
- TCK-20261108-STALE-DOC-DETECTION-PILOT (same PR)
- TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE (pattern)

## Related Docs
- origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR)
- docs/guidelines/frontmatter_schema.md
- docs/guides/delivery_process.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/validate_frontmatter.py, tools/mechanism_registry/mechanism_registry_changed_code_check.py
- tools/agent-monitoring/week_close.py, .claude/workflows/implement-ticket.js (Finalize)

## Assumptions / Open Questions
- The CLAUDE.md After Work line for running the report at a hand close is a governing-file edit: owner's direct OK on the diff, as in E1.

## Implementation Notes
Plan review: agent-working-planner, GO with five conditions (relayed 2026-11-11); all five are built in and listed here.
1. `validate_frontmatter` checks the shape of `evidence_paths` only: a repo-relative file path, no trailing `/`, no glob, no absolute path, no `..`. It has **no existence check**, so deleting an evidence file later cannot turn the corpus frontmatter tests red (that would make drift a blocking gate). A deleted file is reported by the drift report instead. `verified_by` and `reviewed_by` are a TCK-ID or `"#<digits>"` (quote the PR form: an unquoted `#` is a YAML comment); `verified_at` is 7-40 lowercase hex.
2. Rename detection runs `git diff -M --name-status <baseline> <pin>` with no pathspec and filters by old path in Python; the fixture renames a file into a new directory.
3. The doc-text rule is written once, in the `doc_drift.py` module docstring: any diff to the doc after the baseline except the `verified_by`, `verified_at` and `reviewed_by` lines; an `evidence_paths` edit counts.
4. Detect-mode cost: last-commit times and the rename map are built in one `git log` pass each (a test counts the calls), and the route map is called as a library function. Timed at origin/main 5c6990e51: 20 s wall, 88 MB peak, so no heavy slot is needed.
5. Plan lifecycle reads the real status enum (`historical`, `archive`) from `validate_frontmatter.STATUS_VALUES`; the PR 1 search's `superseded` is not a schema value and is not used here.
Smaller points: `-G` with `--follow` is accepted by git 2.51 and a `git mv` fixture covers it; a commit that removes the `verified_by:` line is the baseline and the doc then reads unverified (tested); a shallow clone's boundary commit is treated as no baseline, reported `baseline-unavailable` (tested).
Decisions: (a) the Finalize hook is a log-only advisory block at the Finalize tail of `implement-ticket.js` (`doc_drift.py --format advisory --start-sha`), not a new attested gate site (the pinned `gateCmd` keys test); (b) the weekly summary prints from `week_close.py` after the fold (HEAD of the checkout it runs in, full SHA), never with `--data-dir`, and an exception becomes one "skipped" line; exit status and the Makefile are unchanged; (c) the hand-close line is in `delivery_process.md`, with no CLAUDE.md edit (governing file).
Known gaps: no doc carries the fields yet, so the report shows zeros until batch H; the retro-template line (Q5: 2-3 spot checks) is not added: `.claude/skills/agent-monitoring-retro/SKILL.md` routes as unowned and is not in the approved list. Proposed line for the retro owner: "Spot-check 2-3 docs from `python3 tools/gate_checks/doc_drift.py` (needs-re-verify first): read the changed evidence, and record the verdict."
Docs step (PR 1 search on this change): updated `docs/guidelines/frontmatter_schema.md`, `docs/guides/delivery_process.md`, `docs/ai/workflows.md` (Finalize row) and `docs/agent-monitoring/README.md` (week close); the remaining candidates cite the changed files only incidentally and were left alone.

## Test Summary
- `tests/tools/test_doc_drift.py`: 30 tests (drift states, squash, move, shallow, uncommitted, CLI); `test_validate_frontmatter_evidence_fields.py`: 17; `test_finalize_doc_drift_wiring.py`: 4; `test_week_close.py`: 4 new.
- Scoped run (light cores 0-3, MemoryMax 1G): the 76 test files under tests/tools and tests/docs that mention the files touched: 1472 passed, 12 skipped, 1 xfailed.
- `python3 -m codebase.health check`: exit 0 (2 new report-only rows in src, not from this change).
- `generate_registry --check`, `done_checker_static` and the mechanism advisory: see the Completion Summary.
- Full `tests/tools` + `tests/docs` in a lead slot: requested from the planner before the push.

## Files Changed
tools/gate_checks/doc_drift.py (new), tools/gate_checks/doc_drift_pilot.py (new), tools/gate_checks/changed_files.py (optional cwd), tools/validate_frontmatter.py, tools/agent-monitoring/week_close.py, .claude/workflows/implement-ticket.js, docs/guidelines/frontmatter_schema.md, docs/guides/delivery_process.md, docs/ai/workflows.md, docs/agent-monitoring/README.md, tests/tools/test_doc_drift.py, test_validate_frontmatter_evidence_fields.py, test_finalize_doc_drift_wiring.py, test_week_close.py.

## Completion Summary
Behaviour docs can carry `evidence_paths`, `verified_by`, `verified_at` and `reviewed_by` (shape-checked, optional), and `python3 tools/gate_checks/doc_drift.py` reports each doc as needs-re-verify, verified_by, reviewed_by or unverified from a pinned git read, with a baseline that survives a squash merge. It runs advisory at a pipeline Finalize, in the weekly close, and as a hand-close step, and never blocks. Known gap: no doc carries the fields yet (batch H), and the retro-template line is left to the retro owner.
