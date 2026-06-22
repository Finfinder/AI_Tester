"""Unit tests for PromptLoader."""

from __future__ import annotations

import os

import pytest

from orchestrator.models import Task
from orchestrator.prompt_loader import (
    PromptLoader,
    PromptLoaderError,
    UndefinedVariableError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


_PLAN_TEMPLATE = """# Plan Prompt

You are an architect. Plan the implementation for {{task.id}}.
"""

_IMPLEMENT_TEMPLATE = """# Implement Prompt

You are a software engineer. Implement the plan for {{task.repo}}.
"""

_REVIEW_TEMPLATE = """# Review Prompt

You are a code reviewer. Review the implementation.
"""


@pytest.fixture
def ai_instruction_dir(tmp_path):
    """Create a temporary AI_Instruction repository with prompt files."""
    prompts = tmp_path / ".github" / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "plan.prompt.md").write_text(_PLAN_TEMPLATE, encoding="utf-8")
    (prompts / "implement.prompt.md").write_text(_IMPLEMENT_TEMPLATE, encoding="utf-8")
    (prompts / "review.prompt.md").write_text(_REVIEW_TEMPLATE, encoding="utf-8")
    return tmp_path


@pytest.fixture
def loader(ai_instruction_dir):
    return PromptLoader(ai_instruction_dir)


@pytest.fixture
def task():
    return Task(
        task_id="T1",
        task_type="feature",
        repo="test_repo",
        source="C:/ai_tester/fixtures/source",
    )


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def test_loader_loads_all_templates(ai_instruction_dir):
    loaded = PromptLoader(ai_instruction_dir)
    assert "plan" in loaded.sources
    assert "implement" in loaded.sources
    assert "review" in loaded.sources
    assert loaded.sources["plan"].endswith(
        os.path.join(".github", "prompts", "plan.prompt.md")
    )


def test_loader_missing_plan_prompt(tmp_path):
    prompts = tmp_path / ".github" / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "implement.prompt.md").write_text(_IMPLEMENT_TEMPLATE, encoding="utf-8")
    (prompts / "review.prompt.md").write_text(_REVIEW_TEMPLATE, encoding="utf-8")

    with pytest.raises(
        PromptLoaderError, match="Missing required prompt file for phase 'plan'"
    ):
        PromptLoader(tmp_path)


def test_loader_missing_implement_prompt(tmp_path):
    prompts = tmp_path / ".github" / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "plan.prompt.md").write_text(_PLAN_TEMPLATE, encoding="utf-8")
    (prompts / "review.prompt.md").write_text(_REVIEW_TEMPLATE, encoding="utf-8")

    with pytest.raises(
        PromptLoaderError, match="Missing required prompt file for phase 'implement'"
    ):
        PromptLoader(tmp_path)


def test_loader_missing_review_prompt(tmp_path):
    prompts = tmp_path / ".github" / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "plan.prompt.md").write_text(_PLAN_TEMPLATE, encoding="utf-8")
    (prompts / "implement.prompt.md").write_text(_IMPLEMENT_TEMPLATE, encoding="utf-8")

    with pytest.raises(
        PromptLoaderError, match="Missing required prompt file for phase 'review'"
    ):
        PromptLoader(tmp_path)


def test_loader_missing_root_directory(tmp_path):
    missing = tmp_path / "nonexistent"
    with pytest.raises(PromptLoaderError, match="Missing required prompt file"):
        PromptLoader(missing)


# ---------------------------------------------------------------------------
# load_prompt with template variables
# ---------------------------------------------------------------------------


def test_load_prompt_substitutes_variables(loader):
    context = {"task.id": "T1"}
    prompt = loader.load_prompt("plan", context)
    assert "T1" in prompt
    assert "{{task.id}}" not in prompt


def test_load_prompt_undefined_variable_raises(loader):
    with pytest.raises(UndefinedVariableError, match="undefined"):
        loader.load_prompt("plan", {})


def test_load_prompt_with_repo_language(loader):
    context = {"task.repo": "my_repo"}
    prompt = loader.load_prompt("implement", context)
    assert "my_repo" in prompt
    assert "{{task.repo}}" not in prompt


def test_load_prompt_unknown_name_raises(loader):
    with pytest.raises(KeyError):
        loader.load_prompt("unknown", {})


# ---------------------------------------------------------------------------
# Rendering - plan
# ---------------------------------------------------------------------------


def test_render_plan_prompt_contains_template(loader, task):
    prompt = loader.render_plan_prompt(task, "/workspaces/task-1")
    assert "# Plan Prompt" in prompt
    assert "You are an architect." in prompt


def test_render_plan_prompt_contains_task_context(loader, task):
    prompt = loader.render_plan_prompt(task, "/workspaces/task-1")
    assert "**task_id**: T1" in prompt
    assert "**task_type**: feature" in prompt
    assert "**repo**: test_repo" in prompt
    assert "**source**: C:/ai_tester/fixtures/source" in prompt
    assert "**workspace_path**: /workspaces/task-1" in prompt


def test_render_plan_prompt_with_issue(loader, task):
    prompt = loader.render_plan_prompt(task, "/workspaces/task-1", issue="#42")
    assert "**issue**: #42" in prompt


def test_render_plan_prompt_without_issue_no_issue_line(loader, task):
    prompt = loader.render_plan_prompt(task, "/workspaces/task-1")
    assert "**issue**" not in prompt


def test_render_plan_prompt_does_not_contain_full_spec(loader, task):
    prompt = loader.render_plan_prompt(task, "/workspaces/task-1")
    assert "acceptance criteria" not in prompt.lower()
    assert "definition of done" not in prompt.lower()


def test_render_plan_prompt_with_extra_context(loader, task):
    prompt = loader.render_plan_prompt(
        task,
        "/workspaces/task-1",
        extra_context={"task.id": "T99"},
    )
    assert "T99" in prompt


# ---------------------------------------------------------------------------
# Rendering - implement
# ---------------------------------------------------------------------------


def test_render_implement_prompt_contains_template(loader, task):
    prompt = loader.render_implement_prompt(
        task,
        "My plan content",
        "/workspaces/task-1",
    )
    assert "# Implement Prompt" in prompt


def test_render_implement_prompt_contains_plan(loader, task):
    prompt = loader.render_implement_prompt(
        task,
        "My plan content",
        "/workspaces/task-1",
    )
    assert "## Approved Plan" in prompt
    assert "My plan content" in prompt


def test_render_implement_prompt_contains_task_context(loader, task):
    prompt = loader.render_implement_prompt(task, "plan", "/workspaces/task-1")
    assert "**task_id**: T1" in prompt


# ---------------------------------------------------------------------------
# Rendering - review
# ---------------------------------------------------------------------------


def test_render_review_prompt_contains_template(loader, task):
    prompt = loader.render_review_prompt(
        task,
        "My plan",
        "My implementation summary",
        "/workspaces/task-1",
    )
    assert "# Review Prompt" in prompt


def test_render_review_prompt_contains_plan(loader, task):
    prompt = loader.render_review_prompt(
        task,
        "My plan",
        "My implementation summary",
        "/workspaces/task-1",
    )
    assert "## Approved Plan" in prompt
    assert "My plan" in prompt


def test_render_review_prompt_contains_implementation_summary(loader, task):
    prompt = loader.render_review_prompt(
        task,
        "My plan",
        "My implementation summary",
        "/workspaces/task-1",
    )
    assert "## Implementation Summary" in prompt
    assert "My implementation summary" in prompt


def test_render_review_prompt_contains_ai_tester_rubric(loader, task):
    prompt = loader.render_review_prompt(
        task,
        "My plan",
        "My implementation summary",
        "/workspaces/task-1",
    )
    assert "## AI_Tester Quality Rubric" in prompt
    assert "plan adherence" in prompt.lower()


def test_render_review_prompt_contains_task_context(loader, task):
    prompt = loader.render_review_prompt(task, "plan", "summary", "/workspaces/task-1")
    assert "**task_id**: T1" in prompt


# ---------------------------------------------------------------------------
# Optional references
# ---------------------------------------------------------------------------


def test_render_review_prompt_includes_owasp_when_present(tmp_path):
    prompts = tmp_path / ".github" / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "plan.prompt.md").write_text("# Plan\n", encoding="utf-8")
    (prompts / "implement.prompt.md").write_text("# Implement\n", encoding="utf-8")
    (prompts / "review.prompt.md").write_text("# Review\n", encoding="utf-8")
    docs = tmp_path / "Docs"
    docs.mkdir()
    (docs / "OWASP_TOP_30_PLUS.md").write_text(
        "# OWASP\nSecurity content",
        encoding="utf-8",
    )

    loaded = PromptLoader(tmp_path)
    task = Task(task_id="T1", task_type="feature", repo="r", source="/s")
    prompt = loaded.render_review_prompt(task, "plan", "summary", "/ws")
    assert "OWASP Security Reference" in prompt
    assert "Security content" in prompt


def test_render_review_prompt_omits_owasp_when_missing(tmp_path):
    prompts = tmp_path / ".github" / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "plan.prompt.md").write_text("# Plan\n", encoding="utf-8")
    (prompts / "implement.prompt.md").write_text("# Implement\n", encoding="utf-8")
    (prompts / "review.prompt.md").write_text("# Review\n", encoding="utf-8")

    loaded = PromptLoader(tmp_path)
    task = Task(task_id="T1", task_type="feature", repo="r", source="/s")
    prompt = loaded.render_review_prompt(task, "plan", "summary", "/ws")
    assert "OWASP Security Reference" not in prompt


def test_render_review_prompt_includes_structure_validation_when_examples_present(
    tmp_path,
):
    prompts = tmp_path / ".github" / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "plan.prompt.md").write_text("# Plan\n", encoding="utf-8")
    (prompts / "implement.prompt.md").write_text("# Implement\n", encoding="utf-8")
    (prompts / "review.prompt.md").write_text("# Review\n", encoding="utf-8")
    plan_skill_dir = tmp_path / ".github" / "skills" / "architecture-designing"
    research_skill_dir = tmp_path / ".github" / "skills" / "task-analysing"
    plan_skill_dir.mkdir(parents=True)
    research_skill_dir.mkdir(parents=True)
    (plan_skill_dir / "plan.example.md").write_text(
        "# Plan example\n", encoding="utf-8"
    )
    (research_skill_dir / "research.example.md").write_text(
        "# Research example\n",
        encoding="utf-8",
    )

    loaded = PromptLoader(tmp_path)
    task = Task(task_id="T1", task_type="feature", repo="r", source="/s")
    prompt = loaded.render_review_prompt(task, "plan", "summary", "/ws")

    assert "Artifact Structure Validation" in prompt
    assert "plan.example.md" in prompt
    assert "research.example.md" in prompt
    assert "Task details" in prompt
    assert "Business impact" in prompt


def test_render_review_prompt_includes_skill_mapping_reference(tmp_path):
    prompts = tmp_path / ".github" / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "plan.prompt.md").write_text("# Plan\n", encoding="utf-8")
    (prompts / "implement.prompt.md").write_text("# Implement\n", encoding="utf-8")
    (prompts / "review.prompt.md").write_text("# Review\n", encoding="utf-8")

    loaded = PromptLoader(tmp_path)
    task = Task(task_id="T1", task_type="feature", repo="r", source="/s")
    prompt = loaded.render_review_prompt(task, "plan", "summary", "/ws")

    assert "AI_Instruction Skills as Judge Criteria" in prompt
    assert "Use the following 16 skills as explicit review criteria" in prompt
    assert "`code-reviewing`" in prompt
    assert "`architecture-designing`" in prompt
    assert prompt.count("| `") == 16


def test_render_review_prompt_includes_dependency_report_reference_when_present(
    tmp_path,
):
    prompts = tmp_path / ".github" / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "plan.prompt.md").write_text("# Plan\n", encoding="utf-8")
    (prompts / "implement.prompt.md").write_text("# Implement\n", encoding="utf-8")
    (prompts / "review.prompt.md").write_text("# Review\n", encoding="utf-8")
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "get-dependency-freshness-report.ps1").write_text(
        "# Dependency freshness report",
        encoding="utf-8",
    )

    loaded = PromptLoader(tmp_path)
    task = Task(task_id="T1", task_type="feature", repo="r", source="/s")
    prompt = loaded.render_review_prompt(task, "plan", "summary", "/ws")

    assert "Dependency Freshness Report Reference" in prompt
    assert "Dependency freshness report" in prompt


# ---------------------------------------------------------------------------
# Cache invalidation
# ---------------------------------------------------------------------------


def test_invalidate_cache_reloads_templates_and_resets_skill_mapping(tmp_path):
    prompts = tmp_path / ".github" / "prompts"
    prompts.mkdir(parents=True)
    plan_prompt = prompts / "plan.prompt.md"
    plan_prompt.write_text("# Plan\n{{task.id}}\n", encoding="utf-8")
    (prompts / "implement.prompt.md").write_text("# Implement\n", encoding="utf-8")
    (prompts / "review.prompt.md").write_text("# Review\n", encoding="utf-8")

    loaded = PromptLoader(tmp_path)
    task = Task(task_id="T1", task_type="feature", repo="r", source="/s")
    assert "T1" in loaded.render_plan_prompt(task, "/ws")

    plan_prompt.write_text("# Updated Plan\n{{task.id}}\n", encoding="utf-8")
    assert "Updated Plan" not in loaded.render_plan_prompt(task, "/ws")

    loaded.invalidate_cache()

    prompt = loaded.render_plan_prompt(task, "/ws")
    assert "Updated Plan" in prompt
    assert len(loaded._get_judge_criteria()) == 16


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_rendering_is_deterministic(loader, task):
    prompt1 = loader.render_plan_prompt(task, "/workspaces/task-1")
    prompt2 = loader.render_plan_prompt(task, "/workspaces/task-1")
    assert prompt1 == prompt2
