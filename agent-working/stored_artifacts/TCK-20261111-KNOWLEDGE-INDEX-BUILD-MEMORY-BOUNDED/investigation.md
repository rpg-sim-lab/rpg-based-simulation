---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED
artifact_type: investigation
tags: [delivery]
---

# Investigation: TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED

All runs on host ubuntu, main df3527c69 era, system `python3` (the venv lacks sentence-transformers), under
`systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`, scratch `--db-path`, tool code unchanged, an RSS/VM sampler
in a wrapper. Corpus 17,393 chunks (2,945 ticket summaries, 1,918 investigations, 3,002 working-log rows, 9,528 doc chunks). Each run was
allowed by lead-planner and ran alone.

| run | command | result | peak RSS (VmHWM) | peak virtual (VmPeak) |
|---|---|---|---|---|
| 1 | `build` (full) | rc 0, about 18 min, index + BM25 + cache written | 1.40 GB | 4.68 GB |
| 2 | `build --incremental`, 12 files touched | rc 0, 349 chunks re-embedded, 5,622 files from cache | 1.57 GB | 4.85 GB |
| 3 | run 2 under `ulimit -v 4194304` (4 GB address space) | fails loading the model: `RuntimeError: unable to mmap 90868376 bytes ... model.safetensors` | 1.09 GB | 4.18 GB |

Thread counts for the runs: torch 2 threads, `os.cpu_count()` 6, affinity 2 (taskset 4-5). CI has different counts, so its VmPeak is
probably lower.

Findings:
- The ticket's premise (one `model.encode` over all texts, so memory grows with the corpus) is wrong. The embeddings array is about 26 MB
  (17,224 x 384 x 4 B), sentence-transformers already batches at 32 internally, and the committed index files are small (knowledge.db 55 MB,
  cache 60 MB, bm25 21 MB). Resident memory stays at 1.4-1.6 GB, well under the 3G cap.
- `tests/conftest.py` `pytest_runtest_setup` calls `setrlimit(RLIMIT_AS, (mem_limit, mem_limit))` before every test: 4 GB under the default
  medium budget. Torch reserves several GB of virtual address space, so the build's VmPeak (4.2-4.9 GB) exceeds it and the allocation is refused
  (positive control, run 3). Outside pytest `RLIMIT_AS` is unlimited, also inside the wrapper. `MemoryError` at 1.09 GB RSS is the signature.
- The setrlimit call sets the hard limit too. An unprivileged process can never raise a lowered hard limit, so the first test in a process fixes
  the cap for every later one, and `resource_budget_large` / `extra_slow` tests silently keep the medium cap unless they run first (planner
  checked: raising to 8 GB after lowering to 4 GB raises `ValueError`, which the conftest swallows).
- Lead did not run `make knowledge-index-update` on this host; its "the model OOMs here" came from the same pytest MemoryError (premise corrected, lead, 11-11).
- The post-commit hook never runs under pytest, so `RLIMIT_AS` does not touch it; its only issue was an uncapped 1.4-1.6 GB build on whichever seat commits (hence the opt-in).
