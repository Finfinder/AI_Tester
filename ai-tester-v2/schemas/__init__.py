"""AI_Tester v2 â€” Schemas package.

Exposes JSON Schema definitions for ranking and task-result reports.
"""

from pathlib import Path
import json

_SCHEMA_DIR = Path(__file__).parent


def _load_schema(filename: str) -> dict:
    """Load a JSON schema file from the schemas directory."""
    path = _SCHEMA_DIR / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


RANKING_SCHEMA = _load_schema("ranking.schema.json")
TASK_RESULT_SCHEMA = _load_schema("task-result.schema.json")

__all__ = ["RANKING_SCHEMA", "TASK_RESULT_SCHEMA", "_load_schema"]
