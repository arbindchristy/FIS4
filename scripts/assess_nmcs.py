"""Offline fictional coverage assessment; never trains, exports rows or loads models."""
import json
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prediction.nmcs import Observation, reconstruct, label_coverage
from simulator import SimulationConfig, generate


def assess():
    started = time.perf_counter()
    config = SimulationConfig(as_of=date(2026, 11, 20), seed=42017)
    world = generate(config)
    # Only public status events: no latent episode closure, actions or sampled durations.
    observations = (Observation(r.date.to_pydatetime(), r.tail, r.status, r.command, r.platform)
                    for r in world.events.itertuples(index=False))
    history = reconstruct(observations, cutoff=world.events.date.max().to_pydatetime(),
                          validated_reconstruction=True)
    episodes = 0
    for rows in history.by_tail.values():
        episodes += sum(r.status == 'NMCS' and (i == 0 or rows[i-1].status != 'NMCS')
                        for i, r in enumerate(rows))
    horizons = label_coverage(history)
    return {
        'source': 'fictional_synthetic', 'seed': config.seed,
        'start': config.start.isoformat(), 'cutoff': config.as_of.isoformat(),
        'tails': len(history.by_tail), 'commands': world.aircraft.command.nunique(),
        'days': config.days, 'tail_days': len(world.snapshot),
        'status_change_and_boundary_records': len(world.events),
        'nmcs_runs': episodes,
        'initial_nmcs_left_censored': sum(rows[0].status == 'NMCS' for rows in history.by_tail.values()),
        'eligible_by_horizon': horizons,
        'elapsed_seconds': round(time.perf_counter() - started, 3),
    }


if __name__ == '__main__':
    print(json.dumps(assess(), indent=2))
