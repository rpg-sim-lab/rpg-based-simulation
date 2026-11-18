---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261118-A-DIAGNOSTIC-KIT-PREFLIGHT-CHECKS-EACH-KIT-ON-BOTH-FROZEN-TREES-BEFORE-ITS-RUN
artifact_type: investigation
tags: []
---

# Investigation: faults the preflight must catch

Faults that reached S9 records on 2026-11-18: the #955 divergence probe read `navigation.failure_reason` (no such field, so field 6 was always the string "None"); `python -I` ignores PYTHONPATH so a kit without its own `sys.path` fix cannot import; the gate spy's `ctx`/`context` keyword could be swallowed as "not perceived"; a runner v2 called `blocker_spy.py` while the S9 named v3b; a `_reader.py` near-miss that the shared gate (`busy_gate.sh`, heavy words `_spy|_probe|...`) cannot see.
Findings while building: kit scripts are scripts (argv parsing at top level), so (b) executes only the top-level statements through the last import; the spy `def` sits inside a script, so (g) reads it from the AST; real kit files are named `<name>.py_<sha>_approved`; the divergence probe writes JSONL and reports `str(None)` = "None", so "None" must be in that field's default list.
Real-kit manual run results (evidence: executed, 2026-11-18, kitpre commit 1ad4410c6):
- #955 approved kit, main_99a83adc9_b + head_b5f8bc01e_b, 131 ticks: PASS, 0 FAIL of 45. Fields [2],[3],[7] declared may_be_constant. A 10-tick window left some fields constant, hence the 131-tick run.
- Faulty rebuild (divergence_probe 40ea9fa3...): FAIL, 2 FAIL of 26, both check (d): entities[*][6] constant "None" over 470 values on both trees.
- Churn kit manifest_v3 (blocker_spy_v3b) on tree_fix2, 10 ticks: PASS, 0 FAIL of 21.
Tables: /mnt/data2/rpg-measure/{ci955/kit_approved,ci955/kit_faulty,blockerchurn}/preflight.md. A preflight is "executed", never "validated".
