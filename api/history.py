"""Lifecycle-owned synthetic history; immutable aggregates and no request-time pandas."""
from dataclasses import dataclass
from datetime import date
from threading import Lock
from types import MappingProxyType
from typing import Literal, Mapping

import pandas as pd

import readiness
from api.config import HistorySettings


METRIC_FIELDS = ("total_tails", "fmc_tails", "pmc_tails", "nmcm_tails", "nmcs_tails",
                 "depot_tails", "svc_pct", "avail_pct")


class HistoryUnavailable(RuntimeError):
    def __init__(self):
        super().__init__("Synthetic history unavailable")


@dataclass(frozen=True)
class DailyReadiness:
    total_tails: int
    fmc_tails: int
    pmc_tails: int
    nmcm_tails: int
    nmcs_tails: int
    depot_tails: int
    svc_pct: float
    avail_pct: float
    statuses: tuple[int, ...]

    def metrics(self) -> dict:
        return {field: getattr(self, field) for field in METRIC_FIELDS}


@dataclass(frozen=True)
class HistoryCache:
    start: date
    end: date
    commands: tuple[str, ...]
    records: Mapping[tuple[date, str | None], DailyReadiness]
    events: pd.DataFrame  # Private to the provider; only copied through load_events.


def prepare_history(settings: HistorySettings) -> HistoryCache:
    # Imports and generation occur only after explicit history-mode lifespan startup.
    from simulator import SimulationConfig, generate

    history = generate(SimulationConfig(date.fromisoformat(settings.as_of), seed=settings.seed))
    snapshot = history.snapshot
    commands = tuple(sorted(history.aircraft.command.unique()))
    records = {}
    # Five calls over indexed groups of the already validated snapshot. Fleet and
    # command subsets use the SAME original daily metric function and zero guards.
    for command in (None, *commands):
        selected = snapshot if command is None else snapshot[snapshot.command.eq(command)]
        counts = selected.groupby(["date", "status"]).size().unstack(fill_value=0)
        counts = counts.reindex(columns=readiness.CANONICAL_STATUSES, fill_value=0)
        for row in readiness.compute_jac_daily_metrics(selected).itertuples(index=False):
            metrics = {field: getattr(row, field) for field in METRIC_FIELDS}
            statuses = tuple(int(counts.loc[row.date, code]) for code in readiness.CANONICAL_STATUSES)
            records[(row.date.date(), command)] = DailyReadiness(**metrics, statuses=statuses)
    if (history.source != "synthetic" or len(commands) != 4
            or len(records) != history.config.days * 5
            or len(history.events) > 160 * 1461
            or any(record.total_tails != (160 if command is None else 40)
                   or sum(record.statuses) != record.total_tails
                   for (_, command), record in records.items())):
        raise ValueError("Invalid synthetic history cache coverage")
    # Release telemetry, episodes and full snapshot after preparing compact records.
    return HistoryCache(history.config.start, history.config.as_of, commands,
                        MappingProxyType(records), history.load_events())


class SyntheticHistoryProvider:
    source: Literal["synthetic"] = "synthetic"

    def __init__(self, settings: HistorySettings):
        self._settings = settings
        self._lock = Lock()
        self._cache: HistoryCache | None = None
        self._failed = False

    def initialize(self) -> None:
        failed = False
        with self._lock:
            if self._cache is not None:
                return
            if self._failed:
                raise HistoryUnavailable()
            try:
                cache = prepare_history(self._settings)
            except Exception:
                failed = self._failed = True
            if not failed:
                self._cache = cache  # Atomic publication, never a partially built cache.
        if failed:
            # No raw generator exception or its context escapes to startup/logs/API.
            raise HistoryUnavailable()

    def close(self) -> None:
        with self._lock:
            self._cache = None

    def _ready(self) -> HistoryCache:
        with self._lock:
            if self._cache is None:
                raise HistoryUnavailable()
            return self._cache

    @property
    def start(self) -> date:
        return self._ready().start

    @property
    def end(self) -> date:
        return self._ready().end

    @property
    def commands(self) -> tuple[str, ...]:
        return self._ready().commands

    def read(self, day: date, command: str | None = None) -> DailyReadiness:
        # No generation, snapshot construction, aggregation or mutable cache result.
        return self._ready().records[(day, command)]

    def load_events(self) -> pd.DataFrame:
        return self._ready().events.copy(deep=True)
