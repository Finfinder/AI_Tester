from datetime import datetime

from orchestrator.models import (
    Task,
    PhaseResult,
    TaskResult,
    BenchmarkResult,
)


def test_task_model_serialization():
    """Test Task model serialization and validation."""
    task = Task(task_id="T1", task_type="feature", repo="core", source="src/feature.py")
    data = task.model_dump()
    assert data["task_id"] == "T1"
    assert data["task_type"] == "feature"
    assert data["status"] == "pending"


def test_task_result_serialization():
    """Test TaskResult model serialization and validation."""
    phase = PhaseResult(
        phase="plan",
        start_time=datetime(2026, 1, 1, 12, 0, 0),
        end_time=datetime(2026, 1, 1, 12, 0, 10),
        duration_seconds=10.0,
        status="success",
    )
    task_result = TaskResult(
        task_id="T1",
        task_type="feature",
        repo="core",
        model="GPT-4",
        judge_model="GPT-3.5",
        phases=[phase],
        time=123.45,
        scores={"accuracy": 0.9, "completeness": 0.8},
        details={"notes": "Task completed successfully."},
    )
    data = task_result.model_dump()
    assert data["task_id"] == "T1"
    assert "phases" in data
    assert isinstance(data["phases"][0]["status"], str)


def test_benchmark_result_serialization():
    """Test BenchmarkResult model serialization and validation."""
    task1 = TaskResult(
        task_id="T1",
        task_type="feature",
        repo="core",
        model="GPT-4",
        judge_model="GPT-3.5",
        phases=[],
        time=10.0,
        scores={},
        details={},
    )
    benchmark = BenchmarkResult(
        model="GPT-4",
        judge_model="GPT-3.5",
        tasks=[task1],
        ranking={"GPT-4": 90},
        total_time_seconds=120.0,
    )
    data = benchmark.model_dump()
    assert data["model"] == "GPT-4"
    assert "ranking" in data
    assert data["ranking"]["GPT-4"] == 90
    assert len(data["tasks"]) == 1
