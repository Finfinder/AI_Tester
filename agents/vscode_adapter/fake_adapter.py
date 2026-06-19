"""In-memory VS Code adapter stub used by tests and placeholder workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agents.vscode_adapter.adapter import (
    VsCodeAdapter,
    WorkspacePathError,
    ensure_inside_workspace,
    resolve_workspace_path,
)


class FakeVsCodeAdapter(VsCodeAdapter):
    """Test double for the future VS Code Extension Host Adapter.

    The fake adapter implements the same public contract as ``VsCodeAdapter`` but
    never calls VS Code APIs. File and directory operations are performed through
    Python's ``pathlib`` module and are guarded by the same workspace boundary
    helper used by the future adapter. Terminal, documentation and Context7 calls
    return deterministic stub responses and are logged through ``ToolLogger``.
    """

    TOOL_NAMES = {
        "run_terminal_command",
        "read_file",
        "write_file",
        "search_files",
        "list_directory",
        "fetch_documentation",
        "context7",
    }

    def __init__(self, workspace_path: str | Path, logger: Any | None = None):
        self._workspace_path = resolve_workspace_path(workspace_path)
        self._logger = logger

    @property
    def workspace_path(self) -> Path:
        """Return the isolated task workspace path."""
        return self._workspace_path

    def run_terminal_command(
        self, command: str, timeout_seconds: int = 120
    ) -> dict[str, Any]:
        """Return a deterministic terminal stub result."""
        result = {
            "command": command,
            "timeout_seconds": timeout_seconds,
            "terminal_exit_code": "unknown",
            "status": "stubbed",
            "workspace_path": str(self._workspace_path),
        }
        self._log_terminal(
            command=command,
            exit_code="unknown",
            duration_seconds=0.0,
            output_summary="Stubbed terminal execution.",
        )
        return result

    def read_file(self, relative_path: str, encoding: str = "utf-8") -> str:
        """Read a file from the isolated task workspace."""
        file_path = self._resolve_existing_file(relative_path)
        content = file_path.read_text(encoding=encoding)
        self._log_file_operation("read", str(file_path), len(content.encode(encoding)))
        return content

    def write_file(
        self, relative_path: str, content: str, encoding: str = "utf-8"
    ) -> None:
        """Write a file inside the isolated task workspace."""
        file_path = self._resolve_relative_file(relative_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding=encoding)
        self._log_file_operation("write", str(file_path), len(content.encode(encoding)))

    def search_files(self, pattern: str, include_pattern: str = "**/*") -> list[str]:
        """Search files inside the task workspace and return relative paths."""
        self._validate_relative_pattern(include_pattern)
        matches = [
            path
            for path in self._workspace_path.glob(include_pattern)
            if path.is_file()
        ]
        if pattern:
            matches = [
                path for path in matches if path.name == pattern or path.match(pattern)
            ]
        relative_paths = [
            path.relative_to(self._workspace_path).as_posix() for path in matches
        ]
        self._log_search("search_files", pattern, len(relative_paths))
        return relative_paths

    def list_directory(self, relative_path: str = ".") -> list[str]:
        """List directory entries inside the task workspace."""
        directory_path = ensure_inside_workspace(self._workspace_path, relative_path)
        if not directory_path.is_dir():
            raise WorkspacePathError(f"Directory does not exist: {relative_path}")

        entries = sorted(entry.name for entry in directory_path.iterdir())
        self._log_file_operation("list_directory", str(directory_path), len(entries))
        return entries

    def fetch_documentation(self, url: str, max_length: int = 5000) -> str:
        """Return a deterministic documentation stub."""
        summary = f"Documentation fetch stub for {url} (max_length={max_length})."
        self._log_ai_tool("fetch_documentation", url, summary)
        return summary

    def context7(self, library_name: str, query: str, mode: str = "code") -> str:
        """Return a deterministic Context7 stub."""
        summary = f"Context7 stub for {library_name}: {query} ({mode})."
        self._log_ai_tool("context7", f"{library_name} {query}", summary)
        return summary

    def register_tools(self) -> None:
        """No-op registration for the future ``vscode.lm.registerTool`` integration."""
        self._log_ai_tool(
            "register_tools",
            ", ".join(sorted(self.TOOL_NAMES)),
            "Tools registered by the future adapter.",
        )

    def _resolve_existing_file(self, relative_path: str) -> Path:
        path = self._resolve_relative_file(relative_path)
        if not path.is_file():
            raise WorkspacePathError(f"File does not exist: {relative_path}")
        return path

    def _resolve_relative_file(self, relative_path: str) -> Path:
        path = ensure_inside_workspace(self._workspace_path, relative_path)
        if path.exists() and not path.is_file():
            raise WorkspacePathError(f"Path is not a file: {relative_path}")
        return path

    @staticmethod
    def _validate_relative_pattern(pattern: str) -> None:
        path = Path(pattern)
        if path.is_absolute() or ".." in path.parts:
            raise WorkspacePathError(f"Pattern escapes workspace: {pattern}")

    def _log_terminal(
        self, command: str, exit_code: Any, duration_seconds: float, output_summary: str
    ) -> None:
        if self._logger is not None:
            self._logger.log_terminal(
                command, exit_code, duration_seconds, output_summary
            )

    def _log_file_operation(self, operation: str, path: str, size_bytes: int) -> None:
        if self._logger is not None:
            self._logger.log_file_operation(operation, path, size_bytes)

    def _log_search(self, tool: str, query: str, results_count: int) -> None:
        if self._logger is not None:
            self._logger.log_search(tool, query, results_count)

    def _log_ai_tool(self, tool: str, query: str, response_summary: str) -> None:
        if self._logger is not None:
            self._logger.log_ai_tool(tool, query, response_summary)
