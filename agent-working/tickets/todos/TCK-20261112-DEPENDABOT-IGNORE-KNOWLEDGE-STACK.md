---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261112-DEPENDABOT-IGNORE-KNOWLEDGE-STACK
phase: open
date: 2026-11-12
tags: [platform]
---

# TCK-20261112-DEPENDABOT-IGNORE-KNOWLEDGE-STACK

## Title
Dependabot's uv entry ignores torch, graphifyy and headroom-ai, so grouped PRs leave requirements-knowledge.txt alone

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Owner decision on Dependabot #882 (#715 6812820923, option A): #882 (uv-minor-patch, 20 updates) is closed, not merged.
It also rewrote `requirements-knowledge.txt`: `torch==2.13.0+cpu` -> `2.15.0` (dropping the `+cpu` local version),
`graphifyy 0.9.70 -> 0.9.104`, and `headroom-ai 0.37.0 -> 0.43.1` (which needs mcp 2.x, so it is held at 0.37.0).
Platform adds an `ignore` on the uv entry for these three, so the regrouped minor/patch PR touches only the project's
own pins. agent-working bumps the knowledge-stack pins under its own ticket.

## Scope
- `.github/dependabot.yml`, the `uv` entry (`directory: /`): add
  `ignore: [{dependency-name: torch}, {dependency-name: graphifyy}, {dependency-name: headroom-ai}]`, with no
  `versions`, so every version update for them is skipped. Add a comment that names the decision (#882, owner option A)
  and says who bumps them (agent-working, by hand, with its tests).
- Keep the labels, schedule and groups unchanged.

## Out of Scope
- Any pin change in `requirements-knowledge.txt`, `pyproject.toml` or `uv.lock` (agent-working's and rpg's).
- Closing #882 (the owner's).

## Acceptance Criteria
- `dependabot.yml` parses; the uv entry has exactly those three ignore names and its groups are unchanged; the other 6
  entries are byte-identical (validated: parse and diff).
- After merge, the next uv run (or a re-run the owner triggers) opens a uv-minor-patch PR that does not change
  `requirements-knowledge.txt` (observed after merge; until then: Known gap: not yet observed on a Dependabot run).

## Related Tickets
- TCK-20261111-DEPENDABOT-WATCHES-WEBSITE, TCK-20261015-DEPENDABOT-DOCKER-IGNORE-PYTHON-MINOR-AND-UV (done; same file).
- TCK-20261112-REPO-MOVE-PLATFORM-REFS (same PR).

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
.github/dependabot.yml
requirements-knowledge.txt

## Assumptions / Open Questions
- torch is also in `uv.lock` (2.13.0, a dependency of sentence-transformers). The ignore matches by name, so it also
  stops Dependabot from bumping torch in `uv.lock`. #882 did not bump torch in `uv.lock`, so nothing is lost today;
  torch then moves only by hand with the knowledge-stack pin. graphifyy and headroom-ai are not in `uv.lock`.
- Unverified: whether `ignore` without `versions` also suppresses Dependabot security updates for these names. The
  GitHub docs page on `ignore` is the source to read; record what it says in Implementation Notes.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
