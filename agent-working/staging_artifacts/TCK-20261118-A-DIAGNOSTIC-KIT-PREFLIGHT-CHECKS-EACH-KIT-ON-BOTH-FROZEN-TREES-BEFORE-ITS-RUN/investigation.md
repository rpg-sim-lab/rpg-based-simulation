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
Real-kit manual run results: appended after the run (the ticket's acceptance evidence).
