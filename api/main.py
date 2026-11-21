"""Read-only aggregate API with explicitly configured, injectable event providers."""
from datetime import date
from collections.abc import Callable, Mapping
from contextlib import asynccontextmanager
from typing import Annotated, Literal

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.concurrency import run_in_threadpool

import readiness
from api.config import ProviderConfig, SqlCredentials, parse_config
from api.providers import DataProvider, ProviderError, Source, create_provider
from api.history import HistoryUnavailable, SyntheticHistoryProvider


class Selection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: Annotated[str | None, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")] = None
    command: Annotated[str | None, Field(min_length=1, max_length=32, pattern=r"^[A-Z0-9_-]+$")] = None


class HistoricalSelection(Selection):
    date: Annotated[str, Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")]


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


def get_snapshot(provider: Provider) -> pd.DataFrame | None:
    if isinstance(provider, SyntheticHistoryProvider):
        return None  # History mode serves precomputed records; never rebuild a snapshot.
    events = provider.load_events()
    return readiness.build_tail_daily_snapshot(readiness.coalesce_columns(events))


def selected_snapshot(
    query: Annotated[Selection, Query()],
    snapshot: Annotated[pd.DataFrame | None, Depends(get_snapshot)],
    provider: Provider,
) -> tuple[pd.DataFrame | None, date, str | None]:
    requested = None
    if query.date is not None:
        try:
            requested = date.fromisoformat(query.date)
        except ValueError:
            raise HTTPException(422, "date must be a valid YYYY-MM-DD calendar date") from None
    if isinstance(provider, SyntheticHistoryProvider):
        day = requested or provider.end
        try:
            provider.read(day, query.command)
        except KeyError:
            raise HTTPException(404, "No synthetic snapshot for the requested selection") from None
        return None, day, query.command
    if snapshot.empty:
        raise HTTPException(404, f"No {provider.source} snapshot available")
    day = requested or snapshot["date"].max().date()
    selected = snapshot[snapshot["date"] == pd.Timestamp(day)]
    if query.command is not None:
        selected = selected[selected["command"] == query.command]
    if selected.empty:
        raise HTTPException(404, f"No {provider.source} snapshot for the requested selection")
    return selected, day, query.command


Selected = Annotated[tuple[pd.DataFrame | None, date, str | None], Depends(selected_snapshot)]


def create_app(config: Mapping | ProviderConfig | None = None, *,
               credentials: SqlCredentials | None = None,
               connection_factory: Callable | None = None) -> FastAPI:
    provider = create_provider(parse_config(config), credentials, connection_factory)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if isinstance(provider, SyntheticHistoryProvider):
            await run_in_threadpool(provider.initialize)
        try:
            yield
        finally:
            if isinstance(provider, SyntheticHistoryProvider):
                await run_in_threadpool(provider.close)

    app = FastAPI(title="FIS4 readiness", version="0.3.0",
                  lifespan=lifespan,
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

    @app.exception_handler(HistoryUnavailable)
    async def history_error(request: Request, error: HistoryUnavailable):
        return error_response(request, 503, "Synthetic history unavailable")

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
        metrics = (provider.read(day, command).metrics() if isinstance(provider, SyntheticHistoryProvider)
                   else readiness.compute_jac_daily_metrics(snapshot).to_dict("records")[0])
        return FleetResponse(source=provider.source, date=day, command=command, metrics=Metrics(**metrics))

    @app.get("/api/v1/readiness/commands", response_model=CommandResponse)
    def commands(selection: Selected, provider: Provider):
        snapshot, day, command = selection
        if isinstance(provider, SyntheticHistoryProvider):
            rows = [{"command": code, **provider.read(day, code).metrics()}
                    for code in ((command,) if command is not None else provider.commands)]
        else:
            rows = readiness.compute_command_latest_metrics(snapshot, day).to_dict("records")
        return CommandResponse(source=provider.source, date=day, command=command, commands=rows)

    @app.get("/api/v1/status-distribution", response_model=DistributionResponse)
    def distribution(selection: Selected, provider: Provider):
        snapshot, day, command = selection
        if isinstance(provider, SyntheticHistoryProvider):
            record = provider.read(day, command)
            return DistributionResponse(source=provider.source, date=day, command=command,
                                        total_tails=record.total_tails,
                                        statuses=[StatusCount(status=code, count=count,
                                                              pct=count / record.total_tails * 100)
                                                  for code, count in zip(readiness.CANONICAL_STATUSES,
                                                                         record.statuses)])
        counts = snapshot["status"].value_counts()
        total = int(snapshot["tail"].nunique())
        codes = list(readiness.CANONICAL_STATUSES)
        codes += sorted(set(counts.index) - set(codes))
        return DistributionResponse(source=provider.source, date=day, command=command, total_tails=total,
                                    statuses=[StatusCount(status=code, count=int(counts.get(code, 0)),
                                                          pct=int(counts.get(code, 0)) / total * 100)
                                              for code in codes])

    if isinstance(provider, SyntheticHistoryProvider):
        @app.get("/api/v1/readiness/history", response_model=FleetResponse,
                 description="Explicit end-of-day synthetic readiness; history mode only. No authentication is implemented.")
        def historical_readiness(request: Request, query: Annotated[HistoricalSelection, Query()],
                                 provider: Provider):
            # Dependency overrides/non-history providers cannot expose this cache.
            if not isinstance(provider, SyntheticHistoryProvider):
                raise HTTPException(404, "Historical readiness is not enabled")
            if any(len(request.query_params.getlist(key)) != 1 for key in request.query_params):
                raise HTTPException(422, "Invalid request parameters")
            try:
                day = date.fromisoformat(query.date)
            except ValueError:
                raise HTTPException(422, "date must be a valid YYYY-MM-DD calendar date") from None
            if query.command is not None and query.command not in provider.commands:
                raise HTTPException(422, "Invalid historical command")
            try:
                record = provider.read(day, query.command)
            except KeyError:
                raise HTTPException(404, "No synthetic snapshot for the requested selection") from None
            return FleetResponse(source="synthetic", date=day, command=query.command,
                                 metrics=Metrics(**record.metrics()))

    return app


app = create_app()
