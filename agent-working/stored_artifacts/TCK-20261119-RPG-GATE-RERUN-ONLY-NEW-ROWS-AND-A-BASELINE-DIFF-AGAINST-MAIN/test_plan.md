---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261119-RPG-GATE-RERUN-ONLY-NEW-ROWS-AND-A-BASELINE-DIFF-AGAINST-MAIN
phase: done
date: 2026-11-19
tags: [process-improvement]
---

# Test plan
tests/unit/tools/test_rpg_gate_rerun_only_new_rows.py: replay of five recorded PR-run reports against main run 44323101062 (trimmed fixtures in tests/fixtures/rpg_gate_replay); no new row; one new row; main missing; main unreadable (five shapes); state changed; value changed; gone rows; known list not exempting; harness/baseline mismatch; carried row in a rerun pair; selection rule (schedule, dispatch on main, ref-input elsewhere, branch filter, age bound, invalid bound); CLI. tests/static/test_ci_rpg_gate_workflow_shape.py: permissions and step order.
