---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS
phase: open
date: 2026-11-01
tags: [cooperation, social]
---

# Plan: a contract-formed group keeps its binding through a leadership change

Ruling: rpg-designer 2026-11-01 (word for word in the ticket). Shape A, with the formation-tick stamp. Not B, not C. This plan answers rpg-planner's six questions and states where the code makes the ruling's wording ambiguous. No code before the planner's OK.

## Code facts (tree = this branch, edb638b6a src, checked 2026-11-01)

- Formation: `src/systems/world_systems/groups.py:322-347`. Leader is `id_a`; the contract is the first ACTIVE one on `entity_a.strategic.contracts` (sorted ids) whose other party is near and ungrouped. The record gets `contract_id=active_contract_id` and leaves `last_leadership_check_tick` at its default 0.
- Dissolution read: `groups.py:156-171`. Inside the per-member loop. Reads `group.contract_id` from `state.entities[group.leader_id]` (pending leader update first). A missing or non-ACTIVE or expired contract sets `contract_invalid`, which removes that member (`group_id_set=-1`); the group ends only through the `len(new_member_ids) < 2` rule at line ~180. So today the "dissolve for contract" is really "drop each non-leader member", and a pair always ends.
- Election: `src/engine/pipeline_phases/groups.py:76-` runs `PartyLifecycleService.check_leadership` over state groups plus the groups added this tick; gate `tick - last_leadership_check_tick >= 100` (`party_lifecycle.py:24,48`).
- Trace (investigation.md): the contract sits only on the source's map and never moves; the election moves the leader to the other member, so the leader-map read finds nothing.

## Shape (as ruled)

1. `ContractBinding(holder_id: int, contract_id: str)` frozen dataclass in `src/core/state.py` next to `GroupRecord`; `GroupRecord.bound_by: Optional[ContractBinding] = None`; `to_canonical_dict` adds `"bound_by": {"holder_id":..,"contract_id":..}` only when not None (omitted otherwise, so unbound groups are byte-identical).
2. Formation (`groups.py:339`) sets `bound_by=ContractBinding(holder_id=id_a, contract_id=active_contract_id)` and `last_leadership_check_tick=state.tick`. Single writer: this one site.
3. Dissolution: a group-level check before the member loop. If `bound_by` is set, read `state.entities[bound_by.holder_id].strategic.contracts[bound_by.contract_id]` (with the same pending-update-first lookup as today, on the holder). Reasons:
   - holder not in group's remaining members or dead/inactive: BINDING_HOLDER_LEFT;
   - holder present, contract not found: BINDING_CONTRACT_MISSING;
   - found, status != ACTIVE, or `state.tick > expiry_tick` with expiry != -1: BINDING_CONTRACT_NOT_ACTIVE (carries the status; expired reported as status EXPIRED if the stored status is still ACTIVE).
   Any of the three dissolves the whole group (all members get `group_id_set=-1`, record kept with `dissolution_tick`), which replaces the per-member contract_invalid for bound groups.
4. No rebinding (designer, advance ruling): when the binding contract ends the group dissolves and is never rebound to the pair's next ACTIVE contract. No code path writes `bound_by` after formation.

## Answers to the planner's six questions

### 1. `contract_id` vs `bound_by.contract_id`: one source
Readers of `GroupRecord.contract_id` in `src`: `groups.py:157,163,165` (the dissolution read), `groups.py:344` (the formation write), `groups.py:382` (`find_group_for_contract`, no caller in `src` or `tools`; tests only), `replay/fingerprint.py:281` (the string `contract=...` in the per-group fingerprint), and `to_canonical_dict` (`state.py:749`). In tests: `tests/unit/social/test_domain_7_social.py:164,182,198` and `test_groups.py`-style hand-built groups.
Options:
- **O1 (recommended): keep `contract_id` as the one stored contract id and make the binding hold only the holder.** `bound_by: Optional[ContractBinding]` with `ContractBinding(holder_id)` would not carry the contract id; the contract id is read from `contract_id`. One fact, one place; fingerprint, canonical dict and `find_group_for_contract` unchanged. Deviation from the ruling's example `ContractBinding(holder_id, contract_id)` (the ruling says "e.g.").
- **O2: the ruling's literal shape**, `ContractBinding(holder_id, contract_id)`, and `contract_id` becomes a derived property reading `bound_by.contract_id`. This forces a change to the canonical dict (the `contract_id` key must still be emitted for byte identity of existing unbound-with-contract groups, which only tests build), the fingerprint and three test sites. Cleaner single source but the larger diff.
- **O3: both stored, with a constructor invariant `bound_by.contract_id == contract_id` (checked in `__post_init__`).** Two copies of one fact; rejected by the define-once rule.
I need the planner's choice; the rest of this plan holds under O1 and O2 (only the type of the binding and the property differ).

### 2. Other builders / setters and unbound groups
`GroupRecord(` in `src`: `groups.py:339` (contract formation) and `engine/military_conflict.py:341` (FACTION_SQUAD, no `contract_id`, `bound_by` None, untouched). No other `src` site, no loader from a dict (checked: no `GroupRecord(**`, no from_dict; `engine/checkpoint.py:161` only canonicalises). `src/certification/scenarios.py` does not build groups (grep found none). Tests build records by hand in 19 files; only `test_domain_7_social.py` sets `contract_id`.
Every group made by the formation scan is made through a contract (the loop requires an ACTIVE contract), so there is no production path that creates a contract-less group other than the squad. After the fix every formed group has `bound_by`.
A hand-built record with `contract_id` set and `bound_by` None (tests; any legacy state): proposal is to keep the current leader-map read for it (legacy fallback, byte-identical to today) and state this in the code comment and the mechanics doc; production never produces it after the fix. The alternative, treating it as an unbound group that is never dissolved for its contract, changes behaviour of hand-built test groups. Planner to choose.

### 3. Old saves and checkpoints
There is no group loader from a saved dict in `src` (only the canonical writer), so a record without `bound_by` cannot be "loaded" into a different shape: it is constructed with the default None. The canonical dict omits the key for None, so every old record and every non-contract group canonicalises identically. No schema or fingerprint version constant exists to bump (grep of checkpoint/fingerprint found none). Hashes of runs that form contract groups do change (binding present, formation tick stamp), disclosed in the divergence entry; fixtures regenerated, not edited.

### 4. `member_distance`
Unchanged. The cohesion rule (`dist_sq > (cohesion_radius*2)**2`) stays in the per-member loop and drops that member; the `len < 2` rule dissolves the pair. For a bound pair that distance exit still ends the group, and the recorded reason stays whatever is recorded today (none, see 6). The binding check is separate and runs first, so a group is not both.

### 5. BINDING_HOLDER_LEFT: where the departure is seen
Two places can see it: (a) the group-level binding check, which asks "is the holder still alive, active and a member?" before the member loop, and (b) the existing member loop plus the size rule at line ~180. The pair case falls under both. Proposal: do it in (a), before the member loop, using `is_alive`/`is_active` (same-tick current update aware) and `holder_id in group.member_ids`; a pair whose holder died is recorded BINDING_HOLDER_LEFT and the member loop is skipped, so the generic size rule never gets to label it. A holder removed in the same tick by `member_distance` is a ordering case: the binding check runs first on the start-of-tick member set, so distance exits are seen on the next tick, unchanged. Holder = dead leader: the existing leader-dead branch at line 111 fires first; it keeps today's behaviour (no typed binding reason) unless the planner wants it relabelled BINDING_HOLDER_LEFT when `leader_id == holder_id`; this is the one place the order matters, so I ask.

### 6. Where typed reasons are stored
Nowhere today: the dissolved row carries only `dissolution_tick`; the `member_contract_*` labels in the measurements come from my probe. Proposal: `GroupRecord.dissolution_reason: Optional[GroupDissolutionReason]` with a `str` Enum (`BINDING_CONTRACT_NOT_ACTIVE`, `BINDING_CONTRACT_MISSING`, `BINDING_HOLDER_LEFT`), plus `dissolution_detail: Optional[str]` only if the status must be kept (NOT_ACTIVE with the status): I propose a typed `dissolution_contract_status: Optional[str]` instead of a free string. Both omitted from the canonical dict when None, so every existing dissolution (distance, size, leader dead) stays byte-identical with reason None. Set by the same writer that sets `dissolution_tick` for the binding path only. This adds two fields beyond the ruling's shape; if the planner prefers, the reason goes on the event stream only (no durable state), which loses the re-count the designer wants after the fix. The re-count needs the reason on the record.

## Other work
- Formation stamp (ruling item 3): `last_leadership_check_tick=state.tick` at line 339; groups_add rows seen by the election pass in `pipeline_phases/groups.py` then fail the gate for 100 ticks.
- Risk to check in code before tests: `get_relevant_group_ids` uses the dirty set. A long-lived bound group is only visited when its id is in the dirty set or on a force-full-scan tick; I must confirm the binding contract's status change reaches the dirty set or the check runs on full scan, else a bound group would outlive its contract. The test "binding contract ends -> group dissolves" runs through the real kernel path to cover this.
- Docs: `docs/mechanics/` social chapter and party contract doc, parity entry (new SOC id beside SOC-278), divergence 2.146 rewrite after the re-measure (id fix plus binding, Bug Fix).
- Docs/ledger edits for the group-id ticket stay as they are.

## PR notes carried
- Groups that now last feed REGROUP targets (ties to F3 lodger suppression and N14). If this lands before N14-on-F3, the N14 base sits at or after it, or the order is disclosed.
- 247 = distinct per run summed over 15 runs; drop post_lost; squads 0 in runs.
- Tickets TCK-20261101-A-NO-PARTNER-BLOCKER-IS-RE-CREATED-EVERY-TICK and TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE travel in the PR in todos/ and are not worked.

## Revision after the designer's rulings (2026-11-01) — supersedes the shape and answers above where they differ
The designer's words are in the ticket (word for word). As built:
- **Shape (Q1):** `GroupRecord.contract_holder_id: Optional[int]` plain field next to `contract_id` (the one stored contract id); no ContractBinding class. Omitted from the canonical dict when None; in the fingerprint string (`:holder=`) for bound groups only. `contract_id` set with no holder raises `GroupBindingError` at construction (no legacy fallback). Tests build with a holder.
- **Reasons (Q6):** `GroupDissolutionReason` enum (src/core/enums.py): BINDING_HOLDER_LEFT > BINDING_CONTRACT_MISSING > BINDING_CONTRACT_NOT_ACTIVE > LEADER_LOST > DEFECTION > MEMBERS_BELOW_TWO, one per dissolution, bound groups only. Stored on `GroupRecord.dissolution_reason` with the typed `dissolution_contract_status: ContractStatus` (time expiry records EXPIRED). Writers: `groups.py` (binding check first, then the leader-lost branch, then the size rule) and `party_lifecycle.py` check_defection (DEFECTION, or HOLDER_LEFT when the defector is the holder). The defection pass skips groups already dissolved this tick, so it cannot override a higher reason.
- **Q3 corrected (checkpoints):** the first plan said there is no load path. There is: `ScenarioCheckpointer` pickles the whole state. A slotted dataclass unpickles positionally (zip of fields and the saved tuple, no `__init__`/`__post_init__`), so (a) new slots are absent on old records and (b) a field inserted mid-class takes the next field's old value. Built: new group fields placed after `_canonical_cache`; `AuthoritativeState.next_group_id` moved to the last field (it sat before `next_item_instance_id` in the id-fix commit, which would have swallowed the item counter); one post-unpickle step `src/engine/checkpoint_fields.py` (`FIELD_RULES`, `FieldRule`, `fill_missing_fields`, `CheckpointFieldMissing`, a ValueError so the route answers 400) called once from `ScenarioCheckpointer.restore`. Rows: `next_group_id` seeded by `seeded_next_group_id`; the three group fields None on unbound groups, refused on any group with a `contract_id` (retained dissolved records included). No remote branch holds F3's file; if F3 lands first, add these rows to its module and re-run both sets of old-shape tests (PR notes say which case applied). The general format-version fix is TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION, not here.
- **Dirty set:** count first. 400t crowded_frontier s42 audit_mode: 0 live bound groups with an ended binding left undissolved; all 22 bound dissolutions were in the relevant set; full-scan ticks 0 (relevant set covered all groups on 15 of 400 ticks). Time expiry is not a silent no-write: `resolve_expirations` writes the status (13 of 13 NOT_ACTIVE were FULFILLED, none EXPIRED), which dirties the holder's group. Dirty set untouched. The 15-run report carries the per-run count and lag.
- **Not rebinding:** no code path writes `contract_holder_id`/`contract_id` after formation; test pins it.
- **Docs/parity:** mechanics ch07 (binding, cadence, reasons), parity SOC-279. Divergence 2.146 rewrite waits for the re-measure.

## Revision after the second designer rulings (Q3 pick, fact 2 predicate, fact 3) — as built in 64bf2767b
- **Q3 pick:** at formation the group binds the live contract with the LATEST `expiry_tick` among the contracts that qualified a partner; the holder stays `id_a`; formation only, no rebinding. Two readings are mine, not the designer's words: (1) **`expiry_tick == -1` (no expiry) ranks latest** (implemented as infinity); (2) **"qualified a partner"** means the partner passed the live / alive / ungrouped / not already forming / within 10 tiles checks, so a duplicate contract naming the same partner counts. A tie on expiry takes the lowest contract id (ids are scanned in sorted string order and a later one replaces only on a strictly later expiry).
- **Fact 2:** `contract_is_due` / `contract_is_live` in `src/systems/social_systems/contracts.py`; used by `resolve_expirations` (its old test `expiry != -1` and `tick >= expiry` is exactly "due"), by formation (a due contract forms no group) and by `_binding_end` (a due contract ends the group on its expiry tick as FULFILLED; the EXPIRED branch is removed).
- **Fact 3:** a bound group below two members records BINDING_HOLDER_LEFT when the holder is not among the remaining members.
- **Lag stop (planner, for the final set):** lag above 0 on any FULFILLED end stops the set at the end of that pair; the report names the group, contract, expiry, dissolution tick, whether the contracts phase ran on the expiry tick, and whether the group was in the relevant set. The dirty set is not changed here; a lag is brought to the planner. The set also counts the ticks the contracts phase skipped and the due contracts whose expiry fell on a skipped tick, so a lag of 0 that only holds because the phase never skipped is named as such.
