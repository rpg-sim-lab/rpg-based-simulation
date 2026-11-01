---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-GOVERNING-FILE-EDITS-VISIBLE-TO-OWNER
phase: open
date: 2026-10-31
tags: [governance, delivery, agent-monitoring]
---

# TCK-20261031-GOVERNING-FILE-EDITS-VISIBLE-TO-OWNER

## Title
Show the owner when governing files are edited: one path definition, a list in the PR body and a guard event

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Raised by lead-planner on 2026-10-31, filed from the designer's draft. Nothing of ours stops or shows an agent's edit to a governing file. That matches the owner's 2026-10-07 rule ("Drop all but critical"; "governing files are protected by review and PR merge"), so this is not a malfunction. On 2026-10-31 one `CLAUDE.md` edit succeeded, one settings edit was denied and a later settings edit succeeded, all in auto mode. The records show only those outcomes, so they cannot show whether a prompt appeared. Why the two settings outcomes differ is inferred, not known.

Gaps this leaves:
1. Review relies on the owner noticing, but nothing lists governing paths in a PR.
2. Settings and hooks reload while sessions run, so a local edit takes effect with no merge.
3. The automatic safety check is a judgement we cannot test, so it is not a control we can rely on.
4. "Show the owner first" is a practice that nothing enforces.
5. The current governing list covers `CLAUDE.md` and the two settings files only. The guard, the classifier and `.github/workflows/` are not on it.

**Owner's direction (#715 6543787917, corrected by 6543790124):** detection first, with this shape. Guard `ask` is not chosen and is decided later from the counts. Checks stay report-only, with no strict gate. **Dispatch:** the owner said yes (#715 6543854496), after TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION merges, because both touch the guard. Fresh branch from origin/main. Slots, pushes and merges stay separate asks.

## Scope
Detection only:
1. One definition of governing paths in `tools/sessions/classify.py`, extended to the guard, the classifier and the workflows, for the plan's section 28a gate job to reuse later. Whether `GOVERNING_FILE_EDIT` itself widens or a second list is added is decided at planning, because the classify tests pin current behaviour.
2. `tools/delivery/pr_render.py`: when a PR touches a governing path, generate a visible list of those paths high in the body, from the diff against base. It is absent when none are touched.
3. `tools/sessions/guard.py`: on `governing_file_edit`, still allow, and record an event (seat, path, time) to monitoring. The row says this is an attempt, not a landed edit.
4. A retro line counting those events against the PR lists. An edit recorded but never in a PR is the case to look at.

## Out of Scope
- Any change to `.claude/settings.json` or `CLAUDE.md`.
- Blocking or prompting, and rewriting the 2026-10-07 rule.
- Any contents of a local or project permission list. The repo is public, so this ticket and its artifacts stay at the level of behaviour.

## Acceptance Criteria
1. A PR touching a governing path shows the list, and one that does not shows nothing. Tests cover both.
2. A governing edit by Edit and by Bash each writes one event and the call still succeeds, with a test. A failed write does not fail the call.
3. The guard's allow-with-no-output behaviour for other actions is unchanged.
4. The PR section states the list's limit: it comes from PR-controlled code, so `.github/` changes are still checked on GitHub's files tab (plan section 28a).
5. The retro line exists and has a test.

## Related Tickets
- TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION: its ConfigChange warning is partial cover at most. Its documented sources are settings and skills, not `CLAUDE.md`, and the docs do not say whether Claude's own edits fire it. This ticket relies on that warning only as far as that ticket's live test shows.
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Related Docs
docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md (sections 7 and 28a)

## Related Stored Artifacts
None.

## Related Code Areas
tools/sessions/classify.py, tools/sessions/guard.py, tools/delivery/pr_render.py, tools/agent-monitoring/

## Assumptions / Open Questions
- Owner's option, not in this ticket: the guard returns `ask` on `governing_file_edit`, forcing a prompt. This reverses part of the 2026-10-07 rule, so it is the owner's alone. By commit count, on the order of 15 prompts a month, likely more by edit count, and each stalls an unattended seat. It would close gap 2, which detection only reports afterwards. Not tested live. The designer recommends detection first, then deciding from its counts.
- Commit counts at origin/main over 30 days: `CLAUDE.md` 7, `.claude/settings.json` 8, of 424. These are commits, not edits or attempts.

## Implementation Notes
- Retro line (scope item 4) compares attempts with merged commits on origin/main by path and period, replacing "against the PR lists": a PR body is not a source of record and an event cannot be tied to one PR body. Unmatched can mean a reverted edit, a denied call, an unmerged branch or an unreviewed edit; an attempt can merge the next week.
- Rows carry `basis` (`path` exact for edit tools, `mention` for Bash text, which over-counts) and repo-relative paths only; a file outside the repo writes no row.
- The new path list is a second list in `classify.py` (`GOVERNING_PATHS_EXACT`, `GOVERNING_PATH_PREFIXES`); `GOVERNING_FILE_EDIT` is unchanged.
- Known gap: `discover_changed_files` in `pr_render.py` still uses the two-dot tree diff (`base..HEAD`) for the raw-probe warning and the ticketless file summary, so on a branch behind main those can list files only main changed. The governing section has its own three-dot call. The two-dot output is a separate question, not changed here.
- PR section is a `conditional` entry in `pr_template_spec.json`; the template-order test exempts only conditional entries and asserts this is the only one.

## Test Summary

## Files Changed

## Completion Summary
