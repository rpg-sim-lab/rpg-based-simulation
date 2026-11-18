---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261115-PER-PHASE-TICK-COST-AFTER-THE-HOSTILITY-AND-COOPERATION-FIXES
phase: open
artifact_type: report
date: 2026-11-16
tags: [performance]
---

# Evidence: stage 0 runs (db6b4579d, 2026-11-16)

```

## frontier_living_world: tick mean ms per run [57.55, 34.61, 42.65], spread (max-min)/median 53.8%, rss [98.6, 99.0, 99.0]
resolution_overhead          ms   9.946 [8.903-14.958]  share  25.7%
advancement                  ms   8.421 [6.731-11.540]  share  19.7%
combat_engagement            ms   6.983 [6.038-9.043]  share  16.4%
collection                   ms   4.652 [3.413-6.429]  share  10.9%
locomotion                   ms   3.742 [2.894-5.111]  share   8.8%
cooperation                  ms   3.307 [2.582-4.127]  share   7.5%
governance_ecology           ms   1.955 [1.348-2.196]  share   3.9%
diplomatic_transitions       ms   0.469 [0.419-0.782]  share   1.2%
scheduling                   ms   0.546 [0.451-0.707]  share   1.3%
economy                      ms   0.552 [0.495-0.691]  share   1.3%
interaction                  ms   0.365 [0.267-0.442]  share   0.8%
trust_validity               ms   0.257 [0.218-0.312]  share   0.6%
contracts_production         ms   0.219 [0.149-0.257]  share   0.4%
init                         ms   0.250 [0.145-0.253]  share   0.4%
final_integrity              ms   0.135 [0.104-0.175]  share   0.3%
information_belief           ms   0.104 [0.075-0.114]  share   0.2%
military_conflict            ms   0.059 [0.047-0.093]  share   0.1%
faction_sentiment            ms   0.058 [0.042-0.064]  share   0.1%
memory_update                ms   0.042 [0.030-0.043]  share   0.1%
faction_decision             ms   0.032 [0.026-0.043]  share   0.1%
faction_awareness            ms   0.038 [0.020-0.039]  share   0.1%
cleanup                      ms   0.028 [0.027-0.034]  share   0.1%
persistence                  ms   0.025 [0.021-0.027]  share   0.1%
world_emergence              ms   0.007 [0.005-0.009]  share   0.0%
self_model                   ms   0.007 [0.006-0.007]  share   0.0%
progression_conversion       ms   0.004 [0.004-0.005]  share   0.0%
information_propagation      ms   0.004 [0.003-0.004]  share   0.0%
information_intent_execution ms   0.003 [0.003-0.004]  share   0.0%
role_model_selection         ms   0.003 [0.002-0.003]  share   0.0%
habit_bias_action_style      ms   0.003 [0.003-0.003]  share   0.0%
summary keys ['per_tick_costs', 'runtime_mode_sequence', 'work_mean_per_tick', 'events', 'flag_override', 'replay', 'peak_rss_mb']

## urban_political: tick mean ms per run [24.36, 23.75, 25.34], spread (max-min)/median 6.5%, rss [85.5, 85.6, 85.5]
resolution_overhead          ms   6.788 [6.457-7.075]  share  27.9%
advancement                  ms   4.798 [4.668-4.965]  share  19.7%
combat_engagement            ms   3.915 [3.867-4.189]  share  16.3%
collection                   ms   2.524 [2.480-2.532]  share  10.4%
locomotion                   ms   1.785 [1.782-1.852]  share   7.3%
cooperation                  ms   1.638 [1.627-1.676]  share   6.7%
scheduling                   ms   0.429 [0.427-0.445]  share   1.8%
governance_ecology           ms   0.427 [0.415-0.447]  share   1.8%
diplomatic_transitions       ms   0.440 [0.405-0.471]  share   1.9%
economy                      ms   0.387 [0.368-0.401]  share   1.5%
interaction                  ms   0.252 [0.229-0.261]  share   1.0%
trust_validity               ms   0.173 [0.169-0.179]  share   0.7%
contracts_production         ms   0.140 [0.134-0.141]  share   0.6%
init                         ms   0.137 [0.130-0.140]  share   0.6%
final_integrity              ms   0.109 [0.100-0.112]  share   0.4%
information_belief           ms   0.061 [0.059-0.062]  share   0.2%
military_conflict            ms   0.046 [0.045-0.050]  share   0.2%
faction_sentiment            ms   0.043 [0.040-0.052]  share   0.2%
faction_decision             ms   0.028 [0.027-0.028]  share   0.1%
cleanup                      ms   0.035 [0.026-0.053]  share   0.1%
faction_awareness            ms   0.021 [0.019-0.026]  share   0.1%
memory_update                ms   0.020 [0.020-0.020]  share   0.1%
persistence                  ms   0.020 [0.019-0.022]  share   0.1%
self_model                   ms   0.006 [0.006-0.007]  share   0.0%
world_emergence              ms   0.005 [0.005-0.005]  share   0.0%
information_propagation      ms   0.003 [0.003-0.004]  share   0.0%
information_intent_execution ms   0.003 [0.003-0.003]  share   0.0%
progression_conversion       ms   0.003 [0.003-0.004]  share   0.0%
habit_bias_action_style      ms   0.003 [0.003-0.003]  share   0.0%
role_model_selection         ms   0.002 [0.002-0.003]  share   0.0%
summary keys ['per_tick_costs', 'runtime_mode_sequence', 'work_mean_per_tick', 'events', 'flag_override', 'replay', 'peak_rss_mb']

## crowded_frontier: tick mean ms per run [28.31, 26.81, 26.23], spread (max-min)/median 7.8%, rss [95.6, 95.7, 95.5]
resolution_overhead          ms   5.917 [5.795-6.153]  share  22.1%
advancement                  ms   5.642 [5.503-5.957]  share  21.0%
combat_engagement            ms   4.089 [3.977-4.242]  share  15.2%
collection                   ms   2.776 [2.735-3.081]  share  10.4%
locomotion                   ms   2.625 [2.581-2.855]  share   9.8%
cooperation                  ms   2.023 [2.021-2.170]  share   7.7%
governance_ecology           ms   1.124 [1.101-1.130]  share   4.2%
diplomatic_transitions       ms   0.440 [0.427-0.475]  share   1.6%
economy                      ms   0.452 [0.412-0.465]  share   1.6%
scheduling                   ms   0.402 [0.400-0.425]  share   1.5%
interaction                  ms   0.256 [0.246-0.258]  share   0.9%
trust_validity               ms   0.175 [0.172-0.177]  share   0.7%
contracts_production         ms   0.131 [0.124-0.141]  share   0.5%
init                         ms   0.127 [0.127-0.136]  share   0.5%
final_integrity              ms   0.112 [0.108-0.116]  share   0.4%
military_conflict            ms   0.052 [0.048-0.066]  share   0.2%
cleanup                      ms   0.081 [0.062-0.084]  share   0.3%
information_belief           ms   0.058 [0.055-0.060]  share   0.2%
faction_sentiment            ms   0.048 [0.047-0.054]  share   0.2%
memory_update                ms   0.043 [0.043-0.045]  share   0.2%
faction_decision             ms   0.030 [0.030-0.032]  share   0.1%
faction_awareness            ms   0.026 [0.024-0.028]  share   0.1%
persistence                  ms   0.019 [0.019-0.019]  share   0.1%
world_emergence              ms   0.005 [0.005-0.019]  share   0.0%
self_model                   ms   0.006 [0.005-0.006]  share   0.0%
progression_conversion       ms   0.004 [0.003-0.004]  share   0.0%
information_propagation      ms   0.003 [0.003-0.003]  share   0.0%
habit_bias_action_style      ms   0.003 [0.003-0.003]  share   0.0%
information_intent_execution ms   0.003 [0.003-0.003]  share   0.0%
role_model_selection         ms   0.002 [0.002-0.002]  share   0.0%
summary keys ['per_tick_costs', 'runtime_mode_sequence', 'work_mean_per_tick', 'events', 'flag_override', 'replay', 'peak_rss_mb']

frontier_living_world runs 4-6 (re-run): mean tick 39.75, 43.92, 37.16 ms; peak RSS 96.9, 99.1, 97.0 MB

Quiet gate (passing readings) and swap counters, from the batch log:
2026-11-16T08:18:56Z START head=db6b4579d897728bf0124aa7989821a5348d6ce1 path=/data/vboxuser/Work/rpg-based-simulation/.claude/worktrees/perf-planner
2026-11-16T08:21:13Z GATE try=3 rc=0 loadavg1 0.44; available 5221.9 MB; busy % of allowed CPUs cpu4 1.0, cpu5 8.2; swap in+out pages 0
2026-11-16T08:22:39Z GATE try=2 rc=0 loadavg1 0.25; available 5233.9 MB; busy % of allowed CPUs cpu4 1.2, cpu5 3.5; swap in+out pages 0
2026-11-16T08:23:59Z GATE try=2 rc=0 loadavg1 0.38; available 5188.4 MB; busy % of allowed CPUs cpu4 5.6, cpu5 9.4; swap in+out pages 0
2026-11-16T08:25:22Z GATE try=2 rc=0 loadavg1 0.45; available 5265.3 MB; busy % of allowed CPUs cpu4 0.4, cpu5 2.0; swap in+out pages 0
2026-11-16T08:25:40Z GATE try=1 rc=0 loadavg1 0.56; available 5267.9 MB; busy % of allowed CPUs cpu4 0.0, cpu5 4.7; swap in+out pages 0
2026-11-16T08:29:10Z GATE try=4 rc=0 loadavg1 0.06; available 5381.5 MB; busy % of allowed CPUs cpu4 0.6, cpu5 1.4; swap in+out pages 0
2026-11-16T08:30:28Z GATE try=2 rc=0 loadavg1 0.06; available 5361.4 MB; busy % of allowed CPUs cpu4 0.0, cpu5 1.8; swap in+out pages 0
2026-11-16T08:30:41Z GATE try=1 rc=0 loadavg1 0.26; available 5354.3 MB; busy % of allowed CPUs cpu4 1.6, cpu5 5.7; swap in+out pages 0
2026-11-16T08:30:55Z GATE try=1 rc=0 loadavg1 0.45; available 5279.0 MB; busy % of allowed CPUs cpu4 8.7, cpu5 2.3; swap in+out pages 0
2026-11-16T08:31:09Z GATE try=1 rc=0 loadavg1 0.57; available 5250.8 MB; busy % of allowed CPUs cpu4 4.8, cpu5 5.7; swap in+out pages 0
2026-11-16T08:31:23Z GATE try=1 rc=0 loadavg1 0.58; available 5288.9 MB; busy % of allowed CPUs cpu4 3.0, cpu5 6.5; swap in+out pages 0
2026-11-16T08:31:36Z GATE try=1 rc=0 loadavg1 0.82; available 5302.4 MB; busy % of allowed CPUs cpu4 3.8, cpu5 2.6; swap in+out pages 0
2026-11-16T08:31:45Z STAGE0 COMPLETE
2026-11-16T08:32:56Z GATE try=2 rc=0 loadavg1 0.62; available 5358.3 MB; busy % of allowed CPUs cpu4 1.4, cpu5 2.5; swap in+out pages 0
2026-11-16T08:35:45Z GATE try=1 rc=0 loadavg1 1.17; available 5404.4 MB; busy % of allowed CPUs cpu4 0.4, cpu5 1.6; swap in+out pages 0
2026-11-16T08:37:24Z GATE try=1 rc=0 loadavg1 1.11; available 5432.1 MB; busy % of allowed CPUs cpu4 1.4, cpu5 2.2; swap in+out pages 0
2026-11-16T08:37:49Z GATE try=1 rc=0 loadavg1 1.12; available 5403.0 MB; busy % of allowed CPUs cpu4 4.0, cpu5 4.7; swap in+out pages 0
2026-11-16T08:46:01Z GATE try=7 rc=0 loadavg1 0.67; available 5174.9 MB; busy % of allowed CPUs cpu4 2.2, cpu5 6.4; swap in+out pages 0
2026-11-16T08:54:38Z GATE try=8 rc=0 loadavg1 0.98; available 4908.8 MB; busy % of allowed CPUs cpu4 6.1, cpu5 7.6; swap in+out pages 0
2026-11-16T09:02:36Z GATE try=8 rc=0 loadavg1 0.99; available 5087.4 MB; busy % of allowed CPUs cpu4 1.6, cpu5 1.4; swap in+out pages 0
2026-11-16T09:08:01Z GATE try=4 rc=0 loadavg1 0.41; available 5191.5 MB; busy % of allowed CPUs cpu4 0.2, cpu5 1.8; swap in+out pages 0
2026-11-16T09:10:23Z GATE try=2 rc=0 loadavg1 0.8; available 5189.3 MB; busy % of allowed CPUs cpu4 1.4, cpu5 4.1; swap in+out pages 0
2026-11-16T09:10:37Z RERUN START frontier r4-r6 head=db6b4579d897728bf0124aa7989821a5348d6ce1
2026-11-16T09:14:00Z GATE try=4 rc=0 loadavg1 0.5; available 5589.9 MB; busy % of allowed CPUs cpu4 2.0, cpu5 2.2; swap in+out pages 0
2026-11-16T09:14:01Z SWAP before r4 pswpin=1059720 pswpout=2377843 vmstat_si=0 vmstat_so=0
2026-11-16T09:14:13Z SWAP after r4 pswpin=1059733 pswpout=2377843 vmstat_si=0 vmstat_so=0
2026-11-16T09:16:29Z GATE try=3 rc=0 loadavg1 0.28; available 5702.0 MB; busy % of allowed CPUs cpu4 3.7, cpu5 3.3; swap in+out pages 0
2026-11-16T09:16:30Z SWAP before r5 pswpin=1059771 pswpout=2377843 vmstat_si=0 vmstat_so=0
2026-11-16T09:16:43Z SWAP after r5 pswpin=1059775 pswpout=2377843 vmstat_si=0 vmstat_so=0
2026-11-16T09:17:54Z GATE try=2 rc=0 loadavg1 0.28; available 5679.5 MB; busy % of allowed CPUs cpu4 0.4, cpu5 2.2; swap in+out pages 0
2026-11-16T09:17:55Z SWAP before r6 pswpin=1059777 pswpout=2377843 vmstat_si=0 vmstat_so=0
2026-11-16T09:18:07Z SWAP after r6 pswpin=1059777 pswpout=2377843 vmstat_si=0 vmstat_so=0
2026-11-16T09:18:07Z RERUN COMPLETE
```

An aborted first launch at 08:18:24Z (on perf-planner-next, before the detach) ran no measurement: one failed gate, then killed. Its log was kept aside.
