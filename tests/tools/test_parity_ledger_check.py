"""`parity_ledger_writer.py --check` and pre-push check G (TCK-20261113-PRE-PUSH-CHECKS-HAND-EDITED-PARITY-LEDGER-SHARDS)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools import parity_ledger_writer as writer
from tools.delivery import pre_push_advisory_hook as hook

WRITER = Path(writer.__file__)
GOOD = """\
- id: COMB-001
  priority: P1
  status: verified
  v2_evidence: src/x.py
  test_path: tests/test_x.py::test_a
- id: COMB-002
  priority: P1
  status: missing
  test_path: null
"""
APOSTROPHE = "- id: COMB-342\n  support_boundary: 'the hold's boundary'\n"
LEGACY = "- id: COMB-007\n  priority: P1\n  status: verified\n  v2_evidence: src/y.py\n  test_path: null\n"


def _cli(*args):
    return subprocess.run([sys.executable, str(WRITER), *args], capture_output=True, text=True, check=False)


def test_cli_names_the_file_and_line_of_a_shard_with_an_unescaped_apostrophe(tmp_path):
    shard = tmp_path / "combat_movement.yaml"
    shard.write_text(APOSTROPHE, encoding="utf-8")
    done = _cli("--check", str(shard))
    assert done.returncode != 0 and str(shard) in done.stdout and "line 2" in done.stdout
    assert shard.read_text(encoding="utf-8") == APOSTROPHE  # writes nothing


def test_cli_exits_zero_on_a_valid_shard_and_on_the_real_ledger(tmp_path):
    shard = tmp_path / "ok.yaml"
    shard.write_text(GOOD, encoding="utf-8")
    assert _cli("--check", str(shard)).returncode == 0
    ledger = sorted((Path(__file__).resolve().parents[2] / "docs" / "parity_ledger").glob("*.yaml"))
    assert ledger and _cli("--check", *map(str, ledger)).returncode == 0  # the structural check never sweeps legacy entries


def test_a_legacy_entry_with_a_null_test_path_is_not_reported_but_a_changed_one_is():
    assert writer.check_shard_text("s.yaml", LEGACY, None) == []
    assert writer.check_shard_text("s.yaml", LEGACY, LEGACY) == []  # unchanged against the base: exempt
    changed = LEGACY.replace("src/y.py", "src/z.py")
    problems = writer.check_shard_text("s.yaml", changed, LEGACY)
    assert problems == ["s.yaml: COMB-007: test_path: must be a non-null, non-empty string"]
    assert writer.check_shard_text("s.yaml", LEGACY, "")  # a new file: every entry is new
    assert writer.check_shard_text("s.yaml", "- just a string\n- id: ''\n") and writer.check_shard_text("s.yaml", "a: b\n")


def _runner(files, head_text, base_text):
    def run(cmd, timeout=30):
        if cmd[:3] == ["git", "diff", "--name-only"]:
            return hook.CommandResult(0, "\n".join(files) + "\n", "")
        if cmd[:2] == ["git", "show"]:
            ref = cmd[2].split(":", 1)[0]
            text = head_text if ref == "HEAD" else base_text
            return hook.CommandResult(0 if text is not None else 128, text or "", "")
        raise AssertionError(cmd)
    return run


def test_check_g_warns_on_a_bad_shard_in_the_diff_and_names_the_writer():
    out = hook.check_parity_ledger_shards(_runner(["docs/parity_ledger/combat_movement.yaml"], APOSTROPHE, GOOD))
    assert any("docs/parity_ledger/combat_movement.yaml: line 2" in line for line in out)
    assert any("tools/parity_ledger_writer.py" in line for line in out)


def test_check_g_is_silent_with_no_ledger_change_a_valid_one_a_legacy_one_or_an_error():
    assert hook.check_parity_ledger_shards(_runner(["tools/x.py", "docs/parity_ledger/schema.json"], APOSTROPHE, GOOD)) == []
    assert hook.check_parity_ledger_shards(_runner(["docs/parity_ledger/a.yaml"], GOOD, GOOD)) == []
    assert hook.check_parity_ledger_shards(_runner(["docs/parity_ledger/a.yaml"], LEGACY, LEGACY)) == []
    assert hook.check_parity_ledger_shards(lambda cmd, timeout=30: hook.CommandResult(128, "", "no origin/main")) == []
    assert hook.check_parity_ledger_shards(lambda cmd, timeout=30: (_ for _ in ()).throw(OSError("boom"))) == []
