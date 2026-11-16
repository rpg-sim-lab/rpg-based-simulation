"""Wrapper around the tree's own tools/rpg_measure/arm_child.py for the M1-base record.

Only behaviour change: arm_child's final ``shutil.rmtree(run_dir, ignore_errors=True)`` MOVES run_dir to
/mnt/data2/rpg-measure/m1base/events/$M1BASE_EVENTS_NAME/ instead (refusing if the target exists). The move happens after the
run and after the JSON is written, so hashes are unaffected.
Env: M1BASE_EVENTS_NAME (<world>_s<seed>[_repeat]), M1BASE_TOOL_ROOT. Usage (cwd = the extracted arm tree): python keep_events_child.py <world> <seed> <ticks> <out.json>
"""
import importlib.util
import os
import shutil
import sys
import types
from pathlib import Path

EVENTS_ROOT = Path("/mnt/data2/rpg-measure/m1base/events")


def main(argv):
    # arm_child is loaded from the TOOL checkout, exactly as paired.run_one runs it (paired.CHILD = tool checkout's arm_child.py, whose hash keys the cache);
    # cwd and sys.path[0] are the extracted arm tree, as in run_one.
    tool = Path(os.environ.get("M1BASE_TOOL_ROOT", "/mnt/data/Working/rpg-based-simulation"))
    path = tool / "tools" / "rpg_measure" / "arm_child.py"
    if not path.is_file():
        raise SystemExit(f"STOP: {path} missing")
    sys.path.insert(0, str(Path.cwd()))
    spec = importlib.util.spec_from_file_location("arm_child", path)
    arm_child = importlib.util.module_from_spec(spec)
    sys.modules["arm_child"] = arm_child
    spec.loader.exec_module(arm_child)
    target = EVENTS_ROOT / os.environ["M1BASE_EVENTS_NAME"]

    def keep(run_dir, ignore_errors=False):
        if target.exists():
            raise SystemExit(f"STOP: events target exists, refusing to overwrite: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(run_dir), str(target))

    # a stand-in module object: arm_child's own `shutil` name only, the real shutil module is untouched
    arm_child.shutil = types.SimpleNamespace(rmtree=keep)
    return arm_child.main(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
