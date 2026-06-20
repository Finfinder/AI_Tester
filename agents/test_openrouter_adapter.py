"""Unit tests for the OpenRouter API adapter."""

from __future__ import annotations

import json

import httpx
import pytest

from agents.openrouter_adapter import (
    OpenRouterAPIError,
    OpenRouterAuthenticationError,
    OpenRouterCreditExhaustedError,
    OpenRouterStructuredOutputError,
    OpenRouterAdapter,
)
from agents.openrouter_models import OpenRouterConfig, OpenRouterRateLimitInfo
from orchestrator.config import Config


def _config(**overrides: object) -> OpenRouterConfig:
    return OpenRouterConfig(
        **{
            "models": {
                "plan": "tested/plan-model",
                "implement": "tested/implement-model",
                "judge": "judge/model",
            },
            **overrides,
        }
    )


def _completion_payload(
    *,
    content: str = "ok",
    model: str = "tested/plan-model",
    request_id: str = "req_1",
    cost_usd: float | None = None,
    usage: dict[str, int] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": request_id,
        "model": model,
        "choices": [{"message": {"content": content}, "index": 0}],
        "usage": usage
        or {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
    }
    if cost_usd is not None:
        payload["cost_usd"] = cost_usd
    return payload


def _json_response(payload: dict[str, object], status_code: int = 200, headers=None):
    return httpx.Response(
        status_code=status_code,
        headers={"Content-Type": "application/json", **(headers or {})},
        json=payload,
    )


@pytest.fixture
def api_key(monkeypatch):
    """Provide a fake OpenRouter API key for adapter unit tests."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    return "test-key"


def test_generate_uses_role_model_endpoint_and_attribution_headers(api_key):
    requests_seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests_seen.append(request)
        return _json_response(_completion_payload(model="tested/implement-model"))

    config = _config(http_referer="https://example.test/ai-tester")
    adapter = OpenRouterAdapter(
        config=config,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
        jitter=lambda _a, _b: 0.0,
    )

    completion = adapter.generate("Implement this", role="implement")

    assert completion.content == "ok"
    assert completion.model == "tested/implement-model"
    assert completion.status_code == 200
    assert completion.input_tokens == 1
    assert completion.output_tokens == 2
    assert completion.total_tokens == 3
    assert completion.estimated_cost_usd is None
    assert completion.retry_count == 0

    assert len(requests_seen) == 1
    request = requests_seen[0]
    assert request.method == "POST"
    assert request.url == "https://openrouter.ai/api/v1/chat/completions"
    body = json.loads(request.content)
    assert body["model"] == "tested/implement-model"
    assert body["messages"] == [{"role": "user", "content": "Implement this"}]
    assert body["stream"] is False
    assert body["max_tokens"] == 4096
    assert request.headers["Authorization"] == "Bearer test-key"
    assert request.headers["HTTP-Referer"] == "https://example.test/ai-tester"
    assert request.headers["X-OpenRouter-Title"] == "AI_Tester v2"


def test_generate_reads_api_key_from_configured_env_var(monkeypatch):
    monkeypatch.setenv("CUSTOM_OPENROUTER_KEY", "custom-key")
    seen_authorization: str | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_authorization
        seen_authorization = request.headers["Authorization"]
        return _json_response(_completion_payload())

    adapter = OpenRouterAdapter(
        config=_config(api_key_env_var="CUSTOM_OPENROUTER_KEY"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
        jitter=lambda _a, _b: 0.0,
    )

    adapter.generate("Plan", role="plan")

    assert seen_authorization == pytest.approx("Bearer custom-key")


def test_missing_api_key_raises_clear_error_without_leaking_key():
    adapter = OpenRouterAdapter(config=_config(api_key_env_var="MISSING_KEY"))

    with pytest.raises(OpenRouterAuthenticationError) as exc:
        adapter.generate("Plan", role="plan")

    assert "MISSING_KEY" in str(exc.value)
    assert "custom-key" not in str(exc.value)


def test_openrouter_config_dump_does_not_include_api_key_value(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-key")

    config = OpenRouterConfig().public_dump()

    assert config["api_key_env_var"] == "OPENROUTER_API_KEY"
    assert "secret-key" not in json.dumps(config)


def test_orchestrator_openrouter_config_does_not_include_api_key_value(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-key")

    config = Config().openrouter_config().public_dump()

    assert config["api_key_env_var"] == "OPENROUTER_API_KEY"
    assert "secret-key" not in json.dumps(config)


def test_structured_output_validates_json_schema(api_key):
    schema = {
        "type": "object",
        "properties": {"score": {"type": "integer", "minimum": 0, "maximum": 100}},
        "required": ["score"],
        "additionalProperties": False,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["response_format"]["type"] == "json_schema"
        assert body["response_format"]["json_schema"]["name"] == "review_schema"
        assert body["response_format"]["json_schema"]["strict"] is True
        return _json_response(_completion_payload(content='{"score": 95}'))

    adapter = OpenRouterAdapter(
        config=_config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
        jitter=lambda _a, _b: 0.0,
    )

    payload, completion = adapter.generate_structured(
        "Review", schema=schema, role="judge", schema_name="review_schema"
    )

    assert payload == {"score": 95}
    assert completion.content == '{"score": 95}'


def test_structured_output_rejects_invalid_json(api_key):
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response(_completion_payload(content="not-json"))

    adapter = OpenRouterAdapter(
        config=_config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
        jitter=lambda _a, _b: 0.0,
    )

    with pytest.raises(OpenRouterStructuredOutputError):
        adapter.generate_structured(
            "Review",
            schema={"type": "object"},
            role="judge",
            schema_name="review_schema",
        )


def test_structured_output_rejects_schema_mismatch(api_key):
    schema = {"type": "object", "properties": {"score": {"type": "integer"}}}

    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response(_completion_payload(content='{"score": "high"}'))

    adapter = OpenRouterAdapter(
        config=_config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
        jitter=lambda _a, _b: 0.0,
    )

    with pytest.raises(OpenRouterStructuredOutputError):
        adapter.generate_structured(
            "Review", schema=schema, role="judge", schema_name="review_schema"
        )


def test_retry_for_429_respects_retry_after_and_reports_retry_count(api_key):
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return _json_response(
                {"error": "rate limit"},
                status_code=429,
                headers={"Retry-After": "0"},
            )
        return _json_response(_completion_payload())

    adapter = OpenRouterAdapter(
        config=_config(max_retries=1),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
        jitter=lambda _a, _b: 0.0,
    )

    completion = adapter.generate("Plan", role="plan")

    assert calls == 2
    assert completion.retry_count == 1


def test_retry_for_503_uses_exponential_backoff(api_key):
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls <= 2:
            return _json_response({"error": "server"}, status_code=503)
        return _json_response(_completion_payload())

    adapter = OpenRouterAdapter(
        config=_config(max_retries=2, retry_backoff_seconds=0.01),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
        jitter=lambda _a, _b: 0.0,
    )

    completion = adapter.generate("Implement", role="implement")

    assert calls == 3
    assert completion.retry_count == 2


def test_401_and_402_do_not_retry(api_key):
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return _json_response({"error": "auth"}, status_code=401)

    adapter = OpenRouterAdapter(
        config=_config(max_retries=2),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
        jitter=lambda _a, _b: 0.0,
    )

    with pytest.raises(OpenRouterAuthenticationError) as auth_exc:
        adapter.generate("Plan", role="plan")

    assert auth_exc.value.status_code == 401
    assert calls == 1


def test_402_maps_to_credit_exhausted_error(api_key):
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response({"error": "credits"}, status_code=402)

    adapter = OpenRouterAdapter(
        config=_config(max_retries=2),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
        jitter=lambda _a, _b: 0.0,
    )

    with pytest.raises(OpenRouterCreditExhaustedError) as exc:
        adapter.generate("Plan", role="plan")

    assert exc.value.status_code == 402


def test_503_after_retries_raises_api_error_with_status_code(api_key):
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response({"error": "server"}, status_code=503)

    adapter = OpenRouterAdapter(
        config=_config(max_retries=1),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
        jitter=lambda _a, _b: 0.0,
    )

    with pytest.raises(OpenRouterAPIError) as exc:
        adapter.generate("Plan", role="plan")

    assert exc.value.status_code == 503


def test_list_models_get_model_and_key_limits_parse_responses(api_key):
    responses = {
        "https://openrouter.ai/api/v1/models": {"data": [{"id": "tested/plan-model"}]},
        "https://openrouter.ai/api/v1/model/tested/plan-model": {
            "id": "tested/plan-model"
        },
        "https://openrouter.ai/api/v1/key": {
            "limit": 100.0,
            "limit_remaining": 50.0,
            "usage_daily": 10.0,
            "usage_monthly": 40.0,
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response(responses[str(request.url)])

    adapter = OpenRouterAdapter(
        config=_config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
        jitter=lambda _a, _b: 0.0,
    )

    models = adapter.list_models()
    model = adapter.get_model("tested/plan-model")
    key_limits = adapter.get_key_limits()

    assert models == [{"id": "tested/plan-model"}]
    assert model == {"id": "tested/plan-model"}
    assert isinstance(key_limits, OpenRouterRateLimitInfo)
    assert key_limits.limit == pytest.approx(100.0)
    assert key_limits.limit_remaining == pytest.approx(50.0)
    assert key_limits.usage_daily == pytest.approx(10.0)
    assert key_limits.usage_monthly == pytest.approx(40.0)


def test_get_model_returns_none_for_404(api_key):
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response({"error": "not found"}, status_code=404)

    adapter = OpenRouterAdapter(
        config=_config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
        jitter=lambda _a, _b: 0.0,
    )

    assert adapter.get_model("missing/model") is None
