# AI_Tester v2 — Pogłębiona Analiza Architektury Systemu Orchestracji

## Szczegóły zadania

| Pole | Wartość |
|---|---|
| Tytuł | AI_Tester v2 — Pogłębiona Analiza Architektury Systemu Orchestracji |
| Opis | Głęboka analiza architektury systemu orchestracji koordynującego multi-phase workflow: `/plan` → `/implement` → `/review` → scoring. System ma zarządzać izolowanymi taskami, mierzyć metryki wykonania, integrować z AI_Instruction i OpenRouter oraz generować raporty rankingowe. |
| Priorytet | High |
| Złożoność analizy rozwiązań | L |
| Typ analizy | Solution Research — Architektura Orchestracji |

## Wpływ biznesowy

Architektura orchestracji jest **kluczowym filarem AI_Tester v2** — decyduje o:

- Możliwości sekwencyjnego uruchamiania agentów na izolowanych taskach
- Jakości i wiarygodności zebranych metryk (czas, użycie narzędzi, sygnały testowe)
- Skalowalności systemu do wielu modeli i repozytoriów
- Możliwości integracji z istniejącymi skillami AI_Instruction
- Bezpieczeństwa izolacji tasków (agent nie może modyfikować repozytorium źródłowego)

## Zebrane informacje

### Baza kodu — obecny stan PoC

#### Istniejące komponenty AI_Tester

| Komponent | Ścieżka | Status | Ocena |
|---|---|---|---|
| `harness.py` | `e:\AI_WORKSPACE\Moje projekty\AI_Tester\harness.py` | Do modyfikacji | Tylko build + run Docker; brak workflow multi-phase, brak pomiaru czasu, brak izolacji tasków |
| `scoring.py` | `e:\AI_WORKSPACE\Moje projekty\AI_Tester\scoring.py` | Do modyfikacji | Tylko pytest pass rate + naiwna heurystyka; wymaga rozbudowy o agregację wielowymiarową |
| `evals_integration.py` | `e:\AI_WORKSPACE\Moje projekty\AI_Tester\evals_integration.py` | Do modyfikacji | Lokalny runner benchmarków; może być źródłem obiektywnych sygnałów |
| `langchain_agent.py` | `e:\AI_WORKSPACE\Moje projekty\AI_Tester\langchain_agent.py` | Do usunięcia/rozbudowy | Placeholder; może zostać zastąpiony adapterem OpenRouter |
| `Dockerfile` | `e:\AI_WORKSPACE\Moje projekty\AI_Tester\Dockerfile` | Do modyfikacji | Python 3.11 + pytest; wymaga rozszerzenia o ESLint, ruff, pylint, tsc |
| `run_poc.ps1` | `e:\AI_WORKSPACE\Moje projekty\AI_Tester\run_poc.ps1` | Do modyfikacji | Rozszerzyć o sekwencyjny workflow i konfigurację modeli |
| `ai_tester_report.json` | `e:\AI_WORKSPACE\Moje projekty\AI_Tester\ai_tester_report.json` | Do rozszerzenia | Rozszerzyć schema do rankingu modeli, szczegółów per task |

#### Istniejące zasoby AI_Instruction do wykorzystania

| Zasób | Ścieżka | Rola w orchestracji |
|---|---|---|
| Prompt `/plan` | `.github/prompts/plan.prompt.md` | Uruchamianie planowania przez agenta; zbiera kontekst repo, zakres, kryteria akceptacji |
| Prompt `/implement` | `.github/prompts/implement.prompt.md` | Uruchamianie implementacji przez agenta |
| Prompt `/review` | `.github/prompts/review.prompt.md` | Uruchamianie code review przez Judge |
| Szablon planu | `.github/skills/architecture-designing/plan.example.md` | Walidacja struktury planu |
| Szablon research | `.github/skills/task-analysing/research.example.md` | Walidacja struktury research |
| Reguły V-01..V-18 | `.github/skills/code-reviewing/references/validations.md` | Kryteria walidacyjne dla Judge |
| OWASP TOP 30+ | `Docs/OWASP_TOP_30_PLUS.md` | Kryteria bezpieczeństwa |

### Analiza rozwiązań

#### Pytania badawcze

1. **Jak koordynować sekwencyjny workflow `/plan` → `/implement` → `/review` → scoring?**
2. **Jak zapewnić izolację tasków (temp directories vs Docker sandbox)?**
3. **Jak integrować się z AI_Instruction — jako osobny system, rozszerzenie workspace, czy hybryda?**
4. **Jak zarządzać wieloma modelami AI (OpenRouter) i modelem sędziego?**
5. **Jak mierzyć metryki wykonania: czas, użycie narzędzi, sygnały testowe?**
6. **Jak generować raporty rankingowe z detalami per task?**
7. **Jak skalować system do wielu repozytoriów i typów tasków?**

#### Złożoność: L (Złożone)

Zadanie wymaga wyboru architektury dla nowego subsystemu, który nie istnieje w obecnym codebase. Istniejące skille AI_Instruction dostarczają kryteriów oceny, ale nie gotowego rozwiązania orchestracji.

## Analiza architektury orchestracji

### Decyzja 1: Model wykonania orchestratora

#### Opcja A: Orchestrator jako osobny proces Python

Orchestrator jest aplikacją Python uruchamianą lokalnie, która:

- Zarządza cyklem życia tasków
- Wywołuje `/plan`, `/implement`, `/review` przez API Copilot lub bezpośrednie wywołania promptów
- Mierzy metryki wykonania
- Agreguje wyniki

**Korzyści:**
- Pełna kontrola nad lifecycle tasków
- Łatwe testowanie i debugowanie
- Możliwość integracji z istniejącym `harness.py` i `scoring.py`
- Niska złożoność operacyjna

**Wady:**
- Wymaga dostępu do API Copilot lub interakcji z VS Code
- Ograniczona portability (wymaga VS Code z Copilot)

#### Opcja B: Orchestrator jako skrypt PowerShell

Orchestrator jest skryptem PowerShell uruchamianym na Windows, który:

- Wywołuje `code` CLI do uruchamiania promptów
- Zarządza temp directories i izolacją
- Integruje się z istniejącymi skryptami AI_Instruction

**Korzyści:**
- Naturalna integracja z istniejącym ekosystemem AI_Instruction (skrypty PowerShell)
- Brak zależności od Python
- Łatwe uruchamianie w CI/CD na Windows

**Wady:**
- Ograniczona portability (tylko Windows)
- Trudniejsza obsługa asynchroniczna i parallelizacja

#### Opcja C: Hybryda — orchestrator Python + skrypt uruchamiający PowerShell

Orchestrator jest aplikacją Python, ale do wywoływania promptów używa skryptów PowerShell.

**Korzyści:**
- Łączy zalety obu podejść
- Python zarządza logiką orchestracji, PowerShell wywołuje prompty

**Wady:**
- Podwójna złożoność
- Wymaga obu runtime'ów

#### Rekomendacja: Opcja A (Orchestrator jako osobny proces Python)

**Uzasadnienie:**
- AI_Tester v2 jest systemem evaluacyjnym, który wymaga zaawansowanej logiki zarządzania taskami
- Python jest już używany w PoC (`harness.py`, `scoring.py`, `evals_integration.py`)
- Łatwiejsza integracja z OpenRouter API, benchmarkami i statyczną analizą
- Możliwość uruchamiania w Docker (jak w obecnym PoC)
- Istniejące skrypty PowerShell mogą zostać wykorzystane jako narzędzia wywoływane przez orchestrator

### Decyzja 2: Izolacja tasków

#### Opcja A: Temp directories (rekomendowane)

Każdy task jest uruchamiany w izolowanym katalogu tymczasowym:

```
temp/
  task-<uuid>/
    .git/
    src/
    tests/
    benchmarks/
    artifacts/
```

**Korzyści:**
- Prosta implementacja
- Szybkie tworzenie i usuwanie
- Pełna kontrola nad zawartością
- Brak zależności od Docker

**Wady:**
- Agent może modyfikować system plików (ryzyko bezpieczeństwa)
- Brak izolacji procesów

#### Opcja B: Docker sandbox

Każdy task jest uruchamiany w izolowanym kontenerze Docker:

```
docker run --rm -v <task-dir>:/app ai_tester_runner
```

**Korzyści:**
- Silna izolacja procesów
- Możliwość uruchamiania pełnego środowiska (baza danych, serwery)
- Reproducible environment

**Wady:**
- Wolniejsze tworzenie kontenerów
- Wymaga Docker w hostcie
- Większe zużycie zasobów

#### Opcja C: Hybryda

Domyślnie temp directories, Docker tylko gdy plan uzasadnia (np. potrzeba bazy danych).

#### Rekomendacja: Opcja C (Hybryda)

**Uzasadnienie:**
- Większość tasków (feature, refactor, debug) nie wymaga pełnego sandboxu
- Docker może zostać użyty jako fallback, gdy plan `/plan` uzasadnia potrzebę izolacji
- Spójne z decyzją z `ai-tester-v2.research.md`

### Decyzja 3: Integracja z AI_Instruction

#### Opcja A: Wywoływanie promptów przez API Copilot

Orchestrator wywołuje `/plan`, `/implement`, `/review` przez API Copilot (jeśli dostępne) lub przez symulację interakcji z VS Code.

**Korzyści:**
- Pełne wykorzystanie istniejących skilli i promptów
- Najbardziej spójne z workflow AI_Instruction

**Wady:**
- Wymaga dostępu do API Copilot
- Możliwe ograniczenia licencyjne

#### Opcja B: Wywoływanie promptów przez CLI

Orchestrator wywołuje `code` CLI z odpowiednimi argumentami do uruchamiania promptów.

**Korzyści:**
- Nie wymaga API Copilot
- Możliwość uruchamiania w CI/CD

**Wady:**
- Wymaga VS Code z Copilot zainstalowanych
- Trudniejsza obsługa outputu

#### Opcja C: Bezpośrednie wykorzystanie promptów jako szablonów

Orchestrator wykorzystuje treści promptów `/plan`, `/implement`, `/review` jako szablony, wstrzykując kontekst taska i generując bezpośrednie zapytania do OpenRouter.

**Korzyści:**
- Pełna kontrola nad kontekstem i formatem
- Nie wymaga VS Code ani Copilot
- Możliwość uruchamiania w dowolnym środowisku

**Wady:**
- Wymaga duplikacji logiki promptów
- Ryzyko rozbieżności z istniejącymi promptami

#### Rekomendacja: Opcja C (Bezpośrednie wykorzystanie promptów jako szablonów)

**Uzasadnienie:**
- AI_Tester v2 ma być niezależnym systemem evaluacyjnym
- Możliwość uruchamiania bez VS Code/Copilot zwiększa portability
- Prompty z AI_Instruction są szablonaми — można je wstrzykiwać dynamicznie
- Integracja z OpenRouter jest kluczowa dla benchmarkingu wielu modeli

### Decyzja 4: Zarządzanie modelami AI

#### Architektura zarządzania modelami

```
┌─────────────────────────────────────────────────────┐
│                  ORCHESTRATOR                        │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │
│  │ Model       │  │ Model       │  │ Judge      │  │
│  │ Config      │  │ Config      │  │ Config     │  │
│  │ (tested)    │  │ (optional)  │  │ (judge)    │  │
│  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘  │
│         │                │                │         │
│  ┌──────▼────────────────▼────────────────▼──────┐  │
│  │           OPENROUTER API ADAPTER              │  │
│  │  - Authentication                             │  │
│  │  - Rate limiting                              │  │
│  │  - Response parsing                           │  │
│  │  - Error handling                             │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Kluczowe elementy:**

1. **Konfiguracja modelu testowanego** — określana przy uruchomieniu orchestratora
2. **Konfiguracja modelu sędziego** — określona w konfiguracji lub przy uruchomieniu
3. **Adapter OpenRouter** — jednolity interfejs do wywoływania modeli
4. **Rate limiting** — ochrona przed przekroczeniem limitów API
5. **Retry z backoff** — obsługa tymczasowych błędów API

### Decyzja 5: Pomiar metryk wykonania

#### Metryki czasu

| Metryka | Zakres | Sposób pomiaru |
|---|---|---|
| `plan_seconds` | Start `/plan` → zapis planu | `time.perf_counter()` w orchestratorze |
| `implement_seconds` | Start `/implement` → ukończenie | `time.perf_counter()` w orchestratorze |
| `review_seconds` | Start `/review` → zapis raportu | `time.perf_counter()` w orchestratorze |

#### Metryki użycia narzędzi

| Metryka | Sposób pomiaru |
|---|---|
| `terminal_correctness` | Analiza logów komend terminala przez Judge |
| `search_efficiency` | Liczba wywołań search vs liczba plików przeczytanych |
| `ai_tools_usage` | Analiza logów użycia `context7`, `web/fetch` |

#### Twarde sygnały walidacyjne

| Sygnał | Źródło |
|---|---|
| `tests.passed/failed/total` | pytest / runner benchmarków |
| `benchmarks.passed/failed/total` | evals_integration.py |
| `static_analysis.errors/warnings` | ESLint, ruff, pylint |
| `lint.passed/failed` | Lintery repozytorium |
| `build.success/failure` | Build repozytorium |

### Decyzja 6: Struktura katalogów orchestratora

```
ai-tester-v2/
├── orchestrator/
│   ├── __init__.py
│   ├── orchestrator.py          # Główna klasa Orchestrator
│   ├── task_manager.py          # Zarządzanie cyklem życia tasków
│   ├── time_tracker.py          # Pomiar czasu
│   ├── tool_logger.py           # Logowanie użycia narzędzi
│   └── metrics_engine.py        # Agregacja metryk
├── agents/
│   ├── __init__.py
│   ├── openrouter_adapter.py    # Adapter OpenRouter
│   ├── judge_agent.py           # Agent sędzi
│   └── langchain_runner.py      # Opcjonalny runner LangChain
├── task-generator/
│   ├── __init__.py
│   ├── github_issue_fetcher.py  # Pobieranie Issues z GitHub
│   ├── travianbot_generator.py  # Generowanie tasków dla TravianBot
│   ├── task_complexity_scorer.py # Ocena złożoności tasków
│   └── task_templates/          # Szablony tasków
│       ├── feature/
│       ├── refactor/
│       └── debug/
├── scorers/
│   ├── __init__.py
│   ├── plan_scorer.py           # Ocena planu
│   ├── implementation_scorer.py # Ocena implementacji
│   ├── tools_scorer.py          # Ocena użycia narzędzi
│   ├── review_rubric_scorer.py  # Ocena rubryki /review
│   └── objective_signals.py     # Agregacja sygnałów twardych
├── reporting/
│   ├── __init__.py
│   ├── ranking_generator.py     # Generowanie rankingu
│   ├── task_reporter.py         # Generowanie raportów per task
│   └── schema/
│       ├── ranking.schema.json
│       └── task-result.schema.json
├── task-repos/
│   ├── repo-frontend-ts/        # Izolowane repo TS/JS/React
│   └── repo-fullstack/          # Izolowane repo Python/React/SQLite
├── benchmarks/
│   ├── feature/
│   ├── refactor/
│   └── debug/
├── config/
│   ├── models.yaml              # Konfiguracja modeli
│   └── tasks.yaml               # Konfiguracja tasków
└── schemas/
    ├── ranking.schema.json
    └── task-result.schema.json
```

### Decyzja 7: Workflow sekwencyjny orchestratora

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR WORKFLOW                        │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐ │
│  │ TASK     │    │ /PLAN    │    │ /IMPLEMENT│    │ /REVIEW │ │
│  │ GENERATOR│───▶│ PHASE    │───▶│ PHASE     │───▶│ PHASE   │ │
│  │          │    │          │    │          │    │         │ │
│  │ - Fetch  │    │ - Start  │    │ - Start  │    │ - Start │ │
│  │ - Class. │    │   timer  │    │   timer  │    │   timer │ │
│  │ - Select │    │ - Gather │    │ - Code   │    │ - Code  │ │
│  │ - Create │    │   context│    │   gen.   │    │   review│ │
│  │ - Isolate│    │ - Plan   │    │ - Tests  │    │ - Rubric│ │
│  │          │    │ - Save   │    │   run    │    │ - Score │ │
│  │          │    │   plan   │    │ - Timer  │    │ - Timer │ │
│  │          │    │ - Timer  │    │   stop   │    │ - Save  │ │
│  │          │    │   stop   │    │          │    │         │ │
│  └──────────┘    └──────────┘    └──────────┘    └────┬──┘ │
│                                                         │    │
│                                                         ▼    │
│                                              ┌──────────────────┐ │
│                                              │ SCORING &        │ │
│                                              │ REPORTING        │ │
│                                              │                  │ │
│                                              │ - Aggregate      │ │
│                                              │ - Rank models    │ │
│                                              │ - Generate       │ │
│                                              │   reports        │ │
│                                              └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Decyzja 8: Interfejs API orchestratora

```python
class Orchestrator:
    """Główna klasa koordynująca workflow AI_Tester v2."""

    def __init__(self, config: Config):
        self.config = config
        self.task_manager = TaskManager()
        self.time_tracker = TimeTracker()
        self.tool_logger = ToolLogger()
        self.openrouter = OpenRouterAdapter(config.openrouter_api_key)
        self.scorers = ScorerRegistry()
        self.reporter = Reporter()

    async def run_task(self, task: Task) -> TaskResult:
        """Uruchom pełny workflow dla jednego taska."""
        # 1. Izolacja
        workspace = await self.task_manager.create_isolated_workspace(task)

        # 2. Faza /plan
        plan_result = await self.run_plan_phase(task, workspace)

        # 3. Faza /implement
        implement_result = await self.run_implement_phase(task, workspace, plan_result)

        # 4. Faza /review
        review_result = await self.run_review_phase(task, workspace, implement_result)

        # 5. Scoring
        score = await self.scorers.aggregate(
            plan=plan_result,
            implementation=implement_result,
            review=review_result,
            objective_signals=self.collect_objective_signals(workspace)
        )

        # 6. Cleanup
        await self.task_manager.cleanup(workspace)

        return TaskResult(task=task, score=score, plan=plan_result, implementation=implement_result, review=review_result)

    async def run_benchmark(self, tasks: List[Task], model: str, judge_model: str) -> BenchmarkResult:
        """Uruchom benchmark dla wielu tasków i jednego modelu."""
        results = []
        for task in tasks:
            result = await self.run_task(task)
            result.model = model
            result.judge_model = judge_model
            results.append(result)

        ranking = await self.reporter.generate_ranking(results)
        return BenchmarkResult(model=model, judge_model=judge_model, tasks=results, ranking=ranking)
```

### Decyzja 9: Integracja z promptami AI_Instruction

#### Mechanizm wstrzykiwania kontekstu

Orchestrator wykorzystuje treści promptów `/plan`, `/implement`, `/review` jako szablony, wstrzykując dynamiczny kontekst:

```python
PLAN_TEMPLATE = """
{prompt_content_from_ai_instruction}

## Kontekst taska
- Repozytorium: {repo_url}
- Zakres: {task_scope}
- Kryteria akceptacji: {acceptance_criteria}
- Ograniczenia: {constraints}
"""

IMPLEMENT_TEMPLATE = """
{prompt_content_from_ai_instruction}

## Plan do realizacji
{plan_content}

## Kontekst taska
- Repozytorium: {repo_url}
- Zakres: {task_scope}
"""

REVIEW_TEMPLATE = """
{prompt_content_from_ai_instruction}

## Implementacja do review
{implementation_content}

## Plan do weryfikacji
{plan_content}

## Rubryka oceny
{review_rubric_template}
"""
```

#### Pobieranie promptów z AI_Instruction

```python
class PromptLoader:
    """Ładuje prompty z AI_Instruction jako szablony."""

    def __init__(self, ai_instruction_path: Path):
        self.plan_prompt = (ai_instruction_path / ".github/prompts/plan.prompt.md").read_text()
        self.implement_prompt = (ai_instruction_path / ".github/prompts/implement.prompt.md").read_text()
        self.review_prompt = (ai_instruction_path / ".github/prompts/review.prompt.md").read_text()

    def load_skill_criteria(self, skill_name: str) -> str:
        """Ładuje kryteria z skilla AI_Instruction."""
        skill_path = self.ai_instruction_path / ".github/skills" / skill_name / "SKILL.md"
        return skill_path.read_text()
```

### Decyzja 10: Schema raportu rankingowego

```json
{
  "version": "2.0",
  "timestamp": "ISO8601",
  "benchmark_config": {
    "model": "openrouter/model-name",
    "judge_model": "openrouter/judge-model-name",
    "tasks_count": 5,
    "total_time_seconds": 1234
  },
  "ranking": {
    "model": "openrouter/model-name",
    "judge_model": "openrouter/judge-model-name",
    "scores": {
      "plan": 85,
      "implementation": 78,
      "tools_and_terminal": 72,
      "overall": 78
    },
    "tasks": [
      {
        "task_id": "uuid",
        "task_type": "feature|refactor|debug",
        "repo": "Investment-Assistant|AgentDeck|AutoResearch_SQLServer|TravianBot",
        "scores": {
          "plan": 85,
          "implementation": 78,
          "tools_and_terminal": 72
        },
        "time": {
          "plan_seconds": 123,
          "implementation_seconds": 456,
          "review_seconds": 89
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
}
```

## Plan implementacji (wysokopoziomowy)

### Faza 1: Podstawowa struktura orchestratora
- Utworzenie struktury katalogów `ai-tester-v2/`
- Implementacja klasy `Orchestrator` z metodą `run_task()`
- Implementacja `TaskManager` do zarządzania izolowanymi workspace'ami
- Implementacja `TimeTracker` do pomiaru czasu faz
- Implementacja `ToolLogger` do logowania użycia narzędzi

### Faza 2: Integracja z AI_Instruction
- Implementacja `PromptLoader` do ładowania promptów z AI_Instruction
- Implementacja `OpenRouterAdapter` do wywoływania modeli
- Implementacja mechanizmu wstrzykiwania kontekstu do promptów
- Integracja z skillami AI_Instruction jako źródła kryteriów

### Faza 3: Task Generator
- Implementacja `GitHubIssueFetcher` do pobierania Issues z GitHub
- Implementacja `TravianBotTaskGenerator` do generowania lokalnych tasków
- Implementacja `TaskComplexityScorer` do oceny złożoności
- Szablony tasków: feature, refactor, debug

### Faza 4: Scoring i Reporting
- Implementacja `PlanScorer` do oceny planu
- Implementacja `ImplementationScorer` do oceny implementacji
- Implementacja `ReviewRubricScorer` do oceny rubryki /review
- Implementacja `ObjectiveSignals` do agregacji sygnałów twardych
- Implementacja `RankingGenerator` do generowania rankingów
- Implementacja `TaskReporter` do generowania raportów per task

### Faza 5: Testy i walidacja
- Testy E2E całego workflow
- Benchmarki na przykładowych taskach
- Walidacja spójności ocen
- Testy izolacji tasków

## Powiązane pliki do utworzenia

| Plik | Przeznaczenie |
|---|---|
| `ai-tester-v2.orchestrator-architecture.md` | Ten plik — analiza architektury orchestracji |
| `ai-tester-v2.plan.md` | Szczegółowy plan implementacji po zakończeniu researchu |
| `ai-tester-v2/orchestrator/orchestrator.py` | Główna klasa Orchestrator |
| `ai-tester-v2/orchestrator/task_manager.py` | Zarządzanie cyklem życia tasków |
| `ai-tester-v2/orchestrator/time_tracker.py` | Pomiar czasu faz |
| `ai-tester-v2/orchestrator/tool_logger.py` | Logowanie użycia narzędzi |
| `ai-tester-v2/orchestrator/metrics_engine.py` | Agregacja metryk |
| `ai-tester-v2/agents/openrouter_adapter.py` | Adapter OpenRouter |
| `ai-tester-v2/agents/judge_agent.py` | Agent sędzi |
| `ai-tester-v2/task-generator/github_issue_fetcher.py` | Pobieranie Issues z GitHub |
| `ai-tester-v2/task-generator/travianbot_generator.py` | Generowanie tasków dla TravianBot |
| `ai-tester-v2/task-generator/task_complexity_scorer.py` | Ocena złożoności tasków |
| `ai-tester-v2/scorers/plan_scorer.py` | Ocena planu |
| `ai-tester-v2/scorers/implementation_scorer.py` | Ocena implementacji |
| `ai-tester-v2/scorers/tools_scorer.py` | Ocena użycia narzędzi |
| `ai-tester-v2/scorers/review_rubric_scorer.py` | Ocena rubryki /review |
| `ai-tester-v2/scorers/objective_signals.py` | Agregacja sygnałów twardych |
| `ai-tester-v2/reporting/ranking_generator.py` | Generowanie rankingów |
| `ai-tester-v2/reporting/task_reporter.py` | Generowanie raportów per task |
| `ai-tester-v2/schemas/ranking.schema.json` | Schemat rankingu modeli 0–100 |
| `ai-tester-v2/schemas/task-result.schema.json` | Schemat szczegółów per task |

## Modularization Decision

**Decyzja:** `use-existing-domain`

**Uzasadnienie:** AI_Tester v2 jest subsystemem evaluacyjnym AI_Instruction. Nie definiuje nowych granic domenowych, nie wprowadza zależności cyklicznych, i wykorzystuje istniejące skille jako źródła kryteriów. Nowy katalog `ai-tester-v2/` w workspace AI_Tester jest wystarczający.

---

*Analiza architektury orchestracji przygotowana na podstawie: ai-tester-v2.research.md, istniejących promptów AI_Instruction (/plan, /implement, /review), istniejących skilli AI_Instruction oraz obecnego stanu PoC AI_Tester. Data: 2026-06-17.*
