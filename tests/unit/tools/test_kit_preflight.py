"""TCK-20261118-A-DIAGNOSTIC-KIT-PREFLIGHT-CHECKS-EACH-KIT-ON-BOTH-FROZEN-TREES-BEFORE-ITS-RUN: the preflight fails on the kit faults that reached S9 records, and passes a clean kit.

Synthetic trees and kits in tmp_path (no frozen tree, no host load): two tiny trees with a `fakesrc` package, one probe script per fault class.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parents[3] / "tools" / "rpg_measure" / "kit_preflight.py"
_spec = importlib.util.spec_from_file_location("kit_preflight_under_test", _PATH)
kp = importlib.util.module_from_spec(_spec)
sys.modules["kit_preflight_under_test"] = kp
_spec.loader.exec_module(kp)

WORDS = r"_spy|_probe"

CLEAN_PROBE = '''
import json, os, sys
sys.path.insert(0, os.getcwd())
import fakesrc


def main():
    world, seed, ticks, out = sys.argv[1:5]
    json.dump({"rows": [{"failure_reason": "blocked", "n": 1}, {"failure_reason": None, "n": 2}], "hooks": {"wrap": 3}}, open(out, "w"))
    print("PROBE OK")


if __name__ == "__main__":
    main()
'''
# fault: field 6 read from an attribute that does not exist, so it is None on every row (the d4a5e6a8 navigation.failure_reason fault)
DEAD_FIELD_PROBE = CLEAN_PROBE.replace('"failure_reason": "blocked"', '"failure_reason": None')
# fault: no sys.path fix, so under `python -I` (PYTHONPATH ignored) the import of the tree's package fails
NO_PATH_FIX_PROBE = CLEAN_PROBE.replace("sys.path.insert(0, os.getcwd())\n", "")


def _tree(root: Path, name: str) -> Path:
    tree = root / name
    (tree / "fakesrc").mkdir(parents=True, exist_ok=True)
    (tree / "fakesrc" / "__init__.py").write_text("")
    (tree / "fakesrc" / "gate.py").write_text("class Gate:\n    def can_perceive(self, context, a, b=None):\n        return True\n")
    return tree


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _kit(root: Path, probe_src: str = CLEAN_PROBE, probe_name: str = "step_probe.py", proc_extra: dict | None = None, files_extra: list | None = None):
    kit = root / "kit"
    kit.mkdir(exist_ok=True)
    (kit / probe_name).write_text(probe_src)
    proc = {"name": "probe", "entry": ["{python}", "-I", "{file:" + probe_name + "}", "{world}", "{seed}", "{ticks}", "{out}"],
            "import_files": [probe_name], "fixture": {"world": "w", "seed": 42, "ticks": 10},
            "output": {"fields": [{"path": "rows[*].failure_reason"}, {"path": "rows[*].n"}]},
            "guards": {"ok_regex": "PROBE OK", "bad_regex": "Traceback"}, "hooks": [{"name": "wrap", "count_path": "hooks.wrap"}]}
    proc.update(proc_extra or {})
    manifest = {"kit": "synthetic", "version": 1, "files": [{"path": probe_name, "sha256": _sha(kit / probe_name)}] + (files_extra or []), "processes": [proc]}
    path = kit / "manifest.json"
    path.write_text(json.dumps(manifest))
    return path, manifest


def _run(root: Path, manifest_path: Path):
    trees = [_tree(root, "tree_a"), _tree(root, "tree_b")]
    return kp.preflight(manifest_path, trees, sys.executable, 5, words=WORDS)[0]


def _failed(rows):
    return {(c, s) for c, s, st, _ in rows if st == kp.FAIL}


def _checks_failed(rows):
    return {c for c, _, st, _ in rows if st == kp.FAIL}


def test_a_clean_kit_passes_on_both_trees(tmp_path):
    rows = _run(tmp_path, _kit(tmp_path)[0])
    assert _failed(rows) == set(), rows
    scopes = {s for c, s, st, _ in rows if c == "c fixture run"}
    assert scopes == {"probe@tree_a", "probe@tree_b"}


def test_a_field_that_is_constant_none_fails_check_d(tmp_path):
    rows = _run(tmp_path, _kit(tmp_path, DEAD_FIELD_PROBE)[0])
    assert _checks_failed(rows) == {"d field liveness"}
    assert any("rows[*].failure_reason" in s and "constant null" in d for c, s, st, d in rows if st == kp.FAIL)


def test_a_probe_with_no_sys_path_fix_fails_the_import_under_dash_I(tmp_path):
    rows = _run(tmp_path, _kit(tmp_path, NO_PATH_FIX_PROBE)[0])
    failed = _checks_failed(rows)
    assert "b import" in failed and "c fixture run" in failed


def test_a_declared_may_be_constant_field_passes_and_is_listed(tmp_path):
    path, _ = _kit(tmp_path, DEAD_FIELD_PROBE, proc_extra={"output": {"fields": [{"path": "rows[*].failure_reason", "may_be_constant": True}, {"path": "rows[*].n"}]}})
    rows = _run(tmp_path, path)
    assert _failed(rows) == set()
    assert any("DECLARED may_be_constant" in d for _, _, _, d in rows)


def test_a_missing_field_fails(tmp_path):
    path, _ = _kit(tmp_path, proc_extra={"output": {"fields": [{"path": "rows[*].no_such_field"}]}})
    assert "d field liveness" in _checks_failed(_run(tmp_path, path))


def test_a_sha_mismatch_fails_check_a(tmp_path):
    path, manifest = _kit(tmp_path)
    manifest["files"][0]["sha256"] = "0" * 64
    path.write_text(json.dumps(manifest))
    assert "a files" in _checks_failed(_run(tmp_path, path))


def test_a_nonzero_rc_a_bad_line_an_error_log_and_an_unhit_hook_each_fail(tmp_path):
    crash = CLEAN_PROBE.replace('print("PROBE OK")', 'print("PROBE OK"); sys.exit(3)')
    assert "c fixture run" in _checks_failed(_run(tmp_path, _kit(tmp_path, crash)[0]))
    bad = CLEAN_PROBE.replace('print("PROBE OK")', 'print("PROBE OK"); print("Traceback (swallowed)")')
    assert "e guards" in _checks_failed(_run(tmp_path, _kit(tmp_path, bad)[0]))
    logged = CLEAN_PROBE.replace('print("PROBE OK")', 'print("PROBE OK"); print("ERROR:root:boom", file=sys.stderr)')
    rows = _run(tmp_path, _kit(tmp_path, logged)[0])
    assert any(c == "e guards" and "ERROR+" in s and st == kp.FAIL for c, s, st, _ in rows)
    dead_hook = CLEAN_PROBE.replace('"hooks": {"wrap": 3}', '"hooks": {"wrap": 0}')
    rows = _run(tmp_path, _kit(tmp_path, dead_hook)[0])
    assert any("hook wrap" in s and st == kp.FAIL for _, s, st, _ in rows)


# ---- (f) runner references -----------------------------------------------------------------------------------------------------------------

def test_a_runner_that_calls_a_python_file_with_no_manifest_sha_fails_check_f(tmp_path):
    kit = tmp_path / "kit"
    kit.mkdir()
    (kit / "run.sh").write_text("#!/bin/bash\n# calls the old one in a comment: blocker_spy_v2.py\nPYTHONPATH=$T python $D/blocker_spy.py $W 42 5000\n")
    path, manifest = _kit(tmp_path, files_extra=[{"path": "run.sh", "sha256": _sha(kit / "run.sh"), "role": "runner"}])
    rows = _run(tmp_path, path)
    assert any(c == "f runner refs" and st == kp.FAIL and "blocker_spy.py" in d and "blocker_spy_v2.py" not in d for c, _, st, d in rows)


def test_a_runner_naming_only_manifest_files_passes_check_f(tmp_path):
    kit = tmp_path / "kit"
    kit.mkdir()
    (kit / "run.sh").write_text("python $D/step_probe.py $W 42 5000 out.json\n")
    path, _ = _kit(tmp_path, files_extra=[{"path": "run.sh", "sha256": _sha(kit / "run.sh"), "role": "runner"}])
    assert not any(c == "f runner refs" and st == kp.FAIL for c, _, st, _ in _run(tmp_path, path))


# ---- (g) wrapper signatures ----------------------------------------------------------------------------------------------------------------

def _wrapper_kit(tmp_path, wrapper_src):
    kit = tmp_path / "kit"
    kit.mkdir(exist_ok=True)
    (kit / "wrap_spy.py").write_text(wrapper_src)
    return _kit(tmp_path, files_extra=[{"path": "wrap_spy.py", "sha256": _sha(kit / "wrap_spy.py")}],
                proc_extra={"wraps": [{"target": "fakesrc.gate:Gate.can_perceive", "wrapper": "wrap_spy.py:spy"}]})[0]


def test_a_wrapper_with_ctx_for_context_fails_check_g(tmp_path):
    rows = _run(tmp_path, _wrapper_kit(tmp_path, "def spy(self, ctx, a, b=None):\n    return True\n"))
    assert any(c == "g wrapper signature" and st == kp.FAIL and "context" in d for c, _, st, d in rows)


def test_a_wrapper_with_matching_names_or_star_args_passes_check_g(tmp_path):
    assert "g wrapper signature" not in _checks_failed(_run(tmp_path, _wrapper_kit(tmp_path, "def spy(self, context, a, b=None):\n    return True\n")))
    assert "g wrapper signature" not in _checks_failed(_run(tmp_path, _wrapper_kit(tmp_path, "def spy(self, *args, **kwargs):\n    return True\n")))


def test_signature_problems_pure_rules():
    target = [["self", "POSITIONAL_OR_KEYWORD"], ["context", "POSITIONAL_OR_KEYWORD"], ["a", "POSITIONAL_OR_KEYWORD"]]
    assert kp.signature_problems(target, [["self", "POSITIONAL_OR_KEYWORD"], ["ctx", "POSITIONAL_OR_KEYWORD"], ["a", "POSITIONAL_OR_KEYWORD"]])
    assert kp.signature_problems(target, [["args", "VAR_POSITIONAL"], ["kwargs", "VAR_KEYWORD"]]) == []
    assert kp.signature_problems(target, [["args", "VAR_POSITIONAL"]])  # **kwargs missing: `context=` by keyword is refused
    assert kp.signature_problems([["x", "POSITIONAL_OR_KEYWORD"]], [["x", "KEYWORD_ONLY"]])  # kind differs


# ---- (h) gate visibility -------------------------------------------------------------------------------------------------------------------

def test_a_heavy_kit_file_the_shared_gate_cannot_see_fails_check_h(tmp_path):
    path, _ = _kit(tmp_path, probe_name="unprofiled_reader.py", proc_extra={})
    assert any(c == "h gate visibility" and st == kp.FAIL for c, _, st, _ in _run(tmp_path, path))


def test_a_heavy_word_in_the_name_passes_check_h_and_the_pattern_is_read_from_the_gate_file(tmp_path):
    gate = tmp_path / "busy_gate.sh"
    gate.write_text("RPG_HEAVY_WORDS='arm_child|_spy|_probe|pytest'\n")
    assert kp.heavy_words(str(gate), None) == "arm_child|_spy|_probe|pytest"
    assert kp.heavy_words(str(tmp_path / "missing.sh"), None) is None
    rows = kp.check_gate_visibility(_kit(tmp_path)[1], kp.heavy_words(str(gate), None))
    assert [st for _, _, st, _ in rows] == [kp.PASS]
    assert kp.check_gate_visibility(_kit(tmp_path)[1], None)[0][2] == kp.FAIL


def test_the_cli_exits_nonzero_on_a_fault_and_prints_the_table(tmp_path, capsys):
    path, _ = _kit(tmp_path, DEAD_FIELD_PROBE)
    trees = [str(_tree(tmp_path, "tree_a")), str(_tree(tmp_path, "tree_b"))]
    rc = kp.main([str(path), "--tree", trees[0], "--tree", trees[1], "--python", sys.executable, "--heavy-words", WORDS, "--ticks", "5"])
    out = capsys.readouterr().out
    assert rc == 1 and "KIT PREFLIGHT FAIL" in out and "evidence label: executed" in out and "manifest sha256" in out and "env digest" in out


# ---- real kits are scripts: top-level run, JSONL output, a spy defined inside the script, kit files named <name>.py_<sha>_approved ----------------------------------------

SCRIPT_PROBE = '''
import json, os, sys
sys.path.insert(0, os.getcwd())
import fakesrc
world, seed, ticks, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
def spy(self, source_entity, target_signals, context=None, *args, **kwargs):
    return True
with open(out, "w") as fh:
    for t in range(ticks):
        fh.write(json.dumps({"tick": t, "entities": {"1": ["human", t % 3], "2": ["wolf", "None"]}}) + "\\n")
print("PROBE OK")
'''


def test_a_script_style_probe_with_jsonl_output_passes_and_its_nested_field_is_read(tmp_path):
    path, manifest = _kit(tmp_path, SCRIPT_PROBE, probe_name="step_probe.py_deadbeef_approved",
                          proc_extra={"output": {"format": "jsonl", "fields": [{"path": "[*].entities[*][0]"}, {"path": "[*].entities[*][1]"}]}, "hooks": []})
    assert _failed(_run(tmp_path, path)) == set()


def test_a_jsonl_field_that_is_the_string_none_on_every_row_fails_when_the_manifest_lists_it_as_a_default(tmp_path):
    path, _ = _kit(tmp_path, SCRIPT_PROBE, probe_name="step_probe.py_deadbeef_approved",
                   proc_extra={"output": {"format": "jsonl", "fields": [{"path": "[*].entities[2][1]", "defaults": [None, "None"]}]}, "hooks": []})
    rows = _run(tmp_path, path)
    assert any(c == "d field liveness" and st == kp.FAIL for c, _, st, _ in rows)


def test_a_wrapper_defined_inside_a_script_is_read_from_its_source(tmp_path):
    kit = tmp_path / "kit"
    path, _ = _kit(tmp_path, SCRIPT_PROBE, probe_name="step_probe.py",
                   proc_extra={"output": {"format": "jsonl", "fields": []}, "hooks": [], "wraps": [{"target": "fakesrc.gate:Gate.can_perceive", "wrapper": "step_probe.py:spy"}]})
    rows = _run(tmp_path, path)
    assert any(c == "g wrapper signature" and st == kp.FAIL and "context" in d for c, _, st, d in rows) is False
    assert not any(c == "g wrapper signature" and st == kp.FAIL for c, _, st, _ in rows)
