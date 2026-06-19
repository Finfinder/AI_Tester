# AI_Tester v2 - TimeTracker

import time
from typing import Dict, Any


class TimeTracker:
    """
    Tracks the elapsed time for different phases of the AI_Tester workflow.
    Uses time.perf_counter() for high-resolution timing.
    """

    def __init__(self):
        self.start_times: Dict[str, float] = {}
        self.end_times: Dict[str, float] = {}

    def start_phase(self, phase_name: str):
        """Starts the timer for a given phase."""
        if phase_name in self.start_times and self.start_times[phase_name] != 0:
            print(f"Warning: Phase '{phase_name}' already started. Resetting timer.")

        self.start_times[phase_name] = time.perf_counter()
        self.end_times[phase_name] = 0.0  # Reset end time

    def stop_phase(self, phase_name: str) -> float:
        """Stops the timer for a given phase and returns the elapsed time."""
        if phase_name not in self.start_times:
            raise ValueError(
                f"Phase '{phase_name}' was never started. Call start_phase() first."
            )

        end_time = time.perf_counter()
        self.end_times[phase_name] = end_time

        elapsed = end_time - self.start_times[phase_name]
        print(f"Phase '{phase_name}' completed in {elapsed:.4f} seconds.")
        return elapsed

    def get_elapsed(self, phase_name: str) -> float:
        """Returns the elapsed time for a specific phase."""
        if phase_name not in self.start_times:
            raise ValueError(f"Phase '{phase_name}' was never started.")

        if phase_name not in self.end_times:
            # If end time is not set, assume it's still running or use current time
            return time.perf_counter() - self.start_times[phase_name]

        return self.end_times[phase_name] - self.start_times[phase_name]

    def get_all_elapsed(self) -> Dict[str, float]:
        """Returns a dictionary of elapsed times for all tracked phases."""
        elapsed_times = {}
        for phase in self.start_times:
            elapsed_times[phase] = self.get_elapsed(phase)
        return elapsed_times

    def export_to_json(self) -> Dict[str, Any]:
        """Returns a serializable dictionary containing all timing data.

        Always includes ``plan_seconds`` and ``implement_seconds`` keys with
        a default of ``0.0`` when the corresponding phase has not been tracked.
        """
        all_elapsed = self.get_all_elapsed()
        return {
            "plan_seconds": all_elapsed.get("plan", 0.0),
            "implement_seconds": all_elapsed.get("implement", 0.0),
            "all_phases": all_elapsed,
        }


# Example usage (for testing purposes)
if __name__ == "__main__":
    tracker = TimeTracker()

    print("--- Starting Phase A ---")
    tracker.start_phase("plan")
    time.sleep(0.1)  # Simulate work
    elapsed_plan = tracker.stop_phase("plan")
    print(f"Plan time recorded: {elapsed_plan:.4f}s")

    print("\n--- Starting Phase B ---")
    tracker.start_phase("implement")
    time.sleep(0.2)  # Simulate work
    elapsed_implement = tracker.stop_phase("implement")
    print(f"Implement time recorded: {elapsed_implement:.4f}s")

    print("\n--- Final Report ---")
    report = tracker.export_to_json()
    print(f"Full Report: {report}")

    # Test error handling
    try:
        tracker.get_elapsed("non_existent_phase")
    except ValueError as e:
        print(f"Caught expected error: {e}")
