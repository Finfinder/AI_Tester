"""Unit tests for the Orchestrator class."""

import os

import pytest

from orchestrator.orchestrator import (
    Orchestrator,
    PlanValidationError,
    WorkspaceError,
)
from orchestrator.config import Config
from orchestrator.models import Task


@pytest.fixture
def config(tmp_path):
    """Provide a test configuration using a temporary directory."""
    temp_dir = str(tmp_path / "temp_tasks")
    os.makedirs(temp_dir, exist_ok=True)
    return Config(TEMP_BASE_DIR=temp_dir)


@pytest.fixture
def source_dir(tmp_path):
    """Provide a dummy source directory with a Python file."""
    src = tmp_path / "source_repo"
    src.mkdir()
    (src / "main.py").write_text("print('hello')\n")
    return str(src)


@pytest.fixture
def task(source_dir):
    """Provide a test Task."""
    return Task(
        task_id="T1",
        task_type="feature",
        repo="test_repo",
        source=source_dir,
    )


def test_run_task_flow(config: Config, task: Task):
    """Test that run_task executes the full workflow and returns a TaskResult."""
    orchestrator = Orchestrator(config)
    result = orchestrator.run_task(task)

    assert result.task_id == "T1"
    assert result.task_type == "feature"
    assert result.repo == "test_repo"
    assert result.model == config.DEFAULT_MODEL
    assert result.judge_model == config.DEFAULT_JUDGE_MODEL
    assert len(result.phases) == 3
    assert all(p.status == "success" for p in result.phases)
    assert result.time > 0


def test_run_benchmark_flow(config: Config, source_dir: str):
    """Test that run_benchmark executes multiple tasks and returns a BenchmarkResult."""
    tasks = [
        Task(task_id="T1", task_type="feature", repo="r1", source=source_dir),
        Task(task_id="T2", task_type="debug", repo="r2", source=source_dir),
    ]
    orchestrator = Orchestrator(config)
    result = orchestrator.run_benchmark(
        tasks=tasks, model="gpt-4", judge_model="gpt-4-turbo"
    )

    assert result.model == "gpt-4"
    assert result.judge_model == "gpt-4-turbo"
    assert len(result.tasks) == 2
    assert result.total_time_seconds > 0
    assert result.tasks[0].task_id == "T1"
    assert result.tasks[1].task_id == "T2"


def test_validate_plan_structure_valid(config: Config):
    """Test that a well-structured plan passes validation."""
    orchestrator = Orchestrator(config)
    plan = "Proponowane Rozwiazanie\nPlan Implementacji\nDefinition of Done"
    assert orchestrator.validate_plan_structure(plan) is True


def test_validate_plan_structure_empty(config: Config):
    """Test that an empty plan raises PlanValidationError."""
    orchestrator = Orchestrator(config)
    with pytest.raises(PlanValidationError, match="cannot be empty"):
        orchestrator.validate_plan_structure("")


def test_validate_plan_structure_missing_sections(config: Config):
    """Test that a plan missing required sections raises PlanValidationError."""
    orchestrator = Orchestrator(config)
    plan = "Tylko Proponowane Rozwiazanie"
    with pytest.raises(PlanValidationError, match="missing required sections"):
        orchestrator.validate_plan_structure(plan)


def test_run_task_workspace_error(config: Config):
    """Test that run_task raises WorkspaceError for invalid source."""
    orchestrator = Orchestrator(config)
    task = Task(
        task_id="T_BAD",
        task_type="feature",
        repo="bad_repo",
        source="/nonexistent/source/path",
    )
    with pytest.raises(WorkspaceError):
        orchestrator.run_task(task)
