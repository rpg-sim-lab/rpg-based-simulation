<!-- DRAFT (rpg-implementer). Evidence README for TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED. Raw dumps stay OUT of git; their sha256 are in raw_dumps_sha256.txt (same folder). -->
# Evidence: ENG (SURV-07 Law P at the tactical survival sites, S1 + hunt exemption)

## What is kept in the repo (small, cited)
- Scripts (staging folder): `eng_probe.py` (v1), `eng_probe_v2.py` (+ by_kind, wait_by_kind), `hold_probe.py`, `mode_split.py`, `kind_meals.py`, `probe_ab.py`, `probe_ab2.py`, `probe_gap.py`, `eng_trace.py`, `eng_trace_v2.py`, `eng_trace_v3.py`, `eng_trace_s42.py`, `eng_trace_p45.py`, `eng_classifier.py`, `eng_synthetic_check.py`. All record-only (wrappers never change a result); each works on both arm trees unless its docstring says otherwise.
- Summaries: `paired3_table.md`, `paired4_table.md`, `paired4_verdict.json`, `neutral4_verdict.json` (copied from /mnt/data/scratch-rpg-implementer/eng), `report_by_kind.txt`, `report_per_seed.txt` (copied from /mnt/data2/scratch-eng), this README, the PR body draft.
- Cited small traces: only if the owner row cites a tick-level fact; otherwise referenced by sha256.

## What is NOT in git
Raw run dumps under /mnt/data2/scratch-eng (28 MB) and /mnt/data/scratch-rpg-implementer/eng: `base_*`, `v2_*`, `v2k_*`, `v3_*`, `km_base_*`, `ms_*`, `ms2_*`, `ab_*`, `ab2_*`, `gap_base_*`, `tr_*`, `tr3_*`, `s42tr_*`, `p45_*` JSON files. Their sha256 are listed in `raw_dumps_sha256.txt`.

## Heads and trees
65d43dfa9f2b (base), 3e3a24d10e21 (S2 arm), 039c148a8fc5 (S1), e844e2845421 (S1 + hunt exemption; PR head 5c86b1b8a adds the merge of origin/main 36d4fd78e with no src change). Cached trees: /mnt/data2/rpg-measure/trees/<12 hex>. Paired results: /mnt/data2/rpg-measure/results/<12 hex>-72320cac-5000/<world>_<seed>.json (`final_hash`, `counters`, `final`, `start`). Pinned sequential runner: PYTHONHASHSEED=0, RPG_MEASURE_CACHE=/mnt/data2/rpg-measure. **Measured on the sequential reference; the production path differs until TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS lands.**

## Run -> file -> check
| Step | Files | Check against paired final_hash |
|---|---|---|
| base-arm probe v1 (65d43dfa9) | base_<w>_<s>.json x15 | 15/15 equal |
| probe_v2 on 039c148a8 | v2_<w>_<s>.json x15 | 15/15 equal |
| probes on e844e2845 | v3_<w>_<s>.json x15 | 15/15 equal |
| mode_split (039c arm / e844 arm) | ms_*, ms2_* x12 each | 12/12 each; flee/pursuit totals equal paired counters |
| by_kind frontier (039c) / base all worlds | v2k_* x5; km_base_* x15 | equal |
| A/B probes frontier s43, s45 | ab_* x4 | 4/4 equal |
| B2 probes frontier s42, s44, s46 | ab2_* x6 | 6/6 equal |
| s44 six-victim traces | tr_*, tr3_* | equal (v3 = re-run with hit fields) |
| s42 trace pair (w2, w7, g10 + animals) | s42tr_* x2 | 2/2 equal |
| predator 45 trace | p45_* x2 | 2/2 equal |
| gap probe (base) | gap_base_* x3 | 3/3 equal |
| neutral4 / paired4 | verdict JSON + table | PASS / PASS |
Completeness: every expected file was checked by name (the `rc=` lines of chains 1-3 are invalid; the verification is by file). Not hash-checked: short smoke outputs (not cited). Phase 1 (15a8f5893, hold_probe/eng_probe): NOT CHECKED against plain except urban s42 (== plain at 5000t).

## Disclosures
Overlap with another session's 1.8 GB process (17:55-23:55, 2026-11-02): counts and hashes unaffected, no timing claimed. One B2 probe run overlapped chain5's v3 trace (my error); hashes equal paired. `known_s44` (1620t) dropped, no plain run.
