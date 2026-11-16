---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS
artifact_type: investigation
tags: [ai, agent-monitoring]
---

# Investigation — TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS

## Were the 57 failures and 7 errors environmental?

Yes, and that part is confirmed: the same tests passed capped, with no ENOMEM. Why the environment refused the allocations is open (below). Evidence, all in the vehicle's Test Summary (`agent-working/tickets/done/TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT.md`) and its capped confirmation:

- The native Test phase ran `python3 -m pytest tests/tools/ -m "not slow and not extra_slow" -q --tb=line -rf -p no:cacheprovider`: one process, no `-n`, no memory cap, no CPU pinning. It reported 1 real failure plus 57 failures and 7 errors, all `OSError: Cannot allocate memory` in subprocesses, and a pytest `MemoryError` INTERNALERROR on a first attempt.
- The same tests, run capped (`systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`, `-n 0`, the CI marker filter) as the 59 failing node ids and then as six chunks of `tests/tools`, gave 6,025 passed, no ENOMEM and no MemoryError in any log. The only failures were registry drift on an uncommitted branch and one flake that passed alone.
- A 5 s MemAvailable watcher never saw less than 3.71 GB, yet the Test agent saw ENOMEM at about 1.8 GB free; Committed_AS (13.4-14.8 GB) sat above CommitLimit (13.48 GB). **The mechanism is not established.** Under `vm.overcommit_memory=0` the kernel (upstream v6.17) never compares Committed_AS with CommitLimit, and a 99-test rerun also hit the ENOMEM while a 4,300-test single process ran clean under the cap. So neither commit pressure nor "one uncapped process" is shown to be the cause; what is shown is that the same tests, run capped and chunked, did not fail. See TCK-20261116-UBUNTU-COMMITTED-MEMORY-OVER-COMMIT-LIMIT.

## How the Test phase works now

The test-scoper is an LLM agent that builds and runs pytest itself. `.claude/workflows/implement-ticket.js` cannot run pytest: it injects the floor of bare directories into the prompt, re-checks the returned command string with `test_scope_coverage_static`, and maps `passed=false` to `TESTS_FAILED`. Nothing distinguishes a test that failed from a run that died of the environment.

## Design (option C, ruled by agent-working-planner)

A repo helper `tools/delivery/capped_pytest.py` that takes the same bare directories the floor requires and (1) reads the host cap from `registries/session_test_caps.yaml`, (2) collects with `--collect-only` and chunks by test file into deterministic groups sized by a tests-per-chunk cap in that config, (3) runs each chunk under the cap, summing counts, (4) classifies environment signals and never retries, and (5) emits one JSON result including `environment_failure`. A host with no entry runs unwrapped. `test_scope_coverage_static` rejects a command that bypasses the helper on a host that has an entry. The workflow gets one schema field and one branch (`TESTS_ENVIRONMENT_FAILED`).
