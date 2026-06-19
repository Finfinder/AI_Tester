"""AI_Tester v2 package bridge for Python imports."""

from pathlib import Path

_parent_root = Path(__file__).resolve().parents[1]
__path__.append(str(_parent_root))
