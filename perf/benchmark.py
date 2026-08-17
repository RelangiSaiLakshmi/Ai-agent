"""Performance benchmark for the orchestration graph (Milestone 4).

Runs the multi-agent workflow N times against a throwaway database and reports
latency (avg / p50 / p95 / max) and throughput. Uses the offline MockLLM by
default so the numbers reflect orchestration + persistence overhead, not network
latency to a hosted model.

    python -m perf.benchmark --iterations 200
"""
from __future__ import annotations

import argparse
import statistics
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

from llm.mock import MockLLM
from schemas.state import LeaveRequest
from utils.config import settings
from workflows import run_leave_graph


def _next_weekday(d: date) -> date:
    while d.weekday() >= 5:
        d = date.fromordinal(d.toordinal() + 1)
    return d


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, round((pct / 100) * (len(ordered) - 1))))
    return ordered[k]


def run_benchmark(iterations: int = 100) -> dict[str, float]:
    # Isolate the benchmark from the developer's real database.
    tmp = Path(tempfile.mkdtemp()) / "bench.db"
    original = settings.db_path
    settings.db_path = str(tmp)
    from database.seed import seed

    seed(str(tmp))

    start = _next_weekday(date.today() + timedelta(days=21))
    end = _next_weekday(start + timedelta(days=2))
    scenarios = [
        ("E001", "casual"),   # approve
        ("E002", "earned"),   # reject
        ("E003", "earned"),   # escalate
    ]
    llm = MockLLM()

    latencies: list[float] = []
    wall_start = time.perf_counter()
    try:
        for i in range(iterations):
            emp, lt = scenarios[i % len(scenarios)]
            req = LeaveRequest(emp, lt, start.isoformat(), end.isoformat(), "bench")
            t0 = time.perf_counter()
            run_leave_graph(req, llm)
            latencies.append((time.perf_counter() - t0) * 1000)  # ms
        wall = time.perf_counter() - wall_start
    finally:
        settings.db_path = original

    return {
        "iterations": iterations,
        "total_seconds": wall,
        "throughput_per_sec": iterations / wall if wall else 0.0,
        "avg_ms": statistics.mean(latencies),
        "p50_ms": _percentile(latencies, 50),
        "p95_ms": _percentile(latencies, 95),
        "max_ms": max(latencies),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the orchestration graph")
    parser.add_argument("--iterations", type=int, default=100)
    args = parser.parse_args()

    stats = run_benchmark(args.iterations)
    print("\nOrchestration-graph benchmark (MockLLM, in-process)")
    print("-" * 52)
    print(f"iterations       : {stats['iterations']}")
    print(f"total            : {stats['total_seconds']:.2f} s")
    print(f"throughput       : {stats['throughput_per_sec']:.1f} req/s")
    print(f"latency avg      : {stats['avg_ms']:.1f} ms")
    print(f"latency p50      : {stats['p50_ms']:.1f} ms")
    print(f"latency p95      : {stats['p95_ms']:.1f} ms")
    print(f"latency max      : {stats['max_ms']:.1f} ms")


if __name__ == "__main__":
    main()
