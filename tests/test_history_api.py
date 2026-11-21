"""History-mode API/lifecycle tests; real fictional world plus isolated cache mocks."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
from datetime import date, timedelta
from threading import Barrier, Event
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

import readiness
from api.config import HistorySettings, ProviderConfigurationError, parse_config
from api.history import HistoryUnavailable, SyntheticHistoryProvider, prepare_history
from api.main import create_app, get_provider
from api.providers import SyntheticCsvProvider, create_provider


CONFIG = {"mode": "synthetic_history", "history": {"as_of": "2026-11-20", "seed": 42017}}
ROUTE = "/api/v1/readiness/history"
FIELDS = ("total_tails", "fmc_tails", "pmc_tails", "nmcm_tails", "nmcs_tails", "depot_tails")


class HistoricalApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # One REAL full 160-tail world per test-suite execution. Other tests clone
        # immutable prepared data to exercise app lifecycle without needless reruns.
        cls.cache = prepare_history(HistorySettings(**CONFIG["history"]))

    def prepared(self):
        return replace(self.cache, events=self.cache.events.copy(deep=True))

    def test_default_provider_and_default_contracts_remain_unchanged(self):
        with patch("api.history.prepare_history", side_effect=AssertionError("Unexpected history")) as prepare:
            app = create_app()
            self.assertIsInstance(app.state.provider, SyntheticCsvProvider)
            with TestClient(app) as client:
                self.assertEqual(client.get("/health").json(), {"status": "ok", "source": "synthetic"})
                self.assertEqual(client.get("/api/v1/readiness/fleet").json()["metrics"]["total_tails"], 7)
                self.assertEqual(client.get(ROUTE, params={"date": "2026-11-20"}).status_code, 404)
                self.assertNotIn(ROUTE, client.get("/openapi.json").json()["paths"])
            prepare.assert_not_called()

    def test_history_configuration_is_explicit_and_strict(self):
        invalid = [{"mode": "synthetic_history"}, {"history": CONFIG["history"]},
                   {**CONFIG, "sql": {"server": "example.invalid", "database": "DEMO"}}]
        for history in ({"as_of": "2026-02-30"}, {"as_of": "2026-1-1"}, {"as_of": "1999-01-01"},
                        {"as_of": "2101-01-01"}, {"as_of": "2026-11-20", "seed": True},
                        {"as_of": "2026-11-20", "seed": "1"}, {"as_of": "2026-11-20", "seed": -1},
                        {"as_of": "2026-11-20", "tails": 4}, {"as_of": "2026-11-20", "years": 1}):
            invalid.append({"mode": "synthetic_history", "history": history})
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ProviderConfigurationError):
                parse_config(values)
        with self.assertRaises(ProviderConfigurationError):
            create_provider(parse_config(CONFIG), connection_factory=Mock())

    def test_factory_is_lazy_and_reports_synthetic_source(self):
        with patch("api.history.prepare_history") as prepare:
            provider = create_provider(parse_config(CONFIG))
            self.assertIsInstance(provider, SyntheticHistoryProvider)
            self.assertEqual(provider.source, "synthetic")
            prepare.assert_not_called()
        with self.assertRaises(HistoryUnavailable):
            provider.load_events()

    def test_exact_population_four_commands_and_every_day_cached(self):
        cache = self.cache
        self.assertEqual(cache.events["tail"].nunique(), 160)
        self.assertEqual(cache.events["tail"].min(), "000001")
        self.assertEqual(cache.commands, ("FICTIONAL_A", "FICTIONAL_B", "FICTIONAL_C", "FICTIONAL_D"))
        days = (cache.end - cache.start).days + 1
        self.assertEqual(days, 1461)
        self.assertEqual(len(cache.records), days * 5)
        for offset in range(days):
            day = cache.start + timedelta(days=offset)
            self.assertEqual(cache.records[(day, None)].total_tails, 160)
            for command in cache.commands:
                self.assertEqual(cache.records[(day, command)].total_tails, 40)

    def test_inclusive_history_boundaries_and_out_of_range_dates(self):
        with patch("api.history.prepare_history", return_value=self.prepared()), TestClient(create_app(CONFIG)) as client:
            for day in (self.cache.start, self.cache.end):
                response = client.get(ROUTE, params={"date": day.isoformat()})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["date"], day.isoformat())
            for day in (self.cache.start - timedelta(days=1), self.cache.end + timedelta(days=1), date(1, 1, 1)):
                response = client.get(ROUTE, params={"date": day.isoformat()})
                self.assertEqual(response.status_code, 404)

    def test_date_required_and_calendar_validation_is_strict(self):
        with patch("api.history.prepare_history", return_value=self.prepared()), TestClient(create_app(CONFIG)) as client:
            for query in ({}, {"date": "bad"}, {"date": "2026-02-30"}, {"date": "2026-1-1"},
                          {"date": "2026-11-20T00:00:00"}, {"date": "1795132800"}, {"date": ""}):
                self.assertEqual(client.get(ROUTE, params=query).status_code, 422)

    def test_invalid_and_unknown_commands_rejected_without_echo(self):
        with patch("api.history.prepare_history", return_value=self.prepared()), TestClient(create_app(CONFIG)) as client:
            for command in ("", "fictional_a", "UNKNOWN", "A" * 33, "private-marker;bad"):
                response = client.get(ROUTE, params={"date": "2026-11-20", "command": command})
                self.assertEqual(response.status_code, 422)
                self.assertNotIn("private-marker", response.text)

    def test_unknown_and_duplicate_parameters_rejected(self):
        with patch("api.history.prepare_history", return_value=self.prepared()), TestClient(create_app(CONFIG)) as client:
            for suffix in ("&extra=private-marker", "&date=2026-11-19", "&command=FICTIONAL_A&command=FICTIONAL_B"):
                response = client.get(ROUTE + "?date=2026-11-20" + suffix)
                self.assertEqual(response.status_code, 422)
                self.assertNotIn("private-marker", response.text)

    def test_three_dates_fleet_and_command_reconcile(self):
        with patch("api.history.prepare_history", return_value=self.prepared()), TestClient(create_app(CONFIG)) as client:
            for day in (self.cache.start, self.cache.start + timedelta(days=730), self.cache.end):
                params = {"date": day.isoformat()}
                fleet = client.get(ROUTE, params=params).json()
                commands = [client.get(ROUTE, params={**params, "command": c}).json() for c in self.cache.commands]
                self.assertEqual(fleet["source"], "synthetic")
                self.assertIsNone(fleet["command"])
                for field in FIELDS:
                    self.assertEqual(fleet["metrics"][field], sum(c["metrics"][field] for c in commands))

    def test_nmcm_denominator_and_percentages_match_approved_engine(self):
        # Independent existing-engine reconstruction from retained readiness events.
        snapshot = readiness.build_tail_daily_snapshot(readiness.coalesce_columns(self.cache.events))
        expected = readiness.compute_jac_daily_metrics(snapshot).set_index("date")
        day = next(day for (day, command), row in self.cache.records.items()
                   if command is None and row.nmcm_tails and row.fmc_tails)
        with patch("api.history.prepare_history", return_value=self.prepared()), TestClient(create_app(CONFIG)) as client:
            actual = client.get(ROUTE, params={"date": day.isoformat()}).json()["metrics"]
            for field in (*FIELDS, "svc_pct", "avail_pct"):
                self.assertEqual(actual[field], expected.loc[str(day), field])
            self.assertAlmostEqual(actual["svc_pct"],
                                   (actual["fmc_tails"] + actual["pmc_tails"]) /
                                   (actual["total_tails"] - actual["depot_tails"] - actual["nmcs_tails"]) * 100)

    def test_old_routes_same_shapes_and_same_selected_history(self):
        with patch("api.history.prepare_history", return_value=self.prepared()), TestClient(create_app(CONFIG)) as client:
            params = {"date": "2026-11-20", "command": "FICTIONAL_B"}
            fleet = client.get("/api/v1/readiness/fleet", params=params).json()
            self.assertEqual(fleet, client.get(ROUTE, params=params).json())
            command = client.get("/api/v1/readiness/commands", params=params).json()["commands"][0]
            self.assertEqual(command.pop("command"), "FICTIONAL_B")
            self.assertEqual(command, fleet["metrics"])
            dist = client.get("/api/v1/status-distribution", params=params).json()
            self.assertEqual(dist["total_tails"], 40)
            self.assertEqual([r["status"] for r in dist["statuses"]], list(readiness.CANONICAL_STATUSES))
            self.assertEqual(sum(r["count"] for r in dist["statuses"]), 40)
            self.assertEqual(client.get("/api/v1/readiness/fleet").json()["date"], "2026-11-20")
            self.assertEqual(client.get("/api/v1/readiness/fleet?command=UNKNOWN").status_code, 404)

    def test_repeated_requests_initialize_only_once_without_aggregation(self):
        with patch("api.history.prepare_history", return_value=self.prepared()) as prepare:
            app = create_app(CONFIG)
            with TestClient(app) as client:
                prepare.assert_called_once()
                with patch("api.history.prepare_history", side_effect=AssertionError("Regeneration")), \
                     patch("simulator.generate", side_effect=AssertionError("Regeneration")), \
                     patch("readiness.build_tail_daily_snapshot", side_effect=AssertionError("Snapshot rebuild")), \
                     patch("readiness.compute_jac_daily_metrics", side_effect=AssertionError("Aggregation")), \
                     patch("readiness.compute_command_latest_metrics", side_effect=AssertionError("Aggregation")):
                    for _ in range(3):
                        for path in (ROUTE, "/api/v1/readiness/fleet", "/api/v1/readiness/commands", "/api/v1/status-distribution"):
                            self.assertEqual(client.get(path, params={"date": "2026-11-20"}).status_code, 200)

    def test_concurrent_initialize_publishes_one_cache(self):
        provider = SyntheticHistoryProvider(HistorySettings(**CONFIG["history"]))
        gate, entered, release = Barrier(8), Event(), Event()
        def slow_prepare(settings):
            entered.set()
            if not release.wait(timeout=5):
                raise RuntimeError("Test release timed out")
            return self.prepared()
        def initialize():
            gate.wait(timeout=5)
            provider.initialize()
        with patch("api.history.prepare_history", side_effect=slow_prepare) as prepare:
            with ThreadPoolExecutor(max_workers=8) as pool:
                futures = [pool.submit(initialize) for _ in range(24)]
                self.assertTrue(entered.wait(timeout=5))
                release.set()
                for future in futures:
                    future.result(timeout=10)
            prepare.assert_called_once()
        self.assertEqual(provider.read(self.cache.end).total_tails, 160)

    def test_concurrent_http_reads_return_consistent_isolated_responses(self):
        with patch("api.history.prepare_history", return_value=self.prepared()), TestClient(create_app(CONFIG)) as client:
            def read(index):
                command = self.cache.commands[index % 4]
                return client.get(ROUTE, params={"date": "2026-11-20", "command": command}).json()
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(read, range(32)))
            for index, body in enumerate(results):
                self.assertEqual(body["command"], self.cache.commands[index % 4])
                self.assertEqual(body["metrics"]["total_tails"], 40)

    def test_read_only_results_and_defensive_event_copy(self):
        provider = SyntheticHistoryProvider(HistorySettings(**CONFIG["history"]))
        with patch("api.history.prepare_history", return_value=self.prepared()):
            provider.initialize()
        record = provider.read(self.cache.end)
        with self.assertRaises(FrozenInstanceError):
            record.total_tails = 0
        copied = record.metrics()
        copied["total_tails"] = 0
        events = provider.load_events()
        events.loc[:, "status"] = "INVALID"
        self.assertEqual(provider.read(self.cache.end).total_tails, 160)
        self.assertFalse(provider.load_events().status.eq("INVALID").any())
        with self.assertRaises(TypeError):
            self.cache.records[(self.cache.end, None)] = record

    def test_app_instances_configs_and_shutdown_are_isolated(self):
        first = create_app(CONFIG)
        second = create_app({**CONFIG, "history": {**CONFIG["history"], "seed": 7}})
        seen = []
        def prepare(settings):
            seen.append(settings.seed)
            return self.prepared()
        with patch("api.history.prepare_history", side_effect=prepare) as prepare:
            with TestClient(first) as one, TestClient(second) as two:
                self.assertEqual(one.get(ROUTE + "?date=2026-11-20").status_code, 200)
                self.assertEqual(two.get(ROUTE + "?date=2026-11-20").status_code, 200)
                first.state.provider.close()
                self.assertEqual(one.get(ROUTE + "?date=2026-11-20").status_code, 503)
                self.assertEqual(two.get(ROUTE + "?date=2026-11-20").status_code, 200)
            self.assertEqual(prepare.call_count, 2)
        self.assertEqual(seen, [42017, 7])
        self.assertIsNot(first.state.provider, second.state.provider)

    def test_shutdown_clears_cache_and_new_lifecycle_reinitializes(self):
        app = create_app(CONFIG)
        with patch("api.history.prepare_history", side_effect=lambda _: self.prepared()) as prepare:
            for _ in range(2):
                with TestClient(app) as client:
                    self.assertEqual(client.get(ROUTE + "?date=2026-11-20").status_code, 200)
                with self.assertRaises(HistoryUnavailable):
                    app.state.provider.read(self.cache.end)
            self.assertEqual(prepare.call_count, 2)

    def test_initialization_failure_is_safe_sticky_and_never_falls_back(self):
        app = create_app(CONFIG)
        marker = "fictional-private-marker"
        with patch("api.history.prepare_history", side_effect=ValueError(marker)) as prepare:
            for _ in range(2):
                with self.assertRaises(HistoryUnavailable) as caught:
                    with TestClient(app):
                        self.fail("Startup must fail")
                self.assertNotIn(marker, str(caught.exception))
                self.assertIsNone(caught.exception.__context__)
            prepare.assert_called_once()

    def test_without_lifespan_history_requests_fail_safely(self):
        app = create_app(CONFIG)
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(ROUTE + "?date=2026-11-20")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "Synthetic history unavailable"})
        self.assertEqual(response.headers["X-FIS4-Data-Source"], "synthetic")
        client.close()

    def test_sql_mode_has_no_history_route_and_does_not_generate_or_connect(self):
        # Dummy credentials are generated by the existing mocked-SQL helper.
        from test_providers import credentials, sql_config
        factory = Mock(side_effect=AssertionError("No live SQL"))
        with patch("api.history.prepare_history", side_effect=AssertionError("No history")) as prepare:
            with TestClient(create_app(sql_config(), credentials=credentials(), connection_factory=factory)) as client:
                response = client.get(ROUTE + "?date=2026-11-20")
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.headers["X-FIS4-Data-Source"], "sql")
                self.assertNotIn(ROUTE, client.get("/openapi.json").json()["paths"])
            prepare.assert_not_called()
            factory.assert_not_called()

    def test_provider_override_cannot_expose_history_to_non_history_source(self):
        app = create_app(CONFIG)
        with patch("api.history.prepare_history", return_value=self.prepared()), TestClient(app) as client:
            app.dependency_overrides[get_provider] = lambda: SyntheticCsvProvider()
            self.assertEqual(client.get(ROUTE + "?date=2026-11-20").status_code, 404)
            self.assertEqual(client.get("/api/v1/readiness/fleet").json()["metrics"]["total_tails"], 7)

    def test_history_openapi_and_read_only_route_contract(self):
        with patch("api.history.prepare_history", return_value=self.prepared()), TestClient(create_app(CONFIG)) as client:
            schema = client.get("/openapi.json").json()
            route = schema["paths"][ROUTE]
            self.assertEqual(set(route), {"get"})
            self.assertEqual(route["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"],
                             "#/components/schemas/FleetResponse")
            self.assertEqual(client.post(ROUTE, json={}).status_code, 405)


if __name__ == "__main__":
    unittest.main()
