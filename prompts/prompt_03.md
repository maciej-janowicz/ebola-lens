# Prompt 03: Eksploracja struktury PDF i wybór biblioteki do ekstrakcji

## Rola
Jesteś Codex, ekspertem Pythona pracującym nad projektem EbolaLens. Twoim zadaniem jest przygotowanie narzędzi do eksploracji i ekstrakcji danych z plików PDF, zgodnie z zasadą lekkich, odtwarzalnych rozwiązań działających na zwykłym laptopie.

## Kontekst projektu
- EbolaLens to narzędzie do monitorowania oficjalnych raportów epidemiologicznych.
- Obecny stan: projekt rejestruje źródła i wykrywa zmiany na poziomie bajtów (SHA-256), ale **nie odczytuje jeszcze zawartości merytorycznej** raportów.
- Zasada: Zależności główne muszą być minimalne (biblioteka standardowa). Nowe biblioteki do eksploracji PDF mogą być dodane jako opcjonalne (`[project.optional-dependencies.exploration]`).
- Projekt nie przechowuje pobranych plików PDF w repozytorium Git. Do testów używaj syntetycznych fixture'ów lub skryptów akceptujących ścieżkę do lokalnego pliku jako argument.

## Zadanie do wykonania
Stwórz komplet narzędzi do eksploracji struktury PDF i wyboru biblioteki do produkcji.

### 1. Skrypt inspekcji (`src/ebolalens/exploration/pdf_inspect.py`)
- Skrypt CLI, który przyjmuje ścieżkę do pliku PDF (lub używa domyślnego fixture'a z `data/fixtures/`).
- Wyświetla podstawowe metadane (liczba stron, autor, tytuł, jeśli dostępne).
- Wyodrębnia tekst z pierwszej strony i zapisuje go do `data/generated/pdf_exploration/inspect_output.txt`.
- Obsługuje błędy (np. brak pliku, uszkodzony PDF) w sposób elegancki, bez crashowania.

### 2. Skrypt porównawczy bibliotek (`src/ebolalens/exploration/compare_libs.py`)
- Porównuje wydajność i jakość ekstrakcji tekstu z tego samego pliku PDF za pomocą trzech bibliotek: `pypdf`, `pdfplumber` i `pymupdf` (fitz).
- Mierzy czas wykonania dla każdej z nich.
- Zapisuje wyniki (czas, długość wyodrębnionego tekstu, ewentualne błędy) do `data/generated/pdf_exploration/comparison_results.json`.
- Jeśli którejś biblioteki brakuje w środowisku, odnotowuje to w wynikach, ale nie przerywa działania skryptu.

### 3. Aktualizacja konfiguracji (`pyproject.toml`)
- Dodaj sekcję `[project.optional-dependencies]` z grupą `exploration`:
  ```toml
  [project.optional-dependencies.exploration]
  pdfplumber = ">=0.10.0"
  pypdf = ">=3.0.0"
  pymupdf = ">=1.23.0"
  ```

### 4. Dokumentacja decyzji (`docs/pdf_library_decision.md`)
- Stwórz szablon dokumentu, który zawiera:
  - Cel: wybór lekkiej i niezawodnej biblioteki do ekstrakcji tekstu i tabel z raportów INSP/WHO.
  - Kryteria: lekkość, łatwość instalacji (unikanie problemów z kompilacją C), jakość ekstrakcji, licencja.
  - Wstępna analiza porównawcza (na podstawie ogólnej wiedzy o tych bibliotekach), z miejscem na wklejenie wyników z `comparison_results.json`.

### 5. Testy (`tests/test_exploration.py`)
- Napisz testy jednostkowe, które weryfikują, czy oba skrypty uruchamiają się bez błędów na syntetycznym fixture'ze (np. prosty plik PDF wygenerowany w teście lub istniejący w `data/fixtures/`).
- Upewnij się, że testy nie wymagają sieci ani zewnętrznych plików.

### 6. Pliki podglądu zmian (`difflog/`)
- Utwórz katalog `difflog/`, jeśli nie istnieje.
- Wygeneruj plik `difflog/03.diff`, który zawiera podgląd różnic (unified diff) wszystkich utworzonych lub zmodyfikowanych plików w tym zadaniu.
- Wygeneruj plik `difflog/03.log`, który zawiera:
  - Listę utworzonych/zmodyfikowanych plików.
  - Krótkie podsumowanie działania skryptów (co robią, jakich bibliotek używają).
  - Informację: "Git operations (add, commit, push) are intentionally omitted from this output and must be performed manually after review."

## Ograniczenia i zasady
- **NIE wykonuj** poleceń `git add`, `git commit` ani `git push`. Tylko wygeneruj kod i pliki w `difflog/`.
- Zachowaj spójność z istniejącą architekturą (np. użycie `pathlib`, obsługa wyjątków).
- Kod musi być zgodny z Python 3.11+.
- Skrypty eksploracyjne są opcjonalne (grupa `exploration`), nie wpływają na główne zależności.
- Nie pobieraj automatycznie PDF-ów z internetu – używaj tylko tego, co jest już lokalnie dostępne lub przekazane jako argument.

## Kryteria akceptacji
- Wszystkie wymienione pliki zostały wygenerowane.
- `pyproject.toml` zawiera poprawną sekcję opcjonalnych zależności.
- `difflog/03.diff` i `difflog/03.log` istnieją i zawierają właściwe informacje.
- Brak jakichkolwiek poleceń Git w wygenerowanym kodzie.
- Testy przechodzą: `pytest tests/test_exploration.py -v`

## Struktura plików do utworzenia
```text
src/ebolalens/exploration/
├── __init__.py
├── pdf_inspect.py
└── compare_libs.py
tests/
└── test_exploration.py
docs/
└── pdf_library_decision.md
difflog/
├── 03.diff
└── 03.log
pyproject.toml (zmodyfikowany)
```

## Uwagi końcowe
Po wykonaniu wszystkich kroków, upewnij się, że:
1. Wszystkie pliki są utworzone i zawierają poprawny kod.
2. Pliki w `difflog/` są wygenerowane i zawierają kompletne informacje.
3. Kod jest zgodny ze stylem projektu (użycie `pathlib`, obsługa wyjątków, deterministyczne ścieżki).
4. Testy są napisane i mogą być uruchomione (nawet jeśli fixture'y PDF nie istnieją jeszcze w repozytorium).

Nie wykonuj żadnych operacji Git – to zostanie zrobione ręcznie przez zespół po przeanalizowaniu plików `.diff` i `.log`.