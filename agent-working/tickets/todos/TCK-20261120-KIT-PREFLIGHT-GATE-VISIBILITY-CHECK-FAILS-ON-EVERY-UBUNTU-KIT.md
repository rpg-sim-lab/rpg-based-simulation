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
`kit_preflight.py` check (h) "gate visibility" always FAILs on the ubuntu host, and the births kit names do not match the gate's heavy words even where the gate exists

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

Lead's ruling for the births cell (#715 7016065680): run the preflight unchanged, accept only the (h)-row FAIL as a logged override, and require checks a-g to PASS. That stands until this ticket lands.

## Scope
Choose one fix (or a combination) and say why. Candidates from the finding:
- (A) (h) reports "not applicable" (not FAIL) when no busy gate exists on the host, and says so in the table. Smallest change; leaves cross-lane visibility unchecked on ubuntu.
- (B) a per-host default for the gate path and the interpreter (env var or `--heavy-words` default per host), so the check runs against the host's own gate.
- (C) an ubuntu `busy_gate.sh` that exists and that kits are checked against. Larger; creates a new shared gate.
- (D) kit naming that matches the pattern, or a pattern that matches a stated naming rule (a suffix, not a list of past kit names), plus the docstring corrected to what the pattern really matches.

Whatever is chosen: the defaults must not be hard-coded to one host's mounts (precedent: TCK-20261027-RPG-MEASURE-CACHE-DEFAULT-HOST-NEUTRAL); `--python` default must work or fail early with a clear message on both hosts; a test covers "gate file absent" and "kit name not matching" so neither silently passes or always fails.

## Out of Scope
- Changing a-g, or letting a real FAIL in another check pass.
- Running any measurement kit or heavy run.
- Editing the stored u24 copies of `busy_gate.sh`.
- The births kit itself.

## Acceptance Criteria
1. On the ubuntu host a kit that passes a-g exits 0 (or its (h) row states "not applicable: no gate on this host" and does not count as a FAIL), with no `--heavy-words` flag.
2. On a host with a gate, a heavy kit file whose name matches none of the gate's words still FAILs (a test pins it).
3. The `--python` and gate-path defaults are not tied to `/mnt/data*` mounts; an unusable default fails early with a message naming the flag.
4. The docstring states what name pattern is accepted, matching the code.
5. The births/coin_boss kit names are checked against the new behaviour and the result recorded here (pass, or the rename needed).

## Related Tickets
- TCK-20261118-A-DIAGNOSTIC-KIT-PREFLIGHT-CHECKS-EACH-KIT-ON-BOTH-FROZEN-TREES-BEFORE-ITS-RUN (the preflight this fixes)
- TCK-20261027-RPG-MEASURE-CACHE-DEFAULT-HOST-NEUTRAL (host-neutral defaults precedent)
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND (the births cell that hit it)

## Related Docs
- #715 7016065680 (lead ruling: run unchanged, log the (h) FAIL as an override).

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC/m1base_scripts/busy_gate.sh`, `busy_gate_v2.sh` (u24 copies).

## Related Code Areas
- `tools/rpg_measure/kit_preflight.py` (`DEFAULT_PYTHON`, `DEFAULT_BUSY_GATE`, `heavy_words`, `check_gate_visibility`)

## Assumptions / Open Questions
- Routing: `python3 -m tools.sessions.route` returns `rpg-planner` for `tools/rpg_measure/**`; this is not a testing-owned path. Filed on the testing track at lead-planner's routing; the implementation seat is rpg-planner's call.
- Whether ubuntu should get a shared gate (C) or only an honest "not applicable" (A) is an owner/lead decision; no recommendation beyond: A now (unblocks every ubuntu kit), D's docstring fix with it, and B/C only if cross-lane visibility on ubuntu is wanted.
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
