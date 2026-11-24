"""The replay-digest AC2 kit (TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK): the compare script's mask, controls, step-0 pair check and verdicts, on small synthetic chunks.
No simulation runs here."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

from tools.rpg_measure import replay_digest_compare as cmp

KIT = Path(cmp.__file__).parent
KEYS = KIT / "replay_digest_wall_clock_keys.jsonl"


def _events(n: int = 3, timer: float = 1.0, world_time: int = 0):
    out = []
    for t in range(n):
        out.append({"tick": t, "system": "KERNEL", "event_type": "REFINED_UPDATE", "causal_id": None, "payload": {
            "tick": t, "world_time": world_time + t, "fingerprint": "f",
            "update": {"metric_counters": {"cooperation_phase_ms": timer + t, "phase_runs": 4}, "sub_phase_costs": {"economy": timer * 2, "locomotion": timer * 3}, "entity_updates": {"1": {"readiness_delta": 0.5}}}}})
        out.append({"tick": t, "system": "KERNEL", "event_type": "TICK_END", "causal_id": None, "payload": {"hash": "h", "scheme": "flat-sha256-v5", "digest_status": "computed"}})
    return out


def _write(path: Path, events) -> Path:
    path.write_text(json.dumps(events))
    return path


def test_the_launcher_pins_the_sha256_of_the_key_file_it_ships():
    launcher = (KIT / "replay_digest_launch.sh").read_text()
    pinned = re.search(r"KEYS_SHA256=\$\{REPLAY_DIGEST_KEYS_SHA256:-([0-9a-f]{64})\}", launcher).group(1)
    assert pinned == hashlib.sha256(KEYS.read_bytes()).hexdigest()


def test_the_launcher_is_valid_shell_and_names_step_zero_and_both_arms():
    launcher = KIT / "replay_digest_launch.sh"
    assert subprocess.run(["bash", "-n", str(launcher)]).returncode == 0
    text = launcher.read_text()
    assert "STEP 0" in text and "key list incomplete" in text and "pinned_elsewhere" in text
    assert re.search(r"NEW_SHA=\$\{REPLAY_DIGEST_NEW:-[0-9a-f]{40}\}", text) and re.search(r"BASE_SHA=\$\{REPLAY_DIGEST_BASE:-[0-9a-f]{40}\}", text)


def test_the_mask_keeps_the_keys_and_masks_exactly_the_frozen_leaves():
    mask = cmp.load_mask(KEYS)
    ev = _events(1)[0]
    assert cmp.mask_event(ev, mask) == 1 + 2
    upd = ev["payload"]["update"]
    assert upd["metric_counters"] == {"cooperation_phase_ms": None, "phase_runs": 4}
    assert upd["sub_phase_costs"] == {"economy": None, "locomotion": None}
    assert upd["entity_updates"] == {"1": {"readiness_delta": 0.5}}


def test_the_positive_control_holds_on_a_chunk_and_fails_on_a_chunk_with_no_timers(tmp_path):
    chunk = _write(tmp_path / "c.json", _events())
    assert cmp.run_control(chunk, KEYS)["ok"] is True
    bare = _write(tmp_path / "bare.json", [{"tick": 0, "event_type": "TICK_END", "payload": {"hash": "h"}}])
    assert cmp.run_control(bare, KEYS)["ok"] is False  # no timer leaf to change, no world_time: the control must not pass vacuously


def test_pair_is_ok_when_only_timers_differ_and_names_the_leaf_when_something_else_differs(tmp_path):
    a = _write(tmp_path / "a.json", _events(timer=1.0))
    b = _write(tmp_path / "b.json", _events(timer=7.0))
    assert cmp.run_pair(a, b, KEYS)["ok"] is True
    other = _events(timer=7.0)
    other[0]["payload"]["update"]["entity_updates"]["1"]["readiness_delta"] = 0.75
    c = _write(tmp_path / "c.json", other)
    res = cmp.run_pair(a, c, KEYS)
    assert res["ok"] is False and res["equal_masked"] is False
    assert any("readiness_delta" in p for p in res["differing_leaves_masked"]), res["differing_leaves_masked"]
    assert "INCOMPLETE" in res["reading"]


def test_pair_of_two_identical_chunks_is_a_meaningless_control(tmp_path):
    a = _write(tmp_path / "a.json", _events())
    res = cmp.run_pair(a, a, KEYS)
    assert res["equal_masked"] and res["equal_unmasked"] and res["ok"] is False and "meaningless" in res["reading"]


def _cell(out: Path, arm: str, world: str, events, final_hash: str = "H", rc: str = "0"):
    (out / "cells").mkdir(parents=True, exist_ok=True)
    (out / "cells" / f"{arm}_{world}.rc").write_text(rc)
    (out / "cells" / f"{arm}_{world}.json").write_text(json.dumps({"final_hash": final_hash, "final_tick": 2000}))
    d = out / "rundirs" / f"{arm}_{world}"
    d.mkdir(parents=True, exist_ok=True)
    for i in range(2):
        _write(d / f"chunk_{i:04d}.json", copy.deepcopy(events))


def _compare(out: Path, *extra):
    return cmp.main(["compare", str(out), str(KEYS), "w", *extra])


def test_compare_passes_when_only_timers_differ_and_records_raw_sha_as_information(tmp_path):
    _cell(tmp_path, "new", "w", _events(timer=1.0))
    _cell(tmp_path, "base", "w", _events(timer=9.0))
    assert _compare(tmp_path) == 0
    doc = json.loads((tmp_path / "compare.json").read_text())
    assert doc["verdict"] == "PASS" and doc["worlds"][0]["raw_chunk_sha256_equal_count"] == 0


def test_compare_fails_on_a_non_timer_difference_or_a_different_final_hash(tmp_path):
    changed = _events(timer=1.0)
    changed[0]["payload"]["world_time"] += 1
    _cell(tmp_path, "new", "w", changed)
    _cell(tmp_path, "base", "w", _events(timer=1.0))
    assert _compare(tmp_path) == 1 and json.loads((tmp_path / "compare.json").read_text())["verdict"] == "FAIL"
    other = tmp_path / "o2"
    _cell(other, "new", "w", _events(), final_hash="A")
    _cell(other, "base", "w", _events(), final_hash="B")
    assert _compare(other) == 1 and json.loads((other / "compare.json").read_text())["verdict"] == "FAIL"


@pytest.mark.parametrize("break_it", ["rc", "chunk_count", "no_chunks", "no_final_hash"])
def test_compare_is_void_on_a_bad_exit_a_chunk_count_difference_missing_chunks_or_a_missing_final_hash(tmp_path, break_it):
    _cell(tmp_path, "new", "w", _events())
    _cell(tmp_path, "base", "w", _events())
    if break_it == "rc":
        (tmp_path / "cells" / "base_w.rc").write_text("1")
    elif break_it == "chunk_count":
        (tmp_path / "rundirs" / "base_w" / "chunk_0001.json").unlink()
    elif break_it == "no_chunks":
        for c in (tmp_path / "rundirs" / "new_w").glob("chunk_*.json"):
            c.unlink()
    else:
        (tmp_path / "cells" / "new_w.json").write_text(json.dumps({"final_tick": 2000}))
    assert _compare(tmp_path) == 1
    assert json.loads((tmp_path / "compare.json").read_text())["verdict"] == "VOID"
