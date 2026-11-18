---
trigger: always_on
---

# Ticket Rule

## File Name

Use:

`TCK-YYYYMMDD-SHORT-SCOPE.md`

Example:

`TCK-20260330-CORE-STABILIZATION.md`

Rules:

- uppercase
- hyphen-separated
- short and meaningful
- stable after creation

---

## File Location

Active work:

`agent-working/tickets/inprogress/{ticket_id}.md`

Completed work:

`agent-working/tickets/done/{ticket_id}.md`

---

## Required Content

Use this exact section order:

# TCK-20260330-CORE-STABILIZATION

## Title

Short outcome-focused title

## Status

OPEN | INPROGRESS | BLOCKED | DONE

## Request Summary

What was requested

## Scope

- what this ticket will do

## Out of Scope

- what this ticket will not do

## Acceptance Criteria

- concrete, checkable outcomes

## Related Tickets

- related ticket IDs or None

## Related Docs

- relevant repo doc paths or None

## Related Stored Artifacts

- relevant artifact paths or None

## Related Code Areas

- expected files/modules

## Assumptions / Open Questions

- only material assumptions/questions

## Durable state, lifecycle and clocks

- required for tickets dated 2026-11-19 or later: `N/A: <reason>` (non-empty reason), or short answers per durable field or record the ticket creates or changes: who creates it and is creation idempotent across two passes; does an update merge or replace and what survives a replace; how every non-terminal state exits and what bounds how many exist; who clears it and is the value tested after a successful step; how many code paths write it and does it carry one meaning; which clock each reader uses (rule: the planned docs/engine/time_semantics.md, PLANNED, not landed; ask the question only). Questions only, no world rules; presence is checked at close (`tools/ticket_field_values.py::check_lifecycle_section`).

## Implementation Notes

- important design notes or changes during work

## Test Summary

- tests run
- tests added/updated
- known gaps if any

## Files Changed

- actual changed files

## Completion Summary

- final implementation summary
- limitations/follow-ups if any
