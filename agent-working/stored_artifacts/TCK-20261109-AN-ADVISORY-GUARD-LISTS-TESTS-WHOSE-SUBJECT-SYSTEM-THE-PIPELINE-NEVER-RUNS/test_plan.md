---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261109-AN-ADVISORY-GUARD-LISTS-TESTS-WHOSE-SUBJECT-SYSTEM-THE-PIPELINE-NEVER-RUNS
phase: done
date: 2026-11-15
tags: [testing, architecture]
---

# TCK-20261109-AN-ADVISORY-GUARD-LISTS-TESTS-WHOSE-SUBJECT-SYSTEM-THE-PIPELINE-NEVER-RUNS: test_plan

| AC | Test |
|---|---|
| 1 | synthetic package: exactly the re-export-only (and unreferenced) systems are unwired; exactly the unmarked importing test is flagged, the marked one acknowledged with its reason |
| 2 | real tree: `StrategicRedirectionSystem` unwired, re-export only, with its tests flagged; counts and sample in `investigation.md` |
| 3 | adding a use in a synthetic pipeline moves a system into the wired set; unused import reaches nothing; attribute-chain use is followed |
| 4 | `main` returns 0 with findings; `--json` parses |
| 5 | `tests/unit/tools/test_marker_vocabulary.py` passes with the marker registered |
