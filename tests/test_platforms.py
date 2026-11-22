"""Platform metadata, Streamlit parity and cached API tests; entirely fictional."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from datetime import date, timedelta
from types import MappingProxyType
import unittest
from unittest.mock import Mock, patch

import pandas as pd
from pandas.testing import assert_frame_equal
from fastapi.testclient import TestClient

import readiness
from api.config import HistorySettings
from api.history import MAX_PLATFORMS, HistoryUnavailable, prepare_history
from api.main import MAX_SERIES_BYTES, create_app, get_provider
from api.providers import SyntheticCsvProvider
from simulator import SimulationConfig, generate
from simulator.contracts import COMMANDS, PLATFORMS

CONFIG = {"mode": "synthetic_history", "history": {"as_of": "2026-11-20", "seed": 42017}}
LIST = "/api/v1/platforms"
COMPARE = "/api/v1/readiness/history/platforms"
SERIES = COMPARE + "/series"
COUNTS = ("total_tails", "fmc_tails", "pmc_tails", "nmcs_tails", "nmcm_tails", "depot_tails")
PARAMS = {LIST: {}, COMPARE: {"date": "2026-11-20"},
          SERIES: {"end_date": "2026-11-20", "days": "30", "platform": "UH-60L"}}


class PlatformDomainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = SimulationConfig(date(2026, 11, 20), tails=16, years=1)
        cls.history = generate(cls.config)

    def test_stable_identity_across_commands_events_and_snapshots(self):
        h = self.history
        self.assertEqual(set(h.aircraft.platform), set(PLATFORMS))
        self.assertEqual(h.aircraft.groupby("platform").command.nunique().tolist(), [4] * 4)
        for frame in (h.events, h.snapshot):
            self.assertEqual(frame.groupby("tail").platform.nunique().unique().tolist(), [1])
            self.assertTrue(frame.platform.eq(frame["tail"].map(h.aircraft.set_index("tail").platform)).all())
            self.assertTrue(frame.command.eq(frame["tail"].map(h.aircraft.set_index("tail").command)).all())
        self.assertEqual(h.aircraft["tail"].iloc[0], "000001")

    def test_same_seed_determinism_and_other_seed_validity(self):
        other = generate(self.config)
        for name in ("aircraft", "events", "operations", "episodes", "actions", "snapshot"):
            assert_frame_equal(getattr(self.history, name), getattr(other, name))
        changed = generate(replace(self.config, seed=7))
        changed.validate()
        assert_frame_equal(self.history.aircraft[["tail", "command", "platform"]],
                           changed.aircraft[["tail", "command", "platform"]])
        self.assertFalse(self.history.events.equals(changed.events))

    def test_invalid_domain_platform_or_inconsistent_tail_mapping_rejected(self):
        for table, value in (("aircraft", "INVALID"), ("events", "AW139")):
            bad = deepcopy(self.history)
            getattr(bad, table).loc[0, "platform"] = value
            with self.assertRaises(ValueError):
                bad.validate()

    def test_intraday_missing_days_last_non_null_and_active_population_parity(self):
        # Current associations are already attached to ALL observations. No transfer invented.
        events = pd.DataFrame([
            ("2026-11-13T08:00:00", "000001", "FMC", "FICTIONAL_A", "UH-60L", 50),
            ("2026-11-13T17:00:00", "000001", "NMCS", "FICTIONAL_A", "UH-60L", None),
            ("2026-11-16T08:00:00", "000001", "PMCM", "FICTIONAL_A", "UH-60L", 20),
            ("2026-11-16T17:00:00", "000001", "FMC", "FICTIONAL_A", "UH-60L", None),
            ("2026-11-16T08:00:00", "000002", "PMCS", "FICTIONAL_B", "AH-64E", 10),
            ("2026-11-17T08:00:00", "000002", "FMC", "FICTIONAL_B", "AH-64E", 10),
            ("invalid", "000003", "FMC", "FICTIONAL_C", "AW139", 5),
        ], columns=["date", "tail", "status", "command", "platform", "hrs_to_insp"])
        snap = readiness.build_tail_daily_snapshot(readiness.coalesce_columns(events.iloc[::-1]))
        tail = snap[snap["tail"].eq("000001")].sort_values("date")
        self.assertEqual(tail.status.tolist(), ["NMCS", "NMCS", "NMCS", "FMC", "FMC"])
        self.assertEqual(tail.hrs_to_insp.tolist(), [50, 50, 50, 20, 20])
        self.assertEqual(tail.platform.unique().tolist(), ["UH-60L"])
        self.assertEqual(tail.command.unique().tolist(), ["FICTIONAL_A"])
        self.assertFalse(snap["tail"].eq("000003").any())
        self.assertEqual(snap.groupby("date")["tail"].nunique().tolist(), [1, 1, 1, 2, 2])
        self.assertEqual(len(snap[snap["tail"].eq("000002")]), 2)  # No backfill before first report.
        self.assertEqual(snap.date.max(), pd.Timestamp("2026-11-17"))  # No wall-clock extension.
        self.assertEqual(tail.status.eq("NMCS").sum(), 3)  # Occupancy days, one persistent occurrence.
        assert_frame_equal(snap, readiness.build_tail_daily_snapshot(
            readiness.coalesce_columns(pd.concat([events, events]))))

    def test_fis001_known_answers_and_zero_guards_with_platform(self):
        events = pd.DataFrame([("2026-11-20", f"{i:06d}", status, "FICTIONAL_A", "UH-60L")
                               for i, status in enumerate(readiness.CANONICAL_STATUSES, 1)],
                              columns=["date", "tail", "status", "command", "platform"])
        snap = readiness.build_tail_daily_snapshot(readiness.coalesce_columns(events))
        row = readiness.compute_jac_daily_metrics(snap).iloc[0]
        self.assertEqual((row.svc_pct, row.avail_pct), (75, 50))
        zero = snap[snap.status.isin(["NMCS", "DEPOT"])]
        self.assertEqual(readiness.compute_jac_daily_metrics(zero).iloc[0].svc_pct, 0)
        self.assertEqual(set(snap.status), set(readiness.CANONICAL_STATUSES))


class PlatformApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache = prepare_history(HistorySettings(**CONFIG["history"]))
        cls.snapshot = readiness.build_tail_daily_snapshot(readiness.coalesce_columns(cls.cache.events))

    def setUp(self):
        self.prepare = patch("api.history.prepare_history", return_value=replace(
            self.cache, events=self.cache.events.copy(deep=True)))
        self.preparer = self.prepare.start()
        self.addCleanup(self.prepare.stop)
        self.app = create_app(CONFIG)
        self.client = TestClient(self.app, raise_server_exceptions=False)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def get(self, route, **kwargs):
        return self.client.get(route, params={**PARAMS[route], **kwargs})

    def test_platform_list_is_bounded_sorted_and_associations_verified(self):
        for command in (None, *self.cache.commands):
            response = self.get(LIST, **({} if command is None else {"command": command}))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["X-FIS4-Data-Source"], "synthetic")
            self.assertEqual(response.json(), {"source": "synthetic", "command": command,
                                              "platforms": sorted(PLATFORMS)})
            self.assertLessEqual(len(response.json()["platforms"]), MAX_PLATFORMS)

    def test_default_population_and_three_date_command_platform_partitions(self):
        self.assertEqual(self.cache.events["tail"].nunique(), 160)
        self.assertEqual(len(self.cache.commands), 4)
        for day in (self.cache.start, self.cache.start + timedelta(days=730), self.cache.end):
            for command in (None, *self.cache.commands):
                args = {"date": day.isoformat(), **({} if command is None else {"command": command})}
                body = self.get(COMPARE, **args).json()
                expected = self.cache.records[(day, command)]
                self.assertEqual(expected.total_tails, 160 if command is None else 40)
                for field in COUNTS:
                    self.assertEqual(sum(row[field] for row in body["platforms"]), getattr(expected, field))
                for code, count in zip(readiness.CANONICAL_STATUSES, expected.statuses):
                    self.assertEqual(sum(row["status_counts"][code] for row in body["platforms"]), count)

    def test_combined_filters_match_distinct_tails_and_approved_engine(self):
        for day in (self.cache.start, self.cache.start + timedelta(days=730), self.cache.end):
            for command in self.cache.commands:
                for platform in self.cache.platforms:
                    selected = self.snapshot[self.snapshot.date.eq(pd.Timestamp(day))
                        & self.snapshot.command.eq(command) & self.snapshot.platform.eq(platform)]
                    expected = readiness.compute_jac_daily_metrics(selected).iloc[0]
                    response = self.get(COMPARE, date=day.isoformat(), command=command, platform=platform)
                    self.assertEqual(response.status_code, 200)
                    body = response.json()
                    self.assertEqual((body["command"], body["platform"]), (command, platform))
                    self.assertEqual(len(body["platforms"]), 1)
                    row = body["platforms"][0]
                    self.assertEqual(row["total_tails"], selected["tail"].nunique())
                    for field in (*COUNTS, "svc_pct", "avail_pct"):
                        self.assertEqual(row[field], expected[field])
                    for status in readiness.CANONICAL_STATUSES:
                        self.assertEqual(row["status_counts"][status], int(selected.status.eq(status).sum()))

    def test_all_series_windows_and_clipped_boundaries(self):
        for days in (30, 90, 180, 365):
            for offset in (0, 10, days - 1):
                end = self.cache.start + timedelta(days=offset)
                response = self.get(SERIES, end_date=end.isoformat(), days=str(days))
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertEqual(body["point_count"], min(days, offset + 1))
                self.assertEqual(body["start_date"], self.cache.start.isoformat())
                self.assertEqual(body["end_date"], end.isoformat())
                self.assertEqual([p["date"] for p in body["observations"]],
                                 [(self.cache.start + timedelta(days=i)).isoformat() for i in range(body["point_count"])])

    def test_every_day_of_full_window_reconciles_by_platform_and_command(self):
        for command in (None, *self.cache.commands):
            kwargs = {"days": "365", **({} if command is None else {"command": command})}
            series = [self.get(SERIES, platform=p, **kwargs).json() for p in self.cache.platforms]
            for i in range(365):
                points = [s["observations"][i] for s in series]
                day = date.fromisoformat(points[0]["date"])
                expected = self.cache.records[(day, command)]
                for field in COUNTS:
                    self.assertEqual(sum(p[field] for p in points), getattr(expected, field))
                for status, count in zip(readiness.CANONICAL_STATUSES, expected.statuses):
                    self.assertEqual(sum(p["status_counts"][status] for p in points), count)
                for platform, point in zip(self.cache.platforms, points):
                    record = self.cache.platform_records[(day, command, platform)]
                    self.assertEqual(point["svc_pct"], record.svc_pct)
                    self.assertEqual(point["avail_pct"], record.avail_pct)
                    self.assertEqual(point["pmc_tails"], point["status_counts"]["PMCM"] + point["status_counts"]["PMCS"])

    def test_final_series_point_equals_comparison_and_six_statuses_preserved(self):
        for platform in self.cache.platforms:
            row = self.get(COMPARE, platform=platform).json()["platforms"][0]
            point = self.get(SERIES, platform=platform).json()["observations"][-1]
            self.assertEqual({k: v for k, v in point.items() if k != "date"},
                             {k: v for k, v in row.items() if k != "platform"})
            self.assertEqual(set(row["status_counts"]), set(readiness.CANONICAL_STATUSES))

    def test_unknown_malformed_platforms_rejected_without_echo(self):
        for platform in ("", "uh-60l", "UNKNOWN", "X" * 33, "private-marker;bad", " UH-60L", "true"):
            for route in (COMPARE, SERIES):
                response = self.get(route, platform=platform)
                self.assertEqual(response.status_code, 422)
                self.assertNotIn("private-marker", response.text)

    def test_unknown_duplicate_and_invalid_command_parameters(self):
        for route in PARAMS:
            for suffix in ("&unknown=private-marker", "&command=UNKNOWN", "&command=private-marker;bad",
                           "&command=FICTIONAL_A&command=FICTIONAL_B"):
                from urllib.parse import urlencode
                response = self.client.get(route + "?" + urlencode(PARAMS[route]) + suffix)
                self.assertEqual(response.status_code, 422)
                self.assertNotIn("private-marker", response.text)
        for suffix in ("&platform=AW139", "&%70latform=UH-60L", "&days=90", "&end_date=2026-11-19"):
            from urllib.parse import urlencode
            self.assertEqual(self.client.get(SERIES + "?" + urlencode(PARAMS[SERIES]) + suffix).status_code, 422)
        self.assertEqual(self.get(LIST, date="2026-11-20").status_code, 422)

    def test_missing_required_invalid_dates_windows_and_out_of_history(self):
        for route in (COMPARE, SERIES):
            self.assertEqual(self.client.get(route).status_code, 422)
            field = "date" if route == COMPARE else "end_date"
            for value in ("2026-02-30", "20261120", "2026-1-1", "2026-11-20T01:00:00"):
                self.assertEqual(self.get(route, **{field: value}).status_code, 422)
            for value in (self.cache.start - timedelta(days=1), self.cache.end + timedelta(days=1)):
                self.assertEqual(self.get(route, **{field: value.isoformat()}).status_code, 404)
        for days in ("030", "31", "366", "true", "90.0", "-30", " 30"):
            self.assertEqual(self.get(SERIES, days=days).status_code, 422)
        self.assertEqual(self.client.get(SERIES, params={"end_date": "2026-11-20", "days": "30"}).status_code, 422)

    def test_no_internal_hierarchy_fields_or_identifiers_in_ordinary_responses(self):
        allowed = {LIST: {"source", "command", "platforms"},
                   COMPARE: {"source", "date", "command", "platform", "platforms"},
                   SERIES: {"source", "command", "platform", "requested_days", "start_date", "end_date", "point_count", "observations"}}
        for route in PARAMS:
            response = self.get(route)
            self.assertEqual(set(response.json()), allowed[route])
            self.assertNotIn("battalion", response.text.lower())
            self.assertNotIn("parent_force", response.text.lower())
            self.assertNotIn("000001", response.text)
            self.assertEqual(response.json()["source"], "synthetic")

    def test_csv_sql_and_dependency_overrides_cannot_expose_platform_data(self):
        from test_providers import credentials, sql_config
        factory = Mock(side_effect=AssertionError("SQL forbidden"))
        with patch("api.history.prepare_history", side_effect=AssertionError("Generation forbidden")) as prepare:
            for app in (create_app(), create_app(sql_config(), credentials=credentials(), connection_factory=factory)):
                with TestClient(app) as client:
                    schema = client.get("/openapi.json").json()
                    for route, params in PARAMS.items():
                        self.assertNotIn(route, schema["paths"])
                        response = client.get(route, params=params)
                        self.assertEqual(response.status_code, 404)
                        self.assertNotIn("platforms", response.json())
            factory.assert_not_called()
            prepare.assert_not_called()
        for replacement in (SyntheticCsvProvider(), create_app(sql_config(), credentials=credentials(), connection_factory=factory).state.provider):
            self.app.dependency_overrides[get_provider] = lambda: replacement
            for route in PARAMS:
                self.assertEqual(self.get(route).status_code, 404)
            factory.assert_not_called()

    def test_missing_cache_or_internal_point_returns_safe_503(self):
        for route in PARAMS:
            self.app.state.provider.close()
            self.assertEqual(self.get(route).status_code, 503)
        records = dict(self.cache.platform_records)
        del records[(self.cache.end - timedelta(days=10), None, "UH-60L")]
        partial = replace(self.cache, platform_records=MappingProxyType(records))
        with patch("api.history.prepare_history", return_value=partial), TestClient(create_app(CONFIG)) as client:
            response = client.get(SERIES, params=PARAMS[SERIES])
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json(), {"detail": "Synthetic history unavailable"})
        del records[(self.cache.end, None, "UH-60L")]
        partial = replace(self.cache, platform_records=MappingProxyType(records))
        with patch("api.history.prepare_history", return_value=partial), TestClient(create_app(CONFIG)) as client:
            self.assertEqual(client.get(COMPARE, params=PARAMS[COMPARE]).status_code, 503)

    def test_repeated_concurrent_queries_do_not_regenerate_or_aggregate(self):
        with ExitStack() as stack:
            for name in ("api.history.prepare_history", "simulator.generate", "readiness.build_tail_daily_snapshot",
                         "readiness.compute_jac_daily_metrics", "api.history.SyntheticHistoryProvider.load_events",
                         "pandas.DataFrame.groupby"):
                stack.enter_context(patch(name, side_effect=AssertionError("Warm recomputation forbidden")))
            def query(index):
                route = tuple(PARAMS)[index % 3]
                response = self.get(route, command=COMMANDS[index % 4])
                self.assertEqual(response.status_code, 200)
                return response.json()
            with ThreadPoolExecutor(max_workers=6) as pool:
                self.assertEqual(len(list(pool.map(query, range(24)))), 24)
        self.preparer.assert_called_once()

    def test_cache_is_immutable_and_instances_are_isolated(self):
        with self.assertRaises(TypeError):
            self.cache.platform_records[(self.cache.end, None, "UH-60L")] = None
        with self.assertRaises(TypeError):
            self.cache.platforms_by_command[None] = ()
        with self.assertRaises(FrozenInstanceError):
            self.cache.platform_records[(self.cache.end, None, "UH-60L")].total_tails = 0
        before = self.get(COMPARE).json()
        changed = self.get(COMPARE).json()
        changed["platforms"][0]["status_counts"]["FMC"] = 999
        self.assertEqual(self.get(COMPARE).json(), before)
        with TestClient(create_app(CONFIG)) as other:
            self.assertIsNot(other.app.state.provider, self.app.state.provider)
            other.app.state.provider.close()
            self.assertEqual(other.get(LIST).status_code, 503)
            self.assertEqual(self.get(LIST).status_code, 200)

    def test_payload_bound_and_get_only_openapi_models(self):
        self.assertEqual(MAX_SERIES_BYTES, 262144)
        for route in PARAMS:
            response = self.get(route)
            self.assertLessEqual(len(response.content), MAX_SERIES_BYTES)
            with patch("api.main.MAX_SERIES_BYTES", len(response.content) - 1):
                failed = self.get(route)
                self.assertEqual(failed.status_code, 500)
                self.assertEqual(failed.json(), {"detail": "Internal server error"})
            self.assertEqual(self.client.post(route, json={}).status_code, 405)
        schema = self.client.get("/openapi.json").json()
        self.assertEqual(schema["components"]["schemas"]["PlatformListResponse"]["properties"]["platforms"]["maxItems"], 32)
        self.assertEqual(schema["components"]["schemas"]["PlatformComparisonResponse"]["properties"]["platforms"]["maxItems"], 32)
        for route in PARAMS:
            self.assertEqual(set(schema["paths"][route]), {"get"})
            for code in ("404", "422", "500", "503"):
                self.assertEqual(schema["paths"][route]["get"]["responses"][code]["content"]["application/json"]["schema"]["$ref"],
                                 "#/components/schemas/ErrorResponse")

    def test_existing_routes_keep_exact_response_contracts(self):
        for route in ("/api/v1/readiness/history", "/api/v1/readiness/fleet"):
            response = self.client.get(route, params={"date": "2026-11-20"})
            self.assertEqual(set(response.json()), {"source", "date", "command", "metrics"})
            self.assertEqual(response.json()["metrics"], self.cache.records[(self.cache.end, None)].metrics())
        response = self.client.get("/api/v1/readiness/history/series", params={"end_date": "2026-11-20", "days": "30"})
        self.assertEqual(set(response.json()), {"source", "command", "requested_days", "start_date", "end_date", "point_count", "observations"})
        self.assertEqual(self.client.get("/api/v1/readiness/history", params={"date": "2026-11-20", "platform": "UH-60L"}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
