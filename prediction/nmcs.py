"""Pure, explicit NMCS occupancy preparation. No inference or readiness formulas."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from statistics import mean
from types import MappingProxyType
from typing import Mapping


STATUSES = frozenset(("FMC", "PMCM", "PMCS", "NMCS", "NMCM", "DEPOT"))
WINDOWS = (30, 90, 180, 365)


@dataclass(frozen=True)
class Observation:
    timestamp: datetime
    tail: str
    status: str
    command: str
    platform: str
    hrs_to_insp: float | None = None
    hrs_to_phase: float | None = None


@dataclass(frozen=True)
class Day:
    date: date
    status: str
    command: str
    platform: str
    observed: bool
    usable: bool
    hrs_to_insp: float | None
    hrs_to_phase: float | None


@dataclass(frozen=True)
class History:
    observations: tuple[Observation, ...]
    cutoff: datetime
    validated_reconstruction: bool
    by_tail: Mapping[str, tuple[Day, ...]]

    def at(self, tail: str, day: date) -> Day | None:
        rows = self.by_tail.get(tail, ())
        offset = (day - rows[0].date).days if rows else -1
        return rows[offset] if 0 <= offset < len(rows) else None


@dataclass(frozen=True)
class Target:
    tail: str
    observation_date: date
    horizon_days: int
    target_date: date
    value: int | None
    reason: str
    provenance: str | None


def _day(value):
    if type(value) is not date:
        raise ValueError("A calendar date is required")


def _timestamp(value):
    if type(value) is not datetime or value.tzinfo is not None:
        raise ValueError("An approved source-calendar naive timestamp is required")


def _text(value):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError("Nonempty normalized text identifiers are required")


def reconstruct(observations, *, cutoff: datetime,
                validated_reconstruction: bool = False) -> History:
    """Daily last non-null hours, no backfill, forward-fill to visible global end.

    Only explicitly validated carry days are usable labels/features. Equal-time
    identical rows collapse; conflicts fail closed. Input is already normalized.
    Future contents are excluded before status/ownership validation.
    """
    import math

    _timestamp(cutoff)
    if type(validated_reconstruction) is not bool:
        raise ValueError("Reconstruction approval must be explicit")
    unique = {}
    owners = {}
    for row in observations:
        if not isinstance(row, Observation):
            raise ValueError("Observation records required")
        _timestamp(row.timestamp)
        if row.timestamp > cutoff:
            continue
        for value in (row.tail, row.command, row.platform):
            _text(value)
        if row.status not in STATUSES:
            raise ValueError("Canonical status required; ambiguous aliases rejected")
        for value in (row.hrs_to_insp, row.hrs_to_phase):
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
                raise ValueError("Hours must be finite numeric values or explicitly missing")
        owner = (row.command, row.platform)
        if owners.setdefault(row.tail, owner) != owner:
            raise ValueError("Conflicting current tail ownership or platform identity")
        key = (row.tail, row.timestamp)
        if key in unique and unique[key] != row:
            raise ValueError("Conflicting equal-timestamp observations")
        unique[key] = row
    ordered = tuple(sorted(unique.values(), key=lambda x: (x.tail, x.timestamp)))
    end = max((r.timestamp.date() for r in ordered), default=None)
    groups = {}
    for row in ordered:
        groups.setdefault(row.tail, []).append(row)
    result = {}
    for tail, rows in groups.items():
        daily = {}
        hours = [None, None]
        for row in rows:
            # Equivalent per-column last/non-null then ffill for these inputs.
            for i, value in enumerate((row.hrs_to_insp, row.hrs_to_phase)):
                if value is not None:
                    hours[i] = value
            daily[row.timestamp.date()] = (row, tuple(hours))
        day = rows[0].timestamp.date()
        output = []
        while day <= end:
            observed = day in daily
            if observed:
                last, last_hours = daily[day]
            output.append(Day(day, last.status, last.command, last.platform,
                              observed, observed or validated_reconstruction,
                              last_hours[0], last_hours[1]))
            day += timedelta(days=1)
        result[tail] = tuple(output)
    return History(ordered, cutoff, validated_reconstruction, MappingProxyType(result))


def target_at(history: History, tail: str, observation_date: date, horizon_days: int) -> Target:
    """Label occupancy at exactly T+H, never any-onset-in-window or combined NMC."""
    _day(observation_date)
    _text(tail)
    if type(horizon_days) is not int or not 1 <= horizon_days <= 180:
        raise ValueError("Forecast offset must be an integer in 1..180")
    target_date = observation_date + timedelta(days=horizon_days)
    reference = history.at(tail, observation_date)
    outcome = history.at(tail, target_date)
    reason = "available"
    if observation_date > history.cutoff.date() or reference is None or not reference.usable:
        reason = "reference_unavailable"
    elif target_date > history.cutoff.date():
        reason = "after_cutoff"
    elif outcome is None or not outcome.usable:
        reason = "target_unavailable"
    valid = reason == "available"
    return Target(tail, observation_date, horizon_days, target_date,
                  int(outcome.status == "NMCS") if valid else None, reason,
                  ("observed" if outcome.observed else "validated_carry") if valid else None)


def label_coverage(history: History) -> dict:
    """Bounded 1..180 occupancy counts, without materializing overlapping examples."""
    result = {}
    for horizon in range(1, 181):
        eligible = positive = 0
        for rows in history.by_tail.values():
            for before, after in zip(rows, rows[horizon:]):
                if before.usable and after.usable:
                    eligible += 1
                    positive += after.status == 'NMCS'
        result[horizon] = {'eligible': eligible, 'nmcs_positive': positive}
    return result


def _episodes(rows):
    """Known NMCS fragments; exclude left-censored runs from complete statistics."""
    fragments, transitions = [], []
    previous = None
    active = None
    for row in rows:
        if not row.usable:
            active = None
            previous = None
            continue
        if previous and previous.status != row.status:
            transitions.append((previous.status, row.status))
        if row.status == "NMCS":
            if active is None:
                active = {"start": row.date, "days": 0,
                          "left_censored": previous is None, "recovered": False}
                fragments.append(active)
            active["days"] += 1
        elif active is not None:
            active["recovered"] = True
            active = None
        previous = row
    return fragments, transitions


def features_at(history: History, tail: str, reference_date: date, *,
                windows=WINDOWS, history_years: int = 6) -> dict:
    """Separate feature payload; no labels, future rows, latent episode/action data.

    Default six-calendar-year reference is clipped to available data. Incomplete
    windows have null counts, explicit coverage and censored episode diagnostics.
    """
    _day(reference_date)
    _text(tail)
    if reference_date > history.cutoff.date():
        raise ValueError("Reference exceeds validated-data cutoff")
    if type(history_years) is not int or not 1 <= history_years <= 10:
        raise ValueError("History years must be in 1..10")
    windows = tuple(windows)
    if not windows or len(set(windows)) != len(windows) or any(
            type(w) is not int or not 1 <= w <= 3660 for w in windows):
        raise ValueError("Unique bounded calendar windows required")
    # Reuse immutable daily rows; never rebuild a fleet snapshot per feature query.
    # A future observation must not extend the visible global history endpoint.
    asof_cutoff = min(history.cutoff, datetime.combine(reference_date, time.max))
    visible_end = max((r.timestamp.date() for r in history.observations
                       if r.timestamp <= asof_cutoff), default=None)
    current = history.at(tail, reference_date) if visible_end and reference_date <= visible_end else None
    if current is None or not current.usable:
        raise ValueError("Reference status unavailable")
    try:
        start = reference_date.replace(year=reference_date.year - history_years) + timedelta(days=1)
    except ValueError:
        start = reference_date.replace(year=reference_date.year - history_years, day=28) + timedelta(days=1)
    rows = [r for r in history.by_tail[tail] if start <= r.date <= reference_date]
    fragments, transitions = _episodes(rows)
    complete = [e for e in fragments if not e['left_censored'] and e['recovered']]
    known = [r for r in rows if r.usable]
    last_nmcs = next((r.date for r in reversed(known) if r.status == 'NMCS'), None)
    run = []
    for row in reversed(rows):
        if not row.usable or row.status != current.status:
            break
        run.append(row)
    starts = [e['start'] for e in fragments if not e['left_censored']]
    intervals = [(b - a).days for a, b in zip(starts, starts[1:])
                 if all(r.usable for r in rows if a <= r.date <= b)]
    since_known = (reference_date - last_nmcs).days if last_nmcs else None
    since_valid = last_nmcs is not None and all(r.usable for r in rows if r.date >= last_nmcs)
    result = {
        'reference_date': reference_date.isoformat(),
        'validated_data_cutoff': asof_cutoff.isoformat(),
        'requested_history_start': start.isoformat(),
        'effective_history_start': rows[0].date.isoformat(),
        'history_days': len(rows), 'usable_history_days': len(known),
        'history_complete': len(known) == (reference_date - start).days + 1,
        'command': current.command, 'platform': current.platform, 'current_status': current.status,
        'hrs_to_insp': current.hrs_to_insp, 'hrs_to_phase': current.hrs_to_phase,
        'hrs_to_insp_missing': current.hrs_to_insp is None,
        'hrs_to_phase_missing': current.hrs_to_phase is None,
        'days_since_last_nmcs': since_known if since_valid else None,
        'days_since_last_known_nmcs': since_known,
        'current_state_days_lower_bound': len(run),
        'current_state_left_censored': len(run) == len(rows) or not rows[-len(run)-1].usable,
        'nmcs_fragments': len(fragments),
        'nmcs_known_starts': len(starts),
        'nmcs_complete_episodes': len(complete),
        'nmcs_left_censored_fragments': sum(e['left_censored'] for e in fragments),
        'completed_nmcs_duration_mean': mean(e['days'] for e in complete) if complete else None,
        'completed_nmcs_durations': tuple(e['days'] for e in complete),
        'nmcs_recurrence_interval_mean': mean(intervals) if intervals else None,
        'state_transition_counts': {f'{a}->{b}': transitions.count((a, b)) for a, b in sorted(set(transitions))},
        'windows': {},
    }
    for window in windows:
        selected = [r for r in rows if r.date >= reference_date - timedelta(days=window - 1)]
        usable = sum(r.usable for r in selected)
        full = usable == window
        episodes, _ = _episodes(selected)
        result['windows'][window] = {
            'expected_days': window, 'usable_days': usable, 'complete': full,
            'nmcs_days': sum(r.status == 'NMCS' for r in selected) if full else None,
            'nmcs_known_starts': sum(not e['left_censored'] for e in episodes) if full else None,
        }
    return result
