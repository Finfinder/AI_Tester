"""Unit tests for the Orchestrator class."""

import os

import pytest

from orchestrator.orchestrator import (
    Orchestrator,
    PlanValidationError,
    WorkspaceError,
    PromptLoaderIntegrationError,
)
from orchestrator.config import Config
from orchestrator.models import Task


class FakeAdapter:
    """Deterministic OpenRouter adapter test double."""

    def __init__(self):
        self.calls = []

    @staticmethod
    def _completion(role: str):
        model_id = "judge-model" if role == "judge" else "tested-model"
        if role == "plan":
            content = "Proponowane Rozwiazanie\nPlan Implementacji\nDefinition of Done"
        else:
            content = f"Fake {role} response"
        return type(
            "FakeCompletion",
            (),
            {
                "content": content,
                "model": model_id,
                "status_code": 200,
                "duration_seconds": 0.1,
                "input_tokens": 10,
                "output_tokens": 20,
                "total_tokens": 30,
                "estimated_cost_usd": 0.0001,
                "retry_count": 0,
            },
        )()

    def generate(
        self,
        prompt_or_messages,
        role,
        temperature=None,
        max_tokens=None,
        extra_body=None,
    ):
        self.calls.append((role, prompt_or_messages, extra_body))
        return self._completion(role)

    def generate_structured(
        self,
        prompt_or_messages,
        schema,
        role,
        schema_name,
    ):
        self.calls.append((role, prompt_or_messages, {"schema": schema_name}))
        payload = {
            "scores": {
                "plan": 90,
                "implementation": 88,
                "tools_and_terminal": 85,
                "overall": 88,
            },
            "summary": "Fake review.",
            "findings": ["No findings."],
        }
        return payload, self._completion(role)


@pytest.fixture
def fake_adapter():
    """Provide deterministic adapter calls for orchestrator tests."""
    return FakeAdapter()


@pytest.fixture
def config(tmp_path):
    """Provide a test configuration using a temporary directory."""
    temp_dir = str(tmp_path / "temp_tasks")
    os.makedirs(temp_dir, exist_ok=True)
    return Config(TEMP_BASE_DIR=temp_dir)


@pytest.fixture
def ai_instruction_dir(tmp_path):
    """Create a temporary AI_Instruction repository with prompt files."""
    prompts = tmp_path / ".github" / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "plan.prompt.md").write_text(
        "# Plan Prompt\n\nYou are an architect. Plan the implementation.\n",
        encoding="utf-8",
    )
    (prompts / "implement.prompt.md").write_text(
        "# Implement Prompt\n\nYou are a software engineer. Implement the plan.\n",
        encoding="utf-8",
    )
    (prompts / "review.prompt.md").write_text(
        "# Review Prompt\n\nYou are a code reviewer. Review the implementation.\n",
        encoding="utf-8",
    )
    return tmp_path


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


def test_run_task_flow(config: Config, task: Task, fake_adapter: FakeAdapter):
    """Test that run_task executes the full workflow and returns a TaskResult."""
    orchestrator = Orchestrator(config, adapter=fake_adapter)
    result = orchestrator.run_task(task)

    assert result.task_id == "T1"
    assert result.task_type == "feature"
    assert result.repo == "test_repo"
    assert result.model == config.DEFAULT_MODEL
    assert result.judge_model == config.DEFAULT_MODEL
    assert len(result.phases) == 3
    assert all(p.status == "success" for p in result.phases)
    assert result.time > 0
    assert result.details["prompt_lengths"] == {
        "plan": len(fake_adapter.calls[0][1]),
        "implement": len(fake_adapter.calls[1][1]),
        "review": len(fake_adapter.calls[2][1]),
    }
    assert [request.role for request in result.openrouter_requests] == [
        "plan",
        "implement",
        "judge",
    ]
    assert len(fake_adapter.calls) == 3


def test_run_task_uses_configured_judge_model(
    config: Config, task: Task, fake_adapter: FakeAdapter
):
    """Config.judge_model is used as the default judge model when OPENROUTER_JUDGE_MODEL is unset."""
    config.judge_model = "openai/gpt-4.1"
    orchestrator = Orchestrator(config, adapter=fake_adapter)

    result = orchestrator.run_task(task)

    assert result.judge_model == "openai/gpt-4.1"
    assert config.openrouter_config().models["judge"] == "openai/gpt-4.1"


def test_run_task_prefers_openrouter_judge_model(
    config: Config, task: Task, fake_adapter: FakeAdapter
):
    """OPENROUTER_JUDGE_MODEL takes precedence over Config.judge_model."""
    config.judge_model = "openai/gpt-4.1"
    config.OPENROUTER_JUDGE_MODEL = "anthropic/claude-3.5-sonnet"
    orchestrator = Orchestrator(config, adapter=fake_adapter)

    result = orchestrator.run_task(task)

    assert result.judge_model == "anthropic/claude-3.5-sonnet"
    assert config.openrouter_config().models["judge"] == "anthropic/claude-3.5-sonnet"


def test_run_benchmark_flow(config: Config, source_dir: str, fake_adapter: FakeAdapter):
    """Test that run_benchmark executes multiple tasks and returns a BenchmarkResult."""
    tasks = [
        Task(task_id="T1", task_type="feature", repo="r1", source=source_dir),
        Task(task_id="T2", task_type="debug", repo="r2", source=source_dir),
    ]
    orchestrator = Orchestrator(config, adapter=fake_adapter)
    result = orchestrator.run_benchmark(
        tasks=tasks, model="gpt-4", judge_model="gpt-4-turbo"
    )

    assert result.model == "gpt-4"
    assert result.judge_model == "gpt-4-turbo"
    assert len(result.tasks) == 2
    assert result.total_time_seconds > 0
    assert result.tasks[0].task_id == "T1"
    assert result.tasks[1].task_id == "T2"
    assert all(
        len(task_result.openrouter_requests) == 3 for task_result in result.tasks
    )


def test_create_adapter_uses_benchmark_models(config: Config):
    """Test benchmark-specific model overrides on the default adapter."""
    orchestrator = Orchestrator(config)
    adapter = orchestrator._create_adapter(
        model="tested-model", judge_model="judge-model"
    )

    try:
        assert adapter.config.models == {
            "plan": "tested-model",
            "implement": "tested-model",
            "judge": "judge-model",
        }
    finally:
        adapter.close()


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


class FakeAdapterBadPlan:
    """Adapter that returns a plan missing required sections."""

    def __init__(self):
        self.calls = []

    def generate(
        self,
        prompt_or_messages,
        role,
        temperature=None,
        max_tokens=None,
        extra_body=None,
    ):
        self.calls.append((role, prompt_or_messages, extra_body))
        return type(
            "FakeCompletion",
            (),
            {
                "content": "This is a bad plan without required headings.",
                "model": "tested-model",
                "status_code": 200,
                "duration_seconds": 0.1,
                "input_tokens": 10,
                "output_tokens": 20,
                "total_tokens": 30,
                "estimated_cost_usd": 0.0001,
                "retry_count": 0,
            },
        )()

    def generate_structured(self, *args, **kwargs):
        raise NotImplementedError


class FakeAdapterGoodPlan:
    """Adapter that returns a plan with all required sections."""

    def __init__(self):
        self.calls = []

    def generate(
        self,
        prompt_or_messages,
        role,
        temperature=None,
        max_tokens=None,
        extra_body=None,
    ):
        self.calls.append((role, prompt_or_messages, extra_body))
        return type(
            "FakeCompletion",
            (),
            {
                "content": (
                    "Proponowane Rozwiazanie\nPlan Implementacji\nDefinition of Done"
                ),
                "model": "tested-model",
                "status_code": 200,
                "duration_seconds": 0.1,
                "input_tokens": 10,
                "output_tokens": 20,
                "total_tokens": 30,
                "estimated_cost_usd": 0.0001,
                "retry_count": 0,
            },
        )()

    def generate_structured(self, *args, **kwargs):
        raise NotImplementedError


def test_run_task_validates_plan_from_model_response(config: Config, source_dir):
    """Plan validation must run on model output, not on the prompt.

    If the adapter returns content missing required sections, run_task
    must raise PlanValidationError - proving validation targets the
    model's response rather than the outbound prompt.
    """
    orchestrator = Orchestrator(config, adapter=FakeAdapterBadPlan())
    task = Task(
        task_id="T_BAD_PLAN",
        task_type="feature",
        repo="test_repo",
        source=source_dir,
    )
    with pytest.raises(PlanValidationError, match="missing required sections"):
        orchestrator.run_task(task)


def test_run_task_accepts_valid_plan_from_model(config: Config, source_dir):
    """A well-structured plan from the model must pass validation.

    Uses a fake adapter whose generate() returns content containing
    all required headings, so run_task proceeds past the plan phase.
    """
    orchestrator = Orchestrator(config, adapter=FakeAdapterGoodPlan())
    task = Task(
        task_id="T_GOOD_PLAN",
        task_type="feature",
        repo="test_repo",
        source=source_dir,
    )
    # Should not raise PlanValidationError; will fail later in review
    # phase because FakeAdapterGoodPlan.generate_structured is not
    # implemented - that is acceptable for this test's scope.
    with pytest.raises(NotImplementedError):
        orchestrator.run_task(task)


# ---------------------------------------------------------------------------
# PromptLoader integration tests
# ---------------------------------------------------------------------------


def test_orchestrator_falls_back_without_ai_instruction_path(
    config: Config, task: Task, fake_adapter: FakeAdapter
):
    """Without AI_INSTRUCTION_PATH, orchestrator uses built-in placeholder prompts."""
    orchestrator = Orchestrator(config, adapter=fake_adapter)
    assert orchestrator.prompt_loader is None
    result = orchestrator.run_task(task)
    assert result.task_id == "T1"
    assert "prompt_sources" not in result.details
    assert result.details["prompt_lengths"] == {
        "plan": len(fake_adapter.calls[0][1]),
        "implement": len(fake_adapter.calls[1][1]),
        "review": len(fake_adapter.calls[2][1]),
    }


def test_orchestrator_uses_prompt_loader_when_configured(
    config: Config,
    task: Task,
    fake_adapter: FakeAdapter,
    ai_instruction_dir,
):
    """With AI_INSTRUCTION_PATH set, prompts come from AI_Instruction templates."""
    config.AI_INSTRUCTION_PATH = str(ai_instruction_dir)
    orchestrator = Orchestrator(config, adapter=fake_adapter)
    assert orchestrator.prompt_loader is not None

    result = orchestrator.run_task(task)
    assert result.task_id == "T1"
    assert "prompt_sources" in result.details
    sources = result.details["prompt_sources"]
    assert "plan" in sources
    assert "implement" in sources
    assert "review" in sources
    assert os.path.join(".github", "prompts", "plan.prompt.md") in sources["plan"]


def test_orchestrator_prompt_loader_missing_path_raises(
    config: Config,
    task: Task,
    fake_adapter: FakeAdapter,
):
    """Invalid AI_INSTRUCTION_PATH raises PromptLoaderIntegrationError."""
    config.AI_INSTRUCTION_PATH = "/nonexistent/ai_instruction_path"
    with pytest.raises(
        PromptLoaderIntegrationError, match="Failed to initialize PromptLoader"
    ):
        Orchestrator(config, adapter=fake_adapter)


def test_run_task_flow_with_prompt_loader_sends_ai_instruction_content(
    config: Config,
    task: Task,
    fake_adapter: FakeAdapter,
    ai_instruction_dir,
):
    """Prompts sent to adapter contain AI_Instruction template content."""
    config.AI_INSTRUCTION_PATH = str(ai_instruction_dir)
    orchestrator = Orchestrator(config, adapter=fake_adapter)
    orchestrator.run_task(task)

    assert len(fake_adapter.calls) == 3
    plan_prompt = fake_adapter.calls[0][1]
    implement_prompt = fake_adapter.calls[1][1]
    review_prompt = fake_adapter.calls[2][1]

    assert "You are an architect. Plan the implementation." in plan_prompt
    assert "You are a software engineer. Implement the plan." in implement_prompt
    assert "You are a code reviewer. Review the implementation." in review_prompt
