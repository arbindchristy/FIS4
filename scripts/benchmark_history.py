"""Local TestClient timings, not a network/load benchmark. No output files."""
import argparse
from datetime import timedelta
import gc
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter
import tracemalloc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from api.main import create_app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", default="2026-11-20")
    parser.add_argument("--seed", type=int, default=42017)
    parser.add_argument("--requests", type=int, default=30, help="Warm requests per date/filter")
    parser.add_argument("--profile", action="store_true", help="Measure Python allocations; slows initialization")
    args = parser.parse_args()
    if not 1 <= args.requests <= 1000:
        parser.error("requests must be 1..1000")
    if args.profile:
        tracemalloc.start()
    started = perf_counter()
    app = create_app({"mode": "synthetic_history", "history": {"as_of": args.as_of, "seed": args.seed}})
    with TestClient(app) as client:
        cold_seconds = perf_counter() - started
        gc.collect()
        allocation = tracemalloc.get_traced_memory() if args.profile else (None, None)
        if args.profile:
            tracemalloc.stop()
        provider = app.state.provider
        dates = (provider.start, provider.start + timedelta(days=(provider.end - provider.start).days // 2),
                 provider.end)
        results = []
        for day in dates:
            for command in (None, provider.commands[0]):
                params = {"date": day.isoformat()}
                if command is not None:
                    params["command"] = command
                timings = []
                for _ in range(args.requests):
                    tick = perf_counter()
                    response = client.get("/api/v1/readiness/history", params=params)
                    timings.append((perf_counter() - tick) * 1000)
                    response.raise_for_status()
                    assert response.json()["metrics"]["total_tails"] == (40 if command else 160)
                ordered = sorted(timings)
                results.append(dict(date=day.isoformat(), command=command, requests=len(timings),
                                    mean_ms=round(statistics.mean(timings), 3),
                                    median_ms=round(statistics.median(timings), 3),
                                    min_ms=round(ordered[0], 3), max_ms=round(ordered[-1], 3)))
        report = dict(transport="in-process TestClient; sequential; no TCP/TLS/auth/load test",
                      cold_seconds=round(cold_seconds, 3), profile=args.profile,
                      retained_python_allocation_bytes=allocation[0], peak_python_allocation_bytes=allocation[1],
                      warm=results)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
