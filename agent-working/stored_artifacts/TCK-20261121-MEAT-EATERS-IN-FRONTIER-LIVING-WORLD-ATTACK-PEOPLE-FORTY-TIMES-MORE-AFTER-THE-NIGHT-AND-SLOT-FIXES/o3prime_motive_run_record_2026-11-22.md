---
status: active
layer: simulation
authority: P1
audience: agent
artifact_type: report
ticket_id: TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES
date: 2026-11-22
tags: []
---

# O3 / O3-prime motive trace: run record (OUT paths, GO ids, seals, shas, twin hashes, launcher lines)

Written byte-for-byte from the run directories by a read-only script (python -B, PYTHONDONTWRITEBYTECODE=1); nothing was written into a run directory. The per-cell row files (MBs) are NOT copied: this record names them by path, and the seals (`stage1_SHA256SUMS.md`, `stage2_SHA256SUMS.md`) let anyone re-check them against /data/vboxuser/o3-trace-runs. Rulings, by #715 id, are word for word in `rpg_designer_o3_kit_answers_2026-11-21.md`.

## First O3 run (the old person-only definition; superseded as the record by stage 1)

- OUT: `/data/vboxuser/o3-trace-runs/cd3a76430c63e12e45ffdfc4486c411861f304e5/run`
- heavy GO (#715): 7073542579
- kit head: cd3a76430c63e12e45ffdfc4486c411861f304e5 (kit worktree at dfd62dc3c, a shard-only commit)
- SEAL line: `SEAL 336487dfc4849c5cddf5a739fbb77dd9df64b1e6dfc67977dce3cfbfe0eceb79 11:24:34`
- sha256 of SHA256SUMS: `336487dfc4849c5cddf5a739fbb77dd9df64b1e6dfc67977dce3cfbfe0eceb79`
- `sha256sum -c SHA256SUMS` (run now, from OUT): 52 OK, 0 not OK (exit 0)
- note: This run's launcher wrote NO runner.json (the launcher defect TCK-20261122-PERSON-ATTACK-LAUNCHER-WRITES-NO-RUNNER-RECORD); its twin hashes below come from the cell files.
- `/data/vboxuser/o3-trace-runs/cd3a76430c63e12e45ffdfc4486c411861f304e5/record.env` sha256 `98814b8be021d18fd16f55421f898c457c4eebbe404889b18eeddab65fdff460`
- `/data/vboxuser/o3-trace-runs/cd3a76430c63e12e45ffdfc4486c411861f304e5/RECORD_SET.md` sha256 `550871fb25f4fdce97046cee6abcfe09a72c048ee5c40497104650a93ebd073d`
- `/data/vboxuser/o3-trace-runs/cd3a76430c63e12e45ffdfc4486c411861f304e5/dry_run.txt` sha256 `5bc4c2fca6f656cfca768b9c058d6817f7cfb04b31d722804ff7c3fa60bbe03f`
- `/data/vboxuser/o3-trace-runs/cd3a76430c63e12e45ffdfc4486c411861f304e5/kit_sha256_after_run.txt` sha256 `9d596f1dc826554a07913af577afa5659f3b51ec3b526a8a46f97e27f689ede1`

After-run kit shas file, full text:

```
# sha256 of the 9 kit files after the run (kit head cd3a76430; worktree HEAD dfd62dc3c6d1f1d3a69496eeadad41e24a852b0a), taken 11:25:25
a0e51b577b7579bd6b914c2745fbf844f57be20a3074f08153fe33565f45460c  tools/rpg_measure/person_attack_spy.py
4bcd4c55ed34fe8ceea5e3a11c39df00b17bf529f2294b32a2a034af65157fc9  tools/rpg_measure/person_attack_summary.py
45a5ca1949ddcfff492790c2bc9d0afae015d0b62224cd805083f3baeb087fb4  tools/rpg_measure/person_attack_run.py
7073f4bbed2ff20d4a4f91d4ffcaf506cb21f2fdca14e906d0042169b067ee98  tools/rpg_measure/person_attack_launch.sh
3c58a539f9232af74b45b3598b501106a8719f50062b814e330182d4c2a75f11  tools/rpg_measure/person_attack_watch.sh
52911f76d77d4d5f6ac4d6ce613aafdd9fd9478935a1c59bfce45a5c01ca3049  tools/rpg_measure/person_attack_tree_check.py
86adfd69bd783e7bc8968e88dcc87c2bf27c632c7d2f49fafa048ff0dbcb4917  tools/rpg_measure/person_attack_kit_note.md
9d13c131c1ad73de15ce1b0fd90a5326fcffbff5ed5eee9f197d2bf599a5c1df  tools/rpg_measure/arm_child.py
a4e291ac22ff8539c59d026a4149e813cf24a8de2cd70fda29ca44afa1b3933e  tests/tools/test_person_attack_kit.py
# git -C /data/vboxuser/Work/rpg-based-simulation/.claude/worktrees/rpg-ubuntu-o3-trace status --porcelain (empty = clean):
# end
```

launcher.log lines (RUN START, START, END, RUN EXIT, SUMMARY, TREE, SEAL, SUBJECTS, CELLS):

```
TREE NEW 87792e3e8ec42dfd0015f745bbcc5077262bb17d (/data/vboxuser/o3-trace-trees/87792e3e8ec42dfd0015f745bbcc5077262bb17d): equal to git ls-tree (paths and blob hashes), no data/runs
TREE BASE e722708947004c7f1eb427501b09f404c76c7cfe (/data/vboxuser/o3-trace-trees/e722708947004c7f1eb427501b09f404c76c7cfe): equal to git ls-tree (paths and blob hashes), no data/runs
RUN START 10:27:46 go=7073542579 (sequential: one process per scope)
START new__frontier_living_world__s42__plain 10:27:47
END new__frontier_living_world__s42__plain rc=0 wall=225s 10:31:32
START new__frontier_living_world__s42__spy 10:31:34
END new__frontier_living_world__s42__spy rc=0 wall=236s 10:35:30
START base__frontier_living_world__s42__plain 10:35:31
END base__frontier_living_world__s42__plain rc=0 wall=255s 10:39:46
START base__frontier_living_world__s42__spy 10:39:48
END base__frontier_living_world__s42__spy rc=0 wall=253s 10:44:01
START new__frontier_living_world__s45__plain 10:44:03
END new__frontier_living_world__s45__plain rc=0 wall=375s 10:50:18
START new__frontier_living_world__s45__spy 10:50:20
END new__frontier_living_world__s45__spy rc=0 wall=366s 10:56:26
START base__frontier_living_world__s45__plain 10:56:27
END base__frontier_living_world__s45__plain rc=0 wall=278s 11:01:05
START base__frontier_living_world__s45__spy 11:01:06
END base__frontier_living_world__s45__spy rc=0 wall=283s 11:05:49
START new__frontier_living_world__s43__plain 11:05:50
END new__frontier_living_world__s43__plain rc=0 wall=278s 11:10:28
START new__frontier_living_world__s43__spy 11:10:30
END new__frontier_living_world__s43__spy rc=0 wall=293s 11:15:23
START base__frontier_living_world__s43__plain 11:15:25
END base__frontier_living_world__s43__plain rc=0 wall=264s 11:19:49
START base__frontier_living_world__s43__spy 11:19:51
END base__frontier_living_world__s43__spy rc=0 wall=282s 11:24:33
RUN EXIT 0 status=COMPLETE 11:24:34 (wall 3408s)
SUMMARY EXIT 0 11:24:34
TREE CLEAN: /data/vboxuser/o3-trace-trees/87792e3e8ec42dfd0015f745bbcc5077262bb17d has no data/runs
TREE CLEAN: /data/vboxuser/o3-trace-trees/e722708947004c7f1eb427501b09f404c76c7cfe has no data/runs
```

Per-cell twin final_hash (plain vs spy):

| cell | plain final_hash | spy final_hash | equal |
|---|---|---|---|
| new/s42 | `45063d92bf95ec5ad52fc91f2eeebac434f0061229b44bbbc825564f054832b2` | `45063d92bf95ec5ad52fc91f2eeebac434f0061229b44bbbc825564f054832b2` | yes |
| base/s42 | `07b42d120e76003581351fde267e4e40c32e800ac41eef79fb8f0364d4cd7eb3` | `07b42d120e76003581351fde267e4e40c32e800ac41eef79fb8f0364d4cd7eb3` | yes |
| new/s43 | `3322f90ee42fc1fa96a978fa8b46d501f8b2bc9aed8435dca06551337eb1ef47` | `3322f90ee42fc1fa96a978fa8b46d501f8b2bc9aed8435dca06551337eb1ef47` | yes |
| base/s43 | `65bf51f72f6a0082ce87eb4eb95bbabf651a72b4ffcd82de9bf59f9c97c73f4d` | `65bf51f72f6a0082ce87eb4eb95bbabf651a72b4ffcd82de9bf59f9c97c73f4d` | yes |
| new/s45 | `b91ce90afdfb0bacddb80d95fd7390a76b24e1a6d92c88adf1ef2a06ecfaf36b` | `b91ce90afdfb0bacddb80d95fd7390a76b24e1a6d92c88adf1ef2a06ecfaf36b` | yes |
| base/s45 | `593c7e0e19f66b34911594d95f33888eeea69e54ae788bfa2d4a8048591fb303` | `593c7e0e19f66b34911594d95f33888eeea69e54ae788bfa2d4a8048591fb303` | yes |

## Stage 1: the O3-prime + motive trace (the record under the new definition, accepted #715 7075699606)

- OUT: `/data/vboxuser/o3-trace-runs/83a752cdebb64a20224b764727b41a76f08adaa5/stage1/run`
- heavy GO (#715): 7075026055
- kit head: 83a752cdebb64a20224b764727b41a76f08adaa5
- SEAL line: `SEAL 60c1cb69b692e5e28fc08428a4a435f71ca32ae9c45076fbe8c8eb06b5c88404 14:00:46`
- sha256 of SHA256SUMS: `60c1cb69b692e5e28fc08428a4a435f71ca32ae9c45076fbe8c8eb06b5c88404`
- `sha256sum -c SHA256SUMS` (run now, from OUT): 53 OK, 0 not OK (exit 0)
- `/data/vboxuser/o3-trace-runs/83a752cdebb64a20224b764727b41a76f08adaa5/stage1/record.env` sha256 `9706cd1df6f8c0c2de4fdb1bae4ffe8b73d227fb92e21b259a9a1a7e55230037`
- `/data/vboxuser/o3-trace-runs/83a752cdebb64a20224b764727b41a76f08adaa5/stage1/RECORD_SET.md` sha256 `2a6c1ad983d52b6c4b56d7a270a0a569aba12fda744390b022f136d787ffde0a`
- `/data/vboxuser/o3-trace-runs/83a752cdebb64a20224b764727b41a76f08adaa5/stage1/dry_run.txt` sha256 `8c6105f99daec7ccdd7b6200d6a43c664b3ca46f4f1528e0129a9dd7f8bedb9d`
- `/data/vboxuser/o3-trace-runs/83a752cdebb64a20224b764727b41a76f08adaa5/stage1/kit_sha256_after_run.txt` sha256 `49929fe7fd0ad6da93379917e7836e4c04467d8f8647830ab7238a5ae1d15462`

After-run kit shas file, full text:

```
# sha256 of the 13 kit files after the stage-1 run (kit head 83a752cdebb64a20224b764727b41a76f08adaa5; worktree HEAD 83a752cdebb64a20224b764727b41a76f08adaa5), taken 14:01:45
d3cb707245c8154e7bfa13d822275b51dc1e42789334cf0ca5ff5e77a247890a  tools/rpg_measure/person_attack_spy.py
8e4e390b2aec6d3932b446dff98289f02ed6f056c664aa42236e1ddb4e7a4cbc  tools/rpg_measure/person_attack_summary.py
aa9549943782176bae09f71e2d08141175e7a52dbf44615bb112dab567982f52  tools/rpg_measure/person_attack_run.py
8638882a343b0813b84c73224539dd6e64b72867712fbbf4cafedef9143feb25  tools/rpg_measure/person_attack_launch.sh
3c58a539f9232af74b45b3598b501106a8719f50062b814e330182d4c2a75f11  tools/rpg_measure/person_attack_watch.sh
52911f76d77d4d5f6ac4d6ce613aafdd9fd9478935a1c59bfce45a5c01ca3049  tools/rpg_measure/person_attack_tree_check.py
7d4d771e6143f0bfa969ae15fd6d8236c70d0de16c4146618a21a5282dc1ed03  tools/rpg_measure/person_attack_kit_note.md
9d13c131c1ad73de15ce1b0fd90a5326fcffbff5ed5eee9f197d2bf599a5c1df  tools/rpg_measure/arm_child.py
cb71a7e987fc30ba6542a1f325b49c2e6c6fa1cb2a5a2c1db434e13689aa7bde  tools/rpg_measure/subject_trace_spy.py
eda149ecda8a799314355ef16e8bfcb902fe584ee246ebbeb98950c5d7efba71  tools/rpg_measure/subject_trace_run.py
b0ed4741c61ad313af6d7adafdd73e1997af94ef8a28d3e129b1ccaa853e2a5a  tools/rpg_measure/subject_trace_launch.sh
ce965b1f728d87d8131d4069cd9979a8c0514e529141afaf07c1fbc4330ffaf7  tests/tools/test_person_attack_kit.py
45d61ce3dbc650a97535410672989fdc70fca7d724bdf7e7ef5c3758eb01e774  tests/tools/test_subject_trace_kit.py
# git -C /data/vboxuser/Work/rpg-based-simulation/.claude/worktrees/rpg-ubuntu-o3-trace status --porcelain (empty = clean):
# end
```

launcher.log lines (RUN START, START, END, RUN EXIT, SUMMARY, TREE, SEAL, SUBJECTS, CELLS):

```
TREE NEW 87792e3e8ec42dfd0015f745bbcc5077262bb17d (/data/vboxuser/o3-trace-trees/87792e3e8ec42dfd0015f745bbcc5077262bb17d): equal to git ls-tree (paths and blob hashes), no data/runs
TREE BASE e722708947004c7f1eb427501b09f404c76c7cfe (/data/vboxuser/o3-trace-trees/e722708947004c7f1eb427501b09f404c76c7cfe): equal to git ls-tree (paths and blob hashes), no data/runs
RUN START 12:55:57 go=7075026055 (sequential: one process per scope)
START new__frontier_living_world__s42__plain 12:55:58
END new__frontier_living_world__s42__plain rc=0 wall=232s 12:59:50
START new__frontier_living_world__s42__spy 12:59:52
END new__frontier_living_world__s42__spy rc=0 wall=252s 13:04:04
START base__frontier_living_world__s42__plain 13:04:05
END base__frontier_living_world__s42__plain rc=0 wall=236s 13:08:01
START base__frontier_living_world__s42__spy 13:08:02
END base__frontier_living_world__s42__spy rc=0 wall=248s 13:12:10
START new__frontier_living_world__s43__plain 13:12:12
END new__frontier_living_world__s43__plain rc=0 wall=283s 13:16:55
START new__frontier_living_world__s43__spy 13:16:58
END new__frontier_living_world__s43__spy rc=0 wall=293s 13:21:51
START base__frontier_living_world__s43__plain 13:21:52
END base__frontier_living_world__s43__plain rc=0 wall=276s 13:26:28
START base__frontier_living_world__s43__spy 13:26:29
END base__frontier_living_world__s43__spy rc=0 wall=273s 13:31:02
START new__frontier_living_world__s45__plain 13:31:04
END new__frontier_living_world__s45__plain rc=0 wall=382s 13:37:26
START new__frontier_living_world__s45__spy 13:37:28
END new__frontier_living_world__s45__spy rc=0 wall=537s 13:46:26
START base__frontier_living_world__s45__plain 13:46:28
END base__frontier_living_world__s45__plain rc=0 wall=423s 13:53:31
START base__frontier_living_world__s45__spy 13:53:33
END base__frontier_living_world__s45__spy rc=0 wall=433s 14:00:46
RUN EXIT 0 status=COMPLETE 14:00:46 (wall 3889s)
SUMMARY EXIT 0 14:00:46
TREE CLEAN: /data/vboxuser/o3-trace-trees/87792e3e8ec42dfd0015f745bbcc5077262bb17d has no data/runs
TREE CLEAN: /data/vboxuser/o3-trace-trees/e722708947004c7f1eb427501b09f404c76c7cfe has no data/runs
```

Per-cell twin final_hash (plain vs spy):

| cell | plain final_hash | spy final_hash | equal |
|---|---|---|---|
| new/s42 | `45063d92bf95ec5ad52fc91f2eeebac434f0061229b44bbbc825564f054832b2` | `45063d92bf95ec5ad52fc91f2eeebac434f0061229b44bbbc825564f054832b2` | yes |
| base/s42 | `07b42d120e76003581351fde267e4e40c32e800ac41eef79fb8f0364d4cd7eb3` | `07b42d120e76003581351fde267e4e40c32e800ac41eef79fb8f0364d4cd7eb3` | yes |
| new/s43 | `3322f90ee42fc1fa96a978fa8b46d501f8b2bc9aed8435dca06551337eb1ef47` | `3322f90ee42fc1fa96a978fa8b46d501f8b2bc9aed8435dca06551337eb1ef47` | yes |
| base/s43 | `65bf51f72f6a0082ce87eb4eb95bbabf651a72b4ffcd82de9bf59f9c97c73f4d` | `65bf51f72f6a0082ce87eb4eb95bbabf651a72b4ffcd82de9bf59f9c97c73f4d` | yes |
| new/s45 | `b91ce90afdfb0bacddb80d95fd7390a76b24e1a6d92c88adf1ef2a06ecfaf36b` | `b91ce90afdfb0bacddb80d95fd7390a76b24e1a6d92c88adf1ef2a06ecfaf36b` | yes |
| base/s45 | `593c7e0e19f66b34911594d95f33888eeea69e54ae788bfa2d4a8048591fb303` | `593c7e0e19f66b34911594d95f33888eeea69e54ae788bfa2d4a8048591fb303` | yes |

## Stage 2: the per-tick subject trace (VALID, #715 7076173637)

- OUT: `/data/vboxuser/o3-trace-runs/83a752cdebb64a20224b764727b41a76f08adaa5/stage2/cells`
- heavy GO (#715): 7075868168
- kit head: 83a752cdebb64a20224b764727b41a76f08adaa5
- SEAL line: `SEAL 4e97ee4dd30ebf913f99aa6f0d09fe88aa8789654aaba48fedc6e9351e14aa84 14:45:37`
- sha256 of SHA256SUMS: `4e97ee4dd30ebf913f99aa6f0d09fe88aa8789654aaba48fedc6e9351e14aa84`
- `sha256sum -c SHA256SUMS` (run now, from OUT): 23 OK, 0 not OK (exit 0)
- note: Its spy hashes are compared with the SEALED stage-1 plain twins of the same arm and seed.
- `/data/vboxuser/o3-trace-runs/83a752cdebb64a20224b764727b41a76f08adaa5/stage2/record.env` sha256 `0b70794a9e5024a80b7e353130c5ee748bcccf3d8bb373028e527782578b5986`
- `/data/vboxuser/o3-trace-runs/83a752cdebb64a20224b764727b41a76f08adaa5/stage2/RECORD_SET.md` sha256 `8676a3020f967b7641fe9a9c016432cfbbccbbf51a6c725c64ab58bb0db71cec`
- `/data/vboxuser/o3-trace-runs/83a752cdebb64a20224b764727b41a76f08adaa5/stage2/dry_run.txt` sha256 `96caa732eff0305ba46314c63941bcd0ffe1e8040a8476dbe5237fb804654abb`
- `/data/vboxuser/o3-trace-runs/83a752cdebb64a20224b764727b41a76f08adaa5/stage2/subjects.json` sha256 `65500827d464a1c5a45679ecd06d58abdf5d6f94d995309c6975d231421192f7`
- `/data/vboxuser/o3-trace-runs/83a752cdebb64a20224b764727b41a76f08adaa5/stage2/kit_sha256_after_run.txt` sha256 `d060a06f5d84dcacdf5bb13ab06312adc1db6843263e1cf1d6927e2d9b5dac03`

After-run kit shas file, full text:

```
# sha256 of the 13 kit files after the stage-2 run (kit head 83a752cdebb64a20224b764727b41a76f08adaa5; worktree HEAD 83a752cdebb64a20224b764727b41a76f08adaa5), taken 14:46:44
d3cb707245c8154e7bfa13d822275b51dc1e42789334cf0ca5ff5e77a247890a  tools/rpg_measure/person_attack_spy.py
8e4e390b2aec6d3932b446dff98289f02ed6f056c664aa42236e1ddb4e7a4cbc  tools/rpg_measure/person_attack_summary.py
aa9549943782176bae09f71e2d08141175e7a52dbf44615bb112dab567982f52  tools/rpg_measure/person_attack_run.py
8638882a343b0813b84c73224539dd6e64b72867712fbbf4cafedef9143feb25  tools/rpg_measure/person_attack_launch.sh
3c58a539f9232af74b45b3598b501106a8719f50062b814e330182d4c2a75f11  tools/rpg_measure/person_attack_watch.sh
52911f76d77d4d5f6ac4d6ce613aafdd9fd9478935a1c59bfce45a5c01ca3049  tools/rpg_measure/person_attack_tree_check.py
7d4d771e6143f0bfa969ae15fd6d8236c70d0de16c4146618a21a5282dc1ed03  tools/rpg_measure/person_attack_kit_note.md
9d13c131c1ad73de15ce1b0fd90a5326fcffbff5ed5eee9f197d2bf599a5c1df  tools/rpg_measure/arm_child.py
cb71a7e987fc30ba6542a1f325b49c2e6c6fa1cb2a5a2c1db434e13689aa7bde  tools/rpg_measure/subject_trace_spy.py
eda149ecda8a799314355ef16e8bfcb902fe584ee246ebbeb98950c5d7efba71  tools/rpg_measure/subject_trace_run.py
b0ed4741c61ad313af6d7adafdd73e1997af94ef8a28d3e129b1ccaa853e2a5a  tools/rpg_measure/subject_trace_launch.sh
ce965b1f728d87d8131d4069cd9979a8c0514e529141afaf07c1fbc4330ffaf7  tests/tools/test_person_attack_kit.py
45d61ce3dbc650a97535410672989fdc70fca7d724bdf7e7ef5c3758eb01e774  tests/tools/test_subject_trace_kit.py
# git -C /data/vboxuser/Work/rpg-based-simulation/.claude/worktrees/rpg-ubuntu-o3-trace status --porcelain (empty = clean):
# end
```

launcher.log lines (RUN START, START, END, RUN EXIT, SUMMARY, TREE, SEAL, SUBJECTS, CELLS):

```
TREE NEW 87792e3e8ec42dfd0015f745bbcc5077262bb17d (/data/vboxuser/o3-trace-trees/87792e3e8ec42dfd0015f745bbcc5077262bb17d): equal to git ls-tree, no data/runs
TREE BASE e722708947004c7f1eb427501b09f404c76c7cfe (/data/vboxuser/o3-trace-trees/e722708947004c7f1eb427501b09f404c76c7cfe): equal to git ls-tree, no data/runs
SUBJECTS sha256 65500827d464a1c5a45679ecd06d58abdf5d6f94d995309c6975d231421192f7 (written and hashed before the first stage-2 process)
CELLS for seeds with a subject: 42 45 (NEW and the same-seed BASE)
RUN START 14:22:30 go=7075868168 kind=cells (sequential: one process per scope)
START new__frontier_living_world__s42__spy 14:22:32
END new__frontier_living_world__s42__spy rc=0 wall=380s 14:28:50
START new__frontier_living_world__s45__spy 14:28:53
END new__frontier_living_world__s45__spy rc=0 wall=902s 14:37:32
START base__frontier_living_world__s42__spy 14:37:33
END base__frontier_living_world__s42__spy rc=0 wall=1132s 14:41:22
START base__frontier_living_world__s45__spy 14:41:23
END base__frontier_living_world__s45__spy rc=0 wall=1386s 14:45:36
RUN EXIT 0 status=COMPLETE 14:45:37 (wall 1387s)
TREE CLEAN: /data/vboxuser/o3-trace-trees/87792e3e8ec42dfd0015f745bbcc5077262bb17d has no data/runs
TREE CLEAN: /data/vboxuser/o3-trace-trees/e722708947004c7f1eb427501b09f404c76c7cfe has no data/runs
```

Per-cell spy final_hash vs the SEALED stage-1 plain twin (cell_validity.json), plan_sha256, rows, legality calls in window, offset drift:

| cell | spy final_hash | sealed stage-1 plain final_hash | equal | plan_sha256 | rows | legality in window | offset_drift | valid |
|---|---|---|---|---|---|---|---|---|
| new/s42 | `45063d92bf95ec5ad52fc91f2eeebac434f0061229b44bbbc825564f054832b2` | `45063d92bf95ec5ad52fc91f2eeebac434f0061229b44bbbc825564f054832b2` | yes | `8c16e1435e0a122fae863ef937ffbe023d173cbfceaa044f045a77865ebf864c` | 2344 | 253 | False | True |
| new/s45 | `b91ce90afdfb0bacddb80d95fd7390a76b24e1a6d92c88adf1ef2a06ecfaf36b` | `b91ce90afdfb0bacddb80d95fd7390a76b24e1a6d92c88adf1ef2a06ecfaf36b` | yes | `8c16e1435e0a122fae863ef937ffbe023d173cbfceaa044f045a77865ebf864c` | 3280 | 484 | False | True |
| base/s42 | `07b42d120e76003581351fde267e4e40c32e800ac41eef79fb8f0364d4cd7eb3` | `07b42d120e76003581351fde267e4e40c32e800ac41eef79fb8f0364d4cd7eb3` | yes | `8c16e1435e0a122fae863ef937ffbe023d173cbfceaa044f045a77865ebf864c` | 2344 | 9 | False | True |
| base/s45 | `593c7e0e19f66b34911594d95f33888eeea69e54ae788bfa2d4a8048591fb303` | `593c7e0e19f66b34911594d95f33888eeea69e54ae788bfa2d4a8048591fb303` | yes | `8c16e1435e0a122fae863ef937ffbe023d173cbfceaa044f045a77865ebf864c` | 3280 | 127 | False | True |

