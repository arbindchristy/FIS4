"""Lifecycle-owned synthetic history; immutable aggregates and no request-time pandas."""
from dataclasses import dataclass
from datetime import date, timedelta
from threading import Lock
from types import MappingProxyType
from typing import Literal, Mapping

import pandas as pd

import readiness
from api.config import HistorySettings


METRIC_FIELDS = ("total_tails", "fmc_tails", "pmc_tails", "nmcm_tails", "nmcs_tails",
                 "depot_tails", "svc_pct", "avail_pct")
SERIES_WINDOWS = (30, 90, 180, 365)
MAX_PLATFORMS = 32


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
    platforms: tuple[str, ...]
    platforms_by_command: Mapping[str | None, tuple[str, ...]]
    platform_records: Mapping[tuple[date, str | None, str], DailyReadiness]


@dataclass(frozen=True)
class ReadinessSeries:
    start: date
    end: date
    points: tuple[tuple[date, DailyReadiness], ...]


def prepare_history(settings: HistorySettings) -> HistoryCache:
    # Imports and generation occur only after explicit history-mode lifespan startup.
    from simulator import SimulationConfig, generate

    history = generate(SimulationConfig(date.fromisoformat(settings.as_of), seed=settings.seed))
    snapshot = history.snapshot
    commands = tuple(sorted(history.aircraft.command.unique()))
    platforms = tuple(sorted(history.aircraft.platform.unique()))
    if not 1 <= len(platforms) <= MAX_PLATFORMS:
        raise ValueError("Invalid platform metadata")
    records, platform_records, platforms_by_command = {}, {}, {}
    # All aggregates use the original FIS-001 engine, once during initialization.
    def aggregate(selected):
        counts = selected.groupby(["date", "status"]).size().unstack(fill_value=0)
        counts = counts.reindex(columns=readiness.CANONICAL_STATUSES, fill_value=0)
        for row in readiness.compute_jac_daily_metrics(selected).itertuples(index=False):
            metrics = {field: getattr(row, field) for field in METRIC_FIELDS}
            statuses = tuple(int(counts.loc[row.date, code]) for code in readiness.CANONICAL_STATUSES)
            yield row.date.date(), DailyReadiness(**metrics, statuses=statuses)

    for command in (None, *commands):
        selected = snapshot if command is None else snapshot[snapshot.command.eq(command)]
        records.update(((day, command), record) for day, record in aggregate(selected))
        available = tuple(sorted(selected.platform.unique()))
        platforms_by_command[command] = available
        for platform in available:
            subset = selected[selected.platform.eq(platform)]
            platform_records.update(((day, command, platform), record)
                                    for day, record in aggregate(subset))
            expected_tails = history.aircraft[
                history.aircraft.platform.eq(platform)
                & (True if command is None else history.aircraft.command.eq(command))]["tail"].nunique()
            if any(platform_records[(day.date(), command, platform)].total_tails != expected_tails
                   for day in pd.date_range(history.config.start, history.config.as_of)):
                raise ValueError("Invalid platform coverage")
    if (history.source != "synthetic" or len(commands) != 4
            or len(records) != history.config.days * 5
            or len(history.events) > 160 * 1461
            or any(record.total_tails != (160 if command is None else 40)
                   or sum(record.statuses) != record.total_tails
                   for (_, command), record in records.items())):
        raise ValueError("Invalid synthetic history cache coverage")
    # Release telemetry, episodes and full snapshot after preparing compact records.
    return HistoryCache(history.config.start, history.config.as_of, commands,
                        MappingProxyType(records), history.load_events(), platforms,
                        MappingProxyType(platforms_by_command), MappingProxyType(platform_records))


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

    @property
    def platforms(self) -> tuple[str, ...]:
        return self._ready().platforms

    def platforms_for(self, command: str | None = None) -> tuple[str, ...]:
        return self._ready().platforms_by_command[command]

    @staticmethod
    def _platform_selection(cache: HistoryCache, command: str | None, platform: str) -> None:
        if command is not None and command not in cache.commands:
            raise ValueError("Invalid platform command")
        if platform not in cache.platforms:
            raise ValueError("Invalid platform")
        if platform not in cache.platforms_by_command[command]:
            raise KeyError("No matching platform selection")

    def read_platforms(self, day: date, command: str | None = None,
                       platform: str | None = None) -> tuple[tuple[str, DailyReadiness], ...]:
        cache = self._ready()
        if type(day) is not date:
            raise ValueError("Invalid platform date")
        if command is not None and command not in cache.commands:
            raise ValueError("Invalid platform command")
        if not cache.start <= day <= cache.end:
            raise KeyError("Platform date outside history")
        if platform is not None:
            self._platform_selection(cache, command, platform)
        selected = (platform,) if platform is not None else cache.platforms_by_command[command]
        rows = []
        for label in selected:
            record = cache.platform_records.get((day, command, label))
            if record is None:
                raise HistoryUnavailable()
            rows.append((label, record))
        return tuple(rows)

    def read(self, day: date, command: str | None = None) -> DailyReadiness:
        # No generation, snapshot construction, aggregation or mutable cache result.
        return self._ready().records[(day, command)]

    def read_series(self, end_date: date, days: int, command: str | None = None,
                    platform: str | None = None) -> ReadinessSeries:
        if type(end_date) is not date or type(days) is not int or days not in SERIES_WINDOWS:
            raise ValueError("Invalid series selection")
        cache = self._ready()  # One consistent immutable cache reference, even during shutdown.
        if command is not None and command not in cache.commands:
            raise ValueError("Invalid series command")
        if platform is not None:
            self._platform_selection(cache, command, platform)
        if not cache.start <= end_date <= cache.end:
            raise KeyError("Series end outside history")
        start = max(cache.start, end_date - timedelta(days=days - 1))
        points = []
        for offset in range((end_date - start).days + 1):
            day = start + timedelta(days=offset)
            record = (cache.records.get((day, command)) if platform is None
                      else cache.platform_records.get((day, command, platform)))
            if record is None:
                raise HistoryUnavailable()  # Reject incomplete periods; never silently skip a day.
            points.append((day, record))
        return ReadinessSeries(start, end_date, tuple(points))

    def load_events(self) -> pd.DataFrame:
        return self._ready().events.copy(deep=True)
