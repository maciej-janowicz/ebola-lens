# Prompt 02 — audyt manifestu i kanoniczny rejestr dokumentów

Pracujesz w repozytorium `Ebola_Lens` — niewielkim, reprodukowalnym projekcie informatycznym analizującym **publicznie dostępne raporty epidemiologiczne**. Ten etap dotyczy wyłącznie inżynierii danych: pochodzenia dokumentów, metadanych, wersjonowania, deduplikacji i testów. Nie obejmuje procedur laboratoryjnych, hodowli, modyfikacji biologicznych ani porad klinicznych.

## Stan wejściowy

Repozytorium ma czysty working tree. Istnieją między innymi:

- `data/sources.json`;
- fixture'y HTML, XML i PDF w `data/fixtures/`;
- `data/generated/offline_source_manifest.json`;
- `data/generated/source_manifest.json`;
- `docs/project_charter.md`;
- `docs/source_investigation.md`;
- `src/ebolalens/sources.py` oraz CLI w `src/ebolalens/__main__.py`;
- `tests/test_sources.py` i `tests/test_smoke.py`.

Ostatni test offline zwrócił:

```text
checked 7 registered URLs at 2000-01-01T00:00:00Z
insp-home: ok
who-outbreak-page: ok
who-don-index: ok
insp-sitrep-feed: ok
insp-seed-draft-mve-ituri-actuelb-1: unchanged
insp-seed-sitrep-055: unchanged
insp-seed-sitrep-068: unchanged
total known candidates: 1
newly discovered candidates: 0
candidates present in current feed: 1
unique document payloads: 3
```

Wynik `total known candidates: 1` przy `unique document payloads: 3` może być poprawny, jeżeli „candidate” oznacza wyłącznie pozycję odkrytą w fixture feedu, a trzy payloady pochodzą z jawnie zarejestrowanych dokumentów seed. Trzeba to ustalić na podstawie kodu i danych, nie zgadywać.

## Cel etapu

Przekształć obecny mechanizm kontroli źródeł w mały, audytowalny **kanoniczny rejestr dokumentów**. Każdy dokument ma być identyfikowalny niezależnie od tego, pod iloma URL-ami występuje, a użytkownik ma móc obejrzeć rejestr bez dostępu do sieci.

Najpierw wykonaj audyt istniejącej implementacji. Następnie wprowadź najmniejszy spójny zestaw zmian realizujący poniższe wymagania. Nie przebudowuj projektu ponad potrzebę.

## Wymagania funkcjonalne

### 1. Wyjaśnienie semantyki liczników

Ustal dokładne znaczenie co najmniej następujących pojęć i liczników:

- registered source / registered URL;
- candidate;
- candidate present in current feed;
- document payload;
- unique document payload.

Sprawdź, dlaczego test offline raportuje jednego kandydata i trzy unikalne payloady. Jeżeli wynik jest logicznie poprawny, zachowaj go, ale popraw nazwy lub dokumentację tak, aby nie wprowadzał w błąd. Jeżeli ujawnia błąd, napraw przyczynę i dodaj test regresyjny. Nie zmieniaj oczekiwań testów tylko po to, aby dopasować je do przypadkowego wyniku.

### 2. Kanoniczny rekord dokumentu

Wprowadź jawny, udokumentowany model rekordu dokumentu, zgodny ze stylem istniejącego kodu. Rekord powinien przechowywać, gdy informacja jest dostępna:

- stabilny identyfikator dokumentu;
- kanoniczny URL i wszystkie znane alternatywne URL-e;
- identyfikator źródła, z którego dokument został odkryty;
- tytuł;
- datę publikacji lub raportowania;
- czas sprawdzenia/pobrania;
- typ zawartości;
- rozmiar w bajtach;
- SHA-256 surowego payloadu;
- status (`new`, `unchanged`, `changed`, `unavailable` lub równoważny, jeżeli projekt ma już lepszy model);
- informację o tym, czy rekord pochodzi z jawnego seeda, czy z discovery.

Nie wymyślaj metadanych, których nie da się wiarygodnie wyprowadzić. Brak danych przedstawiaj jawnie jako `null`/brak pola, zgodnie z dotychczasową konwencją projektu.

### 3. Deduplikacja i pochodzenie

- Deduplikuj treści według SHA-256 surowych bajtów.
- Nie usuwaj informacji o wielu URL-ach prowadzących do tej samej treści.
- Rozdziel tożsamość logicznego dokumentu od konkretnej wersji jego payloadu, jeżeli istniejący kod pozwala to zrobić bez nadmiernej przebudowy.
- Wynik ma być deterministyczny: stabilna kolejność rekordów i pól, brak zależności od kolejności zbiorów lub map.
- Nie zapisuj samych binarnych PDF-ów do repozytorium poza istniejącymi fixture'ami. Manifest ma zawierać metadane i skróty, a nie zakodowaną treść dokumentów.

### 4. Polecenie CLI działające offline

Dodaj czytelne polecenie w rodzaju:

```bash
.venv/bin/python -m ebolalens documents list \
  --manifest data/generated/offline_source_manifest.json
```

Jeżeli obecna architektura uzasadnia inną składnię, wybierz ją i wyjaśnij. Polecenie:

- nie może łączyć się z siecią;
- ma domyślnie wyświetlać zwartą tabelę tekstową;
- powinno pokazywać co najmniej ID, datę, skrócony tytuł lub nazwę, liczbę URL-i, status i skrócony SHA-256;
- powinno mieć opcję pełnego, maszynowo czytelnego wyjścia JSON, jeżeli można ją dodać bez nowej ciężkiej zależności;
- ma zwracać niezerowy kod wyjścia i jasny komunikat dla brakującego lub niepoprawnego manifestu.

Nie dodawaj biblioteki do formatowania tabel, jeśli standardowa biblioteka Pythona wystarcza.

### 5. Testy

Dodaj testy obejmujące co najmniej:

- dwa URL-e z identycznym payloadem dają jeden unikalny payload bez utraty obu URL-i;
- ten sam URL z inną treścią zostaje rozpoznany jako zmieniony;
- seed i dokument odkryty w feedzie mają prawidłowo oznaczone pochodzenie;
- kolejność rekordów i serializacja są deterministyczne;
- polecenie listujące działa bez sieci;
- brakujący oraz uszkodzony manifest są obsługiwane kontrolowanie;
- wyjaśniona zostaje relacja między jednym kandydatem i trzema payloadami z obecnego fixture'u albo test wykazuje i zabezpiecza naprawiony wynik.

Testy nie mogą korzystać z bieżącej sieci ani zależeć od aktualnej zawartości stron zewnętrznych.

### 6. Dokumentacja

Zaktualizuj odpowiednie istniejące dokumenty zamiast tworzyć wiele nowych plików. Opisz:

- model danych i znaczenie liczników;
- reguły tożsamości oraz deduplikacji;
- sposób wygenerowania manifestu offline i live;
- sposób wyświetlenia rejestru bez sieci;
- ograniczenia: identyczny payload nie zawsze musi oznaczać ten sam logiczny dokument, a różny payload może być tylko techniczną zmianą opakowania PDF/HTML.

Dodaj krótkie ostrzeżenie, że narzędzie służy do badań i kontroli publicznych danych epidemiologicznych, a nie do decyzji klinicznych ani samodzielnego zarządzania epidemią.

## Ograniczenia wykonawcze

- Najpierw przeczytaj `README`, konfigurację projektu, `data/README.md`, wskazane dokumenty, kod źródłowy i testy.
- Zachowaj zgodność z obsługiwaną wersją Pythona i istniejącymi zależnościami.
- Nie dodawaj ciężkich zależności.
- Nie wykonuj operacji sieciowych podczas testów.
- Nie modyfikuj fixture'ów wyłącznie w celu ukrycia błędu.
- Nie ruszaj plików niezwiązanych z tym etapem.
- Nie wykonuj `git commit`, `git push`, `git reset`, `git checkout` ani innych destrukcyjnych poleceń Git.
- Jeżeli working tree na początku nie jest czysty, zatrzymaj się i opisz zastane zmiany; nie nadpisuj ich.
- Nie ogłaszaj sukcesu, jeżeli testy nie przechodzą.

## Weryfikacja

Uruchom co najmniej:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ebolalens sources check --offline
```

Następnie uruchom nowe polecenie listujące rejestr oraz, jeżeli jest dostępne, jego wariant JSON. Sprawdź ręcznie, czy liczby i rekordy są ze sobą spójne.

## Artefakty końcowe

W katalogu głównym repozytorium zapisz:

- `prompt_02_document_registry.diff` — wynik `git diff --binary`, bez plików wygenerowanych tylko jako log;
- `prompt_02_document_registry.log` — zwięzły dziennik zawierający:
  - rozpoznany stan początkowy;
  - wyjaśnienie wyniku „1 candidate / 3 payloads”;
  - listę zmienionych plików;
  - decyzje projektowe;
  - dokładne uruchomione polecenia weryfikacyjne i ich wyniki;
  - znane ograniczenia i ewentualne dalsze kroki.

Na końcu odpowiedzi podaj:

1. krótkie podsumowanie wykonanych zmian;
2. wyjaśnienie semantyki liczników;
3. wyniki testów i poleceń CLI;
4. listę zmienionych oraz nowych plików;
5. wynik `git status --short`;
6. wszelkie nierozwiązane problemy — bez ich ukrywania.

