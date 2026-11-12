---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261108-STALE-DOC-DETECTION-PILOT
artifact_type: plan
tags: [ai, documentation, governance]
---

# Plan: TCK-20261108-STALE-DOC-DETECTION-PILOT

Spec: the ticket and the plan's Batch J (J1, J2). J3 is not approved.

## Steps
1. J1: `doc_drift.py --mode detect --ref <pin>`: signals `evidence-newer`, `unresolved-name` (renames shown), `plan-lifecycle`; ranked per owning domain; `reviewed_by` docs quiet while the baseline is clean. Same git layer as the drift report.
2. J2: `tools/gate_checks/doc_drift_pilot.py` reproduces the numbers; the evaluation report is `agent-working/stored_artifacts/doc_stale_detection_pilot_<pin8>.md`. The sample is about 20 docs at a fixed stride within each signal's ranked list (7/7/6); I grade each by hand with a one-line reason; the reviewer spot-checks 5.
3. The report states its pin, "docs audit", wall time, and `git status --porcelain -- docs/` before and after.

## Out of scope
J3; any doc edit; any test or threshold that targets the known docs (recall is printed as measured).
