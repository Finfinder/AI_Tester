"""Unit tests for the VS Code adapter contract and fake adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from agents.vscode_adapter import FakeVsCodeAdapter, WorkspacePathError
from agents.vscode_adapter.adapter import (
    VsCodeAdapter,
    ensure_inside_workspace,
    resolve_workspace_path,
)


@pytest.fixture
def workspace(tmp_path: Path):
    """Create a task workspace with sample files."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "sample.py").write_text("print('sample')\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    return tmp_path


def test_fake_adapter_reads_and_writes_only_inside_workspace(workspace: Path):
    """Adapter file operations must stay inside the task workspace."""
    adapter = FakeVsCodeAdapter(workspace)

    content = adapter.read_file("src/sample.py")

    assert content == "print('sample')\n"

    adapter.write_file("src/generated.py", "print('generated')\n")

    assert (workspace / "src" / "generated.py").read_text(
        encoding="utf-8"
    ) == "print('generated')\n"


def test_fake_adapter_rejects_paths_outside_workspace(workspace: Path):
    """Adapter must reject file paths that escape the workspace."""
    adapter = FakeVsCodeAdapter(workspace)

    with pytest.raises(WorkspacePathError):
        adapter.read_file("../outside.py")


def test_fake_adapter_lists_directory(workspace: Path):
    """Adapter list_directory returns workspace entries only."""
    adapter = FakeVsCodeAdapter(workspace)

    entries = adapter.list_directory("src")

    assert entries == ["sample.py"]


def test_fake_adapter_search_files(workspace: Path):
    """Adapter search_files returns relative matching paths."""
    adapter = FakeVsCodeAdapter(workspace)

    matches = adapter.search_files("sample.py", include_pattern="**/*.py")

    assert [Path(match) for match in matches] == [Path("src/sample.py")]


def test_fake_adapter_terminal_and_documentation_stubs(workspace: Path):
    """Adapter terminal and documentation methods return deterministic stubs."""
    adapter = FakeVsCodeAdapter(workspace)

    terminal_result = adapter.run_terminal_command(
        "python -m pytest", timeout_seconds=10
    )
    documentation = adapter.fetch_documentation("https://code.visualstudio.com/api")
    context7_result = adapter.context7("Python", "pytest fixtures", mode="info")
    adapter.register_tools()

    assert terminal_result["terminal_exit_code"] == "unknown"
    assert terminal_result["status"] == "stubbed"
    assert "Documentation fetch stub" in documentation
    assert "Context7 stub" in context7_result


def test_fake_adapter_logs_actions(workspace: Path):
    """Adapter records actions through ToolLogger-compatible methods."""

    class Logger:
        def __init__(self):
            self.entries = []

        def log_terminal(
            self, command, exit_code, duration_seconds, output_summary, verbose=False
        ):
            self.entries.append({"type": "terminal", "command": command})

        def log_file_operation(self, operation, path, size_bytes, success=True):
            self.entries.append({"type": "file_operation", "operation": operation})

        def log_search(self, tool, query, results_count):
            self.entries.append({"type": "search", "tool": tool})

        def log_ai_tool(self, tool, query, response_summary):
            self.entries.append({"type": "ai_tool", "tool": tool})

    logger = Logger()
    adapter = FakeVsCodeAdapter(workspace, logger=logger)

    adapter.read_file("src/sample.py")
    adapter.search_files("sample.py")
    adapter.context7("Python", "pytest")
    adapter.run_terminal_command("python --version")

    assert {entry["type"] for entry in logger.entries} == {
        "file_operation",
        "search",
        "ai_tool",
        "terminal",
    }


def test_resolve_workspace_path_rejects_missing_workspace(tmp_path: Path):
    """Workspace path resolver requires an existing directory."""
    missing_path = tmp_path / "missing"

    with pytest.raises(WorkspacePathError):
        resolve_workspace_path(missing_path)


def test_ensure_inside_workspace_rejects_absolute_path(workspace: Path):
    """Workspace boundary helper rejects absolute paths."""
    with pytest.raises(WorkspacePathError):
        ensure_inside_workspace(workspace, Path("/etc/passwd"))


def test_vscode_adapter_contract_has_required_methods():
    """Contract exposes all required tool methods."""
    required_methods = {
        "run_terminal_command",
        "read_file",
        "write_file",
        "search_files",
        "list_directory",
        "fetch_documentation",
        "context7",
        "register_tools",
    }

    assert required_methods.issubset(
        {name for name in dir(VsCodeAdapter) if not name.startswith("_")}
    )
    assert FakeVsCodeAdapter.TOOL_NAMES == {
        "run_terminal_command",
        "read_file",
        "write_file",
        "search_files",
        "list_directory",
        "fetch_documentation",
        "context7",
    }
