---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261027-RPG-MEASURE-CACHE-DEFAULT-HOST-NEUTRAL
phase: open
date: 2026-10-27
tags: [benchmarking]
---

# TCK-20261027-RPG-MEASURE-CACHE-DEFAULT-HOST-NEUTRAL

## Title
rpg_measure `paired.py` cache default is a u24-only path; make it host-neutral with a clear error

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tools/rpg_measure/paired.py:48` sets
`DEFAULT_CACHE = Path(os.environ.get("RPG_MEASURE_CACHE", "/mnt/data/scratch-rpg-measure"))`.
`/mnt/data` exists only on u24desktop. On host ubuntu, perf-implementer's F1 run (2026-10-26 night)
died within 1 s with a PermissionError. Raised by lead-planner (ubuntu); relayed via
lead-planner-u24 and testing-implementer
(`.claude/handover/drafts/2026-10-27-rpg-measure-cache-default-to-testing-planner.md`).
`tools/rpg_measure/` is rpg-owned since #759 merged (3b5fab1e9).

## Scope
- Replace the hardcoded fallback with a host-neutral one: `$RPG_MEASURE_CACHE` if set, else
  `$XDG_CACHE_HOME/rpg-measure` (else `~/.cache/rpg-measure`). Resolve it at call time, not import
  time, so tests can set the variable.
- When the chosen cache directory cannot be created or written, fail before any arm runs with one
  message that names `RPG_MEASURE_CACHE` and the path tried.
- u24 cache continuity: u24 seats keep their existing cached arms by setting
  `RPG_MEASURE_CACHE=/mnt/data/scratch-rpg-measure`. Say so in the `paired.py` module docstring and
  in `docs/observability/how_to_run_simulation.md` where paired runs are described (if they are).
- Unit tests: env set → used; env unset → XDG path; unwritable path → clear error, no arm started.

## Out of Scope
- `paired_arms.py` (it takes an explicit `--cache` and never reads `DEFAULT_CACHE`; T2 unaffected).
- Any change to cache keys, arm layout or report format. Existing cached arms must stay valid.
- A scheme-aware `paired` mode (separate, testing's).

## Acceptance Criteria
1. No host-specific absolute path remains in `tools/rpg_measure/`.
2. With `RPG_MEASURE_CACHE` unset and no `--cache`, `paired` uses the XDG/home cache path.
3. An unwritable cache gives a one-line error naming `RPG_MEASURE_CACHE` and the path, exit non-zero,
   before any child process starts.
4. Cache keys unchanged: a u24 run with `RPG_MEASURE_CACHE=/mnt/data/scratch-rpg-measure` hits the
   arms cached before the change (show one cache hit).
5. Tests in `tests/unit/` for the three cases pass.

## Related Tickets
- TCK-20261022-SESSION-ROLES-RPG-OWNS-RPG-MEASURE (#759, gives tools/rpg_measure to rpg)

## Related Docs
- docs/observability/how_to_run_simulation.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/rpg_measure/paired.py (DEFAULT_CACHE, line 48, and its readers)

## Assumptions / Open Questions
- Owner lane: offered to rpg-planner-ubuntu (the host that hits it). If ubuntu declines, a u24 rpg
  lane takes it after its current work. Not before the running step A R-only paired run on u24
  finishes: do not change the cache path under a live run.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
