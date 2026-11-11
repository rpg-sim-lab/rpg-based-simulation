---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT
artifact_type: investigation
tags: [ai, documentation, governance]
---

# Investigation: TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT

## Findings
- The existing pattern: `tools/mechanism_registry/mechanism_registry_changed_code_check.py` (changed code a record cites, advisory, `--ticket-id`). The shared search from PR 1 (`tools/gate_checks/docs_search.py`) supplies the exclusion classes, the git-ref source (`cat-file --batch`) and the identifier-shape rule; `derive_changed_files` (`changed_files.py`) gained an optional `cwd`.
- `extract_frontmatter` parses inline lists only, so `evidence_paths` is `[a, b]`; a PR ref must be quoted (`"#123"`), otherwise YAML reads `#` as a comment.
- No doc carries the fields yet, so the weekly summary prints counts of zero until batch H.
- `-G` and `--follow` are accepted together by git 2.51 (checked), and a `git mv` fixture covers it.
- The route map (`tools/sessions/route.py`) labels many `docs/` paths "unowned" (176 of the flagged 480).
- The retro-template line (Q5, 2-3 spot checks) lives in `.claude/skills/agent-monitoring-retro/SKILL.md`, which routes as unowned and is not in the approved unowned list; it was left alone and the proposed line is in the ticket.
