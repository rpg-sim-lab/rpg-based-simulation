---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261107-EVERY-PR-CLOSES-A-TICKET
phase: done
date: 2026-11-07
tags: [delivery, governance, claude-md]
---

# TCK-20261107-EVERY-PR-CLOSES-A-TICKET

## Title
Every PR closes at least one completed ticket, and fixes are weighed before they are built

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Two owner rules, both given on 2026-11-07 and routed to agent-working-planner by lead-planner.

1. **PR size** (#715 6697748243): no small PRs without a completed ticket. Every PR delivers complete work and closes at
   least one ticket. Ticket filings, evidence records and seat-ticket notes ride in the next implementation PR on that
   track, never alone. The reason is to cut CI and check effort. #835 and #836, both "(no tickets)", are examples of
   what it rules out.
2. **Weigh the fix** (#715 6697776913, widened by the owner at 6698958617 to any fix in any domain, with the cost
   including measurement and evidence runs; this supersedes the original RPG wording): before spending time on any fix, weigh whether it is worth it, and prefer the
   simpler fix when it is enough. Some fixes cannot be avoided (determinism, conservation, a hard rule the owner set),
   and those are done properly. Others may be better as a smaller fix, a named known gap, or a follow-up. The planner
   states the choice and the reason when scoping: the cost (including measurement and evidence runs), and what the simpler option leaves out. It escalates to the
   owner only when the simpler option changes a rule the owner set.

The owner's answers on the details (#715 6698888922):
- Exceptions: Dependabot PRs and the handover-transit export only. Week-close and retro batches get a ticket of their
  own, or ride in the next agent-working implementation PR.
- `pr_render.py`: keep the ticketless path, which the exceptions still need, but print a stderr warning naming the rule
  and the exceptions. Report-only, no new gate.
- The exact CLAUDE.md line, below, was approved as written.

## Scope
1. **CLAUDE.md, exactly one line and nothing else.** Add a new paragraph right after the existing paragraph under
   `### PR Lifecycle (once the user has authorized landing a batch)`, the one that ends "...and the PR-body
   no-attribution-trailer rule.". The text, verbatim:

   > Every PR closes at least one completed ticket: ticket filings, evidence records and seat-ticket notes ride in the next implementation PR on that track, never in a PR of their own (full rule and exceptions: `docs/guides/delivery_process.md`, "PR Lifecycle").

   Put the literal before and after in the PR's Review notes. No other CLAUDE.md byte changes. Rule 2 does not go in
   CLAUDE.md: the owner's OK covers only this line.
2. **`docs/guides/delivery_process.md`, "PR Lifecycle": the full PR-size rule, defined once.** State the rule, its
   reason, the two exceptions (Dependabot, the handover-transit export), and that week-close and retro batches get a
   ticket or ride in the next agent-working implementation PR. Merge it with the existing wording rather than adding a
   near-duplicate:
   - "A branch that closes no ticket at all (docs-only or record-only) renders with `--theme`, `--scope`..." (the
     ticketless paragraph after the PR Body Template, about line 321) currently presents such a PR as normal. Reword it
     so the ticketless render is for the two exceptions only, and point to the rule.
   - Step 2a (handover-transit bundle "in its own commit or PR"): consistent with the rule, because it is a named
     exception. Name it as one there, or in the rule, but not in both.
3. **`docs/guides/delivery_process.md`: rule 2, right after the PR-size rule.** Follow the owner's text in #715
   6697776913 as widened at 6698958617 (any fix in any domain; the cost includes measurement and evidence runs; this
   supersedes the original RPG wording): unavoidable fixes done properly, the smaller-fix / named-known-gap / follow-up
   options, the planner stating the choice and reason (the cost, and what the simpler option leaves out), and
   escalation only when the simpler option changes an owner-set rule.
4. **`docs/plans/agent_infrastructure/session_layer_working_process.md` section 7** ("no plan-only PRs" in two
   bullets): keep the role obligations, but replace the restated PR rule with a pointer to delivery_process "PR
   Lifecycle", so the rule lives in one place.
5. **`tools/delivery/pr_render.py`, ticketless path** (`render()`, the `(no tickets)` title branch and
   `render_ticketless_body`): print one stderr warning when it renders a branch that closes no ticket. The warning
   names the rule and the two exceptions and points to delivery_process "PR Lifecycle". Exit code, stdout, `--json`
   output and `--check` are unchanged. Add a test that the warning appears on the ticketless path and not on a branch
   that closes a ticket.

## Out of Scope
- Any gate, CI check or `pr_body_lint` change that blocks a ticketless PR (owner: report-only).
- Rule 2 in CLAUDE.md, and any other CLAUDE.md wording.
- Changing open PRs #838 or earlier merged "(no tickets)" PRs.
- Memory files (the planner's own; updated to point at the doc after merge).
- Widening rule 2 beyond what the owner wrote. (The owner widened it at 6698958617 to any fix in any domain, with measurement and evidence runs in the cost; the delivery_process text follows that, superseding the RPG wording.)

## Acceptance Criteria
1. The CLAUDE.md diff is exactly the one approved line plus its blank separator line, with the before and after shown
   in Review notes.
2. delivery_process "PR Lifecycle" states the PR-size rule once, with its reason and the two exceptions. The ticketless
   paragraph no longer presents a ticketless PR as normal, and no other doc restates the rule.
3. Rule 2 sits right after the PR-size rule, faithful to #715 6697776913.
4. session_layer_working_process section 7 points to the rule instead of restating it.
5. `pr_render.py` warns on stderr for a branch that closes no ticket, with a test, and the output and exit code
   are otherwise unchanged.
6. The PR closes this ticket (the rule applies to its own PR) and rides in the next agent-working implementation batch
   if one is open when it is ready.

## Related Tickets
- TCK-20261002-PR-RENDER-CITED-ONLY-AND-TICKETLESS-BRANCHES (added the ticketless render path this ticket now marks as
  exceptions-only)
- TCK-20261031-GOVERNING-FILE-EDITS-VISIBLE-TO-OWNER (its PR section will list CLAUDE.md for this PR)

## Related Docs
- docs/guides/delivery_process.md ("PR Body Template", "PR Lifecycle", step 2a)
- docs/plans/agent_infrastructure/session_layer_working_process.md section 7
- CLAUDE.md "PR Lifecycle"

## Related Stored Artifacts
None.

## Related Code Areas
- tools/delivery/pr_render.py (`render`, `render_ticketless_body`, `main`)
- tests/tools/test_delivery_pr_render.py

## Assumptions / Open Questions
- What already assumes a "(no tickets)" PR is valid (searched on origin/main 36d4fd78e..5ef440beb):
  - `tools/delivery/pr_render.py`, the ticketless path: `--theme`, `--scope` and `--why` render a `(no tickets)` title
    and `Closes: (none)`, with an error hint that tells the caller how. Kept for the exceptions, now with a warning.
  - delivery_process.md's ticketless paragraph after the PR Body Template, and step 2a.
  - session_layer_working_process.md section 7 ("no plan-only PRs").
  - No gate, workflow or session-layer code checks for a ticket (`.github/`, `tools/gate_checks/`, `tools/sessions/`):
    nothing blocks either way.
- Week-close and retro batches (u24's #804/#805 pattern) now need a ticket. That changes u24's practice. lead-planner
  tells lead-planner-u24.

## Implementation Notes
- CLAUDE.md: one paragraph plus a blank separator after the PR Lifecycle paragraph; nothing else changed. The edit applied without a denial or prompt.
- delivery_process.md: PR-size rule and rule 2 (owner text as widened at 6698958617: any fix, any domain, measurement and evidence runs in the cost) sit at the top of "PR Lifecycle", defined once. The ticketless paragraph now says that path is for the two exceptions and warns. Step 2a is named as one of the two exceptions.
- session_layer_working_process.md section 7: both bullets point to "PR Lifecycle" instead of restating the rule.
- pr_render.py: `TICKETLESS_TITLE_SUFFIX` and `TICKETLESS_WARNING`; `main` prints the warning to stderr when the rendered title is ticketless and the run is not `--check`. `render()` return value, stdout, `--json`, `warnings` key and exit code are unchanged.

## Test Summary
- Light slot (taskset -c 0-3, MemoryMax=1G, -n 1): `tests/tools/test_delivery_pr_render.py` + `tests/tools/test_delivery_templates.py`: 99 passed in 5.0 s.
- `python3 -m tools.generate_registry --check`: In sync (3900 entries) before Finalize; re-run after, result in the PR body.
- Known gap: none. The CLAUDE.md change is prose and has no test.

## Files Changed
CLAUDE.md; docs/guides/delivery_process.md; docs/plans/agent_infrastructure/session_layer_working_process.md; tools/delivery/pr_render.py; tests/tools/test_delivery_pr_render.py; this ticket; monitoring shards.

## Completion Summary
Both owner rules are recorded once in delivery_process "PR Lifecycle", CLAUDE.md carries the single approved line, section 7 points to the rule, and pr_render warns on stderr for a ticketless render (report-only).
