# AI_Tester v2

## Overview

AI_Tester v2 is a comprehensive, modular testing and evaluation framework designed to benchmark the performance of various AI models (e.g., GPT-4, Claude-3) against defined tasks. It orchestrates a multi-stage workflow: **Plan** $\rightarrow$ **Implement** $\rightarrow$ **Review**.

The system is built around the `Orchestrator` class, which manages task isolation, time tracking, and result aggregation.

## Architecture

The core components are:

1. **Orchestrator**: The main coordinator, managing the workflow lifecycle.
2. **OpenRouterAdapter**: Isolated HTTP adapter for OpenRouter chat completions, structured outputs, retry/rate limiting, model lookup and key-limit metadata.
3. **TaskManager**: Handles the creation and cleanup of isolated, temporary workspaces for each task.
4. **TimeTracker**: Provides precise timing metrics for each phase.
5. **ToolLogger**: Logs all agent actions (terminal, file I/O, tool usage) for auditability.
6. **VS Code Adapter stub**: Defines the future controlled adapter contract and `FakeVsCodeAdapter` used by Faza 1 tests.

## VS Code Adapter Stub

Faza 1 does not implement the full VS Code Extension Host integration. It provides a stable contract for the next phase:

- `VsCodeAdapter` in `agents/vscode_adapter/adapter.py`
- public exports in `agents/vscode_adapter/__init__.py`
- `FakeVsCodeAdapter` in `agents/vscode_adapter/fake_adapter.py`

The adapter contract covers `run_terminal_command`, `read_file`, `write_file`, `search_files`, `list_directory`, `fetch_documentation` and `context7`. All future implementations must keep operations inside the task `workspace_path` and log actions through `ToolLogger`. The concrete adapter is expected to use `vscode.lm.registerTool`, `vscode.window.createTerminal`, `shellIntegration.executeCommand` and `onDidEndTerminalShellExecution`; the fake adapter returns deterministic stubs for tests.

## Quality Gates

- **QG-1**: Unit tests are green with OpenRouter adapter, Orchestrator integration, ToolLogger and VS Code Adapter stub coverage.
- **QG-2**: JSON Schemas for task results and ranking reports accept redacted OpenRouter metadata.
- **QG-3**: Static checks pass with `ruff format --check agents orchestrator schemas` and `ruff check agents orchestrator schemas`.

## Getting Started

### Prerequisites

- Python 3.11+
- `pytest` do testów jednostkowych
- `pydantic` do modeli danych
- `httpx` do adaptera OpenRouter
- `jsonschema` do walidacji structured outputs i raportów

### Installation

1. Zainstaluj zależności projektu:

   ```bash
   pip install -r requirements.txt
   ```

2. Faza 1 nie wymaga Docker. Izolacja tasków jest realizowana przez katalogi tymczasowe.

### OpenRouter configuration

AI_Tester v2 uses `OpenRouterAdapter` as the only component that calls the OpenRouter API. The adapter posts to `https://openrouter.ai/api/v1/chat/completions`, selects models by orchestrator role, and records redacted request metadata for reports and logs.

Configure the API key only through an environment variable:

```bash
export OPENROUTER_API_KEY="your-key"
```

On Windows PowerShell:

```powershell
$env:OPENROUTER_API_KEY="your-key"
```

Do not commit `.env` files or real keys. A safe example is available in `.env.example`:

```bash
OPENROUTER_API_KEY=changeme
OPENROUTER_HTTP_REFERER=https://example.invalid/ai-tester
OPENROUTER_APP_TITLE=AI_Tester v2
```

`Config` maps OpenRouter settings to the adapter without storing secrets:

- `OPENROUTER_BASE_URL` defaults to `https://openrouter.ai/api/v1`.
- `OPENROUTER_API_KEY_ENV_VAR` defaults to `OPENROUTER_API_KEY`.
- `OPENROUTER_HTTP_REFERER` and `OPENROUTER_APP_TITLE` populate attribution headers.
- `OPENROUTER_TIMEOUT_SECONDS`, `OPENROUTER_MAX_RETRIES`, `OPENROUTER_RETRY_BACKOFF_SECONDS`, and `OPENROUTER_MAX_TOKENS` guard request duration, retry cost, and token cost.
- `OPENROUTER_PLAN_MODEL`, `OPENROUTER_IMPLEMENT_MODEL`, and `OPENROUTER_JUDGE_MODEL` select the tested model for `plan`/`implement` and the judge model for `review`.

Example:

```python
from orchestrator.config import Config

config = Config(
    OPENROUTER_HTTP_REFERER="https://example.invalid/ai-tester",
    OPENROUTER_PLAN_MODEL="openai/gpt-4.1-mini",
    OPENROUTER_IMPLEMENT_MODEL="anthropic/claude-3.5-sonnet",
    OPENROUTER_JUDGE_MODEL="openai/gpt-4.1-mini",
)
```

`Orchestrator` injects `OpenRouterAdapter` into the workflow. For tests or custom integrations, you can pass a compatible adapter directly:

```python
from orchestrator.orchestrator import Orchestrator

orchestrator = Orchestrator(config, adapter=my_adapter)
```

The adapter also exposes helper endpoints for local diagnostics:

- `list_models()` calls `GET /api/v1/models`.
- `get_model(model_id)` calls `GET /api/v1/model/{author}/{slug}` and returns `None` for `404`.
- `get_key_limits()` calls `GET /api/v1/key` and parses credit/usage fields.

### Structured outputs and metadata

The review stage uses `generate_structured(...)` with `response_format: {"type": "json_schema", ...}`. The adapter validates the model response with `jsonschema.validate`; invalid JSON or schema mismatches raise `OpenRouterStructuredOutputError`.

Each OpenRouter request is recorded as redacted metadata containing request id, role, model, status code, duration, token counts, estimated cost, and retry count. Logs use `type: "ai_tool"` and `tool: "openrouter"` and never include `Authorization`, the API key, request headers, or full payloads.

### Testing

Default tests are deterministic and do not require network access or a real API key. They use `httpx.MockTransport` to assert request paths, headers, retry behavior, structured output payloads, and response parsing.

Run the default test suite:

```bash
python -m pytest
```

Run static checks:

```bash
python -m ruff format --check agents orchestrator schemas
python -m ruff check agents orchestrator schemas
python -m json.tool schemas/ranking.schema.json
python -m json.tool schemas/task-result.schema.json
```

### Optional OpenRouter smoke test

A smoke test is marked with `openrouter_smoke` and is intentionally not part of the default `pytest` run. It is for local verification only and requires `OPENROUTER_API_KEY` to be set in the environment.

Run it explicitly when you want to verify live connectivity:

```bash
python -m pytest -m openrouter_smoke
```

Smoke tests must log only metadata and must not print or persist the API key.

### Usage

The primary entry point is the `Orchestrator` class.

```python
from orchestrator.orchestrator import Orchestrator
from orchestrator.config import Config
from orchestrator.models import Task

# 1. Konfiguracja
config = Config()

# 2. Definicja zadania
task = Task(task_id="T1", task_type="feature", repo="core", source="path/to/source")

# 3. Uruchomienie Orchestratora
orchestrator = Orchestrator(config)
try:
    result = orchestrator.run_task(task)
    print("Task completed successfully!")
except Exception as e:
    print(f"Workflow failed: {e}")
```

## Workflow Stages

1. **Plan**: Generates a detailed plan for the task.
2. **Implement**: Executes the plan, generating code and artifacts in an isolated workspace.
3. **Review**: Evaluates the implemented code against the plan and best practices.

## API Reference

- `orchestrator.orchestrator.Orchestrator`: Main class for running the workflow.
- `orchestrator.models.Task`: Data model for defining tasks.
- `orchestrator.models.TaskResult`: Data model for task outcomes.
