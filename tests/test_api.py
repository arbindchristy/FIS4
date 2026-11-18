import unittest
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from api.main import create_app, get_snapshot


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_health_is_liveness_and_synthetic(self):
        with patch("api.main.pd.read_csv", side_effect=AssertionError("must not load")):
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "source": "synthetic"})

    def test_fleet_first_day_formula_lock_and_contract(self):
        response = self.client.get("/api/v1/readiness/fleet?date=2026-01-01")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertEqual(response.json(), {
            "source": "synthetic", "date": "2026-01-01", "command": None,
            "metrics": {"total_tails": 6, "fmc_tails": 1, "pmc_tails": 2,
                        "nmcm_tails": 1, "nmcs_tails": 1, "depot_tails": 1,
                        "svc_pct": 75.0, "avail_pct": 50.0}})

    def test_default_uses_latest_fixture_date(self):
        body = self.client.get("/api/v1/readiness/fleet").json()
        self.assertEqual(body["date"], "2026-01-03")
        self.assertEqual(body["metrics"]["total_tails"], 7)
        self.assertAlmostEqual(body["metrics"]["svc_pct"], 500 / 6)
        self.assertAlmostEqual(body["metrics"]["avail_pct"], 500 / 7)

    def test_commands_formula_lock_and_sorted_results(self):
        response = self.client.get("/api/v1/readiness/commands")
        self.assertEqual(response.status_code, 200)
        rows = response.json()["commands"]
        self.assertEqual([row["command"] for row in rows], ["A", "B"])
        self.assertAlmostEqual(rows[1]["svc_pct"], 200 / 3)
        self.assertEqual(rows[1]["avail_pct"], 50)
        self.assertEqual(rows[1]["nmcm_tails"], 1)

    def test_command_filter_agrees_across_endpoints(self):
        fleet = self.client.get("/api/v1/readiness/fleet?command=B").json()
        commands = self.client.get("/api/v1/readiness/commands?command=B").json()
        row = commands["commands"][0]
        self.assertEqual(row.pop("command"), "B")
        self.assertEqual(row, fleet["metrics"])
        body = self.client.get("/api/v1/status-distribution?command=B").json()
        self.assertEqual(body["command"], "B")
        self.assertEqual(body["total_tails"], 4)
        self.assertEqual(sum(s["count"] for s in body["statuses"]), 4)

    def test_distribution_keeps_pmcm_and_pmcs_separate_and_zeroes(self):
        response = self.client.get("/api/v1/status-distribution?date=2026-01-01")
        self.assertEqual(response.status_code, 200)
        rows = response.json()["statuses"]
        self.assertEqual([s["status"] for s in rows], ["FMC", "PMCM", "PMCS", "NMCS", "NMCM", "DEPOT"])
        self.assertEqual([s["count"] for s in rows], [1] * 6)
        self.assertAlmostEqual(sum(s["pct"] for s in rows), 100)
        latest = self.client.get("/api/v1/status-distribution").json()
        self.assertEqual(next(s["count"] for s in latest["statuses"] if s["status"] == "NMCS"), 0)

    def test_fleet_command_distribution_reconcile_each_day(self):
        for day in ("2026-01-01", "2026-01-02", "2026-01-03"):
            fleet = self.client.get("/api/v1/readiness/fleet", params={"date": day}).json()["metrics"]
            commands = self.client.get("/api/v1/readiness/commands", params={"date": day}).json()["commands"]
            dist = self.client.get("/api/v1/status-distribution", params={"date": day}).json()
            for key in ("total_tails", "fmc_tails", "pmc_tails", "nmcm_tails", "nmcs_tails", "depot_tails"):
                self.assertEqual(fleet[key], sum(row[key] for row in commands))
            self.assertEqual(dist["total_tails"], fleet["total_tails"])
            self.assertEqual(sum(s["count"] for s in dist["statuses"]), fleet["total_tails"])

    def test_invalid_queries_are_422_without_echo(self):
        for endpoint in ("readiness/fleet", "readiness/commands", "status-distribution"):
            for query in ({"date": "bad"}, {"date": "2026-02-30"}, {"date": "2026-01-01T00:00:00"},
                          {"date": "1767225600"}, {"command": ""}, {"command": "b"},
                          {"command": "A" * 33}, {"path": "private-value"}):
                with self.subTest(endpoint=endpoint, query=query):
                    response = self.client.get("/api/v1/" + endpoint, params=query)
                    self.assertEqual(response.status_code, 422)
                    self.assertNotIn("private-value", response.text)

    def test_absent_selections_are_404(self):
        for endpoint in ("readiness/fleet", "readiness/commands", "status-distribution"):
            for query in ({"date": "2030-01-01"}, {"command": "UNKNOWN"}):
                self.assertEqual(self.client.get("/api/v1/" + endpoint, params=query).status_code, 404)

    def test_empty_source_is_404(self):
        self.app.dependency_overrides[get_snapshot] = lambda: pd.DataFrame()
        self.assertEqual(self.client.get("/api/v1/readiness/fleet").status_code, 404)

    def test_zero_denominator_guards_survive_api(self):
        self.app.dependency_overrides[get_snapshot] = lambda: pd.DataFrame({
            "date": pd.to_datetime(["2026-01-01"] * 2), "tail": ["T", "U"],
            "status": ["NMCS", "DEPOT"], "command": ["A", "A"]})
        fleet = self.client.get("/api/v1/readiness/fleet").json()["metrics"]
        command = self.client.get("/api/v1/readiness/commands").json()["commands"][0]
        for row in (fleet, command):
            self.assertEqual(row["svc_pct"], 0)
            self.assertEqual(row["avail_pct"], 0)

    def test_unknown_status_is_accounted_for(self):
        self.app.dependency_overrides[get_snapshot] = lambda: pd.DataFrame({
            "date": pd.to_datetime(["2026-01-01"]), "tail": ["T"],
            "status": ["MYSTERY"], "command": ["A"]})
        body = self.client.get("/api/v1/status-distribution").json()
        self.assertEqual(body["statuses"][-1], {"status": "MYSTERY", "count": 1, "pct": 100})

    def test_internal_errors_do_not_disclose_details(self):
        for error in (FileNotFoundError("private-path"), ValueError("private-data")):
            with patch("api.main.pd.read_csv", side_effect=error):
                response = self.client.get("/api/v1/readiness/fleet")
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), {"detail": "Internal server error"})

    def test_read_only_routes_and_missing_route(self):
        self.assertEqual(self.client.post("/api/v1/readiness/fleet", json={}).status_code, 405)
        self.assertEqual(self.client.get("/api/v1/missing").status_code, 404)

    def test_openapi_documents_all_contracts(self):
        schema = self.client.get("/openapi.json").json()
        self.assertEqual(set(schema["paths"]), {"/health", "/api/v1/readiness/fleet",
                                               "/api/v1/readiness/commands", "/api/v1/status-distribution"})
        for path in schema["paths"]:
            self.assertIn("200", schema["paths"][path]["get"]["responses"])
            for code in ("404", "422", "500"):
                self.assertEqual(schema["paths"][path]["get"]["responses"][code]["content"]
                                 ["application/json"]["schema"]["$ref"], "#/components/schemas/ErrorResponse")

    def test_fixed_fixture_is_repeatable_and_not_mutated(self):
        first = self.client.get("/api/v1/readiness/fleet").json()
        self.client.get("/api/v1/readiness/fleet?command=B&date=2026-01-01")
        self.assertEqual(self.client.get("/api/v1/readiness/fleet").json(), first)
