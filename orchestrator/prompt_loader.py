"""AI_Tester v2 - PromptLoader.

Loads and renders AI_Instruction prompts for the Plan -> Implement -> Review workflow.
Prompts are loaded from an AI_Instruction repository and combined with runtime
context (task metadata, workspace path, plan content, implementation summary).

Supports ``{{variable}}`` template substitution via :meth:`load_prompt`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class PromptLoaderError(Exception):
    """Raised when a required AI_Instruction prompt file is missing or invalid."""


class UndefinedVariableError(PromptLoaderError):
    """Raised when a template references a variable that is not supplied."""


@dataclass(frozen=True)
class JudgeSkillCriterion:
    """Skill-backed review criterion exposed to the Judge agent."""

    skill: str
    path: str
    description: str
    criteria: tuple[str, ...]


_VAR_PATTERN = re.compile(r"\{\{([\w.]+)\}\}")


class PromptLoader:
    """Loads AI_Instruction prompt templates and renders them with runtime context.

    The loader reads Markdown prompt files from ``.github/prompts/`` in the
    configured AI_Instruction repository. Templates may contain ``{{variable}}``
    placeholders which are substituted at render time via :meth:`load_prompt`.
    """

    _PROMPT_FILES = {
        "plan": ".github/prompts/plan.prompt.md",
        "implement": ".github/prompts/implement.prompt.md",
        "review": ".github/prompts/review.prompt.md",
    }

    _OPTIONAL_REFERENCES = {
        "security": "Docs/OWASP_TOP_30_PLUS.md",
        "validations": ".github/skills/code-reviewing/references/validations.md",
        "plan_example": ".github/skills/architecture-designing/plan.example.md",
        "research_example": ".github/skills/task-analysing/research.example.md",
        "dependency_report": "scripts/get-dependency-freshness-report.ps1",
    }

    _JUDGE_SKILLS = {
        "code-reviewing": (
            "Code quality and review",
            (
                "verify alignment with the plan and acceptance criteria",
                "check KISS, SOLID, dead code, simplicity, and testability",
                "use the shared validation contract from references/validations.md",
            ),
        ),
        "ensuring-code-quality": (
            "Sonar and local quality gates",
            (
                "check SonarQube for IDE / SonarCloud issues before commit",
                "interpret Quality Gate results without replacing local analyzers",
            ),
        ),
        "ensuring-accessibility": (
            "WCAG 2.1 AA and UI accessibility",
            (
                "verify semantic HTML, ARIA, keyboard navigation, focus, and screen readers",
                "use accessible form and widget patterns",
            ),
        ),
        "testing-ts-js": (
            "TypeScript and JavaScript tests",
            (
                "design unit, integration, and contract tests",
                "verify mock boundaries, typed fixtures, async races, and CI smoke tests",
            ),
        ),
        "testing-e2e": (
            "Playwright end-to-end tests",
            (
                "use accessible locators, test isolation, and external service mocks",
                "debug flaky tests as complete user journeys",
            ),
        ),
        "react-testing": (
            "React tests",
            (
                "test user-visible behavior through RTL and user-event",
                "mock API, providers, routing, and async UI without testing internals",
            ),
        ),
        "implementing-backend": (
            "Production backend",
            (
                "verify API, service layer, transactions, auth, cache, queues, rate limiting, and errors",
                "apply resilience patterns: Circuit Breaker, Retry, Saga",
            ),
        ),
        "node-backend-guidelines": (
            "Node.js backend stability",
            (
                "verify event loop, async I/O, timeouts, AbortController, graceful shutdown, and health checks",
                "avoid synchronous filesystem access in request path",
            ),
        ),
        "engineering-databases": (
            "Databases and SQL",
            (
                "verify normalization, indexes, JOINs, transactions, locks, migrations, and parameterized queries",
                "detect N+1, bad migrations, and raw SQL without bind parameters",
            ),
        ),
        "implementing-frontend": (
            "Frontend components",
            (
                "verify component composition, design tokens, barrel files, and error handling",
                "keep stable component contracts and separation of concerns",
            ),
        ),
        "react-hooks-best-practices": (
            "React hooks",
            (
                "apply Rules of Hooks, exhaustive deps, effect cleanup, and stable custom hooks",
                "detect Strict Effects and dependency mistakes",
            ),
        ),
        "typescript-best-practices": (
            "TypeScript typing",
            (
                "enforce strict typing, unknown instead of any, runtime validation, and safe API boundaries",
                "use unions, branded types, satisfies, and as const without theatrical complexity",
            ),
        ),
        "ts-styling-and-linting": (
            "TS/JS style and linting",
            (
                "verify ESLint, Prettier, import ordering, consistent-type-imports, and barrel files",
                "enforce no-floating-promises, no-misused-promises, and any/async/readonly/const policies",
            ),
        ),
        "react-security-and-deps": (
            "React security and dependencies",
            (
                "verify HTML, markdown, URL, public env vars, SSR payload, CSP, and Trusted Types boundaries",
                "check npm dependency vulnerabilities and policy compliance",
            ),
        ),
        "performance-and-memory-js": (
            "JS/TS performance and memory",
            (
                "verify CPU/heap hot paths, listeners, timers, closures, cache, and object churn",
                "apply debounce/throttle, async batching, and worker_threads/Web Workers where needed",
            ),
        ),
        "architecture-designing": (
            "Solution architecture",
            (
                "verify alignment with best practices, standards, and ADR decisions",
                "assess module boundaries, dependencies, risks, and consequences of the chosen solution",
            ),
        ),
    }

    def __init__(self, ai_instruction_path: str | Path) -> None:
        self._root = Path(ai_instruction_path)
        self._templates: dict[str, str] = {}
        self._judge_criteria: tuple[JudgeSkillCriterion, ...] | None = None
        self._load_templates()

    @property
    def sources(self) -> dict[str, str]:
        """Return a mapping of phase -> resolved prompt file path that was loaded."""
        return {
            phase: str(self._root / rel_path)
            for phase, rel_path in self._PROMPT_FILES.items()
        }

    @property
    def judge_criteria(self) -> tuple[JudgeSkillCriterion, ...]:
        """Return AI_Instruction skills mapped to Judge review criteria."""
        return self._get_judge_criteria()

    def load_prompt(self, name: str, context: dict[str, str]) -> str:
        """Load a prompt template by name and substitute ``{{variable}}`` placeholders.

        Args:
            name: One of ``"plan"``, ``"implement"``, ``"review"``.
            context: Mapping of variable names to replacement values.
                     Keys may contain dots (e.g. ``"task.description"``).

        Returns:
            The fully rendered prompt string.

        Raises:
            KeyError: If *name* is not a known prompt.
            UndefinedVariableError: If the template references a variable not in *context*.
        """
        template = self._templates[name]
        return self._render_template(template, context)

    def render_plan_prompt(
        self,
        task: Any,
        workspace_path: str | Path,
        issue: str | None = None,
        extra_context: dict[str, str] | None = None,
    ) -> str:
        """Render the ``/plan`` prompt with minimal task context.

        The rendered prompt does **not** include the full technical specification,
        acceptance criteria, or ready-made fixtures - the agent must derive these
        from its own analysis.
        """
        context_dict = self._build_context_dict(task, workspace_path, issue=issue)
        if extra_context:
            context_dict.update(extra_context)
        template = self._templates["plan"]
        rendered = self._render_template(template, context_dict)
        task_context = self._build_task_context(task, workspace_path, issue=issue)
        return rendered + "\n\n" + task_context

    def render_implement_prompt(
        self,
        task: Any,
        plan_content: str,
        workspace_path: str | Path,
        extra_context: dict[str, str] | None = None,
    ) -> str:
        """Render the ``/implement`` prompt with the approved plan and workspace constraints."""
        context_dict = self._build_context_dict(task, workspace_path)
        if extra_context:
            context_dict.update(extra_context)
        template = self._templates["implement"]
        rendered = self._render_template(template, context_dict)
        task_context = self._build_task_context(task, workspace_path)
        return (
            rendered
            + "\n\n"
            + task_context
            + "\n\n"
            + "## Approved Plan\n\n"
            + plan_content
        )

    def render_review_prompt(
        self,
        task: Any,
        plan_content: str,
        implementation_summary: str,
        workspace_path: str | Path,
        extra_context: dict[str, str] | None = None,
    ) -> str:
        """Render the ``/review`` prompt with plan, implementation summary, and AI_Tester rubric."""
        context_dict = self._build_context_dict(task, workspace_path)
        if extra_context:
            context_dict.update(extra_context)
        template = self._templates["review"]
        rendered = self._render_template(template, context_dict)
        task_context = self._build_task_context(task, workspace_path)
        security_ref = self._read_reference("security")
        validations_ref = self._read_reference("validations")
        plan_structure_ref = self._read_reference("plan_example")
        research_structure_ref = self._read_reference("research_example")
        dependency_report_ref = self._read_reference("dependency_report")
        parts = [
            rendered,
            task_context,
            "## Approved Plan",
            plan_content,
            "## Implementation Summary",
            implementation_summary,
            "## AI_Tester Quality Rubric",
            "Evaluate the implementation using the AI_Tester v2 quality criteria: "
            "plan adherence, code quality, test coverage, security, and "
            "tool/terminal usage.",
        ]
        if security_ref:
            parts.append("## OWASP Security Reference\n\n" + security_ref)
        if validations_ref:
            parts.append("## Validation Rules (V-01..V-18)\n\n" + validations_ref)
        if plan_structure_ref or research_structure_ref:
            parts.append(
                self._build_structure_validation_reference(
                    plan_structure_ref,
                    research_structure_ref,
                )
            )
        parts.append(self._build_skill_mapping_reference())
        if dependency_report_ref:
            parts.append(
                "## Dependency Freshness Report Reference\n\n" + dependency_report_ref
            )
        return "\n\n".join(parts)

    def invalidate_cache(self) -> None:
        """Reload prompt templates and reset cached skill criteria."""
        self._templates.clear()
        self._judge_criteria = None
        self._load_templates()

    def _load_templates(self) -> None:
        for phase, rel_path in self._PROMPT_FILES.items():
            prompt_path = self._root / rel_path
            if not prompt_path.is_file():
                raise PromptLoaderError(
                    f"Missing required prompt file for phase '{phase}': {prompt_path}"
                )
            self._templates[phase] = prompt_path.read_text(encoding="utf-8")

    def _render_template(self, template: str, context: dict[str, str]) -> str:
        """Replace ``{{variable}}`` placeholders in *template* using *context* dict."""

        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            if var_name in context:
                return context[var_name]
            raise UndefinedVariableError(
                f"Template variable '{{{{{var_name}}}}}' is undefined. "
                f"Provide it via context or ensure it is set in the task context."
            )

        return _VAR_PATTERN.sub(replacer, template)

    def _read_reference(self, name: str) -> str | None:
        """Read an optional reference file if it exists."""
        rel_path = self._OPTIONAL_REFERENCES.get(name)
        if rel_path is None:
            return None
        ref_path = self._root / rel_path
        if not ref_path.is_file():
            return None
        return ref_path.read_text(encoding="utf-8")

    def _build_structure_validation_reference(
        self,
        plan_structure_ref: str | None,
        research_structure_ref: str | None,
    ) -> str:
        """Build a concise instruction for validating plan/research artifact structure."""
        lines = ["## Artifact Structure Validation"]
        if plan_structure_ref:
            lines.append(
                "Validate plan artifacts against "
                "`.github/skills/architecture-designing/plan.example.md`. "
                "Required top-level sections: Task details, Proposed solution, "
                "Solution rationale, Current implementation analysis, "
                "Implementation plan, Security aspects, Testing strategy."
            )
        if research_structure_ref:
            lines.append(
                "Validate research artifacts against "
                "`.github/skills/task-analysing/research.example.md`. "
                "Required top-level sections: Task details, Business impact, "
                "Collected information, Current implementation state, Gap analysis."
            )
        if not plan_structure_ref and not research_structure_ref:
            lines.append(
                "No AI_Instruction structure examples are available in this repository."
            )
        return "\n\n".join(lines)

    def _build_skill_mapping_reference(self) -> str:
        """Build a reference table mapping AI_Instruction skills to Judge criteria."""
        lines = [
            "## AI_Instruction Skills as Judge Criteria",
            "Use the following 16 skills as explicit review criteria. For each "
            "applicable skill, mark it as `Sprawdzone`, `Nie dotyczy`, or "
            "`Wymaga narzedzia/danych` with a short justification.",
            "",
            "| Skill | Kryterium oceny | Zakres kontroli |",
            "| --- | --- | --- |",
        ]
        for criterion in self._get_judge_criteria():
            scope = "<br>".join(f"- {item}" for item in criterion.criteria)
            lines.append(f"| `{criterion.skill}` | {criterion.description} | {scope} |")
        return "\n".join(lines)

    def _get_judge_criteria(self) -> tuple[JudgeSkillCriterion, ...]:
        """Return cached skill-to-criteria mapping."""
        if self._judge_criteria is None:
            self._judge_criteria = tuple(
                JudgeSkillCriterion(
                    skill=skill_name,
                    path=str(self._root / ".github/skills" / skill_name / "SKILL.md"),
                    description=description,
                    criteria=criteria,
                )
                for skill_name, (description, criteria) in self._JUDGE_SKILLS.items()
            )
        return self._judge_criteria

    @staticmethod
    def _build_context_dict(
        task: Any,
        workspace_path: str | Path,
        *,
        issue: str | None = None,
    ) -> dict[str, str]:
        """Build a context dict from task metadata for template variable substitution."""
        ctx = {
            "task.id": str(task.task_id),
            "task.type": str(task.task_type),
            "task.repo": str(task.repo),
            "task.source": str(task.source),
            "workspace.path": str(workspace_path),
        }
        if issue:
            ctx["issue"] = issue
        return ctx

    @staticmethod
    def _build_task_context(
        task: Any,
        workspace_path: str | Path,
        *,
        issue: str | None = None,
    ) -> str:
        lines = [
            "## Task Context",
            f"- **task_id**: {task.task_id}",
            f"- **task_type**: {task.task_type}",
            f"- **repo**: {task.repo}",
            f"- **source**: {task.source}",
            f"- **workspace_path**: {workspace_path}",
        ]
        if issue:
            lines.append(f"- **issue**: {issue}")
        return "\n".join(lines)
