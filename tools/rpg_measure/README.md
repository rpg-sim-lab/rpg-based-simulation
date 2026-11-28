---
status: active
layer: testing
authority: P2
audience: agent
tags: []
---

# tools/rpg_measure

Tools for the paired-arm and own-job measurements the RPG track runs on frozen trees: `paired.py` (paired arms), `arm_child.py` (one arm, one run), `env_digest.py`
(the installed-distributions digest of the running interpreter), `stats.py`, and `kit_preflight.py` (below).

## Kit preflight (TCK-20261118-A-DIAGNOSTIC-KIT-PREFLIGHT-CHECKS-EACH-KIT-ON-BOTH-FROZEN-TREES-BEFORE-ITS-RUN)

Every measurement kit (spy, probe, runner, summarizer) is proven on BOTH frozen trees before its S9 run, by a short fixture run, and the table goes in the S9 packet.

```
python tools/rpg_measure/kit_preflight.py <kit>/manifest.json --tree <tree A> --tree <tree B> [--ticks 10] [--python /mnt/data/venv-sync2/bin/python] [--out preflight.md]
```

Exit 0 only when every check passed. The default interpreter is the run's own (`/mnt/data/venv-sync2/bin/python`); the table prints its env digest. The manifest is hand-written JSON
beside the kit (shape in the module docstring): each kit file with its sha256, each process's entry command (placeholders `{python} {tree} {world} {seed} {ticks} {out}
{file:NAME}`), the fixture, the output fields it records, the guard regexes, the hooks it claims, and optional `wraps` (wrapper vs target signatures).

| check | what it catches |
|---|---|
| a | a kit file missing or at another sha than the manifest names |
| b | a script that does not import with the run's interpreter flags, cwd = the tree (with `-I`, a missing `sys.path` fix; `-I` ignores `PYTHONPATH`) |
| c | the 5-10 tick fixture run does not exit 0 |
| d | a recorded field absent, or constant None/default over all entities and ticks (e.g. `navigation.failure_reason`, a field that does not exist), unless declared `may_be_constant` (listed in the table) |
| e | the ok guard line missing, a bad guard line present, ERROR+ log lines, a claimed hook never hit |
| f | a runner or shell file that invokes a `*.py` file that is not a manifest file with a sha (runner v2 calling `blocker_spy.py` while the S9 names v3b) |
| g | a wrapper whose parameters do not match its target's (`ctx` vs `context`, which a swallowed TypeError would hide as "not perceived") |
| h | a heavy kit python file whose name does not match the shared gate's `RPG_HEAVY_WORDS` (`lib/busy_gate.sh`), so other lanes' gates cannot see the job (a `_reader.py` near-miss) |
| i | informational: wall time and the 1-minute loadavg (before -> after) of each fixture run, so later perf reads do not come from file mtimes; always PASS |

### Manifest rules worth knowing

- A hook is `{"name", "count_path"}` or `{"name", "stdout_regex"}`. `count_path` is a dotted path into the output JSON (`a.b`, `[*]` over a list or a dict's values, `[0]` an index); the preflight SUMS the numeric values found (bools ignored) and the hook passes when the sum is at least 1. A path that is absent fails. A list of names (a `hook_coverage` block) is not countable: record a numeric counter in the output if a hook-hit check is wanted.
- Check (b) imports the kit file with the RUN's interpreter flags: the leading flags of the process's `entry` after `{python}`, or an explicit `import_flags` list. An entry with `-I` and no `sys.path` fix fails (b); an entry without `-I` (PYTHONPATH = the tree, as the runs set it) passes. A non-`{python}` entry keeps `-I`.
- Fixture runs use cwd = the tree, so a kit that writes `data/runs` writes into the frozen tree: the S9 `diff -rq` of the trees must exclude `data/runs`, or the preflight must report tree writes.

### The S9 packet line and the evidence labels

The S9 packet carries one line per kit: `Kit preflight: <PASS|FAIL>, manifest sha256 <..>, trees <A sha> <B sha>, interpreter env digest <..>, evidence: executed`, with the preflight table attached.
The preflight run itself is a small diagnostic run on the frozen trees and is recorded under its own S9 line.

Evidence labels, strongest last; a packet states which one each claim has:

- **inspected**: someone read the kit and found no fault (the designer's read). It proves nothing about what runs.
- **executable**: the kit imports and starts on the tree (checks a, b).
- **executed**: the preflight fixture run succeeded with live fields and clean guards on both trees (the whole table PASS). This is what the preflight prints.
- **validated**: the real run's output was checked against an independent source (a known count, a second method, or the unit tests that cover the same writers). A kit is never "validated" by its preflight alone.

### Host-gate hygiene for waiting shells

The shared gate (`lib/busy_gate.sh`) finds a heavy job by `pgrep -af "python.*(<heavy words>)"` plus a project path over the WHOLE command line. A waiting or launcher shell whose command line carries the kit words
(`_spy`, `_probe`, `pytest`, ...) and a project path therefore reads as a heavy job, blocks every other lane's gate and its own (a deadlock). Never self-queue behind the gate, and never put the kit
words on a launcher's command line: put the command in a script file and run that file, as the runners do. Run a heavy job only on the planner's explicit HOST FREE.

## Old names (renamed by owner direction #715 7181423761; no logic change)

The measurement kits and their tests were renamed so a file name says what it measures. The #715 records, the designers' reads and the kit directories under `/mnt/data2/rpg-measure` (sha-pinned evidence, not renamed) use the OLD names.

| old name | new name |
|---|---|
| `tools/rpg_measure/k2k3_count_{launch.sh,logic.py,spy.py,summary.py}` | `tools/rpg_measure/service_refusal_and_need_switch_count_*` |
| `tools/rpg_measure/k2fix_ownjob_{launch.sh,spy.py,summary.py}` | `tools/rpg_measure/inn_refusal_blocker_ownjob_*` |
| `tools/rpg_measure/k3_phase0_{launch.sh,spy.py,summary.py}` | `tools/rpg_measure/need_project_cleared_trace_*` |
| `tools/rpg_measure/k3_switch_{launch.sh,spy.py,summary.py}` | `tools/rpg_measure/escalated_need_switch_ownjob_*` |
| `tests/tools/test_k2k3_count_kit.py` | `tests/tools/test_service_refusal_and_need_switch_count_kit.py` |
| `tests/tools/test_k2fix_ownjob_kit.py` | `tests/tools/test_inn_refusal_blocker_ownjob_kit.py` |
| `tests/tools/test_k3_phase0_kit.py` | `tests/tools/test_need_project_cleared_trace_kit.py` |
| `tests/tools/test_k3_switch_kit.py` | `tests/tools/test_escalated_need_switch_ownjob_kit.py` |
| `tools/release/phase10_enhanced_rollout_gate.py` | `tools/release/rollout_report_gate.py` (class `RolloutGate` unchanged) |
| `tests/certification/test_phase10_enhanced_rollout_gate.py` | `tests/certification/test_rollout_report_gate.py` |

Kit directories on the host (unchanged, old names): `k2k3_kit_v5`/`v6`, `k2fix_ownjob_kit_v1`-`v3`, `k3_phase0_kit_v1`/`v2`, `k3_switch_kit_v1`-`v3`, and their output directories (`k3_phase0_out`, `k3_ownjob_*_out`, `k3_k6_neg_out`, `k2fix_*`). Closed tickets, stored artifacts, monitoring shards and archive docs keep the old names as history. `tests/tools/test_file_names_carry_meaning.py` fails on a new file whose name carries a bare internal code.


## Lesson (births own-job T0 STOP, 2026-11-28)
Kit unit tests take their input from a real compiled state (or the real canonical writer), never from a hand-built dict. The births T0 matcher passed its tests on a hand-written dict whose shape was assumed, and then stopped a real run because the canonical form puts `properties` at the entity level (`entities/<id>/properties/...`, written at `src/core/state.py:947`).
