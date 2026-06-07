import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORT_PATH = os.path.join(ROOT, "ai_tester_report.json")


def test_report_exists():
    assert os.path.exists(REPORT_PATH), (
        f"ai_tester_report.json not found at {REPORT_PATH}. Run scoring.py to generate the report before running tests.")


def test_report_schema():
    with open(REPORT_PATH, encoding='utf-8') as f:
        r = json.load(f)

    # Top-level
    assert r.get("version") == "1.0"
    assert "timestamp" in r
    assert isinstance(r.get("environment"), dict)

    # Environment
    prc = r["environment"].get("pytest_returncode")
    assert isinstance(prc, int)

    # Pytest metrics
    pytest_metrics = r.get("tests", {}).get("pytest")
    assert isinstance(pytest_metrics, dict)
    for k in ("passed", "failed", "total"):
        assert isinstance(pytest_metrics.get(k), int)
    pr = pytest_metrics.get("pass_rate")
    assert pr is None or (isinstance(pr, float) and 0.0 <= pr <= 1.0)

    # Evals (optional)
    evals = r.get("evals")
    if evals is not None:
        assert isinstance(evals, dict)
        metrics = evals.get("metrics")
        assert isinstance(metrics, dict)
        for k in ("total", "passed", "failed"):
            v = metrics.get(k)
            assert v is None or isinstance(v, int)
        pr2 = metrics.get("pass_rate")
        assert pr2 is None or (isinstance(pr2, float) and 0.0 <= pr2 <= 1.0)
        cases = evals.get("cases")
        assert cases is None or isinstance(cases, list)

    # Heuristics
    instr = r.get("heuristics", {}).get("instruction_adherence")
    assert isinstance(instr, dict)
    score = instr.get("score")
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
