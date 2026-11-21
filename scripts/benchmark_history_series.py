"""Warm series response sizes/timings via local TestClient; no output files."""
import argparse
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from api.history import SERIES_WINDOWS
from api.main import MAX_SERIES_BYTES, create_app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", default="2026-11-20")
    parser.add_argument("--seed", type=int, default=42017)
    parser.add_argument("--requests", type=int, default=30)
    args = parser.parse_args()
    if not 1 <= args.requests <= 1000:
        parser.error("requests must be 1..1000")
    app = create_app({"mode": "synthetic_history", "history": {"as_of": args.as_of, "seed": args.seed}})
    started = perf_counter()
    with TestClient(app) as client:
        initialization_seconds = perf_counter() - started
        results = []
        for days in SERIES_WINDOWS:
            for command in (None, app.state.provider.commands[0]):
                params = {"end_date": args.as_of, "days": str(days)}
                if command is not None:
                    params["command"] = command
                # Exclude one untimed request per selection, after real lifespan initialization.
                client.get("/api/v1/readiness/history/series", params=params).raise_for_status()
                timings, sizes = [], set()
                for _ in range(args.requests):
                    tick = perf_counter()
                    response = client.get("/api/v1/readiness/history/series", params=params)
                    timings.append((perf_counter() - tick) * 1000)
                    response.raise_for_status()
                    body = response.json()
                    assert body["point_count"] == days
                    assert body["observations"][0]["total_tails"] == (40 if command else 160)
                    assert len(response.content) <= MAX_SERIES_BYTES
                    sizes.add(len(response.content))
                assert len(sizes) == 1, "Stable selection must have identical response sizes"
                results.append(dict(days=days, command=command, requests=args.requests,
                                    response_bytes=sizes.pop(), mean_ms=round(statistics.mean(timings), 3),
                                    median_ms=round(statistics.median(timings), 3),
                                    min_ms=round(min(timings), 3), max_ms=round(max(timings), 3)))
    print(json.dumps(dict(transport="in-process TestClient; sequential; not network/production latency",
                          initialization_seconds=round(initialization_seconds, 3),
                          maximum_json_body_bytes=MAX_SERIES_BYTES, warm=results), indent=2))


if __name__ == "__main__":
    main()
