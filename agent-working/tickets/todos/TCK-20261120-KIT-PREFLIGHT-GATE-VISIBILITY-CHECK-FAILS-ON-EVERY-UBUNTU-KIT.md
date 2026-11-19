---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261120-KIT-PREFLIGHT-GATE-VISIBILITY-CHECK-FAILS-ON-EVERY-UBUNTU-KIT
phase: open
date: 2026-11-20
tags: []
---

# TCK-20261120-KIT-PREFLIGHT-GATE-VISIBILITY-CHECK-FAILS-ON-EVERY-UBUNTU-KIT

## Title
`kit_preflight.py` check (h) "gate visibility" always FAILs on the ubuntu host, the births kit names miss the gate's heavy words, and check (f) "runner refs" fails on prose naming a .py file

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Finding from rpg-planner-ubuntu, found while preparing the births re-check S9; lead-planner routed it here (#715 7016065680). Filed by testing-planner.

1. `tools/rpg_measure/kit_preflight.py` check (h) (lines 100-124) reads `RPG_HEAVY_WORDS` from `DEFAULT_BUSY_GATE = /mnt/data2/rpg-measure/lib/busy_gate.sh`. That path does not exist on the ubuntu host (checked: `ls` fails, host `ubuntu`), so `heavy_words()` returns None and (h) always emits `FAIL "RPG_HEAVY_WORDS could not be read"`. The tool then exits 1 for every kit on ubuntu. The other default, `DEFAULT_PYTHON = /mnt/data/venv-sync2/bin/python` (line 47), is also u24-only and also missing here.
2. Where the gate does exist, the births/coin_boss kit names do not match its pattern. The stored u24 copies (`agent-working/stored_artifacts/TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC/m1base_scripts/busy_gate.sh` line 7, and `busy_gate_v2.sh` line 10) carry `RPG_HEAVY_WORDS='arm_child|d1_own_job_spy|hold_spy|tally_spy|v3_trace|d1_step0|pytest|run_cells|paired\.py|smoke_wrapcount|dying_window'` (v2 adds `keep_events_child`). None of births_child, births_cost_child, births_obs_check, births_run, births_spy, coin_boss_spy/run/summary matches, though the preflight docstring says a `_spy` name makes a kit visible (the pattern has `hold_spy`, `tally_spy`, `d1_own_job_spy`, not a bare `_spy`). Reported by rpg-planner-ubuntu; the pattern text above is read from the stored copies.
3. ubuntu has no shared busy gate at all; kits on this host rely on their own "no other heavy process" checks (reported, not checked here).

4. A second defect, check (f) "runner refs" (added at rpg-planner-ubuntu's request; lead ruled the births case on #715 7016065680 and its amendment). `check_runner_references` (`kit_preflight.py` lines 81-94) scans every line of a runner or `.sh` file that does not start with `#` (read here), and `_PY_TOKEN` matches any `*.py` text. Prose that names a .py file therefore fails the row though it is not an invocation. Births examples at d3401ba43 (reported, not read here): `tools/rpg_measure/births_run.py:59`, a string literal describing the patch target `src/world/risen.py`; `births_obs_check.py:5`, the module docstring naming `src/observability/config.py`. Neither is an invocation.

Lead's ruling for the births cell (#715 7016065680): run the preflight unchanged, accept only the (h)-row FAIL as a logged override, and require checks a-g to PASS. That stands until this ticket lands.

## Scope
RULING (rpg-planner, via lead-planner-u24 and lead-planner, 2026-11-20): the interim stands (a-g pass; (h) an honest FAIL plus a logged override). The fix must NOT be plain option A: "not applicable" must never be inferred from a missing gate file, or a host that lost its gate would pass silently. Required shape:
1. The gate script path, the python and the heavy-word list are host-configured (an env var or a per-host config file the kit reads), with no `/mnt/data*` default in code.
2. (h) reports N/A only when that config explicitly declares "no gate on this host". If the config names a gate and the file is missing or has no pattern, (h) still FAILs. No config at all FAILs (it is not read as "no gate").
3. The births/coin_boss kit names are added to the heavy words, or the check matches by a stated kit-name pattern (a suffix or prefix rule, not a list of past kit names; the docstring says which).
4. (f) matches only invocation forms (argv elements, `-m` modules, subprocess argument lists), not docstrings, comments or string literals that merely describe a file.
Timing: after #781's own-job on u24. It may be built sooner on ubuntu under these conditions. rpg-planner reviews the diff.

Options A to D considered before the ruling (kept for the record): (A) N/A when no gate exists, rejected as stated; (B) per-host defaults, adopted as item 1; (C) an ubuntu `busy_gate.sh`, not required; (D) kit naming or pattern, adopted as item 3.

Tests: a docstring or string literal naming a .py file does not fail (f); an invocation of a .py file that is not in the manifest still does; "config declares no gate" gives N/A; "config names a gate, file missing" FAILs; "no config" FAILs; a heavy kit name matching none of the words FAILs on a host with a gate.

## Out of Scope
- Changing a-g, or letting a real FAIL in another check pass.
- Running any measurement kit or heavy run.
- Editing the stored u24 copies of `busy_gate.sh`.
- The births kit itself.

## Acceptance Criteria
1. On the ubuntu host, with a config that explicitly declares "no gate on this host", a kit that passes a-g exits 0 and its (h) row says so. A missing gate file or a missing config never yields N/A.
2. On a host with a gate, a heavy kit file whose name matches none of the gate's words still FAILs (a test pins it).
3. The `--python` and gate-path defaults are not tied to `/mnt/data*` mounts; an unusable default fails early with a message naming the flag.
4. The docstring states what name pattern is accepted, matching the code.
5. Check (f) passes on the births kit (`births_run.py`, `births_obs_check.py`) and still FAILs on a real unlisted invocation; a test pins both.
6. The births/coin_boss kit names are checked against the new behaviour and the result recorded here (pass, or the rename needed).

## Related Tickets
- TCK-20261118-A-DIAGNOSTIC-KIT-PREFLIGHT-CHECKS-EACH-KIT-ON-BOTH-FROZEN-TREES-BEFORE-ITS-RUN (the preflight this fixes)
- TCK-20261027-RPG-MEASURE-CACHE-DEFAULT-HOST-NEUTRAL (host-neutral defaults precedent)
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND (the births cell that hit it)

## Related Docs
- #715 7016065680 (lead ruling: run unchanged, log the (h) FAIL as an override).

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC/m1base_scripts/busy_gate.sh`, `busy_gate_v2.sh` (u24 copies).

## Related Code Areas
- `tools/rpg_measure/kit_preflight.py` (`DEFAULT_PYTHON`, `DEFAULT_BUSY_GATE`, `heavy_words`, `check_gate_visibility`, `_PY_TOKEN`, `check_runner_references`)

## Assumptions / Open Questions
- Routing: rpg-planner-ubuntu will take it once it is on main (tools/rpg_measure is rpg's lane). `python3 -m tools.sessions.route` returns `rpg-planner` for `tools/rpg_measure/**`; this is not a testing-owned path. Filed on the testing track at lead-planner's routing; the implementation seat is rpg-planner's call.
- Settled by the ruling above: no inferring N/A from absence. Whether ubuntu also gets a shared gate (C) stays open and is not required.
- Items 2 and 3 of the request summary come from rpg-planner-ubuntu; item 1 was reproduced by reading the code and checking the paths on this host.

## Durable state, lifecycle and clocks
None: a measurement-tool check.

## Implementation Notes
Filing only.

## Test Summary
Not applicable.

## Files Changed
This ticket only.

## Completion Summary
Open.
