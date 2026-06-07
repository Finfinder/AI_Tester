"""Integracja OpenAI Evals — PoC dla AI_Tester

Ten plik zapewnia:
- szablon benchmarku w katalogu benchmarks/
- lokalny runner, który uruchamia przypadki testowe przeciwko funkcji z task/ (fallback)
- opcjonalną próbę uruchomienia OpenAI Evals (jeśli jest zainstalowany)

Użycie:
    python evals_integration.py --write-sample    # wygeneruj sample_benchmark.py
    python evals_integration.py --local-run      # uruchom lokalny runner (nie wymaga openai-evals)
    python evals_integration.py --run-evals      # spróbuj uruchomić openai-evals (jeśli zainstalowany)

Wynik lokalny zapisany jest do AI_Tester/evals_report.json
"""
from pathlib import Path
import runpy
import json
import importlib
import subprocess
import sys
from typing import List, Dict, Any

ROOT = Path(__file__).parent
BENCH_DIR = ROOT / 'benchmarks'
SAMPLE_PATH = BENCH_DIR / 'sample_benchmark.py'
REPORT_PATH = ROOT / 'evals_report.json'

SAMPLE_TEMPLATE = '''# Sample benchmark for AI_Tester (local-friendly)

# cases: list of {{'input': <value>, 'expected': <value>}}
cases = [
    {{'input': [1,2,3], 'expected': 6}},
    {{'input': [], 'expected': 0}},
]

# optional metadata
meta = {{'name': 'sum_list_simple', 'description': 'sum_list should sum a list of numbers'}}
'''


def write_sample_benchmark():
    BENCH_DIR.mkdir(exist_ok=True)
    SAMPLE_PATH.write_text(SAMPLE_TEMPLATE, encoding='utf-8')
    print(f"Wrote sample benchmark to {SAMPLE_PATH}")


def load_cases_from_benchmark(path: Path) -> List[Dict[str, Any]]:
    # execute benchmark file and read `cases` variable
    data = runpy.run_path(str(path))
    cases = data.get('cases')
    if not isinstance(cases, list):
        raise ValueError('Benchmark file must define a list `cases`')
    return cases


def local_run(bench_path: Path = None):
    """Run the benchmark locally by importing the agent code from task/ and executing cases.
    Produces a JSON report at REPORT_PATH."""
    if bench_path is None:
        bench_path = SAMPLE_PATH
    print(f"Loading benchmark from {bench_path}")
    cases = load_cases_from_benchmark(Path(bench_path))

    # import the function under test from task.agent_output
    try:
        from task.agent_output import sum_list
    except Exception as e:
        print("Failed to import agent function from task.agent_output:", e)
        # try to provide helpful error
        report = {'error': str(e)}
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding='utf-8')
        return

    total = len(cases)
    passed = 0
    details = []
    for i, c in enumerate(cases, start=1):
        inp = c.get('input')
        expected = c.get('expected')
        try:
            out = sum_list(inp)
            ok = out == expected
            details.append({'case': i, 'input': inp, 'expected': expected, 'output': out, 'passed': ok})
            if ok:
                passed += 1
        except Exception as e:
            details.append({'case': i, 'input': inp, 'expected': expected, 'error': str(e), 'passed': False})

    report = {
        'runner': 'local_fallback',
        'benchmark': str(bench_path),
        'total': total,
        'passed': passed,
        'pass_rate': passed / total if total else None,
        'details': details,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f"Wrote local evals report to {REPORT_PATH}")


def try_run_openai_evals(bench_path: Path = None):
    """Attempt to invoke OpenAI Evals runner. This is optional and best-effort.
    If openai-evals is not installed, fall back to local_run.
    """
    if bench_path is None:
        bench_path = SAMPLE_PATH
    # prefer importing the package if available
    try:
        spec = importlib.util.find_spec('openai_evals')
        if spec is not None:
            print('openai-evals package found; attempting to run via module entrypoint')
            cmd = [sys.executable, '-m', 'openai_evals.run', str(bench_path)]
            print('Running:', ' '.join(cmd))
            subprocess.check_call(cmd, cwd=str(BENCH_DIR))
            return
    except Exception as e:
        print('openai-evals invocation failed:', e)

    print('openai-evals not available or failed; running local fallback')
    local_run(bench_path)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--write-sample', action='store_true', help='Write sample benchmark to benchmarks/')
    p.add_argument('--local-run', action='store_true', help='Run local fallback evaluator (no external deps)')
    p.add_argument('--run-evals', action='store_true', help='Try to run openai-evals, fallback to local')
    args = p.parse_args()

    if args.write_sample:
        write_sample_benchmark()
    if args.local_run:
        local_run()
    if args.run_evals:
        try_run_openai_evals()
