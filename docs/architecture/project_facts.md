---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation]
---

# Project facts

Generated from commit `6822509a87495262766dcea2e93c10e1302269c0` by `tools/project_stats.py`. Do not edit by hand: a hand edit fails `--check`.
Regenerate with:

```
python3 tools/project_stats.py --write
python3 tools/project_stats.py --check
```

Counts are as of that commit, read from git objects, not from a working tree. Cite this page instead of re-deriving a number; the counting rule beside each count says what it includes, so a different number from a different method is a different rule, not a conflict.

## Code and tests

| What | Count | Counting rule |
|---|---|---|
| src modules | 844 | every `*.py` file under `src/` at the ref (a module is one file, `__init__.py` included) |
| src lines | 136190 | physical lines of those files, blank lines and comments included |
| test files | 2087 | every file named `test_*.py` under `tests/` |
| static test functions | 17854 | every `def test_*` found by `ast` in those files, methods and nested functions included; a parametrized test counts once, not per case; 0 file(s) did not parse and are not counted |

## Tickets and pull requests

| What | Count | Counting rule |
|---|---|---|
| tickets in todos/ | 157 | files named `TCK-*.md` anywhere under `agent-working/tickets/todos/` (epic folders included; SEQUENCE.md and INDEX.md are not tickets) |
| tickets in inprogress/ | 5 | files named `TCK-*.md` anywhere under `agent-working/tickets/inprogress/` (epic folders included; SEQUENCE.md and INDEX.md are not tickets) |
| tickets in done/ | 3097 | files named `TCK-*.md` anywhere under `agent-working/tickets/done/` (epic folders included; SEQUENCE.md and INDEX.md are not tickets) |
| merged PRs | 772 (first merge 2026-03-17, last 2026-11-14) | first-parent commits at the ref whose subject ends `(#N)` (squash merges); the dates are commit dates of the first and last such commit (2026-03-17 to 2026-11-14); a PR merged by another method is not counted |

## Agents and process

| What | Count | Counting rule |
|---|---|---|
| session roles | 32 | entries of `roles:` in `registries/session_roles.yaml` |
| session role cards | 32 | `.claude/agents/session-*.md` files (generated) |
| subagents | 16 | other `.claude/agents/*.md` files |
| skills | 23 | directories under `.claude/skills/` that hold a `SKILL.md` |
| hooks | 18 in 7 events | command entries under `hooks` in `.claude/settings.json`: ConfigChange 1, PostToolUse 5, PostToolUseFailure 1, PreToolUse 8, SessionStart 1, SubagentStop 1, UserPromptSubmit 1 |

## Parity ledger

| What | Count | Counting rule |
|---|---|---|
| ledger files | 9 | `docs/parity_ledger/*.yaml` |
| entries | 2307 | items of the top-level list in each `docs/parity_ledger/*.yaml` file (`schema.json` and `README.md` are not ledgers); one item is one entry |
| entries by status | divergent 30, legacy_verified 222, missing 29, unsupported 66, verified 1960 | the `status` of each entry |
| entries by priority | P0 1687, P1 422, P2 198 | the `priority` of each entry |
| entries by status/priority | divergent/P0 10, divergent/P1 14, divergent/P2 6, legacy_verified/P0 221, legacy_verified/P1 1, missing/P0 27, missing/P1 2, unsupported/P0 44, unsupported/P1 16, unsupported/P2 6, verified/P0 1385, verified/P1 389, verified/P2 186 | the pair `status/priority` of each entry |

## Import contracts

| What | Count | Counting rule |
|---|---|---|
| import contracts | 17 | entries of `tool.importlinter.contracts` in `codebase/structure/importlinter.toml` |
| baseline edges | 129 | non-blank, non-comment lines of `codebase/structure/import_layers_baseline.txt`; each is one accepted layer violation |

## Observability

| What | Count | Counting rule |
|---|---|---|
| metric families | 26 | distinct literal names (first argument) of `prometheus_client` constructor calls with a name and a documentation argument: `Counter`, `Gauge`, `Histogram`, `Summary`, `Info` and their `*MetricFamily` forms, found by `ast` in the `src/` files that mention `prometheus_client`; a name built at run time is not counted |
| alert rules | 11 | `groups[].rules[]` entries of `docker/grafana/provisioning/alerting/rules-*.yaml`: rules-base.yaml 6, rules-redis.yaml 1, rules-slo.yaml 2, rules-worker.yaml 2 |
