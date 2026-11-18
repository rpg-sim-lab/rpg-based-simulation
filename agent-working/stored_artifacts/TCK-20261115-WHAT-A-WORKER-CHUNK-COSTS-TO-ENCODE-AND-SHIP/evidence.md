---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261115-WHAT-A-WORKER-CHUNK-COSTS-TO-ENCODE-AND-SHIP
phase: open
artifact_type: report
date: 2026-11-16
tags: [performance]
---

# Evidence: chunk cost runs (db6b4579d, 2026-11-16)

9 runs, rc=0. final_hash per world, identical across thread, process and --no-probe:

    2026-11-16T08:35:39Z DONE chunk frontier_living_world thread rc=0 {"world": "frontier_living_world", "chunking": "thread", "no_probe": false, "final_hash": "e7096080e6a22ab56a28d4067fc1851f47bd56058a7c85627e143d8357c1b1fe"} rss_kb=256128
    2026-11-16T08:37:18Z DONE chunk frontier_living_world process rc=0 {"world": "frontier_living_world", "chunking": "process", "no_probe": false, "final_hash": "e7096080e6a22ab56a28d4067fc1851f47bd56058a7c85627e143d8357c1b1fe"} rss_kb=262148
    2026-11-16T08:37:43Z DONE chunk frontier_living_world control rc=0 {"world": "frontier_living_world", "chunking": "thread", "no_probe": true, "final_hash": "e7096080e6a22ab56a28d4067fc1851f47bd56058a7c85627e143d8357c1b1fe"} rss_kb=186420
    2026-11-16T08:37:44Z HASH OK frontier_living_world
    2026-11-16T08:39:22Z DONE chunk urban_political thread rc=0 {"world": "urban_political", "chunking": "thread", "no_probe": false, "final_hash": "5efc5d28045a9cd0771a6b5806bcd9add2d37166833d068a847ac2e1caa79202"} rss_kb=177476
    2026-11-16T08:46:53Z DONE chunk urban_political process rc=0 {"world": "urban_political", "chunking": "process", "no_probe": false, "final_hash": "5efc5d28045a9cd0771a6b5806bcd9add2d37166833d068a847ac2e1caa79202"} rss_kb=173560
    2026-11-16T08:54:52Z DONE chunk urban_political control rc=0 {"world": "urban_political", "chunking": "thread", "no_probe": true, "final_hash": "5efc5d28045a9cd0771a6b5806bcd9add2d37166833d068a847ac2e1caa79202"} rss_kb=119816
    2026-11-16T08:54:52Z HASH OK urban_political
    2026-11-16T09:04:39Z DONE chunk crowded_frontier thread rc=0 {"world": "crowded_frontier", "chunking": "thread", "no_probe": false, "final_hash": "24f5faa0fc8f8628dc989d0d0c280244d2a581995a2ae3197fe791701f3bc396"} rss_kb=237040
    2026-11-16T09:09:12Z DONE chunk crowded_frontier process rc=0 {"world": "crowded_frontier", "chunking": "process", "no_probe": false, "final_hash": "24f5faa0fc8f8628dc989d0d0c280244d2a581995a2ae3197fe791701f3bc396"} rss_kb=222652
    2026-11-16T09:10:36Z DONE chunk crowded_frontier control rc=0 {"world": "crowded_frontier", "chunking": "thread", "no_probe": true, "final_hash": "24f5faa0fc8f8628dc989d0d0c280244d2a581995a2ae3197fe791701f3bc396"} rss_kb=154824
    2026-11-16T09:10:36Z HASH OK crowded_frontier

```
world | chunking | packets/tick med | chunks/tick med | pkts/chunk med | request KB med | per-packet-sum KB med | encode ms med | decode ms med | compute ms med | codec round trip ms med/p90 | codec/compute med/p90 | seq collection ms/tick med | packet build ms/tick med | validate ms med
frontier_living_world | thread | 13 | 5 | 3 | 1112 | 2609 | 34.3 | 25.3 | 0.76 | 60.2/86.0 | 78/366 | 2.34 | 0.20 | 0.009
   bytes w/o private caches med KB 1112  response KB med 0.61  result enc+dec ms med 0.143  min codec round trip ms 29.2
   share of chunks with codec < compute: 0 / 971
frontier_living_world | process | 13 | 2 | 6 | 1108 | 5937 | 33.8 | 25.5 | 1.23 | 59.8/81.6 | 47/330 | 2.15 | 0.18 | 0.012
   bytes w/o private caches med KB 1107  response KB med 1.07  result enc+dec ms med 0.206  min codec round trip ms 26.7
   share of chunks with codec < compute: 0 / 496
urban_political | thread | 6 | 5 | 1 | 679 | 751 | 19.5 | 14.8 | 0.22 | 34.7/51.1 | 146/314 | 1.34 | 0.13 | 0.008
   bytes w/o private caches med KB 679  response KB med 0.32  result enc+dec ms med 0.104  min codec round trip ms 16.4
   share of chunks with codec < compute: 0 / 981
urban_political | process | 6 | 3 | 2 | 703 | 1538 | 19.2 | 14.4 | 0.79 | 33.9/47.8 | 44/248 | 1.32 | 0.12 | 0.007
   bytes w/o private caches med KB 703  response KB med 0.52  result enc+dec ms med 0.126  min codec round trip ms 15.8
   share of chunks with codec < compute: 0 / 505
crowded_frontier | thread | 6 | 5 | 1 | 1025 | 1255 | 28.7 | 21.1 | 0.51 | 50.1/65.5 | 93/422 | 1.58 | 0.13 | 0.007
   bytes w/o private caches med KB 1024  response KB med 0.37  result enc+dec ms med 0.107  min codec round trip ms 22.0
   share of chunks with codec < compute: 0 / 956
crowded_frontier | process | 6 | 2 | 2 | 1026 | 2439 | 27.5 | 20.6 | 0.87 | 48.7/66.6 | 53/305 | 1.55 | 0.13 | 0.008
   bytes w/o private caches med KB 1026  response KB med 0.59  result enc+dec ms med 0.135  min codec round trip ms 21.9
   share of chunks with codec < compute: 0 / 489
```
