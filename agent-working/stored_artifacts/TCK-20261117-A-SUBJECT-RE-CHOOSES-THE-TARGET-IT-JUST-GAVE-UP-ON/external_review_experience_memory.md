---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON
artifact_type: report
tags: []
---

> Owner-provided external input (#715 7090468332 / 7090493248), copied verbatim from tmp/reviews/navigation_experience_memory_design_review.md; not written by this repository's sessions.

# Design Review: Reason-Based Entity Experience Memory and Deferred Reassessment

**Project:** `rpg-sim-lab/rpg-based-simulation`  
**Related change:** [PR #996 — A subject does not re-choose the target it just gave up on](https://github.com/rpg-sim-lab/rpg-based-simulation/pull/996)  
**Reviewed PR head:** `4ab97912ef57f188efc7780172d18bf1a4748fb7`  
**Document status:** Proposal for owner review — not an implementation specification yet  
**Scope:** Entity memory, navigation failure handling, destination evaluation, cognitive reassessment, and scheduling. This review does not inspect or rely on anything under `agent-working/`.

---

## 1. Executive Summary

This proposal recommends evolving the repeated-destination protection in PR #996 from a time-based suppression mechanism into a **reason-based, entity-owned experience memory with deferred reassessment**.

The desired behavior is not simply:

> The entity failed to reach destination X, so prevent it from choosing X for N ticks.

Instead, the entity should retain a structured explanation of the failure:

> I failed to reach or use destination X for reason R, under conditions C. I expect that reason may change when condition M changes, so I should reconsider this conclusion at an appropriate time or when relevant evidence arrives.

When the entity reconsiders, it must perform a fresh evaluation using its current state and currently available information. If the problem remains unresolved, it must create a **new reassessment cycle**, including a newly derived decision about when to reconsider again. The previous cycle's schedule, delay, and assumptions must not simply carry forward.

The central design principles are:

1. **Remember causes, not just outcomes.** A failure record must say why the attempt failed and preserve the evidence supporting that explanation.
2. **Reassess conditions, not elapsed time alone.** A past failure is not a permanent prohibition. A destination may become viable after the entity grows stronger, recovers, obtains equipment, learns new information, or observes that an obstruction has changed.
3. **Schedule cognition deliberately.** The entity should estimate when another evaluation is worth performing, instead of repeatedly reconsidering an unchanged problem.
4. **Allow relevant changes to trigger early reconsideration.** A meaningful event may invalidate the old conclusion before its planned review time.
5. **Reset the complete review process after every reconsideration.** If the reason still applies, derive the next review plan again from the newly observed state. Do not inherit the previous wait interval or mechanically increase it.
6. **Keep memory separate from decision policy.** Memory stores experience; reassessment evaluates whether the old explanation remains valid; destination policy decides how that result affects the current candidate.
7. **Preserve immediate navigation safety.** A movement give-up must still clear the active target/path immediately and deterministically. Long-term learning must not delay that same-tick correction.

The proposal does not recommend reusing `CausalMemory` as-is, nor does it recommend treating all failures as one kind of navigation failure. It recommends extending the existing per-entity memory architecture with a typed, target/context-aware experience record and a deterministic reassessment mechanism.

## 2. Problem Statement

PR #996 addresses a real feedback loop:

1. Movement detects repeated oscillation or an unsuccessful way-round attempt.
2. Movement gives up and clears the active navigation target/path.
3. Strategic cognition subsequently chooses the same destination again.
4. The entity repeats the same failure instead of learning from the previous attempt.

The current solution adds a typed `GiveUpRecord`, converts it into a subject-level ACCESS blocker, and suppresses nearby destination proposals for a configured period. This protects against immediate repetition, but its core representation is still a statement about a recent failure and its anchor, rather than a durable explanation of why the attempt failed and what would make a retry sensible.

A fixed suppression window cannot express important differences between failure causes:

- An entity that was too weak may become capable after leveling up or upgrading equipment.
- An entity that was exhausted may become capable after resting.
- A route blocked by a moving entity may become passable when the obstruction moves.
- A route blocked by static terrain may remain impossible until the starting position, route, or world topology changes.
- A pathfinding oscillation may require a different route-search opportunity, not a stronger combat build.

These cases should not share one generic retry timer or one generic blacklist rule.

The broader goal is to make the entity behave like an agent with lived experience: it remembers what happened, forms a reasoned expectation, avoids wasting effort while nothing relevant has changed, and revisits the conclusion when there is a plausible reason to do so.

## 3. Current Repository Foundations and Gaps

This section describes the inspected repository state at the reviewed PR head. It is not a claim that every existing memory mechanism is active in the default runtime profile.

### 3.1 Existing per-entity memory structures

The project already has a nested cognition/memory model in `src/core/cognition.py`:

- `CausalMemory` stores bounded `CausalMemoryEntry` values with event kind, interpreted causes, confidence, future advice, tick, and optional region.
- `SpatialMemory` stores visited regions, safe/dangerous routes, known resource sites, failed search locations, and a home base.
- `ExperienceMemory` exists as a generic shell, currently with untyped `records: Tuple[Any, ...]` and a capacity.
- `TemporalModel` contains deadlines, cooldowns, stale facts, urgency, and delay-risk structures.

This is a strong foundation, but none of these records currently expresses the complete semantics required here.

### 3.2 Why the existing structures should not be reused without refinement

**`CausalMemory` is too general for destination-specific suppression.** It records an interpreted lesson and future advice, but it does not provide a robust identity for the destination, intent, route context, invalidation condition, or next reassessment plan. It should remain useful for general lessons, not become a catch-all navigation blacklist.

**`FailedSearchMemory` is too narrow.** It currently contains only `site_id` and `tick`. It does not represent the cause, evidence, intent, confidence, condition that could resolve the failure, or when it should be reconsidered.

**`RouteMemory` is not yet a failure-reassessment model.** It currently contains a route identifier and safety score. It may be a future input to route learning, but it does not encode the cause of an unsuccessful attempt.

**`TemporalModel.cooldowns` have different semantics.** A cooldown's `ready_tick` represents when an action or retry becomes available. The existing `TemporalPressureService` translates active cooldowns into urgency values; it does not itself schedule a cognitive reassessment or determine whether a prior belief is still valid. A review schedule should not be smuggled into action cooldown state merely because both contain a tick.

### 3.3 Memory pipeline reachability is not automatic

`MemoryUpdatePhase` is wired into the authoritative pipeline behind `ENABLE_MEMORY_UPDATE`, whose current default is OFF in `src/domains/optimization/feature_flags.py`. Therefore, adding a field to entity memory does not guarantee that the field will be written or consumed in ordinary runtime behavior.

The proposed navigation-experience mechanism must have an explicitly verified production write path and read path. It must not silently depend on a feature-gated memory phase that remains disabled by default. Whether it gets a dedicated rollout flag or a deliberately enabled memory rollout is an implementation/owner decision.

### 3.4 Existing cognition/capability estimation is useful but incomplete

`CapabilityEstimateService` already produces deterministic, scoped subjective estimates for combat, travel, gathering, and crafting. It can be a useful input when reassessing a capability-related failure.

However, it should not be treated as a complete solution:

- The caller must provide a scoped `CapabilityContext`.
- The current travel-region path is not actively populated by a production caller.
- `entity.self_model.capabilities.estimates` is not generally populated by the current production flow.
- Static route feasibility, dynamic occupancy, pathfinding oscillation, and world-topology changes are not the same thing as combat capability.

The proposal should reuse the relevant estimator where appropriate, while keeping failure-specific reassessment logic explicit.

## 4. What PR #996 Currently Does

This proposal builds on the useful parts of #996 rather than discarding its safety work.

### 4.1 Movement-side detection

The movement work adds pursuit-anchored way-round tracking. It tracks the count, best distance, pursuit anchor, and last event tick. Progress can rebaseline the count; a sufficiently long quiet interval or a changed pursuit anchor starts a fresh count. The configured way-round limit and quiet interval are content-backed settings.

When the oscillation/way-round replan ladder cannot find a suitable alternative, the movement layer gives up, clears the target/path, and emits a typed `GiveUpRecord`.

### 4.2 The current give-up record is intentionally small

`src/core/giveup_records.py` currently models a give-up as:

- an anchor tile; and
- the tick when the give-up occurred.

This is sufficient to communicate a spatially anchored event to strategic cognition, but it does not explain the reason for failure, identify the semantic destination, or distinguish the intent behind the target.

### 4.3 Strategic filing and suppression

The strategic blocker lifecycle converts give-up observations into ACCESS blockers. The destination-suppression policy then prevents place-target proposals near the anchor while the relevant blocker is still suppressed. The current proposal gate is centralised through `propose_target()` and is used by many strategic and tactical target writers.

The current suppression model includes:

- an anchor-based neighborhood (Chebyshev radius 1);
- subject-level ACCESS blockers;
- suppression windows that grow across give-ups (the content settings currently provide the 100/200/400/800 progression);
- a give-up limit that can end the current project; and
- pending give-up records that participate in same-tick suppression before strategic filing is complete.

The strategic give-up count is distinct from the ordinary blocker failure count. The count can accumulate across project changes, which is a deliberate behavior in the current implementation.

### 4.4 What should be preserved

The following aspects of #996 remain valuable and should survive the proposed redesign:

- movement is allowed to conclude that it cannot continue pursuing its current target;
- target and path clearing happens immediately through the authoritative update path;
- the movement-to-strategy communication is typed rather than inferred from arbitrary log text;
- target proposals are checked centrally rather than relying on every writer to reimplement suppression;
- same-tick precedence is explicit: a new give-up must not be defeated by a target set emitted in the same update;
- transient update fields are merged and applied deterministically; and
- tests exercise the apply-ordering and target-writer coverage, not only isolated helper functions.

The redesign changes the *meaning and lifecycle of the persistent response* to a give-up. It should not weaken the immediate same-tick correction.

## 5. Proposed Concept: Entity-Owned Destination Experience Memory

### 5.1 Core mental model

A destination failure should be recorded as an experience with a cause, observed evidence, applicable context, and a plan for reconsideration.

The memory should answer:

1. What destination or route was involved?
2. What was the entity trying to accomplish there?
3. What happened?
4. Why does the entity believe it happened?
5. What evidence supports that explanation?
6. What condition would make the explanation no longer apply?
7. When is it worth evaluating that condition again?
8. What new information or event could justify an earlier evaluation?

The memory is an entity's subjective record. It must not become a global, omniscient declaration that a place is objectively forbidden to everyone.

### 5.2 Illustrative typed model

The following is a conceptual schema, not a prescribed final Python API:

```python
@dataclass(frozen=True, slots=True)
class DestinationExperience:
    experience_id: str
    target_ref: TargetRef
    intent_kind: str

    failure_kind: FailureKind
    evidence: tuple[FailureEvidence, ...]
    confidence: float

    status: ExperienceStatus
    last_observed_tick: int
    last_reviewed_tick: int | None

    reassessment: ReassessmentPlan
    cycle_id: int


@dataclass(frozen=True, slots=True)
class FailureEvidence:
    cause: FailureCause
    observed_value: object | None
    required_condition: object | None
    source: EvidenceSource
    confidence: float


@dataclass(frozen=True, slots=True)
class ReassessmentPlan:
    next_review_tick: int | None
    wake_conditions: tuple[ReassessmentTrigger, ...]
    rationale: str
    confidence: float
```

The final schema should use concrete typed values rather than unconstrained `object` fields. The example is intended to show the responsibilities and relationships, not to prescribe loose runtime data.

### 5.3 Identity and scope

A memory entry should not be keyed only by an anchor coordinate. At minimum, its identity should account for:

- a stable target reference (place/building/entity/resource/coordinate or a typed route reference);
- the intent or goal family for which the target was selected; and
- relevant approach context where the cause is route-specific.

Why intent matters: failing to reach a building while seeking work should not automatically prohibit visiting the same building to eat, rest, trade, or seek information.

Why context matters: a failure from one starting position does not prove that the same destination is unreachable from another position. A moving obstruction or a changed route may invalidate an earlier conclusion.

Coordinates and anchors can remain useful evidence, but they should not be the sole identity of a semantic destination. For free-coordinate movement, a route/approach signature may be needed. The exact representation should be decided after auditing the actual target types that flow through #996.

### 5.4 Suggested status semantics

Possible statuses:

- `ACTIVE`: the experience is relevant and its failure explanation currently justifies some caution or suppression.
- `UNCERTAIN`: the cause is not known well enough to justify a hard prohibition; a soft score adjustment or another evaluation may be appropriate.
- `RESOLVED`: a fresh evaluation found that the recorded failure condition no longer applies.
- `SUPERSEDED`: a newer experience or a changed explanation has replaced the old active assessment.

`ALLOWED` should generally not be a permanent memory status. It is better treated as the result of the current reassessment: the old negative assessment no longer blocks the candidate. A destination can become infeasible again later, so “allowed forever” would be another stale belief.

Historical records may be retained for explanation, debugging, and learning. If retained, resolved history must not continue to apply a negative score or suppression.

## 6. Failure Causes Must Be Specific and Reassessable

The system must not invent a cause just because it observed a give-up. A movement give-up is evidence that the current pursuit failed under current conditions; it does not by itself prove that the entity is too weak, that the destination is permanently inaccessible, or that a hostile is responsible.

A typed cause taxonomy should distinguish at least these categories:

| Failure category | Example evidence | Reassessment condition |
|---|---|---|
| `INSUFFICIENT_CAPABILITY` | Current subjective capability estimate is below the estimated requirement | Re-evaluate when relevant capability, equipment, skill, or knowledge changes, or when a newly predicted progression point is reached |
| `INSUFFICIENT_VITALITY` | HP/stamina or recovery state made the attempt unviable | Re-evaluate after relevant recovery, rest, or state change |
| `DYNAMIC_OBSTRUCTION` | A known/perceived entity or temporary obstruction prevented passage | Re-evaluate when the obstruction is observed to move, disappear, or stop blocking the approach |
| `STATIC_ROUTE_OBSTRUCTION` | The currently known route is blocked by terrain/building geometry | Re-evaluate when the start position, known route, or relevant topology changes |
| `ROUTE_SEARCH_FAILURE` | A route search failed, exhausted its bound, or could not produce a better route | Re-evaluate when route-search inputs or route-planning opportunities materially change |
| `OSCILLATION` | Repeated movement events show no meaningful progress in the same pursuit | Re-evaluate when the route/approach context changes or new navigation evidence is available |
| `MISSING_INFORMATION` | The entity lacks enough information to choose a viable approach | Re-evaluate when it receives relevant information or observes new evidence |
| `UNCLASSIFIED` | The system knows the attempt failed but cannot justify a more precise cause | Do not pretend to know why; use conservative, lower-confidence behavior and gather better evidence |

This taxonomy is a starting point. It should be expanded only when a real producer can supply the required evidence and a real consumer can reassess it.

### 6.1 Capability example: “I am strong enough now”

Suppose an entity previously judged a dangerous destination too difficult to approach because its estimated combat capability was insufficient.

At the first failure, memory stores the then-current estimate, the perceived/known threat assessment, and the reason the attempt was judged unsuitable. Later, the entity levels up, upgrades equipment, recovers, or acquires better information.

When it next evaluates the destination, it recomputes capability using its current state and currently available information. If the capability condition is now sufficient, the old negative assessment is resolved and must no longer suppress the destination.

The important point is not a hard-coded timer. The important point is that the old conclusion is tied to a condition that can change.

### 6.2 Navigation example: a way-round give-up

A `WAYROUND_GIVE_UP` should initially be recorded as a navigation failure with the actual movement evidence available at that point: pursuit identity, target/anchor, relevant path/obstruction observations, distance/progress history, and the reason code emitted by the movement system.

It must not automatically become `INSUFFICIENT_CAPABILITY`. If the evidence only proves oscillation, the recorded explanation should remain route/search/approach-related or unclassified. Combat strength should only be part of the explanation when the failure producer has evidence that combat danger or capability actually prevented the approach.

This distinction prevents a plausible but incorrect inference from being stored as a durable belief.

## 7. Deferred Reassessment: When Should the Entity Think Again?

### 7.1 Reassessment scheduling is not memory expiration

The record should preserve a `next_review_tick` when a time-based review can be reasonably predicted. This tick means:

> The entity expects that another evaluation may be worth performing around this point.

It does **not** mean:

- the memory expires at that tick;
- the destination automatically becomes allowed;
- the entity is guaranteed to attempt the destination; or
- the entity must interrupt a non-interruptible action at that exact tick.

The experience can remain in memory after the planned review time until it is evaluated. A review is an opportunity to re-evaluate the old conclusion, not a timer that automatically reverses it.

### 7.2 Derive the next review from the cause

The system should estimate when the cause might plausibly change, using deterministic domain logic and the entity's own information.

Examples:

- **Capability deficit:** estimate when planned training/progression or a known equipment acquisition may move capability toward the required level.
- **Low vitality:** estimate when recovery/rest or an expected recovery process may make the entity viable again.
- **Dynamic obstruction:** prefer event-driven review when the entity observes that the obstruction has changed; a time estimate is only appropriate when there is a justified known process that predicts the change.
- **Static obstruction:** do not repeatedly poll an unchanged map. Reconsider when the route, starting position, or known topology changes.
- **Oscillation:** reconsider when a meaningful navigation input changes, or when another route-search opportunity is justified. A stronger character is not automatically a better pathfinder.
- **Missing information:** reconsider when relevant information is received, rather than periodically repeating the same uninformed evaluation.

A global `RETRY_AFTER_N_TICKS` or fixed exponential progression is not an adequate substitute for this reasoning.

### 7.3 Combine predicted time and event-driven triggers

A reassessment plan may contain both:

- an optional predicted `next_review_tick`; and
- a set of relevant early-review triggers.

Examples of triggers include a capability-relevant equipment change, a level/skill change, meaningful recovery, a newly observed obstruction change, a route/topology change, or new information about the target.

The trigger set must be specific to the recorded cause. An unrelated state mutation must not wake the entity to reassess every remembered destination.

Triggers must also respect the entity's information boundary. The entity should react to facts it can perceive, learn, or legitimately derive from its own state—not to hidden omniscient world changes it has no way to know about.

### 7.4 When no defensible time prediction exists

Some causes are event-driven and cannot honestly be assigned a useful future tick. In those cases, `next_review_tick` may be absent and the memory waits for a relevant trigger or an ordinary decision point at which the target is reconsidered.

If the design requires a fallback review to avoid permanent dormancy, that fallback must be justified by the cognition/scheduling model and entity context, not added as an unexplained universal constant. The owner should explicitly decide whether every unresolved experience needs a periodic fallback or whether some memories should remain dormant until new evidence arrives.

## 8. Mandatory Rule: Every Reconsideration Starts a Fresh Cycle

This is a core invariant, not an optional optimization.

### 8.1 Required semantics

Whenever an entity actually reconsiders an experience, the previous reassessment plan is consumed. The entity then:

1. captures the current relevant state and evidence;
2. re-evaluates the original cause from the beginning;
3. checks whether the old failure condition still applies;
4. identifies any new or changed causes;
5. produces a fresh assessment; and
6. if the problem remains unresolved, derives a completely new plan for when and how to reconsider again.

This applies whether the reconsideration was caused by a scheduled review or an early relevant event.

### 8.2 If the cause is resolved

If the fresh evaluation shows that the recorded failure condition no longer applies:

- remove the active suppression or negative decision effect associated with that cause;
- mark the experience `RESOLVED` or retain it as historical evidence;
- allow the destination to compete normally under current decision policy;
- do not preserve the previous `next_review_tick` as an active restriction; and
- do not mark the destination permanently `ALLOWED`.

A new failure under new conditions may create a new active experience/cycle.

### 8.3 If the cause remains unresolved

If the fresh evaluation still finds the destination infeasible or undesirable:

- replace the stale evidence snapshot with the current evidence, or append a new immutable review event if the data model uses event history;
- record the new assessment and its confidence;
- recalculate which condition could change the conclusion;
- derive a new `next_review_tick` and/or new event triggers from the current situation;
- start a new cycle; and
- do not mechanically carry forward, add to, multiply, or otherwise reuse the previous waiting interval.

For example, if an entity reconsiders and still lacks the required capability, it must estimate the next useful review opportunity based on its current progression and plans. It must not simply say “I waited 200 ticks last time, so now I will wait 400.”

### 8.4 Reset what, exactly?

The **cycle-local** state must be reset:

- prior scheduled review time;
- prior wait interval/delay;
- pending/due marker for the previous cycle;
- prior predicted condition-change time;
- transient review result; and
- any cycle-local retry/backoff accumulator.

The entity may retain **historical** information for audit or learning:

- prior failure observations;
- previous assessment outcomes;
- review timestamps;
- evidence that earlier predictions were too early or too late; and
- a count of historical reviews, if useful for observability.

However, historical counters must not silently become a fixed exponential-backoff policy. If historical outcomes are ever used to improve future predictions, that must be an explicit deterministic learning rule that estimates the next opportunity from relevant observed rates—not a mechanical “multiply the old delay” shortcut.

### 8.5 Idempotence and repeated evaluation

A single reconsideration event must not create multiple new cycles due to repeated evaluation in the same tick, duplicate event delivery, or multiple target writers. The implementation needs a stable cycle/event identity or equivalent idempotency rule.

A review that happens in the same tick as a relevant state change should evaluate against the authoritative/staged state defined by the pipeline ordering. It must not read a stale pre-change snapshot and then overwrite the newly computed reassessment plan.

## 9. Destination Evaluation and Decision Policy

Memory should not directly execute movement and should not independently decide the entity's goal. It should inform a central destination evaluation policy.

### 9.1 Suggested evaluation sequence

When a destination candidate is considered:

1. Resolve the candidate's stable target identity and intent context.
2. Find only experiences relevant to that target/context.
3. Determine whether a relevant event or scheduled review makes reassessment due.
4. If due, run a fresh cause-specific reassessment and create a new cycle/result.
5. If not due, use the latest valid assessment without repeating the full evaluation.
6. Pass the resulting assessment into destination policy.
7. Decide whether the candidate is open, softly discouraged, or currently suppressed.

### 9.2 Avoid turning every failure into a hard blacklist

The decision effect should reflect the strength and kind of evidence:

- **Proven current impossibility:** a hard refusal may be justified while the exact relevant condition remains true.
- **Probable but uncertain failure:** use a soft penalty or reduced attractiveness rather than a hard prohibition.
- **Resolved cause:** no active negative effect from that experience.
- **Unclassified failure:** avoid an unjustified permanent/long prohibition. Preserve the observation and seek better evidence.

A prior navigation failure should not suppress an unrelated intent to the same place. It should not suppress a materially different route or approach if the memory only describes the old one.

### 9.3 Keep the central proposal point

The existing `propose_target()`/central destination gate is a good architectural place to preserve as the single proposal policy for place destinations. It should evolve from “is there a currently suppressed ACCESS blocker near this anchor?” into “what is the current experience-based assessment of this candidate for this entity and intent?”

All relevant target writers should continue to pass through the shared policy. The static architecture check and mutant tests added around the single proposal path remain valuable and should be adapted, not removed.

## 10. Scheduling and Runtime Integration

### 10.1 Scheduling responsibility

The reassessment plan owns the target-specific planned review time and triggers. The scheduler owns deciding when an entity's brain is eligible to run.

When a review becomes due, it should create a **reassessment wake request** for the owning entity. The scheduler can then wake the entity's brain at the next legal decision point, subject to action-interruption rules.

A due review should not automatically interrupt a non-interruptible committed action merely because its tick arrived. The due marker should remain pending until a legal decision point occurs.

### 10.2 Avoid per-tick full-memory scans

The implementation should not run an expensive reassessment of every remembered destination for every entity on every tick.

Preferred behavior:

- process a new failure when it is emitted;
- process explicit relevant change events for entries indexed by the affected condition/target;
- process entries whose `next_review_tick` becomes due;
- otherwise reuse the most recent valid assessment;
- reassess a specific entry when its destination is considered and a relevant trigger has invalidated the old assessment.

The data structures should support bounded lookup by entity and target/context. Any global due-entry index must be deterministic and must be checkpoint/replay-safe if it affects authoritative behavior.

### 10.3 Distinguish cognition scheduling from action cooldowns

Do not reuse `TemporalModel.cooldowns` as a hidden substitute for reassessment plans. A skill cooldown, a failed-action retry delay, and the time at which an entity should reconsider a belief are different concepts.

They may share low-level scheduling utilities, but their stored semantics, consumers, and observability should remain distinct.

### 10.4 Do not depend accidentally on the existing default-OFF memory phase

The write and read paths for destination experiences must be verified in the intended runtime profile. If the implementation chooses to route writes through `MemoryUpdatePhase`, the rollout status of `ENABLE_MEMORY_UPDATE` must be an explicit owner decision. Otherwise, a dedicated typed navigation-experience write/apply path or separately controlled phase may be more appropriate.

## 11. Authoritative State, Determinism, Replay, and Persistence

This project relies on deterministic state transitions. The proposed memory and scheduler behavior must preserve that contract.

Requirements:

- use frozen/typed state records and authoritative update/patch paths;
- do not mutate entity memory directly from movement or strategy workers;
- do not use wall-clock time;
- do not use unseeded randomness to choose review timing;
- ensure ordering and tie-breaking are deterministic;
- serialize all behaviorally relevant active memory and schedule fields in canonical state;
- include behaviorally relevant fields in state fingerprints/replay comparisons;
- support checkpoint round-tripping and backward-compatible defaults for older checkpoints;
- ensure update merge semantics do not lose a same-tick cognition/memory write from an earlier phase; and
- make duplicate failure/review events idempotent.

If history is retained only for observability and does not affect simulation behavior, it may be kept outside the authoritative state hash. The distinction must be explicit: any value that changes a future decision or wake time is authoritative state and must be serialized/fingerprinted.

## 12. Performance and Cognitive Cost

The design goal is not to make every entity think more frequently. It is to make its thinking more useful.

The implementation should favor:

- small, typed, bounded experience records;
- cause-specific reassessment instead of generic re-planning;
- event-driven invalidation where a meaningful event exists;
- one fresh evaluation per due cycle;
- no repeated evaluation while neither the relevant evidence nor the review schedule has changed;
- deterministic due-entry lookup; and
- observability for the number and cost of reassessments.

Useful counters include:

- experiences created by failure kind;
- reassessments triggered by schedule versus early event;
- reassessments resolved versus unresolved versus uncertain;
- newly derived review delays (or event-only plans);
- due reviews deferred because the entity was in a non-interruptible action;
- repeated reviews that found no relevant change; and
- destination proposals blocked or penalized by active experience memory.

These metrics should explain whether memory is reducing repeated work without making entities indecisive or inert.

## 13. Migration Strategy from PR #996

A staged migration is safer than replacing every component at once.

### Stage 1 — Preserve the immediate movement behavior

Keep the way-round/oscillation detection, typed movement-to-strategy signal, immediate target/path clearing, and same-tick precedence. Do not weaken the guarantee that a target just given up on cannot be reinstalled in the same authoritative update.

### Stage 2 — Enrich the failure observation

Extend the transient signal so it carries the evidence actually known by the movement/attempt layer:

- stable destination/target reference where available;
- intent context where available;
- typed movement failure reason;
- anchor and relevant route/approach context;
- observed progress/oscillation evidence; and
- the tick/event identity.

Do not infer a richer semantic cause than the producer can support. `UNCLASSIFIED` is preferable to fabricated certainty.

### Stage 3 — Store the experience on the entity

Add a typed entity-memory record and an authoritative write path. Decide whether the natural home is a refined `ExperienceMemory` or a new navigation-experience structure adjacent to `SpatialMemory`. Do not force broad target/intent/cause semantics into the narrow existing `FailedSearchMemory` type.

### Stage 4 — Add fresh reassessment and scheduling

Implement cause-specific reassessment, a planned review time where defensible, relevant early triggers, and the mandatory cycle-reset semantics. At this stage, tests should prove the schedule is derived afresh after every review.

### Stage 5 — Connect destination policy and scheduler

Update the central destination policy to consume experience assessments. Connect due reviews to the entity scheduler without interrupting actions that are not legally interruptible. Ensure early events and due reviews are deterministic and idempotent.

### Stage 6 — Retire duplicate suppression semantics

Avoid running both a legacy subject-level ACCESS blocker and the new experience policy as independent sources of truth for the same give-up. Otherwise one layer may continue suppressing a destination after the experience layer has resolved it.

Other ACCESS blockers that represent distinct strategic facts should remain unaffected. Existing checkpoints with legacy blockers need a deliberate compatibility policy. Do not fabricate a detailed cause from a legacy anchor/tick record; either preserve the legacy behavior until safely retired or migrate it as a low-confidence/unclassified historical observation.

## 14. Important Edge Cases and Risks

### 14.1 Same destination, different intent

A failed attempt to reach a workplace for employment should not automatically prevent eating or resting at the same building. Target identity alone is insufficient; intent context matters.

### 14.2 Same destination, different approach

A route failure from one starting position should not be treated as proof that every approach is impossible. Route-specific memories should be scoped to the relevant approach or invalidated when the starting position/path context materially changes.

### 14.3 Moving corridor obstruction (the known G3 gap)

PR #996 explicitly leaves a moving-corridor case for later work: a per-anchor suppression can miss a corridor whose obstruction/anchor changes position over time. Experience memory offers a better conceptual fit, but it does not automatically solve the problem. A future corridor-level representation may need a route segment, obstruction identity, or route signature rather than a single failed tile. This should remain an explicit follow-up until backed by a clear producer and tests.

### 14.4 Cause changes between reviews

A fresh review may discover that the original explanation is no longer the main problem and a different cause now applies. The system should replace/supersede the active explanation or maintain multiple independently reassessable causes. It must not blindly keep suppressing based on an obsolete cause.

### 14.5 Multiple simultaneous causes

A destination may be blocked by more than one condition, e.g. poor capability and low vitality. Each cause may have a different invalidation condition and review opportunity. The model should avoid treating the whole destination as resolved merely because one cause disappears while another remains active.

### 14.6 Insufficient information

The entity may not know whether an obstruction has disappeared or whether a destination is safe. In that case, the correct assessment may be `UNCERTAIN`, not `RESOLVED`. New perception or information can trigger a fresh cycle.

### 14.7 False predictions

A derived review time can be early or late. The entity may reconsider and find no meaningful change. That still consumes the current cycle: it must form a fresh assessment and derive a new plan from current evidence. It must not immediately loop through the same reconsideration every tick.

### 14.8 Unintended permanent suppression

If a relevant trigger can never be observed and no defensible fallback review exists, an active experience could remain indefinitely. The owner must decide which cause types are allowed to be event-only and which require a periodic fallback. This is a domain rule, not something to hide behind a universal timeout.

## 15. Testing and Acceptance Criteria

The change should not be considered complete merely because unit tests show that a record can be stored. It needs producer, persistence, scheduler, reassessment, and real decision-consumer coverage.

### 15.1 Memory model and authoritative apply

- A typed experience can be created from a genuine failure observation.
- Target identity, intent, failure kind, evidence, confidence, status, and review plan survive authoritative apply.
- Same-tick memory writes merge safely with other cognition writes.
- Capacity/eviction behavior is bounded and deterministic.
- Checkpoint round-trip preserves all behaviorally relevant fields.
- Canonical state and replay fingerprints change when active experience/schedule state changes.
- Legacy checkpoint defaults are backward compatible.

### 15.2 Cause-specific reassessment

- Capability-related failure resolves after a relevant capability improvement makes the current estimate sufficient.
- Capability-related failure remains active when only unrelated stats change.
- Vitality-related failure resolves after relevant recovery.
- A dynamic obstruction failure is reconsidered after the entity observes a meaningful obstruction change.
- A static route failure is not repeatedly rechecked without a relevant route/start/topology change or an explicitly justified review.
- Oscillation evidence is not misclassified as insufficient combat capability.
- Unknown causes remain uncertain/unclassified rather than being promoted to false certainty.
- Multiple causes are resolved independently; one resolved cause does not hide another active cause.

### 15.3 Scheduling and reset semantics

- The first failure produces a cause-appropriate reassessment plan.
- A scheduled review becomes due at the derived tick and creates one legal reassessment opportunity.
- A relevant event can trigger early reassessment before the scheduled tick.
- An unrelated event does not trigger reassessment.
- A due review deferred by a non-interruptible action remains pending until the next legal decision point.
- Every actual review consumes the previous cycle's schedule and cycle-local state.
- If the cause remains unresolved, the next review plan is recomputed from the newly observed state.
- The next review is not calculated by blindly adding the old delay, doubling a previous delay, or relying on a cumulative retry counter.
- If a review finds no change, a fresh plan is still created and the entity does not reconsider every subsequent tick.
- Duplicate event delivery or repeated same-tick evaluation cannot create multiple cycles.

### 15.4 Destination policy

- A resolved experience no longer suppresses or penalizes the candidate.
- An active failure only affects matching target/intent/approach context.
- A different intent to the same target is not incorrectly blocked.
- A materially different route/starting context can be evaluated independently.
- Every relevant target writer still passes through the central proposal policy.
- A same-tick give-up still clears the old target/path and prevents reinstallation of the just-abandoned target in that update.
- Tactical retreat/flight alternatives are not accidentally eliminated by stale memory where safety behavior requires a fallback.

### 15.5 Runtime, determinism, and performance

- The production runtime profile actually writes and reads the new memory; tests must not only call services directly.
- Cross-hash-seed runs produce identical state transitions and review schedules.
- Replay from checkpoint yields the same decisions and wake timing.
- There is no per-tick full scan/reassessment of all entity memories.
- The number of reassessments is bounded by actual failure events, due reviews, relevant changes, and candidate evaluation.
- Performance measurements compare the same scenarios/seeds before and after the feature.

## 16. Open Design Decisions for Owner Review

The following should be decided before implementation is treated as approved:

1. **Memory placement:** Should typed destination experiences live under `ExperienceMemory`, under `SpatialMemory`, or in a dedicated `NavigationMemory` inside `MemoryModel`? The existing `FailedSearchMemory` is too narrow, but the best ownership boundary remains a design decision.
2. **Target identity:** Which real target types must be supported in the first slice (place/building, entity, resource site, arbitrary coordinate, route segment)?
3. **Intent scope:** Which intent/goal identifier is stable enough to distinguish employment, eating, resting, retreat, combat positioning, investigation, and other movement purposes?
4. **Cause taxonomy:** Which causes can the current movement/strategic producers genuinely identify today, and which should remain unclassified until richer evidence exists?
5. **Hard versus soft effects:** Under what evidence/confidence conditions may an experience hard-refuse a candidate rather than merely penalize it?
6. **Review-time inference:** Which existing progression/recovery/knowledge models can produce defensible estimates of when a condition may change? What should happen when no estimate is possible?
7. **Early triggers:** Which typed state changes/events can invalidate each cause, and how does the entity know about those changes?
8. **Scheduler behavior:** Should a due reassessment wake the brain immediately when legal, or wait for the next ordinary strategic decision unless the entity is otherwise idle/held?
9. **Historical retention:** Should resolved experiences remain as history, and if so, what bounded retention/eviction policy is appropriate?
10. **Rollout:** Should this be guarded by a dedicated feature flag, or should the existing memory feature rollout be explicitly changed? The current default-OFF state must not be ignored.
11. **Legacy blocker compatibility:** How are already persisted ACCESS blockers handled during transition without fabricating causes or keeping two competing suppression systems active?
12. **Corridor memory:** Is G3 included in this design slice, or does it remain a deliberately separate follow-up requiring route-segment/corridor identity?

## 17. Recommendation

Adopt the reason-based experience-memory direction as the target architecture, but do not immediately rewrite all of PR #996 around a broad “learning system.” The safest first increment is narrow:

1. Preserve #996's movement give-up detection and immediate same-tick target clearing.
2. Enrich the typed failure observation with the real evidence available at the movement/attempt layer.
3. Store an entity-owned, target/intent-aware experience record.
4. Implement one or two well-supported cause-specific reassessments first, rather than claiming generic reasoning for every failure category.
5. Add deferred review scheduling with cause-derived timing and relevant early triggers.
6. Enforce the fresh-cycle reset rule after every reconsideration, including a fresh derivation of the next review plan when the failure remains unresolved.
7. Wire the experience memory into the real destination policy and scheduler, with deterministic/replay-safe tests.
8. Retire the legacy give-up ACCESS suppression for the same failure path only when the new consumer demonstrably provides equivalent or better protection.

The key design statement is:

> **An entity should remember why a destination failed, not merely when it failed. It should avoid spending cognition on an unchanged problem, reconsider when the predicted review point or relevant evidence warrants it, and rebuild its assessment and next-review plan from scratch every time it thinks again. A past failure is evidence, not a permanent prohibition.**

## 18. Repository References

All code references below are pinned to the reviewed PR #996 head where possible. No files under `agent-working/` were used.

- [PR #996](https://github.com/rpg-sim-lab/rpg-based-simulation/pull/996)
- [`src/core/giveup_records.py`](https://github.com/rpg-sim-lab/rpg-based-simulation/blob/4ab97912ef57f188efc7780172d18bf1a4748fb7/src/core/giveup_records.py)
- [`src/strategy/destination_suppression.py`](https://github.com/rpg-sim-lab/rpg-based-simulation/blob/4ab97912ef57f188efc7780172d18bf1a4748fb7/src/strategy/destination_suppression.py)
- [`src/systems/strategic_systems/blocker_lifecycle.py`](https://github.com/rpg-sim-lab/rpg-based-simulation/blob/4ab97912ef57f188efc7780172d18bf1a4748fb7/src/systems/strategic_systems/blocker_lifecycle.py)
- [`src/engine/movement.py`](https://github.com/rpg-sim-lab/rpg-based-simulation/blob/4ab97912ef57f188efc7780172d18bf1a4748fb7/src/engine/movement.py)
- [`src/engine/route_search.py`](https://github.com/rpg-sim-lab/rpg-based-simulation/blob/4ab97912ef57f188efc7780172d18bf1a4748fb7/src/engine/route_search.py)
- [`src/core/cognition.py`](https://github.com/rpg-sim-lab/rpg-based-simulation/blob/4ab97912ef57f188efc7780172d18bf1a4748fb7/src/core/cognition.py)
- [`src/domains/memory/phase.py`](https://github.com/rpg-sim-lab/rpg-based-simulation/blob/4ab97912ef57f188efc7780172d18bf1a4748fb7/src/domains/memory/phase.py)
- [`src/domains/memory/spatial_update.py`](https://github.com/rpg-sim-lab/rpg-based-simulation/blob/4ab97912ef57f188efc7780172d18bf1a4748fb7/src/domains/memory/spatial_update.py)
- [`docs/simulation/domains/memory_contract.md`](https://github.com/rpg-sim-lab/rpg-based-simulation/blob/19f6ecac8d90450f3a564073886aa41acd73598f/docs/simulation/domains/memory_contract.md)
- [`src/cognition/capability_estimate.py`](https://github.com/rpg-sim-lab/rpg-based-simulation/blob/4ab97912ef57f188efc7780172d18bf1a4748fb7/src/cognition/capability_estimate.py)
- [`docs/cognition/capability_and_knowledge_contract.md`](https://github.com/rpg-sim-lab/rpg-based-simulation/blob/4ab97912ef57f188efc7780172d18bf1a4748fb7/docs/cognition/capability_and_knowledge_contract.md)
- [`src/engine/scheduler.py`](https://github.com/rpg-sim-lab/rpg-based-simulation/blob/4ab97912ef57f188efc7780172d18bf1a4748fb7/src/engine/scheduler.py)
- [`src/engine/pipeline.py`](https://github.com/rpg-sim-lab/rpg-based-simulation/blob/4ab97912ef57f188efc7780172d18bf1a4748fb7/src/engine/pipeline.py)
- [`src/domains/optimization/feature_flags.py`](https://github.com/rpg-sim-lab/rpg-based-simulation/blob/4ab97912ef57f188efc7780172d18bf1a4748fb7/src/domains/optimization/feature_flags.py)

---

**Review note:** This document consolidates the design discussion and proposes an architecture for review. It does not modify PR #996, submit a GitHub review, or claim that the proposed model has been implemented or validated by tests.
