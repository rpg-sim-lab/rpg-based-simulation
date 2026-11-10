---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261103-THE-STARVATION-RECORD-MISSES-MEALS-WITHOUT-AN-INTENT-RESULT
artifact_type: plan
---

# Plan — starvation record counts every meal

1. `StarvationRecorder._note_attempts`: a drop in hunger is a meal, whatever wrote it, with or without an intent result and whether or not the subject is escalated; it stamps `_last_meal` and clears the union and the attempts. Attempts are still counted only from an escalated subject.
2. `_attempted_way`: CORPSE_FOOD maps to SCAVENGE.
3. Tests in tests/unit/observability/test_starvation_death_record.py (4 new).
4. Re-read the five known entries with the fixed recorder (needs the heavy slot); report, do not edit rpg_gate_known.yaml.
5. Observability only: no authoritative state, hash unchanged (one pinned run, base vs fix).
