---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261103-NEAR-DEATH-HARDENING-FIRES-WITH-NOTHING-HITTING-THE-SUBJECT
artifact_type: test_plan
tags: []
---

# test_plan: TCK-20261103-NEAR-DEATH-HARDENING-FIRES-WITH-NOTHING-HITTING-THE-SUBJECT

New: tests/unit/engine/test_near_death_hardening_hit_gate.py (max 100, line 10): hit to 8 grants +5; town +1 at 8 grants nothing; hazard to 8 grants nothing; hit + heal netting to 0 at 8 grants +5; hit below 0 grants nothing. Checked against the old code: the town-heal and hazard rows fail there; the other three pass there too (a grant is correct for them, and a hit below 0 grants nothing in both).
Edited inputs (assertions unchanged): test_near_death_hardening_emotion.py x3, test_species_base_stats_preserved.py::test_hardening_grants_five_accumulates_and_survives_recalc.
Must pass unchanged: test_emotion_near_death_hardening.py, test_lifecycle.py::test_near_death_hardening_logic.
