---
status: active
layer: ticket
authority: P2
audience: agent
phase: inprogress
ticket_id: TCK-20261115-PROJECT-SYNC-ALL-LANES
artifact_type: test_plan
tags: [planning, delivery]
---

# Test plan

No network. Files: tests/tools/test_session_project_sync.py (+ _second_host), tests/tools/test_project_client.py. About 14-16 tests:
1. Lanes come from the roster (9) and a ticket on a branch of any registered domain is a candidate; `pilot_lanes` ignored.
2. Main-only todos/inprogress tickets become To do items; main-only Done tickets with no item do not.
3. Main-only Domain: a host segment's domain wins; else the single domain every routed Related-Code-Areas path gives (unowned skipped); else `unassigned` when they disagree, none route or there is no path token; never from `layer`.
4. `attribute()`: `agent-working-x` gives agent-working, `rpg-planner-seat-8` gives rpg, `foo-bar` gives unknown/unknown, a recorded seat wins, longest prefix wins.
5. Domain is a single-select: a value without an option is a finding and the field stays empty; two disagreeing domains give the sorted-first plus a finding.
6. `--init`: renames TEXT Domain to `Domain (old)` and creates the single-select with domains + unassigned + unknown; a second `--init` is "left alone"; both-exist refuses with nothing written; never a delete.
7. Epic (a) through origin's path for a branch copy under inprogress/.
8. `--fetch` success, failure and timeout (failure/timeout: carries on, finding, origin/main age printed; 60 s timeout).
9. Last-run file written on `--apply` and not on a dry run; mode 600; write failure does not fail the run.
10. `failed_streak` and the start-hook line: warns at 2 failures, silent at 1, silent when the file is absent or unreadable.
11. Heartbeat: `--apply` rewrites only its own segment; created when absent; written even when the plan was empty; written with rc=1 after a stop.
12. Stale-host flag: another host older than `stale_host_hours` is reported; Status untouched; own host never flagged.
13. The heartbeat item is never archived and never counted as a ticket, even with no Ticket ID. Two heartbeats: segments read from both, own segment written to the first, a finding names the extra, nothing archived. A failed heartbeat write leaves rc and the first error unchanged: plan steps stop, heartbeat raises, rc=1, the last-run file is still written, `heartbeat: not written (...)` printed; the heartbeat is a single attempt (no retry sleeps).
14. Convergence A→B→A with all lanes: two hosts' runs reach a fixed point (nothing to do).
Run: `pytest tests/tools/test_session_project_sync.py tests/tools/test_session_project_sync_second_host.py tests/tools/test_project_client.py tests/tools/test_session_status.py -p no:randomly` (scoped, TMPDIR + --basetemp), never the full suite.
15. Rename fixture (A): items have `Domain (old)` set and `Domain` empty; the run reports no hand edits and plans Domain updates only.
