"""Deterministic discrete-day simulation using fictional engineering assumptions."""
from dataclasses import dataclass
from datetime import datetime, time, timedelta
import random

import pandas as pd

import readiness
from simulator.contracts import COMMANDS, PLATFORMS, SCHEMAS, SimulationConfig, SyntheticHistory


@dataclass(frozen=True)
class Conditions:
    flying_probability: float
    environmental_stress: float
    supply_delay: int
    repair_days: int


# Purely invented contrasts; these do not describe any service or aircraft type.
CONDITIONS = (
    Conditions(.77, 1.0, 7, 3), Conditions(.62, 1.35, 12, 4),
    Conditions(.85, 1.15, 9, 3), Conditions(.55, .85, 5, 5),
)
FAULTS = ("FICTIONAL_SENSOR", "FICTIONAL_ACTUATOR", "FICTIONAL_COOLING", "FICTIONAL_POWER")


def generate(config: SimulationConfig) -> SyntheticHistory:
    """Generate all history, construct/validate approved snapshots, return in memory.

    No file/network access, system clock, global RNG, model or API import.
    Durations are latent simulator state and are never exported as future features.
    """
    if not isinstance(config, SimulationConfig):
        raise ValueError("validated SimulationConfig required")
    rows = {name: [] for name in SCHEMAS}
    for index in range(config.tails):
        rng = random.Random((config.seed << 16) + index)
        tail = f"{index + 1:06d}"
        command = COMMANDS[index % 4]
        # Metadata only: no extra RNG draws or changes to operational trajectories.
        platform = PLATFORMS[(index // len(COMMANDS)) % len(PLATFORMS)]
        condition = CONDITIONS[index % 4]
        initial = rng.randint(5000, 25000)  # Integer tenths of a flight hour.
        hours = initial
        interval = 2400
        remaining = rng.randint(500, interval)
        rows["aircraft"].append((tail, command, initial / 10, interval / 10, remaining / 10, platform))
        active = None
        faults = recurrent = serial = 0
        last_fault = ""
        seen_faults = set()
        previous_status = None
        next_depot = rng.randint(80, 650)

        def action(stamp, episode, name):
            rows["actions"].append((stamp, episode["id"], name))

        for offset in range(config.days):
            day = config.start + timedelta(days=offset)
            midnight = datetime.combine(day, time())
            eod = midnight + timedelta(hours=23, minutes=59, seconds=59)
            # All lifecycle work precedes today's flight opportunity.
            if active:
                age = offset - active["start"]
                if active["supply"] and age == active["arrival"]:
                    action(midnight, active, "PART_RECEIPT")
                if age == active["duration"]:
                    action(midnight + timedelta(minutes=1), active, "CLOSE")
                    active["row"][6] = midnight + timedelta(minutes=1)
                    if active["kind"] in ("INSPECTION", "DEPOT"):
                        remaining = interval
                    if active["kind"] == "DEPOT":
                        next_depot = offset + rng.randint(550, 750)
                    active = None

            # At most one active maintenance/depot episode per aircraft.
            if active is None:
                kind = None
                if offset >= next_depot:
                    kind = "DEPOT"
                elif remaining == 0:
                    kind = "INSPECTION"
                else:
                    # Stress, accumulated use and proximity to inspection alter risk;
                    # random noise and healthy days prevent deterministic labels.
                    risk = .008 * condition.environmental_stress * (1 + hours / 100000)
                    risk *= 1 + .8 * (1 - remaining / interval)
                    if rng.random() < risk:
                        kind = "FAULT"
                if kind:
                    serial += 1
                    eid = f"SYN-{tail}-{serial:05d}"
                    repeat_last = kind == "FAULT" and bool(last_fault) and rng.random() < .45
                    code = (last_fault if repeat_last else rng.choice(FAULTS)) if kind == "FAULT" else ""
                    is_recurring = kind == "FAULT" and code in seen_faults
                    if kind == "FAULT":
                        faults += 1
                        recurrent += int(is_recurring)
                        last_fault = code
                        seen_faults.add(code)
                    supply = kind == "FAULT" and rng.random() < .5
                    arrival = rng.randint(2, condition.supply_delay * 2) if supply else 0
                    repair = rng.randint(1, condition.repair_days * 2)
                    duration = (rng.randint(30, 65) if kind == "DEPOT" else
                                rng.randint(2, 5) if kind == "INSPECTION" else arrival + repair)
                    major = kind != "FAULT" or rng.random() < .6
                    row = [eid, tail, kind, code, is_recurring, midnight + timedelta(minutes=2), None]
                    rows["episodes"].append(row)
                    active = dict(id=eid, row=row, kind=kind, start=offset,
                                  duration=duration, arrival=arrival, supply=supply, major=major)
                    action(row[5], active, "OPEN")
                    if supply:
                        action(midnight + timedelta(minutes=3), active, "PART_REQUEST")

            age = offset - active["start"] if active else 0
            waiting = bool(active and active["supply"] and age < active["arrival"])
            if not active:
                status = "FMC"
            elif active["kind"] == "DEPOT":
                status = "DEPOT"
            elif active["major"]:
                status = "NMCS" if waiting else "NMCM"
            else:
                status = "PMCS" if waiting else "PMCM"
            flown = 0
            if status in ("FMC", "PMCM", "PMCS"):
                probability = condition.flying_probability * (.6 if status != "FMC" else 1)
                if rng.random() < probability:
                    flown = min(remaining, rng.randint(5, 40))
                    remaining -= flown
                    hours += flown
            rows["operations"].append((pd.Timestamp(day), tail, flown / 10, hours / 10,
                                       remaining / 10, faults, recurrent,
                                       active["id"] if active else "", age,
                                       age if waiting else 0, int(waiting)))
            if status != previous_status or offset == config.days - 1:
                rows["events"].append((eod, tail, status, command, platform))
            previous_status = status

    frames = {name: pd.DataFrame(records, columns=SCHEMAS[name]) for name, records in rows.items()}
    for name, columns in (("events", ["date", "tail"]), ("operations", ["date", "tail"]),
                          ("actions", ["date", "episode_id", "action"])):
        frames[name] = frames[name].sort_values(columns).reset_index(drop=True)
    for name in ("episodes",):
        for field in ("opened_at", "closed_at"):
            frames[name][field] = pd.to_datetime(frames[name][field])
    events = frames["events"]
    snapshot = readiness.build_tail_daily_snapshot(readiness.coalesce_columns(events))
    snapshot = snapshot.sort_values(["date", "tail"]).reset_index(drop=True)
    result = SyntheticHistory(config, **frames, snapshot=snapshot)
    result.validate()
    return result
