---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-AN-ADVISORY-GUARD-LISTS-TESTS-WHOSE-SUBJECT-SYSTEM-THE-PIPELINE-NEVER-RUNS
phase: done
date: 2026-11-15
tags: [testing, architecture]
---

# TCK-20261109-AN-ADVISORY-GUARD-LISTS-TESTS-WHOSE-SUBJECT-SYSTEM-THE-PIPELINE-NEVER-RUNS: investigation

- The found case: `StrategicRedirectionSystem` is defined in `src/systems/strategic_systems/redirection.py`, re-exported by the facade `src/systems/redirection.py`, and named by no src module; the pipeline does not call it. Five tests import it.
- Module-level reachability would mark it reached (package `__init__` imports); the check therefore follows names that are *used*, not imports, and treats `__all__` and unused imports as re-exports.
- Registry or string dispatch is invisible: a symbol in a reached module that nothing names is reported dispatch-reached, not unwired (the ticket's open question).
- The kernel and scheduler are not roots by default (`--also-root` adds them). With the kernel as a root the real tree gives 15 unwired instead of 19.
- Real tree (default root): 63 public `src/systems` symbols: 29 wired, 15 dispatch-reached, 19 unwired; 26 test files flagged. Full report: `real_tree_report.txt` in this folder.
- Hand-checked sample of 5 unwired entries (grep over src): HarvestSystem (only the facade `harvest_system.py` names it): true positive. QuestGenerationSystem (only the facade `quests.py`): true positive. SocialMemoryService (`engine/apply.py:52` imports it and never uses it; the rest are comments): true positive, import-only. GroupService (no reference in src at all): true positive, test-only. LoyaltyDriftService (named only by `domains/campaigns/orchestrator.py`, which the pipeline does not reach, also not from the kernel root): a real caller outside the pipeline, so "never runs" is not shown; the report labels it "used only by src module(s) the pipeline does not reach". 4 of 5 true positives; the same label covers 4 entries in all (evaluate_social_consequence, LoyaltyDriftService, CognitionGraphExporter, EventInterpreter), which are the likely false positives for "never runs".
