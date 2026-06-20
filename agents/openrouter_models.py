"""OpenRouter API integration for AI_Tester v2.

This module keeps all OpenRouter HTTP communication isolated from the
orchestrator workflow so tests can exercise the benchmark logic without a real
API key or network access.
"""

from __future__ import annotations

import os
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

OPENROUTER_API_KEY_ENV_VAR = "OPENROUTER_API_KEY"
OPENROUTER_BASE_URL_DEFAULT = "https://openrouter.ai/api/v1"
OPENROUTER_APP_TITLE = "AI_Tester v2"
OPENROUTER_DEFAULT_MODEL = "openai/gpt-4.1-mini"
OPENROUTER_TIMEOUT_SECONDS_DEFAULT = 30.0
OPENROUTER_MAX_RETRIES_DEFAULT = 2
OPENROUTER_RETRY_BACKOFF_SECONDS_DEFAULT = 1.0
OPENROUTER_MAX_TOKENS_DEFAULT = 4096


class OpenRouterRole(BaseModel):
    """Role used by the orchestrator when selecting an OpenRouter model."""

    name: Literal["plan", "implement", "judge"]


class OpenRouterModelConfig(BaseModel):
    """Model mapping for a single orchestrator role."""

    role: Literal["plan", "implement", "judge"]
    model_id: str = Field(..., min_length=1)


class OpenRouterConfig(BaseModel):
    """Configuration for the OpenRouter adapter.

    The API key is deliberately not stored in this model. It is read from
    ``OPENROUTER_API_KEY`` immediately before a request is sent, which prevents
    accidental serialization of secrets in reports or tests.
    """

    model_config = ConfigDict(extra="forbid")

    base_url: HttpUrl = Field(default=OPENROUTER_BASE_URL_DEFAULT)
    api_key_env_var: str = Field(default=OPENROUTER_API_KEY_ENV_VAR)
    http_referer: str | None = None
    app_title: str = Field(default=OPENROUTER_APP_TITLE)
    app_categories: list[str] = Field(default_factory=list)
    timeout_seconds: float = Field(default=OPENROUTER_TIMEOUT_SECONDS_DEFAULT, gt=0)
    max_retries: int = Field(default=OPENROUTER_MAX_RETRIES_DEFAULT, ge=0)
    retry_backoff_seconds: float = Field(
        default=OPENROUTER_RETRY_BACKOFF_SECONDS_DEFAULT, gt=0
    )
    max_tokens: int = Field(default=OPENROUTER_MAX_TOKENS_DEFAULT, gt=0)
    temperature: float = Field(default=0.2, ge=0, le=2)
    models: dict[Literal["plan", "implement", "judge"], str] = Field(
        default_factory=lambda: {
            "plan": OPENROUTER_DEFAULT_MODEL,
            "implement": OPENROUTER_DEFAULT_MODEL,
            "judge": OPENROUTER_DEFAULT_MODEL,
        }
    )

    @model_validator(mode="after")  # type: ignore[misc]
    def validate_models(self) -> "OpenRouterConfig":
        missing_roles = {"plan", "implement", "judge"} - set(self.models)
        if missing_roles:
            raise ValueError(f"Missing OpenRouter model mappings for: {missing_roles}")
        return self

    def model_for_role(self, role: str) -> str:
        """Return the configured model for an orchestrator role."""
        if role not in self.models:
            raise ValueError(f"Unknown OpenRouter role: {role}")
        return self.models[role]  # type: ignore[index]

    def api_key(self) -> str | None:
        """Read the API key from environment without storing it in config."""
        return os.getenv(self.api_key_env_var)

    def public_dump(self) -> dict[str, Any]:
        """Return a serializable dump without secret material."""
        return {
            "base_url": str(self.base_url),
            "api_key_env_var": self.api_key_env_var,
            "http_referer": self.http_referer,
            "app_title": self.app_title,
            "app_categories": self.app_categories,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "retry_backoff_seconds": self.retry_backoff_seconds,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "models": self.models,
        }


class OpenRouterCompletion(BaseModel):
    """Normalized OpenRouter chat completion response."""

    model_config = ConfigDict(extra="allow")

    content: str
    request_id: str | None = None
    model: str
    status_code: int
    duration_seconds: float = Field(ge=0)
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    retry_count: int = Field(default=0, ge=0)


class OpenRouterRequestMetadata(BaseModel):
    """Request metadata safe to include in reports and logs."""

    model_config = ConfigDict(extra="forbid")

    request_id: str | None = None
    role: str
    model: str
    status_code: int
    duration_seconds: float = Field(ge=0)
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    retry_count: int = Field(default=0, ge=0)

    @classmethod
    def from_completion(
        cls, completion: OpenRouterCompletion, role: str
    ) -> "OpenRouterRequestMetadata":
        """Create safe request metadata from a normalized completion."""
        return cls(
            request_id=completion.request_id,
            role=role,
            model=completion.model,
            status_code=completion.status_code,
            duration_seconds=completion.duration_seconds,
            input_tokens=completion.input_tokens,
            output_tokens=completion.output_tokens,
            total_tokens=completion.total_tokens,
            estimated_cost_usd=completion.estimated_cost_usd,
            retry_count=completion.retry_count,
        )


class OpenRouterRateLimitInfo(BaseModel):
    """Usage and credit information returned by ``GET /api/v1/key``."""

    model_config = ConfigDict(extra="allow")

    limit: float | None = None
    limit_remaining: float | None = None
    usage_daily: float | None = None
    usage_monthly: float | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "OpenRouterRateLimitInfo":
        """Parse OpenRouter key endpoint payload into rate limit metadata."""
        return cls(
            limit=payload.get("limit"),
            limit_remaining=payload.get("limit_remaining"),
            usage_daily=payload.get("usage_daily"),
            usage_monthly=payload.get("usage_monthly"),
        )
