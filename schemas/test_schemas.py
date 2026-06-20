"""Tests for JSON Schema definitions used by AI_Tester v2 reports."""

import json
from pathlib import Path

import jsonschema

from schemas import RANKING_SCHEMA, TASK_RESULT_SCHEMA


SCHEMA_DIR = Path(__file__).parent


def test_task_result_schema_accepts_openrouter_metadata():
    """Validate a task result containing redacted OpenRouter metadata."""
    document = {
        "task_id": "T1",
        "task_type": "feature",
        "repo": "test_repo",
        "model": "openai/gpt-4.1-mini",
        "judge_model": "openai/gpt-4.1-mini",
        "phases": [
            {"phase": "plan", "status": "success", "duration_seconds": 0.1},
            {"phase": "implement", "status": "success", "duration_seconds": 0.2},
            {"phase": "review", "status": "success", "duration_seconds": 0.3},
        ],
        "time": 0.6,
        "scores": {"overall_score": 0.95},
        "details": {"message": "Workflow completed successfully."},
        "openrouter_requests": [
            {
                "request_id": "req_1",
                "role": "plan",
                "model": "openai/gpt-4.1-mini",
                "status_code": 200,
                "duration_seconds": 0.1,
                "input_tokens": 10,
                "output_tokens": 20,
                "total_tokens": 30,
                "estimated_cost_usd": 0.0001,
                "retry_count": 0,
            }
        ],
    }

    jsonschema.validate(instance=document, schema=TASK_RESULT_SCHEMA)


def test_ranking_schema_accepts_openrouter_metadata():
    """Validate a ranking report containing aggregated OpenRouter metadata."""
    document = {
        "version": "2.0",
        "timestamp": "2026-06-20T12:00:00Z",
        "benchmark_config": {
            "model": "openai/gpt-4.1-mini",
            "judge_model": "openai/gpt-4.1-mini",
            "tasks_count": 1,
            "total_time_seconds": 0.6,
            "openrouter": {
                "provider": "openrouter",
                "model": "openai/gpt-4.1-mini",
                "judge_model": "openai/gpt-4.1-mini",
                "total_input_tokens": 10,
                "total_output_tokens": 20,
                "total_tokens": 30,
                "total_estimated_cost_usd": 0.0001,
            },
        },
        "ranking": {
            "model": "openai/gpt-4.1-mini",
            "judge_model": "openai/gpt-4.1-mini",
            "scores": {
                "plan": 90,
                "implementation": 88,
                "tools_and_terminal": 85,
                "overall": 88,
            },
            "tasks": [
                {
                    "task_id": "T1",
                    "task_type": "feature",
                    "repo": "test_repo",
                    "scores": {
                        "plan": 90,
                        "implementation": 88,
                        "tools_and_terminal": 85,
                    },
                    "time": {
                        "plan_seconds": 0.1,
                        "implement_seconds": 0.2,
                        "review_seconds": 0.3,
                    },
                    "details": {"message": "Workflow completed successfully."},
                    "openrouter_requests": [
                        {
                            "request_id": "req_1",
                            "role": "judge",
                            "model": "openai/gpt-4.1-mini",
                            "status_code": 200,
                            "duration_seconds": 0.3,
                            "input_tokens": None,
                            "output_tokens": None,
                            "total_tokens": None,
                            "estimated_cost_usd": None,
                            "retry_count": 0,
                        }
                    ],
                }
            ],
        },
    }

    jsonschema.validate(instance=document, schema=RANKING_SCHEMA)


def test_schema_files_are_valid_json():
    """Ensure schema files remain parseable JSON."""
    for filename in ("ranking.schema.json", "task-result.schema.json"):
        schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
        jsonschema.Draft7Validator.check_schema(schema)
