---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME
artifact_type: test_plan
phase: done
date: 2026-11-11
tags: []
---

# Test plan

Rows (the designer's, in the ticket): a trust-only SocialUpdate leaves rejection_count intact; a merge of two same-tick rejections from one offerer gives 2; two offerers stay separate; a to_canonical_dict round trip. Plus one appraisal row: the fatigue penalty reads the kept count.

Each row must fail on origin/main 5c6990e51 (shown before the fix) and pass after. Scoped runs at -n 1: tests/unit/social, tests/unit/core. Timing NOT MEASURED (perf pause).

## Proof Plan

- Level: unit (apply, merge, canonical dict, appraisal), then a paired 5000-tick simulation measurement.
- Proof kind: bug fix guarded by rows that fail before the fix, plus a measured paired comparison.
- Oracle source: the designer's ruling rows; base cells fresh on main 5c6990e51.
- Expected effect: counts survive unrelated updates and sum within a tick; recruitment rejected counts rise and LOYALTY_ACCEPTANCE moves (reported separately); deaths do not rise beyond the standing bar.
- Selected commands: pytest tests/unit/social tests/unit/core -n 1 -p no:randomly; python -m codebase.gates.mypy_gate; python -m codebase.health check.
