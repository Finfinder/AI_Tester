AI Tester PoC

Cel: Prosty PoC do uruchamiania testów kodu wygenerowanego przez agenta w izolowanym runnerze (Docker), oraz integracji z narzędziami oceny (Evals, LangChain).

Szybkie kroki:

1. (Opcjonalnie) Zainstaluj Docker.
2. Uruchom PowerShell: .\run_poc.ps1 — skrypt zbuduje obraz i uruchomi testy w kontenerze.
3. Alternatywnie uruchom Python harness: python harness.py (wymaga Docker dostępnego w PATH).

Zawartość katalogu:
- Dockerfile — obraz runnera uruchamiający pytest w katalogu task/
- task/agent_output.py — przykładowy plik generowany przez agenta
- task/tests/test_agent_output.py — przykładowy test PyTest
- harness.py — prosty orchestrator budujący i uruchamiający kontener
- langchain_agent.py — placeholder pokazujący, jak można wygenerować kod z LangChain (przykład)
- run_poc.ps1 — helper uruchamiający docker build + run
- requirements.txt — lista pakietów przydatnych do rozwoju PoC (nie wymagana do uruchomienia kontenera)
