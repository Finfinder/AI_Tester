"""OpenRouter API adapter for AI_Tester v2."""

from __future__ import annotations

from dataclasses import dataclass
import json
import random
import time
from typing import Any, Mapping
from urllib.parse import urljoin

import httpx
import jsonschema

from agents.openrouter_models import (
    OPENROUTER_APP_TITLE,
    OpenRouterCompletion,
    OpenRouterConfig,
    OpenRouterRateLimitInfo,
    OpenRouterRequestMetadata,
)


def _to_optional_int(value: Any) -> int | None:
    """Convert API usage fields to integers when present."""
    if value is None:
        return None
    return int(value)


def _to_optional_float(value: Any) -> float | None:
    """Convert optional cost fields to floats when present."""
    if value is None:
        return None
    return float(value)


class OpenRouterAPIError(RuntimeError):
    """Raised when OpenRouter returns an unrecoverable API error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class OpenRouterAuthenticationError(OpenRouterAPIError):
    """Raised when OpenRouter rejects the API key."""

    def __init__(self, message: str, status_code: int | None = 401) -> None:
        super().__init__(message, status_code=status_code)


class OpenRouterRateLimitError(OpenRouterAPIError):
    """Raised when OpenRouter rate limits the request."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class OpenRouterCreditExhaustedError(OpenRouterAPIError):
    """Raised when OpenRouter credits are exhausted."""

    def __init__(self, message: str, status_code: int | None = 402) -> None:
        super().__init__(message, status_code=status_code)


class OpenRouterStructuredOutputError(OpenRouterAPIError):
    """Raised when a structured OpenRouter response cannot be parsed/validated."""


@dataclass(frozen=True)
class _OpenRouterResponseEnvelope:
    """Internal response envelope carrying safe metadata for completion parsing."""

    payload: dict[str, Any]
    response: httpx.Response
    retry_count: int
    duration_seconds: float


class OpenRouterAdapter:
    """Small HTTP adapter for OpenRouter chat completions and helper endpoints."""

    def __init__(
        self,
        config: OpenRouterConfig | None = None,
        logger: Any | None = None,
        client: httpx.Client | None = None,
        sleep: Any = time.sleep,
        jitter: Any = random.uniform,
    ) -> None:
        self.config = config or OpenRouterConfig()
        self.logger = logger
        self._client = client
        self._owns_client = client is None
        self._sleep = sleep
        self._jitter = jitter

    def close(self) -> None:
        """Close the owned HTTP client when present."""
        if self._owns_client and self._client is not None:
            self._client.close()

    def generate(
        self,
        prompt_or_messages: str | list[dict[str, Any]],
        role: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        extra_body: Mapping[str, Any] | None = None,
    ) -> OpenRouterCompletion:
        """Generate a chat completion for an orchestrator role."""
        messages = self._normalize_messages(prompt_or_messages)
        model = self.config.model_for_role(role)
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": self.config.temperature
            if temperature is None
            else temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "stream": False,
        }
        if extra_body:
            payload.update(dict(extra_body))

        response = self._request_json(
            method="POST",
            path="/chat/completions",
            payload=payload,
            model=model,
            role=role,
        )
        completion = self._parse_completion(response, model=model)
        self._log_completion(role, completion)
        return completion

    def generate_structured(
        self,
        prompt_or_messages: str | list[dict[str, Any]],
        schema: Mapping[str, Any],
        role: str,
        schema_name: str,
    ) -> tuple[dict[str, Any], OpenRouterCompletion]:
        """Generate and validate a JSON response against a JSON Schema."""
        completion = self.generate(
            prompt_or_messages=prompt_or_messages,
            role=role,
            extra_body={
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "strict": True,
                        "schema": schema,
                    },
                }
            },
        )
        try:
            parsed = json.loads(completion.content)
        except json.JSONDecodeError as exc:
            raise OpenRouterStructuredOutputError(
                f"OpenRouter response is not valid JSON for role {role!r}."
            ) from exc

        try:
            jsonschema.validate(instance=parsed, schema=schema)
        except jsonschema.ValidationError as exc:
            raise OpenRouterStructuredOutputError(
                f"OpenRouter response for role {role!r} does not match schema: {exc.message}"
            ) from exc

        return parsed, completion

    def list_models(self) -> list[dict[str, Any]]:
        """List models available from OpenRouter."""
        payload = self._request_json(
            method="GET",
            path="/models",
            payload=None,
            model=self.config.model_for_role("judge"),
            role="judge",
        ).payload
        data = payload.get("data")
        if not isinstance(data, list):
            raise OpenRouterAPIError(
                "OpenRouter models endpoint returned no data list."
            )
        return data

    def get_model(self, model_id: str) -> dict[str, Any] | None:
        """Return one model by id or by author/slug path."""
        path = f"/model/{model_id}"
        try:
            payload = self._request_json(
                method="GET",
                path=path,
                payload=None,
                model=model_id,
                role="judge",
            ).payload
        except OpenRouterAPIError as exc:
            if getattr(exc, "status_code", None) == 404:
                return None
            raise
        return payload

    def get_key_limits(self) -> OpenRouterRateLimitInfo:
        """Return OpenRouter key limits and usage metadata."""
        payload = self._request_json(
            method="GET",
            path="/key",
            payload=None,
            model=self.config.model_for_role("judge"),
            role="judge",
        ).payload
        return OpenRouterRateLimitInfo.from_payload(payload)

    def _request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
        model: str,
        role: str,
    ) -> _OpenRouterResponseEnvelope:
        retry_count = 0
        last_response: httpx.Response | None = None
        started = time.monotonic()

        for attempt in range(self.config.max_retries + 1):
            retry_count = attempt
            try:
                response = self._send_request(method, path, payload)
                last_response = response
                envelope = self._handle_response(
                    response,
                    path=path,
                    model=model,
                    role=role,
                    retry_count=retry_count,
                    started=started,
                )
                if envelope is not None:
                    return envelope
            except httpx.TimeoutException as exc:
                if attempt >= self.config.max_retries:
                    raise OpenRouterAPIError("OpenRouter request timed out.") from exc
                self._sleep_for_retry(None, attempt)
            except httpx.TransportError as exc:
                if attempt >= self.config.max_retries:
                    raise OpenRouterAPIError("OpenRouter transport error.") from exc
                self._sleep_for_retry(None, attempt)

        if last_response is not None:
            raise self._error_from_response(last_response)
        raise OpenRouterAPIError("OpenRouter request failed without a response.")

    def _handle_response(
        self,
        response: httpx.Response,
        *,
        path: str,
        model: str,
        role: str,
        retry_count: int,
        started: float,
    ) -> _OpenRouterResponseEnvelope | None:
        """Handle OpenRouter status codes and return a parsed envelope on success."""
        status_code = response.status_code
        if status_code in (400, 401, 402):
            self._log_error_response(role, model, response, retry_count, started)
            raise self._error_from_response(response)
        if status_code == 404 and path.startswith("/model/"):
            raise self._error_from_response(response)
        if status_code == 429:
            retry_after = self._parse_retry_after(response)
            if retry_count >= self.config.max_retries:
                self._log_error_response(role, model, response, retry_count, started)
                raise OpenRouterRateLimitError(
                    "OpenRouter rate limit exceeded.", retry_after=retry_after
                )
            self._sleep_for_retry(retry_after, retry_count)
            return None
        if 500 <= status_code < 600:
            if retry_count >= self.config.max_retries:
                self._log_error_response(role, model, response, retry_count, started)
                raise OpenRouterAPIError(
                    "OpenRouter server error after retries.",
                    status_code=status_code,
                )
            self._sleep_for_retry(None, retry_count)
            return None

        response.raise_for_status()
        return _OpenRouterResponseEnvelope(
            payload=response.json(),
            response=response,
            retry_count=retry_count,
            duration_seconds=time.monotonic() - started,
        )

    def _send_request(
        self, method: str, path: str, payload: dict[str, Any] | None
    ) -> httpx.Response:
        client = self._get_client()
        headers = self._headers()
        with client.stream(
            method, self._url(path), json=payload, headers=headers
        ) as response:
            body = response.read()
            return httpx.Response(
                status_code=response.status_code,
                headers=response.headers,
                content=body,
                request=response.request,
            )

    def _headers(self) -> dict[str, str]:
        api_key = self.config.api_key()
        if not api_key:
            raise OpenRouterAuthenticationError(
                f"Missing OpenRouter API key in {self.config.api_key_env_var}."
            )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.config.http_referer
            or "https://example.invalid/ai-tester",
            "X-OpenRouter-Title": self.config.app_title or OPENROUTER_APP_TITLE,
        }
        if self.config.app_categories:
            headers["X-OpenRouter-Categories"] = ",".join(self.config.app_categories)
        return headers

    def _url(self, path: str) -> str:
        return urljoin(str(self.config.base_url).rstrip("/") + "/", path.lstrip("/"))

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.config.timeout_seconds)
        return self._client

    def _normalize_messages(
        self, prompt_or_messages: str | list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if isinstance(prompt_or_messages, str):
            return [{"role": "user", "content": prompt_or_messages}]
        return prompt_or_messages

    def _parse_completion(
        self, envelope: _OpenRouterResponseEnvelope, model: str
    ) -> OpenRouterCompletion:
        payload = envelope.payload
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise OpenRouterAPIError("OpenRouter response contains no choices.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise OpenRouterAPIError("OpenRouter choice is not an object.")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise OpenRouterAPIError("OpenRouter choice message is not an object.")
        content = message.get("content")
        if not isinstance(content, str):
            raise OpenRouterAPIError("OpenRouter completion content is not a string.")

        usage = payload.get("usage")
        input_tokens = output_tokens = total_tokens = None
        if isinstance(usage, dict):
            input_tokens = _to_optional_int(usage.get("prompt_tokens"))
            output_tokens = _to_optional_int(usage.get("completion_tokens"))
            total_tokens = _to_optional_int(usage.get("total_tokens"))

        return OpenRouterCompletion(
            content=content,
            request_id=payload.get("id")
            if isinstance(payload.get("id"), str)
            else None,
            model=payload.get("model")
            if isinstance(payload.get("model"), str)
            else model,
            status_code=envelope.response.status_code,
            duration_seconds=envelope.duration_seconds,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=_to_optional_float(payload.get("cost_usd")),
            retry_count=envelope.retry_count,
        )

    def _error_from_response(self, response: httpx.Response) -> OpenRouterAPIError:
        if response.status_code == 401:
            return OpenRouterAuthenticationError(
                f"OpenRouter authentication failed ({response.status_code})."
            )
        if response.status_code == 402:
            return OpenRouterCreditExhaustedError(
                f"OpenRouter credits exhausted ({response.status_code})."
            )
        if response.status_code == 429:
            return OpenRouterRateLimitError(
                "OpenRouter rate limit exceeded.",
                retry_after=self._parse_retry_after(response),
            )
        return OpenRouterAPIError(
            f"OpenRouter API error ({response.status_code}).",
            status_code=response.status_code,
        )

    def _parse_retry_after(self, response: httpx.Response) -> float | None:
        retry_after = response.headers.get("Retry-After")
        if retry_after is None:
            return None
        try:
            return max(float(retry_after), 0.0)
        except ValueError:
            return None

    def _sleep_for_retry(self, retry_after: float | None, attempt: int = 0) -> None:
        delay = retry_after
        if delay is None:
            delay = self.config.retry_backoff_seconds * (2**attempt)
        self._sleep(delay + self._jitter(0.0, min(delay, 0.25)))

    def _log_error_response(
        self,
        role: str,
        model: str,
        response: httpx.Response,
        retry_count: int,
        started: float,
    ) -> None:
        if self.logger is None:
            return
        metadata = OpenRouterRequestMetadata(
            role=role,
            model=model,
            status_code=response.status_code,
            duration_seconds=time.monotonic() - started,
            retry_count=retry_count,
        )
        self.logger.log_openrouter_request(**metadata.model_dump())

    def _log_completion(self, role: str, completion: OpenRouterCompletion) -> None:
        if self.logger is None:
            return
        metadata = OpenRouterRequestMetadata.from_completion(completion, role=role)
        self.logger.log_openrouter_request(**metadata.model_dump())
