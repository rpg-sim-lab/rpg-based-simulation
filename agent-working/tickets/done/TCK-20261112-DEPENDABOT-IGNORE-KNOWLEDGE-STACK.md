---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261112-DEPENDABOT-IGNORE-KNOWLEDGE-STACK
phase: done
date: 2026-11-12
tags: [platform]
---

# TCK-20261112-DEPENDABOT-IGNORE-KNOWLEDGE-STACK

## Title
Dependabot's uv entry ignores torch, graphifyy and headroom-ai, so grouped PRs leave requirements-knowledge.txt alone

## Status
DONE

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
- Resolved by lead-planner (uv.lock owner), 2026-11-12: freezing torch in `uv.lock` is fine. That torch is the CUDA build pulled in through the knowledge extra, which no environment installs from the lock, and it moves only with the knowledge pin, by hand.
- Unverified: whether `ignore` without `versions` also suppresses Dependabot security updates for these names. The
  GitHub docs page on `ignore` is the source to read; record what it says in Implementation Notes.

## Implementation Notes
- `.github/dependabot.yml`, uv entry (`directory: /`): added `ignore` with `dependency-name` torch, graphifyy and headroom-ai, no `versions`, plus a comment that cites #882 (owner option A, #715 6812820923), says agent-working bumps them by hand with its tests, and that torch in `uv.lock` moves the same way. Labels, schedule, limit and groups are untouched.
- **Open question, answered from the docs (read 2026-11-12):** GitHub's docs do not say whether `ignore` with only `dependency-name` also suppresses security updates. The page "Controlling which dependencies are updated" says "you can configure Dependabot to ignore those dependencies when it opens pull requests for version updates and security updates" and "Configure the `ignore` option for the dependency in your `dependabot.yml` file"; that is a general statement, not about the bare-name case. The same page and the options reference say of `update-types` (under `allow`): "`update-types` only affects *version* updates, not *security updates*." The `ignore` section of the options reference was only partly read (the fetch returned the first 39,883 of 186,189 characters), so nothing is quoted from it. Reading: a bare-name ignore should be assumed to also skip security PRs for these three names. A security advisory for torch, graphifyy or headroom-ai would then not open a Dependabot PR, so agent-working's hand bumps must watch the advisories (Dependabot alerts still appear in the Security tab).
## Test Summary
- **validated:** the file parses; the uv entry has exactly the three ignore names and its groups equal the previous groups; the other 6 entries compare equal to the previous version (parsed with yaml and compared with `==` against `git show HEAD:.github/dependabot.yml`). No test in `tests/` reads `dependabot.yml`.
- **not observed:** a Dependabot run after merge.
## Files Changed
- `.github/dependabot.yml`: ignore on the uv entry and its comment.
## Completion Summary
Dependabot's uv entry now skips torch, graphifyy and headroom-ai, so the grouped minor/patch PR leaves `requirements-knowledge.txt` alone. Owner decision #882, option A.
Known gap: the next uv run (or a re-run the owner triggers) is not yet observed; after merge it should open a uv-minor-patch PR that does not change `requirements-knowledge.txt`.
Known gap: the docs do not say whether a bare-name ignore also suppresses security updates for these names; assume it does (see Implementation Notes) and watch the advisories by hand.
