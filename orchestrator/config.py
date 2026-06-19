"""AI_Tester v2 - Orchestrator Configuration.

Global configuration settings for the AI_Tester v2 orchestrator.
"""

from pydantic import BaseModel


class Config(BaseModel):
    """Configuration settings for the AI_Tester v2 orchestrator."""

    SOURCE_REPO_PATH: str = "src/"
    TEMP_BASE_DIR: str = "./temp"
    DEFAULT_MODEL: str = "gpt-4"
    DEFAULT_JUDGE_MODEL: str = "gpt-4-turbo"
    PLAN_TEMPLATE_PATH: str = "./templates/plan_template.md"
    REPORT_SCHEMA_VERSION: str = "1.0.0"
