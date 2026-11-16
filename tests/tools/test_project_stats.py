"""TCK-20261108-PROJECT-FACTS-PAGE-GENERATED: the stats tool counts a git ref, and the page it writes is checked against the tool."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools import project_stats as pst

REPO_ROOT = Path(__file__).resolve().parents[2]


def _git(root, *args, date=None):
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = f"{date}T12:00:00"
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, env=env)


def _w(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _w(root, "src/a.py", "x = 1\n\n# c\n")
    _w(root, "src/pkg/__init__.py", "")
    _w(root, "src/pkg/m.py", "from prometheus_client import Counter, Gauge\nfrom collections import Counter as C\n"
       "a = Counter('sim_a_total', 'doc')\nb = Gauge('sim_b', 'doc')\nc = Gauge('sim_b', 'again')\nd = C('abc')\n"
       "e = GaugeMetricFamily('sim_e', 'doc')\nf = Gauge(name_var, 'doc')\n")
    _w(root, "src/other.py", "Counter('sim_not_counted_total', 'doc')\n")  # no prometheus_client in the file
    _w(root, "tests/test_a.py", "def test_one():\n    pass\n\nclass TestX:\n    def test_two(self):\n        pass\n\n"
       "import pytest\n@pytest.mark.parametrize('v', [1, 2, 3])\ndef test_param(v):\n    pass\n\ndef helper():\n    pass\n")
    _w(root, "tests/sub/test_b.py", "def test_three():\n    pass\n")
    _w(root, "tests/conftest.py", "def test_not_counted():\n    pass\n")
    _w(root, "agent-working/tickets/todos/TCK-20260101-A.md", "x")
    _w(root, "agent-working/tickets/todos/epic/TCK-20260101-B.md", "x")
    _w(root, "agent-working/tickets/todos/epic/SEQUENCE.md", "x")
    _w(root, "agent-working/tickets/done/TCK-20260101-C.md", "x")
    _w(root, "registries/session_roles.yaml", "roles:\n  - role: a\n  - role: b\n")
    _w(root, ".claude/agents/session-a.md", "x")
    _w(root, ".claude/agents/helper.md", "x")
    _w(root, ".claude/skills/one/SKILL.md", "x")
    _w(root, ".claude/skills/one/notes.md", "x")
    _w(root, ".claude/settings.json", json.dumps({"hooks": {"PreToolUse": [{"hooks": [{}, {}]}], "SessionStart": [{"hooks": [{}]}]}}))
    _w(root, "docs/parity_ledger/x.yaml", "- {id: A, status: verified, priority: P0}\n- {id: B, status: missing, priority: P1}\n- {id: C, status: verified, priority: P0}\n")
    _w(root, "docs/parity_ledger/README.md", "- not a ledger\n")
    _w(root, "codebase/structure/importlinter.toml", "[tool.importlinter]\nroot_packages = ['src']\n[[tool.importlinter.contracts]]\nname = 'a'\n[[tool.importlinter.contracts]]\nname = 'b'\n")
    _w(root, "codebase/structure/import_layers_baseline.txt", "# header\nsrc.a -> src.b\n\nsrc.c -> src.d\n")
    _w(root, "docker/grafana/provisioning/alerting/rules-x.yaml", "groups:\n  - rules: [{uid: r1}, {uid: r2}]\n  - rules: [{uid: r3}]\n")
    _w(root, "docker/grafana/provisioning/alerting/policies.yaml", "groups: []\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "first", date="2026-03-17")
    _w(root, "src/a.py", "x = 2\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "work (#1)", date="2026-05-01")
    _git(root, "commit", "-q", "--allow-empty", "-m", "also (#2)", date="2026-09-09")
    _git(root, "commit", "-q", "--allow-empty", "-m", "not a pr", date="2026-09-10")
    return root


def facts(root, ref="HEAD"):
    repo = pst.Repo(root, ref)
    return {f.label: f.value for build in pst.SECTIONS for f in build(repo).facts}


def test_each_counter_on_a_fixture_repo(tmp_path):
    f = facts(make_repo(tmp_path))
    assert f["src modules"] == "4" and f["src lines"] == "10"  # a.py 1, pkg/__init__.py 0, pkg/m.py 8, other.py 1
    assert f["test files"] == "2" and f["static test functions"] == "4"
    assert (f["tickets in todos/"], f["tickets in inprogress/"], f["tickets in done/"]) == ("2", "0", "1")
    assert f["merged PRs"] == "2 (first merge 2026-05-01, last 2026-09-09)"
    assert (f["session roles"], f["session role cards"], f["subagents"], f["skills"]) == ("2", "1", "1", "1")
    assert f["hooks"] == "3 in 2 events"
    assert f["ledger files"] == "1" and f["entries"] == "3"
    assert f["entries by status"] == "missing 1, verified 2" and f["entries by priority"] == "P0 2, P1 1"
    assert f["entries by status/priority"] == "missing/P1 1, verified/P0 2"
    assert (f["import contracts"], f["baseline edges"]) == ("2", "2")
    assert f["metric families"] == "3"  # sim_a_total, sim_b (deduped), sim_e; collections.Counter, a run-time name and the file without prometheus_client are not counted
    assert f["alert rules"] == "3"


def test_a_parametrized_test_counts_once_and_conftest_is_not_a_test_file(tmp_path):
    f = facts(make_repo(tmp_path))
    assert f["test files"] == "2" and f["static test functions"] == "4"  # test_one, TestX.test_two, test_param, test_three


def test_counts_come_from_the_ref_not_the_working_tree(tmp_path):
    root = make_repo(tmp_path)
    first = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    _w(root, "src/new.py", "y = 1\n")  # untracked: never counted
    assert facts(root)["src modules"] == facts(root, first)["src modules"]
    assert facts(root, first)["merged PRs"] == "0 (first merge -, last -)"


def test_two_runs_at_one_ref_are_byte_identical(tmp_path):
    root = make_repo(tmp_path)
    assert pst.render(pst.Repo(root, "HEAD")) == pst.render(pst.Repo(root, "HEAD"))


def test_the_page_header_carries_the_ref_and_every_count_has_a_rule(tmp_path):
    root = make_repo(tmp_path)
    page = pst.render(pst.Repo(root, "HEAD"))
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    assert f"Generated from commit `{sha}` by `tools/project_stats.py`" in page
    rows = [line for line in page.splitlines() if line.startswith("| ") and not line.startswith(("| What", "|---"))]
    assert rows and all(len(r.split("|")) == 5 and r.split("|")[3].strip() for r in rows)


def _page(root):
    (root / "docs/architecture").mkdir(parents=True, exist_ok=True)
    page = root / pst.PAGE_REL
    page.write_text(pst.render(pst.Repo(root, "HEAD")), encoding="utf-8")
    return page


def test_check_passes_on_a_fresh_page_and_fails_on_a_hand_edit(tmp_path):
    root = make_repo(tmp_path)
    page = _page(root)
    assert pst.check(root, page)[0] == 0
    page.write_text(page.read_text(encoding="utf-8").replace("| src modules | 4 |", "| src modules | 5 |"), encoding="utf-8")
    code, lines = pst.check(root, page)
    assert code == 1 and "differs" in lines[0]


def test_check_fails_when_the_rules_change_but_the_page_does_not(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    page = _page(root)
    real = pst.code_facts

    def changed(repo):
        section = real(repo)
        return pst.Section(section.title, tuple(pst.Fact(f.label, f.value, f.rule + " (new rule)") for f in section.facts))

    monkeypatch.setattr(pst, "SECTIONS", (changed, *pst.SECTIONS[1:]))
    assert pst.check(root, page)[0] == 1


def test_check_still_passes_after_head_moves_and_prints_a_note(tmp_path):
    root = make_repo(tmp_path)
    page = _page(root)
    _w(root, "src/more.py", "z = 1\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "more", date="2026-10-01")
    code, lines = pst.check(root, page)
    assert code == 0 and any(line.startswith("note: HEAD is 1 commit(s) past") for line in lines)


def test_check_reports_a_missing_page_a_missing_header_and_an_unknown_ref(tmp_path):
    root = make_repo(tmp_path)
    assert pst.check(root, root / pst.PAGE_REL)[0] == 1
    page = _page(root)
    page.write_text("# no header\n", encoding="utf-8")
    assert pst.check(root, page)[0] == 1
    page.write_text("Generated from commit `" + "0" * 40 + "` by `tools/project_stats.py`", encoding="utf-8")
    code, lines = pst.check(root, page)
    assert code == 1 and "cannot regenerate" in lines[0]


def test_the_committed_page_matches_the_tool_at_its_own_ref():
    page = REPO_ROOT / pst.PAGE_REL
    found = pst.HEADER_RE.search(page.read_text(encoding="utf-8"))
    assert found, "docs/architecture/project_facts.md has no generated header"
    have_ref = subprocess.run(["git", "cat-file", "-e", f"{found.group(1)}^{{commit}}"], cwd=REPO_ROOT, capture_output=True, check=False)
    if have_ref.returncode != 0:
        pytest.skip(f"the page's ref {found.group(1)[:9]} is not in this clone (shallow checkout)")
    result = subprocess.run([sys.executable, str(REPO_ROOT / "tools/project_stats.py"), "--check"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
