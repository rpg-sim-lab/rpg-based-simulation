---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261118-A-DIAGNOSTIC-KIT-PREFLIGHT-CHECKS-EACH-KIT-ON-BOTH-FROZEN-TREES-BEFORE-ITS-RUN
artifact_type: test_plan
tags: []
---

# Test plan

`tests/unit/tools/test_kit_preflight.py`: clean kit passes on two trees; constant-None field fails (d); no-sys.path-fix probe fails (b) and (c); may_be_constant listed and passes; missing field; sha mismatch; rc!=0, bad line, ERROR log, unhit hook; (f) unlisted runner python file fails, comments ignored; (g) ctx-for-context fails, matching/*args/**kwargs pass, pure signature rules; (h) `_reader.py` fails, pattern parsed from a busy_gate.sh; script-style probe, JSONL output, spy inside a script; CLI exit code.
Manual (host, with HOST FREE): the approved ci955 kit PASSES, the faulty probe FAILS, the churn v3 kit PASSES, on the frozen trees.
