# #992 wolf-starvation read: evidence (plan 53eebf2fe8955aeed574b8ba79b23366ddc784c1b807f28d88dcb61f53921218, world frontier_living_world)
Evidence only: no line below says which reading holds.

## s42/47  windows [[2953, 3653]]
FRIENDLY_FIRE_ILLEGAL rows on NEW: 3; absent on BASE at the same (target, tick): 3 (3 with no BASE legality call at that key)
  t3151 target 38 BASE at that key: no call
  t3481 target 37 BASE at that key: no call
  t3482 target 37 BASE at that key: no call

### NEW  rows 701  death none in the run
attempts per target (legality calls; reasons):
  target 30: 15 calls, 4 legal, 11 illegal {'OUT_OF_RANGE': 11, 'LEGAL': 4}
  target 37: 2 calls, 0 legal, 2 illegal {'FRIENDLY_FIRE_ILLEGAL': 2}
  target 38: 1 calls, 0 legal, 1 illegal {'FRIENDLY_FIRE_ILLEGAL': 1}
hunger / hp every 25 ticks (tick, hunger, hp): [[2953, 88.59000000000259, 23], [2975, 89.25000000000261, 6], [3000, 90.00000000000264, 7], [3025, 90.75000000000267, 10], [3050, 91.5000000000027, 11], [3075, 92.25000000000273, 14], [3100, 93.00000000000276, 15], [3125, 93.75000000000279, 18], [3150, 94.50000000000281, 21], [3175, 95.25000000000284, 22], [3200, 96.00000000000287, 3], [3225, 96.7500000000029, 3], [3250, 97.50000000000293, 3], [3275, 98.25000000000296, 3], [3300, 99.00000000000298, 3], [3325, 99.75000000000301, 2], [3350, 100.0, 2], [3375, 100.0, 2], [3400, 100.0, 2], [3425, 100.0, 2], [3450, 100.0, 1], [3475, 100.0, 1], [3500, 100.0, 1], [3525, 100.0, 1], [3550, 100.0, 1], [3575, 100.0, 0], [3600, 100.0, 0], [3625, 100.0, 0], [3650, 100.0, 0], [3653, 100.0, 0]]  (hp min 0, hunger max 100.0)
hits taken by source: {'30': {'hits': 2, 'damage': 36, 'first_tick': 2972, 'last_tick': 3186}}
open ways and food steps (runs):
  t2953-2968: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t2969-2995: {'ways': ['SCAVENGE', 'HUNT_EAT_RAW'], 'open_food_steps': ['HUNT', 'SCAVENGE']}
  t2996-2998: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t2999-2999: {'ways': [], 'open_food_steps': []}
  t3000-3000: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3001-3019: {'ways': [], 'open_food_steps': []}
  t3020-3055: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3056-3069: {'ways': [], 'open_food_steps': []}
  t3070-3078: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3079-3130: {'ways': [], 'open_food_steps': []}
  t3131-3131: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3132-3161: {'ways': [], 'open_food_steps': []}
  t3162-3162: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3163-3172: {'ways': [], 'open_food_steps': []}
  t3173-3195: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3196-3211: {'ways': [], 'open_food_steps': []}
  t3212-3216: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3217-3230: {'ways': [], 'open_food_steps': []}
  t3231-3237: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3238-3249: {'ways': [], 'open_food_steps': []}
  t3250-3258: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3259-3268: {'ways': [], 'open_food_steps': []}
  t3269-3279: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3280-3287: {'ways': [], 'open_food_steps': []}
  t3288-3300: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3301-3306: {'ways': [], 'open_food_steps': []}
  t3307-3321: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3322-3553: {'ways': [], 'open_food_steps': []}
  t3554-3653: None
carcasses in reach, [id, edible, in way range] (runs):
  t2953-2968: []
  t2969-2995: [[1000052, True, True]]
  t2996-3011: [[1000052, False, True]]
  t3012-3047: []
  t3048-3068: [[1000052, False, True]]
  t3069-3553: []
  t3554-3653: None
last HUNT: tick 3321 target 30; the hunt ended: hunt_refused; flags {"beyond_hunt_radius": true, "last_call_at_target": "OUT_OF_RANGE", "legality_calls_at_target": 1, "manhattan_to_prey_next_row": 12.0, "prey_dead_tick": null, "refused": [{"reason": "OUT_OF_RANGE", "tick": 3313}], "struck_back": [], "subject_dead_tick": 3553}

### BASE  rows 701  death none in the run
attempts per target (legality calls; reasons):
  target 52: 20 calls, 8 legal, 12 illegal {'OUT_OF_RANGE': 11, 'LEGAL': 8, 'INSUFFICIENT_READINESS': 1}
hunger / hp every 25 ticks (tick, hunger, hp): [[2953, 88.59000000000259, 45], [2975, 89.25000000000261, 45], [3000, 90.00000000000264, 45], [3025, 90.75000000000267, 45], [3050, 91.5000000000027, 45], [3075, 92.25000000000273, 45], [3100, 93.00000000000276, 45], [3125, 93.75000000000279, 45], [3150, 94.50000000000281, 45], [3175, 95.25000000000284, 45], [3200, 96.00000000000287, 45], [3225, 96.7500000000029, 45], [3250, 97.50000000000293, 45], [3275, 98.25000000000296, 45], [3300, 99.00000000000298, 44], [3325, 99.75000000000301, 44], [3350, 100.0, 44], [3375, 100.0, 44], [3400, 100.0, 44], [3425, 100.0, 43], [3450, 100.0, 43], [3475, 100.0, 43], [3500, 100.0, 43], [3525, 100.0, 43], [3550, 100.0, 42], [3575, 60.630000000000024, 42], [3600, 61.38000000000005, 42], [3625, 62.13000000000008, 45], [3650, 62.88000000000011, 45], [3653, 62.97000000000011, 45]]  (hp min 42, hunger max 100.0)
hits taken by source: none
open ways and food steps (runs):
  t2953-3019: {'ways': ['SCAVENGE'], 'open_food_steps': ['SCAVENGE']}
  t3020-3434: {'ways': [], 'open_food_steps': []}
  t3435-3550: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3551-3564: {'ways': ['SCAVENGE'], 'open_food_steps': ['SCAVENGE']}
  t3565-3653: {'ways': [], 'open_food_steps': []}
carcasses in reach, [id, edible, in way range] (runs):
  t2953-3019: [[1000009, True, True]]
  t3020-3550: []
  t3551-3564: [[1000052, True, True]]
  t3565-3603: [[1000052, False, True]]
  t3604-3653: []
last HUNT: tick 3550 target 52; the hunt ended: prey_dead; flags {"beyond_hunt_radius": false, "last_call_at_target": "LEGAL", "legality_calls_at_target": 8, "manhattan_to_prey_next_row": 1.0, "prey_dead_tick": 3550, "refused": [{"reason": "OUT_OF_RANGE", "tick": 3538}, {"reason": "OUT_OF_RANGE", "tick": 3538}, {"reason": "INSUFFICIENT_READINESS", "tick": 3543}], "struck_back": [], "subject_dead_tick": null}

## s45/49  windows [[3369, 4069]]
FRIENDLY_FIRE_ILLEGAL rows on NEW: 0; absent on BASE at the same (target, tick): 0 (0 with no BASE legality call at that key)

### NEW  rows 701  death none in the run
attempts per target (legality calls; reasons):
  target 30: 20 calls, 4 legal, 16 illegal {'OUT_OF_RANGE': 16, 'LEGAL': 4}
hunger / hp every 25 ticks (tick, hunger, hp): [[3369, 100.0, 55], [3375, 100.0, 54], [3400, 100.0, 54], [3425, 100.0, 54], [3450, 100.0, 54], [3475, 100.0, 54], [3500, 100.0, 53], [3525, 100.0, 53], [3550, 100.0, 53], [3575, 100.0, 53], [3600, 100.0, 52], [3625, 100.0, 52], [3650, 100.0, 20], [3675, 100.0, 3], [3700, 100.0, 3], [3725, 100.0, 3], [3750, 100.0, 3], [3775, 100.0, 2], [3800, 100.0, 2], [3825, 100.0, 2], [3850, 100.0, 2], [3875, 100.0, 1], [3900, 100.0, 1], [3925, 100.0, 1], [3950, 100.0, 1], [3975, 100.0, 0], [4000, 100.0, 0], [4025, 100.0, 0], [4050, 100.0, 0], [4069, 100.0, 0]]  (hp min 0, hunger max 100.0)
hits taken by source: {'30': {'hits': 3, 'damage': 48, 'first_tick': 3626, 'last_tick': 3664}}
open ways and food steps (runs):
  t3369-3542: {'ways': [], 'open_food_steps': []}
  t3543-3686: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3687-3695: {'ways': [], 'open_food_steps': []}
  t3696-3708: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3709-3969: {'ways': [], 'open_food_steps': []}
  t3970-4069: None
carcasses in reach, [id, edible, in way range] (runs):
  t3369-3969: []
  t3970-4069: None
last HUNT: tick 3686 target 30; the hunt ended: hunt_refused; flags {"beyond_hunt_radius": true, "last_call_at_target": "OUT_OF_RANGE", "legality_calls_at_target": 3, "manhattan_to_prey_next_row": 12.0, "prey_dead_tick": null, "refused": [{"reason": "OUT_OF_RANGE", "tick": 3671}, {"reason": "OUT_OF_RANGE", "tick": 3681}, {"reason": "OUT_OF_RANGE", "tick": 3701}], "struck_back": [], "subject_dead_tick": 3969}

### BASE  rows 701  death none in the run
attempts per target (legality calls; reasons):
  target 1: 3 calls, 0 legal, 3 illegal {'FRIENDLY_FIRE_ILLEGAL': 3}
  target 2: 4 calls, 0 legal, 4 illegal {'FRIENDLY_FIRE_ILLEGAL': 4}
  target 5: 7 calls, 0 legal, 7 illegal {'FRIENDLY_FIRE_ILLEGAL': 7}
  target 6: 1 calls, 0 legal, 1 illegal {'FRIENDLY_FIRE_ILLEGAL': 1}
  target 7: 1 calls, 0 legal, 1 illegal {'FRIENDLY_FIRE_ILLEGAL': 1}
  target 8: 3 calls, 0 legal, 3 illegal {'FRIENDLY_FIRE_ILLEGAL': 3}
  target 10: 2 calls, 0 legal, 2 illegal {'FRIENDLY_FIRE_ILLEGAL': 2}
  target 30: 20 calls, 15 legal, 5 illegal {'LEGAL': 15, 'OUT_OF_RANGE': 4, 'INSUFFICIENT_READINESS': 1}
  target 36: 4 calls, 0 legal, 4 illegal {'FRIENDLY_FIRE_ILLEGAL': 4}
hunger / hp every 25 ticks (tick, hunger, hp): [[3369, 100.0, 44], [3375, 100.0, 44], [3400, 100.0, 44], [3425, 100.0, 43], [3450, 100.0, 43], [3475, 100.0, 43], [3500, 100.0, 43], [3525, 100.0, 43], [3550, 100.0, 42], [3575, 100.0, 42], [3600, 100.0, 42], [3625, 100.0, 42], [3650, 100.0, 42], [3675, 100.0, 41], [3700, 100.0, 41], [3725, 100.0, 41], [3750, 100.0, 41], [3775, 100.0, 41], [3800, 100.0, 41], [3825, 100.0, 40], [3850, 100.0, 40], [3875, 100.0, 40], [3900, 100.0, 40], [3925, 100.0, 40], [3950, 100.0, 39], [3975, 100.0, 39], [4000, 100.0, 39], [4025, 100.0, 39], [4050, 100.0, 39], [4069, 100.0, 39]]  (hp min 39, hunger max 100.0)
hits taken by source: none
open ways and food steps (runs):
  t3369-3470: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3471-3471: {'ways': [], 'open_food_steps': []}
  t3472-3472: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3473-3479: {'ways': ['SCAVENGE', 'HUNT_EAT_RAW'], 'open_food_steps': ['HUNT', 'SCAVENGE']}
  t3480-3505: {'ways': ['SCAVENGE'], 'open_food_steps': ['SCAVENGE']}
  t3506-3527: {'ways': ['SCAVENGE', 'HUNT_EAT_RAW'], 'open_food_steps': ['HUNT', 'SCAVENGE']}
  t3528-3528: {'ways': ['SCAVENGE'], 'open_food_steps': ['SCAVENGE']}
  t3529-3532: {'ways': ['SCAVENGE', 'HUNT_EAT_RAW'], 'open_food_steps': ['HUNT', 'SCAVENGE']}
  t3533-3560: {'ways': ['SCAVENGE'], 'open_food_steps': ['SCAVENGE']}
  t3561-3572: {'ways': ['SCAVENGE', 'HUNT_EAT_RAW'], 'open_food_steps': ['HUNT', 'SCAVENGE']}
  t3573-3593: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3594-3612: {'ways': [], 'open_food_steps': []}
  t3613-3641: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3642-3841: {'ways': [], 'open_food_steps': []}
  t3842-3973: {'ways': ['HUNT_EAT_RAW'], 'open_food_steps': ['HUNT']}
  t3974-4069: {'ways': [], 'open_food_steps': []}
carcasses in reach, [id, edible, in way range] (runs):
  t3369-3472: []
  t3473-3572: [[1000005, True, True]]
  t3573-4069: []
last HUNT: tick 3479 target 30; the hunt ended: hunt_refused; flags {"beyond_hunt_radius": true, "last_call_at_target": "OUT_OF_RANGE", "legality_calls_at_target": 2, "manhattan_to_prey_next_row": 12.0, "prey_dead_tick": null, "refused": [{"reason": "OUT_OF_RANGE", "tick": 3467}, {"reason": "OUT_OF_RANGE", "tick": 3467}], "struck_back": [], "subject_dead_tick": null}

