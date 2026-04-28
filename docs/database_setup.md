# Dokumentacja Projektu Bazy Danych - ePraktyki

## Zadanie 3. Dobór systemu bazy danych

Dla prototypu aplikacji **ePraktyki** wybrano silnik **SQLite**, natomiast jako rozwiązanie docelowe wskazano **MariaDB**.

### Uzasadnienie wyboru SQLite (Etap Prototypu)
* **Zero konfiguracji:** Baza danych jest przechowywana w pojedynczym pliku `.db`, co eliminuje konieczność instalacji serwera na etapie developmentu (uproszczenie względem MS SQL czy Oracle).
* **Natywna integracja:** Jako biblioteka standardowa Pythona, SQLite pozwala na natychmiastowe testowanie logiki biznesowej i integrację z aplikacją.
* **Lekkość:** Idealna do szybkich iteracji schematu i testów jednostkowych w środowisku lokalnym.

### Ograniczenia i rekomendacja docelowa (MariaDB)
Choć SQLite jest wydajny, w wersji produkcyjnej zostanie zastąpiony przez **MariaDB** (Open Source'owa, wydajna alternatywa dla MySQL/Oracle). Powody migracji to:
1. **Współbieżność:** MariaDB obsługuje setki równoległych połączeń (studentów i opiekunów), unikając blokowania bazy przy zapisie.
2. **Bezpieczeństwo:** Oferuje zaawansowane mechanizmy uprawnień (GRANT/REVOKE) oraz pełną transakcyjność ACID.

---

## Zadanie 4. Dobór narzędzia do prototypowania BD

Wybrane narzędzie: **DBeaver Community**.

### Uzasadnienie i zastosowanie
DBeaver to uniwersalne narzędzie (Universal Database Tool), które dla tego projektu stanowi darmowy odpowiednik SQL Server Management Studio (SSMS) lub Oracle SQL Developer.

* **Multiplatformowość:** Obsługuje zarówno pliki SQLite, jak i docelowe bazy MariaDB/PostgreSQL w jednym oknie.
* **Wizualizacja ERD:** Pozwala na automatyczne generowanie graficznych schematów na podstawie istniejących tabel, co ułatwia weryfikację poprawności kluczy obcych i relacji.
* **Edytor SQL:** Posiada zaawansowane podpowiadanie składni (IntelliSense), co minimalizuje błędy przy tworzeniu złożonych zapytań JOIN.

---

## Zadanie 5. Propozycja narzędzia do organizacji projektu

Do modelowania przepływów danych i dokumentowania logiki biznesowej wybrano narzędzie **Mermaid**.

### Uzasadnienie
* **Diagram-as-Code:** Umożliwia tworzenie diagramów za pomocą tekstu, co pozwala na ich wersjonowanie w systemie Git (podobnie jak kodu źródłowego).
* **Mapowanie na SQL:** Diagramy sekwencji pozwalają precyzyjnie określić momenty interakcji użytkowników z bazą (np. kiedy następuje UPDATE statusu w tabeli `praktyki`).

### Wizualizacja przepływu (Workflow)
Szczegółowy diagram przepływu danych, opisujący kroki od Inicjacji do Wyniku końcowego, został opracowany w formacie Mermaid i znajduje się w głównym katalogu dokumentacji:

👉 **[Link do pliku workflow.mmd](./diagrams/workflow.mmd)**

Diagram ten służy jako podstawa do implementacji logiki blokowania edycji rekordów przez System po przesłaniu kompletu dokumentów przez Studenta.
