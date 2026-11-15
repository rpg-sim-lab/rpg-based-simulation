"""World farm step one: the refuse-never-delete guard and the process-safe append (T6 helper part, T8)."""

import json
import multiprocessing as mp

import pytest

from src.observability.world_farm_io import RunDirectoryInUseError, append_line, claim_run_dir, ensure_run_dir_free


def test_ensure_run_dir_free_passes_for_a_new_path(tmp_path):
    ensure_run_dir_free(str(tmp_path / "run_a_seed_1"), label="run directory")


def test_ensure_run_dir_free_refuses_an_existing_dir_and_deletes_nothing(tmp_path):
    existing = tmp_path / "run_a_seed_1"
    existing.mkdir()
    (existing / "keep.txt").write_text("mine", encoding="utf-8")
    with pytest.raises(RunDirectoryInUseError) as err:
        ensure_run_dir_free(str(existing), label="run directory")
    assert str(existing) in str(err.value)
    assert (existing / "keep.txt").read_text(encoding="utf-8") == "mine"


def test_claim_run_dir_creates_it_and_a_second_claim_is_refused_without_deleting(tmp_path):
    target = tmp_path / "data" / "runs" / "run_a_seed_1"
    claim_run_dir(str(target), label="run directory")
    assert target.is_dir()
    (target / "keep.txt").write_text("mine", encoding="utf-8")
    with pytest.raises(RunDirectoryInUseError) as err:
        claim_run_dir(str(target), label="run directory")  # the exclusive create is the claim
    assert str(target) in str(err.value)
    assert (target / "keep.txt").read_text(encoding="utf-8") == "mine"


def test_refusal_is_a_file_exists_error(tmp_path):
    assert issubclass(RunDirectoryInUseError, FileExistsError)


def test_append_line_adds_the_newline_once(tmp_path):
    path = tmp_path / "a.jsonl"
    append_line(str(path), '{"n": 1}')
    append_line(str(path), '{"n": 2}\n')
    assert path.read_text(encoding="utf-8").splitlines() == ['{"n": 1}', '{"n": 2}']


def _writer(path: str, tag: int, rows: int) -> None:
    for i in range(rows):
        # every fifth row is longer than 8 KiB, past any stdio buffer
        pad = "x" * (9000 if i % 5 == 0 else 20)
        append_line(path, json.dumps({"tag": tag, "i": i, "pad": pad}))


def test_two_processes_append_without_losing_or_splitting_a_line(tmp_path):
    path = str(tmp_path / "shared.jsonl")
    ctx = mp.get_context("spawn")
    procs = [ctx.Process(target=_writer, args=(path, tag, 500)) for tag in (1, 2)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=120)
        assert p.exitcode == 0
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]  # every line parses
    assert len(rows) == 1000
    for tag in (1, 2):
        assert sorted(r["i"] for r in rows if r["tag"] == tag) == list(range(500))
