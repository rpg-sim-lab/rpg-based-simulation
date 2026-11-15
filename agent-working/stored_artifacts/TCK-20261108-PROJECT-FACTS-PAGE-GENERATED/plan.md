---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261108-PROJECT-FACTS-PAGE-GENERATED
phase: done
date: 2026-11-14
tags: [ai, documentation, governance]
---

# Plan

1. `tools/project_stats.py` (new): `--ref <sha>` (default HEAD), `--write` (writes `docs/architecture/project_facts.md`), `--check` (exit 1 when the committed page differs from a regeneration at the page's own header ref; prints one note if HEAD has moved on). Reads only git objects at the ref: `git ls-tree -r`, `git cat-file --batch`, `git log --first-parent`. No network, no imports of repo code, no timestamps; deterministic ordering.
2. Counters (each a small function with its rule string): src_modules_lines; test_files_functions (ast, no parametrize expansion); tickets_by_folder; merged_prs (first-parent subjects ending `(#N)`, with first and last commit dates); roles, subagents, session cards, skills, hooks by event; parity_ledger (entries by status and priority, with the rule that settles 2,307 vs 6,201); import_contracts and baseline_edges; metric_families; alert_rules.
3. Page `docs/architecture/project_facts.md`: frontmatter (status active, layer architecture, authority P2, tag), header "Generated from commit <sha> by tools/project_stats.py. Do not edit by hand. Regenerate with: ...", then one table per area with a "Counting rule" column. Lead approved the page and its generated marking (2026-11-14).
4. `registries/session_roles.yaml`: add `tools/project_stats.py` to agent-working's `owns`; regenerate `.claude/agents` and all derived views (`python3 -m tools.sessions.generate_agents`, then the registry/territory views per `feedback_registry_edit_run_full_tools_dir_and_all_views`); run test_session_cards.py.
5. No other doc is edited (citing the page elsewhere is a per-domain follow-up, listed in the Completion Summary with a CI wiring proposal and who refreshes the page: the weekly close running `--write`).
6. Close: ticket to done/, move the whole `todos/docs-as-review-source/` folder (SEQUENCE.md, epic ticket) to done/ per CLAUDE.md; artifacts to stored_artifacts/; hand-orchestrated closure; make docs-registry.
7. Verification: new tests; the full `tests/tools` dir chunked in a lead slot before the push (lead go needed); AC1-3.
