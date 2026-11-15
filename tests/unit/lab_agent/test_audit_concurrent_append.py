"""World farm step one (T8): two processes logging to one lab session never split or lose an audit line."""

import json
import multiprocessing as mp
from pathlib import Path

from src.lab.audit import LabAuditTrail
from src.lab.session import LabSessionStore


def _log(workspace: str, tag: int, rows: int) -> None:
    trail = LabAuditTrail(workspace_root=Path(workspace))
    for i in range(rows):
        pad = "x" * (9000 if i % 5 == 0 else 20)  # every fifth row is longer than 8 KiB
        trail.log_event("session_farm", "tick", {"tag": tag, "i": i, "pad": pad})


def test_two_processes_share_one_audit_log_without_splitting_a_line(tmp_path: Path):
    (tmp_path / "data" / "lab_sessions").mkdir(parents=True)
    LabSessionStore(tmp_path / "data" / "lab_sessions").create_session("session_farm")
    ctx = mp.get_context("spawn")
    procs = [ctx.Process(target=_log, args=(str(tmp_path), tag, 200)) for tag in (1, 2)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=120)
        assert p.exitcode == 0
    audit_file = tmp_path / "data" / "lab_sessions" / "session_farm" / "audit_log.jsonl"
    with open(audit_file, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]  # every line parses
    assert len(rows) == 400
    for tag in (1, 2):
        assert sorted(r["details"]["i"] for r in rows if r["details"]["tag"] == tag) == list(range(200))
