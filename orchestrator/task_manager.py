"""AI_Tester v2 - TaskManager.

Manages isolated workspaces for AI tasks.
Ensures each task runs in a clean, isolated environment.
"""

import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse

MAX_SOURCE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_SOURCE_FILES = 10_000
_IGNORED_NAMES = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
}


class WorkspaceAlreadyExistsError(Exception):
    """Raised when attempting to create a workspace that already exists."""

    pass


class WorkspaceCleanupError(Exception):
    """Raised when cleanup of a workspace fails."""

    pass


class TaskManager:
    """Manages isolated workspaces for AI tasks."""

    def __init__(self, temp_base_dir: str):
        self.temp_base_dir = str(Path(temp_base_dir).resolve())

    def create_workspace(self, source_repo: str) -> str:
        """Create a new isolated workspace directory.

        Args:
            source_repo: Path to the source code repository or a git URL.

        Returns:
            Absolute path to the newly created workspace.

        Raises:
            WorkspaceAlreadyExistsError: If the directory already exists.
            FileNotFoundError: If the source repository path does not exist.
            ValueError: If the source is invalid or exceeds limits.
        """
        workspace_uuid = uuid.uuid4()
        workspace_path = os.path.join(self.temp_base_dir, f"task-{workspace_uuid}")
        workspace_path = str(Path(workspace_path).resolve())

        if os.path.exists(workspace_path):
            raise WorkspaceAlreadyExistsError(
                f"Workspace already exists at {workspace_path}"
            )

        os.makedirs(workspace_path, exist_ok=True)

        for subdir in ("src", "tests", "benchmarks", "artifacts"):
            os.makedirs(os.path.join(workspace_path, subdir), exist_ok=True)

        parsed = urlparse(source_repo)
        is_url = parsed.scheme in ("http", "https", "git")

        if is_url:
            self._clone_repo(source_repo, workspace_path)
        else:
            self._copy_local_source(source_repo, workspace_path)

        try:
            subprocess.check_call(
                ["git", "init"],
                cwd=workspace_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        return workspace_path

    def _clone_repo(self, url: str, workspace_path: str) -> None:
        """Clone a git URL into the workspace src directory."""
        dest_src = os.path.join(workspace_path, "src")
        try:
            subprocess.check_call(
                ["git", "clone", "--depth", "1", url, dest_src],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise ValueError(f"Failed to clone source repository {url}: {exc}") from exc

    def _copy_local_source(self, source_repo: str, workspace_path: str) -> None:
        """Copy a local directory into the workspace src directory with safety limits."""
        source_path = Path(source_repo).resolve()
        if not source_path.is_dir():
            raise FileNotFoundError(f"Source repository not found at {source_repo}")

        dest_src = Path(workspace_path) / "src"

        total_size = 0
        total_files = 0
        for item in source_path.iterdir():
            if item.name in _IGNORED_NAMES:
                continue
            if item.is_dir():
                total_size, total_files = self._copy_tree_limited(
                    item, dest_src / item.name, total_size, total_files
                )
            else:
                total_files += 1
                total_size += item.stat().st_size
                if total_files > MAX_SOURCE_FILES:
                    raise ValueError(
                        f"Source repository exceeds max file count ({MAX_SOURCE_FILES})"
                    )
                if total_size > MAX_SOURCE_SIZE_BYTES:
                    raise ValueError(
                        f"Source repository exceeds max size ({MAX_SOURCE_SIZE_BYTES} bytes)"
                    )
                shutil.copy2(str(item), str(dest_src / item.name))

    def _copy_tree_limited(
        self, src: Path, dst: Path, total_size: int, total_files: int
    ) -> tuple:
        """Recursively copy a directory tree with size and file-count limits."""
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            if item.name in _IGNORED_NAMES:
                continue
            if item.is_dir():
                total_size, total_files = self._copy_tree_limited(
                    item, dst / item.name, total_size, total_files
                )
            else:
                total_files += 1
                total_size += item.stat().st_size
                if total_files > MAX_SOURCE_FILES:
                    raise ValueError(
                        f"Source repository exceeds max file count ({MAX_SOURCE_FILES})"
                    )
                if total_size > MAX_SOURCE_SIZE_BYTES:
                    raise ValueError(
                        f"Source repository exceeds max size ({MAX_SOURCE_SIZE_BYTES} bytes)"
                    )
                shutil.copy2(str(item), str(dst / item.name))
        return total_size, total_files

    def cleanup_workspace(self, workspace_path: str) -> bool:
        """Remove the entire workspace directory and all its contents.

        Only removes paths that are children of temp_base_dir for safety.
        """
        resolved = str(Path(workspace_path).resolve())
        if not resolved.startswith(self.temp_base_dir):
            raise WorkspaceCleanupError(
                f"Refusing to cleanup path outside temp_base_dir: {workspace_path}"
            )
        if os.path.exists(resolved):
            try:
                shutil.rmtree(resolved)
                return True
            except OSError as exc:
                raise WorkspaceCleanupError(
                    f"Failed to cleanup workspace at {workspace_path}: {exc}"
                ) from exc
        return False

    def get_workspace_info(self, workspace_path: str) -> Dict[str, Any]:
        """Gather metadata about the workspace."""
        path = Path(workspace_path)
        if not path.is_dir():
            return {"error": "Workspace directory does not exist."}

        file_count = 0
        total_size = 0
        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d != ".git"]
            file_count += len(files)
            for fname in files:
                try:
                    total_size += os.path.getsize(os.path.join(root, fname))
                except OSError:
                    pass

        git_status = "not_initialized"
        if (path / ".git").is_dir():
            git_status = "initialized"

        return {
            "path": str(path),
            "file_count": file_count,
            "size_bytes": total_size,
            "git_status": git_status,
        }
