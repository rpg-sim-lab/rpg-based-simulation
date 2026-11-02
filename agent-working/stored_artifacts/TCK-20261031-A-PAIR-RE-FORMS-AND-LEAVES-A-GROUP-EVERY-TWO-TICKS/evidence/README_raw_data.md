---
status: active
layer: simulation
authority: P1
audience: agent
artifact_type: report
ticket_id: TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS
phase: done
date: 2026-11-02
tags: []
---

# Raw run dumps (kept out of git)

The raw per-run and per-tick files of this ticket's measurements (121 files, 3,348,680 bytes: run json, per-tick jsonl traces, run stdout and `.done` markers) are NOT committed. They were committed first and removed at the re-sync onto #826, following the owner's trim ruling (#715 6573916118) and the shape #826 used for its own raw dumps. The files live in the author's scratch `/data/vboxuser/Work/groups_base/raw_evidence/` under the same relative path as below (relative to `agent-working/stored_artifacts/TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS/`), and the originals are in `/data/vboxuser/Work/groups_base/out*` and `trees/*`. Every number the disclosures use is in the kept summaries (`.txt`), scripts (`.py`, `.sh`), READMEs, `pr_notes.md` and divergence 2.146; the sha256 below lets a copy be checked against the file that was removed.

Five small traces that other tickets cite stay IN git (`evidence/f3_remeasure/traces/`): `tier2/crowded_s43_e10.jsonl` and `tier2/crowded_s43_trust.jsonl` (e10 rows, cited by TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET), `e23/u42_effd2e8fc.jsonl` and `e23/u42_30307228c.jsonl` (e23, both arms) and `tier2/frontier_living_world_s45.jsonl` (e22) (the last three cited by TCK-20261101-A-LOW-HP-VANGUARD-TAKES-ROLE-GATED-MOVES-INTO-CONTACT). One cited trace is OUT because of its size: `evidence/f3_remeasure/traces/tier2/crowded_frontier_s43.jsonl` (434,644 bytes), cited by TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET (as out_t2/crowded_frontier_s43.jsonl, raw read); its sha256 is in the table.

Their `.json` files were added while this folder was still under `staging_artifacts/` (not ignored) and moved here with `git mv`; `.gitignore` ignores `stored_artifacts/**/*.json` only for new files, which is why they were tracked at all.

## Cited scratch files that were never in git

| name as cited | bytes | sha256 | citing ticket | kept at |
|---|---|---|---|---|
| out_profA/frontier_profile.json | 22617 | 314e7d18690842bcc0e1d036603c7d1d28bde3cf120bd21b55d8dbdb9ff170b0 | TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE (line 72) | `/data/vboxuser/Work/groups_base/raw_evidence/out_profA/frontier_profile.json` (the profile run inside the groups phase on the pre-F3 step-(a) tree, frontier s42, 2000t) |
| out_t2/crowded_frontier_s43.jsonl | 434644 | see the table above (traces/tier2/crowded_frontier_s43.jsonl) | TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET (line 72) | out of git, same raw_evidence path |

| file | bytes | sha256 |
|---|---|---|
| evidence/f3_remeasure/traces/e30/f43_effd2e8fc.jsonl | 14574 | a8029466046f320f8bab8a1be88f10851d7173def8079ac0f8b8f1492620cb6e |
| evidence/f3_remeasure/traces/f43_30307228c.jsonl | 66250 | f212683819c2b4005eb0efbc07389518af21ab414c4612b5e46a8ed271c083eb |
| evidence/f3_remeasure/traces/f43_effd2e8fc.jsonl | 68604 | 82245e1386a98e8900d2da8a5b383cdfdde020c5c3721c8db12e8fd279e6f72f |
| evidence/f3_remeasure/traces/occ/u42.jsonl | 130492 | 04cc3998b4169acf6bdb986b7e233d2f13efbc9fc77098c81e464340acdd2b59 |
| evidence/f3_remeasure/traces/tier2/crowded_frontier_s43.jsonl | 434644 | 51326fffa4a7a91979e0454a7c08d767eeb6f2c7c85f48ec6818a033b5b5482b |
| evidence/f3_remeasure/traces/tier2/urban_political_s44.jsonl | 98627 | 5f6429429ffc280b5fc60199a960b40a20e0708f2eb86052857949ce1d4f134e |
| evidence/fixture/after_lifecycle.json | 911 | ae8989a00587a57a651e3782e2b2b1451d5e46e981cd5380fab22865c46e04f0 |
| evidence/fixture/before_lifecycle.json | 747 | 3a52688162de740dbd2371ba0b63f8f4df6df8712161fec7c1b745d5dc17368e |
| evidence/fixture/lag_crowded_400.json | 645 | 21650bf92fb8a3d7b8ad7f47aa9666d1e68057f7138692f0128f68bf28fba1d9 |
| evidence/out6/control_lifecycle_100t.jsonl | 3135 | ca9db430cb1f5f795b0ef3483ecf4a80634bc6d5a143b8ce2456d8a40a4e48e2 |
| evidence/out6/control_lifecycle_100t_g.jsonl | 6035 | 85dc90e1636442f02d461776666e7aaead9ab86e8f31285d3089f139b5e5502c |
| evidence/out6/crowded_frontier_6fdfdf555.jsonl | 61162 | 6e4267273587a54fee8a047548373bbd73f4400052aea4a3492a3f73bad08bc4 |
| evidence/out6/crowded_frontier_edb638b6a.jsonl | 106457 | 014f76d5ccc2f277f0edb85d92afc1874a899c7e83da21ab114956542aa160d7 |
| evidence/out6/frontier_living_world_6fdfdf555.jsonl | 61374 | 6bb2ff2d949577c6eb3ac9b431441cbb398596463e91bb5167b4763ccbb4e0f9 |
| evidence/out6/frontier_living_world_edb638b6a.jsonl | 168062 | 151a821e8bc68879d2743a2c098e4ea7a06042e098c2d73575bfaaa4f3fec995 |
| evidence/out6/urban_political_6fdfdf555.jsonl | 48393 | 0a9d84d95301741231cfa5e1ede0a790269b3e7ccca70fc244c309eec51b2f9c |
| evidence/out6/urban_political_edb638b6a.jsonl | 144165 | c846ca8d7a03717ad5e7696ebc664ac78d82bcdd14a0ac0bf1e6a86456833981 |
| evidence/set15/crowded_frontier_s42_base.json | 46562 | 20045036c84a90bc17ac5f5f249ca6dcf497348d312c83b9332272e2b27b3d5e |
| evidence/set15/crowded_frontier_s42_branch.json | 22551 | 1804d1c00ecff4c996a5778feee2cf964483a8687021fb6039eb8d4066af93a8 |
| evidence/set15/crowded_frontier_s43_base.json | 33186 | 25f8960c4dc2638e7a9fe632b2a73946446c9ff1957e1292af3fc32bc1d4e469 |
| evidence/set15/crowded_frontier_s43_branch.json | 28447 | c9be8a34b8dc89bcb0bb5eee66679768e25bb0634b4f9707d5d59641c3f7779f |
| evidence/set15/crowded_frontier_s44_base.json | 67347 | 5d90e5c41d8f4f90e09a702e48db3e5c7b98272fbaac4453f3bb4feea16c717d |
| evidence/set15/crowded_frontier_s44_branch.json | 23402 | 21fd98a6e21524afb3c28b3f98f1d684963c438daffafa03603b697423808024 |
| evidence/set15/crowded_frontier_s45_base.json | 39574 | 01fa71ef10559636f9dbee9f31d87425adfbe13b3e42b2e0f0175b2e5cafbbe5 |
| evidence/set15/crowded_frontier_s45_branch.json | 26151 | 9c8a61e41c9ec90035f1c373cda5ed21101507444a0ded6acbb3eb5b4eeffa7f |
| evidence/set15/crowded_frontier_s46_base.json | 34808 | a7624e41b0613be61dd6751cde5dc9dd5d8a9b957674462dd8a68a425aef8995 |
| evidence/set15/crowded_frontier_s46_branch.json | 20301 | 296642db52be223cc6cb439dadeb93fc388e2e1ce36aafd2a06a8f4a97332c55 |
| evidence/set15/frontier_living_world_s42_base.json | 40417 | 9e1fd118886e1811678021411dfd7e6b5cc86498230918287dffd48a991c3299 |
| evidence/set15/frontier_living_world_s42_branch.json | 41285 | 5ca5dfe65da60d4d5642967794a5b8c37c2a61560f91ee0b14a6a2bd498b5099 |
| evidence/set15/frontier_living_world_s43_base.json | 28826 | 97838b71ccc09ff9a11777c749a74ac7e03bc6d7d149e27e02177683b4ea53f5 |
| evidence/set15/frontier_living_world_s43_branch.json | 39774 | 9d654f1f3062983c0ebb5164d0df873d96f42477331293c1b7aab467b8aa2e15 |
| evidence/set15/frontier_living_world_s44_base.json | 39568 | 344db2c6af92350bf22fac638507cf92cb0756b60bc19151261745a7a0de263a |
| evidence/set15/frontier_living_world_s44_branch.json | 33703 | 1be181ea3c08c2ff0494ae5e46df4a2d95b84f19cef9eec9d85ecece299b4f78 |
| evidence/set15/frontier_living_world_s45_base.json | 57255 | d146961f2f2cd3f2f8ee09b942299ed71d3cb44067254a5e1e2acd8922420720 |
| evidence/set15/frontier_living_world_s45_branch.json | 51974 | 48d7c2b1571f41685d03e6cf9508c4d018940c8a94c68f5dd974ec4c009b86e2 |
| evidence/set15/frontier_living_world_s46_base.json | 65704 | 56d09b67f67e2e4d6010bc44a370f52b0c51aaafee1de3e08399a72b73bdca88 |
| evidence/set15/frontier_living_world_s46_branch.json | 31962 | dc0e7272b036e979daddee41e52ca645155aca0e38e7ac1a478eb266d26706e9 |
| evidence/set15/urban_political_s42_base.json | 24878 | cc409e6fa2ff93b5b178d2b886c871ed37af71f591a8126672a98c2b95f2aecf |
| evidence/set15/urban_political_s42_branch.json | 32120 | 51d0653345b3e109e9069c20c18de7e2ba933e334d4ce34bff07bddd6187d910 |
| evidence/set15/urban_political_s43_base.json | 68123 | 3b91f76c73142f016b0eba3b98bb07aa8a12cf3f68795a612fe2328da0ee5fbe |
| evidence/set15/urban_political_s43_branch.json | 22891 | 84850df75eb88b2bd2ba5c2ce9f14b3a8d4c310bba1ffe60209ca3724aed30c8 |
| evidence/set15/urban_political_s44_base.json | 39976 | f7c3ce834a8552128454797e1289fbc83f336cb4dc79c84fba7e7709e1e3a20d |
| evidence/set15/urban_political_s44_branch.json | 18381 | 73ef28ab4f04084d1f1e880f800c5a09c4fd45e98f7de1adbaa5c1ca5739cb15 |
| evidence/set15/urban_political_s45_base.json | 49108 | 394e5aa0ebafa42b614d1df9bd571931528b96b7e6779b7bcf9e312e86242097 |
| evidence/set15/urban_political_s45_branch.json | 27968 | f50cbadc719c504c5db1eda541ec550dc221a087d40857e7638c11332e22c81d |
| evidence/set15/urban_political_s46_base.json | 43671 | 9c54d3b457a780dc8d3161a5d45bf441cd02c438085ab1be5e74537ecdc9b30f |
| evidence/set15/urban_political_s46_branch.json | 20133 | a275a57e04a1bd8a640bb78278abc76f8160e92d0ad74196029abea321fb135f |
| evidence/stepa/crowded_frontier.json | 3358 | 658de55396e13c0ba0b1ab79b69876d77c96d7cbc23d7b10ac4ec2480eae804e |
| evidence/stepa/frontier_living_world.json | 3379 | 90de4bf7b484cf4ed56f5b4e9a44c8f4b61d95576e2e9a1673a136ed7e35a5bb |
| evidence/stepa/urban_political.json | 3367 | f02368f3c25d26198ca1b5cf7c926bc72f1f353720a04559a5331b93e0b5a8b4 |
| evidence/timing/count/crowded_frontier_base.json | 2744 | 5e7454e4b3b7c2f55b75592d894624c5979f47748433e89ead1e5c6d52fb9c90 |
| evidence/timing/count/crowded_frontier_branch.json | 2803 | 737d51642cba8b744791c1c69d8fd2e9b702066a207d868d512d03768148019d |
| evidence/timing/count/frontier_living_world_base.json | 2736 | 0217ab639e73685164c259d2187c33ced9a8ebc8b5eb1b3fb010de42361b8737 |
| evidence/timing/count/frontier_living_world_branch.json | 2783 | 535866e28f7aa117232270e458e705086059fcf0bf1481565c6034b8f7342259 |
| evidence/timing/count/urban_political_base.json | 2800 | d42da2665d13df23c69ed91e6b897efe2cce0e85944ac5bbcba1f51331851f2c |
| evidence/timing/count/urban_political_branch.json | 2734 | 44c85d9720d7da1527de5097d9bc86e895f9d4a844cb34d7d2dd60b3824c5a3a |
| evidence/timing/crowded_frontier_r1_base.done | 22 | 0287f3234471717bbc94b493adbbcc1790411695306b35ea016102525f5d61d1 |
| evidence/timing/crowded_frontier_r1_base.json | 2642 | 487e4cd536b7612b041ffefd3e4b0cc35199268739f0893f521c1caae2bce321 |
| evidence/timing/crowded_frontier_r1_branch.done | 22 | 86a5c24b369612fd7a3f3c9793222275a4c08b1095b576e73caa6dad7965b2ec |
| evidence/timing/crowded_frontier_r1_branch.json | 2665 | ea06bc63aab97766214a0ca30f14e6a1f43d82bf59c108ad0732c59f53f06a01 |
| evidence/timing/crowded_frontier_r2_base.done | 22 | 0ae1ee6b9c138d5fc3670835044f2fbf55b6622c4360e3253eb4980713a924f0 |
| evidence/timing/crowded_frontier_r2_base.json | 2627 | 236d89525c0af3680d4198b889a8bd0d20f24d39526e845a879becf257bccde5 |
| evidence/timing/crowded_frontier_r2_branch.done | 22 | f5b4ca8dbe4522cf8373567bb62134f2196690eab3b27e418fa3718a824c2269 |
| evidence/timing/crowded_frontier_r2_branch.json | 2618 | 6e0f235919085848d0c2397d658caebab76f691d669185c3d0fd6e8b7d049ce5 |
| evidence/timing/crowded_frontier_r3_base.done | 22 | 43ce8067965524811a5f4afeea17e855ed802e85b4f0456117d09deb85f965a6 |
| evidence/timing/crowded_frontier_r3_base.json | 2638 | 4f7969f22c75c04ad79e14bb27b41fdfe0b5718754f5c2efce6f37414ac31642 |
| evidence/timing/crowded_frontier_r3_branch.done | 22 | 18709d60fbd8e7a13290075623598a94768ebbbd196d0cfa6f8d10333b7e2d46 |
| evidence/timing/crowded_frontier_r3_branch.json | 2630 | 319a4fbee6d328119fd8367acf2ab605173659851fbe2c3f1e145b08ded7233b |
| evidence/timing/frontier_living_world_r1_base.done | 22 | 2476c974568aa4a0493b3d42bb83bf111e8712a7fda85491d4e47df5d73a3ee3 |
| evidence/timing/frontier_living_world_r1_base.json | 2658 | 66d7042cf8706bc402116d4fdb6373e6c51f62a302c1e0aac958d521be60522e |
| evidence/timing/frontier_living_world_r1_branch.done | 22 | 6e62faf3992e18c35099dff7bde43debbb5d7b02ef8957e432ecb95edb70b4ef |
| evidence/timing/frontier_living_world_r1_branch.json | 2669 | a9b7f4007b304c4ce23a154afee5739abdf3a1a23ae24d88df4faa18de782dc0 |
| evidence/timing/frontier_living_world_r2_base.done | 22 | fb58578a43015ba58ea65124088aec2c5fe378a9baf7082de5b10f2807223309 |
| evidence/timing/frontier_living_world_r2_base.json | 2631 | d2d2a7119825e9a8a47ee62384048d68ff940158a5e172c88c6be3eb91a43468 |
| evidence/timing/frontier_living_world_r2_branch.done | 22 | bd80a67c985a33cd6d55167485371516a7333b53c44da5bcd084b981cc3fab11 |
| evidence/timing/frontier_living_world_r2_branch.json | 2656 | 447d86ad944681f3f9179b5a87af10da15a58d2562ba30acc47ef6190d6c91e4 |
| evidence/timing/frontier_living_world_r3_base.done | 22 | 7cc60b0a4db4f365e8f4d690193d2a7660a93317cdab674828c3b4432a173922 |
| evidence/timing/frontier_living_world_r3_base.json | 2653 | 40bcee677bc074fcc1a94b6eb9029d267bf0620d7099f20326534ea88c02bd4b |
| evidence/timing/frontier_living_world_r3_branch.done | 22 | 35c94c30ae84f22c9535d617663d0252278a5085f260646663a6175f34d93d67 |
| evidence/timing/frontier_living_world_r3_branch.json | 2696 | 93e5e6bb81ac1be96b06ed6580edb10cb5e1ee152f696b92b0db1205596f83d9 |
| evidence/timing/smoke/crowded_frontier_base.json | 2787 | badffbe52a654750f971878537f013b4ed1653bc1113ef2d020ef4c1c0cc6ac2 |
| evidence/timing/smoke/crowded_frontier_base.stdout | 9134 | 3b882f58dbb5c47c7d4790a58338d7307db39abca65e17b9a13dcf3d74c5c759 |
| evidence/timing/smoke/crowded_frontier_branch.json | 2754 | 7b7f1a371ef0c54d13d6f3afb8f3ae338749c89c55f79af379c97f963db00781 |
| evidence/timing/smoke/crowded_frontier_branch.stdout | 8170 | 92248608330fd3ab7f8f8aabeb467816f6a7c60062affb959e6e3719c1f8f3df |
| evidence/timing/smoke/frontier_living_world_base.json | 2755 | 6a3c2ac63ef317d0dd33dc418f383a26edfb1c6c14104554fc362abeee77f9a8 |
| evidence/timing/smoke/frontier_living_world_base.stdout | 20363 | 5126598893dcec4bd34f43e591157f2718c780a69eccfdcdd910518994e17ec7 |
| evidence/timing/smoke/frontier_living_world_branch.json | 2729 | 46752781795093a305cd9a69807a46a6efc1cc6dbb2a3978ec08556ae75b3880 |
| evidence/timing/smoke/frontier_living_world_branch.stdout | 15341 | 736ae930da19a491805ed086da296c48e02166340a058c1829b5b9b07f3ea574 |
| evidence/timing/smoke/frontier_living_world_branch_repeat.json | 2717 | cfbf177f8844f8e544ca174035bd2df5195edbcaaa0f062e5532cb577efd4007 |
| evidence/timing/smoke/frontier_living_world_branch_repeat.stdout | 14193 | 522db1f3f5582074aeb9288c8fc512c9546ae444368a90650aeeb905abb0cbd5 |
| evidence/timing/smoke/urban_political_base.json | 2727 | 2fcf461406bd0f0c1d46bdd244a96af0302352ee50f76b02955128108422ca3f |
| evidence/timing/smoke/urban_political_base.stdout | 8516 | 1e890cf0b3e2fcfdc1041b8dea674309993853f4a07486a6cc90dfc1b1eb3a2e |
| evidence/timing/smoke/urban_political_branch.json | 2676 | 627d0c69ac414f4b03763c4872593185d973cb473e87737f4c8b6fc5e1c6ab30 |
| evidence/timing/smoke/urban_political_branch.stdout | 7898 | 32c5af0b3c8bda9af08d01e5413c2dd7fc21c6cea124d3f331fb7ad2bcb14e77 |
| evidence/timing/urban_political_r1_base.done | 22 | bee3b2fa0a7293f45c307ac04231afa2ddf6c37a501277f8677f814054afc314 |
| evidence/timing/urban_political_r1_base.json | 2649 | 288c74e5d038a473368f0f56bf90f06b92347fe9132376fb69291c710890e0d4 |
| evidence/timing/urban_political_r1_branch.done | 22 | 2dce02a9224b1df1a40d3925fc47b54e5e707c0dc5a75763d7ec4028258c4552 |
| evidence/timing/urban_political_r1_branch.json | 2577 | b242901ca8a84a231c321f91eb34dca0c79bb579ef40b4c88769d7d3e493caa4 |
| evidence/timing/urban_political_r2_base.done | 22 | 290703692552908be316e4cc5f87ce0f8e5d1df8c90e6b50accb35a7cea2f163 |
| evidence/timing/urban_political_r2_base.json | 2607 | f26355f5731fe9525f9c7cc318429106c22b3fdc206c74146b34bc23f9586b82 |
| evidence/timing/urban_political_r2_branch.done | 22 | a01268701c53db234bb8001a04aae4eff36ee792a1793674f593d160ec198a18 |
| evidence/timing/urban_political_r2_branch.json | 2634 | 20b2284e8ae41f15ef41d9bb58927972e57f8bff58953aafe9993450ec43e63b |
| evidence/timing/urban_political_r3_base.done | 22 | daa8a5146e9b430fa1f0b5546ff74f6a3d2bf1424dce9231e5a235c7c2cc8e05 |
| evidence/timing/urban_political_r3_base.json | 2614 | de7f73c9c7e60c0c3f7165999ba83544774f937d58c5064ce8fdfd5d76ce6b52 |
| evidence/timing/urban_political_r3_branch.done | 22 | 54fc9bcb874d6c0699b165a3ae1d064a460c085521cb570f637a85bbc23edc65 |
| evidence/timing/urban_political_r3_branch.json | 2673 | 9291e46e56dda804ff05b5cdcb789c7f000284763d652479ffa32e0b2a752fb6 |
| evidence/trace/crowded_6fdfdf555.jsonl | 108573 | bc47b4e86d3fbe4facaa61d35aef8909a06e4b6b9999a6a7b786d3e6419a578f |
| evidence/trace/crowded_edb638b6a.jsonl | 108957 | 37fd4d3a1e9f6f48ee2a0516f009df39d6e8dd828261ce26d23530d07d4b7ce7 |
| evidence/trace15/crowded_frontier_s42_base.json | 37639 | 4904124070f51f58115a65fbdd062b56441b5061a267ed8e538893d31f672645 |
| evidence/trace15/crowded_frontier_s42_branch.json | 32770 | 7932d537e9ef16653431fbc44d3788d6a737de2dfe451f8bca2a801d0ce3493f |
| evidence/trace59f/pair_rows/crowded_frontier_s42_base.json | 46562 | 20045036c84a90bc17ac5f5f249ca6dcf497348d312c83b9332272e2b27b3d5e |
| evidence/trace59f/pair_rows/crowded_frontier_s42_branch.json | 22551 | 1804d1c00ecff4c996a5778feee2cf964483a8687021fb6039eb8d4066af93a8 |
| evidence/trace59f/pair_rows/frontier_living_world_s43_base.json | 28826 | 97838b71ccc09ff9a11777c749a74ac7e03bc6d7d149e27e02177683b4ea53f5 |
| evidence/trace59f/pair_rows/frontier_living_world_s43_branch.json | 39774 | 9d654f1f3062983c0ebb5164d0df873d96f42477331293c1b7aab467b8aa2e15 |
| evidence/trace59f/pair_rows/urban_political_s42_base.json | 24878 | cc409e6fa2ff93b5b178d2b886c871ed37af71f591a8126672a98c2b95f2aecf |
| evidence/trace59f/pair_rows/urban_political_s42_branch.json | 32120 | 51d0653345b3e109e9069c20c18de7e2ba933e334d4ce34bff07bddd6187d910 |
| evidence/trace59f/pair_rows/urban_political_s44_base.json | 39976 | f7c3ce834a8552128454797e1289fbc83f336cb4dc79c84fba7e7709e1e3a20d |
| evidence/trace59f/pair_rows/urban_political_s44_branch.json | 18381 | 73ef28ab4f04084d1f1e880f800c5a09c4fd45e98f7de1adbaa5c1ca5739cb15 |
| evidence/trace59f/proof_runs_s42/crowded_frontier_s42.json | 22550 | 2a5e4676b1377f749bda68a1d472fc3a33ccfef7ccab005dea134d5c2adc9af2 |
| evidence/trace59f/proof_runs_s42/frontier_living_world_s42.json | 41284 | 7907897e716c7cada939e98ad757f8169ed80479faa258841cc8ec07f0c5641c |
| evidence/trace59f/proof_runs_s42/urban_political_s42.json | 32119 | 88184e2e4d81bccee6c8efeb3cff0246275c25294af805ddbcb252ee2e0f6669 |
