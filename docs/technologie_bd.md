# Dokumentacja Techniczna Systemu ePraktyki

## Zadanie 3. Dobór systemu bazy danych

Dla prototypu aplikacji **ePraktyki** wybrano silnik **SQLite**, natomiast jako rozwiązanie docelowe wskazano **MariaDB**.

### Uzasadnienie wyboru SQLite (Etap Prototypu)
* **Zero konfiguracji:** Baza danych jest przechowywana w pojedynczym pliku `.db`, co eliminuje konieczność instalacji i konfiguracji serwera (uproszczenie względem MS SQL czy Oracle).
* **Natywna integracja:** Jest to biblioteka standardowa języka Python, co przyspiesza proces implementacji modelu danych.
* **Lekkość:** Idealna do szybkich iteracji i testowania logiki biznesowej bez narzutu administracyjnego.

### Ograniczenia SQLite i rozwiązanie docelowe
1. **Współbieżność:** SQLite blokuje cały plik podczas zapisu, co przy jednoczesnej pracy wielu studentów i opiekunów mogłoby powodować przestoje.
2. **Uprawnienia:** W przeciwieństwie do systemów takich jak Oracle, SQLite nie posiada rozbudowanego systemu ról na poziomie silnika bazy danych.

**Rekomendacja docelowa: MariaDB**
* **Skalowalność:** Pozwala na setki równoczesnych połączeń i bezpieczną pracę wieloużytkownikową.
* **Bezpieczeństwo:** Oferuje zaawansowane mechanizmy uprawnień (GRANT/REVOKE) i pełną transakcyjność ACID.
* **Open Source:** Darmowa i wydajna alternatywa dla komercyjnych rozwiązań, w pełni kompatybilna ze standardami SQL.

---

## Zadanie 4. Dobór narzędzia do prototypowania BD

Wybrane narzędzie: **DBeaver Community**.

### Uzasadnienie wyboru
Jako uniwersalne narzędzie typu *Universal Database Tool*, DBeaver stanowi darmową i nowoczesną alternatywę dla narzędzi takich jak SQL Server Management Studio (SSMS) czy Oracle SQL Developer.

### Zastosowanie w projekcie
* **Uniwersalność:** Obsługuje zarówno SQLite (faza prototypu), jak i MariaDB/PostgreSQL (faza produkcyjna) w obrębie jednej aplikacji.
* **Wizualizacja (ERD):** Posiada funkcję automatycznego generowania schematów graficznych na podstawie istniejących tabel, co ułatwia weryfikację relacji między encjami.
* **Edytor SQL:** Oferuje zaawansowane podpowiadanie składni (IntelliSense), co znacząco przyspiesza pisanie zapytań i skryptów DDL.
* **Zarządzanie danymi:** Umożliwia łatwy eksport/import danych oraz migrację schematów pomiędzy różnymi silnikami baz danych.
