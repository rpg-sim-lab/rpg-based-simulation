"""F3 architecture: `lodged_in` is set and cleared only through the apply path; decision code reads it and never writes it; the fingerprint and read model show it only while lodged."""
import re
from pathlib import Path

from src.replay.fingerprint import StateFingerprinter
from tests.unit.engine.lodging_kernel import INN_AT, INN_ID, hero, kernel

SRC = Path(__file__).resolve().parents[3] / "src"
# The only modules that write the lodging: the field and its update (state, updates), the patch and the apply path that commit it, the lodging module whose claim/grant/leave
# steps run inside the authoritative pipeline phases, and the phase gate that reads it.
WRITERS = {"core/state.py", "core/updates.py", "engine/patches.py", "engine/apply.py", "engine/lodging.py", "engine/pipeline_phases/occupancy.py"}
READERS_THAT_FORMAT_IT = {"replay/fingerprint.py"}   # builds a string containing the field name; writes nothing


def test_only_the_apply_path_and_the_lodging_steps_write_lodged_in():
    pattern = re.compile(r"lodged_in(_set|_clear)?\s*=(?!=)")
    offenders = []
    for path in SRC.rglob("*.py"):
        rel = path.relative_to(SRC).as_posix()
        if rel in WRITERS or rel in READERS_THAT_FORMAT_IT:
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line) and "lodged_in ==" not in line and not line.lstrip().startswith("#"):
                offenders.append(f"{rel}:{n}: {line.strip()[:100]}")
    assert not offenders, offenders


def test_the_fingerprint_changes_only_while_someone_lodges():
    k = kernel([hero(1, (9.0, 10.0))], beds=2)
    try:
        st = k._state
        before = StateFingerprinter.get_fingerprint(st)
        from dataclasses import replace
        e = st.entities[1]
        lodged = replace(st, entities={1: replace(e, navigation=replace(e.navigation, lodged_in=INN_ID))})
        assert StateFingerprinter.get_fingerprint(lodged) != before
        same = replace(st, entities={1: replace(e, navigation=replace(e.navigation, lodged_in=None))})
        assert StateFingerprinter.get_fingerprint(same) == before
    finally:
        k.shutdown()
