"""Read-only aggregate API; the only data source is the reviewed fictional fixture."""
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

import readiness

FIXTURE = Path(__file__).resolve().parents[1] / "data" / "synthetic_readiness.csv"


class Selection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: Annotated[str | None, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")] = None
    command: Annotated[str | None, Field(min_length=1, max_length=32, pattern=r"^[A-Z0-9_-]+$")] = None


class Metrics(BaseModel):
    total_tails: int = Field(ge=0)
    fmc_tails: int = Field(ge=0)
    pmc_tails: int = Field(ge=0)
    nmcm_tails: int = Field(ge=0)
    nmcs_tails: int = Field(ge=0)
    depot_tails: int = Field(ge=0)
    svc_pct: float = Field(ge=0, le=100, allow_inf_nan=False)
    avail_pct: float = Field(ge=0, le=100, allow_inf_nan=False)


class CommandMetrics(Metrics):
    command: str


class Metadata(BaseModel):
    source: Literal["synthetic"] = "synthetic"
    date: date
    command: str | None = None


class FleetResponse(Metadata):
    metrics: Metrics


class CommandResponse(Metadata):
    commands: list[CommandMetrics]


class StatusCount(BaseModel):
    status: str
    count: int = Field(ge=0)
    pct: float = Field(ge=0, le=100, allow_inf_nan=False)


class DistributionResponse(Metadata):
    total_tails: int = Field(ge=0)
    statuses: list[StatusCount]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    source: Literal["synthetic"] = "synthetic"


class ErrorResponse(BaseModel):
    detail: str


def get_snapshot() -> pd.DataFrame:
    # Fixed source: callers cannot supply paths, URLs, or uploaded data.
    events = pd.read_csv(FIXTURE, dtype={"tail": str})
    return readiness.build_tail_daily_snapshot(readiness.coalesce_columns(events))


def selected_snapshot(
    query: Annotated[Selection, Query()],
    snapshot: Annotated[pd.DataFrame, Depends(get_snapshot)],
) -> tuple[pd.DataFrame, date, str | None]:
    requested = None
    if query.date is not None:
        try:
            requested = date.fromisoformat(query.date)
        except ValueError:
            raise HTTPException(422, "date must be a valid YYYY-MM-DD calendar date") from None
    if snapshot.empty:
        raise HTTPException(404, "No synthetic snapshot available")
    day = requested or snapshot["date"].max().date()
    selected = snapshot[snapshot["date"] == pd.Timestamp(day)]
    if query.command is not None:
        selected = selected[selected["command"] == query.command]
    if selected.empty:
        raise HTTPException(404, "No synthetic snapshot for the requested selection")
    return selected, day, query.command


Selected = Annotated[tuple[pd.DataFrame, date, str | None], Depends(selected_snapshot)]


def create_app() -> FastAPI:
    app = FastAPI(title="FIS4 synthetic readiness", version="0.2.0",
                  description="Phase 02A: fictional aggregate data only; FIS-001 formulas.",
                  responses={code: {"model": ErrorResponse} for code in (404, 422, 500)})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        # Do not echo arbitrary query values or internal exception context.
        return JSONResponse(status_code=422, content={"detail": "Invalid request parameters"})

    @app.exception_handler(Exception)
    async def internal_error(request: Request, error: Exception):
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.get("/health", response_model=HealthResponse)
    def health():
        # Liveness only; readiness data is checked by the aggregate endpoints.
        return HealthResponse()

    @app.get("/api/v1/readiness/fleet", response_model=FleetResponse)
    def fleet(selection: Selected):
        snapshot, day, command = selection
        metrics = readiness.compute_jac_daily_metrics(snapshot).to_dict("records")[0]
        return FleetResponse(date=day, command=command, metrics=Metrics(**metrics))

    @app.get("/api/v1/readiness/commands", response_model=CommandResponse)
    def commands(selection: Selected):
        snapshot, day, command = selection
        rows = readiness.compute_command_latest_metrics(snapshot, day).to_dict("records")
        return CommandResponse(date=day, command=command, commands=rows)

    @app.get("/api/v1/status-distribution", response_model=DistributionResponse)
    def distribution(selection: Selected):
        snapshot, day, command = selection
        counts = snapshot["status"].value_counts()
        total = int(snapshot["tail"].nunique())
        codes = list(readiness.CANONICAL_STATUSES)
        codes += sorted(set(counts.index) - set(codes))
        return DistributionResponse(date=day, command=command, total_tails=total,
                                    statuses=[StatusCount(status=code, count=int(counts.get(code, 0)),
                                                          pct=int(counts.get(code, 0)) / total * 100)
                                              for code in codes])

    return app


app = create_app()
