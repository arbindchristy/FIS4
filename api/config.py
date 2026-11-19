"""Explicit configuration only: no environment, credential-store or file discovery."""
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, model_validator


class ProviderConfigurationError(ValueError):
    def __init__(self):
        super().__init__("Invalid provider configuration")


class SqlSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    server: str = Field(min_length=1, max_length=253, pattern=r"^[A-Za-z0-9.-]+$")
    database: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    port: int = Field(default=1433, ge=1, le=65535, strict=True)
    source: Literal["readiness_events_v1"] = "readiness_events_v1"
    login_timeout: int = Field(default=5, ge=1, le=60, strict=True)
    query_timeout: int = Field(default=15, ge=1, le=120, strict=True)
    max_rows: int = Field(default=10000, ge=1, le=100000, strict=True)
    batch_size: int = Field(default=500, ge=1, le=1000, strict=True)
    max_span_days: int = Field(default=366, ge=1, le=3660, strict=True)
    max_snapshot_rows: int = Field(default=100000, ge=1, le=1000000, strict=True)


class SqlCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    username: SecretStr = Field(min_length=1, max_length=128, repr=False)
    password: SecretStr = Field(min_length=1, max_length=1024, repr=False)


class ProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    mode: Literal["synthetic", "sql"] = "synthetic"
    sql: SqlSettings | None = None

    @model_validator(mode="after")
    def validate_mode(self):
        if (self.mode == "sql") != (self.sql is not None):
            raise ValueError("SQL settings must be present exactly when SQL mode is selected")
        return self


def parse_config(values: Mapping | ProviderConfig | None = None) -> ProviderConfig:
    try:
        return ProviderConfig.model_validate({} if values is None else values)
    except (ValidationError, TypeError, ValueError):
        pass
    # No raw validation input or chained exception escapes to startup logs.
    raise ProviderConfigurationError()
