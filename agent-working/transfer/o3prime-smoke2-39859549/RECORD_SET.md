# Stage-2 SMOKE record set (nothing run; needs lead's GO for THIS set)

Drafted by rpg-implementer-ubuntu, 2026-11-22, for rpg-planner-ubuntu. Kit branch `rpg-ubuntu-o3prime-q2-kit`, **head 39859549b250b9d9ddc6d555968f993a19ed23b4** (the launcher checks file sha256s, not HEAD; worktree clean at this head). Supersedes the bb32b19b2 stage-2 smoke set (void: its GO 7074481823 is void). Purpose (B6): a real-kernel run of the stage-2 subject trace on NEW s42 to **t2000**, which reaches the t1901 chain, to prove the per-tick rows, the legality wrapper (its tick from the context or world_time + offset, `offset_drift`), the per-tick motive reads and the stage-2 checks before the real stage 2.

## READ THIS FIRST: this smoke is a WIRING TEST ONLY
`SEALED` = `/data/vboxuser/o3-trace-runs/cd3a76430c63e12e45ffdfc4486c411861f304e5/run/cells`, the OLD O3 run (the person-only definition, rows only for person victims, label by the person flag, no motive inputs). The subject list below is derived from those OLD cells so that the smoke has subjects at all (stage 1 does not exist yet). **Nothing read from this smoke is evidence about O3'**; **the real stage 2 derives its subjects from the stage-1 SEALED cells** (the seal of THAT run is checked first: sha256(SHA256SUMS) must equal its SEAL line, and its `kit_sha256_after_run.txt` must name the stage-1 spy; the cd3a76430 run's seal was checked read-only and matches 336487df...; the after-run spy assert is skipped for a smoke).

## What runs: 2 processes, ONE AT A TIME, each in its own scope
NEW 87792e3e8, frontier_living_world, seed 42, **2000 ticks**: the PLAIN twin, then the SPY (the spy wraps the apply path and `LegalityServiceV2.verify_attack_legality`; same scope, cores, watcher, TMPDIR, env and freeze checks as stage 1). No sealed 2000t twin exists, so the smoke compares its own plain and spy hashes (**read the hashes FIRST; if they differ, stop and read nothing else**: the per-tick motive reads call `relation()`, which reaches the perception gate). BASE does not run in the smoke.
Preflight, in this order: the stage-1 seal check (`seal-check`), `sha256sum -c` of the sealed set, trees, freeze, the kit file shas, heavy-job check, MemAvailable, the disk floor; then `subjects.json` is derived, written and hashed (`subjects.json.sha256`) before the first process.
Files here: `record.env`, `dry_run.txt`, `derived_preview.txt`, this file. OUT = `/data/vboxuser/o3-trace-runs/39859549b250b9d9ddc6d555968f993a19ed23b4/smoke2/smoke` (does not exist; created by the launcher; sealed LAST; nothing deleted).

## The subject list and windows (read-only preview of `derive_subjects` on the sealed cd3a76430 NEW spy cells, now with EVERY qualifying chain; the launcher derives the same into subjects.json; the smoke uses seed 42's list)
- seed 42: **30** (chain_victim, victim) window **[1801, 2710]**, counterparts 46, 47, 49; **46** (attacker) [1801, 2710]; **47** (attacker) [1801, 2062]; **49** (attacker) [1801, 2062]. At 2000t only the part of each window up to tick 2000 is traced (the t1901 chain is inside it).
- seed 45 (derived, not run in the smoke): 30 [[2896, 3572], [3635, 4055], [4670, 4954]], counterparts 45, 46, 47, 49; 45 [3646, 3904]; 46 [3635, 4055]; 47 [3196, 3450]; 49 [2896, 3572] and [4670, 4954].
(`derived_preview.txt` has the full output; seed 45 has more windows than in the bb32b19b2 preview because every qualifying chain is now listed, not only the worst per victim.)

## Launch
`setsid /data/vboxuser/Work/rpg-based-simulation/.claude/worktrees/rpg-ubuntu-o3-trace/tools/rpg_measure/subject_trace_launch.sh /data/vboxuser/o3-trace-runs/39859549b250b9d9ddc6d555968f993a19ed23b4/smoke2/record.env <GO id> smoke >/dev/null 2>&1 &`
Before launch: MemAvailable >= 3 GiB, no other heavy job, the kit worktree clean at 39859549b250b9d9ddc6d555968f993a19ed23b4, nothing committed in it while it runs; PYTHONDONTWRITEBYTECODE=1 for anything that touches a frozen tree.

## Expected wall time and RSS
The O3 run took 225-236 s for NEW s42 at 5000t (plain / spy), so 2000t is about 90-100 s per process: about 3.5 to 4 minutes in all with the checks. Peak RSS: no reading exists above 300t (89-90 MB there); the 3 GiB scope and the 2.85 GiB watcher bound it, and neither fired in the 5000t O3 run. The spy adds rows only for 4 subjects in their windows (plus the motive reads for each counterpart per tick), so no large growth is expected.

## Stop rules (nothing is retried or deleted)
Preflight abort (stage-1 seal mismatch, tree, freeze, kit sha, heavy job, memory, disk); disk floor before each process; freeze change (void); a return code outside {0, 8} stops the run (8 = a spy exception: the cell is void); the first process over 25 min and the run over 2 h, both **checked only after a process ends**. A `runner.json` that cannot be written makes the run non-COMPLETE (RECORD_NOT_WRITTEN, RC 6). Suggested manual hard stop: 15 minutes after RUN START.

## What the smoke reads, in this order
1. the twin hashes (plain vs spy); stop here if they differ. 2. `subjects.json` and its sha; `cells/new__frontier_living_world__s42__spy.json`: row_count, legality_call_count, legality_calls_in_window, legality_calls_unplaced, offsets_seen and offset_drift, tick_source on the legality rows (does combat_actions.py:56 give "world_time+offset"?), the rows at t1901.. (mode, task/reason, navigation.target, failure_reason, readiness, hp and state ALIVE/DEAD/ABSENT, positions, distances, motive_reads), spy_exceptions (must be empty). 3. `runner.json`; `launcher.log`. The cell check against sealed plain twins (`check`) does not run in smoke mode.
