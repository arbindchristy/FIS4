"""Entirely fictional records and injected DB-API mocks; no live SQL acceptance."""
from datetime import datetime, timezone
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

import pandas as pd
from fastapi.testclient import TestClient
from pandas.testing import assert_frame_equal

import readiness
from api.config import (ProviderConfig, ProviderConfigurationError, SqlCredentials,
                        SqlSettings, parse_config)
from api.main import create_app, get_provider
from api.providers import (EVENT_COLUMNS, FIXTURE, SELECTS, SQL_LOCK, ProviderError,
                           SqlProvider, SyntheticCsvProvider, create_provider)


def credentials():
    # Disposable test-only values, never a real credential or environment lookup.
    return SqlCredentials.model_validate(dict(zip(("username", "password"),
                                                  ("fictional-user", "FICTIONAL_" + uuid4().hex))))


def event(stamp="2026-01-01T08:00:00", tail="0001", status="FMC", command="A"):
    return dict(date=datetime.fromisoformat(stamp), tail=tail, status=status, command=command)


def fixture_events():
    frame = pd.read_csv(FIXTURE, dtype={"tail": str})
    clean = readiness.coalesce_columns(frame)
    return clean[list(EVENT_COLUMNS)].to_dict("records")


def mock_connection(records, description=EVENT_COLUMNS):
    remaining = list(records)
    cursor = Mock()
    cursor.description = [(column,) for column in description]

    def fetch(size):
        batch = remaining[:size]
        del remaining[:size]
        return batch

    cursor.fetchmany.side_effect = fetch
    connection = Mock()
    connection.cursor.return_value = cursor
    factory = Mock(return_value=connection)
    return factory, connection, cursor


def sql_config(**overrides):
    return parse_config({"mode": "sql", "sql": {
        "server": "sql.example.invalid", "database": "FIS4_DEMO", **overrides}})


class ConfigurationTests(unittest.TestCase):
    def test_default_is_synthetic_without_environment_discovery(self):
        with patch("os.getenv", side_effect=AssertionError("No environment discovery")):
            config = parse_config()
            provider = create_provider(config)
        self.assertEqual(config.mode, "synthetic")
        self.assertIsInstance(provider, SyntheticCsvProvider)

    def test_explicit_sql_selection_does_not_connect_at_construction(self):
        factory = Mock(side_effect=AssertionError("No startup connection"))
        provider = create_provider(sql_config(), credentials(), factory)
        self.assertIsInstance(provider, SqlProvider)
        factory.assert_not_called()

    def test_invalid_modes_settings_and_identifiers_are_rejected(self):
        invalid = [{"mode": "typo"}, {"mode": "sql"}, {"path": "private-marker"},
                   {"mode": "synthetic", "sql": {"server": "demo", "database": "demo"}}]
        for values in invalid:
            with self.subTest(values=values), self.assertRaisesRegex(ProviderConfigurationError, "^Invalid provider configuration$"):
                parse_config(values)
        for key, value in (("source", "mod.VW_MNT_AIRCRAFT_SERVICEABILITY"),
                           ("source", "readiness_events_v1; DROP TABLE x"),
                           ("server", "demo;bad"), ("database", "demo]bad"),
                           ("query", "SELECT anything")):
            with self.subTest(key=key), self.assertRaises(ProviderConfigurationError):
                sql_config(**{key: value})

    def test_bounds_and_numeric_types_are_strict(self):
        for key, value in (("port", 0), ("port", "1433"), ("login_timeout", 0),
                           ("query_timeout", 121), ("max_rows", 100001), ("max_rows", True),
                           ("batch_size", 1001), ("max_span_days", 0), ("max_snapshot_rows", 0)):
            with self.subTest(key=key, value=value), self.assertRaises(ProviderConfigurationError):
                sql_config(**{key: value})

    def test_sql_requires_credentials_and_synthetic_rejects_them(self):
        with self.assertRaises(ProviderConfigurationError):
            create_provider(sql_config())
        with self.assertRaises(ProviderConfigurationError):
            create_provider(ProviderConfig(), credentials())

    def test_safe_template_has_no_credentials_and_does_not_autoload(self):
        path = Path(__file__).resolve().parents[1] / "config" / "sql-provider.example.json"
        config = parse_config(json.loads(path.read_text()))
        self.assertEqual(config.mode, "sql")
        self.assertEqual(config.sql.server, "sql.example.invalid")
        with self.assertRaises(ProviderConfigurationError):
            create_provider(config)
        self.assertEqual(create_app().state.provider.source, "synthetic")

    def test_credentials_and_configuration_errors_are_redacted(self):
        secret = credentials()
        sentinel = secret.password.get_secret_value()
        for rendered in (str(secret), repr(secret), secret.model_dump_json()):
            self.assertNotIn(sentinel, rendered)
            self.assertNotIn("fictional-user", rendered)
        try:
            parse_config({"mode": sentinel})
        except ProviderConfigurationError as error:
            self.assertNotIn(sentinel, str(error))
            self.assertIsNone(error.__context__)
        else:
            self.fail("Invalid config was accepted")


class SqlProviderTests(unittest.TestCase):
    def provider(self, records=None, **settings):
        factory, connection, cursor = mock_connection([event()] if records is None else records)
        return SqlProvider(sql_config(**settings).sql, credentials(), factory), factory, connection, cursor

    def test_success_uses_literal_select_parameters_and_secure_connection_options(self):
        provider, factory, connection, cursor = self.provider(max_rows=10, batch_size=2)
        frame = provider.load_events()
        self.assertEqual(frame["tail"].tolist(), ["0001"])
        cursor.execute.assert_called_once_with(SELECTS["readiness_events_v1"], (11,))
        self.assertTrue(cursor.execute.call_args.args[0].startswith("SELECT TOP (%s)"))
        options = factory.call_args.kwargs
        self.assertEqual(options["login_timeout"], 5)
        self.assertEqual(options["timeout"], 15)
        self.assertTrue(options["read_only"])
        self.assertEqual(options["encryption"], "require")
        self.assertEqual(options["tds_version"], "7.4")
        self.assertFalse(options["autocommit"])
        connection.commit.assert_not_called()
        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    def test_empty_result_keeps_event_schema(self):
        provider, _, connection, cursor = self.provider([])
        frame = provider.load_events()
        self.assertTrue(frame.empty)
        self.assertEqual(tuple(frame.columns), EVENT_COLUMNS)
        connection.close.assert_called_once()
        cursor.close.assert_called_once()

    def test_missing_or_wrong_result_columns_fail_even_for_empty_results(self):
        for columns in (("date", "tail"), tuple(reversed(EVENT_COLUMNS))):
            provider, _, connection, cursor = self.provider([])
            cursor.description = [(column,) for column in columns]
            with self.assertRaises(ProviderError):
                provider.load_events()
            connection.close.assert_called_once()

    def test_invalid_records_are_rejected_without_dropping_them(self):
        bad = [None, (), {"tail": "0001"}, {**event(), "extra": "hidden"}]
        for key, value in (("date", "bad"), ("date", None),
                           ("date", datetime(2026, 1, 1, tzinfo=timezone.utc)),
                           ("date", datetime(1, 1, 1)), ("tail", 1), ("tail", None),
                           ("tail", " "), ("tail", "X" * 65), ("command", None),
                           ("command", ""), ("command", "a"), ("command", "A\nB"),
                           ("status", None), ("status", ""), ("tail", "00\x001")):
            bad.append({**event(), key: value})
        for row in bad:
            with self.subTest(kind=type(row).__name__):
                provider, _, connection, cursor = self.provider([row])
                with self.assertRaisesRegex(ProviderError, "^SQL data unavailable$"):
                    provider.load_events()
                connection.close.assert_called_once()
                cursor.close.assert_called_once()

    def test_leading_zero_text_tail_is_preserved_and_numeric_tail_is_rejected(self):
        provider, *_ = self.provider([event(tail=" 0001 ")])
        self.assertEqual(provider.load_events().iloc[0]["tail"], "0001")
        provider, *_ = self.provider([event(tail=1)])
        with self.assertRaises(ProviderError):
            provider.load_events()

    def test_unknown_status_is_normalized_without_reclassification(self):
        provider, *_ = self.provider([event(status=" mystery ")])
        frame = provider.load_events()
        self.assertEqual(frame.iloc[0]["status"], "MYSTERY")
        metrics = readiness.compute_jac_daily_metrics(readiness.build_tail_daily_snapshot(frame))
        self.assertEqual(metrics.iloc[0]["svc_pct"], 0)

    def test_snapshot_order_gaps_transfer_and_no_backfill_match_synthetic(self):
        provider, *_ = self.provider(list(reversed(fixture_events())))
        actual = readiness.build_tail_daily_snapshot(provider.load_events())
        expected = readiness.build_tail_daily_snapshot(readiness.coalesce_columns(
            SyntheticCsvProvider().load_events()))[list(actual.columns)]
        assert_frame_equal(actual, expected)
        self.assertEqual(len(actual), 19)
        self.assertEqual(actual.query("tail == '0002'")["command"].tolist(), ["A", "A", "B"])
        self.assertEqual(len(actual.query("tail == '0007'")), 1)

    def test_exact_duplicate_events_do_not_inflate_readiness(self):
        records = fixture_events()
        provider, *_ = self.provider(records + records)
        actual = readiness.build_tail_daily_snapshot(provider.load_events())
        self.assertEqual(len(actual), 19)
        self.assertFalse(actual.duplicated(["date", "tail"]).any())
        first = readiness.compute_jac_daily_metrics(actual).iloc[0]
        self.assertEqual(first["svc_pct"], 75)
        self.assertEqual(first["avail_pct"], 50)

    def test_conflicting_equal_time_events_fail_without_invented_tie_break(self):
        provider, *_ = self.provider([event(), event(status="NMCM")])
        with self.assertRaises(ProviderError):
            provider.load_events()

    def test_bounded_batches_and_overflow_fail_without_partial_metrics(self):
        provider, _, connection, cursor = self.provider([event(tail=f"T{i}") for i in range(4)],
                                                       max_rows=3, batch_size=2)
        with self.assertRaises(ProviderError):
            provider.load_events()
        self.assertEqual([call.args[0] for call in cursor.fetchmany.call_args_list], [2, 2])
        connection.close.assert_called_once()

    def test_exact_row_limit_is_accepted(self):
        provider, *_ = self.provider([event(tail="T1"), event(tail="T2")], max_rows=2, batch_size=1)
        self.assertEqual(len(provider.load_events()), 2)

    def test_bad_batch_shape_fails_closed(self):
        for batch in ((event(),), [event()] * 3):
            provider, _, _, cursor = self.provider(batch_size=2)
            cursor.fetchmany.side_effect = None
            cursor.fetchmany.return_value = batch
            with self.assertRaises(ProviderError):
                provider.load_events()

    def test_calendar_span_and_snapshot_size_are_bounded(self):
        rows = [event(), event("2026-01-03T08:00:00", tail="0002")]
        for options in ({"max_span_days": 2}, {"max_snapshot_rows": 3}):
            provider, *_ = self.provider(rows, **options)
            with self.assertRaises(ProviderError):
                provider.load_events()

    def test_connection_failure_and_login_timeout_are_safe(self):
        for error_type in (ConnectionError, TimeoutError):
            provider, factory, *_ = self.provider()
            sentinel = provider._credentials.password.get_secret_value()
            factory.side_effect = error_type(sentinel)
            with self.assertRaises(ProviderError) as caught:
                provider.load_events()
            self.assertNotIn(sentinel, str(caught.exception))
            self.assertIsNone(caught.exception.__context__)

    def test_query_and_fetch_timeouts_and_failures_close_resources(self):
        for operation in ("cursor", "execute", "fetchmany"):
            for error_type in (TimeoutError, RuntimeError):
                provider, _, connection, cursor = self.provider()
                target = connection.cursor if operation == "cursor" else getattr(cursor, operation)
                target.side_effect = error_type("FICTIONAL_PRIVATE_DETAIL")
                with self.assertRaises(ProviderError):
                    provider.load_events()
                connection.close.assert_called_once()
                if operation != "cursor":
                    cursor.close.assert_called_once()

    def test_cleanup_failures_still_close_other_resource_and_redact(self):
        for target_name in ("cursor", "connection"):
            provider, _, connection, cursor = self.provider()
            target = cursor if target_name == "cursor" else connection
            target.close.side_effect = RuntimeError("FICTIONAL_PRIVATE_DETAIL")
            with self.assertRaises(ProviderError):
                provider.load_events()
            cursor.close.assert_called_once()
            connection.close.assert_called_once()

    def test_lock_wait_is_bounded_and_never_connects_when_busy(self):
        provider, factory, *_ = self.provider(login_timeout=1)
        with patch("api.providers.SQL_LOCK") as lock:
            lock.acquire.return_value = False
            with self.assertRaises(ProviderError):
                provider.load_events()
            lock.acquire.assert_called_once_with(timeout=1)
            lock.release.assert_not_called()
        factory.assert_not_called()

    def test_lock_is_released_after_failure(self):
        provider, factory, *_ = self.provider()
        factory.side_effect = RuntimeError("FICTIONAL_PRIVATE_DETAIL")
        with self.assertRaises(ProviderError):
            provider.load_events()
        self.assertFalse(SQL_LOCK.locked())

    def test_native_connector_is_injectable_and_driver_pin_enforced(self):
        for version in ("2.3.3", "0.0.0"):
            factory, _, _ = mock_connection([event()])
            fake_driver = SimpleNamespace(__version__=version, connect=factory)
            with patch.dict(sys.modules, {"pymssql": fake_driver}):
                provider = create_provider(sql_config(), credentials())
                if version == "2.3.3":
                    self.assertEqual(len(provider.load_events()), 1)
                    factory.assert_called_once()
                else:
                    with self.assertRaises(ProviderError):
                        provider.load_events()
                    factory.assert_not_called()

    def test_error_trace_and_logs_do_not_retain_driver_details(self):
        import traceback

        provider, factory, *_ = self.provider()
        sentinel = provider._credentials.password.get_secret_value()
        factory.side_effect = RuntimeError(sentinel)
        output = io.StringIO()
        with redirect_stderr(output), redirect_stdout(output), self.assertNoLogs("api", level="DEBUG"):
            try:
                provider.load_events()
            except ProviderError:
                output.write(traceback.format_exc())
        self.assertNotIn(sentinel, output.getvalue())
        self.assertIn("SQL data unavailable", output.getvalue())


class SqlApiTests(unittest.TestCase):
    def app(self, rows=None):
        factory, connection, cursor = mock_connection(fixture_events() if rows is None else rows)
        app = create_app(sql_config(), credentials=credentials(), connection_factory=factory)
        return TestClient(app, raise_server_exceptions=False), factory, connection, cursor

    def test_health_reports_sql_without_connecting(self):
        client, factory, *_ = self.app()
        response = client.get("/health")
        self.assertEqual(response.json(), {"status": "ok", "source": "sql"})
        self.assertEqual(response.headers["x-fis4-data-source"], "sql")
        factory.assert_not_called()

    def test_sql_success_preserves_contracts_and_formula_lock(self):
        client, *_ = self.app()
        response = client.get("/api/v1/readiness/fleet?date=2026-01-01")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "sql")
        self.assertEqual(response.json()["metrics"]["svc_pct"], 75)
        self.assertEqual(response.json()["metrics"]["avail_pct"], 50)

    def test_each_sql_failure_never_loads_synthetic_or_leaks_details(self):
        for endpoint in ("readiness/fleet", "readiness/commands", "status-distribution"):
            for stage in ("connect", "query", "fetch"):
                client, factory, _, cursor = self.app()
                sentinel = client.app.state.provider._credentials.password.get_secret_value()
                target = factory if stage == "connect" else cursor.execute if stage == "query" else cursor.fetchmany
                target.side_effect = RuntimeError(sentinel)
                with patch.object(SyntheticCsvProvider, "load_events", side_effect=AssertionError("No fallback")) as synthetic:
                    response = client.get("/api/v1/" + endpoint)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json(), {"detail": "SQL data unavailable", "source": "sql"})
                self.assertEqual(response.headers["x-fis4-data-source"], "sql")
                self.assertNotIn(sentinel, response.text)
                synthetic.assert_not_called()

    def test_empty_sql_result_returns_404_with_sql_source(self):
        for endpoint in ("readiness/fleet", "readiness/commands", "status-distribution"):
            client, *_ = self.app([])
            response = client.get("/api/v1/" + endpoint)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["source"], "sql")
            self.assertNotIn("synthetic", response.text)

    def test_invalid_sql_record_returns_503(self):
        client, *_ = self.app([event(tail=1)])
        self.assertEqual(client.get("/api/v1/readiness/fleet").status_code, 503)

    def test_validation_reports_configured_source(self):
        client, *_ = self.app()
        response = client.get("/api/v1/readiness/fleet?path=FICTIONAL_PRIVATE_DETAIL")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["source"], "sql")
        self.assertNotIn("FICTIONAL_PRIVATE_DETAIL", response.text)

    def test_dependency_override_does_not_require_native_driver(self):
        app = create_app()
        provider = Mock(source="sql")
        provider.load_events.return_value = pd.DataFrame([event()])
        app.dependency_overrides[get_provider] = lambda: provider
        response = TestClient(app).get("/api/v1/readiness/fleet")
        self.assertEqual(response.json()["source"], "sql")
        self.assertEqual(response.headers["x-fis4-data-source"], "sql")
        provider.load_events.assert_called_once()

    def test_fleet_command_and_distribution_reconcile_for_each_day(self):
        for day in ("2026-01-01", "2026-01-02", "2026-01-03"):
            # Each request gets fresh connection/cursor mocks, as in the provider.
            client, *_ = self.app()
            fleet = client.get("/api/v1/readiness/fleet", params={"date": day}).json()["metrics"]
            client, *_ = self.app()
            commands = client.get("/api/v1/readiness/commands", params={"date": day}).json()["commands"]
            client, *_ = self.app()
            distribution = client.get("/api/v1/status-distribution", params={"date": day}).json()
            for column in ("total_tails", "fmc_tails", "pmc_tails", "nmcm_tails", "nmcs_tails", "depot_tails"):
                self.assertEqual(fleet[column], sum(row[column] for row in commands))
            self.assertEqual(sum(row["count"] for row in distribution["statuses"]), fleet["total_tails"])
            denominator = sum(row["total_tails"] - row["nmcs_tails"] - row["depot_tails"] for row in commands)
            weighted = sum(row["svc_pct"] * (row["total_tails"] - row["nmcs_tails"] - row["depot_tails"]) for row in commands)
            self.assertAlmostEqual(fleet["svc_pct"], weighted / denominator)
