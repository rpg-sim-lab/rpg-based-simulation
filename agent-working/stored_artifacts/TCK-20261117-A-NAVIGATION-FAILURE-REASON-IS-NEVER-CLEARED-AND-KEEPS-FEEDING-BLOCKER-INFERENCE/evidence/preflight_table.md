KIT PREFLIGHT PASS (evidence label: executed)

| input | value |
|---|---|
| kit | failreason_move v1 |
| manifest sha256 | 488582e9b3e2de5d71c1369818846ff2a8bd3798f8bbe8a00e7cd2bffe054b2e |
| preflight sha256 | f81e5100dd782429d4104367100b741ad0ef79dcbf6e998dd1572a896255eb59 |
| interpreter | /mnt/data/venv-sync2/bin/python |
| env digest | 8702e05791045689960cd31d3d34f12980aa8595b9bcb7ca85833c6c164c0445 |
| ticks cap | 10 |
| file failreason_move_spy.py | 9c0b7c56471ead2f7d36f06760ed12a235facf8eb6364fcffa57b2e99ba9a1ec |
| file run_move_cells.sh | 528a7548fb92c559fb36dcba49ef0e6e5b2f5f207a27363a0cf439682ad17e01 |
| file failreason_move_summarizer.py | 7140a02c2630d9773b914a9bc3e85b41cd07051d10f0eac89d91f575bdb2c98f |
| tree fixtree_merged | /mnt/data2/rpg-measure/failreason/fixtree_merged |

| check | scope | result | detail |
|---|---|---|---|
| a files | failreason_move_spy.py | PASS | sha256 9c0b7c56471ead2f |
| a files | run_move_cells.sh | PASS | sha256 528a7548fb92c559 |
| a files | failreason_move_summarizer.py | PASS | sha256 7140a02c2630d977 |
| f runner refs | run_move_cells.sh | PASS | names 1 python file(s) |
| h gate visibility | move_spy: failreason_move_spy.py | PASS | matches the shared gate's heavy words |
| h gate visibility | plain_twin: failreason_move_spy.py | PASS | matches the shared gate's heavy words |
| c fixture run | move_spy@fixtree_merged | PASS | rc=0, 10 tick(s) |
| i perf | move_spy@fixtree_merged | PASS | wall 3.00s, loadavg1 1.84 -> 1.84 |
| d field liveness | move_spy@fixtree_merged final_hash | PASS | 1 distinct over 1 value(s) |
| d field liveness | move_spy@fixtree_merged bars.L1_post_ne_expected | PASS | DECLARED may_be_constant; 1 distinct over 1 value(s) |
| d field liveness | move_spy@fixtree_merged bars.M1_moved_with_unattributed_code | PASS | DECLARED may_be_constant; 1 distinct over 1 value(s) |
| d field liveness | move_spy@fixtree_merged bars.M2_moved_with_code_no_writer | PASS | DECLARED may_be_constant; 1 distinct over 1 value(s) |
| d field liveness | move_spy@fixtree_merged bars.reasons_set | PASS | DECLARED may_be_constant; 1 distinct over 1 value(s) |
| d field liveness | move_spy@fixtree_merged reported.hook_coverage.missing | PASS | DECLARED may_be_constant; 1 distinct over 1 value(s) |
| d field liveness | move_spy@fixtree_merged bars.moves.all | PASS | DECLARED may_be_constant; 1 distinct over 1 value(s) |
| d field liveness | move_spy@fixtree_merged logging_errors | PASS | DECLARED may_be_constant; 1 distinct over 1 value(s) |
| d field liveness | move_spy@fixtree_merged exceptions | PASS | DECLARED may_be_constant; 1 distinct over 1 value(s) |
| d field liveness | move_spy@fixtree_merged match | PASS | DECLARED may_be_constant; 1 distinct over 1 value(s) |
| d field liveness | move_spy@fixtree_merged bars.R2_blocker_filed_after_move | PASS | DECLARED may_be_constant; 1 distinct over 1 value(s) |
| d field liveness | move_spy@fixtree_merged bars.reasons_cleared | PASS | DECLARED may_be_constant; 1 distinct over 1 value(s) |
| e guards | move_spy@fixtree_merged ok line | PASS | present |
| e guards | move_spy@fixtree_merged bad line | PASS | absent |
| e guards | move_spy@fixtree_merged ERROR+ log lines | PASS | 0 |
| e guards | move_spy@fixtree_merged hook navigation_patch_apply (L1 wrap) | PASS | hit 67 time(s) |
| c fixture run | plain_twin@fixtree_merged | PASS | rc=0, 10 tick(s) |
| i perf | plain_twin@fixtree_merged | PASS | wall 2.31s, loadavg1 1.84 -> 1.85 |
| d field liveness | plain_twin@fixtree_merged final_hash | PASS | 1 distinct over 1 value(s) |
| d field liveness | plain_twin@fixtree_merged plain | PASS | DECLARED may_be_constant; 1 distinct over 1 value(s) |
| e guards | plain_twin@fixtree_merged ok line | PASS | present |
| e guards | plain_twin@fixtree_merged bad line | PASS | absent |
| e guards | plain_twin@fixtree_merged ERROR+ log lines | PASS | 0 |

0 FAIL of 31 check(s).
