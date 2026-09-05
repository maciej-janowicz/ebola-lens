# Prompt 00 — minimalny szkielet projektu EbolaLens

Pracujesz w pustym lokalnym repozytorium Git projektu **EbolaLens**.

EbolaLens ma być lekkim, publicznym i w pełni reprodukowalnym narzędziem operacyjnym do przetwarzania oficjalnych raportów o trwającej epidemii choroby wywołanej wirusem Bundibugyo. Wersja podstawowa musi działać na zwykłym laptopie bez HPC, płatnej chmury, serwera bazodanowego i ciężkiego frontendu.

Dewiza projektu:

> Public quickly. Correct carefully. Revise transparently.

## Cel tego etapu

Utwórz wyłącznie minimalny, profesjonalny szkielet projektu. Nie pobieraj jeszcze raportów, nie implementuj parsera PDF, modeli epidemicznych, dashboardu ani GitHub Pages.

## Wymagane pliki i katalogi

Utwórz co najmniej:

* `README.md`
* `pyproject.toml`
* `.gitignore`
* `src/ebolalens/__init__.py`
* `src/ebolalens/__main__.py`
* `tests/test_smoke.py`
* `docs/project_charter.md`
* `data/README.md`
* `prompts/README.md`

Nie usuwaj ani nie modyfikuj tego promptu.

## Zasady projektu

1. Użyj układu `src`.

2. Wymagaj Python 3.11 lub nowszego.

3. Nie dodawaj zależności wykonawczych bez rzeczywistej potrzeby.

4. `pytest` może być zależnością deweloperską.

5. Dodaj minimalne polecenie:

   ```bash
   python -m ebolalens --version
   ```

6. Dodaj test sprawdzający import pakietu oraz działanie informacji o wersji.

7. Początkowa wersja pakietu: `0.0.0`.

8. Nie wybieraj jeszcze licencji. W `README.md` zaznacz krótko, że polityka licencyjna zostanie ustalona przed pierwszym publicznym wydaniem.

9. Nie dodawaj CI, GitHub Actions, dokumentacji generowanej, Dockera, notebooków, dashboardu ani frameworka webowego.

10. Nie wykonuj `git add`, `git commit`, `git push` ani operacji na GitHubie.

11. Wszystkie pliki tekstowe mają być zapisane jako UTF-8.

12. Kod i dokumentacja techniczna mają być po angielsku.

## Treść karty projektu

`docs/project_charter.md` powinien zwięźle określać:

* cel operacyjny;
* pierwszych użytkowników: analityków wspierających INSP, WHO, Africa CDC i organizacje terenowe;
* trzy obszary obrazu sytuacji:

  * epidemic evolution,
  * observation and reporting quality,
  * response-system pressure;
* zakres MVP-0:

  * rejestrowanie oficjalnych raportów,
  * zachowanie pochodzenia danych,
  * wykrywanie nowych i zmienionych dokumentów,
  * ekstrakcja podstawowych danych,
  * walidacja sum,
  * jawny rejestr rewizji,
  * publikacja lekkich wyników statycznych;
* wyłączenia MVP-0:

  * zalecenia kliniczne,
  * oficjalne prognozy,
  * automatyczne decyzje operacyjne,
  * złożone modele przestrzenne,
  * ciężki dashboard;
* zasadę działania na zwykłym laptopie;
* zasadę wyraźnego oddzielania danych obserwowanych, skorygowanych i modelowanych.

## README

`README.md` powinien być krótki i zawierać:

* jednozdaniowy opis;
* ostrzeżenie, że projekt jest na bardzo wczesnym etapie i nie stanowi oficjalnego źródła ani porady klinicznej;
* wymagania;
* instrukcję utworzenia środowiska wirtualnego;
* instalację w trybie edytowalnym z zależnościami deweloperskimi;
* uruchomienie testów;
* uruchomienie polecenia wersji;
* odsyłacz do karty projektu.

Nie wpisuj niezweryfikowanych liczb epidemiologicznych.

## Kontrola

Po utworzeniu plików:

1. utwórz lokalne środowisko `.venv`, jeśli nie istnieje;
2. zainstaluj projekt w trybie edytowalnym z zależnościami deweloperskimi;
3. uruchom testy;
4. uruchom `python -m ebolalens --version`;
5. sprawdź `git status --short`;
6. przejrzyj wszystkie utworzone pliki pod kątem prostoty, spójności i braku przedwczesnej architektury.

Jeżeli instalacja lub testy nie działają, napraw przyczynę i powtórz kontrolę.

## Artefakty kontrolne

Na końcu utwórz:

* `stage00_scaffold_report.log` — zwięzły raport zawierający listę utworzonych plików, wykonane kontrole, dokładne wyniki testów oraz wszelkie założenia;
* `stage00_scaffold_changes.diff` — czytelny unified diff obejmujący wszystkie nowe pliki, również nieśledzone.

Nie umieszczaj sekretów, tokenów, danych uwierzytelniających ani pełnej zawartości środowiska w raporcie.

Na końcu wyświetl krótkie podsumowanie, wynik testów i `git status --short`. Nie wykonuj commitu.
