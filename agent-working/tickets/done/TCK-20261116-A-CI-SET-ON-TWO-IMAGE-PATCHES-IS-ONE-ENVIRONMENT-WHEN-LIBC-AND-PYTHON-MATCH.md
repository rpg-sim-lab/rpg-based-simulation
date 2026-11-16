---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261116-A-CI-SET-ON-TWO-IMAGE-PATCHES-IS-ONE-ENVIRONMENT-WHEN-LIBC-AND-PYTHON-MATCH
phase: done
date: 2026-11-16
tags: [testing, determinism]
---

# TCK-20261116-A-CI-SET-ON-TWO-IMAGE-PATCHES-IS-ONE-ENVIRONMENT-WHEN-LIBC-AND-PYTHON-MATCH

## Title
A CI set on two image patch versions is one environment when libc and the Python build match; a split is refused by name, and the AC1 table is readable from the log

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
T2 AC1's second off-host run, paired-arms.yml run 43805965260 on main a3ffe6bae (owner #715 6907556766), ran all 9 arm jobs successfully in 2.11 runner-h.
Its compare step then refused with exit 2: "missing collected results" for all 12 base/new keys (#715 fyi 6907980116).
GitHub had served one job (`urban_political` s43 pair) on runner image `ubuntu-26.04` Version `20261111.82.6`, and the other 8 on `20261111.196.1`.
- `paired.run_env` keys `runner = "ci:" + ImageOS-ImageVersion`, so that job's results keyed under a second env8.
- `_arm_dirs` then found two directories per key prefix, and `collected_path` returned a path that does not exist for every key.
- `assemble` compares only python and os, so it did not catch the split.
- `--collected` runs `missing_results` before `env_problems`, so the refusal was misnamed.
Refusing was correct (one recorded environment per set). The key is the problem: it splits on an image patch version that GitHub rolls out gradually, so a mixed set is likely on most 9-job runs.

rpg-planner ruled on env8 on 2026-11-16 (it owns the env8 ruling):
- Key on `ImageOS`, not `ImageVersion`.
- Add the two fields an image patch could change in the sim's bytes. The first is the C library, `platform.libc_ver()`: Python's math goes through the system libm. The second is the full Python build string, `sys.version`.
- Record `ImageVersion` in env.json and cost.json.
- Mixed python, os release (kernel), dists or uv_lock are still refused.
- The base-vs-base repeats stay the evidence that bytes did not move. A repeat that differs inside one env8 is a STOP, not a key change.

lead-planner-u24's condition: dropping the version from the key is a determinism claim, so the ticket must not merely assert it. In run 43805965260, no arm ran on both patch versions: the `.82.6` job was the only urban_political s43 job, and `run-arm` logs only wall time. So cross-patch byte identity is UNPROVEN by this run, and the ticket says so. The key stays safe by keying glibc and the Python build. Scope 4 makes future runs prove or disprove it.

## Scope
1. `tools/rpg_measure/paired.py` `run_env`:
   - CI runner = `"ci:" + ImageOS`, with the self-hosted and unidentified branches unchanged.
   - Add `libc` (`"-".join(platform.libc_ver())`, recorded as-is when empty) and `python_build` (`sys.version`) to the env dict for every runner, local included.
   - Record `image_version` in env.json. Whether it is a keyed field or a recorded-only field must be explicit. Prefer a separate recorded block outside the hashed dict, so it does not key.
   - `tools/test_architecture/paired_arms.py` `runner_identity` keeps the full image and records `libc` and `python_build` too.
2. `paired.py --collected`:
   - Run `env_problems` (and a new split check) BEFORE `missing_results`.
   - A prefix with more than one env8 directory is refused as "results built under N environments: <env8> (<field>=<value>) vs ...", naming the differing env fields.
   - The runner-identity comparison between the arms of a key uses the same fields as the key (ImageOS, not the full image), so it is never stricter or looser than the key.
3. `paired_arms assemble`: refuse a set whose jobs differ in any env-key field (from each job's env.json), not only in python or os, with the same naming. Two jobs that differ only in image version assemble.
4. Evidence for the claim:
   - `run-arm`'s console line prints the arm document's `final_hash` (and start hash) beside the wall time. The log then carries the hashes even when artifacts cannot be downloaded.
   - The aggregate step summary lists the image versions present in the set.
5. `.github/workflows/paired-arms.yml` compare step: after `paired --collected`, print `table.md` and `verdict.json` to the step log (`if: always()`, guarded by file existence). This host cannot download artifacts: blob storage returns 403 through FortiGate, so the AC1 byte comparison reads the CI table from the log.
6. Cache keys move for every runner, local included, because the env dict gains fields. The ticket and PR body say: existing caches are not reused under the new keys. Old entries are a miss, never read and never deleted, the same rule as the env8 introduction. `child_hash()` is unchanged (`arm_child.py` is not touched).

## Out of Scope
- `arm_child.py`, the child hash, refusal semantics other than the order and message in Scope 2, and the AC9 spy hook.
- Re-dispatching paired-arms. That is a new owner ask after this merges, and it carries an AC10 note: the CI tool commit then differs from the local one by #930 plus this ticket, all path, key or log changes with the child unchanged.

## Acceptance Criteria
- [x] AC1: tests show that two env dicts differing only in `ImageVersion` give one env8, and that differing `libc`, `python_build`, python, os, dists or uv_lock give different env8s.
- [x] AC2: a collected cache with a prefix split across two env8 directories is refused (exit 2) with a "built under 2 environments" message naming the differing field, and that refusal comes before any "missing" refusal. A test mirrors run 43805965260's shape: one pair job on a second env8.
- [x] AC3: `assemble` refuses a set split on an env-key field, and assembles a set split only on image version.
- [x] AC4: the `run-arm` log line carries `final_hash`. The shape test pins the workflow's `cat table.md` / `cat verdict.json` step. The workflow end-to-end test still passes with the new key.
- [x] AC5: the ticket and PR body state that cross-image-patch identity is unproven by run 43805965260, that keys move, and that old cache entries are a miss, not reused.
- [x] AC6: `test_paired_env_key.py`, `test_paired_relative_cache.py`, `test_paired_arms_workflow_end_to_end.py`, `test_paired_arms.py`, `test_rpg_measure_collected.py`, `test_rpg_measure.py`, `test_arm_child_pinned_check.py` and the workflow shape tests pass. Unit tests only, `-n 1`.

## Related Tickets
- TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST (parent T2; AC1 is blocked on this)
- TCK-20261116-AN-ARM-RUNS-WHEN-THE-CACHE-PATH-IS-RELATIVE (#930)
- TCK-20261115-PAIRED-ARMS-EVIDENCE-SETS-NEED-THEIR-REPEAT-AND-ONE-LOCKED-ENVIRONMENT (#927, introduced env8)

## Related Docs
- `docs/performance/` or the paired tool docs that describe env8. Update them if they list the key's fields.

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/rpg_measure/paired.py` (`run_env`, `env_key`, `env_problems`, `missing_results`, `_arm_dirs`, the `--collected` branch)
- `tools/test_architecture/paired_arms.py` (`runner_identity`, `assemble`, `run-arm`)
- `.github/workflows/paired-arms.yml`

## Assumptions / Open Questions
- RESOLVED 2026-11-16: rpg-planner ruled on env8 (above). The arrangement is the same as #928, #930 and #932: testing builds this and rpg-planner reviews the paired.py diff before the push.

## Implementation Notes
- `paired.run_env`: a CI runner is `ci:<ImageOS>` (the family); the env dict gains `libc` (`platform.libc_ver()` joined) and `python_build` (`sys.version`) for every runner, local included. `ImageVersion` is not in the dict. `write_env_json` writes it to `image.json` beside `env.json` (outside the hashed object, so it does not key). The self-hosted and unidentified branches are unchanged.
- `paired_arms.runner_identity` (cost.json) keeps the full `image` and adds `image_os`, `image_version`, `libc`, `python_build`. The fields compared across jobs and within a key are the keyed ones (`python`, `python_build`, `libc`, `os`, `image_os`, `uv_lock`); the image patch version is recorded and listed, never compared.
- `--collected` (both the neutral and the step branch): `env_problems` runs BEFORE `missing_results`. A prefix with several env8 directories is refused as "results built under N environments: <env8> (<field>=<value>, ...) vs <env8> (...)", naming the differing fields read from each directory's env.json.
- `assemble`: also compares the whole `env.json` across jobs and refuses a difference in any field by name ("built under different environments: <field> differs"); jobs that differ only in image version assemble. `image.json` and `cost.json` are per-job records and are exempt from the "two jobs wrote different bytes" check (found by the end-to-end test: the base arm's result directory is shared by a pair job and a self job, which may be served different image patches). `identities.json` and the assemble console line list the image versions present.
- `run-arm`'s console line carries `final_hash=` and `start_hash=` of the arm document beside the wall time.
- `paired-arms.yml`: a new step "Print the table and the verdict to the log" (`if: always()`, each file guarded by existence) after the compare step, and the step summary lists the runner image versions in the set. A separate step, not extra lines in the compare step, because a refusing compare exits non-zero.
- `arm_child.py` is NOT touched: `child_hash()` is unchanged (`9d13c131`).
- Docs: `docs/plans/test_architecture/reference/paired_arms_off_host.md` states the key's fields.
- FOR THE PR BODY (AC5): (1) cross-image-patch byte identity is UNPROVEN by run 43805965260: no arm ran on both patch versions (the `.82.6` job was the only urban_political s43 job) and run-arm logged only wall time. The key stays safe by keying glibc and the Python build; the final hashes now in the run-arm log, and the base-vs-base repeats, will prove or disprove it on future runs. (2) Cache keys MOVE for every runner, local included, because the env dict gains `libc` and `python_build` and a CI runner is keyed by `ImageOS`: existing caches are not reused under the new keys. Old entries are a miss, never read and never deleted, the same rule as the env8 introduction. (3) AC10 on re-dispatch: the CI tool commit will differ from the local one (f94417e6f) by #930 and this ticket, all path, key or log changes with the child unchanged.

## Test Summary
- 201 passed, `-p no:xdist -p no:randomly`, in 17 s (unit and static only): test_paired_env_key, test_paired_relative_cache, test_paired_arms_workflow_end_to_end, test_paired_arms, test_rpg_measure_collected, test_rpg_measure, test_arm_child_pinned_check, the workflow shape test and the two workflow-guard tests.
- AC1: two env dicts that differ only in `ImageVersion` are equal and share an env8; a change in libc, python_build, python, os, dists, uv_lock or runner gives a different env8.
- AC2: a collected cache with one pair job's new arm under a second env8 (libc differs) is refused (exit 2, REFUSED verdict) with "built under 2 environments ... libc=... glibc-2.99", and the message is not "missing collected results". A cache split only by recorded image versions compares (exit 0).
- AC3: `assemble` refuses jobs that differ in libc, python_build, image_os, python, os or uv_lock (cost record) or dists (env.json only); it assembles jobs and arms that differ only in image version and lists both versions.
- AC4: the `run-arm` line carries `final_hash=f1 start_hash=s1` (stub child); the shape test pins the print step and the summary line. The end-to-end test now serves one job a different `ImageVersion` (the run 43805965260 shape) and still assembles and compares to PASS, with both versions in `identities.json`.
- Revert evidence: with `ImageVersion` keyed again (`ci:<ImageOS>-<ImageVersion>`), 5 tests FAIL (both end-to-end tests, the CI-vs-local key test, the hosted-runner key test, `test_two_image_patch_versions_are_one_environment`). With the missing check put back before the env check, `test_a_prefix_split_across_two_env8_directories_is_refused_by_name_before_the_missing_check` FAILS. Both reverts undone before commit.

## Files Changed
- tools/rpg_measure/paired.py
- tools/test_architecture/paired_arms.py
- .github/workflows/paired-arms.yml
- docs/plans/test_architecture/reference/paired_arms_off_host.md
- tests/unit/tools/test_paired_env_key.py, test_paired_arms.py, test_paired_arms_workflow_end_to_end.py, test_paired_relative_cache.py, test_rpg_measure_collected.py
- tests/static/test_ci_paired_arms_workflow_shape.py

## Completion Summary
A GitHub image patch rollout no longer splits an evidence set: the key is the image family plus glibc and the Python build, the patch version is recorded and listed, a real split is refused by name before any "missing", and the run log carries the hashes and the table. Cross-patch identity remains unproven by run 43805965260; future runs will show it.
