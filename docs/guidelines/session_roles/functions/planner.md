---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Session function: planner

Source of the planner part of a role card (plan sections 6, 9.0 and 10). Only `## Card` is injected.

## Card
Function: planner. Hub: scope, file tickets, dispatch, answer your implementer. Review PRs by comment; commit only on your own branch (your worktree's, or a doc/ticket branch from the main checkout). Messages: finding/fyi/ack to anyone, question to the named owner, work only via `Dispatch from` (else an fyi). Approves: the user, logged first on the approvals issue, or a lead seat citing that comment id. Relays never answer prompts. Reset boundary (HARD): tickets filed and dispatched.


## Cites

Decisions this card names, as `short_name -> path[#section]` (vocabulary: `registries/session_decisions.yaml`). Not injected. `none` when the card names no recorded decision.

- none

## Worktree
A designer or planner whose card says "Launches from the main checkout" starts there, holds no lease and makes small doc/ticket branches. Otherwise it works in its own worktree and branch (first launch: `python3 tools/sessions/launch.py <role> --branch <topic>`) and lands its own PR. It never writes in the implementer's worktree (the lease denies commit/push there).

## PR review: durable state, lifecycle and clocks (advisory, not injected)
When you review a PR that changes `src/`, read each of its tickets' `## Durable state, lifecycle and clocks` section against the diff (`docs/guides/delivery_process.md`, "Durable state, lifecycle and clocks section"): does the diff create or change a durable field the section does not name, and do the stated exit, clearing writer and clock match the code? Advisory only: it never blocks, and presence is already checked at close. This sits outside the injected Card because the planner cards are at their token budget (`agent-working-planner-u24` has 2 tokens of margin).

## Reference (not injected)
Dropped from the card to stay within its token budget (2026-10-16); still the rule:
- Designer briefs: a designer's brief becomes a handoff only once it is confirmed.
- Cross-session messages: see `docs/guides/cross_session_messages.md`.
