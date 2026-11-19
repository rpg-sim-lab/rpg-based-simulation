---
status: active
layer: simulation
authority: P1
audience: agent
artifact_type: report
ticket_id: TCK-20261118-TEMPORAL-SCALE-AUDIT-CAN-THE-CURRENT-CALENDAR-CARRY-MULTI-GENERATION-RUNS
date: 2026-11-19
---

# Tick-constant inventory and tuning-value inventory (scope 7)

Read-only audit of `src/` and `data/content/` on main a30847030. No code change and no run. 1 tick = 36 s at 2,400 ticks/day; 1 h = 100 ticks; 1 day = 2,400; 1 fantasy year = 288,000.

## How it was built, and what it does not cover

- **Named constants:** an AST scan of every `src/**/*.py` module and class for UPPER_CASE names bound to a number or a tuple, list, dict or set of numbers: 387 hits, all in Tables A and C. **Dataclass and Pydantic field defaults and call-site literals** that carry a tick value were collected by pattern search (names holding tick, age, interval, cooldown, window, ttl, duration, expiry, modulo): they are in Table A.
- **Not covered:** a number written inline inside a function body without a name or a field (a threshold in an `if`, a weight in an expression). They are too many to list by hand and a scan cannot tell tuning from arithmetic. Table A lists the ones that sit on a tick comparison or a `tick %` cadence. If the owner wants the rest, the next step is a scan that proposes them for a designer to judge. This is a gap, stated, not a claim of completeness.
- **Not a tuning value:** enum members (`EntityRole.HERO = 0` and the like) are identifiers, not settings; they are grouped in Table C with their reason.
- **Classification:** REALISM-TUNED means the value matches a believable real duration at 36 s per tick. WINDOW-FITTED means it reads as chosen so the event happens inside a short run or a gate window. NEITHER (engineering cadence) is my addition: a cadence, cache lifetime, watchdog or sampler that makes no game-time claim. UNDETERMINED means the code does not say and the owner or rpg-designer has to judge. The two ticket classes are my reading of the value and its comment; nothing here is a ruling.

## Clocks

- `state.tick`: the run's tick counter, +1 per kernel tick. Nearly every interval, cooldown and window below is read on it.
- `state.world_time`: never wraps, +1 per tick; the day cycle reads it through `time_of_day` / `is_night` in `src/core/calendar.py`. Only the night boundaries read it.
- `lifecycle.age_ticks`: a per-body age in ticks, advanced by the lifecycle system; life stages and `max_age_ticks` read it.
- Counters local to one task, project or scenario (a work shift, a chase, a stall counter): they count ticks since a reset and are not the global clock.
- The world clock and `state.tick` move together today, so the two are not distinguished in the code; a checkpoint restore that did not carry both would split them (see TCK-20261110-A-RUN-RESTORED-FROM-A-CHECKPOINT-EQUALS-THE-UNINTERRUPTED-RUN-TICK-BY-TICK).

## Table A: tick-valued constants in src

| file:line | constant | value | real time at 2,400 ticks/day | class | clock | note |
|---|---|---|---|---|---|---|
| src/core/calendar.py:10 | TICKS_PER_DAY | 2400 | 24 h | REALISM-TUNED | defines the clock | the approved baseline (2026-08-29): 1 tick = 36 s |
| src/core/calendar.py:13 | TICKS_PER_FANTASY_YEAR | 288000 | 120 days | REALISM-TUNED | defines the clock | 120 days; 4 seasons of 30 days |
| src/core/calendar.py:17 | NIGHT_START_TICK | 1800 | 18 h | REALISM-TUNED | world_time (time of day) | 18:00; night is half of every day |
| src/core/calendar.py:18 | NIGHT_END_TICK | 600 | 6 h | REALISM-TUNED | world_time (time of day) | 06:00 |
| src/core/state.py:168 | LifecycleComponent.max_age_ticks (default) | 20160000 | 70 fantasy years | REALISM-TUNED | lifecycle.age_ticks | 70 fantasy years = 8,400 days |
| src/ai/life_stage.py:53 | CHILD to ADULT boundary (literal) | 3456000 | 12 fantasy years | REALISM-TUNED | lifecycle.age_ticks | 12 fantasy years; duplicated as a literal in the cohort model (WORLD-DEMO-003) |
| src/ai/life_stage.py:55 | ADULT to ELDER boundary (literal) | 17280000 | 60 fantasy years | REALISM-TUNED | lifecycle.age_ticks | 60 fantasy years |
| src/engine/natural_healing.py:25 | HEALING.awake_ticks | 9600 | 4 days | REALISM-TUNED | state.tick (per-tick regen rate = max_hp / ticks) | 4 days to full health awake |
| src/engine/natural_healing.py:26 | HEALING.resting_ticks | 4800 | 2 days | REALISM-TUNED | state.tick | 2 days asleep or resting |
| src/engine/starvation.py:24 | STARVATION.death_ticks | 6000 | 2.5 days | REALISM-TUNED | state.tick | 2.5 days from the starving line to death at full health |
| src/engine/biological_needs.py:30 | BASE_HUNGER_RATE (per tick) | 0.1 | a rate per tick (see note) | REALISM-TUNED | state.tick | hunger +0.1 per tick at medium: line 95 in 950 ticks = 9.5 h from 0; NEED_LEVEL_RATE_SCALE multiplies it (0 to 1.5) |
| src/engine/biological_needs.py:31 | BASE_SLEEP_DEBT_RATE (per tick) | 0.05 | a rate per tick (see note) | REALISM-TUNED | state.tick | sleep debt +0.05 per tick: line 98 in 1,960 ticks = 19.6 h awake |
| src/engine/need_pull.py:37 | TICKS_PER_TILE | 1.0 | 36 s per tile | UNDETERMINED (designer) | state.tick | one tile per tick = 36 s per tile; the tile size in metres is not declared, so the walking speed has no stated meaning |
| src/engine/work_shift.py:27 | SHIFT_TICKS | 200 | 2 h | WINDOW-FITTED | consecutive-tick counter on the task (reset when the task changes) | a 2 h work shift; a real shift would be about 800 |
| src/core/strategic.py:336 | BLOCKER_BACKOFF_BASE_TICKS | 100 | 1 h | WINDOW-FITTED | state.tick | 1 h first backoff, doubling per failure up to the cap (divergence 2.213 tuning) |
| src/core/strategic.py:337 | BLOCKER_BACKOFF_CAP_TICKS | 800 | 8 h | WINDOW-FITTED | state.tick | 8 h cap |
| src/core/strategic.py:338 | BLOCKER_QUIET_SPELL_TICKS | 200 | 2 h | WINDOW-FITTED | state.tick | 2 h of observable quiet before a congestion blocker is removed (divergence 2.214) |
| src/core/strategic.py:541 | SUSPENSION_TTL_TICKS | 200 | 2 h | WINDOW-FITTED | state.tick | 2 h before a SUSPENDED project is ABANDONED (N10, divergence 2.212); window-fitted? confirmed: chosen for the N10 window, not from realism; rpg-designer reads it as a tuning value that goes to data |
| src/core/combat_constants.py:33 | CLEAR_TICKS | 200 | 2 h | WINDOW-FITTED | state.tick (project.cleared_since) | 2 h clear of a retreat before the project ends |
| src/core/state.py:515 | NavigationComponent.max_chase_ticks | 15 | 9 min | WINDOW-FITTED | per-body counter (nav.chase_ticks) | 9 min of chasing before giving up |
| src/core/state.py:1153 | respawn_cooldown (default; the compiler overrides it from bare_wait_ticks) | 100 | 1 h | WINDOW-FITTED | state.tick | 1 h |
| src/core/skills.py:34 | power_strike.cooldown (and :44 :55 cooldowns 4, 5) | 3 | 1.8 min | WINDOW-FITTED | state.tick | 1.8 min; the other skills 2.4 and 3 min |
| src/engine/tactical_threat.py:147 | ATTACKED_RECENTLY_WINDOW_TICKS | 10 | 6 min | WINDOW-FITTED | state.tick (combat.last_hit_tick) | 6 min |
| src/engine/perception_signals.py:22 | MOVING_WINDOW | 3 | 1.8 min | WINDOW-FITTED | tick (navigation.last_moved_tick) | 108 s a body still reads as moving |
| src/engine/scheduler.py:19 | ADJACENCY_WAKE_COOLDOWN | 2 | 1.2 min | NEITHER (engineering cadence) | state.tick plus entity id (staggered) | 72 s |
| src/engine/route_search.py:30 | ROUTE_PLAN_TICKS | 10 | 6 min | NEITHER (engineering cadence) | state.tick | 6 min a cached route stays valid |
| src/engine/scenario_runtime.py:34 | STALL_THRESHOLD | 50 | 30 min | NEITHER (engineering cadence) | scenario-local counter (no events) | 30 min watchdog |
| src/engine/candidate_selector.py:47 | EXACT_DIRTY_STARVED_CADENCE_MODULO | 20 | 12 min | NEITHER (engineering cadence) | state.tick plus entity id | 12 min |
| src/engine/lod.py:14 | LODService.CADENCE {0:1,1:2,2:5,3:10} | 1,2,5,10 | see note | NEITHER (engineering cadence) | state.tick | 36 s to 6 min between runs per level of detail |
| src/engine/cadence.py:21-43 | SystemCadence defaults | 1 (movement, combat, interaction, shop, lifecycle, biological, groups); 10 (strategic, concern, detour, social_memory, faction_decision); 50 (world_dynamics); 100 (ecology, building_sabotage, boss_spawn); 200 (reproduction_humanoid) | see note | NEITHER (engineering cadence) | state.tick | 36 s / 6 min / 30 min / 1 h / 2 h. Biological and lifecycle run every tick; reproduction every 2 h. No game-time claim: a performance dial |
| src/engine/cache_registry.py:53 | CachePolicy.sweep_interval_ticks | 10 | 6 min | NEITHER (engineering cadence) | state.tick | 6 min |
| src/engine/phase_graph.py:101 | phase skip modulo (literal) | 5 | 3 min | NEITHER (engineering cadence) | state.tick | 3 min, only under the CONSERVATIVE skip policy |
| src/systems/strategic_systems/intelligence.py:699 | periodic block modulo (literal) | 10 | 6 min | NEITHER (engineering cadence) | state.tick | 6 min |
| src/engine/access_audit/observe.py:94 | TIMELINE_SAMPLE_EVERY | 100 | 1 h | NEITHER (engineering cadence) | state.tick | an audit sampler, not a rule |
| src/domains/chronicle/grouper.py:101 | ChronicleGrouper.INCIDENT_TICK_WINDOW | 50 | 30 min | WINDOW-FITTED | event tick | 30 min: events closer than this share one incident |
| src/domains/demographics/cohort.py:346 | DemographicCycleService.COHORT_INTERVAL | 200 | 2 h | WINDOW-FITTED | state.tick | the cohort model advances every 2 h; ages in it are fantasy years |
| src/domains/faction/sentiment.py:38 | FactionSentimentService.DECAY_INTERVAL | 500 | 5 h | WINDOW-FITTED | state.tick | 5 h |
| src/domains/faction/sentiment.py:40 | FactionSentimentService.DECAY_STALENESS_THRESHOLD | 1000 | 10 h | WINDOW-FITTED | state.tick (fsent.last_interaction_tick) | 10 h |
| src/domains/world_emergence/services.py:214 | resource_crisis expiry_ticks (literal) | 200 | 2 h | WINDOW-FITTED | state.tick | an offered quest lapses after 2 h (compared as tick > expiry_ticks) |
| src/domains/world_emergence/services.py:247 | threat_response expiry_ticks (literal) | 100 | 1 h | WINDOW-FITTED | state.tick | 1 h |
| src/domains/cooperation/services.py:289 | recruitment duration_ticks (literal) | 100 | 1 h | WINDOW-FITTED | state.tick | a hired contract lasts 1 h while it pays a daily rate |
| src/systems/social_systems/contracts.py:12 | COOPERATION_OFFER_COOLDOWN_TICKS | 15 | 9 min | WINDOW-FITTED | state.tick (current_tick) | 9 min |
| src/systems/social_systems/party_lifecycle.py:50 | PartyLifecycleService.LEADERSHIP_CHECK_INTERVAL | 100 | 1 h | WINDOW-FITTED | state.tick (group.last_leadership_check_tick) | 1 h |
| src/world/reproduction_humanoid.py:28 | REPRODUCTION_COOLDOWN_TICKS | 400 | 4 h | WINDOW-FITTED | state.tick | 4 h between births for a parent; a birth cadence fitted to a short run |
| src/world/calamity.py:18 | CalamityService.MATURITY_INTERVAL | 1000 | 10 h | WINDOW-FITTED | state.tick | 10 h |
| src/world/calamity.py:19 | CalamityService.CALAMITY_MIN_INTERVAL | 2000 | 20 h | WINDOW-FITTED | state.tick | 20 h |
| src/world/calamity.py:21 | CalamityService.CALAMITY_FORCE_INTERVAL | 5000 | 2.08 days | WINDOW-FITTED | state.tick | about 2.1 days |
| src/world/calamity.py:120 | CalamityPressurePropagator.SEASONAL_PROPAGATION_INTERVAL | 500 | 5 h | WINDOW-FITTED | state.tick | named SEASONAL but 5 h; a season is 72,000 ticks, so the name and the value disagree |
| src/world/camp.py:20 | CampService.CAMP_SPAWN_INTERVAL | 30 | 18 min | WINDOW-FITTED | state.tick | 18 min |
| src/world/camp.py:18 | CampService.MATURITY_PER_TICK (rate) | 0.05 | a rate per tick (see note) | WINDOW-FITTED | state.tick | with RAID_MATURITY_THRESHOLD 80 a camp matures in 1,600 ticks = 16 h |
| src/world/creature_territory.py:22 | TERRITORY_MATURITY_RATES (rate) | 0.04 / 0.03 | a rate per tick (see note) | WINDOW-FITTED | state.tick | with threshold 100: 2,500 to 3,333 ticks = 25 to 33 h |
| src/world/ecology.py:17 | ResourceEcologyService.ECOLOGY_INTERVAL | 200 | 2 h | WINDOW-FITTED | state.tick | regrowth step every 2 h |
| src/world/regional_sovereignty.py:16 | RegionalSovereigntyService.TAX_INTERVAL | 100 | 1 h | WINDOW-FITTED | state.tick | tax every 1 h |
| src/world/raid.py:9 | RaidService.RAID_INTERVAL_DAYS | 5 | 5 days | UNDETERMINED (designer) | none: no reader in src | 5 days = 12,000 ticks; the constant has no reader in src (the global raid cadence it described was removed; the test note says it was a tick % 500 cadence at 100 ticks/day) |
| src/world/threat.py:17 | ThreatService.THREAT_DECAY_RATE (per tick) | 0.01 | a rate per tick (see note) | WINDOW-FITTED | state.tick | trauma decays 1 per 100 ticks |
| src/world/threat.py:18 | ThreatService.PRESSURE_COOLING_RATE (per tick) | 0.1 | a rate per tick (see note) | WINDOW-FITTED | state.tick | retaliation pressure cools 1 per 10 ticks |
| src/economy/health_monitor.py:21 | EconomyHealthMonitor.WINDOW_SIZE | 100 | 1 h | NEITHER (engineering cadence) | state.tick | an observation window (1 h) |
| src/simulation_quality/persistence.py:17 | QualityPersistence._FLUSH_INTERVAL | 50 | 30 min | NEITHER (engineering cadence) | state.tick | a write batching interval |
| src/domains/campaigns/runner.py:115 | runner progress modulo (literal) | 50 | 30 min | NEITHER (engineering cadence) | runner tick | 30 min; a reporting cadence |

## Table B: tick-valued numbers in data/content

| file:line | key | value | real time | class | clock | note |
|---|---|---|---|---|---|---|
| data/content/world/resources.yaml | required_ticks (16 resources: 8, 10, 12, 15, 16, 18, 20, 24, 25) | 8 to 25 | 5 to 15 min | WINDOW-FITTED | state.tick (ticks of work to harvest) | a harvest of a few minutes; chosen so a harvest finishes inside a short run |
| data/content/defaults.yaml:11 | default_resource_required_ticks | 10 | 6 min | WINDOW-FITTED | state.tick |  |
| data/content/world/resources.yaml:152 | bare_wait_ticks (tree-like node) | 4800 | 2 days | REALISM-TUNED | state.tick | wait after a node is emptied before regrowth resumes |
| data/content/world/resources.yaml:165 | bare_wait_ticks | 2400 | 1 day | REALISM-TUNED | state.tick |  |
| data/content/world/resources.yaml:178 | bare_wait_ticks | 1200 | 12 h | REALISM-TUNED | state.tick |  |

On main, no `data/content` file declares a species lifespan, a gestation, a maturity age or a life-stage length; those live only in code (Table A). The births branch adds some (next section). The camp pilot module sets `maturity: 79.9`, a starting level, not a duration.

## Pending on the births branch (not on main)

Pending, not on main; values as of `3d1a14a00` (`origin/rpg-ubuntu-wild-births-impl`, TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND), read with `git show 3d1a14a00:<path>` and not run. It adds `data/content/living/reproduction_profiles.yaml` (new) and `src/world/births.py`. All are read on `state.tick` (a check is dated by `state.tick`; a pregnancy ends at `due_tick = conceived tick + gestation_ticks`; a birth interval ends at `tick + min_birth_interval_ticks`). Real time is at 36 s per tick. The file's own comments say the values were fixed by rulings v2.2 D1 and the owner (2026-11-18) before any data, and that gestation is COMPRESSED with the order kept; they are not tuned on measurement data.

| file:line | key | value | real time | class | clock | note |
|---|---|---|---|---|---|---|
| src/engine/cadence.py:36 (births branch) | SystemCadence.births | 30 | 18 min | NEITHER (engineering cadence) | state.tick | a births check runs every 30 ticks = 80 a day; the file calls it a check, not a rule |
| reproduction_profiles.yaml (humanoid_births) | gestation_ticks | 2400 | 24 h | WINDOW-FITTED | state.tick (pregnancy due_tick) | compressed; the file says the real length for a person is about 672,000 ticks (280 days at 2,400 a day) and waits on the calendar decision |
| reproduction_profiles.yaml (carnivore_births) | gestation_ticks | 1200 | 12 h | WINDOW-FITTED | state.tick | compressed, order kept |
| reproduction_profiles.yaml (goblin_births) | gestation_ticks | 900 | 9 h | WINDOW-FITTED | state.tick | compressed, order kept |
| reproduction_profiles.yaml (plant_eater_births) | gestation_ticks | 600 | 6 h | WINDOW-FITTED | state.tick | compressed, order kept |
| reproduction_profiles.yaml (humanoid_births, carnivore_births) | min_birth_interval_ticks | 12000 | 5 days | WINDOW-FITTED | state.tick (per partner entry in lifecycle.reproduction_cooldowns) | the file says it is chosen so a pair breeds at most once inside a 5,000-tick run |
| reproduction_profiles.yaml (goblin_births, plant_eater_births) | min_birth_interval_ticks | 7200 | 3 days | WINDOW-FITTED | state.tick | same reason |
| reproduction_profiles.yaml (all four) | birth_chance_per_check | 0.005 (humanoid), 0.004 (carnivore), 0.008 (goblin, plant eater) | per check; mean wait 200 checks = 6,000 ticks = 2.5 days at 0.005 | WINDOW-FITTED | state.tick (a seeded draw per check) | a probability, not a duration; its mean wait is set against run length |
| reproduction_profiles.yaml (all four) | fed_line | 30 | hunger 30 of 100; about 6 h after a full meal for a person (per the file) | REALISM-TUNED | state.tick (hunger rises per tick, Table A) | a hunger level, not a tick count |
| reproduction_profiles.yaml (all four) | birth_hunger_cost | 25 | one birth costs 25 hunger, a little under one inn meal (INN_MEAL_HUNGER 20 on main; the file says 40) | UNDETERMINED (designer) | state.tick | the comment's "40" does not match INN_MEAL_HUNGER = 20 on main; flagged, not decided |
| reproduction_profiles.yaml (all four) | mate_radius_tiles | 10 | n/a (a distance) | setting | n/a | in data already |
| reproduction_profiles.yaml | litter_weights | per kind | n/a | setting (report-only, provisional per the file) | n/a | a distribution, not a duration |

`src/world/births.py` on that branch declares only two named numbers, `BIRTH_DRAW_SUB_ID = 7` and `LITTER_DRAW_SUB_ID = 11`, which are RNG stream ids (code invariants, not tuning); every duration it uses comes from the profile file.

## Table C: other numeric tuning values in src (named constants)

Classified by the constant's name and use, one reason each. A **setting** is a value the owner or a designer would tune and which should move to `data/` (in stages, under TCK-20261119-THE-CALENDAR-IS-DECLARED-IN-CONFIGURATION-NOT-IN-CODE's conditions). A **code invariant** is a value that is part of the code's own correctness or limits. The classification is mine, by rule on the name; entries marked UNDETERMINED need a designer. Tick-valued constants already in Table A are not repeated.

| file:line | constant | value | kind | reason |
|---|---|---|---|---|
| src/ai/coming_of_age.py:38 | BASE_WEIGHT | 1.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/ai/coming_of_age.py:39 | PERSONALITY_COEFF | 1.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/ai/coming_of_age.py:40 | PARENTAL_COEFF | 1.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/ai/coming_of_age.py:41 | DEFAULT_REGIONAL_COEFF | 1.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/ai/coming_of_age.py:44 | WEIGHT_FLOOR | 0.05 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/ai/goals/adventure_scorer.py:34 | _ADVENTURE_ROUTE_TIER5_COMPETITION_MAX | 2.4 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/ai/goals/opening_steps.py:84 | SCAVENGE_RADIUS | 20.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/ai/goals/opening_steps.py:85 | HUNT_RADIUS | 10.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/api/admission_control.py:29 | _BUCKET_CAPACITY | 30.0 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/api/admission_control.py:30 | _BUCKET_REFILL_PER_SECOND | 3.0 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/api/admission_control.py:31 | _IDLE_TTL_SECONDS | 1800.0 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/api/admission_control.py:32 | _MAX_CLIENT_ENTRIES | 1000 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/api/admission_control.py:33 | _RETRY_AFTER_SECONDS | 5 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/api/admission_control.py:34 | _WS_THROTTLE_CLOSE_CODE | 1013 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/api/agent_ops_dashboard/ingest.py:91 | ACTIVE_WINDOW_MINUTES | 10 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/api/agent_ops_dashboard/ingest.py:98 | _LIFECYCLE_PRIORITY | {'inprogress': 0, 'done': 1, 'todos': 2} | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/api/agent_ops_dashboard/serve.py:25 | DEFAULT_PORT | 8420 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/api/http_metrics.py:21 | _BUCKETS | (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.3, 0.5, 1.0, 2.5, 5. | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/api/metrics_port.py:21 | DEFAULT_METRICS_PORT | 9109 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/api/presenters/state_presenter.py:14 | DETAIL_TERMINAL_QUESTS | 10 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/api/presenters/state_presenter.py:15 | DETAIL_CLOSED_CONTRACTS | 5 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/api/presenters/state_presenter.py:16 | MAX_ENTITY_PAGE | 500 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/api/tracing.py:30 | DEFAULT_SAMPLE_RATIO | 0.1 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/cognition/capability_estimate.py:70 | COMMON_KNOWLEDGE_DANGER | {'low': 0.2, 'medium': 0.5, 'high': 0.75, 'extreme': 0.95} | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/cognition/capability_estimate.py:71 | NEUTRAL_DANGER | 0.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/cognition/capability_estimate.py:72 | UNINFORMED_CONFIDENCE | 0.1 | setting (move to data/) | a need or knowledge level that changes who eats, rests or trusts; a balance number |
| src/cognition/capability_estimate.py:81 | _REGION_DANGER | {'hometown': 0.0, 'near_forest': 0.3, 'old_mine': 0.35, 'nor | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/cognition/need_interpretation.py:31 | _URGENCY_CRITICAL | 0.95 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/cognition/need_interpretation.py:32 | _URGENCY_HIGH | 0.75 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/cognition/need_interpretation.py:33 | _URGENCY_MEDIUM | 0.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/cognition/need_interpretation.py:34 | _URGENCY_LOW | 0.25 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/cognition/need_interpretation.py:37 | _GOLD_LOW | 30 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/cognition/need_interpretation.py:38 | _GOLD_VERY_LOW | 10 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/cognition/self_assessment.py:27 | _HP_LOW | 0.35 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/cognition/self_assessment.py:28 | _HP_CRITICAL | 0.2 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/cognition/self_assessment.py:29 | _STAMINA_LOW | 0.3 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/cognition/self_assessment.py:30 | _HUNGER_HIGH | 60.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/cognition/self_assessment.py:31 | _SLEEP_DEBT_HIGH | 50.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/cognition/self_assessment.py:32 | _INVENTORY_HIGH | 0.85 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/cognition/self_assessment.py:33 | _GEAR_DAMAGE_LOW | 0.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/cognition/self_assessment.py:34 | _LEVEL_WEAPON_GAP | 5 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/content/common_knowledge_seed.py:29 | COMMON_KNOWLEDGE_CERTAINTY | 0.3 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/core/calendar.py:11 | DAYS_PER_SEASON | 30 | setting (move to data/) | a calendar definition; the calendar is the approved baseline (2,400 ticks/day, 120-day year) and moves to configuration under TCK-20261119-THE-CALENDAR-IS-DECLARED-IN-CONFIGURATION-NOT-IN-CODE |
| src/core/calendar.py:12 | SEASONS_PER_YEAR | 4 | setting (move to data/) | a calendar definition; the calendar is the approved baseline (2,400 ticks/day, 120-day year) and moves to configuration under TCK-20261119-THE-CALENDAR-IS-DECLARED-IN-CONFIGURATION-NOT-IN-CODE |
| src/core/combat_constants.py:18 | NEAR_DEATH_HP_RATIO | 0.2 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/core/combat_constants.py:28 | ENTITY_TARGET_PERCEPTION_RADIUS | 10.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/core/combat_constants.py:34 | RETREAT_ARRIVAL_RADIUS | 1.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/core/enums.py:7 | EntityRole.HERO | 0 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:8 | EntityRole.SHOPKEEPER | 1 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:9 | EntityRole.MONSTER | 2 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:10 | EntityRole.CITIZEN | 3 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:11 | EntityRole.WORKER | 4 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:12 | EntityRole.GUARD | 5 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:48 | Faction.HERO_GUILD | 0 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:49 | Faction.MONSTER_HORDE | 1 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:50 | Faction.TOWN_COUNCIL | 2 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:51 | Faction.NEUTRAL | 3 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:56 | Direction.NORTH | 0 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:57 | Direction.EAST | 1 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:58 | Direction.SOUTH | 2 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:59 | Direction.WEST | 3 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:64 | MovementIntention.NONE | 0 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:65 | MovementIntention.PURSUE | 1 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:66 | MovementIntention.RETREAT | 2 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:67 | MovementIntention.HOLD | 3 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:68 | MovementIntention.REPOSITION | 4 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:69 | MovementIntention.INTERCEPT | 5 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:70 | MovementIntention.GUARD | 6 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:71 | MovementIntention.WANDER | 7 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:72 | MovementIntention.REGROUP | 8 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:76 | ActionType.REST | 0 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:77 | ActionType.MOVE | 1 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:78 | ActionType.INTERACT | 2 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:79 | ActionType.ATTACK | 3 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:80 | ActionType.SKILL | 4 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:85 | ActionStyle.BALANCED | 0 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:86 | ActionStyle.AGGRESSIVE | 1 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:87 | ActionStyle.EVASIVE | 2 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:213 | Domain.DEFAULT | 0 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:214 | Domain.SPAWN | 1 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:215 | Domain.WORLD | 2 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:216 | Domain.CALAMITY | 3 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:217 | Domain.SOCIAL | 4 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:218 | Domain.STRATEGIC | 5 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:219 | Domain.TACTICAL | 6 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:220 | Domain.ECONOMY | 7 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:221 | Domain.QUEST | 8 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:222 | Domain.COMBAT | 9 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:223 | Domain.LOOT | 10 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/enums.py:224 | Domain.INIT | 11 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/governance.py:13 | RuntimeMode.NORMAL | 0 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/governance.py:14 | RuntimeMode.CONSTRAINED | 1 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/governance.py:15 | RuntimeMode.DEGRADED | 2 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/governance.py:16 | RuntimeMode.SURVIVAL | 3 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/models/quests.py:16 | QuestStatus.ACTIVE | 1 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/models/quests.py:17 | QuestStatus.COMPLETED | 2 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/models/quests.py:18 | QuestStatus.REWARDED | 3 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/models/quests.py:19 | QuestStatus.REWARD_PENDING | 4 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/replay_modes.py:11 | ReplayMode.OFF | 0 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/replay_modes.py:12 | ReplayMode.MINIMAL | 1 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/replay_modes.py:13 | ReplayMode.DEBUG_WINDOWED | 2 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/replay_modes.py:14 | ReplayMode.FORENSIC_SHORT_RUN | 3 | code invariant | an enum member: an identifier, not a value anyone tunes |
| src/core/social_constants.py:17 | ALLY_TRUST_THRESHOLD | 0.3 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/core/stable_hash.py:16 | _INT31_MODULUS | 2147483648 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/core/state.py:91 | StaminaComponent.ATTACK_COST | 8.0 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/core/state.py:92 | StaminaComponent.MOVE_COST | 3.0 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/core/state.py:93 | StaminaComponent.HARVEST_COST | 5.0 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/core/state.py:94 | StaminaComponent.SKILL_COST_MULT | 1.0 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/core/state.py:1292 | GROUP_ID_BASE | 10000 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/core/state.py:1317 | AuthoritativeState.MAX_PROCESSED_IDS | 1000 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/core/state.py:1318 | AuthoritativeState.MAX_TRACE_SIZE | 100 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/core/update_models/world.py:95 | NO_OWNER_SENTINEL | -1 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/domains/belief_institution/deriver.py:49 | OUT_GROUP_DAMPENING | 0.4 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/campaigns/grief_urgency.py:28 | NEMESIS_EPISODE_COUNT | 2 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/campaigns/plan_revision.py:39 | _MILESTONE_THRESHOLDS | {'craft_upgrade': 5, 'quest_opportunity': 10, 'gather_resour | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/campaigns/social_memory.py:374 | SocialMemoryDecay.FRIENDSHIP_DECAY | 0.4 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/campaigns/social_memory.py:375 | SocialMemoryDecay.GRUDGE_DECAY | 0.1 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/chronicle/grouper.py:102 | ChronicleGrouper.ERA_EPISODE_MIN | 3 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/chronicle/significance.py:22 | BASE_SIGNIFICANCE | {'entity_death': 0.5, 'faction_destroyed': 0.9, 'quest_compl | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/chronicle/significance.py:41 | CHRONICLE_THRESHOLD | 0.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/learning_outcome.py:38 | _SEVERITY_NEAR_DEATH | 1.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/learning_outcome.py:39 | _SEVERITY_LOST | 0.8 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/learning_outcome.py:40 | _SEVERITY_WON_EASY | 0.3 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/memory_store.py:27 | MAX_OPPONENT_MODELS_PER_ENTITY | 8 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/domains/combat_engagement/phase.py:54 | COMBAT_RISK_LOW_MAX | 0.2 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/phase.py:55 | COMBAT_RISK_NORMAL_MAX | 0.4 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/phase.py:56 | COMBAT_RISK_HIGH_MAX | 0.8 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/phase.py:101 | WITNESSED_COMBAT_RADIUS | 10.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/domains/combat_engagement/power.py:24 | TRUE_POWER_DEF_WEIGHT | 0.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/power.py:25 | TRUE_POWER_MAX_HP_WEIGHT | 0.1 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/power.py:29 | _APPARENT_POWER_CRITICAL_HP_RATIO | 0.3 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/power.py:30 | _APPARENT_POWER_CRITICAL_MULTIPLIER | 0.6 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/power.py:31 | _APPARENT_POWER_WOUNDED_HP_RATIO | 0.7 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/power.py:32 | _APPARENT_POWER_WOUNDED_MULTIPLIER | 0.85 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/power.py:36 | UNCERTAINTY_FLOOR | 0.05 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/power.py:37 | UNCERTAINTY_CEILING | 0.6 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/power.py:38 | _GAP_SHARPNESS_BASE | 0.05 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/power.py:39 | _PERCEPTION_SCALE_MAX | 99.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/combat_engagement/power.py:43 | NOISE_MAGNITUDE_AT_MAX_UNCERTAINTY | 0.3 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/culture/applicator.py:32 | CULTURE_ACTIVATION_THRESHOLD | 0.3 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/culture/deriver.py:35 | NORMALISE_DENOMINATOR | 3.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/faction/sentiment.py:33 | FactionSentimentService.FACTION_SCALE_FACTOR | 0.1 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/faction/sentiment.py:44 | FactionSentimentService.DECAY_FACTOR | 0.9 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/fame/deriver.py:42 | NORMALISE_DENOMINATOR | 3.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/fame/legend.py:38 | FAME_THRESHOLD | 0.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/fidelity/deriver.py:32 | FIDELITY_DECAY_PER_ERA | 0.2 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/progression/ledger.py:19 | RewardLedgerService.MAX_ENTRIES | 20 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/domains/world_emergence/models.py:149 | RegionalPressureModel.ADJACENCY_GAP | 50.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/domains/world_emergence/models.py:150 | RegionalPressureModel.PROPAGATION_FACTOR | 0.3 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/world_emergence/services.py:176 | QuestOpportunityGenerator._THREAT_SEVERITY_THRESHOLD | 0.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/world_emergence/services.py:392 | TraumaRegionConcernBridge.TRAUMA_CONCERN_THRESHOLD | 0.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/domains/world_emergence/services.py:393 | TraumaRegionConcernBridge.URGENCY_SCALE | 50.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/economy/health_monitor.py:22 | EconomyHealthMonitor.INFLATION_SPIRAL_GINI_THRESHOLD | 0.7 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/economy/health_monitor.py:23 | EconomyHealthMonitor.GOLD_HOARDING_GINI_THRESHOLD | 0.8 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/access_audit/observe.py:32 | _MAX_DEPTH | 3 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/engine/access_audit/observe.py:33 | _NODE_BUDGET | 400 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/engine/access_audit/observe.py:97 | FIELD_REPR_CHARS | 80 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/engine/appraisal.py:30 | THREAT_RANGE | 4 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/engine/appraisal.py:31 | WARY_DISTANCE | 5 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/engine/appraisal.py:34 | HUNT_HUNGER | 40.0 | setting (move to data/) | a need or knowledge level that changes who eats, rests or trusts; a balance number |
| src/engine/biological_needs.py:34 | NEED_LEVEL_RATE_SCALE | {'none': 0.0, 'very_low': 0.3, 'low': 0.5, 'medium': 1.0, 'h | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/building_arrival.py:35 | HUNGER_NEED_FLOOR | 20.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/cognition.py:72 | FLEE_PANIC_THRESHOLD | 0.4 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/cognition.py:77 | REGIONAL_DREAD_MAX | 0.3 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/combat.py:49 | CombatResolutionSystem.HIGH_GROUND_BONUS | 0.2 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/combat.py:50 | CombatResolutionSystem.FLANKING_BONUS | 0.15 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/combat.py:51 | CombatResolutionSystem.COVER_REDUCTION | 0.3 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/combat.py:52 | CombatResolutionSystem.BOND_SYNERGY_BONUS | 0.1 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/domain/cognition_extras.py:44 | InformationNeedDetector.SEEKING_THRESHOLD | 0.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/domain/core_actions.py:72 | EAT_AT_CORPSE_REACH | 2.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/engine/faction_decision.py:251 | _CRITICAL_SEVERITY_THRESHOLD | 0.8 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/interaction.py:28 | InteractionSystem.ITEM_WEIGHTS | {'WOOD': 2.0, 'ORE': 5.0, 'FISH': 1.0, 'GOLD': 0.01, '__DEFA | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/lodging.py:36 | LEAVE_RING_RADIUS | 3 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/engine/military_conflict.py:27 | _SIEGE_SVC_DELTA | -0.05 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/engine/military_conflict.py:28 | _SIEGE_PROGRESS_DELTA | 0.05 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/engine/military_conflict.py:30 | _DEF_SVC_DELTA | 0.02 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/engine/military_conflict.py:31 | _DEF_PROGRESS_DELTA | -0.02 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/engine/military_conflict.py:32 | _DEF_ENTITY_THRESHOLD | 3 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/military_conflict.py:34 | _MAX_SQUAD_SIZE | 5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/military_conflict.py:36 | _EXHAUSTION_DRAIN | 0.001 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/military_conflict.py:38 | _PEACE_THRESHOLD | 0.3 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/need_pull.py:26 | ESCALATION_ONSET | 0.6 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/need_pull.py:27 | ESCALATION_FULL | 0.85 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/need_pull.py:28 | ESCALATION_AMPLITUDE | 60.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/need_pull.py:33 | HUNGER_LINE | 95.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/need_pull.py:34 | SLEEP_LINE | 98.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/pipeline_phases/lead_contradiction.py:38 | _RELIABILITY_PENALTY | 0.1 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/pipeline_phases/lead_contradiction.py:39 | _RELIABILITY_FLOOR | 0.1 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/pipeline_phases/lead_contradiction.py:40 | _REPLANNING_PRIORITY | 0.7 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/pipeline_phases/paid_information.py:44 | _INFO_BASE_COST | 10 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/engine/pipeline_phases/paid_information.py:45 | _MIN_RELIABILITY | 0.1 | setting (move to data/) | a need or knowledge level that changes who eats, rests or trusts; a balance number |
| src/engine/route_search.py:28 | ROUTE_NODE_CAP | 3000 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/engine/route_search.py:32 | ROUTE_PLAN_LIMIT | 5000 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/engine/rpg_depth.py:26 | ATTRIBUTE_CAP | 99 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/engine/rpg_depth.py:178 | LEASH_CHASE_MULTIPLIER | 1.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/rpg_depth.py:292 | TARGET_SWITCH_MARGIN | 0.3 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/semantic_entity_index.py:13 | HUNGER_NEED_THRESHOLD | 95.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/semantic_entity_index.py:15 | SLEEP_DEBT_NEED_THRESHOLD | 98.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/semantic_entity_index.py:19 | REST_PRESSURE_NEED_THRESHOLD | 70.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/service_prices.py:7 | EAT_PRICE_GOLD | 5 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/engine/service_prices.py:8 | REST_PRICE_GOLD | 10 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/engine/service_prices.py:9 | INN_MEAL_HUNGER | 20.0 | setting (move to data/) | a need or knowledge level that changes who eats, rests or trusts; a balance number |
| src/engine/shop_sale.py:25 | FOOD_KEPT_HUNGER_RECOVERY | 60.0 | setting (move to data/) | a need or knowledge level that changes who eats, rests or trusts; a balance number |
| src/engine/tactical.py:42 | WOUND_DISTRESS_COVER_THRESHOLD | 9.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/engine/tactical.py:47 | PROTECTOR_GUARD_DISTRESS_THRESHOLD | 5.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/engine/tactical.py:51 | SCAR_DISTRESS_HP_THRESHOLD_BUMP_PER_POINT | 0.01 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/engine/tactical.py:52 | SCAR_DISTRESS_HP_THRESHOLD_BUMP_CAP | 0.1 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/engine/tactical_destinations.py:28 | RETREAT_STEP | 10.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/engine/tactical_destinations.py:30 | WANDER_RADIUS | 5.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/engine/tactical_destinations.py:31 | _EPSILON | 1e-09 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/engine/tactical_rest.py:35 | REST_MIN_SLEEP_DEBT | 20.0 | setting (move to data/) | a need or knowledge level that changes who eats, rests or trusts; a balance number |
| src/engine/tactical_rest.py:91 | EAT_CARRIED_MIN_HUNGER | 40.0 | setting (move to data/) | a need or knowledge level that changes who eats, rests or trusts; a balance number |
| src/engine/tactical_threat.py:30 | CAUTIOUS_SAFETY_PRESSURE | 0.75 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/tactical_threat.py:35 | WOUNDED_HP_RATIO | 0.7 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/tactical_threat.py:37 | ADJACENT_DISTANCE | 1.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/engine/tactical_threat.py:39 | THREAT_RANGE | 4.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/engine/tactical_threat.py:41 | OUTMATCH_RATIO | 1.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/work_shift.py:28 | WAGE_GOLD | 6 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/engine/work_units.py:22 | ENTITY_MS | 0.68 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/engine/work_units.py:23 | LEAD_MS | 7.42 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/engine/work_units.py:24 | THREAD_CHUNK_CAP | 50 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/engine/world_dynamics.py:23 | HAZARD_GROWTH_TRAUMA_THRESHOLD | 50.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/engine/world_dynamics.py:25 | HAZARD_GROWTH_STEP | 0.01 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/observability/alerts/router.py:11 | SEVERITY_LEVELS | {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'CRITI | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/alerts/sinks.py:47 | WebhookAlertSink.BACKOFF_BASE_SECONDS | 0.5 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/alerts/sinks.py:48 | WebhookAlertSink.BACKOFF_CAP_SECONDS | 10.0 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/alerts/sinks.py:49 | WebhookAlertSink.BACKOFF_JITTER_RATIO | 0.2 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/alerts/sinks.py:51 | WebhookAlertSink.CIRCUIT_BREAKER_FAILURE_THRESHOLD | 5 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/alerts/sinks.py:52 | WebhookAlertSink.CIRCUIT_BREAKER_COOLDOWN_SECONDS | 60.0 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/cognition/pattern_miner.py:20 | CognitionPatternMiner.DEFAULT_THRESHOLDS | {'project_churn': 3, 'detour_loop': 2, 'stale_blocker_age':  | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/death_ledger.py:29 | MAX_RECORDS | 5000 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/event_extractor.py:304 | EventExtractor._SOCIAL_MEMORY_THRESHOLD | 0.3 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/event_recorder.py:19 | SEVERITY_ORDER | {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL' | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/event_recorder.py:46 | ObservabilityController.PRESSURE_THRESHOLD | 0.7 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/event_recorder.py:47 | ObservabilityController.DEGRADED_THRESHOLD | 0.9 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/event_recorder.py:48 | ObservabilityController.SURVIVAL_THRESHOLD | 1.0 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/event_shapers.py:507 | FactionShaper._FACTION_STAGNANT_TICKS | 300 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/event_shapers.py:1471 | SocialShaper._SOCIAL_MEMORY_THRESHOLD | 0.3 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/extraction/capability.py:12 | CAPABILITY_STALL_TICKS | 300 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/extraction/leads.py:13 | CERTAINTY_FLOAT | {'PRECISE': 1.0, 'APPROXIMATE': 0.5, 'VAGUE': 0.25, 'EXHAUST | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/extraction/leads.py:18 | BELIEF_STALE_TICKS | 50 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/extraction/progression.py:11 | XP_PLATEAU_TICKS | 50 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/extraction/resources.py:11 | _SPAWN_INTERVAL | 50 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/readiness/harness.py:28 | PRODUCTION_READINESS_CRITERIA | {'max_tick_p95_overhead_percent': 5.0, 'max_memory_overhead_ | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/rpg_gate_metrics.py:63 | MAX_EXAMPLES | 5 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/rpg_gate_metrics.py:64 | COIN_EPSILON | 1e-06 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/rpg_gate_metrics.py:68 | COUNT_FLOOR_REL | 0.1 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/rpg_gate_metrics.py:100 | POOLED_THRESHOLDS | {'O2.seeds_with_survivors': 1.0} | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/run_ledger.py:33 | POPULATION_SAMPLE_EVERY | 500 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/run_ledger.py:37 | PERCEPTION_SAMPLE_EVERY | 10 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/run_ledger.py:40 | MAX_EXAMPLES | 5 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/stream/consumer.py:19 | RedisStreamConsumer.BACKOFF_BASE_SECONDS | 0.2 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/stream/consumer.py:20 | RedisStreamConsumer.BACKOFF_CAP_SECONDS | 30.0 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/stream/consumer.py:21 | RedisStreamConsumer.BACKOFF_JITTER_RATIO | 0.2 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/stream/consumer.py:22 | RedisStreamConsumer.RECLAIM_IDLE_MS | 30000 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/stream/consumer.py:23 | RedisStreamConsumer.MAX_DELIVERY_ATTEMPTS | 3 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/stream/lag_metrics.py:17 | DEFAULT_METRICS_PORT | 9108 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/understanding/domain/economy.py:36 | EconomyDomainAnalyzer.ZERO_PRODUCTION_WINDOW_TICKS | 50 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/understanding/domain/movement.py:36 | MovementDomainAnalyzer.STUCK_CLUSTER_THRESHOLD | 3 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/understanding/domain/movement.py:37 | MovementDomainAnalyzer.HIGH_STUCK_RATIO_THRESHOLD | 0.3 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/understanding/domain/quest.py:34 | QuestDomainAnalyzer.LOW_COMPLETION_RATE_THRESHOLD | 0.2 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/understanding/domain/runtime.py:38 | RuntimeDomainAnalyzer.GOVERNOR_DEGRADED_THRESHOLD | 3 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/understanding/domain/runtime.py:39 | RuntimeDomainAnalyzer.DROP_RATE_THRESHOLD | 2 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/understanding/rootcause/rules.py:153 | InventoryFullReturnLoopBroken.STAGNATION_TICK_THRESHOLD | 50 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/understanding/stories/patterns.py:76 | ResourceCrisis.CRISIS_TICK_THRESHOLD | 80 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/observability/understanding/stories/patterns.py:123 | QuestHero.HERO_QUEST_MINIMUM | 3 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/perf/benchmark_record.py:71 | MAX_EMBEDDED_SAMPLES | 500 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/perf/scenarios.py:19 | _REGION_GRID_SIDE | 19 | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/quests/generator.py:60 | PRESSURE_WEIGHT_SCALE | 2.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/quests/generator.py:103 | QuestGenerator._EXPLORE_TARGET_MIN_DIST | 15.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/quests/generator.py:104 | QuestGenerator._EXPLORE_TARGET_MAX_DIST | 40.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/rendering/incremental.py:22 | ENTITY_COLOR_ALIVE | (74, 158, 255) | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/rendering/render.py:44 | DEFAULT_TERRAIN_COLOR | (255, 0, 255) | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/rendering/render.py:54 | BUILDING_COLOR | (192, 128, 64) | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/rendering/render.py:55 | ENTITY_COLOR_ALIVE | (74, 158, 255) | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/rendering/render.py:56 | ENTITY_COLOR_DEAD | (96, 48, 48) | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/rendering/render.py:57 | BLOCKED_OUTLINE | (255, 80, 80) | code invariant | engineering limit of an output, a budget or a sampler; no game-time meaning |
| src/simulation_quality/api/routes.py:24 | _DISABLED_RESPONSE | {'enabled': False} | code invariant | a minimum sample, a fixed response or a loop guard of the code itself; no game rule |
| src/simulation_quality/pillars.py:22 | DEFAULT_MIN_EVENTS | 3 | code invariant | a minimum sample, a fixed response or a loop guard of the code itself; no game rule |
| src/simulation_quality/pillars.py:92 | GRADE_THRESHOLDS | {'S': 2.0, 'A': 0.5, 'B': 0.0, 'C': -0.5, 'D': -1.0} | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/strategy/role_model_imitation.py:28 | RoleModelImitationService.HIGH_TIER_FIDELITY | 1.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/strategy/role_model_imitation.py:29 | RoleModelImitationService.LOW_TIER_FIDELITY | 0.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/strategy/role_model_imitation.py:30 | RoleModelImitationService.DEFAULT_FIDELITY | 0.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/strategy/role_model_phase.py:28 | RoleModelSelectionPhase.RADIUS | 10.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/systems/economy_systems/market.py:11 | UNKNOWN_ITEM_BASE_VALUE | 10.0 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/systems/lifecycle_systems/lifecycle.py:27 | LifecycleSystem.INHERITED_NEMESIS_SEVERITY_MULTIPLIER | 0.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/social_systems/appraisal.py:19 | CLAN_INFLUENCE_WEIGHT | 0.2 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/social_systems/clan_lifecycle.py:32 | CLAN_REPUTATION_MISCONDUCT_DELTA | -0.25 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/systems/social_systems/consequence_events.py:47 | LEGENDARY_REP_THRESHOLD | 0.9 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/social_systems/consequence_events.py:50 | TRAITOR_HOSTILITY_THRESHOLD | 0.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/social_systems/consequence_events.py:53 | OLD_DEBT_SCORE_THRESHOLD | 0.5 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/social_systems/party_composition.py:45 | PartyCompositionScorer.ROLE_DIVERSITY_WEIGHT | 0.6 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/social_systems/party_composition.py:46 | PartyCompositionScorer.OCEAN_COMPAT_WEIGHT | 0.4 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/social_systems/party_composition.py:47 | PartyCompositionScorer.TRUST_BONUS_WEIGHT | 0.15 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/social_systems/party_composition.py:48 | PartyCompositionScorer.ROLE_AFFINITY_WEIGHT | 0.1 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/social_systems/party_lifecycle.py:134 | PartyLifecycleService.DEFECTION_GRIEVANCE_THRESHOLD | 3 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/social_systems/relationships.py:21 | RelationshipService.FRIEND_SENTIMENT_THRESHOLD | 0.8 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/social_systems/relationships.py:22 | RelationshipService.RIVAL_SENTIMENT_THRESHOLD | -0.8 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/social_systems/reputation.py:9 | ReputationService.IMPACTS | {'THEFT': -0.2, 'MURDER': -1.0, 'BETRAYAL': -0.5, 'HEROISM': | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/systems/strategic_systems/intelligence.py:27 | _MAX_CONSECUTIVE_REJECTIONS | 20 | code invariant | a minimum sample, a fixed response or a loop guard of the code itself; no game rule |
| src/systems/strategic_systems/intelligence.py:32 | _ADVENTURE_ROUTE_SCORE_MAX | 2.9 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/strategic_systems/intelligence.py:47 | _GOAL_UTILITY_SCORE_MAX | 100.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/strategic_systems/intelligence.py:53 | _INTERRUPTION_URGENCY_FLOOR_PCT | 0.8 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/strategic_systems/intelligence.py:59 | _COMMITTED_INTENTION_BASE_UTILITY | 50.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/systems/world_systems/generator.py:43 | _SPAWN_FREE_TILE_RADIUS | 5 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/systems/world_systems/generator.py:44 | _SPAWN_REACH | 1 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/world/boss.py:54 | BossService.BOSS_SPAWN_THRESHOLD | 2.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/boss.py:55 | BossService.BOSS_SPAWN_TRAUMA_THRESHOLD | 8.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/calamity.py:20 | CalamityService.CALAMITY_RANDOM_CHANCE | 0.005 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/calamity.py:121 | CalamityPressurePropagator.PROPAGATION_FACTOR | 0.15 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/calamity.py:122 | CalamityPressurePropagator.PROPAGATION_THRESHOLD | 0.1 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/camp.py:19 | CampService.RAID_MATURITY_THRESHOLD | 80.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/camp.py:29 | CampService.EXPAND_TERRITORY_MATURITY_BOOST | 1.0 | setting (move to data/) | a need or knowledge level that changes who eats, rests or trusts; a balance number |
| src/world/creature_territory.py:26 | CreatureTerritoryService.DEFAULT_TERRITORY_MATURITY_RATE | 0.03 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/creature_territory.py:27 | CreatureTerritoryService.TERRITORY_MATURITY_THRESHOLD | 100.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/displacement.py:30 | DisplacementService.DISPLACEMENT_THRESHOLD | 0.6 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/ecology.py:22 | ResourceEcologyService.DENSITY_CAP | 16 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/world/ecology.py:23 | ResourceEcologyService.DENSITY_FLOOR | 0.25 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/influence.py:25 | FactionInfluenceService.DEATH_INFLUENCE_SHIFT | 5.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/influence.py:26 | FactionInfluenceService.CONQUEST_THRESHOLD | -50.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/influence.py:27 | FactionInfluenceService.LIBERATION_THRESHOLD | 50.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/motivation/pressure_resolver.py:25 | _LEVEL_TO_FLOAT | {'very_high': 1.0, 'high': 0.9, 'medium_high': 0.75, 'medium | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/occupation_config.py:15 | MIN_OCCUPATION_SLOTS | 1 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/world/perception/gate.py:31 | _LEVEL_TO_FLOAT | {'very_high': 1.0, 'high': 0.9, 'medium_high': 0.75, 'medium | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/perception/gate.py:42 | _PERCEPTION_THRESHOLD | 0.2 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/perception/gate.py:47 | TOUCH_REACH | 1 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/world/perception/gate.py:51 | NIGHT_VISION_STEPS | 2 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/providers/requirements.py:29 | PerformanceBudgets.MAX_REQUIREMENTS_BUDGET | 1000 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/world/raid.py:10 | RaidService.RAID_BASE_SIZE | 3 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/world/raid.py:11 | RaidService.SANCTUARY_RADIUS | 15 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/world/regional_sovereignty.py:17 | RegionalSovereigntyService.TAX_RATE_ENTITY | 2.0 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/world/regional_sovereignty.py:18 | RegionalSovereigntyService.TAX_RATE_BUILDING | 10.0 | setting (move to data/) | a price, cost, wage or reputation/trust step: a game-economy number the owner would want to tune |
| src/world/regional_sovereignty.py:20 | RegionalSovereigntyService.CONQUERED_ATK_DEF_MOD | 0.8 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/regional_sovereignty.py:21 | RegionalSovereigntyService.CONQUERED_SPD_MOD | 0.9 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/world/reproduction_humanoid.py:27 | HumanoidReproductionService.HUMANOID_PAIRING_RADIUS | 10.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/worldassembly/cover.py:19 | TILES_PER_DENSITY_UNIT | 1000.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/worldbuilding/camp_food.py:16 | CAMP_SPAWN_RANGE | 8.0 | setting (move to data/) | a distance or reach in tiles: a world-scale number |
| src/worldbuilding/compiler.py:120 | _ENTITY_SPAWN_COLLISION_MAX_REROLLS | 12 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/worldbuilding/compiler.py:121 | _ENTITY_SPAWN_COLLISION_SUB_ID_BASE | 100 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/worldbuilding/compiler.py:126 | RESOURCE_PLACEMENT_ATTEMPTS | 64 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/worldbuilding/compiler.py:259 | _YOUNG_ADULT_ELDER_RATIO | {'young': 0.3, 'adult': 0.5, 'elder': 0.2} | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/worldgeneration/generator.py:54 | _TOWN_REFERENCE_AREA | 900 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/worldgeneration/generator.py:55 | _WILD_REFERENCE_AREA | 3366 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/worldgeneration/generator.py:56 | _WILD_REFERENCE_HAZARD | 1.2 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |
| src/worldgeneration/generator.py:401 | ProceduralCompositionGenerator.BUDGET | 6 | code invariant | a bound, id range or budget for the code itself; changing it changes no rule of the game |
| src/worldgeneration/scorer.py:29 | ModuleScorer._DANGER_MAX | 5.0 | setting (move to data/) | a balance number (a rate, threshold, weight, band or size) that shapes behaviour; a designer would tune it |

Counts: code invariant 150, setting (move to data/) 196.

## Observations for the audit

- **Names and values disagree:** `SEASONAL_PROPAGATION_INTERVAL = 500` ticks is 5 hours; a season is 72,000 ticks. `REPRODUCTION_COOLDOWN_TICKS = 400` is a 4-hour birth cooldown against a 70-year life.
- **Two scales sit side by side:** the biological layer (healing 2 to 4 days, starvation 2.5 days, hunger line about 9.5 h) is tuned in days, while most behaviour windows (Table A, WINDOW-FITTED) are minutes to hours. Life stages and lifespan are in fantasy years (12, 60, 70 years = 3.5M to 20M ticks) and no run reaches them.
- **One constant has no reader:** `RAID_INTERVAL_DAYS`.
- **A literal sits outside the calendar module:** the life-stage boundaries in `src/ai/life_stage.py` repeat `fantasy_years_to_ticks(12)` and `(60)` as numbers.
- **Most WINDOW-FITTED values read `state.tick`**, so they would be unchanged under a lower ticks/day only if their meaning were held in ticks; held in hours they would scale. That distinction is the one the recommendation has to make explicit.
