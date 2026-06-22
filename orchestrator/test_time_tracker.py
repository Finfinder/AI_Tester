import time

import pytest

from orchestrator.time_tracker import TimeTracker


@pytest.fixture
def tracker():
    """Fixture to provide a fresh TimeTracker instance for each test."""
    return TimeTracker()


def test_start_stop_single_phase(tracker: TimeTracker):
    """Test basic start and stop functionality for a single phase."""
    phase = "test_phase"
    tracker.start_phase(phase)
    time.sleep(0.05)  # Simulate work
    elapsed = tracker.stop_phase(phase)

    assert elapsed > 0.04  # Check if time elapsed is reasonable
    assert tracker.get_elapsed(phase) == pytest.approx(elapsed)


def test_multiple_phases(tracker: TimeTracker):
    """Test tracking multiple, distinct phases."""
    phase1 = "plan"
    phase2 = "implement"

    tracker.start_phase(phase1)
    time.sleep(0.05)
    tracker.stop_phase(phase1)

    tracker.start_phase(phase2)
    time.sleep(0.05)
    tracker.stop_phase(phase2)

    elapsed1 = tracker.get_elapsed(phase1)
    elapsed2 = tracker.get_elapsed(phase2)

    assert elapsed1 > 0.04
    assert elapsed2 > 0.04
    assert elapsed1 == pytest.approx(elapsed2, rel=0.5)  # Allow scheduler variance


def test_export_to_json(tracker: TimeTracker):
    """Test that the export_to_json method returns the correct structure."""
    phase1 = "plan"
    phase2 = "implement"

    tracker.start_phase(phase1)
    time.sleep(0.01)
    tracker.stop_phase(phase1)

    tracker.start_phase(phase2)
    time.sleep(0.01)
    tracker.stop_phase(phase2)

    report = tracker.export_to_json()

    assert "plan_seconds" in report
    assert "implement_seconds" in report
    assert "all_phases" in report
    assert report["all_phases"]["plan"] == pytest.approx(report["plan_seconds"])
