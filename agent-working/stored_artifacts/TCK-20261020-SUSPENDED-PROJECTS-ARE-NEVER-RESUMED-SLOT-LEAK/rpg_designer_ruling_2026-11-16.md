---
status: active
layer: ai
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK
phase: open
date: 2026-11-16
tags: []
---

# N10: when a SUSPENDED project resumes or ends, and the own-job counts (rpg-designer, 2026-11-16, v1.1)

- Ticket: TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK.
- Dispatched to ubuntu as a HARD liveness repair (#715 6916732562). M1 pace (a): #715 6912138476, memo row 96.
- Read on origin/main:
  - src/core/strategic.py: ProjectState, ProjectEnd, live_projects;
  - src/ai/goals/live_record_route.py (2.143);
  - src/engine/tactical.py `_suspend_project_for_threat`;
  - intelligence.py evaluate_project_switch / resume_project / the detour resume;
  - events.py :165.
- The ticket's 2026-10-21 findings still describe the suspend writers. The resume path changed since then: 2.143 replaced first-of-kind with `same_kind_record`.

## (a) The harm join is withdrawn
- My 11-02 "counts first: a harm join, no fix shape before I read it" was a BALANCE diagnosis. It asked whether the leak kills.
- Under M1 pace (a), a diagnosis like that is not a gate. N10's HARD part is liveness: a record that can never leave SUSPENDED is a state that never exits.
- So N10 is an own-job check (below), at 1 seed per world.
- The harm join becomes an optional BALANCE row. It's run only if the backlog picks it up. CAP_REFUSAL and "no project, no capacity" counts are reported, base vs fix.
- The owner was told N10 is an own-job check, and that stays true.

## (b) The lifecycle rule

### Resume (no new trigger)
A SUSPENDED project resumes only by the paths that exist today:
- its kind wins goal selection at a matching target (`route_live_record`, 2.143);
- a detour completes (intelligence.py, the detour-completion resume).

I add no threat-cleared or blocker-cleared resume. Each would be a new choice rule, which is behaviour, and liveness doesn't need it.

### End: a bounded suspension
- A SUSPENDED project that has been SUSPENDED for `SUSPENSION_TTL_TICKS` ticks without resuming ends.
  - Its status becomes ABANDONED, and its `ended_by` is set to a new `ProjectEnd.SUSPENSION_EXPIRED` through `end_record`. Its typed reason is recorded once, as with SUPERSEDED_BY_TARGET.
  - One bound applies to every project kind, the exempt need projects of step 2 included. A need that arises again builds or resumes as it does today.
- `SUSPENSION_TTL_TICKS = 200`.
  - The value is BALANCE, not law. It matches the 200-tick window used by R3 and the harm join, and it's reviewed with the post-foundation bands.
  - Liveness only needs it to be finite.
- **The clock:** a new `ProjectState.suspended_since: Optional[int]`.
  - **Who writes it:** every SUSPENDED writer sets it to the current tick:
    - the switch (`evaluate_project_switch`);
    - the tactical threat suspend;
    - the near-death path, which has no production caller today but is set for consistency.
  - **Clearing:** `resume_project` clears it to None.
  - **Hash:** it's omitted from the canonical dict while None, like `cleared_since`, so the hash of a state with no SUSPENDED project doesn't move.
  - **Field order:** it's appended last, with a FIELD_RULES fill of None.
  - **A SUSPENDED record with None** (an old checkpoint): the expiry pass stamps the current tick on first sight, and the age counts from there.
- **Where it runs:** in the subject's strategic pass, before goal selection and the capacity gate, so the freed slot counts on the same call. It goes through StrategicUpdate and the authoritative apply path, never as a direct write.
  - The bound a subject can actually see is TTL + its strategic cadence gap. The planner states that gap from the code.
- **Unchanged:**
  - 2.77's live predicate (SUSPENDED still counts as live);
  - the trims;
  - step 2's escalated-need admission;
  - no eviction to make room.

### Why a timer, not resume-on-condition or evict-on-refusal
- It is the simplest rule that ends every SUSPENDED record. It needs no new choice: no "which one to evict", no "has the blocker cleared".
- The ticket's out-of-scope already rejects eviction.
- Simpler option: none simpler gives liveness. Not fixing leaves the state that never exits, which is a HARD liveness fail.
- Cost of the timer: a project that would have been worth resuming after 200 ticks is lost, and is rebuilt as a new project if its goal wins again (existing behaviour). That's a balance effect, so it's reported.

### Docs, in the same change
- Bible 04, the project lifecycle (L225 area);
- a divergence entry (rationale class Bounded);
- the parity-ledger row in strategic_cognition.yaml;
- the ProjectEnd docstring.
- Checkpoint-format ticket: `suspended_since` is an append. Whichever of N10 and TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION lands second adds it to the fingerprint/FIELD_RULES set.

## Own-job counts (HARD; fixed before data, never rewritten)
- **Run:** the fix arm only, the 3 gate worlds of paired.WORLDS (frontier_living_world, urban_political, crowded_frontier; v1.1 fix 2026-11-16: v1 said frontier_marches, which M1-base does not cover), s42, 5000 ticks, spied plus a plain twin (6 processes).
- **What the spy records:** inputs only, per strategic call for each alive subject:
  - the tick, subject, and each live project's id, kind, status, suspended_since, ended_by;
  - the current project id;
  - each SUSPENDED→terminal transition, with its tick and reason.
- I assign the classes.
- **The bars:**
  - **L1, no unbounded suspension.** An alive subject's SUSPENDED project with age > TTL + cadence gap: **0**.
  - **L2, no leak at the cap.** An alive subject at cap (live == max_active_projects) whose live set is all SUSPENDED for longer than TTL + gap: **0**. This is the ticket's AC.
  - **L3, no early or untyped end.** A SUSPENSION_EXPIRED end at age < TTL, or a SUSPENDED→ABANDONED by this rule without the typed reason: **0**.
  - **L4, the clock is honest.** A SUSPENDED project with suspended_since None after its first strategic pass, or an ACTIVE or terminal project with suspended_since set: **0**.
  - **L5, resume unchanged.** Resumes counted by path (route_live_record vs detour completion). Reported, no bar.
- **Not vacuous:** at least 1 SUSPENSION_EXPIRED end over the 3 worlds. The ticket shows thousands of SUSPENDED ticks, so 0 means the rule never fired, and that's a trip.
- **HARD evidence:**
  - spied == plain hash;
  - spy exceptions and logging_errors empty;
  - spy and runner pinned at the shas I approve;
  - no crash or ENOMEM.
- **Reported (BALANCE):**
  - the CAP_REFUSAL ticks and subjects;
  - "no project, no capacity" subjects per world (sampled every 20 ticks);
  - deaths per world × cause.
  - Base arm = M1-base cells if ubuntu's M1-base exists, else the next pooled reading.
