# Stan projektu EbolaLens

Stan opisany poniżej odpowiada zawartości repozytorium sprawdzonej 24 września
2026 r. Obejmuje także niezatwierdzone jeszcze zmiany w drzewie roboczym. Historia
Git zawiera dwa commity: utworzenie szkieletu projektu oraz rejestru źródeł i
wykrywania zmian (oba z 6 września 2026 r.). Nowszy interfejs rejestru dokumentów
jest obecnie zmianą roboczą, a nie osobnym commitem.

## Cel i obecny zakres

EbolaLens ma być lekkim, odtwarzalnym narzędziem do monitorowania oficjalnych
materiałów o trwającym ognisku choroby wywołanej wirusem Bundibugyo. Projekt ma
działać na zwykłym laptopie, bez bazy danych, HPC ani płatnej chmury. Planowany
MVP-0 opisuje `docs/project_charter.md`: rejestrację raportów, zachowanie
proweniencji i rewizji, podstawową ekstrakcję i walidację danych oraz lekkie
publikowanie wyników.

**Zakres działający obecnie jest węższy.** Kod rejestruje adresy oficjalnych
źródeł, wykrywa kandydatów w jednym kanale RSS, pobiera zarejestrowane dokumenty
i rozpoznaje ich wersje na poziomie surowych bajtów. Potrafi też wyświetlić
kanoniczne rekordy dokumentów z istniejącego manifestu. Nie odczytuje zawartości
epidemiologicznej raportów, nie oblicza wskaźników, nie weryfikuje sum, nie
prognozuje i nie publikuje dashboardu. Nie jest oficjalnym źródłem ani narzędziem
do decyzji klinicznych lub samodzielnego zarządzania epidemią.

## Co jest zaimplementowane

- `data/sources.json` jest utrzymywanym ręcznie rejestrem schematu 1. Zawiera
  trzy strony źródłowe (INSP i WHO), jeden endpoint odkrywania — kanał INSP
  SitRep RSS — oraz trzy jawnie potwierdzone dokumenty startowe INSP. Nieznane
  numery i daty raportów pozostają `null`; nazwa pliku nie jest traktowana jako
  dowód metadanych ani tożsamości dokumentu.
- `src/ebolalens/sources.py` waliduje rejestr, obsługuje transport live i
  deterministyczne fixture'y offline, parsuje RSS, buduje historię kandydatów,
  identyfikuje treść przez SHA-256, deduplikuje identyczne payloady, zachowuje
  wersje i błędy oraz zapisuje JSON atomowo. Pobrania są sekwencyjne, mają
  15-sekundowy timeout, limit 10 MiB, własny `User-Agent`, obsługę przekierowań
  oraz warunkowych nagłówków ETag/Last-Modified.
- `src/ebolalens/__main__.py` udostępnia CLI: wersję, listę źródeł, kontrolę
  offline/live oraz listę dokumentów w tabeli lub JSON. Polecenie `documents
  list` tylko czyta manifest i nie korzysta z sieci.
- `data/fixtures/` zawiera małe dane syntetyczne, a nie kopie pobranych raportów.
  Służą one do powtarzalnych testów bez sieci.
- `tests/test_smoke.py` i `tests/test_sources.py` sprawdzają m.in. CLI, walidację
  konfiguracji, odkrywanie RSS, kumulatywną historię kandydatów, zmianę i brak
  zmiany payloadu, odpowiedź 304, zachowanie stanu po błędzie, deduplikację,
  deterministyczny porządek, atomowy zapis i odczyt rejestru dokumentów.

Najważniejsze polecenia:

```bash
.venv/bin/python -m ebolalens --version
.venv/bin/python -m ebolalens sources list
.venv/bin/python -m ebolalens sources check --offline
.venv/bin/python -m ebolalens sources check --live
.venv/bin/python -m ebolalens documents list \
  --manifest data/generated/offline_source_manifest.json
.venv/bin/python -m ebolalens documents list \
  --manifest data/generated/offline_source_manifest.json --json
```

## Jak wykrywane są zmiany i powstaje manifest

1. CLI wczytuje i waliduje `data/sources.json`. Identyfikatory i kanoniczne URL-e
   muszą być unikalne, a adresy muszą używać HTTPS.
2. W trybie live pobierane są zarejestrowane strony, endpointy i dokumenty. Tryb
   offline podstawia fixture'y oraz stały znacznik czasu
   `2000-01-01T00:00:00Z`; jest to wartość testowa, nie data obserwacji świata.
3. Z potwierdzonego kanału `https://insp.cd/category/sitrep/feed/` parser wydobywa
   linki wpisów i osadzone URL-e PDF. Są one tylko **kandydatami**. Kod ich
   automatycznie nie pobiera, nie rejestruje jako dokumentów i nie przypisuje im
   znaczenia epidemiologicznego.
4. Rejestr kandydatów jest kumulatywny: przechowuje dokładny URL, wydawcę,
   endpoint, pierwszą i ostatnią obserwację, obecność w ostatniej poprawnej
   odpowiedzi oraz informację, czy URL jest nowy w danym przebiegu. Zniknięcie z
   poprawnie odczytanego feedu zmienia flagę obecności, ale nie usuwa historii.
   Błąd transportu lub XML pozostawia ostatni poprawny stan obecności.
5. Dla każdego ręcznie zarejestrowanego dokumentu obliczany jest SHA-256 surowych
   bajtów. Nowy hash tworzy payload i wersję; znany hash oznacza brak zmiany lub
   współdzielenie payloadu przez inny URL. Status dokumentu to `new`,
   `unchanged`, `changed` albo `unavailable`. Różne bajty mogą oznaczać jedynie
   przepakowanie pliku, a identyczne bajty nie dowodzą wspólnej tożsamości
   logicznej.
6. Stan jest zapisywany atomowo i deterministycznie. Domyślne ścieżki są
   rozdzielone: `data/generated/offline_source_manifest.json` dla fixture'ów i
   `data/generated/source_manifest.json` dla live. Można je zmienić przez
   `--manifest PATH`; pliki `data/generated/*.json` są ignorowane przez Git.

Manifest rozdziela logiczne dokumenty (`documents`) od wersji bajtowych
(`payloads`) oraz zawiera osobne kolekcje stron, endpointów i kandydatów. Błąd
pojedynczego źródła jest zapisany przy rekordzie i nie usuwa wcześniejszych
udanych wyników.

## Uruchomienie i testy

Projekt wymaga Pythona 3.11 lub nowszego i nie ma zależności uruchomieniowych
poza biblioteką standardową. W repozytorium istnieje działające `.venv` z
instalacją edytowalną. W obecnym środowisku wystarczy:

```bash
source .venv/bin/activate
python -m pytest -q
python -m ebolalens sources check --offline
```

Aby odtworzyć środowisko od zera:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest -q
```

Kontrola live wykonuje rzeczywiste żądania sieciowe i aktualizuje stan
operacyjny, dlatego należy uruchamiać ją świadomie. Kontrola offline jest
bezpiecznym pierwszym sprawdzeniem po zmianie rejestru.

## Potwierdzone wyniki

- Kontrola wykonana podczas przygotowania tego dokumentu 24 września 2026 r.:
  `23 passed in 0.86s`; CLI podało wersję `0.0.0`, wypisało 3 strony, 1 endpoint
  i 3 dokumenty. Świeży przebieg offline do pliku tymczasowego sprawdził 7 URL-i
  fixture'ów, znalazł 1 syntetycznego kandydata i 3 unikalne syntetyczne
  payloady. Nie wykonano nowego sprawdzenia live.
- Zachowany lokalnie, ignorowany przez Git `data/generated/source_manifest.json`
  ma `generated_at` równy `2026-09-08T21:55:14.852378Z`. Rejestruje 3 poprawnie
  dostępne strony (HTTP 200), poprawny feed INSP (HTTP 200), 20 obecnych
  kandydatów oraz 3 niezmienione dokumenty obsłużone odpowiedzią HTTP 304 i 3
  payloady. Kandydaci byli po raz pierwszy widziani
  `2026-09-08T21:52:05.429770Z`. Jest to wynik pojedynczych uruchomień i dowód
  dostępności/identyczności bajtów w tamtym czasie, nie walidacja treści.
- `docs/source_investigation.md` i `stage01_sources_report.log` dokumentują
  rozpoznanie z 6 września 2026 r.: strona INSP, WordPress REST i RSS odpowiadały
  HTTP 200, a badane sitemap'y HTTP 404. Raport etapu zapisuje także live run z
  `2026-09-05T23:11:04.454220Z`: 7 osiągalnych zarejestrowanych URL-i, 20
  kandydatów i 3 payloady. Są to artefakty audytowe; obecny kod automatycznie
  używa tylko RSS, nie WordPress REST ani sitemap.

## Co pozostaje do zrobienia i ograniczenia

- Ręcznie ocenić kandydatów RSS i dopiero po potwierdzeniu dopisywać dokumenty
  oraz jawnie znane metadane do `data/sources.json`. Obecny rejestr ma tylko trzy
  dokumenty startowe, mimo 20 URL-i kandydatów w zachowanym przebiegu live.
- Poszerzyć i uodpornić odkrywanie. RSS może być niepełny lub zniknąć; WHO jest
  tylko sprawdzane pod kątem dostępności, bez automatycznego wydobywania
  dokumentów. Nie ma szerokiego crawlera ani produkcyjnego fallbacku REST.
- Zaimplementować kolejne, obecnie wyłącznie planowane etapy: ekstrakcję danych z
  raportów, rozdzielenie danych obserwowanych/korygowanych/modelowanych,
  walidację sum, rejestr rewizji semantycznych i lekkie wyniki statyczne.
- Dodać harmonogram uruchomień, alertowanie/raportowanie operacyjne oraz politykę
  retencji lub archiwizacji. Aktualnie narzędzie działa na żądanie i zapisuje
  tylko manifest metadanych; nie przechowuje pobranych treści dokumentów.
- Ustalić licencję przed pierwszym publicznym wydaniem. Projekt ma nadal wersję
  `0.0.0`, nie ma deklarowanej stabilności API ani produkcyjnych gwarancji.
- Traktować zapisany manifest live ostrożnie: jest lokalnym, ignorowanym
  artefaktem uruchomienia i powstał przed najnowszym rozszerzeniem kanonicznych
  rekordów (`origin`, `all_urls`, `discovered_from`). Nowy przebieg utworzy
  rekordy według bieżącego kodu, ale nie należy nadpisywać historii operacyjnej
  fixture'ami — temu służą rozdzielone ścieżki manifestów.
