"""Static guard for TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST (AC4): the paired-arms workflow is manual, advisory, pinned and non-cancelling.

No GitHub Actions execution is possible from pytest, so this reads the YAML. The pin guard (`test_workflow_actions_pinned_by_sha.py`) and the context guard
(`test_workflow_run_blocks_take_github_context_via_env.py`) glob / list workflows too; this file also pins that they cover this one.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tests.static import test_workflow_actions_pinned_by_sha as pins
from tests.static import test_workflow_run_blocks_take_github_context_via_env as ctx

_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "paired-arms.yml"
INPUTS = {"base_sha", "new_sha", "step", "worlds", "seeds", "ticks", "self_check"}


def _wf() -> dict:
    return yaml.safe_load(_PATH.read_text(encoding="utf-8"))


def _on() -> dict:
    wf = _wf()
    return wf.get("on", wf.get(True))  # YAML 1.1 reads a bare `on` key as True


def test_it_is_dispatch_only_with_no_pull_request_push_or_schedule_trigger():
    on = _on()
    assert set(on) == {"workflow_dispatch"}
    for trigger in ("pull_request", "pull_request_target", "push", "schedule", "workflow_run", "workflow_call", "release"):
        assert trigger not in on


def test_the_dispatch_inputs_are_the_ticket_ones():
    inputs = _on()["workflow_dispatch"]["inputs"]
    assert INPUTS <= set(inputs)
    assert {name for name, spec in inputs.items() if spec.get("required")} == {"base_sha", "new_sha", "step"}
    assert inputs["self_check"]["default"] == "seed42" and inputs["legacy_base"]["type"] == "boolean"


def test_concurrency_is_per_step_and_never_cancels_a_running_pair():
    concurrency = _wf()["concurrency"]
    assert concurrency["cancel-in-progress"] is False
    assert concurrency["group"] == "paired-arms-${{ inputs.step }}"


def test_every_action_is_pinned_by_sha_and_the_two_guards_cover_this_file():
    assert pins.unpinned(_PATH.read_text(encoding="utf-8")) == []
    assert "paired-arms.yml" in pins.WORKFLOWS
    assert ctx.offending_steps(_PATH.read_text(encoding="utf-8")) == []
    assert _PATH in ctx.FILES


def test_the_jobs_are_plan_arms_aggregate_with_least_privilege():
    jobs = _wf()["jobs"]
    assert list(jobs) == ["plan", "arms", "aggregate"]
    for name, job in jobs.items():
        assert job["permissions"] == {"contents": "read"}, name
        assert job["timeout-minutes"] <= 360, name


def test_the_matrix_is_per_world_and_seed_and_both_arms_run_in_the_same_job():
    arms = _wf()["jobs"]["arms"]
    assert arms["strategy"]["fail-fast"] is False
    assert "needs.plan.outputs.matrix" in arms["strategy"]["matrix"]
    steps = {s["name"]: s for s in arms["steps"] if "name" in s}
    base, new, repeat = steps["Base arm"], steps["New arm"], steps["Base-vs-base repeat arm"]
    assert "--arm base" in base["run"] and "${BASE_SHA}" in base["run"] and "if" not in base
    assert "--arm new" in new["run"] and "${NEW_SHA}" in new["run"] and new["if"] == "${{ matrix.kind == 'pair' }}"
    assert "--repeat" in repeat["run"] and "${BASE_SHA}" in repeat["run"] and repeat["if"] == "${{ matrix.kind == 'self' }}"
    for step in (base, new, repeat):
        assert "paired_arms run-arm" in step["run"] and "--cache arm-cache" in step["run"]  # paired's own functions, never a re-implementation in the workflow


def test_every_job_checks_out_the_same_ref_so_the_child_hash_agrees():
    for name, job in _wf()["jobs"].items():
        checkouts = [s for s in job["steps"] if str(s.get("uses", "")).startswith("actions/checkout@")]
        assert len(checkouts) == 1 and "ref" not in checkouts[0].get("with", {}), name  # the dispatched ref, the same commit in plan, arms and aggregate


def test_artifact_names_carry_step_world_and_seed_and_self_jobs_are_marked():
    upload = next(s for s in _wf()["jobs"]["arms"]["steps"] if str(s.get("uses", "")).startswith("actions/upload-artifact@"))
    name = upload["with"]["name"]
    assert name.startswith("paired-arms-${{ needs.plan.outputs.slug }}-${{ matrix.world }}-s${{ matrix.seed }}") and "-self" in name
    assert upload["with"]["path"] == "upload/"
    download = next(s for s in _wf()["jobs"]["aggregate"]["steps"] if str(s.get("uses", "")).startswith("actions/download-artifact@"))
    assert download["with"]["pattern"] == "paired-arms-${{ needs.plan.outputs.slug }}-*" and "merge-multiple" not in download["with"]


def test_the_aggregate_refuses_mixed_runners_before_calling_paired_collected_with_the_verdict_json():
    steps = [s for s in _wf()["jobs"]["aggregate"]["steps"] if "name" in s]
    names = [s["name"] for s in steps]
    assert names.index("Assemble one paired cache root") < names.index("Compare with paired.py --collected")
    assemble = next(s for s in steps if s["name"] == "Assemble one paired cache root")["run"]
    assert "paired_arms assemble" in assemble and '--base "${BASE_SHA}"' in assemble and '--new "${NEW_SHA}"' in assemble
    compare = next(s for s in steps if s["name"] == "Compare with paired.py --collected")["run"]
    assert "tools.rpg_measure.paired --collected collected" in compare and "--verdict-json verdict.json" in compare
    assert "--jobs" not in compare and "--clean-cache" not in compare  # both are rejected with --collected


def test_no_step_pipes_a_refusable_command_into_tee():
    for name, job in _wf()["jobs"].items():
        for step in job["steps"]:
            assert "| tee" not in str(step.get("run", "")), f"{name}/{step.get('name')}: the default shell has no pipefail, a pipe hides the exit status"


def test_unit_infra_fetches_exactly_the_pre_record_arm_trees_arm_childs_test_declares():
    """unit-infra checks out at depth 1, so the two old arm trees must be fetched by sha before the tests that archive them run; the step and the test's list are held equal
    so they cannot drift (TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE)."""
    from tests.unit.tools import test_arm_child_pinned_check as arm_test

    workflow = yaml.safe_load((Path(__file__).resolve().parents[2] / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["unit-infra"]["steps"]
    fetches = [(i, st) for i, st in enumerate(steps) if str(st.get("name", "")).startswith("Fetch the pre-record arm trees")]
    assert len(fetches) == 1, "exactly one such step (the base-branch collect-only step has its own, unrelated git fetch)"
    index, step = fetches[0]
    assert str(steps[0].get("uses", "")).startswith("actions/checkout@") and index == 1, "right after checkout, before setup-uv"
    assert str(steps[2].get("uses", "")).startswith("astral-sh/setup-uv@")
    words = step["run"].split()
    assert words[:5] == ["git", "fetch", "--no-tags", "--depth=1", "origin"]
    assert sorted(words[5:]) == sorted(arm_test.PRE_RECORD) and all(len(w) == 40 for w in words[5:])


# TCK-20261115-PAIRED-ARMS-RUNS-ONLY-COMMITS-ON-A-REPO-BRANCH: no token on disk while the arms run dispatched code, and only repo-branch commits run.
def _checkout_steps() -> list[tuple[str, dict]]:
    return [
        (job_name, step)
        for job_name, job in _wf()["jobs"].items()
        for step in job["steps"]
        if str(step.get("uses", "")).startswith("actions/checkout@")
    ]


def test_every_checkout_keeps_no_token_on_disk():
    checkouts = _checkout_steps()
    assert {job for job, _ in checkouts} == {"plan", "arms", "aggregate"}
    for job, step in checkouts:
        assert step.get("with", {}).get("persist-credentials") is False, f"{job}: a checkout persists GITHUB_TOKEN in .git/config"


def _plan_steps() -> list[dict]:
    return _wf()["jobs"]["plan"]["steps"]


def _step_index(prefix: str) -> int:
    return next(i for i, step in enumerate(_plan_steps()) if str(step.get("name", "")).startswith(prefix))


def test_the_plan_refuses_a_commit_no_repo_branch_contains_before_it_writes_the_matrix():
    refuse, plan = _step_index("Refuse a commit"), _step_index("Plan")
    assert refuse < plan, "the containment check must run before the step that writes the matrix output"
    step = _plan_steps()[refuse]
    assert step["env"] == {"BASE_SHA": "${{ inputs.base_sha }}", "NEW_SHA": "${{ inputs.new_sha }}"}
    run = step["run"]
    assert "${{" not in run, "inputs reach the script only through env"
    assert "--filter=blob:none" in run and "--no-tags" in run
    assert "'+refs/heads/*:refs/remotes/origin/*'" in run, "every branch, mapped to remote-tracking refs, is the whole fetch"
    assert "refs/pull" not in run, "pull refs stay outside the fetch: a fork pull request's commit must not count as contained"
    assert "--unshallow" in run, "the checkout is depth 1, which cannot prove containment"
    assert "cat-file -e" in run and "^{commit}" in run
    assert "branch -r --contains" in run, "a commit that exists locally but sits on no branch must still be refused"
    assert run.count("exit 1") >= 3


def test_the_header_comment_states_the_hardening_and_what_it_does_not_guard():
    header = _PATH.read_text(encoding="utf-8").split("\non:", 1)[0]
    assert "persist-credentials: false" in header and "refuses a base/new sha that" in header
    assert "push access" in header and "other workflows' checkouts still persist" in header
    assert "anonymous, so it needs the repo to stay public" in header and "fail closed" in header


def test_the_arms_job_still_fetches_the_two_shas_anonymously_by_sha():
    fetch = next(step for step in _wf()["jobs"]["arms"]["steps"] if step.get("name") == "Fetch the base and new commits")
    assert fetch["run"] == 'git fetch --no-tags --depth=1 origin "${BASE_SHA}" "${NEW_SHA}"'
    assert "env" not in fetch or "TOKEN" not in str(fetch["env"])


def test_evidence_defaults_true_and_the_plan_step_passes_it_through():
    """AC6 (g): the evidence input defaults to true and reaches `paired_arms plan --evidence`, so self_check off is refused unless the dispatcher opts out."""
    spec = _on()["workflow_dispatch"]["inputs"]["evidence"]
    assert spec["type"] == "boolean" and spec["default"] is True
    step = next(s for s in _wf()["jobs"]["plan"]["steps"] if s.get("id") == "plan")
    assert step["env"]["EVIDENCE"] == "${{ inputs.evidence }}"
    assert '--evidence' in step["run"] and 'EVIDENCE}" = "true"' in step["run"]
