"""Bounded cached history series; fictional full-world fixture, no live SQL."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from dataclasses import FrozenInstanceError, replace
from datetime import date, timedelta
from types import MappingProxyType
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

import readiness
from api.config import HistorySettings
from api.history import HistoryUnavailable, SERIES_WINDOWS, SyntheticHistoryProvider, prepare_history
from api.main import MAX_SERIES_BYTES, create_app, get_provider
from api.providers import SyntheticCsvProvider


CONFIG = {"mode": "synthetic_history", "history": {"as_of": "2026-11-20", "seed": 42017}}
ROUTE = "/api/v1/readiness/history/series"
FIELDS = ("total_tails", "fmc_tails", "pmc_tails", "nmcs_tails", "nmcm_tails", "depot_tails")


class HistorySeriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache = prepare_history(HistorySettings(**CONFIG["history"]))

    def setUp(self):
        self.prepare = patch("api.history.prepare_history", return_value=replace(
            self.cache, events=self.cache.events.copy(deep=True)))
        self.prepare_mock = self.prepare.start()
        self.addCleanup(self.prepare.stop)
        self.app = create_app(CONFIG)
        self.client = TestClient(self.app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def get(self, days=30, end=None, command=None):
        params = {"end_date": (end or self.cache.end).isoformat(), "days": str(days)}
        if command is not None:
            params["command"] = command
        return self.client.get(ROUTE, params=params)

    def test_all_windows_are_inclusive_chronological_and_complete(self):
        for days in SERIES_WINDOWS:
            response = self.get(days)
            self.assertEqual(response.status_code, 200)
            body = response.json()
            start = self.cache.end - timedelta(days=days - 1)
            self.assertEqual(body["source"], "synthetic")
            self.assertIsNone(body["command"])
            self.assertEqual(body["requested_days"], days)
            self.assertEqual(body["start_date"], start.isoformat())
            self.assertEqual(body["end_date"], self.cache.end.isoformat())
            self.assertEqual(body["point_count"], days)
            self.assertEqual([p["date"] for p in body["observations"]],
                             [(start + timedelta(days=i)).isoformat() for i in range(days)])

    def test_clipped_start_and_exact_first_full_window(self):
        for days in SERIES_WINDOWS:
            for offset in (0, 10, days - 1):
                body = self.get(days, self.cache.start + timedelta(days=offset)).json()
                self.assertEqual(body["start_date"], self.cache.start.isoformat())
                self.assertEqual(body["point_count"], offset + 1)
                self.assertEqual(len(body["observations"]), offset + 1)

    def test_end_date_boundaries_reject_outside_instead_of_clipping_end(self):
        for end in (self.cache.start - timedelta(days=1), self.cache.end + timedelta(days=1),
                    date(1, 1, 1), date(9999, 12, 31)):
            response = self.get(end=end)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {"detail": "No synthetic snapshot for the requested selection"})

    def test_required_real_iso_date_and_window(self):
        for params in ({}, {"days": "30"}, {"end_date": "2026-11-20"}):
            self.assertEqual(self.client.get(ROUTE, params=params).status_code, 422)
        for value in ("", "bad", "2026-02-30", "2026-1-01", "20261120", "2026-11-20T00:00:00", "1795132800"):
            response = self.client.get(ROUTE, params={"end_date": value, "days": "30"})
            self.assertEqual(response.status_code, 422)

    def test_days_are_strict_canonical_supported_values(self):
        for value in ("0", "-30", "1", "31", "366", "99999999999", "30.0", "030", "+30", " 30", "true", ""):
            response = self.client.get(ROUTE, params={"end_date": "2026-11-20", "days": value})
            self.assertEqual(response.status_code, 422)

    def test_all_commands_filter_and_preserve_six_status_counts(self):
        for command in self.cache.commands:
            body = self.get(90, command=command).json()
            self.assertEqual(body["command"], command)
            for point in body["observations"]:
                self.assertEqual(point["total_tails"], 40)
                counts = point["status_counts"]
                self.assertEqual(tuple(counts), readiness.CANONICAL_STATUSES)
                self.assertEqual(sum(counts.values()), 40)
                self.assertEqual(point["pmc_tails"], counts["PMCM"] + counts["PMCS"])
                for field, code in (("fmc_tails", "FMC"), ("nmcs_tails", "NMCS"),
                                    ("nmcm_tails", "NMCM"), ("depot_tails", "DEPOT")):
                    self.assertEqual(point[field], counts[code])

    def test_fleet_command_reconciliation_for_every_day_of_every_window(self):
        for days in SERIES_WINDOWS:
            fleet = self.get(days).json()["observations"]
            commands = [self.get(days, command=c).json()["observations"] for c in self.cache.commands]
            for index, point in enumerate(fleet):
                for field in FIELDS:
                    self.assertEqual(point[field], sum(rows[index][field] for rows in commands))
                for code in readiness.CANONICAL_STATUSES:
                    self.assertEqual(point["status_counts"][code], sum(rows[index]["status_counts"][code] for rows in commands))
                self.assertTrue(all(rows[index]["date"] == point["date"] for rows in commands))

    def test_all_points_equal_cache_and_preserve_fis001_denominator(self):
        observed_nmcm = False
        for command in (None, *self.cache.commands):
            for point in self.get(365, command=command).json()["observations"]:
                record = self.cache.records[(date.fromisoformat(point["date"]), command)]
                for field, value in record.metrics().items():
                    self.assertEqual(point[field], value)
                self.assertEqual(tuple(point["status_counts"].values()), record.statuses)
                ready = point["fmc_tails"] + point["pmc_tails"]
                denominator = point["total_tails"] - point["nmcs_tails"] - point["depot_tails"]
                self.assertAlmostEqual(point["svc_pct"], ready / denominator * 100 if denominator > 0 else 0)
                self.assertAlmostEqual(point["avail_pct"], ready / point["total_tails"] * 100)
                observed_nmcm |= point["nmcm_tails"] > 0 and ready > 0
        self.assertTrue(observed_nmcm)

    def test_series_and_existing_single_day_contract_agree(self):
        for point in self.get(30, command="FICTIONAL_B").json()["observations"]:
            old = self.client.get("/api/v1/readiness/history", params={"date": point["date"], "command": "FICTIONAL_B"})
            self.assertEqual(old.status_code, 200)
            self.assertEqual(old.json()["metrics"], {key: point[key] for key in old.json()["metrics"]})

    def test_invalid_unknown_commands_and_parameters_do_not_echo_input(self):
        for command in ("", "fictional_a", "UNKNOWN", "A" * 33, "private-marker;bad"):
            response = self.get(command=command)
            self.assertEqual(response.status_code, 422)
            self.assertNotIn("private-marker", response.text)
        response = self.client.get(ROUTE, params={"end_date": "2026-11-20", "days": "30", "extra": "private-marker"})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("private-marker", response.text)

    def test_duplicate_keys_including_encoded_alias_are_rejected(self):
        for suffix in ("&days=30", "&days=90", "&%64ays=180", "&end_date=2026-11-19",
                       "&command=FICTIONAL_A&command=FICTIONAL_B", "&command=FICTIONAL_A&command=FICTIONAL_A"):
            response = self.client.get(ROUTE + "?end_date=2026-11-20&days=30" + suffix)
            self.assertEqual(response.status_code, 422)

    def test_csv_and_sql_modes_neither_expose_route_nor_initialize_history(self):
        from test_providers import credentials, sql_config
        factory = Mock(side_effect=AssertionError("No SQL connection"))
        self.prepare_mock.reset_mock()
        apps = (create_app(), create_app(sql_config(), credentials=credentials(), connection_factory=factory))
        for app in apps:
            with TestClient(app) as client:
                response = client.get(ROUTE + "?end_date=2026-11-20&days=30")
                self.assertEqual(response.status_code, 404)
                self.assertNotIn("observations", response.json())
                self.assertNotIn(ROUTE, client.get("/openapi.json").json()["paths"])
        factory.assert_not_called()
        self.prepare_mock.assert_not_called()

    def test_dependency_override_cannot_leak_history_into_other_providers(self):
        for provider in (SyntheticCsvProvider(), Mock(source="sql")):
            self.app.dependency_overrides[get_provider] = lambda: provider
            response = self.get()
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.headers["X-FIS4-Data-Source"], provider.source)
            self.assertNotIn("observations", response.json())

    def test_missing_lifecycle_or_closed_cache_returns_safe_503(self):
        app = create_app(CONFIG)
        with TestClient(app, raise_server_exceptions=False) as client:
            app.state.provider.close()
            response = client.get(ROUTE + "?end_date=2026-11-20&days=30")
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json(), {"detail": "Synthetic history unavailable"})
        client = TestClient(create_app(CONFIG), raise_server_exceptions=False)
        try:
            response = client.get(ROUTE + "?end_date=2026-11-20&days=30")
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("observations", response.json())
        finally:
            client.close()

    def test_missing_internal_record_rejects_entire_series(self):
        records = dict(self.cache.records)
        del records[(self.cache.end - timedelta(days=10), None)]
        partial = replace(self.cache, records=MappingProxyType(records))
        with patch("api.history.prepare_history", return_value=partial), TestClient(create_app(CONFIG)) as client:
            response = client.get(ROUTE + "?end_date=2026-11-20&days=30")
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json(), {"detail": "Synthetic history unavailable"})

    def test_repeated_concurrent_queries_do_not_regenerate_or_aggregate(self):
        with ExitStack() as stack:
            for name in ("api.history.prepare_history", "simulator.generate", "readiness.build_tail_daily_snapshot",
                         "readiness.compute_jac_daily_metrics", "readiness.compute_command_latest_metrics",
                         "api.history.SyntheticHistoryProvider.load_events", "pandas.DataFrame.groupby"):
                stack.enter_context(patch(name, side_effect=AssertionError("Warm recomputation forbidden")))
            def query(index):
                days = SERIES_WINDOWS[index % 4]
                command = self.cache.commands[index % 4] if index % 2 else None
                response = self.get(days, command=command)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["point_count"], days)
                return response.json()["command"]
            for index in range(8):
                query(index)
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(query, range(24)))
            self.assertEqual(len(results), 24)
        self.prepare_mock.assert_called_once()

    def test_provider_bounds_and_read_only_series_snapshot(self):
        provider = self.app.state.provider
        for days in (0, 31, 366, True, "30"):
            with self.assertRaises(ValueError):
                provider.read_series(self.cache.end, days)
        series = provider.read_series(self.cache.end, 30)
        self.assertIs(series.points[-1][1], provider.read(self.cache.end))
        with self.assertRaises(FrozenInstanceError):
            series.start = self.cache.end
        before = self.get().json()
        changed = self.get().json()
        changed["observations"][0]["status_counts"]["FMC"] = 999
        self.assertEqual(self.get().json(), before)
        # A captured immutable cache reference remains complete during shutdown.
        provider.close()
        with patch.object(provider, "_ready", return_value=self.cache) as ready:
            self.assertEqual(len(provider.read_series(self.cache.end, 365).points), 365)
            ready.assert_called_once()
        with self.assertRaises(HistoryUnavailable):
            provider.read_series(self.cache.end, 30)

    def test_payload_size_cap_is_enforced_without_truncation(self):
        self.assertEqual(MAX_SERIES_BYTES, 262144)
        for command in (None, *self.cache.commands):
            response = self.get(365, command=command)
            self.assertLessEqual(len(response.content), MAX_SERIES_BYTES)
            self.assertEqual(int(response.headers["content-length"]), len(response.content))
        size = len(self.get(365).content)
        with patch("api.main.MAX_SERIES_BYTES", size):
            self.assertEqual(self.get(365).status_code, 200)
        with patch("api.main.MAX_SERIES_BYTES", size - 1):
            response = self.get(365)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), {"detail": "Internal server error"})
        self.assertEqual(self.get(365).json()["point_count"], 365)

    def test_openapi_documents_bounded_model_validation_and_get_only(self):
        schema = self.client.get("/openapi.json").json()
        route = schema["paths"][ROUTE]
        self.assertEqual(set(route), {"get"})
        response = route["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        self.assertEqual(response["$ref"], "#/components/schemas/HistorySeriesResponse")
        models = schema["components"]["schemas"]
        self.assertEqual(models["HistorySeriesResponse"]["properties"]["observations"]["maxItems"], 365)
        self.assertEqual(set(models["CanonicalStatusCounts"]["properties"]), set(readiness.CANONICAL_STATUSES))
        for code in ("404", "422", "500", "503"):
            self.assertEqual(route["get"]["responses"][code]["content"]["application/json"]["schema"]["$ref"],
                             "#/components/schemas/ErrorResponse")
        self.assertEqual(self.client.post(ROUTE, json={}).status_code, 405)


if __name__ == "__main__":
    unittest.main()
