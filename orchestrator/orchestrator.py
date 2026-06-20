"""AI_Tester v2 - Orchestrator.

The main orchestrator class coordinating the AI_Tester v2 workflow.
Manages task lifecycle, timing, logging and OpenRouter model execution.
"""

from typing import Any, List, Mapping, Protocol

from agents.openrouter_adapter import OpenRouterAdapter
from agents.openrouter_models import OpenRouterRequestMetadata
from orchestrator.config import Config
from orchestrator.task_manager import TaskManager, WorkspaceCleanupError
from orchestrator.time_tracker import TimeTracker
from orchestrator.tool_logger import ToolLogger
from orchestrator.models import (
    Task,
    TaskResult,
    BenchmarkResult,
    PhaseResult,
)

_REQUIRED_PLAN_SECTIONS = [
    "Proponowane Rozwiazanie",
    "Plan Implementacji",
    "Definition of Done",
]

_REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "object",
            "properties": {
                "plan": {"type": "integer", "minimum": 0, "maximum": 100},
                "implementation": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                },
                "tools_and_terminal": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                },
                "overall": {"type": "integer", "minimum": 0, "maximum": 100},
            },
            "required": ["plan", "implementation", "tools_and_terminal", "overall"],
            "additionalProperties": False,
        },
        "summary": {"type": "string"},
        "findings": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["scores", "summary", "findings"],
    "additionalProperties": False,
}


class WorkflowError(Exception):
    """Base exception for workflow failures."""

    pass


class PlanValidationError(WorkflowError):
    """Raised when the plan structure is invalid."""

    pass


class WorkspaceError(WorkflowError):
    """Raised when workspace management fails."""

    pass


class AdapterProtocol(Protocol):
    """Minimal protocol for OpenRouter adapters used by tests and production."""

    def generate(
        self,
        prompt_or_messages: str | list[dict[str, Any]],
        role: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        extra_body: Mapping[str, object] | None = None,
    ) -> object:
        """Generate a completion for a role."""

    def generate_structured(
        self,
        prompt_or_messages: str | list[dict[str, Any]],
        schema: dict[str, object],
        role: str,
        schema_name: str,
    ) -> tuple[dict[str, object], object]:
        """Generate and validate a structured completion for a role."""


class Orchestrator:
    """Main orchestrator class coordinating the AI_Tester v2 workflow."""

    def __init__(self, config: Config, adapter: AdapterProtocol | None = None) -> None:
        self.config = config
        self._default_adapter = adapter is None
        self.task_manager = TaskManager(temp_base_dir=config.TEMP_BASE_DIR)
        self.time_tracker = TimeTracker()
        self.tool_logger = ToolLogger(
            log_file_path=f"{config.TEMP_BASE_DIR}/logs/tool_log.json"
        )
        self.adapter = adapter or OpenRouterAdapter(
            config=config.openrouter_config(), logger=self.tool_logger
        )

    def validate_plan_structure(self, plan_content: str) -> bool:
        """Validate the structure of the provided plan against required sections.

        Checks for presence of key sections from plan.example.md.
        """
        if not plan_content or not plan_content.strip():
            raise PlanValidationError("Plan content cannot be empty.")

        missing = [
            section
            for section in _REQUIRED_PLAN_SECTIONS
            if section not in plan_content
        ]
        if missing:
            raise PlanValidationError(
                f"Plan is missing required sections: {', '.join(missing)}"
            )
        return True

    def _build_plan_prompt(self, task: Task) -> str:
        return (
            f"Plan for task {task.task_id}: "
            f"Implement {task.task_type} functionality in {task.repo}\n\n"
            f"Proponowane Rozwiazanie\n"
            f"Plan Implementacji\n"
            f"Definition of Done"
        )

    def _build_implement_prompt(self, task: Task, plan_content: str) -> str:
        return (
            f"Implement {task.task_type} functionality in {task.repo}.\n\n"
            f"Approved plan:\n{plan_content}"
        )

    def _build_review_prompt(
        self, task: Task, plan_content: str, implementation_summary: str
    ) -> str:
        return (
            "Review the implementation against the plan and AI_Tester quality criteria.\n\n"
            f"Task: {task.task_id} ({task.task_type}) in {task.repo}\n"
            f"Plan:\n{plan_content}\n\n"
            f"Implementation summary:\n{implementation_summary}"
        )

    def _create_adapter(
        self, model: str | None = None, judge_model: str | None = None
    ) -> OpenRouterAdapter:
        config = self.config.openrouter_config()
        if model is not None:
            config.models["plan"] = model
            config.models["implement"] = model
        if judge_model is not None:
            config.models["judge"] = judge_model
        return OpenRouterAdapter(config=config, logger=self.tool_logger)

    def _completion_content(self, completion: object) -> str:
        if hasattr(completion, "content"):
            return str(getattr(completion, "content"))
        return str(completion)

    def _record_openrouter_completion(
        self,
        openrouter_requests: list[OpenRouterRequestMetadata],
        role: str,
        completion: object,
    ) -> None:
        if isinstance(completion, OpenRouterRequestMetadata):
            openrouter_requests.append(completion)
            return
        if hasattr(completion, "model") and hasattr(completion, "status_code"):
            openrouter_requests.append(
                OpenRouterRequestMetadata(
                    role=role,
                    model=str(getattr(completion, "model")),
                    status_code=int(getattr(completion, "status_code")),
                    duration_seconds=float(
                        getattr(completion, "duration_seconds", 0.0)
                    ),
                    input_tokens=getattr(completion, "input_tokens", None),
                    output_tokens=getattr(completion, "output_tokens", None),
                    total_tokens=getattr(completion, "total_tokens", None),
                    estimated_cost_usd=getattr(completion, "estimated_cost_usd", None),
                    retry_count=int(getattr(completion, "retry_count", 0)),
                )
            )

    def run_task(
        self, task: Task, adapter: AdapterProtocol | None = None
    ) -> TaskResult:
        """Execute the full task workflow: Plan -> Implement -> Review."""
        active_adapter = adapter or self.adapter
        workspace_path = None
        try:
            workspace_path = self.task_manager.create_workspace(source_repo=task.source)
            self.tool_logger.log_file_operation("create", workspace_path, 0)
        except Exception as exc:
            raise WorkspaceError(f"Failed to set up workspace: {exc}") from exc

        try:
            openrouter_requests: list[OpenRouterRequestMetadata] = []

            # Plan Phase
            self.time_tracker.start_phase("plan")
            try:
                plan_prompt = self._build_plan_prompt(task)
                self.validate_plan_structure(plan_prompt)
                plan_completion = active_adapter.generate(
                    prompt_or_messages=plan_prompt,
                    role="plan",
                )
                plan_content = self._completion_content(plan_completion)
                self._record_openrouter_completion(
                    openrouter_requests, "plan", plan_completion
                )
            except PlanValidationError as exc:
                self.tool_logger.log_ai_tool("plan_generator", task.task_id, str(exc))
                raise
            finally:
                self.time_tracker.stop_phase("plan")

            # Implement Phase
            self.time_tracker.start_phase("implement")
            try:
                implementation_prompt = self._build_implement_prompt(task, plan_content)
                implementation_completion = active_adapter.generate(
                    prompt_or_messages=implementation_prompt,
                    role="implement",
                )
                implementation_summary = self._completion_content(
                    implementation_completion
                )
                self._record_openrouter_completion(
                    openrouter_requests, "implement", implementation_completion
                )
            finally:
                self.time_tracker.stop_phase("implement")

            # Review Phase
            self.time_tracker.start_phase("review")
            try:
                review_prompt = self._build_review_prompt(
                    task, plan_content, implementation_summary
                )
                review_payload, review_completion = active_adapter.generate_structured(
                    prompt_or_messages=review_prompt,
                    schema=_REVIEW_SCHEMA,
                    role="judge",
                    schema_name="ai_tester_review",
                )
                self._record_openrouter_completion(
                    openrouter_requests, "judge", review_completion
                )
            finally:
                self.time_tracker.stop_phase("review")

            elapsed = self.time_tracker.get_all_elapsed()
            total_time = sum(elapsed.values())

            return TaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                repo=task.repo,
                model=self.config.DEFAULT_MODEL,
                judge_model=self.config.DEFAULT_JUDGE_MODEL,
                phases=[
                    PhaseResult(
                        phase="plan",
                        status="success",
                        duration_seconds=elapsed.get("plan", 0),
                    ),
                    PhaseResult(
                        phase="implement",
                        status="success",
                        duration_seconds=elapsed.get("implement", 0),
                    ),
                    PhaseResult(
                        phase="review",
                        status="success",
                        duration_seconds=elapsed.get("review", 0),
                    ),
                ],
                time=total_time,
                scores={"overall_score": 0.0},
                details={
                    "message": "Workflow completed successfully.",
                    "review": review_payload,
                },
                openrouter_requests=openrouter_requests,
            )
        finally:
            if workspace_path:
                try:
                    self.task_manager.cleanup_workspace(workspace_path)
                    self.tool_logger.log_file_operation("cleanup", workspace_path, 0)
                except WorkspaceCleanupError:
                    self.tool_logger.log_file_operation(
                        "cleanup_failed", workspace_path, 0
                    )

    def run_benchmark(
        self, tasks: List[Task], model: str, judge_model: str
    ) -> BenchmarkResult:
        """Run a benchmark across multiple tasks using specified models."""
        task_results: List[TaskResult] = []
        total_time = 0.0
        benchmark_adapter: OpenRouterAdapter | None = None

        try:
            if self._default_adapter:
                benchmark_adapter = self._create_adapter(
                    model=model, judge_model=judge_model
                )

            for task in tasks:
                result = self.run_task(task, adapter=benchmark_adapter)
                result.model = model
                result.judge_model = judge_model
                task_results.append(result)
                total_time += result.time
        finally:
            if benchmark_adapter is not None:
                benchmark_adapter.close()

        return BenchmarkResult(
            model=model,
            judge_model=judge_model,
            tasks=task_results,
            ranking={},
            total_time_seconds=total_time,
        )


# Example usage (for testing purposes)
if __name__ == "__main__":
    # Setup dummy config
    class MockConfig:
        SOURCE_REPO_PATH = "dummy_src"
        TEMP_BASE_DIR = "./temp_tasks"
        DEFAULT_MODEL = "gpt-4"
        DEFAULT_JUDGE_MODEL = "gpt-3.5"
        PLAN_TEMPLATE_PATH = "dummy/plan.json"
        REPORT_SCHEMA_VERSION = "2.0"

    mock_config = MockConfig()

    # Setup dummy task
    mock_task = Task(
        task_id="T_TEST", task_type="feature", repo="test_repo", source="dummy_src"
    )

    # Initialize and run
    orchestrator = Orchestrator(mock_config)
    try:
        result = orchestrator.run_task(mock_task)
        print("\n--- Workflow Result ---")
        print(f"Task ID: {result.task_id}")
        print(f"Total Time: {result.time:.2f}s")
    except Exception as e:
        print("\n--- Workflow Failed ---")
        print(e)
