"""Optional live smoke tests for the OpenRouter API adapter."""

from __future__ import annotations

import os

import pytest

from agents.openrouter_adapter import OpenRouterAdapter
from agents.openrouter_models import (
    OPENROUTER_API_KEY_ENV_VAR,
    OPENROUTER_APP_TITLE,
    OpenRouterConfig,
)

pytestmark = pytest.mark.openrouter_smoke


def test_get_key_limits_with_real_openrouter_api():
    """Verify live OpenRouter connectivity without logging or exposing the key."""
    api_key = os.getenv(OPENROUTER_API_KEY_ENV_VAR)
    if not api_key:
        pytest.skip(f"{OPENROUTER_API_KEY_ENV_VAR} is not set")

    adapter = OpenRouterAdapter(
        config=OpenRouterConfig(
            http_referer=os.getenv("OPENROUTER_HTTP_REFERER"),
            app_title=os.getenv("OPENROUTER_APP_TITLE", OPENROUTER_APP_TITLE),
        )
    )
    try:
        limits = adapter.get_key_limits()
    finally:
        adapter.close()

    assert limits.limit is None or limits.limit >= 0
    assert limits.limit_remaining is None or limits.limit_remaining >= 0
    assert limits.usage_daily is None or limits.usage_daily >= 0
    assert limits.usage_monthly is None or limits.usage_monthly >= 0
