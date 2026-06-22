"""AI_Tester v2 - Orchestrator.

The main orchestrator class coordinating the AI_Tester v2 workflow.
Manages task lifecycle, timing, logging and OpenRouter model execution.
"""

from pathlib import Path
from typing import Any, List, Mapping, Protocol
import warnings

from agents.openrouter_adapter import OpenRouterAdapter
from agents.openrouter_models import OpenRouterRequestMetadata
from orchestrator.config import Config
from orchestrator.prompt_loader import PromptLoader, PromptLoaderError
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


class PromptLoaderIntegrationError(WorkflowError):
    """Raised when PromptLoader fails due to missing or invalid AI_Instruction path."""

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
        if adapter is None and not hasattr(config, "openrouter_config"):
            raise TypeError(
                "config must implement openrouter_config() when no adapter is provided"
            )
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
        self.prompt_loader = self._create_prompt_loader(config)

    def close(self) -> None:
        """Close the adapter when owned by this orchestrator.

        Delegates to the adapter's ``close()`` only when the orchestrator
        created the adapter itself (i.e. no adapter was injected).
        Safe to call multiple times.
        """
        if getattr(self, "_default_adapter", False) and hasattr(self.adapter, "close"):
            self.adapter.close()  # type: ignore[union-attr]

    def __enter__(self) -> "Orchestrator":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def __del__(self) -> None:
        if getattr(self, "_default_adapter", False) and hasattr(self.adapter, "close"):
            warnings.warn(
                "Orchestrator was garbage-collected without calling close(). "
                "Use a context manager (``with Orchestrator(...) as o``) or "
                "call ``close()`` explicitly to avoid resource leaks.",
                ResourceWarning,
                stacklevel=2,
            )
            self.close()  # type: ignore[union-attr]

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

    def _create_prompt_loader(self, config: Config) -> PromptLoader | None:
        ai_path = getattr(config, "AI_INSTRUCTION_PATH", "")
        if not ai_path:
            return None
        try:
            return PromptLoader(ai_path)
        except PromptLoaderError as exc:
            raise PromptLoaderIntegrationError(
                f"Failed to initialize PromptLoader: {exc}"
            ) from exc

    def _build_prompt_metadata(self) -> dict[str, Any]:
        if self.prompt_loader is None:
            return {}
        sources = self.prompt_loader.sources
        return {
            "prompt_sources": {
                "plan": sources.get("plan", ""),
                "implement": sources.get("implement", ""),
                "review": sources.get("review", ""),
            }
        }

    def _build_plan_prompt(self, task: Task, workspace_path: str | Path) -> str:
        if self.prompt_loader is not None:
            return self.prompt_loader.render_plan_prompt(task, workspace_path)
        return (
            f"Plan for task {task.task_id}: "
            f"Implement {task.task_type} functionality in {task.repo}\n\n"
            f"Proponowane Rozwiazanie\n"
            f"Plan Implementacji\n"
            f"Definition of Done"
        )

    def _build_implement_prompt(
        self, task: Task, plan_content: str, workspace_path: str | Path
    ) -> str:
        if self.prompt_loader is not None:
            return self.prompt_loader.render_implement_prompt(
                task, plan_content, workspace_path
            )
        return (
            f"Implement {task.task_type} functionality in {task.repo}.\n\n"
            f"Approved plan:\n{plan_content}"
        )

    def _build_review_prompt(
        self,
        task: Task,
        plan_content: str,
        implementation_summary: str,
        workspace_path: str | Path,
    ) -> str:
        if self.prompt_loader is not None:
            return self.prompt_loader.render_review_prompt(
                task, plan_content, implementation_summary, workspace_path
            )
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
                    request_id=getattr(completion, "request_id", None),
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
                plan_prompt = self._build_plan_prompt(task, workspace_path)
                plan_completion = active_adapter.generate(
                    prompt_or_messages=plan_prompt,
                    role="plan",
                )
                plan_content = self._completion_content(plan_completion)
                self.validate_plan_structure(plan_content)
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
                implementation_prompt = self._build_implement_prompt(
                    task, plan_content, workspace_path
                )
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
                    task, plan_content, implementation_summary, workspace_path
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

            prompt_metadata = self._build_prompt_metadata()
            prompt_lengths = {
                "plan": len(plan_prompt),
                "implement": len(implementation_prompt),
                "review": len(review_prompt),
            }

            return TaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                repo=task.repo,
                model=self.config.DEFAULT_MODEL,
                judge_model=(
                    self.config.OPENROUTER_JUDGE_MODEL
                    or self.config.judge_model
                    or self.config.DEFAULT_MODEL
                ),
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
                    "prompt_lengths": prompt_lengths,
                    "review": review_payload,
                    **prompt_metadata,
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
    from agents.openrouter_models import OpenRouterConfig

    # Setup dummy config
    class MockConfig:
        SOURCE_REPO_PATH = "dummy_src"
        TEMP_BASE_DIR = "./temp_tasks"
        DEFAULT_MODEL = "gpt-4"
        OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
        OPENROUTER_API_KEY_ENV_VAR = "OPENROUTER_API_KEY"
        OPENROUTER_HTTP_REFERER = None
        OPENROUTER_APP_TITLE = "AI_Tester v2"
        OPENROUTER_APP_CATEGORIES: list[str] = []
        OPENROUTER_TIMEOUT_SECONDS = 30.0
        OPENROUTER_MAX_RETRIES = 2
        OPENROUTER_RETRY_BACKOFF_SECONDS = 1.0
        OPENROUTER_MAX_TOKENS = 4096
        OPENROUTER_TEMPERATURE = 0.2
        OPENROUTER_PLAN_MODEL = None
        OPENROUTER_IMPLEMENT_MODEL = None
        OPENROUTER_JUDGE_MODEL = None

        def openrouter_config(self) -> OpenRouterConfig:
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
                    "plan": self.OPENROUTER_PLAN_MODEL or self.DEFAULT_MODEL,
                    "implement": self.OPENROUTER_IMPLEMENT_MODEL or self.DEFAULT_MODEL,
                    "judge": self.OPENROUTER_JUDGE_MODEL or self.DEFAULT_MODEL,
                },
            )

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
