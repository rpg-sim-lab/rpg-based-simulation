---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP
artifact_type: evidence
tags: []
---

# Evidence for TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP

Measurement outputs copied from `/mnt/data2/rpg-measure/holdmove/` (the originals stay there until the owner removes them).

- `stage1_cells/` (fix) and `stage1_cells/base/`: stage 1, `frontier_marches` and `crowded_frontier` seed 42, plain and spied cells and drivers.
- `stage2_cells_summary.json`: per cell of the 34 stage-2 runs, `final_hash`, `match`, `exceptions`, deaths and end census (the full 30 MB cells are not copied).
- `dying_cells/`: the four Tier 2 cells (`dying_window_v8` `3828af12`): fix s42 `6daf3802`, fix s43 `c085c86b`, fix s45 `14735c06`, base s43 `7fd61d77` (sha256 prefixes of the JSON files).
- `scripts/`: the spies, checkers, drivers and launchers used. `hold_spy_v7.py` `69e529f9`, `stage2_check` `94ca9b14` (`stage2_world_waive.py` `848a2375` carries the one owner waiver), `run_stage2.sh` `73af4af8`, `launch_stage2_resume.sh` `e8479b7e`, `dying_window_v8_3828af12_approved.py` `3828af12` (`dying_window_v8.py` is the same code plus a docstring paragraph, `082e99e8`), `dying_stop_check.py` `c31cc811` (replaced by `dying_stop_check_fatal.py` `804fb0e6` for runs 2-4), `run_dying_one.sh` `156f1777`.
- `logs/`: the stage-2 drivers (`stage2_driver.log`, `stage2_driver_resume.log`) and the four Tier 2 run logs.
- `head_hash/`: the post-measurement hash-equality check (below), `run_head_hash.sh` `a2b00cb4`, its driver log and the two plain cells.
- CI fix round (not copied; they stay under `/mnt/data2/rpg-measure/holdmove/` until the owner removes them): `head_hash/` and `head_hash2/` (hash proofs at 3a7ea995d and 852325043, scripts `run_head_hash.sh` a2b00cb4, `run_head_hash2.sh` 80cc3eff, `run_head_hash2b.sh` 53ce8721, `run_head_hash2c.sh` e8ba6b9a), `smoke_pair/` (the interaction smoke: `smoke_driver.sh` 9c12d18b, `smoke_wrapcount.py` 6fdfaa35, `hold_spy_v7.py` 69e529f9; the 8 run JSONs with wrapcount sidecars), the throwaway trees `tree_head_3a7ea995d`, `tree_head_852325043`, `p2_main_7bf4a5670`, `tree_smoke_merged_e1dc568bc`, `tree_smoke_main_7bf4a5670`, and the six `rpgdying_*` run dirs under `stage2/tree_*/data/runs/`.
