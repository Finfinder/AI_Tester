# AI_Tester v2

## Overview

AI_Tester v2 is a comprehensive, modular testing and evaluation framework designed to benchmark the performance of various AI models (e.g., GPT-4, Claude-3) against defined tasks. It orchestrates a multi-stage workflow: **Plan** $\rightarrow$ **Implement** $\rightarrow$ **Review**.

The system is built around the `Orchestrator` class, which manages task isolation, time tracking, and result aggregation.

## Architecture

The core components are:

1. **Orchestrator**: The main coordinator, managing the workflow lifecycle.
2. **TaskManager**: Handles the creation and cleanup of isolated, temporary workspaces for each task.
3. **TimeTracker**: Provides precise timing metrics for each phase.
4. **ToolLogger**: Logs all agent actions (terminal, file I/O, tool usage) for auditability.
5. **VS Code Adapter stub**: Defines the future controlled adapter contract and `FakeVsCodeAdapter` used by Faza 1 tests.

## VS Code Adapter Stub

Faza 1 does not implement the full VS Code Extension Host integration. It provides a stable contract for the next phase:

- `VsCodeAdapter` in `agents/vscode_adapter/adapter.py`
- public exports in `agents/vscode_adapter/__init__.py`
- `FakeVsCodeAdapter` in `agents/vscode_adapter/fake_adapter.py`

The adapter contract covers `run_terminal_command`, `read_file`, `write_file`, `search_files`, `list_directory`, `fetch_documentation` and `context7`. All future implementations must keep operations inside the task `workspace_path` and log actions through `ToolLogger`. The concrete adapter is expected to use `vscode.lm.registerTool`, `vscode.window.createTerminal`, `shellIntegration.executeCommand` and `onDidEndTerminalShellExecution`; the fake adapter returns deterministic stubs for tests.

## Quality Gates

- **QG-1**: Unit tests are green with at least 22 tests across TimeTracker, ToolLogger, TaskManager, Models, Orchestrator and VS Code Adapter stub coverage.

## Getting Started

### Prerequisites

- Python 3.11+
- `pytest` do testów jednostkowych
- `pydantic` do modeli danych

### Installation

1. Zainstaluj zależności projektu:

   ```bash
   pip install pydantic pytest
   ```

2. Faza 1 nie wymaga Docker. Izolacja tasków jest realizowana przez katalogi tymczasowe.

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
