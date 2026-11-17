---
status: active
layer: simulation
authority: P1
audience: agent
artifact_type: report
ticket_id: TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP
phase: done
date: 2026-11-02
tags: []
---

# Raw run dumps (kept out of git)

The raw per-run and per-tick files of this ticket's measurements (41 files, 370,073 bytes: run json, per-tick jsonl traces, run stdout and `.done` markers) are NOT committed. They were committed first and removed at the re-sync onto #826, following the owner's trim ruling (#715 6573916118) and the shape #826 used for its own raw dumps. The files themselves live in the author's scratch `/data/vboxuser/Work/groups_base/raw_evidence/` under the same relative path as below (relative to `agent-working/stored_artifacts/TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP/`), and the originals are in `/data/vboxuser/Work/groups_base/out*` and `trees/*`. Every number the disclosures use is in the kept summaries (`.txt`), scripts (`.py`, `.sh`), READMEs, `pr_notes.md` and divergence 2.146; the sha256 below lets a copy be checked against the file that was removed.

Their `.json` files were added while this folder was still under `staging_artifacts/` (not ignored) and moved here with `git mv`; `.gitignore` ignores `stored_artifacts/**/*.json` only for new files, which is why they were tracked at all.

| file | bytes | sha256 |
|---|---|---|
| evidence/base15/crowded_frontier_s42.jsonl | 1756 | a6be055d804e4c77663263011515c3c4a13f4cf504f28f034202aa8d3f577d3c |
| evidence/base15/crowded_frontier_s43.jsonl | 1696 | e041c2be2b6897bedac9ece2d9649debde9992eda56e9e90da4953398a661a33 |
| evidence/base15/crowded_frontier_s44.jsonl | 1556 | e1718513a94111679a7fcd93d354f036cec9acd2155bab34d7ea55f60722dea5 |
| evidence/base15/crowded_frontier_s45.jsonl | 1688 | d5076f26e60af7860d09f875d40ff593e72ffe65e38a88e3d6480941ea27794c |
| evidence/base15/crowded_frontier_s46.jsonl | 1764 | e512f1131b029ad2de331bc01f3337194f0fd9a9a165950d540042eb24403540 |
| evidence/base15/frontier_living_world_s42.jsonl | 1800 | 06f9e4e11e31ccfc4c9e5d9456b418e70b2811644596b68bcd042a80c7663150 |
| evidence/base15/frontier_living_world_s43.jsonl | 1722 | 4880bf149b5d649cc1ec317cc6618da7ceedf1ee950a3c319df026e793677ab3 |
| evidence/base15/frontier_living_world_s44.jsonl | 1696 | 80f44e42ac64108c7097bdce8828d77bbbac78de335158db847217058da4ed66 |
| evidence/base15/frontier_living_world_s45.jsonl | 1730 | 49c1e0dcc8d7877ec7445b9d1d11ad89d2a30e2315bfe3df4a1e6b1601a6055a |
| evidence/base15/frontier_living_world_s46.jsonl | 1755 | e5788fbbf9997ea8f6c2167242567ebfd1a1c1d4b2fe15c8b510fe03c59cec29 |
| evidence/base15/urban_political_s42.jsonl | 1643 | b6044ca4d14cf97794a46c57c6078fad09b8e7938bf1017eb4725ddc452ce376 |
| evidence/base15/urban_political_s43.jsonl | 1593 | 595686c5e46352cf82f6a609f139eccfdbb7a331f574b1ded349394da1f68e52 |
| evidence/base15/urban_political_s44.jsonl | 1686 | 6eecb387558d492def57d35545118d48ebcb28bdb9df253c7c96e57022974b8c |
| evidence/base15/urban_political_s45.jsonl | 1753 | ec932bca8be428b9c11587aa9bc57677cd90d6f58f098396ac0d72f815324aa9 |
| evidence/base15/urban_political_s46.jsonl | 1673 | 52ee448ccfea68a2c405d8b4de570ef465b997252550587fe4665beb75f6181b |
| evidence/base3/crowded_frontier_s42.jsonl | 2148 | 4984a13342cd20af54d4b10db2b98e5769ba13e1657883e78b8f23d497180aff |
| evidence/base3/frontier_living_world_s42.jsonl | 2196 | 768fba74e152cc044a28b513bd55d4803a63d92d6c0297c0ae47dfdb59b0ab15 |
| evidence/base3/urban_political_s42.jsonl | 2032 | 04c815fd2999bb1fdefec4aaef1eaee508ae86d4a75ef9cfcb2248e82a3013bf |
| evidence/control2/ctl_base.jsonl | 35292 | e0cb10bd44d065e79322fefe10eb23d0131e6ea40b2a8f9df12d8580e6e28451 |
| evidence/control2/ctl_branch.jsonl | 35330 | dcc9b84b7211e259174f6de9662c05c5a0bcd5a6f496d10b2d76b1a9a4b6c6cc |
| evidence/profile_pair/base_frontier_living_world_s42.jsonl | 75668 | 549a2bf463327c787ef46a5c8f0c7f57fb51d4a9924a1302e1b41e3ab8b05057 |
| evidence/profile_pair/branch_frontier_living_world_s42.jsonl | 133514 | d302cc52c1294d01466fd3fe244527e6be52bb84a9c7c882a2fc385a7fc8224b |
| evidence/profile_pair/control_branch_lifecycle_100t.jsonl | 32118 | 10babc80c3a51a7d777c8adc584a96c5f6560fa8b51a03490392dcf60335140c |
| evidence/timing18/crowded_frontier_r1_6fdfdf555.jsonl | 2150 | 1e44e344a9a039fd6a9b0cea6703d17181feffa77b1ce59c0fa9acb50bc549ea |
| evidence/timing18/crowded_frontier_r1_edb638b6a.jsonl | 791 | ca828718cd7f401f73d60954bc875f92aa1445eba69c914da2c51f0c265a0e6b |
| evidence/timing18/crowded_frontier_r2_6fdfdf555.jsonl | 2151 | bbcf7f5a9080ae5cd00f08a5a8433a4a106b9112332b5b2861864b29156c5e80 |
| evidence/timing18/crowded_frontier_r2_edb638b6a.jsonl | 790 | 6481b4ca9fe3483618804e8d8fd6be5df3a647c06fde11850ed185f14ebd5b9f |
| evidence/timing18/crowded_frontier_r3_6fdfdf555.jsonl | 2150 | bfe471b7e0fda3a466a2226d099ad1c435caa1d2efd98db1cb4c224f53099cf0 |
| evidence/timing18/crowded_frontier_r3_edb638b6a.jsonl | 792 | 50821b09b4f670824747c0abffc9f94682928f13a6d640fc8342d18b9b8caa8d |
| evidence/timing18/frontier_living_world_r1_6fdfdf555.jsonl | 2194 | 68733f7373d7d4111c85cb69439528df8de62138c62abdaf4ce93d620385e501 |
| evidence/timing18/frontier_living_world_r1_edb638b6a.jsonl | 799 | d623dabe0f7091dc220d12f94b33b55ead6a780659d10ca6ff24797d99c7746d |
| evidence/timing18/frontier_living_world_r2_6fdfdf555.jsonl | 2193 | a55a50eec9a133299489958cdb54d1429d8671bc1b2194a25b342788cfa1e5b4 |
| evidence/timing18/frontier_living_world_r2_edb638b6a.jsonl | 799 | 8ed01d43bac26e558f221879f9732bcee0d1dd9b89407ff35bc7ee45daab05e9 |
| evidence/timing18/frontier_living_world_r3_6fdfdf555.jsonl | 2195 | 7f4a5892e61669261cf22fe0caddc406cf52848277c2e34c10fd08b4ff83ad41 |
| evidence/timing18/frontier_living_world_r3_edb638b6a.jsonl | 799 | a2f1340fe9c4673c3ef6be5adabafa9a13ba7a9f575dfa316d4b63d54665ce36 |
| evidence/timing18/urban_political_r1_6fdfdf555.jsonl | 2033 | 56a2a087e6a75ec32118eac4bc95728839a0351714aa7aa47582d434eaadd80e |
| evidence/timing18/urban_political_r1_edb638b6a.jsonl | 788 | fbf1381386264c8e847403f11ad45e3e3bde9f4712bb0b3931136d80c0bb0a6f |
| evidence/timing18/urban_political_r2_6fdfdf555.jsonl | 2032 | 19d96a8d4792ec30a245920d9789e7fd5c5587dc0f3f5a05d6d5e95118847fce |
| evidence/timing18/urban_political_r2_edb638b6a.jsonl | 785 | 0dc0f73837ed1f214d459ad0830990c74a99c0e0c4eef72bd0f26811b20d2a89 |
| evidence/timing18/urban_political_r3_6fdfdf555.jsonl | 2035 | 25a70baed4804128b9c5e52a1e1e5ef492f6f952e65ae1c65e03c0d33721e6da |
| evidence/timing18/urban_political_r3_edb638b6a.jsonl | 788 | 878dbd619da7e488eabc4dd45f385a35a1e36d81e3921f63730960d105cbabb5 |
