---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261115-PER-PHASE-TICK-COST-AFTER-THE-HOSTILITY-AND-COOPERATION-FIXES
phase: open
artifact_type: test_plan
date: 2026-11-16
tags: [performance]
---

# Test plan: stage 0 per-phase re-measure

Measurement ticket; the checks are run checks:
1. Quiet gate passed before every run (log in `evidence.md`).
2. 3 timed runs per world; spread stated; a world over about 10 % spread is INCONCLUSIVE, with no figure (frontier).
3. Every run's commit line reads `db6b4579d`; every run rc=0; measured_ticks 200.
4. The py-spy share of `fused_strategic_pass` is cross-checked against the unprofiled `resolution_overhead` share.
5. Run data cleaned by id.
