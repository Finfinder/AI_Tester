"""AI_Tester v2 - Orchestrator.

The main orchestrator class coordinating the AI_Tester v2 workflow.
Manages task lifecycle, timing, and logging.
"""

from typing import List
from ai_tester_v2.orchestrator.config import Config
from ai_tester_v2.orchestrator.task_manager import TaskManager, WorkspaceCleanupError
from ai_tester_v2.orchestrator.time_tracker import TimeTracker
from ai_tester_v2.orchestrator.tool_logger import ToolLogger
from ai_tester_v2.orchestrator.models import (
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


class WorkflowError(Exception):
    """Base exception for workflow failures."""

    pass


class PlanValidationError(WorkflowError):
    """Raised when the plan structure is invalid."""

    pass


class WorkspaceError(WorkflowError):
    """Raised when workspace management fails."""

    pass


class Orchestrator:
    """Main orchestrator class coordinating the AI_Tester v2 workflow."""

    def __init__(self, config: Config):
        self.config = config
        self.task_manager = TaskManager(temp_base_dir=config.TEMP_BASE_DIR)
        self.time_tracker = TimeTracker()
        self.tool_logger = ToolLogger(
            log_file_path=f"{config.TEMP_BASE_DIR}/logs/tool_log.json"
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

    def run_task(self, task: Task) -> TaskResult:
        """Execute the full task workflow: Plan -> Implement -> Review."""
        workspace_path = None
        try:
            workspace_path = self.task_manager.create_workspace(
                source_repo=task.source
            )
            self.tool_logger.log_file_operation("create", workspace_path, 0)
        except Exception as exc:
            raise WorkspaceError(f"Failed to set up workspace: {exc}") from exc

        try:
            # Plan Phase
            self.time_tracker.start_phase("plan")
            try:
                plan_content = (
                    f"Plan for task {task.task_id}: "
                    f"Implement {task.task_type} functionality in {task.repo}\n\n"
                    f"Proponowane Rozwiazanie\n"
                    f"Plan Implementacji\n"
                    f"Definition of Done"
                )
                self.validate_plan_structure(plan_content)
                self.tool_logger.log_ai_tool(
                    "plan_generator", task.task_id, plan_content
                )
            except PlanValidationError as exc:
                self.tool_logger.log_ai_tool("plan_generator", task.task_id, str(exc))
                raise
            finally:
                self.time_tracker.stop_phase("plan")

            # Implement Phase
            self.time_tracker.start_phase("implement")
            try:
                self.tool_logger.log_terminal(
                    f"implement {task.task_type}", 0, 0.1, "Implementation placeholder"
                )
            except Exception as exc:
                self.tool_logger.log_terminal("implementation", 1, 0.0, str(exc))
                raise
            finally:
                self.time_tracker.stop_phase("implement")

            # Review Phase
            self.time_tracker.start_phase("review")
            try:
                self.tool_logger.log_ai_tool(
                    "code_reviewer", task.task_id, "Review placeholder"
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
                details={"message": "Workflow completed successfully."},
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

        for task in tasks:
            result = self.run_task(task)
            result.model = model
            result.judge_model = judge_model
            task_results.append(result)
            total_time += result.time

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
