"""Performance smoke test (Milestone 4).

Not a micro-benchmark — a guardrail that the orchestration graph sustains a
reasonable throughput with the offline MockLLM, so a regression that makes the
workflow pathologically slow fails CI. Generous bounds keep it non-flaky on
shared/CI hardware.
"""
from __future__ import annotations

from perf.benchmark import run_benchmark


def test_throughput_and_latency_within_bounds():
    stats = run_benchmark(iterations=30)
    # With the mock LLM the whole pipeline should be well under a quarter second.
    assert stats["avg_ms"] < 250, f"avg latency too high: {stats['avg_ms']:.1f}ms"
    assert stats["throughput_per_sec"] > 5, f"throughput too low: {stats['throughput_per_sec']:.1f}/s"
