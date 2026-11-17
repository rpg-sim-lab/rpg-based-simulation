---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261107-README-OVERVIEW-AND-VERIFICATION-SCOPE
phase: done
date: 2026-11-07
tags: [documentation, determinism]
---

# TCK-20261107-README-OVERVIEW-AND-VERIFICATION-SCOPE

## Title
The root README names classes that do not exist (WorldLoop, IdentityAspect and the other aspects), describes a four-section published docs site that has one unpublished section, lists Promtail where Alloy ships logs, and frames determinism without its scope

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
personal-career, on the owner's behalf (2026-11-07), relayed an external AI review of the public README and GitHub metadata (`personal-career/tmp/reviews/ext-ai-suggest-update-readme.md`, outside this repo). Its claims were treated as hypotheses and each was checked against origin/main a7f1bb3df. This ticket fixes the confirmed README problems with minimal edits and adds an overview. The metadata proposal is not part of this ticket: the owner decides it and changes the settings.

## Scope
- `README.md` only.
- Fix confirmed wrong claims:
  - `WorldLoop`: no such class; the loop is `Kernel` (`src/engine/kernel.py`).
  - `IdentityAspect`/`BodyAspect`/`MindAspect`/`SocialAspect`: no such classes in `src/`. Entities are frozen typed components (`src/core/state.py`, `docs/core/entities.md`).
  - "Thread-safe isolated read models ... without locking the tick loop": the engine thread publishes state and the read cache under `_state_lock` (`src/api/engine_manager.py:143-150`), and API reads take the same lock (`:188-200`).
  - Docs site "four sections", tickets "~657", "all four sections" search: `docs/README.md:25-38` says one Docs section; the plugins were removed. The Pages deploy is `workflow_dispatch` only (`.github/workflows/deploy-docs.yml:1-13`), and `gh api .../pages` returns 404.
  - Hardcoded counts ("912 entries", "500+ files"): removed.
  - Promtail: compose runs `alloy` (`compose.yaml:5,260`).
  - Tempo: it is provisioned, but `src/` has no OpenTelemetry or span code. This is now stated.
  - "For reviewers": renamed "Verification and reproducibility". The section states the DET-PORT-0 scope (`docs/engine/deterministic_execution.md:30-36`). `make replay-check` is called a demo, as its own docstring does (`codebase/reports/replay_check.py:2-8`). Points to `known_limitations.md`.
- Add: an overview, a verified-capabilities table, a propose / refine-apply explanation, a statement that simulated entities are not the development agents, the workflow by purpose, the license status, `make dev`, and `--resource-budget=large`.

## Out of Scope
- GitHub description, topics, homepage and badges: proposed to the owner, not changed.
- `CONTRIBUTING.md`: its title "Resource-Safe Engine" and its cited `engineering_playbook_m10.md` are not checked here. It has no contribution-permission statement under the All Rights Reserved license. Reported as a finding; the file is not lead-owned.
- `docs/engine/known_limitations.md` does not list the open defects below; adding them belongs to the owning tickets.
- Fixing any defect.

## Acceptance Criteria
- Every class, command, flag, file and link named in README.md exists at the branch head.
- No hardcoded ticket, registry or doc counts.
- The determinism wording matches DET-PORT-0 and names the Live contract's difference.
- The docs-site text matches `docs/README.md` and the deploy workflow.

## Related Tickets
- TCK-20261025-README-DETERMINISM-AND-ENTITIES-FLAG-CLAIMS (the previous README fix)
- TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING (todo)
- TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ (todo)

## Related Docs
- docs/engine/deterministic_execution.md
- docs/engine/known_limitations.md
- docs/README.md
- docs/core/entities.md
- docs/engine/kernel.md

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
src/engine/kernel.py, src/api/engine_manager.py, src/api/ws/stream.py, src/engine/scenario_checkpoint.py, compose.yaml, Makefile, codebase/reports/replay_check.py, tests/conftest.py

## Assumptions / Open Questions
- Open defects found at a7f1bb3df:
  - `src/engine/scenario_checkpoint.py:91` restores with `base_seed=0`. A normal run uses `state.seed` (`scenario_runtime.py:420`), and `set_state` does not restore the base seed (`src/platform/rng.py:57-62`). No ticket exists yet; it is in lead-planner's unrouted review draft.
  - Harvest availability subtracts both the pending delta and the in-tick reservation (`src/core/conservation.py:317-324`). Unrouted.
  - Digest coverage gaps: tracked by TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ (todo).
  - The reclaim sweep ACKs after a failed DLQ write (`src/observability/stream/consumer.py:158-164`). Unrouted.
- The README names only the checkpoint seed defect, because it qualifies a determinism claim. The others sit outside the README's claims.
- Not run: `make install`, `make serve`, `make cli`, `make dev`, `make replay-check`, `docker compose`. They were checked by reading the Makefile, `src/cli/entry.py` flags, compose and conftest.

## Implementation Notes
Minimal edits; the existing sections are kept. The verification notes are in the Scope above.

## Test Summary
Docs-only. Links and paths are checked with `git cat-file -e` at the branch head. Frontmatter is validated.

## Files Changed
- README.md
- agent-working/tickets/done/TCK-20261107-README-OVERVIEW-AND-VERIFICATION-SCOPE.md

## Completion Summary
README.md corrected and extended as scoped; every named path verified at the branch head. Metadata proposal and the findings list went to personal-career for the owner; no repository settings were changed.
