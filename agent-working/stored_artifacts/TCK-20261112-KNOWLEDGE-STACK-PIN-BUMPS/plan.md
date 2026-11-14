---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261112-KNOWLEDGE-STACK-PIN-BUMPS
artifact_type: plan
tags: [knowledge-store, setup]
---

# Plan

Ticket Scope 1-8, amended after the planner's review (four changes below). A lead heavy-slot go is needed before every build, index or graphify run; each runs under `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`, detached (setsid/nohup) and polled when it may exceed 10 minutes.

**Lead conditions for every slot run (planner relay, lead-planner):** (a) one run at a time under the wrapper, MemAvailable at least 3 GB at launch, the ~18 min builds detached; (b) torch only from the CPU index, and the pip cache on /data (`PIP_CACHE_DIR=/data/vboxuser/aw-pinbump-pipcache`), never on /; (c) deleting is owner-only.

1. Disk: `tools/sessions/disk_headroom.py`; record / and /data free. Stop if /data is under 10 GB.
2. **One scratch tree for both sides.** `eval_search.py` has no `--db-path`; it reads the default index of the checkout it runs in, and this worktree's index is stale (~5.5k changed files). So: `git archive HEAD | tar -x -C /data/vboxuser/aw-pinbump-scratch`.
   - Baseline: build in the scratch tree with the CURRENT main `.venv-knowledge`: `knowledge_search.py build --corpus-root <scratch> --db-path <scratch>/agent-working/.index/knowledge-index/knowledge.db`, then `eval_search.py` and the five spot queries run from `<scratch>`. Before trusting a number, print the db path `eval_search.py` opens and confirm it is the scratch db.
   - Move that db aside, then repeat with the throwaway venv.
   - Two full builds (~18 min each): a separate go for each, detached.
3. Throwaway venv at `/data/vboxuser/aw-pinbump-venv`, never the main venv: torch 2.15.0+cpu from the CPU index first, then the unchanged pins (sentence-transformers 6.1.0, sqlite-vec, rank-bm25, mcp 1.30.0), graphifyy 0.9.104, headroom-ai 0.43.1 (base only). Own go.
4. **graphify:** always the throwaway venv's own `bin/graphify` by absolute path (the bare `graphify` on PATH is not the pinned one; TCK-20261024-GRAPHIFY-ON-PATH-IS-NOT-THE-PINNED-VERSION). Run in the scratch tree on a copy of `graphify-out` (505M). Record node and edge counts before and after `graphify update .`, the changelog 0.9.70 to 0.9.104, and any CLI, format or node-id change. Own go for the update (it walks ~19k files). Stop before touching the shared graph if format or ids changed.
5. **headroom smoke:** `KNOWLEDGE_PYTHON=<throwaway>/bin/python3` and `HEADROOM_WORKSPACE_DIR=<scratch>/.headroom-workspace`, so a newer headroom never touches or migrates the shared `.headroom-workspace`. Start `tools/start_headroom_mcp.sh`, list tools, one call; never `headroom wrap`.
6. Decision per pin (torch only if Recall@5 and MRR@10 are not lower), then edit `requirements-knowledge.txt`, the two pin tests and a dated line in `docs/guidelines/agent_working_environment.md`.
7. With a further go: rebuild the main `.venv-knowledge` and real index; confirm `search_docs` and the headroom MCP start.
8. **Cleanup (owner-only deletion):** I do not remove anything. I send the planner the exact `rm` commands with sizes for the throwaway venv, the scratch index, `/data/vboxuser/aw-pinbump-scratch` and `/data/vboxuser/aw-pinbump-pipcache`, and the planner hands them to the owner. Acceptance criterion 5 is met when the owner has removed them.
