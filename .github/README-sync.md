---
# Synchronizacja metadanych GitHub

Pliki `.github/gh-sync.json` oraz `.github/issue-seed.json` (jeśli występują) są źródłem prawdy i powinny definiować metadane repozytorium oraz seed issue. Sekwencja operacji: `sync` → `seed`.

Przykładowe komendy PowerShell (dry-run):

```powershell
.\scripts\sync-github-meta.ps1 -DryRun > sync-dry-run.log
.\scripts\seed-github-issues.ps1 -DryRun >> sync-dry-run.log
```

Przykładowe komendy PowerShell (Apply):

```powershell
.\scripts\sync-github-meta.ps1 -Apply
.\scripts\seed-github-issues.ps1 -Apply
```

Przed Apply:
- Wykonaj backup REST repozytorium (np. `gh api` lub `curl`) i zachowaj jako JSON.
- Sprawdź kodowanie plików (UTF-8) oraz unikalność `sourceId`.

Checklist przed Apply:
- Backup REST
- Walidacja UTF-8
- Unikatowe `sourceId`
- Zgodność prefixów tytułów issue (dopasuj do repo)

Jeśli brakuje skryptów `scripts/sync-github-meta.ps1` / `scripts/seed-github-issues.ps1` — zaimplementuj lokalne skrypty lub zaakceptuj, że workflow nie wykona żadnych działań. Workflow nie kończy się błędem, gdy skrypty nie występują.

Dostosuj prefix issue (np. TB-, IA-, AR-, SEQ-, DQN-) jeśli używasz lokalnego seed.

Króciutka checklista walidacji:
- UTF-8
- `sourceId` unikatowe
- Tytuły issue spójne z konwencją

---
