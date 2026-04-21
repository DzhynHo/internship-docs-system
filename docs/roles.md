# Role użytkowników (User Roles)

## 1. Wprowadzenie

Dokument opisuje role użytkowników w systemie ePraktyki oraz ich zakres uprawnień.
System wykorzystuje model autoryzacji oparty na rolach (*RBAC – Role-Based Access Control*).

---

## 2. Student

**Opis:**
Podstawowy użytkownik systemu, odpowiedzialny za uzupełnianie dokumentacji praktyk.

**Uprawnienia:**

* dostęp do własnych formularzy (załączniki 1–9)
* wypełnianie dokumentów
* edycja dokumentów przed wysłaniem do weryfikacji
* przegląd uwag od opiekuna
* ponowne przesyłanie dokumentów po poprawkach
* podgląd własnego protokołu zaliczenia

**Ograniczenia:**

* brak dostępu do danych innych studentów
* brak możliwości edycji po wysłaniu dokumentów do weryfikacji

---

## 3. Opiekun (Uczelniany / Zakładowy)

**Opis:**
Osoba odpowiedzialna za nadzór merytoryczny nad praktykami studenta.

**Uprawnienia:**

* przegląd dokumentów przypisanych studentów
* dodawanie uwag i komentarzy do dokumentów
* odsyłanie dokumentów do poprawy
* akceptacja poprawnych dokumentów

**Ograniczenia:**

* brak możliwości edycji danych wprowadzonych przez studenta
* brak dostępu do studentów spoza swojego zakresu

---

## 4. Administracja (Sekretariat / Dziekanat / Dyrekcja)

**Opis:**
Rola odpowiedzialna za obsługę formalną i końcową weryfikację dokumentacji.

**Uprawnienia:**

* dostęp do dokumentacji wszystkich studentów
* weryfikacja kompletności załączników (2a–7)
* zatwierdzanie dokumentacji
* dostęp do protokołów zaliczenia

**Ograniczenia:**

* brak ingerencji w treść merytoryczną dokumentów

---

## 5. Instytucja (Prezes / Kierownik)

**Opis:**
Przedstawiciel miejsca odbywania praktyk.

**Uprawnienia:**

* akceptacja dokumentów formalnych (np. oświadczenia, porozumienia)
* potwierdzenie realizacji praktyk

**Ograniczenia:**

* brak dostępu do pełnej dokumentacji systemu
* brak możliwości edycji dokumentów studenta

---

## 6. Uwagi końcowe

* Każdy użytkownik systemu posiada dokładnie jedną rolę.
* Uprawnienia są przypisane na podstawie roli (RBAC).
* System zapewnia izolację danych między użytkownikami.
* Dostęp do funkcji systemu jest kontrolowany na poziomie ról.
