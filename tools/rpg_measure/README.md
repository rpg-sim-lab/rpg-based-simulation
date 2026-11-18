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
| b | a script that does not import under `python -I`, cwd = the tree (a missing `sys.path` fix; `-I` ignores `PYTHONPATH`) |
| c | the 5-10 tick fixture run does not exit 0 |
| d | a recorded field absent, or constant None/default over all entities and ticks (e.g. `navigation.failure_reason`, a field that does not exist), unless declared `may_be_constant` (listed in the table) |
| e | the ok guard line missing, a bad guard line present, ERROR+ log lines, a claimed hook never hit |
| f | a runner or shell file that invokes a `*.py` file that is not a manifest file with a sha (runner v2 calling `blocker_spy.py` while the S9 names v3b) |
| g | a wrapper whose parameters do not match its target's (`ctx` vs `context`, which a swallowed TypeError would hide as "not perceived") |
| h | a heavy kit python file whose name does not match the shared gate's `RPG_HEAVY_WORDS` (`lib/busy_gate.sh`), so other lanes' gates cannot see the job (a `_reader.py` near-miss) |

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
