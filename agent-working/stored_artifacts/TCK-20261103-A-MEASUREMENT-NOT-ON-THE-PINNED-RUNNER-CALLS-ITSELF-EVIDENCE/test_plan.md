---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE
phase: done
date: 2026-11-15
tags: [testing, determinism, observability]
---

# TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE: test_plan

- `tests/unit/kernel/test_run_conditions_record.py` (16): pinned and default builds record their conditions and classify PINNED / NOT_PINNED from a real manifest; same state hash and same events with and without the record; manifest round trip; an older manifest loads; each condition alone makes NOT_PINNED; a larger budget is still PINNED; a missing record is NOT_PINNED; `build_kernel` classifies PINNED (ties PINNED to the builder); the evidence helper returns a pinned run and refuses the other; CLI exit codes; arm_child refuses an unpinned build.
- `tests/tools/test_evidence_runner_advisory.py` (6): flagged with line numbers; clean script OK; longer names and markdown not matched; staged scripts read, none is NA; unreadable root never raises; the done-checker lists it without changing its verdict.
- Must stay green: `tests/unit/kernel/test_executor_context_parity.py` (26 passed). SIMQ tools still run: `tests/simulation_quality/test_anchors_audit_mode.py` and the paired-arms tests pass.
- Wider: `tests/unit/kernel` + `tests/tools` single process: 6120 passed, 57 skipped, 1 xfailed. Scoped done-checker tests (static, audit, ticket lookup, proof plan, cited evidence, evidence runner): 232 passed.

## Proof Plan
- level: unit plus a hash-equal evidence run on real worlds
- proof kind: record + classifier + refusal, and a hash-equality run showing the record changes nothing
- oracle source: rpg-planner's conditions (record after executor selection, Optional, out of hashed state and events, one PINNED definition) and the main-tree hash
- expected effect: a build_kernel run classifies PINNED, a `_run_engine` run NOT_PINNED and is refused, and the run hash equals main's at the same end tick
- selected commands: pytest tests/unit/kernel/test_run_conditions_record.py tests/tools/test_evidence_runner_advisory.py tests/unit/kernel/test_executor_context_parity.py
