---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE
phase: done
date: 2026-11-15
tags: [testing, determinism, observability]
---

# TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE: plan

## Approach (planner rulings, testing-planner + rpg-planner, 2026-11-15; owner #715 6883358041)
1. `RunConditions` pydantic sub-model (governor, executor class qualnames; max_tick_budget_ms; audit_mode; no_frame_pacing) and `RunManifest.run_conditions: Optional[RunConditions] = None` in `src/observability/reporting/artifact_repository.py`.
2. One `update_manifest(run_id, run_conditions=...)` in `Kernel.__init__` right after executor selection. `create_run_directory` and the rng order are not touched; `no_frame_pacing` is read from the `flags` argument because `self._no_frame_pacing` is set later.
3. `tools/test_architecture/pinned_runner.py`: the single PINNED definition (`PinnedSpec`), `classify` from the record only, `require_pinned`, `evidence_row`, a CLI. `tools/rpg_measure/arm_child.py` imports it and reads the manifest record.
4. `tools/test_architecture/evidence_runner_advisory.py`, wired into `done_checker_static.run_advisory_checks` (agent-working-planner-u24 OK'd the two-line hook on condition of a lazy import).
5. Docs in the same batch: `docs/engine/kernel.md` manifest line, parity ledger INFRA-440 via `tools/parity_ledger_writer.py`. The `delivery_process.md:170` sentence is drafted and goes to the owner through the lead; the file is not edited here.
Out of scope: the cause of the runner difference, SIMQ anchors (they use `_run_engine` by design), re-measuring #826/#828.
