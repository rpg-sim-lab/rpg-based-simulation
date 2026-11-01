---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK
phase: done
date: 2026-11-01
tags: [testing, architecture]
---

# TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK: investigation

Premise check (2026-10-31, main 6fdfdf555): the OFF assertion first failed. recorder and decision_trace_writer were in sys.modules after world compile, before any Kernel existed: src/ai/goals/adventure_scorer.py:10 imported decision_trace_writer at the top level and src/observability/cognition/__init__.py:11 imports recorder. src.ai.goals is not a source module of c06, so the linter could not see it. Reported to testing-planner; rpg-planner chose to fix src (hotfix TCK-20261031-ADVENTURE-SCORER-LOADS-THE-COGNITION-PACKAGE-IN-OFF-MODE, PR #803, merge 0bba1ff7d). The four module paths and four ignore_imports edges matched main; the toml comment's kernel.py line numbers had drifted (not used by the test). Stated limit: one tick on sandbox_world does not cover imports reached only on later ticks or other worlds.
