"""The replay-bytes comparison for the per-tick digest memo (TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK, AC2), pre-registered:

(a) the FINAL HASH: raw equal, NEW vs BASE, per world.
(b) per CHUNK: the chunk's canonical JSON (sort_keys, compact separators) with EXACTLY the wall-clock leaves of `replay_digest_wall_clock_keys.jsonl` masked to null (the key stays, so a changed key SET still differs), equal NEW vs BASE.
(c) the RAW chunk sha256s: recorded for information only (they cannot match across two processes: the wall-clock leaves differ).
(d) a POSITIVE CONTROL run before the real compare, on a copy of one chunk: a timer-only change must compare EQUAL (PASS), a non-timer change must compare DIFFERENT (FAIL), and without the mask the timer-only change must differ.
The key list is frozen in the record set before any process starts; this script reads it and never adds to it.

Step 0 (completeness of the key list): `pair` compares two BASE chunk_0000 files (two smokes of the same tree) under the mask and also unmasked; they must be EQUAL masked and DIFFERENT unmasked.

Usage: python replay_digest_compare.py control <chunk.json> <keys.json>                      exit 0 = all control expectations hold
       python replay_digest_compare.py pair <chunk_a.json> <chunk_b.json> <keys.json> [out.json]   exit 0 = equal masked AND different unmasked; 1 = key list incomplete (differing leaf paths listed) or a meaningless control
       python replay_digest_compare.py compare <OUT> <keys.json> <world>... [--context-prefix P --context-world W]
Reads OUT/cells/<arm>_<world>.json (the arm documents), OUT/cells/<arm>_<world>.rc (the exit codes), OUT/rundirs/<arm>_<world>/chunk_*.json. Writes OUT/compare.json and OUT/compare.md.
Exit 0 = PASS; 1 = FAIL (a content difference) or VOID (the evidence is not valid). VOID: an arm exit code that is not 0, a missing arm document, a missing final hash, no chunk, chunk counts that differ between the arms.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_mask(keys_file: Path) -> list:
    return json.loads(keys_file.read_text())["mask"]


def mask_event(event: dict, mask: list) -> int:
    """Set the masked leaves of one event to null (in place); returns how many leaves were masked. A path part '*' masks every key at that level."""
    count = 0
    for path in mask:
        nodes = [event]
        for part in path[:-1]:
            nodes = [n[part] for n in nodes if isinstance(n, dict) and part in n]
        last = path[-1]
        for n in nodes:
            if not isinstance(n, dict):
                continue
            for k in (list(n) if last == "*" else [last]):
                if k in n:
                    n[k] = None
                    count += 1
    return count


def canonical(events: list, mask: list) -> str:
    masked = copy.deepcopy(events)
    for e in masked:
        mask_event(e, mask)
    return json.dumps(masked, sort_keys=True, separators=(",", ":"))


def chunk_digest(path: Path, mask: list) -> str:
    return hashlib.sha256(canonical(json.loads(path.read_text()), mask).encode("utf-8")).hexdigest()


def run_control(chunk: Path, keys_file: Path) -> dict:
    mask = load_mask(keys_file)
    events = json.loads(chunk.read_text())
    timer_only, non_timer = copy.deepcopy(events), copy.deepcopy(events)
    touched_timers = 0
    for e in timer_only:
        upd = (e.get("payload") or {}).get("update") if isinstance(e.get("payload"), dict) else None
        if isinstance(upd, dict):
            mc, sp = upd.get("metric_counters"), upd.get("sub_phase_costs")
            if isinstance(mc, dict) and "cooperation_phase_ms" in mc:
                mc["cooperation_phase_ms"] = mc["cooperation_phase_ms"] * 2 + 1.0; touched_timers += 1
            if isinstance(sp, dict):
                for k in sp:
                    sp[k] = sp[k] + 1.0; touched_timers += 1
    changed = None
    for e in non_timer:
        if isinstance(e.get("payload"), dict) and isinstance(e["payload"].get("world_time"), int):
            e["payload"]["world_time"] += 1; changed = "payload.world_time (first event with one)"; break
    original = canonical(events, mask)
    result = {
        "chunk": str(chunk), "chunk_sha256": sha256(chunk), "timer_leaves_changed": touched_timers, "non_timer_change": changed,
        "same_chunk_equal": canonical(events, mask) == original,
        "timer_only_change_equal_masked": canonical(timer_only, mask) == original,
        "timer_only_change_equal_unmasked": canonical(timer_only, []) == canonical(events, []),
        "non_timer_change_equal_masked": canonical(non_timer, mask) == original,
    }
    result["ok"] = bool(touched_timers > 0 and changed and result["same_chunk_equal"] and result["timer_only_change_equal_masked"]
                        and not result["timer_only_change_equal_unmasked"] and not result["non_timer_change_equal_masked"])
    result["reading"] = ("timer-only change compares EQUAL (PASS), non-timer change compares DIFFERENT (FAIL), the unmasked timer change differs (the mask is what makes it PASS)"
                         if result["ok"] else "CONTROL FAILED: do not trust a compare made with this mask")
    return result


def differing_leaves(a, b, mask: list, path: str = "", out: list | None = None, limit: int = 60) -> list:
    """The generalised paths (list indexes as []) of leaves that differ between two masked event lists, at most `limit`."""
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append(f"{path}.{k} (present in only one)")
            else:
                differing_leaves(a[k], b[k], mask, f"{path}.{k}", out, limit)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}[] (length {len(a)} vs {len(b)})")
        for x, y in zip(a, b):
            differing_leaves(x, y, mask, f"{path}[]", out, limit)
    elif a != b:
        out.append(path)
    return out


def run_pair(chunk_a: Path, chunk_b: Path, keys_file: Path) -> dict:
    mask = load_mask(keys_file)
    ea, eb = json.loads(chunk_a.read_text()), json.loads(chunk_b.read_text())
    masked_a, masked_b = copy.deepcopy(ea), copy.deepcopy(eb)
    for e in masked_a:
        mask_event(e, mask)
    for e in masked_b:
        mask_event(e, mask)
    equal_masked = json.dumps(masked_a, sort_keys=True, separators=(",", ":")) == json.dumps(masked_b, sort_keys=True, separators=(",", ":"))
    equal_unmasked = json.dumps(ea, sort_keys=True, separators=(",", ":")) == json.dumps(eb, sort_keys=True, separators=(",", ":"))
    result = {"chunk_a": str(chunk_a), "chunk_b": str(chunk_b), "chunk_a_sha256": sha256(chunk_a), "chunk_b_sha256": sha256(chunk_b), "equal_masked": equal_masked, "equal_unmasked": equal_unmasked,
              "differing_leaves_masked": [] if equal_masked else differing_leaves(masked_a, masked_b, mask),
              "differing_leaves_unmasked_sample": [] if equal_unmasked else differing_leaves(ea, eb, [], limit=8)}
    result["ok"] = equal_masked and not equal_unmasked
    result["reading"] = ("the two chunks are equal under the frozen mask and differ without it: the key list is complete for this chunk" if result["ok"]
                         else ("KEY LIST INCOMPLETE: the masked chunks still differ (VOID)" if not equal_masked else "the unmasked chunks are equal: the control is meaningless (VOID)"))
    return result


def arm_facts(out: Path, arm: str, world: str, mask: list) -> dict:
    name = f"{arm}_{world}"
    facts = {"arm": arm, "world": world, "void": [], "doc": None, "raw_sha256": {}, "masked_sha256": {}}
    rc_file, doc_file = out / "cells" / f"{name}.rc", out / "cells" / f"{name}.json"
    rc = rc_file.read_text().strip() if rc_file.exists() else None
    if rc != "0":
        facts["void"].append(f"{name}: exit code {rc!r}")
    if doc_file.exists():
        facts["doc"] = json.loads(doc_file.read_text())
        if not facts["doc"].get("final_hash"):
            facts["void"].append(f"{name}: no final hash")
    else:
        facts["void"].append(f"{name}: no arm document")
    run_dir = out / "rundirs" / name
    chunks = sorted(run_dir.glob("chunk_*.json")) if run_dir.is_dir() else []
    if not chunks:
        facts["void"].append(f"{name}: no chunk_*.json in {run_dir}")
    for c in chunks:
        facts["raw_sha256"][c.name] = sha256(c)
        facts["masked_sha256"][c.name] = chunk_digest(c, mask)
    return facts


def compare_world(out: Path, world: str, mask: list) -> dict:
    new, base = arm_facts(out, "new", world, mask), arm_facts(out, "base", world, mask)
    void = new["void"] + base["void"]
    if new["masked_sha256"] and base["masked_sha256"] and len(new["masked_sha256"]) != len(base["masked_sha256"]):
        void.append(f"{world}: chunk counts differ (new {len(new['masked_sha256'])}, base {len(base['masked_sha256'])})")
    names = sorted(set(new["masked_sha256"]) | set(base["masked_sha256"]))
    differing = [n for n in names if new["masked_sha256"].get(n) != base["masked_sha256"].get(n)]
    raw_equal = sum(1 for n in names if new["raw_sha256"].get(n) == base["raw_sha256"].get(n))
    nh, bh = (new["doc"] or {}).get("final_hash"), (base["doc"] or {}).get("final_hash")
    return {"world": world, "void": void, "new_chunks": len(new["masked_sha256"]), "base_chunks": len(base["masked_sha256"]), "differing_masked_chunks": differing,
            "raw_chunk_sha256_equal_count": raw_equal, "new_final_hash": nh, "base_final_hash": bh, "final_hash_equal": bool(nh) and nh == bh,
            "new_final_tick": (new["doc"] or {}).get("final_tick"), "base_final_tick": (base["doc"] or {}).get("final_tick"),
            "new_masked_sha256": new["masked_sha256"], "base_masked_sha256": base["masked_sha256"], "new_raw_sha256": new["raw_sha256"], "base_raw_sha256": base["raw_sha256"],
            "new_memo": (new["doc"] or {}).get("memo")}


def main_compare(args: list) -> int:
    ctx_prefix, ctx_world = None, "frontier_living_world"
    while "--context-prefix" in args:
        i = args.index("--context-prefix"); ctx_prefix = args[i + 1]; del args[i:i + 2]
    while "--context-world" in args:
        i = args.index("--context-world"); ctx_world = args[i + 1]; del args[i:i + 2]
    out, keys_file, worlds = Path(args[0]), Path(args[1]), args[2:]
    mask = load_mask(keys_file)
    results = [compare_world(out, w, mask) for w in worlds]
    void = [v for r in results for v in r["void"]]
    passed = not void and all(r["final_hash_equal"] and not r["differing_masked_chunks"] and r["new_chunks"] == r["base_chunks"] > 0 for r in results)
    context = None
    if ctx_prefix:
        base_hash = next((r["base_final_hash"] for r in results if r["world"] == ctx_world), None)
        context = {"reference_prefix": ctx_prefix, "world": ctx_world, "base_final_hash": base_hash, "base_matches_reference": bool(base_hash) and base_hash.startswith(ctx_prefix),
                   "note": "context only: the reference was recorded at 613a8365bcd1; equality is not required if main changed simulation behaviour since"}
    verdict = "VOID" if void else ("PASS" if passed else "FAIL")
    doc = {"verdict": verdict, "void_reasons": void, "keys_file": str(keys_file), "keys_file_sha256": sha256(keys_file), "mask": mask, "worlds": results, "context": context}
    (out / "compare.json").write_text(json.dumps(doc, indent=1, sort_keys=True))
    lines = [f"# Replay bytes, NEW vs BASE: {verdict}", "", f"Pre-registered: (a) final hash raw equal; (b) per chunk the canonical JSON with the frozen wall-clock leaves masked equal ({keys_file.name} sha256 {doc['keys_file_sha256'][:16]}); (c) raw chunk sha256 information only.", ""]
    for r in results:
        lines.append(f"- {r['world']}: final hash equal={r['final_hash_equal']} (new {r['new_final_hash']}, base {r['base_final_hash']}); chunks new {r['new_chunks']} / base {r['base_chunks']}; "
                     f"differing masked chunks: {r['differing_masked_chunks'] or 'none'}; raw-sha256-equal chunks (information only): {r['raw_chunk_sha256_equal_count']} of {r['new_chunks']}; final ticks {r['new_final_tick']}/{r['base_final_tick']}")
    for v in void:
        lines.append(f"- VOID: {v}")
    if context:
        lines.append(f"- context ({context['world']}): BASE final hash {context['base_final_hash']} starts with {context['reference_prefix']}: {context['base_matches_reference']} (context only)")
    (out / "compare.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if verdict == "PASS" else 1


def main(argv: list) -> int:
    if len(argv) >= 3 and argv[0] == "control":
        result = run_control(Path(argv[1]), Path(argv[2]))
        print(json.dumps(result, indent=1, sort_keys=True))
        return 0 if result["ok"] else 1
    if len(argv) >= 4 and argv[0] == "pair":
        result = run_pair(Path(argv[1]), Path(argv[2]), Path(argv[3]))
        if len(argv) >= 5:
            Path(argv[4]).write_text(json.dumps(result, indent=1, sort_keys=True))
        print(json.dumps(result, indent=1, sort_keys=True))
        return 0 if result["ok"] else 1
    if len(argv) >= 4 and argv[0] == "compare":
        return main_compare(argv[1:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
