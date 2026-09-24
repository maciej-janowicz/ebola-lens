# Wybór biblioteki do ekstrakcji PDF

## Cel

Celem eksploracji jest wybór lekkiej i niezawodnej biblioteki do ekstrakcji
tekstu i tabel z raportów INSP i WHO. Decyzja produkcyjna powinna opierać się na
reprezentatywnej, lokalnej próbce raportów, bez dodawania pobranych PDF-ów do Git.

## Kryteria

- lekkość zależności i zużycie zasobów na zwykłym laptopie;
- łatwa, powtarzalna instalacja, najlepiej z gotowych wheelów i bez lokalnej
  kompilacji rozszerzeń C;
- jakość tekstu: kolejność czytania, znaki diakrytyczne, nagłówki i kolumny;
- jakość tabel i możliwość zachowania ich struktury;
- aktywność projektu, dokumentacja i stabilność API;
- licencja zgodna z przyszłą licencją i sposobem dystrybucji EbolaLens.

## Wstępna analiza

| Biblioteka | Mocne strony | Koszty i ryzyka | Wstępna rola |
| --- | --- | --- | --- |
| `pypdf` | Czysty Python, prosta instalacja, metadane i podstawowy tekst | Ograniczona rekonstrukcja tabel i złożonego układu | Lekki punkt odniesienia i inspekcja |
| `pdfplumber` | Dostęp do geometrii znaków, słów i tabel; wygodne API eksploracyjne | Więcej zależności i wolniejsze przetwarzanie | Kandydat do ekstrakcji tabel |
| `pymupdf` (`fitz`) | Zwykle szybka ekstrakcja tekstu i renderowanie stron | Natywne binaria; należy osobno zatwierdzić konsekwencje licencji | Kandydat do szybkiej ekstrakcji tekstu |

To są hipotezy oparte na ogólnej charakterystyce bibliotek, nie wynik benchmarku
EbolaLens. Licencje i warunki dystrybucji trzeba zweryfikować ponownie względem
konkretnych wersji przed decyzją produkcyjną.

## Wyniki lokalnego porównania

Uruchom:

```bash
python -m ebolalens.exploration.compare_libs /ścieżka/do/raportu.pdf
```

Następnie wklej lub podsumuj tutaj zawartość
`data/generated/pdf_exploration/comparison_results.json`, wraz z informacją o
systemie, wersji Pythona, wersjach bibliotek i rodzaju badanego raportu.

<!-- Miejsce na wyniki comparison_results.json. -->

## Decyzja

Do uzupełnienia po testach na kilku reprezentatywnych raportach INSP i WHO.
Należy osobno wskazać bibliotekę podstawową, ewentualny fallback oraz uzasadnić,
czy obsługa tabel wymaga innego backendu niż ekstrakcja zwykłego tekstu.
