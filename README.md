# ePraktyki – System zarządzania dokumentacją praktyk

Projekt opracowany przez **Valeriia Khylchenko**   

##  Opis projektu

ePraktyki to system koncepcyjny do zarządzania dokumentacją praktyk studenckich.
Umożliwia obsługę całego procesu — od wypełniania formularzy przez studenta, przez weryfikację opiekuna, aż po końcowe zatwierdzenie przez administrację.

Projekt został przygotowany w podejściu **documentation-first** i opisuje pełny workflow systemu, role użytkowników oraz wymagania funkcjonalne i niefunkcjonalne.

---

##  Cel systemu

Celem systemu jest:

* cyfryzacja procesu dokumentacji praktyk
* automatyzacja obiegu dokumentów
* zapewnienie kontroli i spójności danych
* uproszczenie procesu weryfikacji i zaliczenia praktyk

---

##  Role użytkowników

* Student
* Opiekun (uczelniany / zakładowy)
* Administracja (dziekanat / sekretariat)
* Instytucja (kierownik / prezes)

---

##  Główne funkcjonalności

* zarządzanie formularzami (załączniki 1–9)
* dziennik praktyk (dynamiczna tabela)
* workflow dokumentów (Student → Opiekun → Administracja)
* system uwag i weryfikacji
* generowanie dokumentów PDF
* kontrola dostępu (RBAC)

---

##  Dokumentacja

Projekt zawiera pełną specyfikację:

* `docs/requirements.md` – wymagania funkcjonalne
* `docs/user-stories.md` – scenariusze użytkowników
* `docs/roles.md` – role i uprawnienia
* `docs/workflow.md` – przebieg procesu
* `docs/architecture.md` – architektura systemu

---

##  Status projektu

📌 Etap: analiza i projekt (bez implementacji)

---

## 📌 Założenia techniczne (koncepcyjne)

* architektura trójwarstwowa
* model RBAC
* generowanie dokumentów PDF
* integralność danych (oryginały cyfrowe)


