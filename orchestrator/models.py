"""AI_Tester v2 - Data models for the orchestrator."""

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# --- Core Models ---


class Task(BaseModel):
    """Defines a single task to be executed by the orchestrator."""

    model_config = ConfigDict(from_attributes=True)

    task_id: str = Field(..., description="Unique identifier for the task.")
    task_type: str = Field(
        ..., description="Type of task (e.g., feature, refactor, debug)."
    )
    repo: str = Field(..., description="Target repository/module.")
    source: str = Field(
        ..., description="Source of the task (e.g., local file path, URL)."
    )
    status: str = Field(
        "pending",
        description="Current status of the task (pending, running, completed, failed).",
    )


class PhaseResult(BaseModel):
    """Result summary for a major phase (plan, implement, review)."""

    model_config = ConfigDict(from_attributes=True)

    phase: str = Field(
        ..., description="The phase name (e.g., 'plan', 'implement', 'review')."
    )
    start_time: Optional[datetime] = Field(None, description="Start time of the phase.")
    end_time: Optional[datetime] = Field(None, description="End time of the phase.")
    duration_seconds: Optional[float] = Field(
        None, description="Total duration of the phase in seconds."
    )
    status: str = Field(
        "pending", description="Status of the phase (success, failure, incomplete)."
    )
    artifacts: Dict[str, Any] = Field(
        default_factory=dict, description="Artifacts generated during this phase."
    )


class TaskResult(BaseModel):
    """Aggregated result for a single task execution."""

    model_config = ConfigDict(from_attributes=True)

    task_id: str
    task_type: str
    repo: str
    model: str = Field(..., description="The primary model used for the task.")
    judge_model: str = Field(..., description="The model used for judging the task.")
    phases: List[PhaseResult] = Field(
        default_factory=list, description="Timeline of phases executed."
    )
    time: float = Field(..., description="Total execution time for the task.")
    scores: Dict[str, float] = Field(
        default_factory=dict, description="Scores from different evaluation metrics."
    )
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Detailed output and findings."
    )


class BenchmarkResult(BaseModel):
    """Aggregated result for a set of benchmarks."""

    model_config = ConfigDict(from_attributes=True)

    model: str
    judge_model: str
    tasks: List[TaskResult]
    ranking: Dict[str, int] = Field(
        default_factory=dict, description="Model ranking based on performance (1-100)."
    )
    total_time_seconds: float


def to_dict(model_instance: BaseModel) -> Dict[str, Any]:
    """Convert a Pydantic model instance to a serializable dictionary."""
    return model_instance.model_dump()
