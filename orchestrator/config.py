"""AI_Tester v2 - Orchestrator Configuration.

Global configuration settings for the AI_Tester v2 orchestrator.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from agents.openrouter_models import (
    OPENROUTER_API_KEY_ENV_VAR,
    OPENROUTER_BASE_URL_DEFAULT,
    OPENROUTER_MAX_RETRIES_DEFAULT,
    OPENROUTER_MAX_TOKENS_DEFAULT,
    OPENROUTER_RETRY_BACKOFF_SECONDS_DEFAULT,
    OPENROUTER_TIMEOUT_SECONDS_DEFAULT,
    OpenRouterConfig,
)


class Config(BaseModel):
    """Configuration settings for the AI_Tester v2 orchestrator."""

    SOURCE_REPO_PATH: str = "src/"
    TEMP_BASE_DIR: str = "./temp"
    DEFAULT_MODEL: str = "openai/gpt-4.1-mini"
    DEFAULT_JUDGE_MODEL: str = "openai/gpt-4.1-mini"
    PLAN_TEMPLATE_PATH: str = "./templates/plan_template.md"
    REPORT_SCHEMA_VERSION: str = "1.0.0"

    OPENROUTER_BASE_URL: str = Field(default=OPENROUTER_BASE_URL_DEFAULT)
    OPENROUTER_API_KEY_ENV_VAR: str = Field(default=OPENROUTER_API_KEY_ENV_VAR)
    OPENROUTER_HTTP_REFERER: str | None = None
    OPENROUTER_APP_TITLE: str = "AI_Tester v2"
    OPENROUTER_APP_CATEGORIES: list[str] = Field(default_factory=list)
    OPENROUTER_TIMEOUT_SECONDS: float = Field(
        default=OPENROUTER_TIMEOUT_SECONDS_DEFAULT, gt=0
    )
    OPENROUTER_MAX_RETRIES: int = Field(default=OPENROUTER_MAX_RETRIES_DEFAULT, ge=0)
    OPENROUTER_RETRY_BACKOFF_SECONDS: float = Field(
        default=OPENROUTER_RETRY_BACKOFF_SECONDS_DEFAULT, gt=0
    )
    OPENROUTER_MAX_TOKENS: int = Field(default=OPENROUTER_MAX_TOKENS_DEFAULT, gt=0)
    OPENROUTER_TEMPERATURE: float = Field(default=0.2, ge=0, le=2)
    OPENROUTER_PLAN_MODEL: str = DEFAULT_MODEL
    OPENROUTER_IMPLEMENT_MODEL: str = DEFAULT_MODEL
    OPENROUTER_JUDGE_MODEL: str = DEFAULT_JUDGE_MODEL

    def openrouter_config(self) -> OpenRouterConfig:
        """Build the OpenRouter adapter configuration without storing secrets."""
        return OpenRouterConfig(
            base_url=self.OPENROUTER_BASE_URL,
            api_key_env_var=self.OPENROUTER_API_KEY_ENV_VAR,
            http_referer=self.OPENROUTER_HTTP_REFERER,
            app_title=self.OPENROUTER_APP_TITLE,
            app_categories=self.OPENROUTER_APP_CATEGORIES,
            timeout_seconds=self.OPENROUTER_TIMEOUT_SECONDS,
            max_retries=self.OPENROUTER_MAX_RETRIES,
            retry_backoff_seconds=self.OPENROUTER_RETRY_BACKOFF_SECONDS,
            max_tokens=self.OPENROUTER_MAX_TOKENS,
            temperature=self.OPENROUTER_TEMPERATURE,
            models={
                "plan": self.OPENROUTER_PLAN_MODEL,
                "implement": self.OPENROUTER_IMPLEMENT_MODEL,
                "judge": self.OPENROUTER_JUDGE_MODEL,
            },
        )
