"""Scoring script for AI_Tester PoC.

Normalizes test, evals and heuristic outputs into a stable schema and
writes ai_tester_report.json.

Schema (v1.0):
{
  "version": "1.0",
  "timestamp": "...",
  "environment": { ... },
  "tests": { "pytest": {passed, failed, total, pass_rate, report_file} },
  "evals": { runner, benchmark, metrics: {total, passed, failed, pass_rate}, cases: [...] },
  "heuristics": { instruction_adherence: {...} },
  "artifacts": { pytest_report, evals_report },
  "raw": { ... }
}
"""
import subprocess
import re
import json
import os
import time

ROOT = os.path.dirname(__file__)
TASK_DIR = os.path.join(ROOT, "task")
REPORT_PATH = os.path.join(ROOT, "ai_tester_report.json")
EVALS_PATH = os.path.join(ROOT, "evals_report.json")
PYTEST_REPORT_PATH = os.path.join(ROOT, "pytest_report.json")
REPORT_SCHEMA_VERSION = "1.0"


def run_pytest():
    report_file = PYTEST_REPORT_PATH
    cmd = ["pytest", "-q", "task/tests", "--json-report", f"--json-report-file={report_file}"]
    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out, _ = proc.communicate()
    return proc.returncode, out, report_file


def parse_pytest(output, returncode, report_file):
    # try to read pytest-json-report if present
    if os.path.exists(report_file):
        try:
            with open(report_file, encoding='utf-8') as f:
                data = json.load(f)
            summary = data.get("summary", {})
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            total = summary.get("collected", passed + failed)
            pass_rate = (passed / total) if total > 0 else 0.0
            return {"passed": passed, "failed": failed, "total": total, "pass_rate": pass_rate, "report_file": report_file}
        except Exception:
            pass
    # fallback to parsing output
    passed = 0
    failed = 0
    m = re.search(r"(\d+)\s+passed", output)
    if m:
        passed = int(m.group(1))
    m2 = re.search(r"(\d+)\s+failed", output)
    if m2:
        failed = int(m2.group(1))
    if passed + failed == 0:
        if returncode == 0:
            dots = output.count('.')
            Fs = output.count('F')
            passed = dots
            failed = Fs
        else:
            failed = 1
    total = passed + failed
    pass_rate = (passed / total) if total > 0 else 0.0
    return {"passed": passed, "failed": failed, "total": total, "pass_rate": pass_rate, "report_file": None}


def instruction_adherence_heuristic(agent_file_path):
    """Naive heuristic: check for presence of keywords and a docstring describing intent.
    Returns score in [0,1] and details."""
    if not os.path.exists(agent_file_path):
        return {"score": 0.0, "reason": "agent file missing"}
    text = open(agent_file_path, encoding='utf-8').read().lower()
    keywords = ["def", "return", "sum", "list", "for"]
    found = [k for k in keywords if k in text]
    keyword_score = len(found) / len(keywords)
    has_doc = '"""' in text or "'''" in text
    doc_score = 1.0 if has_doc else 0.0
    # simple weighted combination
    score = 0.7 * keyword_score + 0.3 * doc_score
    details = {"keywords_found": found, "keyword_score": keyword_score, "has_docstring": has_doc}
    return {"score": round(score, 3), "details": details}


def normalize_evals(raw):
    """Normalize various eval report shapes into a canonical structure.
    Expected fields produced by evals_integration.py local fallback are:
      {"runner": "local_fallback", "benchmark": path, "total": n, "passed": m, "details": [cases...]}
    This function returns:
      { runner, benchmark, metrics: {total, passed, failed, pass_rate}, cases: [...] }
    """
    if not raw:
        return None
    try:
        runner = raw.get('runner') if isinstance(raw, dict) else None
        benchmark = raw.get('benchmark') if isinstance(raw, dict) else None
        total = raw.get('total') if isinstance(raw, dict) else None
        passed = raw.get('passed') if isinstance(raw, dict) else None
        details = raw.get('details') if isinstance(raw, dict) else None
        failed = None
        pass_rate = None
        if total is not None and passed is not None:
            failed = total - passed
            pass_rate = (passed / total) if total > 0 else None
        # Normalize cases list
        cases = []
        if isinstance(details, list):
            for d in details:
                cases.append(d)
        return {
            "runner": runner,
            "benchmark": benchmark,
            "metrics": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": pass_rate
            },
            "cases": cases
        }
    except Exception:
        return {"error": "failed_to_normalize"}


def run_scoring():
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    rc, out, report_file = run_pytest()

    pytest_metrics = parse_pytest(out, rc, report_file)
    agent_path = os.path.join(TASK_DIR, 'agent_output.py')
    instr = instruction_adherence_heuristic(agent_path)

    # Load raw evals if present
    raw_evals = None
    try:
        if os.path.exists(EVALS_PATH):
            with open(EVALS_PATH, encoding='utf-8') as ef:
                raw_evals = json.load(ef)
    except Exception as e:
        raw_evals = {"error": f"failed_to_load: {e}"}

    normalized_evals = normalize_evals(raw_evals)

    report = {
        "version": REPORT_SCHEMA_VERSION,
        "timestamp": ts,
        "environment": {
            "pytest_returncode": rc
        },
        "tests": {
            "pytest": pytest_metrics
        },
        "evals": normalized_evals,
        "heuristics": {
            "instruction_adherence": instr
        },
        "artifacts": {
            "pytest_report": PYTEST_REPORT_PATH if os.path.exists(PYTEST_REPORT_PATH) else None,
            "evals_report": EVALS_PATH if os.path.exists(EVALS_PATH) else None
        },
        "raw": {
            "pytest_output_snippet": out[:2000],
            "raw_evals": raw_evals
        }
    }

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Saved report to {REPORT_PATH}")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    run_scoring()
