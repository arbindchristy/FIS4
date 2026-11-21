"""Local generation/measurement entry point; no server or database access."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
from time import perf_counter
import tracemalloc

from simulator import SimulationConfig, generate
from simulator.contracts import SCHEMAS


def main():
    parser = argparse.ArgumentParser(description="Generate FICTIONAL FIS4 fleet history offline")
    parser.add_argument("--as-of", type=date.fromisoformat, required=True)
    parser.add_argument("--seed", type=int, default=42017)
    parser.add_argument("--tails", type=int, default=160)
    parser.add_argument("--years", type=int, default=4)
    parser.add_argument("--profile", action="store_true", help="Measure Python allocation peak (slower)")
    parser.add_argument("--export", action="store_true", help="Write CSVs to a new workspace-local ignored directory")
    args = parser.parse_args()
    try:
        config = SimulationConfig(args.as_of, args.seed, args.tails, args.years)
    except ValueError as error:
        parser.error(str(error))
    if args.profile:
        tracemalloc.start()
    started = perf_counter()
    history = generate(config)
    elapsed = perf_counter() - started
    peak = tracemalloc.get_traced_memory()[1] if args.profile else None
    if args.profile:
        tracemalloc.stop()
    frames = {name: getattr(history, name) for name in (*SCHEMAS, "snapshot")}
    report = dict(schema_version=1, source="synthetic", seed=config.seed,
                  start=config.start.isoformat(), as_of=config.as_of.isoformat(),
                  tails=config.tails, commands=4, days=config.days,
                  rows={name: len(frame) for name, frame in frames.items()})
    if args.export:
        # Fixed, ignored workspace boundary. Never overwrite an earlier artifact.
        root = Path(__file__).resolve().parents[1]
        destination = root / ".harness-test-tmp" / f"synthetic-{config.as_of}-{config.seed}-{config.tails}-{config.years}"
        destination.mkdir(parents=True, exist_ok=False)
        digests = {}
        for name, frame in frames.items():
            path = destination / f"{name}.csv"
            frame.to_csv(path, index=False, lineterminator="\n", date_format="%Y-%m-%dT%H:%M:%S")
            digests[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest = {**report, "sha256": digests}
        (destination / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report["export_directory"] = str(destination.relative_to(root))
    report.update(seconds=round(elapsed, 3),
                  retained_frame_bytes=sum(int(f.memory_usage(index=True, deep=True).sum()) for f in frames.values()),
                  peak_python_allocation_bytes=peak)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
