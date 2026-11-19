"""Read-only aggregate API with explicitly configured, injectable event providers."""
from datetime import date
from collections.abc import Callable, Mapping
from typing import Annotated, Literal

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

import readiness
from api.config import ProviderConfig, SqlCredentials, parse_config
from api.providers import DataProvider, ProviderError, Source, create_provider


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
    source: Source = "synthetic"
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
    source: Source = "synthetic"


class ErrorResponse(BaseModel):
    detail: str
    source: Source | None = None


def get_provider(request: Request) -> DataProvider:
    return request.app.state.provider


def selected_provider(request: Request, provider: Annotated[DataProvider, Depends(get_provider)]):
    request.state.data_source = provider.source
    return provider


Provider = Annotated[DataProvider, Depends(selected_provider)]


def get_snapshot(provider: Provider) -> pd.DataFrame:
    events = provider.load_events()
    return readiness.build_tail_daily_snapshot(readiness.coalesce_columns(events))


def selected_snapshot(
    query: Annotated[Selection, Query()],
    snapshot: Annotated[pd.DataFrame, Depends(get_snapshot)],
    provider: Provider,
) -> tuple[pd.DataFrame, date, str | None]:
    requested = None
    if query.date is not None:
        try:
            requested = date.fromisoformat(query.date)
        except ValueError:
            raise HTTPException(422, "date must be a valid YYYY-MM-DD calendar date") from None
    if snapshot.empty:
        raise HTTPException(404, f"No {provider.source} snapshot available")
    day = requested or snapshot["date"].max().date()
    selected = snapshot[snapshot["date"] == pd.Timestamp(day)]
    if query.command is not None:
        selected = selected[selected["command"] == query.command]
    if selected.empty:
        raise HTTPException(404, f"No {provider.source} snapshot for the requested selection")
    return selected, day, query.command


Selected = Annotated[tuple[pd.DataFrame, date, str | None], Depends(selected_snapshot)]


def create_app(config: Mapping | ProviderConfig | None = None, *,
               credentials: SqlCredentials | None = None,
               connection_factory: Callable | None = None) -> FastAPI:
    provider = create_provider(parse_config(config), credentials, connection_factory)
    app = FastAPI(title="FIS4 readiness", version="0.3.0",
                  description="Explicit event providers; FIS-001 formulas. SQL acceptance is mocked only.",
                  responses={code: {"model": ErrorResponse} for code in (404, 422, 500, 503)})
    app.state.provider = provider

    def error_response(request: Request, status: int, detail: str):
        source = getattr(request.state, "data_source", request.app.state.provider.source)
        content = {"detail": detail}
        if source == "sql":
            content["source"] = source
        return JSONResponse(status_code=status, content=content,
                            headers={"X-FIS4-Data-Source": source})

    @app.middleware("http")
    async def source_header(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-FIS4-Data-Source"] = getattr(request.state, "data_source", provider.source)
        return response

    @app.exception_handler(ProviderError)
    async def provider_error(request: Request, error: ProviderError):
        return error_response(request, 503, "SQL data unavailable")

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, error: StarletteHTTPException):
        response = error_response(request, error.status_code, error.detail)
        if error.headers:
            response.headers.update(error.headers)
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        # Do not echo arbitrary query values or internal exception context.
        return error_response(request, 422, "Invalid request parameters")

    @app.exception_handler(Exception)
    async def internal_error(request: Request, error: Exception):
        return error_response(request, 500, "Internal server error")

    @app.get("/health", response_model=HealthResponse)
    def health(provider: Provider):
        # Liveness only; readiness data is checked by the aggregate endpoints.
        return HealthResponse(source=provider.source)

    @app.get("/api/v1/readiness/fleet", response_model=FleetResponse)
    def fleet(selection: Selected, provider: Provider):
        snapshot, day, command = selection
        metrics = readiness.compute_jac_daily_metrics(snapshot).to_dict("records")[0]
        return FleetResponse(source=provider.source, date=day, command=command, metrics=Metrics(**metrics))

    @app.get("/api/v1/readiness/commands", response_model=CommandResponse)
    def commands(selection: Selected, provider: Provider):
        snapshot, day, command = selection
        rows = readiness.compute_command_latest_metrics(snapshot, day).to_dict("records")
        return CommandResponse(source=provider.source, date=day, command=command, commands=rows)

    @app.get("/api/v1/status-distribution", response_model=DistributionResponse)
    def distribution(selection: Selected, provider: Provider):
        snapshot, day, command = selection
        counts = snapshot["status"].value_counts()
        total = int(snapshot["tail"].nunique())
        codes = list(readiness.CANONICAL_STATUSES)
        codes += sorted(set(counts.index) - set(codes))
        return DistributionResponse(source=provider.source, date=day, command=command, total_tails=total,
                                    statuses=[StatusCount(status=code, count=int(counts.get(code, 0)),
                                                          pct=int(counts.get(code, 0)) / total * 100)
                                              for code in codes])

    return app


app = create_app()
