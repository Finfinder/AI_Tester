# AI_Tester v2 - ToolLogger

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any


# Setup JSON logging format
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
        }
        return json.dumps(log_record)


class ToolLogger:
    """
    Logs all agent actions (terminal, file ops, search, AI tools) in a structured JSON format.
    """

    def __init__(self, log_file_path: str):
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("ToolLogger")
        self.logger.setLevel(logging.INFO)

        # Ensure logger doesn't propagate to root logger if already configured
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file_path)
            handler.setFormatter(JsonFormatter())
            self.logger.addHandler(handler)

        self.log_entries: List[Dict[str, Any]] = []

    def log_terminal(
        self,
        command: str,
        exit_code: int,
        duration: float,
        output_summary: str,
        verbose: bool = False,
    ):
        """Logs terminal command execution."""
        entry = {
            "type": "terminal",
            "command": command,
            "exit_code": exit_code,
            "duration_seconds": duration,
            "output_summary": output_summary,
            "verbose": verbose,
        }
        self.log_entries.append(entry)
        self.logger.info(json.dumps(entry))

    def log_file_operation(
        self, operation: str, path: str, size_bytes: int, success: bool = True
    ):
        """Logs file system operations (read, write, delete)."""
        entry = {
            "type": "file_operation",
            "operation": operation,
            "path": path,
            "size_bytes": size_bytes,
            "success": success,
        }
        self.log_entries.append(entry)
        self.logger.info(json.dumps(entry))

    def log_search(self, tool: str, query: str, results_count: int):
        """Logs search tool usage (e.g., semantic_search, grep_search)."""
        entry = {
            "type": "search",
            "tool": tool,
            "query": query,
            "results_count": results_count,
        }
        self.log_entries.append(entry)
        self.logger.info(json.dumps(entry))

    def log_ai_tool(self, tool: str, query: str, response_summary: str):
        """Logs usage of external AI tools (e.g., context7, web fetch)."""
        entry = {
            "type": "ai_tool",
            "tool": tool,
            "query": query,
            "response_summary": response_summary,
        }
        self.log_entries.append(entry)
        self.logger.info(json.dumps(entry))

    def log_openrouter_request(
        self,
        role: str,
        model: str,
        status_code: int,
        duration_seconds: float,
        input_tokens: int | None,
        output_tokens: int | None,
        estimated_cost_usd: float | None,
        request_id: str | None = None,
        total_tokens: int | None = None,
        retry_count: int = 0,
    ):
        """Logs a redacted OpenRouter request with safe metadata only."""
        entry = {
            "type": "ai_tool",
            "tool": "openrouter",
            "request_id": request_id,
            "role": role,
            "model": model,
            "status_code": status_code,
            "duration_seconds": duration_seconds,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost_usd,
            "retry_count": retry_count,
        }
        self.log_entries.append(entry)
        self.logger.info(json.dumps(entry))

    def get_log_entries(self) -> List[Dict[str, Any]]:
        """Returns all recorded log entries."""
        return self.log_entries

    def export_to_json(self) -> Dict[str, Any]:
        """Returns a serializable dictionary with logs grouped by type."""
        grouped_logs = {
            "terminal": [],
            "file_operation": [],
            "search": [],
            "ai_tool": [],
        }
        for entry in self.log_entries:
            log_type = entry["type"]
            if log_type in grouped_logs:
                grouped_logs[log_type].append(entry)

        return {
            "log_summary": "AI_Tester v2 Tool Log",
            "log_count": len(self.log_entries),
            "logs": grouped_logs,
        }


# Example usage (for testing purposes)
if __name__ == "__main__":
    # Setup a temporary log file for testing
    TEST_LOG_PATH = "test_tool_log.json"

    # Clean up previous test log
    if os.path.exists(TEST_LOG_PATH):
        os.remove(TEST_LOG_PATH)

    logger = ToolLogger(log_file_path=TEST_LOG_PATH)

    # Test logging functions
    logger.log_terminal(
        "docker build -t ai_tester_runner .",
        0,
        15.5,
        "Image built successfully.",
        verbose=True,
    )
    logger.log_file_operation(
        "write", "ai-tester-v2/orchestrator/config.py", 1024, success=True
    )
    logger.log_search("semantic_search", "AI_Tester v2 architecture", 5)
    logger.log_ai_tool(
        "mcp_context7", "How to use OpenRouter API", "Found 3 relevant endpoints."
    )

    # Get and print the final structured log
    final_report = logger.export_to_json()
    print("\n--- Final Structured Log Report ---")
    print(json.dumps(final_report, indent=2))

    # Clean up
    if os.path.exists(TEST_LOG_PATH):
        os.remove(TEST_LOG_PATH)
