import pytest
import os
from ai_tester_v2.orchestrator.task_manager import (
    TaskManager,
    WorkspaceAlreadyExistsError,
    WorkspaceCleanupError,
)


@pytest.fixture
def temp_dir(tmp_path):
    """Fixture to provide a temporary base directory."""
    temp_path = str(tmp_path / "temp_tasks_test")
    os.makedirs(temp_path)
    return temp_path


@pytest.fixture
def source_dir(tmp_path):
    """Fixture to create a dummy source directory."""
    src = tmp_path / "dummy_source"
    src.mkdir()
    (src / "dummy.py").write_text("print('dummy')\n")
    return str(src)


def test_create_workspace_success(temp_dir: str, source_dir: str):
    """Test successful creation of a workspace."""
    manager = TaskManager(temp_base_dir=temp_dir)
    workspace_path = manager.create_workspace(source_repo=source_dir)

    assert os.path.isdir(workspace_path)
    assert os.path.isdir(os.path.join(workspace_path, "src"))
    assert os.path.isdir(os.path.join(workspace_path, "tests"))
    assert os.path.isdir(os.path.join(workspace_path, "benchmarks"))
    assert os.path.isdir(os.path.join(workspace_path, "artifacts"))
    assert os.path.isdir(os.path.join(workspace_path, ".git"))


def test_create_workspace_already_exists(temp_dir: str, source_dir: str, monkeypatch):
    """Test handling of workspace already existing."""
    manager = TaskManager(temp_base_dir=temp_dir)
    monkeypatch.setattr(
        "ai_tester_v2.orchestrator.task_manager.uuid.uuid4",
        lambda: "fixed-workspace",
    )
    manager.create_workspace(source_repo=source_dir)

    with pytest.raises(WorkspaceAlreadyExistsError):
        manager.create_workspace(source_repo=source_dir)


def test_cleanup_workspace(temp_dir: str, source_dir: str):
    """Test successful cleanup of a workspace."""
    manager = TaskManager(temp_base_dir=temp_dir)
    workspace_path = manager.create_workspace(source_repo=source_dir)

    assert os.path.isdir(workspace_path)
    success = manager.cleanup_workspace(workspace_path)
    assert success is True
    assert not os.path.exists(workspace_path)


def test_cleanup_rejects_outside_path(temp_dir: str, tmp_path):
    """Test that cleanup refuses to remove paths outside temp_base_dir."""
    manager = TaskManager(temp_base_dir=temp_dir)
    outside_path = str(tmp_path / "some_other_path")
    with pytest.raises(WorkspaceCleanupError):
        manager.cleanup_workspace(outside_path)


def test_get_workspace_info(temp_dir: str, source_dir: str):
    """Test gathering metadata about the workspace."""
    manager = TaskManager(temp_base_dir=temp_dir)
    workspace_path = manager.create_workspace(source_repo=source_dir)

    info = manager.get_workspace_info(workspace_path)
    assert "path" in info
    assert isinstance(info["file_count"], int)
    assert info["file_count"] > 0
    assert "size_bytes" in info
    assert info["git_status"] == "initialized"

    info_fail = manager.get_workspace_info("./non_existent_path")
    assert "error" in info_fail
