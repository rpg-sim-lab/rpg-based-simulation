---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-GOVERNING-FILE-EDITS-VISIBLE-TO-OWNER
artifact_type: plan
tags: [governance, delivery, agent-monitoring]
---

# Plan

Standard tier, hand-orchestrated, report-only. Order of work; each step has its tests in test_plan.md.

1. `tools/sessions/classify.py`: add `GOVERNING_PATHS` (single definition; repo-relative prefixes, no `/hooks/` marker; includes `registries/session_authority.yaml`) and two functions: `governing_path(path, repo_root=None)` (exact, repo-relative) and `governing_mentions(command_text)` (matched tokens only). `Classification` gains `governing_paths` + `governing_basis` (`path`|`mention`). `GOVERNING_FILE_EDIT`, `GOVERNING_FILES`, `is_authority` untouched.
2. `tools/sessions/boundary.py`: `write_event(record, data_dir=None, family="role_boundary.jsonl")`.
3. `tools/sessions/guard.py`: extend `_AUTHORITY_TEXT` with the three new names; add `_record_governing` called before the `is_authority` early return; try/except around everything; allow path unchanged.
4. `tools/delivery/pr_render.py` + `pr_template_spec.json` (+ template if pinned): `## Governing paths touched` section, absent when none, with the limit sentence; ticketless body too.
5. `tools/agent-monitoring/session_layer_report.py`: governing attempts vs merged-commit section; wire through `generate_retro` call site.
6. Docs: `docs/agent-monitoring/schema.md` (new family; also check validate.py, week_close.py and any family list), plus one paragraph in `docs/guides/delivery_process.md` (PR section) and the session-roles guideline noting the family and the limit. Mechanism registry untouched (rpg-planner owns mechanisms.yaml).
7. Close: working_log via the closure tool, monitoring, registry regen.

Out of scope kept: no settings/CLAUDE.md edit, no ask/deny, no new gate; plan 28a's gate job reuses `governing_paths_in` later, not built here.
Risks: Classification field add could break an equality assertion in a test (check at implementation, tests exist); `/hooks/` marker is broad; PR template pinned to spec.
Base: rebase onto fresh origin/main (#806, #807 pending) once the plan is OK'd, before code.

## Amendments (planner review): see investigation.md "Amendments"
Row fields: ts, event, seat, path (repo-relative), basis (path|mention), attempt:true. No row for paths outside the repo. Tests redirect the data dir for the whole guard test file. Retro shows basis path and mention separately and says an attempt can merge in a later week and rows reach main only when a branch carries them. Ticket text: retro compares by path and period, replacing "against the PR lists".
