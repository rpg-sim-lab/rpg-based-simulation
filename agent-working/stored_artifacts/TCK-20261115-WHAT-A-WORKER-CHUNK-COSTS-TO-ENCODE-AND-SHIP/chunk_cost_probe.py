"""Chunk cost probe (TCK-20261115-WHAT-A-WORKER-CHUNK-COSTS-TO-ENCODE-AND-SHIP, cheap form).

Drives the pinned kernel (``rpg_gate_run.build_kernel``: pinned governor, LocalSequentialExecutor, audit mode). On each measured
tick, after the real executor has produced its results, a side path builds what ``ConcurrentExecutionAdapter.execute`` would hand
a worker manager (the real ``execute`` method on its own adapter instance, whose manager captures the packets instead of running
them), chunks them with the worker manager's formulas, and times per chunk:

  pickle encode -> decode -> compute (``_process_chunk_wrapper`` on the decoded copy) -> result encode -> decode -> validate.

The side path reads state only and its results are discarded. Positive control: ``--no-probe`` runs the same kernel without the
side path; both print ``final_hash`` and the two must match. Lives in staging only; no src/ edit.
"""

from __future__ import annotations

import argparse
import copyreg
import dataclasses
import gc
import json
import os
import pickle
import statistics
import sys
import time
from types import MappingProxyType
from typing import Any, Dict, List

PRIVATE_CACHE_FIELDS = ("_region_index_cache", "_regions_global_bounds", "_building_region_map_cache",
                        "_node_map_cache", "_corpse_map_cache", "_ground_item_map_cache")


def thread_chunk_size(n: int, workers: int) -> int:
    """worker_manager.execute_batch, thread path (today's default)."""
    return max(1, min(50, n // (workers * 2 if workers > 0 else 1)))


def process_chunk_size(n: int, workers: int) -> int:
    """worker_manager.execute_batch, process path (mega-chunks)."""
    return max(1, n // workers)


def chunks_of(packets: List[Any], size: int) -> List[List[Any]]:
    return [packets[i:i + size] for i in range(0, len(packets), size)]


class _CapturingManager:
    """Stands in for WorkerManager inside the probe's own adapter: records the packets and the time they reached it."""

    def __init__(self) -> None:
        self.packets: List[Any] = []
        self.reached_ns = 0

    def execute_batch(self, packets, worker_fn, force_local=False, concurrency_limit=1.0):
        self.reached_ns = time.perf_counter_ns()
        self.packets = list(packets)
        return []


def _pickle_check(obj: Any) -> str:
    """'' when ``obj`` pickles as-is, else the error text."""
    try:
        pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        return ""
    except Exception as exc:  # noqa: BLE001 - the probe reports what fails
        return f"{type(exc).__name__}: {exc}"


class ProbeExecutor:
    """Wraps the pinned kernel's executor; the real results are what the kernel gets."""

    def __init__(self, inner, workers: int, chunking: str, per_packet_every: int, warmup: int) -> None:
        from src.engine.executor import ConcurrentExecutionAdapter

        self._inner = inner
        self._capture = _CapturingManager()
        self._adapter = ConcurrentExecutionAdapter(self._capture)  # its own freeze cache, never the kernel's
        self._workers = workers
        self._chunking = chunking
        self._per_packet_every = per_packet_every
        self._warmup = warmup
        self.calls = 0
        self.ticks: List[Dict[str, Any]] = []
        self.unpicklable: Dict[str, str] = {}

    def set_concurrency_limit(self, limit: float) -> None:
        self._inner.set_concurrency_limit(limit)

    def execute(self, work_items, state, rng, profile):
        t0 = time.perf_counter_ns()
        results = self._inner.execute(work_items, state, rng, profile)
        inner_ns = time.perf_counter_ns() - t0
        self.calls += 1
        if self.calls > self._warmup:
            self.ticks.append(self._side_path(work_items, state, rng, profile, inner_ns))
        return results

    def _side_path(self, work_items, state, rng, profile, inner_ns: int) -> Dict[str, Any]:
        from src.core.protocol_validator import ProtocolValidator
        from src.engine.worker_logic import default_simulation_worker
        from src.engine.worker_manager import _process_chunk_wrapper

        t0 = time.perf_counter_ns()
        self._adapter.execute(work_items, state, rng, profile)  # packet build + validate_packet_batch, then the capture
        build_ns = self._capture.reached_ns - t0
        packets = self._capture.packets
        size = (thread_chunk_size if self._chunking == "thread" else process_chunk_size)(len(packets), self._workers)
        tick_doc: Dict[str, Any] = {"tick": state.tick, "work_items": len(work_items), "packets": len(packets),
                                    "chunk_size": size, "sequential_collection_ms": inner_ns / 1e6,
                                    "packet_build_ms": build_ns / 1e6, "chunks": []}
        do_per_packet = self._per_packet_every > 0 and (len(self.ticks) % self._per_packet_every == 0)
        for chunk in chunks_of(packets, size):
            gc.disable()
            try:
                e0 = time.perf_counter_ns(); blob = pickle.dumps(chunk, protocol=pickle.HIGHEST_PROTOCOL); e1 = time.perf_counter_ns()
                decoded = pickle.loads(blob); e2 = time.perf_counter_ns()
                res = _process_chunk_wrapper(decoded, default_simulation_worker); e3 = time.perf_counter_ns()
                rblob = pickle.dumps(res, protocol=pickle.HIGHEST_PROTOCOL); e4 = time.perf_counter_ns()
                rdec = pickle.loads(rblob); e5 = time.perf_counter_ns()
                ProtocolValidator.validate_result_batch(rdec, {p.packet_id: p for p in chunk}); e6 = time.perf_counter_ns()
            finally:
                gc.enable()
            c: Dict[str, Any] = {"packets": len(chunk), "request_bytes": len(blob), "encode_ms": (e1 - e0) / 1e6,
                                 "decode_ms": (e2 - e1) / 1e6, "compute_ms": (e3 - e2) / 1e6, "response_bytes": len(rblob),
                                 "result_encode_ms": (e4 - e3) / 1e6, "result_decode_ms": (e5 - e4) / 1e6,
                                 "validate_ms": (e6 - e5) / 1e6}
            stripped = [dataclasses.replace(p, **{f: None for f in PRIVATE_CACHE_FIELDS}) for p in chunk]
            c["request_bytes_without_private_caches"] = len(pickle.dumps(stripped, protocol=pickle.HIGHEST_PROTOCOL))
            if do_per_packet:
                c["request_bytes_per_packet_sum"] = sum(len(pickle.dumps(p, protocol=pickle.HIGHEST_PROTOCOL)) for p in chunk)
            tick_doc["chunks"].append(c)
            del decoded, res, rdec, blob, rblob, stripped
        return tick_doc


def _register_reducers(mode: str) -> List[str]:
    """``none``: pickle as the code stands. ``mappingproxy``: a process-local reducer that ships a MappingProxyType as a dict
    (the receiving side gets a plain dict; a codec would re-wrap it). The reducer is the probe's, named in the result."""
    if mode == "mappingproxy":
        copyreg.pickle(MappingProxyType, lambda m: (dict, (dict(m),)))
        return ["types.MappingProxyType -> dict"]
    return []


def _summary(values: List[float]) -> Dict[str, float]:
    if not values:
        return {}
    s = sorted(values)
    return {"n": len(s), "median": statistics.median(s), "p90": s[min(len(s) - 1, int(0.9 * len(s)))],
            "max": s[-1], "sum": sum(s)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Chunk cost probe (cheap form).")
    ap.add_argument("--world", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--warmup", type=int, default=20)
    ap.add_argument("--ticks", type=int, default=200, help="measured ticks after warmup")
    ap.add_argument("--workers", type=int, default=2, help="PROD_SMALL.max_worker_count")
    ap.add_argument("--chunking", choices=("thread", "process"), default="thread")
    ap.add_argument("--reducers", choices=("none", "mappingproxy"), default="none")
    ap.add_argument("--per-packet-every", type=int, default=20, help="every Nth measured tick also sums per-packet sizes (0 = never)")
    ap.add_argument("--no-probe", action="store_true", help="positive control: the same run without the side path")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    sys.path.insert(0, os.getcwd())
    from src.engine.checkpoint import CanonicalStateHasher
    from tools.test_architecture.rpg_gate_run import build_kernel

    reducers = [] if args.no_probe else _register_reducers(args.reducers)
    run_id = f"chunkprobe_{args.world}_s{args.seed}_{'ctl' if args.no_probe else args.chunking}_{os.getpid()}"
    kernel = build_kernel(args.world, args.seed, run_id)
    probe = None
    if not args.no_probe:
        probe = ProbeExecutor(kernel._executor, args.workers, args.chunking, args.per_packet_every, args.warmup)
        kernel._executor = probe
    tick_ms: List[float] = []
    try:
        for i in range(args.warmup + args.ticks):
            t0 = time.perf_counter_ns()
            kernel.tick_once()
            if i >= args.warmup:
                tick_ms.append((time.perf_counter_ns() - t0) / 1e6)
        final_hash = CanonicalStateHasher.get_hash(kernel.state)
    finally:
        kernel.shutdown()

    doc: Dict[str, Any] = {"schema": "chunk-cost-probe/v1", "world": args.world, "seed": args.seed, "warmup": args.warmup,
                           "ticks": args.ticks, "workers": args.workers, "chunking": args.chunking, "reducers": reducers,
                           "no_probe": args.no_probe, "run_id": run_id, "final_hash": final_hash,
                           "tick_ms_including_probe": _summary(tick_ms)}
    if probe is not None:
        chunks = [c for t in probe.ticks for c in t["chunks"]]
        sent = [c["encode_ms"] + c["decode_ms"] + c["result_encode_ms"] + c["result_decode_ms"] for c in chunks]
        ratio = [s / c["compute_ms"] for s, c in zip(sent, chunks) if c["compute_ms"] > 0]
        doc["per_chunk"] = {k: _summary([c[k] for c in chunks if k in c]) for k in
                            ("packets", "request_bytes", "request_bytes_without_private_caches", "request_bytes_per_packet_sum",
                             "encode_ms", "decode_ms", "compute_ms", "response_bytes", "result_encode_ms", "result_decode_ms", "validate_ms")}
        doc["per_chunk"]["codec_round_trip_ms"] = _summary(sent)
        doc["per_chunk"]["codec_over_compute"] = _summary(ratio)
        doc["per_tick"] = {k: _summary([t[k] for t in probe.ticks]) for k in
                           ("packets", "chunk_size", "sequential_collection_ms", "packet_build_ms")}
        doc["per_tick"]["chunks"] = _summary([len(t["chunks"]) for t in probe.ticks])
        doc["ticks_detail"] = probe.ticks
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    print(json.dumps({k: doc[k] for k in ("world", "chunking", "no_probe", "final_hash")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
