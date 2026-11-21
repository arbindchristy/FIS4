"""Event providers. SQL identifiers and queries are authored here, never by callers."""
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
import re
from threading import Lock
from typing import Literal, Protocol

import pandas as pd

import readiness
from api.config import ProviderConfig, ProviderConfigurationError, SqlCredentials, SqlSettings

Source = Literal["synthetic", "sql"]
FIXTURE = Path(__file__).resolve().parents[1] / "data" / "synthetic_readiness.csv"
EVENT_COLUMNS = ("date", "tail", "status", "command")
# This is a REQUIRED contract view, not a claim that it exists on any server.
# Each allowlisted key selects a complete literal SELECT; no identifier interpolation.
SELECTS = {
    "readiness_events_v1": (
        "SELECT TOP (%s) [event_time] AS [date], [tail], [status], [command] "
        "FROM [fis].[readiness_events_v1] ORDER BY [event_time], [tail]"
    )
}
# FreeTDS timeout settings are process-wide. Serialize this application's SQL work.
SQL_LOCK = Lock()


class DataProvider(Protocol):
    source: Source

    def load_events(self) -> pd.DataFrame: ...


class ProviderError(RuntimeError):
    def __init__(self):
        super().__init__("SQL data unavailable")


class SyntheticCsvProvider:
    source: Literal["synthetic"] = "synthetic"

    def load_events(self) -> pd.DataFrame:
        return pd.read_csv(FIXTURE, dtype={"tail": str})


def connect_pymssql(**kwargs):
    # Import is lazy; synthetic use and injected mocks need no native driver.
    import pymssql

    if pymssql.__version__ != "2.3.3":
        raise ProviderError()
    return pymssql.connect(**kwargs)


class SqlProvider:
    source: Literal["sql"] = "sql"

    def __init__(self, settings: SqlSettings, credentials: SqlCredentials,
                 connection_factory: Callable = connect_pymssql):
        self.settings = settings
        self._credentials = credentials
        self._connect = connection_factory

    def load_events(self) -> pd.DataFrame:
        failed = False
        events = None
        if not SQL_LOCK.acquire(timeout=self.settings.login_timeout):
            raise ProviderError()
        try:
            try:
                events = self._read_events()
            except Exception:
                failed = True
        finally:
            SQL_LOCK.release()
        if failed:
            # Outside the except block: no driver exception/context can leak.
            raise ProviderError()
        return events

    def _read_events(self) -> pd.DataFrame:
        connection = cursor = None
        try:
            connection = self._connect(
                server=self.settings.server, port=str(self.settings.port),
                database=self.settings.database,
                user=self._credentials.username.get_secret_value(),
                password=self._credentials.password.get_secret_value(),
                login_timeout=self.settings.login_timeout, timeout=self.settings.query_timeout,
                as_dict=True, charset="UTF-8", tds_version="7.4", use_datetime2=True,
                read_only=True, encryption="require", autocommit=False, appname="FIS4",
            )
            cursor = connection.cursor()
            cursor.execute(SELECTS[self.settings.source], (self.settings.max_rows + 1,))
            if tuple(column[0] for column in cursor.description or ()) != EVENT_COLUMNS:
                raise ProviderError()
            records = []
            while True:
                size = min(self.settings.batch_size, self.settings.max_rows + 1 - len(records))
                batch = cursor.fetchmany(size)
                if not batch:
                    break
                if not isinstance(batch, list) or len(batch) > size:
                    raise ProviderError()
                records.extend(batch)
                if len(records) > self.settings.max_rows:
                    raise ProviderError()  # Never compute readiness from truncated history.
            return self._validate_records(records)
        finally:
            cleanup_failed = False
            for resource in (cursor, connection):
                if resource is not None:
                    try:
                        resource.close()
                    except Exception:
                        cleanup_failed = True
            if cleanup_failed:
                raise ProviderError()

    def _validate_records(self, records: list[dict]) -> pd.DataFrame:
        for row in records:
            if not isinstance(row, dict) or set(row) != set(EVENT_COLUMNS):
                raise ProviderError()
            stamp = row["date"]
            if not isinstance(stamp, datetime) or pd.isna(stamp) or stamp.tzinfo is not None:
                raise ProviderError()
            for field, limit in (("tail", 64), ("status", 64), ("command", 32)):
                value = row[field]
                if (not isinstance(value, str) or not value.strip() or len(value) > limit
                        or not value.isprintable()):
                    raise ProviderError()
            if re.fullmatch(r"[A-Z0-9_-]{1,32}", row["command"].strip()) is None:
                raise ProviderError()
        events = pd.DataFrame(records, columns=EVENT_COLUMNS)
        if events.empty:
            return events
        clean = readiness.coalesce_columns(events)
        if len(clean) != len(events):
            raise ProviderError()
        # Exact retransmissions are harmless; conflicting equal-time events have
        # no approved tie-break rule, so reject rather than invent ordering.
        clean = clean.drop_duplicates()
        if clean.duplicated(["date", "tail"]).any():
            raise ProviderError()
        first_days = clean.groupby("tail")["date"].min().dt.normalize()
        last_day = clean["date"].max().normalize()
        spans = (last_day - first_days).dt.days + 1
        if spans.max() > self.settings.max_span_days or spans.sum() > self.settings.max_snapshot_rows:
            raise ProviderError()
        return clean.sort_values(["date", "tail"]).reset_index(drop=True)


def create_provider(config: ProviderConfig, credentials: SqlCredentials | None = None,
                    connection_factory: Callable | None = None) -> DataProvider:
    if config.mode in ("synthetic", "synthetic_history"):
        if credentials is not None or connection_factory is not None:
            raise ProviderConfigurationError()
        if config.mode == "synthetic_history":
            from api.history import SyntheticHistoryProvider

            return SyntheticHistoryProvider(config.history)
        return SyntheticCsvProvider()
    if not isinstance(credentials, SqlCredentials) or not isinstance(config.sql, SqlSettings):
        raise ProviderConfigurationError()
    if connection_factory is not None and not callable(connection_factory):
        raise ProviderConfigurationError()
    factory = connect_pymssql if connection_factory is None else connection_factory
    return SqlProvider(config.sql, credentials, factory)
