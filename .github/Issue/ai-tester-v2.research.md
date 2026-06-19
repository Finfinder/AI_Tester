# AI_Tester v2 — System Oceny Jakości Pracy Agentów AI

## Szczegóły zadania

| Pole | Wartość |
|---|---|
| Tytuł | AI_Tester v2 — System Oceny Jakości Pracy Agentów AI |
| Opis | Rozwinięcie obecnego PoC AI_Tester w kompleksowy system oceny pracy agentów AI generujących kod w dwóch różnych stosach technologicznych (TS/JS/React oraz Python/React/SQLite). System ma automatycznie generować zadania (feature, refactor, debug), uruchamiać agenta z wykorzystaniem promptów /plan i /implement z AI_Instruction, a następnie oceniać jakość pracy agenta sędzią wielowymiarową. |
| Priorytet | High |
| Złożoność analizy rozwiązań | L |

## Wpływ biznesowy

AI_Tester v2 ma na celu obiektywną ewaluację jakości pracy agentów AI (GitHub Copilot, Claude, GPT) w zadaniach programistycznych. System dostarczy metryki umożliwiające porównanie agentów, identyfikację słabych obszarów (np. jakość planu, bezpieczeństwo kodu, użycie narzędzi) oraz ciągłą poprawę workflow AI_Instruction. Wyniki będą wykorzystywane do:

- Walidacji skuteczności istniejących skilli i promptów AI_Instruction
- Identyfikacji luk w obecnych instrukcjach Copilot
- Optymalizacji workflow planowania i implementacji
- Benchmarkowania różnych modeli AI w zadaniach programistycznych
- Generowania raportów dla zespołów deweloperskich

## Zebrane informacje

### Baza kodu

#### Obecny stan AI_Tester (PoC)

**Struktura:**

| Plik / Katalog | Opis | Potencjalna rola w AI_Tester v2 |
|---|---|---|
| `harness.py` | Prosty orchestrator Docker (build + run kontenera) |  |
| `langchain_agent.py` | Placeholder generowania kodu z LangChain |  |
| `scoring.py` | Normalizacja wyników pytest + naiwna heurystyka instruction adherence |  |
| `evals_integration.py` | Lokalny runner benchmarków + opcjonalny OpenAI Evals | Można rozszerzyć jako dodatkowy obiektywny kanał oceny implementacji, szczególnie dla tasków feature/debug z benchmarkami deterministycznymi |
| `Dockerfile` | Python 3.11 z pytest i openai-evals | Można rozszerzyć o narzędzia do statycznej analizy TS/JS/Python |
| `run_poc.ps1` | Skrypt budowania i uruchamiania w Docker | Można zastąpić lub rozszerzyć o sekwencyjny workflow `/plan → /implement → /review → scoring` |
| `task/agent_output.py` | Przykładowy kod generowany przez agenta (`sum_list`) | W v2 powinien być generowany dynamicznie w izolowanym katalogu taska |
| `task/tests/test_agent_output.py` | Przykładowe testy pytest | W v2 powinien być zestaw testów per task, w tym testy regresji dla debug |
| `benchmarks/sample_benchmark.py` | Sample benchmark z przypadkami testowymi | Można rozszerzyć na benchmarki feature/debug oraz ewentualne metryki refactor |
| `ai_tester_report.json` | Sformatowany raport wyjściowy | Powinien zostać zastąpiony lub rozszerzony do rankingu modeli i szczegółów per task |
| `evals_report.json` | Raport z evals | Powinien być jednym z artefaktów pomocniczychJudge, a nie jedynym źródłem oceny |
| `pytest_report.json` | Raport z pytest | Powinien być jednym z artefaktów weryfikacji implementacji |
| `USAGE.md` | Dokumentacja użytkowania |  |

**Ocena obecnego stanu:**

| Obszar | Ocena | Komentarz |
|---|---|---|
| Orchestracja | PoC | Tylko build + run Docker, brak workflow multi-phase |
| Scoring | Bazowy | Tylko pass rate pytest + naiwna heurystyka słów kluczowych |
| Evals | Bazowy | Lokalny runner benchmarków, brak integracji z AI_Instruction |
| Reporting | Bazowy | Prosty JSON, brak dashboardu |
| Judge | Brak | Nie zaimplementowany |
| Task Generator | Brak | Nie zaimplementowany |
| Test Repositories | 1 (tylko task/) | Brak izolowanych repo TS/JS/React i Python/React/SQLite |
| Metryki narzędzi | Brak | Nie śledzi użycia terminala, search, file operations |
| Pomiar czasu | Brak | Nie mierzy czasu generowania rozwiązania |
| Integracja AI_Instruction | Brak | Nie wykorzystuje skilli (SOLID, OWASP, ARIA) ani promptów (/review) |
| Integracja VS Code API | Brak | Nie ma kontrolowanego adaptera narzędzi i terminala dla modelu |

#### Istniejące zasoby w AI_Instruction do wykorzystania

**Skille oceny jakości kodu:**

| Skill | Przeznaczenie w AI_Tester v2 |
|---|---|
| `code-reviewing` | Główny kontrakt weryfikacyjny dla Judge |
| `ensuring-code-quality` | Weryfikacja z SonarQube, lintery, quality gates |
| `ensuring-accessibility` | Ocena ARIA/WCAG 2.1 AA dla frontend |
| `implementing-frontend` | Kryteria jakości komponentów React |
| `implementing-backend` | Kryteria jakości backendu (SOLID, clean architecture) |
| `reviewing-frontend` | Szybkie findings review regresji UI |
| `ts-project-structure` | Ocena struktury projektów TS |
| `ts-styling-and-linting` | Ocena stylu i lintingu TS/JS |
| `typescript-best-practices` | Ocena zaawansowanych praktyk TS |
| `javascript-modern-patterns` | Ocena ES2020+ patterns |
| `node-backend-guidelines` | Kryteria jakości Node.js backendu |
| `react-accessibility` | Szczegółowa ocena a11y React |
| `react-performance` | Ocena wydajności React |
| `react-testing` | Ocena jakości testów React |
| `testing-ts-js` | Ocena jakości testów TS/JS |
| `testing-e2e` | Ocena testów E2E |
| `modeling-domain` | Ocena wzorców DDD |
| `engineering-databases` | Ocena projektu bazy danych |

**Szablony i prompty:**

| Zasób | Przeznaczenie w AI_Tester v2 |
|---|---|
| `.github/prompts/plan.prompt.md` | Uruchamianie planowania przez agenta |
| `.github/prompts/implement.prompt.md` | Uruchamianie implementacji przez agenta |
| `.github/prompts/review.prompt.md` | Uruchamianie code review przez Judge |
| `.github/skills/architecture-designing/plan.example.md` | Szablon walidacji struktury planu |
| `.github/skills/task-analysing/research.example.md` | Szablon walidacji struktury research |
| `.github/skills/code-reviewing/references/validations.md` | Reguły V-01..V-18 dla Judge |
| `Docs/OWASP_TOP_30_PLUS.md` | Kryteria bezpieczeństwa OWASP |

**Skrypty i narzędzia:**

| Narzędzie | Przeznaczenie w AI_Tester v2 |
|---|---|
| `scripts/get-dependency-freshness-report.ps1` | Ocena świeżości zależności |
| `scripts/ensure-pester5.ps1` | Bootstrap Pester 5.7.1 |
| `tests/*.tests.ps1` | Suite'y walidacyjne (można rozszerzyć) |

### Powiązane linki

- [OWASP TOP 30+](e:\AI_WORKSPACE\Moje projekty\AI_Instruction\Docs\OWASP_TOP_30_PLUS.md) — rozszerzona lista wektorów bezpieczeństwa
- [Reguły walidacji kodu](e:\AI_WORKSPACE\Moje projekty\AI_Instruction\.github\skills\code-reviewing\references\validations.md) — V-01..V-18 dla Judge
- [Szablon planu](e:\AI_WORKSPACE\Moje projekty\AI_Instruction\.github\skills\architecture-designing\plan.example.md) — struktura planu do walidacji
- [Szablon research](e:\AI_WORKSPACE\Moje projekty\AI_Instruction\.github\skills\task-analysing\research.example.md) — struktura research do walidacji

### Repozytoria źródłowe i taski

AI_Tester v2 powinien wykorzystywać realne repozytoria jako bazę kodu do testów agentów, ale wyłącznie po wykonaniu `git clone` do izolowanego katalogu. Agent nie pracuje na repozytorium źródłowym ani na „żywym organizmie".

| Źródło | Typ repo | Potencjalne zadania testowe | Uwagi |
|---|---|---|---|
| `https://github.com/Finfinder/Investment-Assistant` | Fullstack: Python/FastAPI + Next.js/React + SQLite/Docker | Feature backend, feature frontend, debug testów, refactor modułów analizy | Najbardziej realistyczne repo fullstack; dobre do testów Python + React |
| `https://github.com/Finfinder/AgentDeck` | Electron + React + TypeScript + SQLite + MCP/Monaco | Refactor UI, debug testów, poprawki a11y, integracja narzędzi, testy architektury | Dobre do testów React/TS, a11y, architektury i narzędzi AI |
| `https://github.com/Finfinder/AutoResearch_SQLServer` | Python CLI + SQL Server | Refactor Python, debug testów, poprawki walidacji, testy statycznej analizy | Dobre do backendu Python, SQL, walidacji i testów jednostkowych |
| `E:\AI_WORKSPACE\Moje projekty\TravianBot\` | Python + Playwright | Debug testów E2E, refactor skryptów, poprawki bezpieczeństwa konfiguracji | Dobre do testów automation, Playwright i konfiguracji YAML |

#### Taski z GitHub Issues

Dla repozytoriów `Investment-Assistant`, `AgentDeck` i `AutoResearch_SQLServer` taski mogą pochodzić z otwartych Issues na GitHubie. Takie Issues mają zwykle wystarczający poziom złożoności i są lepszym źródłem benchmarków niż zbyt proste zadania syntetyczne.

Przykładowe Issues do wykorzystania jako baza tasków:

| Repozytorium | Issue | Typ zadania | Potencjalny obszar |
|---|---|---|---|
| `Investment-Assistant` | `IA-18 Build a mobile companion surface` (#88) | feature | frontend/mobile UX |
| `Investment-Assistant` | `IA-17 Ship a PWA experience` (#87) | feature | frontend/PWA |
| `Investment-Assistant` | `IA-13 Add Polish and English localization` (#86) | feature | i18n/frontend |
| `Investment-Assistant` | `IA-12 Add multi-user authentication` (#85) | feature | backend/auth |
| `Investment-Assistant` | `IA-10 Add broker-backed auto-trading` (#83) | feature | backend/automation |
| `Investment-Assistant` | `IA-9 Add cryptocurrency support via CCXT` (#82) | feature | backend/data provider |
| `Investment-Assistant` | `IA-8 Build a notification system` (#81) | feature | backend/notifications |
| `Investment-Assistant` | `IA-100 Add observability metrics for macro data sources` (#77) | feature/refactor | observability/backend |
| `Investment-Assistant` | `IA-97 Add a shared lookback test helper` (#74) | refactor/tests | test helper/backend |
| `AgentDeck` | `AD-28 Add local telemetry system with output channel and usage data collection` (#53) | feature | telemetry/Node |
| `AgentDeck` | `AD-27 Add Settings UI panel with gear icon in activity bar` (#52) | feature | React/UI |
| `AgentDeck` | `AD-26 Aggregate Problems panel diagnostics from all open editors` (#43) | feature/refactor | diagnostics/Monaco |
| `AgentDeck` | `AD-25 Add OpenRouter Fusion support for multi-model deliberation` (#42) | feature | OpenRouter/model gateway |
| `AgentDeck` | `AD-20 Automated guard for pinning third-party actions` (#29) | feature/security | CI/security |
| `AgentDeck` | `AD-18 Expand vscode shim to broader VS Code API compatibility` (#23) | feature/compatibility | extension host |
| `AgentDeck` | `AD-16 Add standalone general CI workflow` (#21) | CI/CD | validation pipeline |
| `AutoResearch_SQLServer` | `Model Benchmark Result Payloads with TypedDict or Dataclass` (#30) | refactor | Python typing |
| `AutoResearch_SQLServer` | `Move Generator Hyperparameters to settings.yaml` (#29) | refactor | configuration |
| `AutoResearch_SQLServer` | `Migrate Project Metadata and Tooling to pyproject.toml` (#28) | refactor/tooling | packaging |
| `AutoResearch_SQLServer` | `Add LLM-Assisted SQL Variant Generation` (#27) | feature/AI | SQL generation |
| `AutoResearch_SQLServer` | `Add an Agent That Suggests Indexes` (#26) | feature/AI | SQL/indexing |
| `AutoResearch_SQLServer` | `Add an Agent That Analyzes Execution Plans` (#25) | feature/AI | execution plans |
| `AutoResearch_SQLServer` | `Add Stored Procedure Parsing and Optimization` (#24) | feature | SQL parsing |
| `AutoResearch_SQLServer` | `Support Triple Transformation Combinations` (#23) | feature | query variants |
| `AutoResearch_SQLServer` | `Integrate Automated Query Optimization into CI/CD` (#21) | CI/CD | automation |
| `AutoResearch_SQLServer` | `Build a Benchmark Dashboard` (#20) | feature | reporting/dashboard |
| `AutoResearch_SQLServer` | `Persist Benchmark Results to a Database` (#19) | feature/backend | persistence |
| `AutoResearch_SQLServer` | `Add Nightly Benchmark Runs` (#18) | CI/CD | scheduled benchmarks |
| `AutoResearch_SQLServer` | `Add Experiment History Tracking` (#17) | feature/backend | persistence/history |

#### Taski dla TravianBot

Dla `TravianBot` taski powinny być generowane lokalnie, ponieważ repo nie ma obecnie Issues do wykorzystania. Generowane taski powinny mieć zbliżony poziom złożoności do Issues z pozostałych repozytoriów.

Przykładowe generowane taski:

- refactor konfiguracji YAML do walidowanego schematu i usunięcia sekretów z plików konfiguracyjnych,
- debug testów Playwright z celowym błędem w selektorze lub oczekiwaniu,
- dodanie retry i timeoutów dla operacji zależnych od UI lub sieci,
- wydzielenie adapterów akcji do osobnego modułu,
- dodanie testów regresji dla scheduler cycle,
- poprawka obsługi wielu profili serwerów,
- refactor parsera konfiguracji i walidacji ustawień,
- debug testów E2E z wielopoziomowym zagnieżdżeniem problemu, np. błąd w konfiguracji + błąd w selektorze.

#### Rola promptu `/plan`

Taski z Issues są traktowane jako źródło wymagań, a nie pełny opis techniczny. Nie należy przed uruchomieniem agenta przygotowywać pełnego kontekstu repo, zakresu zadania, kryteriów akceptacji, ograniczeń, poleceń walidacyjnych, mocków ani fixtures.

Prompt `/plan` powinien samodzielnie zebrać i przygotować:

- kontekst repo,
- zakres zadania,
- kryteria akceptacji,
- ograniczenia,
- polecenia walidacyjne,
- mocki lub fixtures, jeśli są potrzebne.

W treści promptu `/plan` można dodać instrukcję, aby model zbadał kontekst repo i uzupełnił te elementy w planie. Dzięki temu ocena jakości planu mierzy rzeczywistą zdolność modelu do analizy niepełnego zadania, a nie jakość przygotowania zadania przez system.

Jeśli wybrane Issue będzie zbyt mało opisowe, można uzupełnić opis Issue o niezbędne minimum, ale nie należy tworzyć pełnej specyfikacji technicznej. Minimalne uzupełnienie powinno dotyczyć tylko braków uniemożliwiających zrozumienie zadania, np. brak jasnego celu, brak zakresu albo brak informacji, czy zadanie dotyczy backendu, frontendu lub testów.

#### Główna zasada doboru zadań

Głównym celem AI_Tester v2 powinno być unikanie zbyt prostych tasków. Taski z GitHub Issues mają zwykle wystarczający poziom złożoności i powinny być preferowane nad zadaniami syntetycznymi.

Testy powinny być jak najbardziej obiektywne. Oznacza to:

- wykorzystanie istniejących testów repozytorium,
- uruchamianie lintów, typechecków i buildów z repozytorium,
- dodawanie ukrytych testów tylko wtedy, gdy da się je zdefiniować bez naruszania celu zadania,
- oddzielanie twardych sygnałów walidacyjnych od jakościowej rubryki `/review`,
- raportowanie, które źródło dało który sygnał: testy, benchmarki, Evals, statyczna analiza oraz rubryka `/review`.

### Analiza rozwiązań

Zadanie wymaga analizy rozwiązań dotyczących:

1. **Architektury systemu orchestracji** — jak koordynować multi-phase workflow
2. **Mechanizmu generowania zadań** — jak tworzyć realistyczne taski z baseline, expected results i ukrytymi błędami
3. **Roli promptu `/plan`** — jak model ma sam badać kontekst repo i uzupełniać kryteria akceptacji, ograniczenia, polecenia walidacyjne, mocki lub fixtures
4. **Agenta sędzi** — jak zbudować wielowymiarowy evaluator wykorzystujący istniejące skille
5. **Systemu metryk** — jak mierzyć i agregować wyniki z wielu wymiarów
6. **Izolacji środowisk** — jak zapewnić sandbox dla każdego taska
7. **Integracji narzędziowej** — jak bezpiecznie udostępnić modelowi terminal, pliki, wyszukiwanie i narzędzia AI
8. **Roli istniejących mechanizmów LangChain i Evals** — czy mogą zwiększyć miarodajność oceny implementacji

**Złożoność: L (Złożone)** — zadanie wymaga wyboru architektury dla nowego subsystemu, który nie istnieje w obecnym codebase. Istniejące skille AI_Instruction dostarczają kryteriów oceny, ale nie gotowego rozwiązania orchestracji.

> **Rekomendacja:** Należy przygotować osobny plik `ai-tester-v2.solution-research.md` z analizą architektury orchestracji, mechanizmu task generation, designu judge agenta, roli promptu `/plan`, integracji narzędziowej przez VS Code Extension Host Adapter oraz roli mechanizmów LangChain/Evals jako pomocniczych sygnałów oceny implementacji. Patrz sekcja "Analiza rozwiązań" poniżej.

## Aktualny stan implementacji

### Istniejące komponenty do ponownego wykorzystania

| Komponent | Ścieżka | Status | Uwagi |
|---|---|---|---|
| `Docker harness` | `harness.py` | Do modyfikacji | Obecnie tylko build+run; rozszerzyć o sekwencyjny workflow `/plan → /implement → /review → scoring` |
| `Scoring engine` | `scoring.py` | Do modyfikacji | Obecnie tylko pytest pass rate; rozszerzyć o scoring implementacji 0–100 i agregację artefaktów |
| `Evals runner` | `evals_integration.py` | Do modyfikacji | Lokalny benchmark runner; może być dodatkowym obiektywnym sygnałem dla Judge |
| `LangChain placeholder` | `langchain_agent.py` | Do usunięcia/rozbudowy | Placeholder; może zostać zastąpiony adapterem OpenRouter albo pozostawiony jako opcjonalny runner agenta |
| `Dockerfile` | `Dockerfile` | Do modyfikacji | Obecnie tylko pytest; rozszerzyć o ESLint, ruff, pylint, tsc oraz narzędzia benchmarkowe |
| `Skrypt PowerShell` | `run_poc.ps1` | Do modyfikacji | Rozszerzyć o sekwencyjny workflow i konfigurację modeli |
| `Raport JSON` | `ai_tester_report.json` | Do rozszerzenia | Rozszerzyć schema do rankingu modeli, szczegółów per task i artefaktów pomocniczych |
| Reguły V-01..V-18 | `code-reviewing/references/validations.md` | Ponowne użycie | Gotowe do wykorzystania w Judge |
| OWASP TOP 30+ | `Docs/OWASP_TOP_30_PLUS.md` | Ponowne użycie | Gotowe kryteria bezpieczeństwa |
| Szablon planu | `architecture-designing/plan.example.md` | Ponowne użycie | Walidacja struktury planu |
| Szablon research | `task-analysing/research.example.md` | Ponowne użycie | Walidacja struktury research |
| Prompt /plan | `prompts/plan.prompt.md` | Ponowne użycie | Uruchamianie planowania |
| Prompt /implement | `prompts/implement.prompt.md` | Ponowne użycie | Uruchamianie implementacji |
| Prompt /review | `prompts/review.prompt.md` | Ponowne użycie | Code review przez Judge |

### Kluczowe pliki i katalogi do utworzenia

| Katalog / Plik | Przeznaczenie |
|---|---|
| `task-repos/repo-frontend-ts/` | Izolowane repo TS/JS/React do testów |
| `task-repos/repo-fullstack/` | Izolowane repo Python/React/SQLite do testów |
| `task-generator/` | Generator zadań (feature, refactor, debug) |
| `judge/` | Agent sędzi — wielowymiarowa ocena |
| `orchestrator/` | Koordynator całego workflow |
| `metrics/` | Silnik metryk i agregacji |
| `reporting/` | Generowanie raportów i dashboardu |
| `schemas/` | Schematy JSON dla raportów |
| `benchmarks/` | Rozszerzone benchmarki (obecnie tylko sample) |
| `scorers/` | Obiektywne skrypty scoringowe: testy, benchmarki, statyczna analiza, ewentualnie Evals |
| `agents/` | Adaptery uruchamiające modele OpenRouter, sędziego, opcjonalny runner LangChain oraz adapter narzędzi VS Code |
| `agents/vscode_adapter/` | Kontrolowany adapter VS Code API: chat participant, zarejestrowane narzędzia LM, terminal, uprawnienia i logowanie akcji |

## Analiza luk

### Luki identyfikowane w wymaganiach

**Luka 1: Zakres tasków debug**

Użytkownik wskazał "debug nie działającego testu z wielopoziomowym zagnieżdżeniem problemu". Niejasne jest, czy:

- Debug taski mają zawierać **celowo wstrzyknięte błędy** (np. 3-5 poziomów głębokości: błąd w komponencie → błąd w hooku → błąd w test → błąd w konfiguracji)?
- Czy system ma generować te błędy automatycznie, czy ręcznie?
- Czy solution (poprawka) ma być ukryte, czy jawne dla porównania?

**Pytanie 1: Zakres debug tasków**
> Czy debug taski mają zawierać celowo wstrzyknięte błędy na 3-5 poziomach głębokości (np. błąd w komponencie → błąd w hooku → błąd w test → błąd w konfiguracji)? Jeśli tak, czy solution ma być ukryte, czy jawne?

**Luka 2: Metryka jakości planu**

Użytkownik wskazał ocenę "jakości przygotowanego planu", ale nie sprecyzował kryteriów.

**Pytanie 2: Kryteria oceny planu**
> Jakie konkretne kryteria mają być wykorzystane do oceny jakości planu? Czy mają to być: (a) struktura zgodna z plan.example.md, (b) kompletność względem research.md, (c) adekwatność podejścia do zadania, (d) uwzględnienie bezpieczeństwa, (e) strategia testowania — czy wszystkie powyższe? Czy mają być wagi poszczególnych kryteriów?

**Luka 3: Metryka użycia narzędzi**

Użytkownik wskazał ocenę "jak model radził sobie z używaniem narzędzi i obsługą terminala", ale nie sprecyzował, co dokładnie ma być mierzone.

**Pytanie 3: Kryteria oceny użycia narzędzi**
> Jakie konkretne aspekty użycia narzędzi mają być oceniane? Czy: (a) poprawność komend terminala, (b) efektywność wyszukiwania (semantic_search vs grep vs read_file), (c) czy agent czytał plki przed modyfikacją, (d) czy agent stosował git workflow, (e) czy agent używał narzędzi AI (context7, web/fetch) adekwatnie? Czy każde z powyższych, czy wybrane kryteria?

**Luka 4: Pomiar czasu**

Użytkownik wskazał "czas generowania rozwiązania", ale nie sprecyzował, które etapy mają być mierzone.

**Pytanie 4: Granice pomiaru czasu**
> Czy czas ma być mierzony per-faza (czas planowania, czas implementacji, czas debugowania), czy jako całkowity czas od startu do końca? Czy mają być mierzone osobno czasy na pierwsze uruchomienie testów i na pierwsze zielone testy?

**Luka 5: Integracja z AI_Instruction**

Użytkownik wskazał wykorzystanie promptów /plan i /implement z AI_Instruction. Niejasne jest, czy:

- Agent ma być wywoływany **wewnątrz** AI_Instruction (jako część workspace), czy **poza** nim (jako osobny system)?
- Czy Judge ma być uruchamiany jako osobny agent Copilot (z promptem /judge), czy jako skrypt Python?
- Czy system ma wspierać **wiele modeli AI** (Copilot, Claude, GPT) do porównywania, czy tylko jeden?

**Pytanie 5: Architektura integracji z AI_Instruction**
> Czy AI_Tester v2 ma działać jako: (a) osobny system poza AI_Instruction z integracją przez API, (b) rozszerzenie workspace AI_Instruction z nowymi promptami i skillami, (c) hybryda — orchestrator poza AI_Instruction, ale Judge jako prompt /review w AI_Instruction? Które modele AI mają być wspierane do benchmarkingu?

**Luka 6: Zakres raportowania**

Użytkownik nie sprecyfikował, jakie raporty mają być generowane.

**Pytanie 6: Zakres raportowania**
> Jakie raporty mają być generowane? Czy: (a) per-task report (score dla każdego zadania), (b) cross-task summary (średnie wyniki dla danego agenta), (c) cross-repo comparison (porównanie TS vs Python), (d) trend analysis (wykresy zmian w czasie), (e) detailed findings z rekomendacjami — czy wszystkie, czy wybrane?

**Luka 7: Izolacja środowisk**

Niejasne, czy taski mają być uruchamiane sekwencyjnie, czy równolegle, oraz jak ma wyglądać izolacja.

**Pytanie 7: Izolacja i parallelizacja**
> Czy taski mają być uruchamiane sekwencyjnie (jeden po drugim), czy równolegle (wielokontenerowo)? Czy sandboxy mają być izolowane na poziomie Docker, czy wystarczą temp directories? Czy ma być mechanizm czyszczenia sandboxów po zakończeniu taska?

**Luka 8: Benchmarki dla refaktora i debugu**

Użytkownik wskazał trzy typy zadań (feature, refactor, debug), ale obecne benchmarki w AI_Tester PoC obsługują tylko feature (funkcje do przetestowania).

**Pytanie 8: Benchmarki dla refactor i debug**
> Jak mają wyglądać benchmarki dla refactor i debug? (a) Dla refactor: czy ma być porównanie kodu przed/pod względem metryk (cyclomatic complexity, LOC, test coverage)? (b) Dla debug: czy ma być porównanie naprawionego kodu z expected solution? Jakie metryki mają oceniać jakość refaktora i debugu?

**Luka 9: Integracja narzędziowa przez VS Code API**

Niejasne było, czy testowany model ma korzystać bezpośrednio z natywnego środowiska Copilot/VS Code, czy przez kontrolowany adapter narzędziowy.

**Pytanie 9: Integracja VS Code API**
> Jak udostępnić modelowi narzędzia takie jak terminal, pliki, wyszukiwanie i narzędzia AI, aby akcje były izolowane, logowane i oceniane?

**Luka 10: Adapter VS Code API**

Nie było określone, czy integracja ma używać `vscode.chat.createChatParticipant`, `vscode.lm.registerTool`, `vscode.window.createTerminal` i `shellIntegration.executeCommand`, czy tylko zewnętrznych skryptów/CLI.

**Pytanie 10: Adapter narzędzi VS Code**
> Czy integracja powinna być zrealizowana jako VS Code Extension Host Adapter z zarejestrowanymi narzędziami LM i dedykowanym terminalem, czy jako prostszy runner CLI?

### Odpowiedzi użytkownika

#### Pytanie 1: Zakres debug tasków
Debug taski mają zawierać **1–2 celowo wstrzyknięte błędy** w ramach jednego testu/zadania. Przykładowe typy błędów: błąd na poziomie komponentu, błąd w konfiguracji, błąd w samym teście. Solution ma być **ukryte**; model sam musi znaleźć przyczynę błędu, zdiagnozować problem i usunąć ją.

#### Pytanie 2: Kryteria oceny planu
Plan ma być oceniany według wszystkich kryteriów: struktura zgodna z `plan.example.md`, kompletność, adekwatność, bezpieczeństwo i strategia testowania. Wagi są równe dla każdego punktu; ewentualna modyfikacja wag może zostać dodana w przyszłości.

#### Pytanie 3: Kryteria oceny użycia narzędzi
Ocenie powinny podlegać: poprawność komend terminala, efektywność wyszukiwania oraz adekwatne użycie narzędzi AI, takich jak `context7` i `web/fetch`.

#### Pytanie 4: Granice pomiaru czasu
Czas ma być mierzony osobno dla przygotowania planu oraz implementacji aż do ukończenia zadania.

#### Pytanie 5: Architektura integracji z AI_Instruction
AI_Tester v2 ma korzystać z repozytorium AI_Instruction lub jego clona i wykorzystywać zawarte tam prompty, skille i agentów. Modele testowane mają pochodzić z OpenRouter. Przy uruchomieniu musi być wskazany model do przetestowania, a konfiguracja powinna umożliwiać ustawienie modelu sędziego.

#### Pytanie 6: Zakres raportowania
Raport główny ma być rankingiem modeli. Dla każdego modelu powinny być przyznawane punkty 0–100 za plan, implementację łącznie oraz użycie narzędzi i terminala. Ranking powinien umożliwiać rozwinięcie wyniku i pokazanie szczegółów wyników per task.

#### Pytanie 7: Izolacja i parallelizacja
Taski mają być uruchamiane sekwencyjnie: najpierw przygotowanie planu, następnie realizacja według planu przez `/implement`. Preferowane są `temp directories`; Docker sandboxy są dopuszczalne, jeśli w planie pojawi się uzasadnienie techniczne.

#### Pytanie 8: Benchmarki dla refactor i debug
Refactor ma być oceniany przez porównanie metryk jakości kodu przed i po oraz ocenę, czy refactor rzeczywiście poprawił jakość kodu. Debug ma być oceniany przez to, czy model znalazł i usunął przyczynę błędu. Metryki jakości obejmują zasady SOLID, OWASP TOP 30+ oraz inne kryteria określone przez skille używane przez prompt `/review` z AI_Instruction.

#### Pytanie 9: Integracja VS Code API
Testowany model ma korzystać z narzędzi przez kontrolowany VS Code Extension Host Adapter. Adapter ma rejestrować narzędzia przez `vscode.lm.registerTool`, tworzyć dedykowany terminal przez `vscode.window.createTerminal`, preferować `shellIntegration.executeCommand` dla komend z `exitCode`, a fallback `sendText` oznaczać jako brak pewnego kodu zakończenia.

#### Pytanie 10: Adapter narzędzi VS Code
Docelowe podejście to VS Code Extension Host Adapter, a nie prosty runner CLI. Narzędzia mają obejmować `run_terminal_command`, `read_file`, `write_file`, `search_files`, `list_directory`, `fetch_documentation` oraz `context7`. Wszystkie operacje mają być ograniczone do `workspacePath` taska i zapisane do `ToolLogger`.

- Taski z GitHub Issues mają być preferowane, ponieważ mają wystarczający poziom złożoności i nie są zbyt proste.
- Taski z Issues są źródłem wymagań, ale prompt `/plan` ma sam zebrać kontekst repo, kryteria akceptacji, ograniczenia, polecenia walidacyjne, mocki lub fixtures.
- Pełne specyfikacje techniczne nie powinny być przygotowywane przed `/plan`, aby nie osłabiać pomiaru jakości planowania.
- Jeśli Issue jest zbyt mało opisowe, można uzupełnić opis o niezbędne minimum, ale nie o pełną specyfikację.
- Testy powinny być jak najbardziej obiektywne: istniejące testy repozytorium, lint/typecheck/build, ukryte testy tylko tam, gdzie mają sens, oraz wyraźne oddzielenie sygnałów twardych od oceny `/review`.
- Integracja narzędziowa ma być realizowana przez kontrolowany **VS Code Extension Host Adapter**, który udostępnia testowanemu modelowi zarejestrowane narzędzia i terminal, a wszystkie akcje zapisuje do `ToolLogger`.
- Model testowany nie powinien mieć bezpośredniego dostępu do repozytorium źródłowego. Wszystkie operacje plików, wyszukiwania i terminala mają być ograniczone do `workspacePath` taska.
- Dla terminala preferowane jest użycie `window.createTerminal` oraz `shellIntegration.executeCommand`, gdy dostępne, aby uzyskać `exitCode` z `onDidEndTerminalShellExecution`; fallback do `sendText` jest dozwolony, ale musi oznaczać `terminal_exit_code: unknown`.
- Narzędzia VS Code powinny obejmować co najmniej: `run_terminal_command`, `read_file`, `write_file`, `search_files`, `list_directory`, `fetch_documentation` oraz `context7`.
- Narzędzia plikowe i terminalowe muszą wymuszać politykę uprawnień: dozwolone tylko w izolowanym workspace taska, komendy wychodzące poza workspace lub modyfikujące system wymagają blokady albo jawnej zgody.
- Faza 1 może przygotować interfejs adaptera i mocki, a pełna implementacja VS Code Extension Host Adapter powinna trafić do kolejnej fazy jako osobny komponent.

## Decyzje projektowe

### Decyzja 10: Rola LangChain i Evals w ocenie implementacji

Istniejące mechanizmy LangChain i Evals mogą zostać wykorzystane w AI_Tester v2, ale wyłącznie jako **pomocnicze źródła obiektywnych sygnałów**, a nie jako zamiennik głównego sędziego.

#### Czy ma to sens?

Tak, ma to sens, jeśli zostaną zastosowane selektywnie:

- **Evals / lokalny benchmark runner** ma sens dla tasków typu `feature` i `debug`, gdzie da się zdefiniować deterministyczne przypadki testowe, oczekiwane zachowanie albo ukryty zestaw testów.
- **LangChain** ma sens jako opcjonalny adapter/runner agenta lub warstwa orkiestracji, jeśli ułatwi uruchamianie modeli OpenRouter i zbieranie artefaktów wykonania.
- **Nie ma sensu** opierać całego rankingu wyłącznie na Evals, ponieważ Evals dobrze mierzą zachowanie funkcjonalne, ale słabo oceniają jakość planu, SOLID, ARIA, bezpieczeństwo, architekturę i jakość użycia narzędzi.

#### Rekomendowane zastosowanie

| Mechanizm | Rola w AI_Tester v2 | Czy wpływa na ranking? | Zakres |
|---|---|---:|---|
| `/review` z AI_Instruction | Główna ocena jakości implementacji i refactorów | Tak | SOLID, OWASP TOP 30+, ARIA, architektura, testy, narzędzia |
| Testy jednostkowe/integracyjne/E2E | Obiektywna weryfikacja poprawności | Tak, pośrednio | Feature i debug |
| Lokalny benchmark runner / Evals | Dodatkowy sygnał funkcjonalny | Tak, pomocniczo | Feature i debug z deterministycznymi przypadkami |
| LangChain | Opcjonalny adapter/runner agenta | Nie bezpośrednio | Uruchamianie agenta, zbieranie logów, integracja z OpenRouter |
| Statyczna analiza | Dodatkowy sygnał jakości kodu | Tak, pośrednio | TS/JS, Python, security, style |

#### Wpływ na scoring

Mechanizmy Evals i lokalne benchmarki mogą zwiększać miarodajność oceny implementacji, ale nie powinny dominować nad oceną sędziego. Rekomendowane podejście:

- wynik implementacji 0–100 jest wyliczany głównie przez `/review` oraz statyczną analizę,
- wyniki testów i benchmarków są traktowane jako twarde sygnały: pass/fail, coverage, liczba błędów, liczba przypadków spełnionych,
- Evals mogą być dodatkowym komponentem jakości implementacji, ale z ograniczoną wagą, np. jako sygnał pomocniczy w szczegółach per task,
- LangChain nie powinien być osobnym kryterium rankingowym, chyba że w przyszłości zostanie użyty jako główny adapter uruchamiania agentów OpenRouter.

#### Ograniczenia

- Evals z obecnego PoC są zbyt proste dla pełnego rankingu — obsługują głównie lokalny benchmark funkcji.
- LangChain w obecnym `langchain_agent.py` jest tylko placeholderem i wymagałby przebudowy, jeśli miałby być wykorzystany produkcyjnie.
- Nie należy mieszać oceny sędziego z wynikami Evals w sposób nieczytelny; raport powinien wskazywać, które źródło dało który sygnał.

### Decyzja 11: Architektura systemu

Na podstawie zebranych informacji, odpowiedzi użytkownika i dostępnych zasobów, rekomendowana architektura:

```
AI_Tester v2 Architecture (Rekomendacja):

┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                             │
│  (orchestrator/orchestrator.py)                            │
│  - Workflow sekwencyjny: /plan → /implement               │
│  - Zarządzanie temp directories / sandboxami               │
│  - Logowanie akcji agenta                                  │
│  - Pomiar czasu: plan osobno, implementacja osobno         │
└──────────┬───────────────────────────────┬─────────────────┘
           │                               │
    ┌──────▼──────┐                  ┌─────▼───────┐
    │ TASK        │                  │ JUDGE       │
    │ GENERATOR   │                  │ (judge/)    │
    │             │                  │   - Plan    │
    │ (task-      │                  │   - Code    │
    │ generator/) │                  │   - Tools   │
    │             │                  │   - Time    │
    │ - Feature   │                  │   - Security│
    │ - Refactor  │                  │   - A11y    │
    │ - Debug     │                  └─────┬───────┘
    └──────┬──────┘                        │
           │                    ┌──────────▼──────────┐
           │                    │ METRICS ENGINE      │
           │                    │ (metrics/)          │
           │                    │  - Agregacja        │
           │                    │  - Normalizacja     │
           │                    │  - Równe wagi planu│
           │                    │  - Ranking modeli  │
           └────────┬───────────┤  - Score 0–100     │
                    │           └──────────┬──────────┘
                    │                      │
         ┌──────────▼──────────┐   ┌───────▼────────┐
         │ TEST REPOSITORIES   │   │ REPORTING      │
         │ (task-repos/)       │   │ (reporting/)   │
         │                     │   │  - Ranking     │
         │ repo-frontend-ts/   │   │  - Per-task    │
         │ repo-fullstack/     │   │  - OpenRouter  │
         └─────────────────────┘   └────────────────┘
```

### Decyzja 12: Wykorzystanie istniejących skilli AI_Instruction

Judge ma wykorzystywać istniejące skille AI_Instruction jako **kryteria oceny**, nie jako bezpośrednie wywołania:

| Wymiar oceny | Wykorzystywane skille AI_Instruction |
|---|---|
| Jakość planu | `architecture-designing/plan.example.md` (struktura), `task-analysing/research.example.md` (kompletność) |
| Jakość kodu backendu | `implementing-backend` (SOLID, clean architecture), `node-backend-guidelines` |
| Jakość kodu frontendu | `implementing-frontend` (kompozycja, design system), `react-component-design` |
| Bezpieczeństwo | `code-reviewing` + `validations.md` (V-01..V-18), `Docs/OWASP_TOP_30_PLUS.md` |
| Dostępność (frontend) | `ensuring-accessibility` (WCAG 2.1 AA, ARIA) |
| Jakość testów | `testing-ts-js` (unit/integration), `testing-e2e` |
| Jakość TS/JS | `typescript-best-practices`, `ts-project-structure`, `ts-styling-and-linting` |
| Jakość Python | `node-backend-guidelines` (adaptacja dla Python), `engineering-databases` |
| Jakość architektury | `modeling-domain` (DDD), `system-modularising` |

### Decyzja 13: Schema raportu

Raport główny ma mieć formę rankingu modeli. Każdy model otrzymuje oceny 0–100 za plan, implementację łącznie oraz użycie narzędzi i terminala. Szczegóły per task mają umożliwiać rozwinięcie wyniku i pokazanie wyników dla poszczególnych zadań.

```json
{
  "version": "2.0",
  "timestamp": "ISO8601",
  "models": [
    {
      "model": "openrouter/model-name",
      "judge_model": "openrouter/judge-model-name",
      "scores": {
        "plan": 85,
        "implementation": 78,
        "tools_and_terminal": 72
      },
      "tasks": [
        {
          "task_id": "uuid",
          "task_type": "feature|refactor|debug",
          "repo": "frontend-ts|fullstack",
          "scores": {
            "plan": 85,
            "implementation": 78,
            "tools_and_terminal": 72
          },
          "time": {
            "plan_seconds": 123,
            "implementation_seconds": 456
          },
          "details": {
            "plan": {
              "structure": 90,
              "completeness": 80,
              "adequacy": 85,
              "security": 80,
              "testing_strategy": 85
            },
            "implementation": {
              "solid": 75,
              "owasp_top_30_plus": 85,
              "aria": 70,
              "clean_architecture": 80,
              "test_quality": 82,
              "review_findings": 76,
              "objective_signals": {
                "tests": {"passed": 12, "failed": 0, "total": 12},
                "benchmarks": {"passed": 8, "failed": 0, "total": 8},
                "evals_runner": "local_fallback|openai_evals|disabled",
                "static_analysis": {"errors": 0, "warnings": 2}
              },
              "review_rubric": {
                "score": 78,
                "classification": "quality_signal",
                "categories": {
                  "requirements": {"score": 85, "met": 4, "missed": 1, "details": ["Pokrywa zakres zadania", "Brak pełnej obsługi edge case"]},
                  "security": {"score": 90, "met": 5, "missed": 0, "details": ["OWASP", "walidacja wejść", "brak sekretów"]},
                  "code_quality": {"score": 80, "met": 4, "missed": 1, "details": ["czytelny kod", "drobna duplikacja"]},
                  "architecture": {"score": 75, "met": 3, "missed": 1, "details": ["pasuje do modułu", "brak komentarza API"]},
                  "tests": {"score": 70, "met": 2, "missed": 1, "details": ["dodano test jednostkowy", "brak testu integracyjnego"]},
                  "regression": {"score": 85, "met": 4, "missed": 0, "details": ["build OK", "lint OK", "typecheck OK"]},
                  "documentation": {"score": 60, "met": 1, "missed": 1, "details": ["README wymaga aktualizacji"]}
                },
                "findings": [
                  {"type": "positive", "category": "security", "description": "Dodano walidację wejść"},
                  {"type": "gap", "category": "tests", "description": "Brak testu integracyjnego"}
                ]
              }
            },
            "tools_and_terminal": {
              "terminal_correctness": 80,
              "search_efficiency": 65,
              "ai_tools_usage": 60
            },
            "bugs": {
              "total": 3,
              "critical": 0,
              "major": 1,
              "minor": 2,
              "details": [
                {"line": 42, "severity": "major", "description": "Brak error handling w async funkcji"},
                {"line": 87, "severity": "minor", "description": "Brak aria-label na button"},
                {"line": 103, "severity": "minor", "description": "Inconsistent formatting"}
              ]
            }
          }
        }
      ]
    }
  ]
}
```

### Decyzja 14: Kryteria oceny planu

Plan ma być oceniany w skali 0–100 według pięciu kryteriów o równych wagach:

| Kryterium | Waga domyślna | Zakres oceny |
|---|---:|---|
| Struktura zgodna z `plan.example.md` | 20% | Obecność wymaganych sekcji i zgodność z szablonem |
| Kompletność względem `research.md` | 20% | Czy plan obejmuje wymagania, ograniczenia, kryteria akceptacji i zależności |
| Adekwatność podejścia | 20% | Czy rozwiązanie jest proporcjonalne do zadania i nie wprowadza nieuzasadnionej złożoności |
| Bezpieczeństwo | 20% | Czy uwzględniono OWASP TOP 30+, walidację, auth/rate limit, sekrety i surface attack |
| Strategia testowania | 20% | Czy plan definiuje testy jednostkowe, integracyjne, E2E, lint/statyczną analizę i quality gates |

Każde kryterium jest oceniane osobno 0–100, a wynik końcowy planu jest średnią arytmetyczną pięciu kryteriów.

### Decyzja 15: Kryteria oceny użycia narzędzi i terminala

Użycie narzędzi i terminala ma być oceniane w skali 0–100 według trzech kryteriów:

| Kryterium | Zakres oceny |
|---|---|
| Poprawność komend terminala | Czy komendy były poprawne, bezpieczne i adekwatne do zadania |
| Efektywność wyszukiwania | Czy agent używał wyszukiwania celowo, bez nadmiernego ręcznego przeglądania i z właściwym doborem narzędzi |
| Adekwatne użycie narzędzi AI | Czy agent używał `context7`/`web/fetch` tam, gdzie wymagana była aktualna dokumentacja lub analiza zewnętrznych rozwiązań |

Każde kryterium jest oceniane osobno 0–100, a wynik końcowy narzędzi i terminala jest średnią arytmetyczną trzech kryteriów.

### Decyzja 16: Pomiar czasu

Czas ma być mierzony osobno dla:

- przygotowania planu, od startu `/plan` do zapisania planu,
- implementacji, od startu `/implement` do ukończenia zadania.

Czas nie musi być osobno raportowany dla `first_test_run` ani `first_green`, chyba że w przyszłości pojawi się taka potrzeba.

### Decyzja 17: Integracja z AI_Instruction i OpenRouter

AI_Tester v2 ma działać jako aplikacja korzystająca z repozytorium `AI_Instruction` lub jego clona. Ma wykorzystywać istniejące prompty, skille i agentów, w szczególności:

- `/plan` do przygotowania planu,
- `/implement` do realizacji zadania,
- `/review` do jakościowej rubryki oceny kodu, refactorów i braków,
- skille `code-reviewing`, `ensuring-code-quality`, `ensuring-accessibility`, `implementing-frontend`, `implementing-backend`, `testing-ts-js` i `testing-e2e` jako źródła kryteriów oceny.

Modele testowane mają pochodzić z **OpenRouter**. Przy uruchomieniu musi być wskazany model podlegający testowi. Konfiguracja musi umożliwiać ustawienie modelu sędziego.

### Decyzja 19: Integracja narzędziowa przez VS Code Extension Host Adapter

AI_Tester v2 ma udostępniać testowanemu modelowi narzędzia przez kontrolowany **VS Code Extension Host Adapter**, a nie przez bezpośredni, nielogowany dostęp do środowiska.

Docelowy adapter:

- tworzy lub używa uczestnika czatu przez `vscode.chat.createChatParticipant`,
- rejestruje narzędzia modelu przez `vscode.lm.registerTool`,
- tworzy dedykowany terminal taska przez `vscode.window.createTerminal`,
- preferuje `shellIntegration.executeCommand`, gdy dostępne, aby uzyskać `exitCode`,
- stosuje fallback do `sendText`, oznaczając brak pewnego kodu zakończenia jako `terminal_exit_code: unknown`,
- zapisuje wszystkie akcje do `ToolLogger` w kategoriach: `terminal`, `file_operation`, `search`, `ai_tool`.

Minimalny zestaw narzędzi:

| Narzędzie | Zakres |
|---|---|
| `run_terminal_command` | Wykonanie komendy tylko w `workspacePath` taska |
| `read_file` | Odczyt pliku tylko w izolowanym workspace |
| `write_file` | Zapis pliku tylko w izolowanym workspace |
| `search_files` | Wyszukiwanie ograniczone do workspace taska |
| `list_directory` | Lista katalogu tylko w workspace taska |
| `fetch_documentation` | Pobranie dokumentacji zewnętrznej, logowane jako `ai_tool` |
| `context7` | Pobranie dokumentacji biblioteki, logowane jako `ai_tool` |

Polityka uprawnień:

- pliki, wyszukiwanie i terminal są ograniczone do `workspacePath`,
- komendy wychodzące poza workspace taska są blokowane albo wymagają jawnej zgody,
- `delete_file` powinien być domyślnie wyłączony albo wymagać potwierdzenia,
- pełne outputy terminala są logowane tylko przy błędzie, chyba że włączono tryb verbose,
- fallback `sendText` nie daje pewnego `exitCode`, więc musi być oznaczony w raporcie.

### Decyzja 20: Izolacja i sekwencyjność

Taski mają być uruchamiane sekwencyjnie:

1. przygotowanie planu przez `/plan`,
2. realizacja zadania przez `/implement`.

Preferowane są izolowane katalogi tymczasowe (`temp directories`). Docker sandboxy mogą zostać użyte, jeśli w planie pojawi się uzasadnienie techniczne, np. konieczność uruchomienia pełnego środowiska z bazą danych lub usługą zewnętrzną.

### Decyzja 20: Źródła tasków i rola promptu `/plan`

AI_Tester v2 powinien wykorzystywać realne repozytoria jako bazę kodu do testów agentów. Dla `Investment-Assistant`, `AgentDeck` i `AutoResearch_SQLServer` źródłem tasków powinny być otwarte Issues na GitHubie. Dla `TravianBot` taski powinny być generowane lokalnie, ponieważ repo nie ma obecnie Issues do wykorzystania.

Prompt `/plan` ma pełnić rolę aktywnego analityka zadania: powinien samodzielnie zbadać kontekst repo, zidentyfikować zakres, kryteria akceptacji, ograniczenia, polecenia walidacyjne oraz potrzebne mocki lub fixtures. System nie powinien przygotowywać tych elementów przed uruchomieniem `/plan`, ponieważ wtedy ocena jakości planu mierzyłaby jakość przygotowania zadania przez system, a nie zdolność modelu do analizy i planowania.

Jeśli Issue jest zbyt mało opisowe, można uzupełnić opis o niezbędne minimum, ale nie należy tworzyć pełnej specyfikacji technicznej. Głównym celem jest dobieranie zadań o wystarczającej złożoności i maksymalnie obiektywnych testach.

### Decyzja 21: Obiektywność testów i rubryka `/review`

Testy powinny być jak najbardziej obiektywne. System powinien wykorzystywać istniejące testy, linty, typechecki, buildy i ukryte testy tam, gdzie mają sens. Wyniki tych mechanizmów powinny być raportowane jako **twarde sygnały walidacyjne**, osobno od jakościowej rubryki `/review`.

Prompt `/review` nie powinien być traktowany jako deterministyczna ani w pełni obiektywna walidacja. Jego rola powinna polegać na ustrukturyzowanej ocenie jakościowej: wskazaniu, które aspekty zostały zrealizowane poprawnie, które zasady bezpieczeństwa i jakości kodu zostały spełnione oraz jakie braki nadal pozostają.

Rekomendowany model rubryki `/review`:

- każda kategoria ma przypisaną maksymalną liczbę punktów,
- za spełnienie kryterium przyznawane są punkty dodatnie,
- za brak kryterium odejmowane są punkty lub kategoria nie otrzymuje punktów,
- wynik `/review` jest raportowany jako sygnał jakościowy/semi-obiektywny, a nie jako twardy wynik testu,
- raport zawiera listę punktów spełnionych, braków i rekomendowanych poprawek.

Przykładowe kategorie rubryki:

| Kategoria | Przykładowe kryteria |
|---|---|
| Realizacja wymagań | Czy implementacja pokrywa zakres zadania i kryteria akceptacji |
| Bezpieczeństwo | Czy uwzględniono OWASP TOP 30+, walidację wejść, autoryzację, sekrety i rate limit |
| Jakość kodu | Czy kod jest czytelny, zgodny z SOLID, bez duplikacji i nadmiernej złożoności |
| Architektura | Czy zmiana pasuje do istniejącej struktury repo i nie narusza granic modułów |
| Testy | Czy dodano lub uruchomiono adekwatne testy jednostkowe, integracyjne albo E2E |
| Brak regresji | Czy istniejące testy, build, lint i typecheck przechodzą |
| Dokumentacja | Czy zaktualizowano dokumentację, README, changelog lub komentarze tam, gdzie to konieczne |

Dzięki temu `/review` nadal wnosi wartość do rankingu, ale nie miesza się z twardymi sygnałami walidacyjnymi. Ranking może zawierać osobne pola: `objective_signals` dla testów, benchmarków, Evals i statycznej analizy oraz `review_rubric` dla jakościowej oceny `/review`.

#### Refactor

Refactor ma być oceniany przez porównanie jakości kodu przed i po zmianach. Ocena może być wykonana przez prompt `/review` z AI_Instruction oraz skrypty statycznej analizy.

Kryteria jakości refactoru:

- czy kod stał się prostszy i bardziej czytelny,
- czy poprawiono przestrzeganie SOLID,
- czy zmniejszono złożoność i powtarzalność,
- czy nie wprowadzono nowych błędów,
- czy testy nadal przechodzą,
- czy zmiana jest zgodna z OWASP TOP 30+ i innymi regułami `/review`.

#### Debug

Debug ma być oceniany przez to, czy model znalazł i usunął przyczynę błędu, a nie tylko objawy.

Kryteria jakości debugu:

- czy model zdiagnozował prawdziwą przyczynę,
- czy poprawka usuwa problem źródłowy,
- czy testy po poprawce przechodzą,
- czy nie wprowadzono nowych błędów,
- czy rozwiązanie jest minimalne i nie narusza istniejącej architektury,
- czy kod po poprawce spełnia kryteria SOLID, OWASP TOP 30+ i jakości testów.

### Decyzja 22: Modularizacja

**modularization: use-existing-domain**

Istniejąca struktura AI_Instruction (agents, skills, prompts, compliance) stanowi solidną bazę dla AI_Tester v2. Nowy subsystem powinien być dodany jako **oddzielny katalog `ai-tester-v2/`** w workspace, wykorzystujący istniejące skille AI_Instruction jako źródła kryteriów oceny. Nie ma potrzeby tworzenia nowego bounded context — AI_Tester v2 jest **subsystemem evaluacyjnym** AI_Instruction, nie osobnym produktem.

**Uzasadnienie:**
- AI_Tester v2 nie definiuje nowych granic domenowych — operuje na istniejących skillach i promptach
- Nie ma zależności cyklicznych z istniejącym codebase
- Nowy subsystem jest izolowany (nie modyfikuje istniejących skilli, tylko je wykorzystuje)
- Istniejąca struktura `skills/`, `prompts/`, `compliance/` dostarcza wszystkich potrzebnych kryteriów

## Plan implementacji (wysokopoziomowy)

> **Uwaga:** Szczegółowy plan implementacji zostanie przygotowany przez architekta po zakończeniu researchu. Poniżej tylko wysokopoziomowy podział na fazy zgodny z potwierdzonymi ustaleniami.

### Faza 1: Infrastruktura bazowa
- Utworzenie struktury katalogów `ai-tester-v2/`
- Rozbudowa `harness.py` do sekwencyjnego orchestratora `/plan → /implement`
- Utworzenie izolowanych katalogów tymczasowych dla tasków
- Integracja z promptami /plan i /implement
- Konfiguracja modelu testowanego z OpenRouter oraz modelu sędziego
- Przygotowanie stuba VS Code Adapter i kontraktu narzędzi do przyszłej integracji

### Faza 2: Task Generator
- Generator tasków feature (TS/JS/React + Python/React/SQLite)
- Generator tasków refactor
- Generator tasków debug z 1–2 ukrytymi błędami
- Pobieranie tasków z GitHub Issues dla repozytoriów `Investment-Assistant`, `AgentDeck`, `AutoResearch_SQLServer`
- Generowanie lokalnych tasków dla `TravianBot`
- Klasyfikacja złożoności i obiektywności testów
- Benchmarki dla każdego typu taska

### Faza 3: Judge Agent
- Implementacja oceny jakości planu według pięciu równoważnych kryteriów
- Implementacja oceny jakości implementacji przez `/review` jako jakościową rubrykę, skrypty statycznej analizy oraz pomocnicze sygnały z testów/benchmarków/Evals
- Implementacja oceny użycia narzędzi i terminala według trzech kryteriów
- Implementacja pomiaru czasu planu i implementacji
- Integracja z istniejącymi skillami AI_Instruction
- Walidacja, czy plan samodzielnie zebrał kontekst repo, kryteria akceptacji, ograniczenia, polecenia walidacyjne, mocki lub fixtures

### Faza 4: Metrics & Reporting
- Silnik metryk i agregacji
- Ranking modeli 0–100 dla planu, implementacji i narzędzi
- Szczegóły per task umożliwiające rozwinięcie wyniku
- Konfiguracja modelu testowanego i modelu sędziego
- Integracja pomocniczych sygnałów z testów, benchmarków i Evals
- Rozróżnienie twardych sygnałów walidacyjnych od jakościowej rubryki `/review`

### Faza 5: Testy i walidacja
- Testy E2E całego workflow
- Benchmarki na przykładowych taskach
- Walidacja spójności ocen

### Faza 6: Integracja VS Code API
- Implementacja VS Code Extension Host Adapter
- Rejestracja narzędzi LM przez `vscode.lm.registerTool`
- Dedykowany terminal taska przez `vscode.window.createTerminal`
- Obsługa `shellIntegration.executeCommand` i fallback `sendText`
- Polityka uprawnień ograniczająca narzędzia do `workspacePath`
- Integracja narzędzi z `ToolLogger`

## Powiązane pliki do utworzenia

| Plik | Przeznaczenie |
|---|---|
| `ai-tester-v2.solution-research.md` | Szczegółowa analiza architektury orchestracji |
| `ai-tester-v2.plan.md` | Szczegółowy plan implementacji po zakończeniu researchu |
| `ai-tester-v2/schemas/ranking.schema.json` | Schemat rankingu modeli 0–100 |
| `ai-tester-v2/schemas/task-result.schema.json` | Schemat szczegółów per task |
| `ai-tester-v2/task-generator/github-issue-fetcher.py` | Pobieranie i klasyfikacja Issues z GitHub |
| `ai-tester-v2/task-generator/travianbot-task-generator.py` | Generowanie lokalnych tasków dla TravianBot |
| `ai-tester-v2/task-generator/task-complexity-scorer.py` | Ocena złożoności tasków i obiektywności testów |
| `ai-tester-v2/scorers/` | Obiektywne skrypty scoringowe: testy, benchmarki, statyczna analiza, Evals |
| `ai-tester-v2/agents/` | Adaptery OpenRouter, sędzia, opcjonalny runner LangChain oraz adapter narzędzi VS Code |
| `ai-tester-v2/agents/vscode_adapter/` | Kontrolowany adapter VS Code API: chat participant, zarejestrowane narzędzia LM, terminal, uprawnienia i logowanie akcji |
| `ai-tester-v2/task-generator/` | Generator zadań |
| `ai-tester-v2/judge/` | Agent sędzi |
| `ai-tester-v2/orchestrator/` | Orchestrator workflow |
| `ai-tester-v2/metrics/` | Silnik metryk |
| `ai-tester-v2/reporting/` | Generowanie raportów |
| `ai-tester-v2/task-repos/repo-frontend-ts/` | Repo TS/JS/React |
| `ai-tester-v2/task-repos/repo-fullstack/` | Repo Python/React/SQLite |

## Modularization Decision

**Decyzja:** `use-existing-domain`

**Uzasadnienie:** AI_Tester v2 jest subsystemem evaluacyjnym AI_Instruction. Nie definiuje nowych granic domenowych, nie wprowadza zależności cyklicznych, i wykorzystuje istniejące skille jako źródła kryteriów. Nowy katalog `ai-tester-v2/` w workspace jest wystarczający.

---

*Research zaktualizowano na podstawie odpowiedzi użytkownika z 2026-06-16. Szczegółowy plan implementacji powinien zostać przygotowany przez prompt `/plan` po zakończeniu tego etapu.*
