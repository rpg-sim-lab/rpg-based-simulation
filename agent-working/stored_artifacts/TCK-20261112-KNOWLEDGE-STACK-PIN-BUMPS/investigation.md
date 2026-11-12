---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261112-KNOWLEDGE-STACK-PIN-BUMPS
artifact_type: investigation
tags: [knowledge-store, setup]
---

# Investigation

- Source: Dependabot #882 (closed unmerged) bumped the three pins with no checks, dropped torch's `+cpu` label (a PyPI install would pull CUDA wheels) and failed `TestRequirementsPin`. Owner decision #715 6812820923.
- Pin sites: `requirements-knowledge.txt` (torch 2.13.0+cpu, graphifyy 0.9.70, headroom-ai 0.37.0), `tests/tools/test_code_test_index.py::TestRequirementsPin`, `tests/tools/test_graphify_shim.py` (`PIN = "0.9.70"`), the dated pin paragraph in `docs/guidelines/agent_working_environment.md`.
- Disk at start (2026-11-12): / 8.1G free, /data 16G free (above the 10 GB stop line).
- Prior procedure: TCK-20261024-KNOWLEDGE-STACK-SECURITY-BUMPS and TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR (same eval and five spot queries).
- Findings are appended here as the smoke tests run.

## Baseline (heavy run #1, 2026-11-12, current pins: torch 2.13.0+cpu, graphifyy 0.9.70, headroom-ai 0.37.0)

- Scratch tree `/data/vboxuser/aw-pinbump-scratch` = `git archive HEAD` (331M), built with the main `.venv-knowledge`, detached under the 3G wrapper on cores 4-5. Start 09:52:11, build rc 0 at 10:02:14 (10 min, 17407 documents), eval rc 1 at 10:07:19 (the exit code is the Recall@5 threshold, below), spot queries rc 0 at 10:07:44.
- `eval_search.py` ran from the scratch tree: its db path is `_REPO_ROOT / KNOWLEDGE_INDEX / knowledge.db`, `_REPO_ROOT` being the scratch tree, and its report landed in the scratch `reports/`.
- Eval (61 queries, 54 with expected): Recall@5 0.41, Recall@10 0.65, MRR@10 0.27, zero-result 0, avg duplicate rate 0.09. The 0.80 threshold line says FAIL; this is the baseline for this scratch corpus, not a regression. The candidate must not be lower.
- Spot queries print "knowledge index is stale: 0 changed, 4877 new, 4877 removed" for a fresh scratch build (scratch paths vs manifest); it applies to both sides. Baseline top-5 per query is in the run's `spot.log` (kept with the baseline db at `/data/vboxuser/aw-pinbump-keep/baseline.db`, 55M).
- Why 0.41 is low (so it is not read as a regression): of the 60 expected doc ids in `tools/eval/queries.json`, 51 are absent as exact ids from the freshly built index, and 45 of the 54 queries with expected ids have none of theirs present. For example `mechanics/02_combat_laws` is expected, while the index holds chunk ids such as `mechanics/02_combat_laws#1-the-damage-formula-001`. So the low score comes from the expected set against the index's id shape, not from the scratch tree, and the candidate is graded against the same baseline.

## Candidate (heavy run #3, 2026-11-12; torch 2.15.0+cpu, graphifyy 0.9.104, headroom-ai 0.43.1; sentence-transformers 6.1.0, sqlite-vec 0.1.9, rank-bm25 0.2.2, mcp 1.30.0 unchanged)

Throwaway venv `/data/vboxuser/aw-pinbump-venv` (built in run #2: all rc 0, 1.9G, `pip list` shows torch 2.15.0+cpu and no nvidia or triton package). Same scratch tree, baseline index moved aside. Start 10:13:23, build rc 0 at 10:24:59 (11.6 min), eval rc 1 at 10:30:28 (the 0.80 threshold line, same as baseline), spot queries rc 0 at 10:30:54.

| | Baseline (torch 2.13.0+cpu) | Candidate (torch 2.15.0+cpu) |
|---|---|---|
| Documents embedded | 17407 | 17407 |
| Recall@5 | 0.4074 | 0.4074 |
| Recall@10 | 0.6481 | 0.6481 |
| MRR@10 | 0.2741 | 0.2741 |
| Zero-result | 0 | 0 |
| Avg duplicate rate | 0.0852 | 0.0852 |

The two per-query reports differ only in the order of two ids inside five `expected` lists (set serialization); every metric field is equal. The five spot queries return identical top-5 lists, top-1 included, in both runs. Decision for torch: metrics are not lower and the spot checks match, so 2.15.0+cpu is taken.

## graphifyy 0.9.104 smoke (heavy run #4, 2026-11-12; scratch copy only)

- Run: throwaway venv's `bin/graphify` by absolute path, in `/data/vboxuser/aw-pinbump-scratch` on a copy of the shared `graphify-out` (built by 0.9.70; `graph.json` 98.5 MB). Start 10:35:26, `graphify update .` rc 0 in 411 s, `graphify query` rc 0 before and after. The shared `graphify-out` was only read for the copy; its `graph.json` mtime is unchanged (2026-10-29).
- Counts: before 58782 nodes / 168594 edges; after 67552 nodes / 193368 edges. The tree differs (the scratch tree is HEAD, the shared graph was last built 2026-10-29), so the counts are not a version effect on their own. Node ids: 57651 of 58781 old ids survive the update (ids are stable across 0.9.70 -> 0.9.104 for the same files).
- Format: `graph.json` keys are the same set, except that the 0.9.70 file carries `built_at_commit` and the rebuilt file does not. The node-link shape (`nodes`, `links`, `hyperedges`) is unchanged and `graphify query` output has the same shape. The update also printed: a `tree_sitter_hcl not installed` warning for `.tf` and `.hcl` files (the optional `graphifyy[terraform]` extra, not installed), a note that 458 community labels were renamed because the community set changed, and that it backed up the curated graph before writing.
- Side effect to report: the 0.9.104 CLI auto-refreshed the user-scope skill copies at `~/.claude/skills/graphify` and `~/.agents/skills/graphify` (0.6.7 -> 0.9.104, `SKILL.md.bak` kept) on its first command. `GRAPHIFY_NO_AUTO_REFRESH=1` disables this and must be set for every later 0.9.104 call.

## The graphify skill auto-refresh and its restore (owner decision #715 6813744774, "Restore the .bak copies (Recommended)")

- What happened: the first 0.9.104 CLI command (10:12, `graphify --version` in the throwaway venv; again at 10:35 in the smoke) rewrote the user-scope skill copies `~/.claude/skills/graphify` and `~/.agents/skills/graphify` from 0.6.7 to 0.9.104, kept the old text as `SKILL.md.bak`, set `.graphify_version` to `0.9.104` and wrote a new `references/` folder (8 files, all mtime 10:12:10). I did not set `GRAPHIFY_NO_AUTO_REFRESH=1`, although the earlier version warning named those paths. That was my slip. Nothing in the repo or the shared `graphify-out` was touched.
- Evidence that `references/` was created by the refresh, not restored from before: `SKILL.md.bak` (0.6.7 text) mentions no `references/` file, and the untouched 0.6.7 copy at `~/.copilot/skills/graphify` holds only `SKILL.md` and a 5-byte `.graphify_version`.
- Before: both folders held the 0.9.104 `SKILL.md` (md5 7c3c8af4... for `.claude`, cb706f81... for `.agents`), `.graphify_version` = `0.9.104`, `SKILL.md.bak` (md5 aa061fb0...), and `references/`.
- Restore (10:44): `SKILL.md.bak` moved back over `SKILL.md` (md5 aa061fb0... in both, 63823 bytes, original mtimes kept), `.graphify_version` rewritten to `0.6.7` (5 bytes), `references/` and the refreshed `SKILL.md` moved, not deleted, to `/data/vboxuser/aw-pinbump-keep/refreshed-{claude,agents}-*`. After: each folder lists `.graphify_version` and `SKILL.md` only; `head -3 SKILL.md` shows the original `description: "any input (code, docs, papers, ...`. The shipped graphify CLI on PATH reports its package as 0.9.70 and no longer warns about these two folders.
- Every later 0.9.104 call sets `GRAPHIFY_NO_AUTO_REFRESH=1`.

## headroom-ai 0.43.1 smoke: FAILED

- Run (10:44:46): `tools/start_headroom_mcp.sh` with `KNOWLEDGE_PYTHON` on the throwaway venv and `HEADROOM_WORKSPACE_DIR` in the scratch tree, driven by an mcp stdio client. The server exited at start: `TypeError: Server.__init__() got an unexpected keyword argument 'on_list_tools'` (`headroom/ccr/mcp_server.py:495`), so the client saw "Connection closed" and no tool list. `~/.headroom` was not created, `.mcp.json` and `~/.claude.json` untouched.
- Cause: headroom-ai 0.43.1 declares `mcp>=2.2.0,<3.0.0` for its MCP server (0.37.0 declares `mcp>=1.28.1,<2.0.0`). This repo pins `mcp==1.30.0` because `tools/search_mcp.py` is on the 1.x API (see `requirements-knowledge.txt`), so the new headroom cannot serve MCP in the same venv. Moving to mcp 2.x is the major-version change the ticket puts out of scope.
- Decision: headroom-ai stays at 0.37.0 (smoke failed, per Scope 6). graphifyy 0.9.104 and torch 2.15.0+cpu are taken. A headroom version that works with mcp 1.x, if one exists, was not looked for (past the named targets).

## Main-venv rebuild (step 7; owner yes #715 6813901686, lead slot go; 2026-11-12)

- Old main index copied to `/data/vboxuser/aw-pinbump-keep/main-index-before` first (127M). The main `.venv-knowledge` has no `pip`, so the install used `uv pip install --python .venv-knowledge/bin/python3 "torch==2.15.0+cpu" "graphifyy==0.9.104" --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple --index-strategy unsafe-best-match`, UV cache and TMPDIR on /data, under the 3G wrapper. A dry run showed only those two packages changing; the install took 29 s (10:53:42 to 10:54:11). Result: torch 2.15.0+cpu, graphifyy 0.9.104, mcp 1.30.0, headroom-ai 0.37.0, no nvidia package.
- The shared `search_shared.py` (pid 43022 when lead looked) had already exited when I went to stop it; nothing was stopped. Per-seat `search_mcp` children were not touched.
- `graphify install --platform claude` and `--platform agents` run deliberately (owner choice "Yes, and refresh the graphify skill too"): both skill folders are back at 0.9.104 with `references/`; `SKILL.md.bak` copies stay. Side effect not named in the approval: `~/.claude/CLAUDE.md` changed on disk during these installs (the graphify section's third line now reads "use the installed graphify skill or instructions before doing anything else"); I did not edit it and left it as is.
- Full index rebuild in the main checkout, 3G wrapper, detached: start 10:54:54, rc 0 at 11:07:33, 16795 documents.
- AC4: `tools/knowledge_search.py query "mechanics damage formula"` from the main checkout under the new venv returns the combat-laws chunk; the headroom MCP (0.37.0) started through `tools/start_headroom_mcp.sh` (the `.mcp.json` command) listed `headroom_compress`, `headroom_retrieve`, `headroom_stats` and answered `headroom_stats`, with `HEADROOM_WORKSPACE_DIR` in the scratch tree and no `~/.headroom` created. The `search_docs` MCP tool in the agent-working seat answers "index not found" for a different reason (lead-planner, owner yes #715 6813678492): lead deleted this worktree's own knowledge-index at about 10:40, and `search_mcp` resolves its index path once at startup, so this seat's running server still points at the deleted path; a `/mcp` reconnect or the next restart reads the main checkout's index. From lead's main-checkout seat, `search_docs` answers on the new index. The 16795 documents come from the main checkout's tree, which is far behind origin/main; the scratch tree (HEAD of this branch) had 17407, so the two counts are not comparable.

## Owner decisions after step 7 (#715 6814303604, 2026-11-12)

- `~/.claude/CLAUDE.md` line 3, rewritten by `graphify install`: KEPT ("Keep the new line (Recommended)").
- Scratch cleanup: "Delete all six (Recommended)". lead-planner deleted `/data/vboxuser/aw-pinbump-venv` (1.9G), `-pipcache` (1.2G), `-scratch` (1.1G), `-baseline-index` (132M), `-tmp` and `-keep` (180M) after checking that no process used them; `ls` shows none left and /data is back to 16G free. The step-7 rebuild is accepted. Acceptance criterion 5 is met.
