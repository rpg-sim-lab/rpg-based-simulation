---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE
artifact_type: investigation
---

# Evidence: low-hp retreat measurement (9 pinned cells, 5000t)

- Wrappers: `arm_child_starv.py` (sha256 e6d87053438d85a9382e476e1e51c65145aef22547bcc51f4bfae885b564b6d5) and `arm_child_lowhp.py` (sha256 0530f5904f56d2476db5700cf5a335d69fc530a103a40afe91d7efdce2241421; adds spies on `_panic_yields_to_need` and on `retreat_destination` calls from the hp<0.15 line, env LOWHP_LINE: 523 on the fix tree, 510 on the base tree). Cell command: `PYTHONHASHSEED=0 PYTHONPATH=$t systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 timeout 1800 /mnt/data/venv-sync2/bin/python <wrapper> <world> <seed> 5000 <out>`, cwd = an extracted git archive.
- Trees: fix d88efa7ea (tree f4d68046d6a9378896219a2fff749a42b12665a4; rebased as 13162deb7, same tree), base e512a40d9 (src equal to 777ede6e2's). Crowded base s43-46 are lane C's e755dc3d1 arm_child cells (tree-equal src); base s42 and the fliving s43 base were run here.
- Checks: base s42 end hash c5f6398be8968f3ce9d07a634a8588fcec6852f50b091546e7acd7267486a987; the counter-wrapper fix s42 equals the plain fix s42.
- `cells.json`: per-cell end hash, spy counts, starvation events and the sha256 of each full result (full results stay under /mnt/data2/rpg-measure/lowhp/results). `analysis_output.txt` / `analyze.py`: the per-seed, per-cause read. People = the base arm's tick-0 keeps_coin roster by id.
- Not counted: prey plus panic (the held (c) evaluations are not split by cause).
