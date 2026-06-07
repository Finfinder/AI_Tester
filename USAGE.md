AI_Tester PoC — dodatkowe narzędzia

Scoring:
- Uruchom: python scoring.py
- Zapisuje wynik do ai_tester_report.json (pass rate, naiwna heurystyka zgodności z instrukcjami)

Evals integration (przykład):
- Uruchom: python evals_integration.py --write-sample  # utworzy benchmarks/sample_benchmark.py
- Gdy masz zainstalowane OpenAI Evals, możesz spróbować: python evals_integration.py --run

Notatki:
- Skrypty są demonstracyjne i zawierają heurystyki zastępcze. Do produkcyjnego użycia warto rozszerzyć:
  - dokładne parsowanie wyników pytest (np. plugin json-report)
  - statyczną analizę (pylint/flake8) oraz mutation testing
  - embedding-based similarity dla mierzenia instruction-adherence
