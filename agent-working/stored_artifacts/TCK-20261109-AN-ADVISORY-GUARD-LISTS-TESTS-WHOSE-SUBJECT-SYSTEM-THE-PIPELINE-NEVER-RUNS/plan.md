---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261109-AN-ADVISORY-GUARD-LISTS-TESTS-WHOSE-SUBJECT-SYSTEM-THE-PIPELINE-NEVER-RUNS
phase: done
date: 2026-11-15
tags: [testing, architecture]
---

# TCK-20261109-AN-ADVISORY-GUARD-LISTS-TESTS-WHOSE-SUBJECT-SYSTEM-THE-PIPELINE-NEVER-RUNS: plan

1. `tools/test_architecture/unwired_subject_check.py`: AST import-and-use reachability from `src/engine/pipeline.py`; `phase_inventory.inventory_pipeline` is run on the pipeline text so the report shows the root was read as the refinement pipeline.
2. Classes: wired, dispatch-reached (module reached, symbol never named), unwired (with how it is referenced). Tests importing an unwired symbol are flagged unless the file carries `pytest.mark.unwired_subject("<reason>")`.
3. `tests/architecture/test_unwired_subject_check.py`: synthetic package (wired, re-export-only, unmarked and marked importing tests), a pipeline edit moves a system into the wired set, one real-tree run asserting `StrategicRedirectionSystem` is unwired.
4. Register the marker in pyproject; one paragraph in `docs/testing/test_taxonomy.md`. Exit code always 0; no CI job reads the output.
