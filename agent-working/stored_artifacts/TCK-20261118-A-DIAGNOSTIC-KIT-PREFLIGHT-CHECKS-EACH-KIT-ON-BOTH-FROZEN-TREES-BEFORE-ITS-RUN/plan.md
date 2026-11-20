---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261118-A-DIAGNOSTIC-KIT-PREFLIGHT-CHECKS-EACH-KIT-ON-BOTH-FROZEN-TREES-BEFORE-ITS-RUN
artifact_type: plan
tags: []
---

# Plan: kit preflight

1. `tools/rpg_measure/kit_preflight.py` (stdlib only): hand-written JSON manifest; checks (a) sha, (b) import under `python -I` with cwd = the tree (top-level statements up to the last import, so script-style kits are checked without running them), (c) fixture run rc 0, (d) field liveness (constant None/default fails unless `may_be_constant`), (e) guards, ERROR+ log lines, hooks, (f) runner `*.py` references must be manifest files, (g) wrapper vs target signature (wrapper read from its AST), (h) heavy kit file names must match the shared gate's `RPG_HEAVY_WORDS`.
2. Interpreter default `/mnt/data/venv-sync2/bin/python`; env digest printed with `env_digest.py` run under that interpreter.
3. Tests: synthetic trees and kits in tmp_path, one per fault class, no frozen tree.
4. README with the S9 packet line and the evidence labels. Real manifests live beside each kit outside the repo.
Out of scope: judging a kit's design; runs longer than the fixture.
