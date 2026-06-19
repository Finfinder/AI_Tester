"""VS Code Extension Host Adapter contract for AI_Tester v2.

The concrete adapter is intentionally not implemented in Faza 1. This module
defines the public interface and helper types used by the future integration
with VS Code Extension Host APIs such as ``vscode.lm.registerTool``,
``vscode.window.createTerminal`` and ``shellIntegration.executeCommand``.

All implementations must keep operations inside ``workspace_path`` and record
actions through ``ToolLogger``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Protocol


class WorkspacePathError(ValueError):
    """Raised when an adapter operation would escape the task workspace."""


class VsCodeAdapter(ABC):
    """Contract for controlled VS Code tool access during a task.

    The future implementation should register the methods below as Language
    Model tools with ``vscode.lm.registerTool``. Terminal access should be
    created with ``vscode.window.createTerminal`` and commands should preferably
    be executed with ``shellIntegration.executeCommand`` so that an ``exitCode``
    can be captured. If a fallback such as ``sendText`` is used, the result must
    report ``terminal_exit_code`` as ``unknown``.
    """

    @property
    @abstractmethod
    def workspace_path(self) -> Path:
        """Return the isolated task workspace path."""

    @abstractmethod
    def run_terminal_command(
        self, command: str, timeout_seconds: int = 120
    ) -> dict[str, Any]:
        """Run a terminal command scoped to the task workspace."""

    @abstractmethod
    def read_file(self, relative_path: str, encoding: str = "utf-8") -> str:
        """Read a file from the task workspace."""

    @abstractmethod
    def write_file(
        self, relative_path: str, content: str, encoding: str = "utf-8"
    ) -> None:
        """Write a file inside the task workspace."""

    @abstractmethod
    def search_files(self, pattern: str, include_pattern: str = "**/*") -> list[str]:
        """Search files in the task workspace."""

    @abstractmethod
    def list_directory(self, relative_path: str = ".") -> list[str]:
        """List a directory inside the task workspace."""

    @abstractmethod
    def fetch_documentation(self, url: str, max_length: int = 5000) -> str:
        """Fetch external documentation for the model.

        This method is part of the adapter contract so that future tool calls
        can be logged and rate-limited consistently. Faza 1 does not implement
        network access.
        """

    @abstractmethod
    def context7(self, library_name: str, query: str, mode: str = "code") -> str:
        """Fetch Context7 documentation for a library.

        The concrete adapter should call the Context7 MCP documentation tools
        through a controlled wrapper in a future phase.
        """

    @abstractmethod
    def register_tools(self) -> None:
        """Register adapter methods as VS Code Language Model tools."""


class SupportsPathLike(Protocol):
    """Minimal protocol for objects that expose a filesystem path."""

    path: Path


def resolve_workspace_path(workspace_path: str | Path) -> Path:
    """Resolve and normalize a task workspace path."""
    path = Path(workspace_path).expanduser().resolve()
    if not path.is_dir():
        raise WorkspacePathError(
            f"Workspace path does not exist or is not a directory: {path}"
        )
    return path


def ensure_inside_workspace(workspace_path: Path, requested_path: str | Path) -> Path:
    """Resolve a requested path and ensure it stays inside the workspace."""
    resolved_workspace = workspace_path.resolve()
    resolved_path = (resolved_workspace / requested_path).resolve()

    try:
        resolved_path.relative_to(resolved_workspace)
    except ValueError as exc:
        raise WorkspacePathError(f"Path escapes workspace: {requested_path}") from exc

    return resolved_path
