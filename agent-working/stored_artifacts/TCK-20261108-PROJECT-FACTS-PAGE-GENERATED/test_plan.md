---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261108-PROJECT-FACTS-PAGE-GENERATED
phase: done
date: 2026-11-14
tags: [ai, documentation, governance]
---

# Test plan

`tests/tools/test_project_stats.py` (new, under tests/tools so CI covers it); fixtures build a throwaway git repo in tmp with a few files so counts are exact.
- Each counter on the fixture repo: modules/lines, test files and static functions (a parametrized test counts once), tickets by folder, merged PRs from `(#N)` subjects, roles/subagents/skills/hooks, parity entries by status and priority, import baseline edges, alert rules.
- AC1 `--check`: passes on a fresh page; fails after one count is changed in the committed page; fails after the tool's rule text changes; header carries the ref SHA and each count has a rule string.
- AC2: two runs at the same ref are byte-identical (md and json).
- `--check` at a later HEAD with an unchanged tool still passes and prints the "HEAD moved" note.
- Real-tree check: the committed `docs/architecture/project_facts.md` passes `--check` (so a rule change without regeneration fails CI; the weekly close runs the same check).
- AC3: full `tests/tools` chunked in a lead slot (needs a lead go); `test_session_cards.py` and `test_session_roster.py` for the owns change; paths-guard, ci_workflow_test_coverage, no_duplicate_content_blocks.
