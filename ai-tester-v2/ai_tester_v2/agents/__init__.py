"""Agent adapter package bridge."""

from pathlib import Path

_parent_root = Path(__file__).resolve().parents[2]
__path__.append(str(_parent_root / "agents"))
