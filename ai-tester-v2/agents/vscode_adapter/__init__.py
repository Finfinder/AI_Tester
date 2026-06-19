"""Public exports for the VS Code adapter contract and stubs."""

from .adapter import (
    SupportsPathLike,
    VsCodeAdapter,
    WorkspacePathError,
    ensure_inside_workspace,
    resolve_workspace_path,
)
from .fake_adapter import FakeVsCodeAdapter

__all__ = [
    "FakeVsCodeAdapter",
    "SupportsPathLike",
    "VsCodeAdapter",
    "WorkspacePathError",
    "ensure_inside_workspace",
    "resolve_workspace_path",
]
