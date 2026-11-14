"""Tests for tools/gate_checks/doc_drift.py (TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT and
TCK-20261108-STALE-DOC-DETECTION-PILOT). Every case builds a real git history in a temp repo; nothing reads the
project's own docs, and no test targets a known stale doc (the recall number is reported by the pilot, never asserted).
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

from tools.gate_checks import doc_drift


class FixtureRepo:
    def __init__(self, root: Path):
        self.root = root
        self.clock = 1_700_000_000
        self._git("init", "-q", "-b", "main")
        self._git("config", "user.email", "t@example.com")
        self._git("config", "user.name", "t")

    def _git(self, *args, check=True):
        env = {**os.environ, "GIT_AUTHOR_DATE": f"{self.clock} +0000", "GIT_COMMITTER_DATE": f"{self.clock} +0000"}
        return subprocess.run(["git", *args], cwd=self.root, check=check, capture_output=True, text=True, env=env).stdout

    def write(self, path: str, text: str):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def commit(self, message="c", days=1):
        self.clock += days * 86400
        self._git("add", "-A")
        self._git("commit", "-q", "-m", message)
        return self._git("rev-parse", "HEAD").strip()

    def repo(self, ref="HEAD"):
        repo = doc_drift.Repo(self.root, ref)
        assert repo.resolve()
        return repo


def doc(body="The kernel runs phases in order.\n", **fields):
    lines = ["---", "status: active", "layer: engine", "authority: P1", "audience: agent"]
    for key, value in fields.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines) + "\n---\n\n" + body


PATH = "docs/engine/kernel.md"


@pytest.fixture
def fx(tmp_path):
    return FixtureRepo(tmp_path)


def classify(fx, extra=()):
    repo = fx.repo()
    return doc_drift.classify(repo, PATH, (fx.root / PATH).read_text(encoding="utf-8"), extra)


def verified_doc(fx, **extra_fields):
    fx.write("src/engine/kernel.py", "def run():\n    return 1\n")
    fx.write(PATH, doc(evidence_paths="[src/engine/kernel.py]", verified_by="TCK-20261101-KERNEL", verified_at="abcdef1", **extra_fields))
    return fx.commit("verify the doc")


# --- AC 1: unverified ---------------------------------------------------------------------------------------------


def test_a_doc_without_verified_by_shows_as_unverified(fx):
    fx.write("src/engine/kernel.py", "x = 1\n")
    fx.write(PATH, doc(evidence_paths="[src/engine/kernel.py]"))
    fx.commit()
    report = doc_drift.drift_report(fx.repo(), [PATH])
    assert [(r["path"], r["state"]) for r in report["docs"]] == [(PATH, "unverified")]


def test_a_doc_with_no_field_at_all_is_only_counted(fx):
    fx.write(PATH, doc())
    fx.commit()
    report = doc_drift.drift_report(fx.repo())
    assert report["docs"] == [] and report["docs_without_fields"] == 1


# --- AC 2: drift signals ---------------------------------------------------------------------------------------------


def test_a_clean_verified_doc_keeps_its_state(fx):
    verified_doc(fx)
    assert classify(fx)["state"] == "verified_by"


def test_a_changed_evidence_path_needs_re_verify(fx):
    verified_doc(fx)
    fx.write("src/engine/kernel.py", "def run():\n    return 2\n")
    fx.commit("change the code")
    row = classify(fx)
    assert row["state"] == "needs-re-verify" and row["reasons"] == ["evidence changed: src/engine/kernel.py"]


def test_a_deleted_evidence_path_needs_re_verify(fx):
    verified_doc(fx)
    (fx.root / "src/engine/kernel.py").unlink()
    fx.commit("delete the code")
    assert classify(fx)["reasons"] == ["evidence deleted: src/engine/kernel.py"]


def test_a_rename_to_a_new_directory_shows_as_a_rename_not_a_delete(fx):
    verified_doc(fx)
    (fx.root / "src/core").mkdir()
    fx._git("mv", "src/engine/kernel.py", "src/core/kernel.py")
    fx.commit("move the code")
    assert classify(fx)["reasons"] == ["evidence renamed: src/engine/kernel.py -> src/core/kernel.py"]


def test_the_name_status_diff_is_run_without_a_pathspec(fx, monkeypatch):
    verified_doc(fx)
    seen = []
    original = doc_drift.Repo.git

    def spy(self, *args):
        seen.append(args)
        return original(self, *args)

    monkeypatch.setattr(doc_drift.Repo, "git", spy)
    classify(fx)
    name_status = [a for a in seen if "--name-status" in a and "diff" in a]
    assert name_status and all("--" not in a for a in name_status)


def test_a_doc_text_edit_after_the_baseline_needs_re_verify(fx):
    verified_doc(fx)
    fx.write(PATH, doc(body="The kernel now runs in parallel.\n", evidence_paths="[src/engine/kernel.py]",
                       verified_by="TCK-20261101-KERNEL", verified_at="abcdef1"))
    fx.commit("edit the text")
    assert classify(fx)["reasons"] == ["doc text changed after the baseline"]


def test_editing_only_the_verified_at_line_is_not_a_text_change(fx):
    verified_doc(fx)
    fx.write(PATH, doc(evidence_paths="[src/engine/kernel.py]", verified_by="TCK-20261101-KERNEL", verified_at="abcdef2"))
    fx.commit("bump verified_at")
    assert classify(fx)["state"] == "verified_by"


def test_an_evidence_paths_edit_counts_as_a_text_change(fx):
    verified_doc(fx)
    fx.write("src/engine/other.py", "y = 1\n")
    fx.write(PATH, doc(evidence_paths="[src/engine/kernel.py, src/engine/other.py]", verified_by="TCK-20261101-KERNEL", verified_at="abcdef1"))
    fx.commit("add evidence")
    assert classify(fx)["reasons"] == ["doc text changed after the baseline"]


def test_uncommitted_evidence_changes_are_reported_when_passed_in(fx):
    verified_doc(fx)
    assert classify(fx, extra=["src/engine/kernel.py"])["reasons"] == ["evidence changed (uncommitted): src/engine/kernel.py"]


def test_the_baseline_survives_a_squash_merge(fx):
    fx.write("README.md", "hi\n")
    fx.commit("root")
    fx._git("switch", "-q", "-c", "feature")
    fx.write("src/engine/kernel.py", "def run():\n    return 1\n")
    fx.commit("code")
    fx.write(PATH, doc(evidence_paths="[src/engine/kernel.py]", verified_by="TCK-20261101-KERNEL", verified_at="abcdef1"))
    fx.commit("doc")
    fx._git("switch", "-q", "main")
    fx._git("merge", "--squash", "feature")
    squash = fx.commit("squash: kernel verified (#1)")
    assert classify(fx)["baseline"] == squash and classify(fx)["state"] == "verified_by"
    fx.write("src/engine/kernel.py", "def run():\n    return 9\n")
    fx.commit("later code change")
    assert classify(fx)["state"] == "needs-re-verify"


def test_a_moved_doc_keeps_its_baseline_through_follow(fx):
    verified_doc(fx)
    (fx.root / "docs/architecture").mkdir()
    fx._git("mv", PATH, "docs/architecture/kernel.md")
    fx.commit("move the doc")
    repo = fx.repo()
    new_path = "docs/architecture/kernel.md"
    row = doc_drift.classify(repo, new_path, (fx.root / new_path).read_text(encoding="utf-8"))
    assert row["state"] == "verified_by"


def test_removing_the_verified_by_line_makes_the_doc_unverified(fx):
    verified_doc(fx)
    fx.write(PATH, doc(evidence_paths="[src/engine/kernel.py]"))
    removal = fx.commit("drop the claim")
    assert classify(fx)["state"] == "unverified"
    assert fx.repo().baseline(PATH, "verified_by") == removal


def test_a_shallow_clone_reports_baseline_unavailable(fx, tmp_path_factory):
    verified_doc(fx)
    fx.write("README.md", "x\n")
    fx.commit("later")
    clone = tmp_path_factory.mktemp("shallow")
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{fx.root}", str(clone)], check=True, capture_output=True)
    repo = doc_drift.Repo(clone)
    repo.resolve()
    row = doc_drift.classify(repo, PATH, (clone / PATH).read_text(encoding="utf-8"))
    assert row["state"] == "baseline-unavailable"


# --- reviewed_by (pilot AC 3) -------------------------------------------------------------------------------------


def test_a_reviewed_by_doc_with_unchanged_evidence_and_text_is_quiet(fx):
    fx.write("src/engine/kernel.py", "x = 1\n")
    fx.write(PATH, doc(body="See src/engine/kernel.py for the loop.\n", reviewed_by="TCK-20261105-TRIAGE"))
    fx.commit()
    row = classify(fx)
    assert row["state"] == "reviewed_by" and not row["reasons"]
    result = doc_drift.detect(fx.repo())
    assert result["flagged"] == 0 and result["quiet_with_clean_baseline"] == 1


def test_a_reviewed_by_doc_is_flagged_again_when_its_cited_evidence_changes(fx):
    fx.write("src/engine/kernel.py", "x = 1\n")
    fx.write(PATH, doc(body="See src/engine/kernel.py for the loop.\n", reviewed_by="TCK-20261105-TRIAGE"))
    fx.commit()
    fx.write("src/engine/kernel.py", "x = 2\n")
    fx.commit()
    assert classify(fx)["state"] == "needs-re-verify"
    assert doc_drift.detect(fx.repo())["flagged"] == 1


def test_a_verified_by_doc_outranks_reviewed_by(fx):
    verified_doc(fx)
    fx.write(PATH, doc(evidence_paths="[src/engine/kernel.py]", verified_by="TCK-20261101-KERNEL", verified_at="abcdef1",
                       reviewed_by="TCK-20261105-TRIAGE"))
    fx.commit()
    assert classify(fx)["fields"] == ["evidence_paths", "reviewed_by", "verified_at", "verified_by"]
    assert classify(fx)["state"] in ("verified_by", "needs-re-verify")


# --- detection mode (J1) --------------------------------------------------------------------------------------------


def detect_fixture(fx):
    fx.write("docs/guides/old.md", doc(body="Read src/engine/kernel.py and src/engine/gone.py.\nCall `old_helper_name()` first.\n"))
    fx.write("src/engine/kernel.py", "def run():\n    return 1\n")
    fx.commit("doc and code", days=1)
    fx.write("src/engine/kernel.py", "def run():\n    return 2\n")
    fx.commit("code moves on", days=10)


def test_evidence_newer_is_ranked_by_lag_and_count(fx):
    detect_fixture(fx)
    result = doc_drift.detect(fx.repo())
    row = next(r for rows in result["ranked"].values() for r in rows if r["path"] == "docs/guides/old.md")
    newer = row["signals"]["evidence-newer"]
    assert newer["newer"] == 1 and newer["max_lag_days"] == 10.0 and newer["paths"] == ["src/engine/kernel.py"]


def test_an_unresolved_name_is_reported_as_unresolved_with_a_rename_shown(fx):
    fx.write("docs/guides/old.md", doc(body="Read src/engine/old_name.py and src/engine/gone.py and `old_helper_name()`.\n"))
    fx.write("src/engine/old_name.py", "def a():\n    pass\n")
    fx.commit()
    fx._git("mv", "src/engine/old_name.py", "src/engine/new_name.py")
    fx.commit("rename")
    result = doc_drift.detect(fx.repo())
    row = next(r for rows in result["ranked"].values() for r in rows if r["path"] == "docs/guides/old.md")
    names = {n["name"]: n["renamed_to"] for n in row["signals"]["unresolved-name"]["names"]}
    assert names["src/engine/old_name.py"] == "src/engine/new_name.py"
    assert names["src/engine/gone.py"] is None and "old_helper_name" in names


def test_a_backticked_name_that_exists_in_the_code_is_not_unresolved(fx):
    fx.write("src/engine/kernel.py", "def run_batch():\n    return 1\n")
    fx.write("docs/guides/g.md", doc(body="Call `run_batch()` to start.\n"))
    fx.commit()
    assert doc_drift.detect(fx.repo())["flagged"] == 0


def test_plan_lifecycle_uses_the_real_status_enum(fx):
    fx.write("agent-working/tickets/done/TCK-20261101-A.md", "done\n")
    fx.write("agent-working/tickets/done/TCK-20261101-B.md", "done\n")
    fx.write("agent-working/tickets/inprogress/TCK-20261101-C.md", "open\n")
    fx.write("docs/plans/live.md", doc(body="Tickets TCK-20261101-A and TCK-20261101-B.\n"))
    fx.write("docs/plans/finished_archive.md", doc(body="TCK-20261101-A.\n").replace("status: active", "status: archive"))
    fx.write("docs/plans/still_open.md", doc(body="TCK-20261101-A and TCK-20261101-C.\n"))
    fx.commit()
    assert doc_drift.FINISHED_STATUSES == {"historical", "archive"}
    flagged = {r["path"] for rows in doc_drift.detect(fx.repo())["ranked"].values() for r in rows}
    assert flagged == {"docs/plans/live.md"}


def test_excluded_classes_and_brainstorm_are_skipped(fx):
    for path in ("docs/archive/a.md", "docs/audits/b.md", "docs/brainstorm/c.md"):
        fx.write(path, doc(body="Read src/engine/gone.py.\n"))
    fx.commit()
    result = doc_drift.detect(fx.repo())
    assert result["flagged"] == 0 and result["excluded"] == {"archive": 1, "audit": 1}


def test_detect_reads_the_pin_and_leaves_the_tree_untouched(fx):
    detect_fixture(fx)
    fx.write("docs/guides/old.md", doc(body="Edited and uncommitted, no cited paths.\n"))
    before = fx._git("status", "--porcelain")
    result = doc_drift.detect(fx.repo())
    assert fx._git("status", "--porcelain") == before
    assert result["flagged"] == 1, "the uncommitted edit must not hide the flag: the run reads the pinned commit"


def test_detect_builds_times_and_renames_in_one_pass(fx, monkeypatch):
    detect_fixture(fx)
    for n in range(5):
        fx.write(f"docs/guides/extra{n}.md", doc(body=f"Read src/engine/kernel.py {n}.\n"))
    fx.commit()
    calls = []
    original = doc_drift.Repo.git

    def spy(self, *args):
        calls.append(args[0])
        return original(self, *args)

    monkeypatch.setattr(doc_drift.Repo, "git", spy)
    doc_drift.detect(fx.repo())
    assert calls.count("log") == 2, "one log for commit times, one for renames, independent of how many docs cite paths"


# --- CLI ----------------------------------------------------------------------------------------------------------------


def test_the_cli_prints_the_pin_and_exits_zero(fx, capsys):
    verified_doc(fx)
    assert doc_drift.main(["--repo-root", str(fx.root)]) == 0
    out = capsys.readouterr().out
    assert fx.repo().pin in out and "verified_by" in out


def test_a_bad_ref_prints_a_marker_error_and_still_exits_zero(fx, capsys):
    fx.write("a.txt", "x\n")
    fx.commit()
    assert doc_drift.main(["--repo-root", str(fx.root), "--ref", "no-such-ref"]) == 0
    assert capsys.readouterr().out.startswith("MARKER:")


def test_jsonl_output_has_a_summary_then_one_row_per_flagged_doc(fx, capsys):
    detect_fixture(fx)
    assert doc_drift.main(["--repo-root", str(fx.root), "--mode", "detect", "--format", "jsonl"]) == 0
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert lines[0]["mode"] == "detect" and lines[1]["path"] == "docs/guides/old.md"


def test_start_sha_counts_uncommitted_changes_as_changed_evidence(fx, capsys):
    base = verified_doc(fx)
    fx.write("src/engine/kernel.py", "def run():\n    return 3\n")  # not committed
    assert doc_drift.main(["--repo-root", str(fx.root), "--format", "advisory", "--start-sha", base]) == 0
    out = capsys.readouterr().out
    assert "needs re-verify" in out and "(uncommitted)" in out


def test_the_advisory_format_prints_nothing_when_no_doc_needs_re_verifying(fx, capsys):
    verified_doc(fx)
    assert doc_drift.main(["--repo-root", str(fx.root), "--format", "advisory"]) == 0
    assert capsys.readouterr().out.strip() == ""
