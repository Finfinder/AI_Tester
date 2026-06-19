import pytest
from ai_tester_v2.orchestrator.tool_logger import ToolLogger


@pytest.fixture
def logger(tmp_path):
    """Fixture to provide a fresh ToolLogger instance for each test."""
    log_path = tmp_path / "test_tool_log.json"
    tool_logger = ToolLogger(log_file_path=str(log_path))
    yield tool_logger
    tool_logger.logger.handlers.clear()
    if log_path.exists():
        log_path.unlink()


def test_log_terminal(logger: ToolLogger):
    """Test logging of terminal commands."""
    command = "docker build -t test_runner ."
    output = "Build successful."
    logger.log_terminal(command, 0, 10.5, output, verbose=True)

    logs = logger.get_log_entries()
    assert len(logs) == 1
    assert logs[0]["type"] == "terminal"
    assert logs[0]["command"] == command
    assert logs[0]["exit_code"] == 0


def test_log_file_operation(logger: ToolLogger):
    """Test logging of file system operations."""
    path = "src/config.py"
    logger.log_file_operation("write", path, 2048, success=True)

    logs = logger.get_log_entries()
    assert len(logs) == 1
    assert logs[0]["type"] == "file_operation"
    assert logs[0]["operation"] == "write"


def test_log_search(logger: ToolLogger):
    """Test logging of search tool usage."""
    tool = "semantic_search"
    query = "AI_Tester v2 architecture"
    results = 5
    logger.log_search(tool, query, results)

    logs = logger.get_log_entries()
    assert len(logs) == 1
    assert logs[0]["type"] == "search"
    assert logs[0]["tool"] == tool
    assert logs[0]["results_count"] == results


def test_log_ai_tool(logger: ToolLogger):
    """Test logging of external AI tool usage."""
    tool = "mcp_context7"
    query = "How to use OpenRouter API"
    summary = "Found 3 relevant endpoints."
    logger.log_ai_tool(tool, query, summary)

    logs = logger.get_log_entries()
    assert len(logs) == 1
    assert logs[0]["type"] == "ai_tool"
    assert logs[0]["tool"] == tool
    assert logs[0]["query"] == query
