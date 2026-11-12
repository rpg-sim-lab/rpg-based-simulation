---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT
artifact_type: plan
tags: [ai, documentation, governance]
---

# Plan: TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT

Spec: the two tickets, `SEQUENCE.md`, and the plan (`agent-working/lead/docs_as_review_source_plan.md`, rev 3.2: P1 "Drift report", P5, Batch J). Cited, not copied. Planner review of the plan-review point: GO with five conditions (relayed 2026-11-11), recorded in the ticket's Implementation Notes.

## Steps
1. `tools/gate_checks/doc_drift.py`: one module, read-only at a resolved pin (printed as a full SHA), exit status always 0. Drift mode and the J1 detect mode share its git layer (`Repo`).
2. `tools/validate_frontmatter.py` + `docs/guidelines/frontmatter_schema.md`: the four optional fields, shape only, no existence check (condition 1).
3. Hooks, all advisory: a Finalize-tail `log` line in `implement-ticket.js` (`--format advisory --start-sha`), a summary printed by `week_close.py` after the fold (exit status unchanged, not printed with `--data-dir`), no Makefile edit.
4. E2: `docs/guides/delivery_process.md` gets the fields, the drift report, and the P5 rules that use them. No CLAUDE.md edit (governing file): the hand-close line is in delivery_process.md and is named as a follow-up in the ticket.
5. Pilot (ticket 2): `doc_drift_pilot.py` + the J2 report under `agent-working/stored_artifacts/`.

## Decisions
- Baseline: `git log -1 --follow -G'^verified_by:'` (or `reviewed_by`), because `-G` also catches a changed value and the squash commit is the last commit that touched the line. A shallow-clone boundary commit is not a baseline (`baseline-unavailable`).
- Renames: `git diff -M --name-status <base> <pin>` WITHOUT a pathspec, filtered by old path in Python.
- Doc-text rule written once in the module docstring: any diff after the baseline except the `verified_by`, `verified_at` and `reviewed_by` lines; `evidence_paths` edits count.
- Cost: commit times and the rename map are built in one pass each (`git log --name-only`), not per path. Measured at 5c6990e51: 20 s, 88 MB, so no heavy slot.
- Plan lifecycle uses the real status enum (`historical`, `archive`), read from `validate_frontmatter.STATUS_VALUES`.

## Out of scope (hard lines)
No doc gets `verified_by` or `reviewed_by` (batch H); nothing blocks; J3 is not approved (no doc found stale is edited, retired or marked); recall is reported, never tuned to.
