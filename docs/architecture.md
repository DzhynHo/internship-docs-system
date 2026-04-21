# Architektura systemu

## 1. Wprowadzenie

Dokument opisuje założenia architektoniczne systemu ePraktyki, w tym wymagania niefunkcjonalne oraz główne komponenty systemu.

System ma charakter aplikacji webowej wspierającej zarządzanie dokumentacją praktyk studenckich.

---

## 2. Architektura ogólna

System oparty jest na klasycznej architekturze trójwarstwowej:

### 2.1 Warstwy systemu

**Frontend (Warstwa prezentacji):**

* interfejs użytkownika (UI)
* formularze (załączniki 1–9)
* responsywność (mobile + desktop)

**Backend (Warstwa logiki biznesowej):**

* obsługa workflow
* walidacja danych
* zarządzanie użytkownikami i rolami
* generowanie dokumentów PDF

**Baza danych (Warstwa danych):**

* przechowywanie danych użytkowników
* przechowywanie formularzy i dokumentów
* statusy workflow

---

## 3. Model autoryzacji (RBAC)

System wykorzystuje model **RBAC (Role-Based Access Control)**.

### Role:

* Student
* Opiekun
* Administracja
* Instytucja

### Zasady:

* każdy użytkownik posiada przypisaną rolę
* dostęp do danych i funkcji zależy od roli
* użytkownik widzi tylko dane, do których ma uprawnienia

---

## 4. Workflow i stany dokumentów

Dokumenty przechodzą przez określone stany:

1. **Draft (Roboczy)** – edytowany przez studenta
2. **Submitted (Przesłany)** – oczekuje na weryfikację
3. **Needs Correction (Do poprawy)** – zwrócony przez opiekuna
4. **Approved (Zatwierdzony)** – zaakceptowany przez opiekuna
5. **Finalized (Zakończony)** – zatwierdzony przez administrację

---

## 5. Generowanie dokumentów PDF

System umożliwia generowanie oficjalnych dokumentów:

* każdy załącznik posiada szablon
* dane są automatycznie wstawiane do wzoru
* generowane pliki traktowane są jako „oryginały cyfrowe”

Możliwe rozszerzenia:

* podpis elektroniczny
* sumy kontrolne (integralność dokumentów)

---

## 6. Wymagania niefunkcjonalne

### 6.1 Bezpieczeństwo

* autoryzacja oparta na rolach (RBAC)
* izolacja danych między użytkownikami
* ochrona dostępu do dokumentów

---

### 6.2 Użyteczność

* interfejs typu „Serious UI” (formalny, uczelniany styl)
* czytelne formularze
* wsparcie dla urządzeń mobilnych

---

### 6.3 Wydajność

* generowanie pełnej paczki dokumentów PDF w czasie < 10 sekund
* szybkie ładowanie formularzy

---

### 6.4 Integralność danych

* brak możliwości edycji po zatwierdzeniu
* spójność danych między formularzami
* powiązanie dziennika (załącznik 6) ze sprawozdaniem (załącznik 7)

---

## 7. Struktura danych (ogólnie)

System przechowuje:

* użytkowników i role
* formularze (załączniki 1–9)
* wpisy dziennika praktyk
* statusy dokumentów
* komentarze i uwagi

---

## 8. Możliwości rozwoju

System może zostać rozszerzony o:

* ankietę studenta (załącznik 5)
* powiadomienia e-mail
* integrację z systemem uczelnianym
* panel raportowy dla administracji

---

## 9. Uwagi końcowe

* Architektura została zaprojektowana w sposób skalowalny i modularny
* System może być rozwijany etapami (zgodnie z MoSCoW)
* Dokument stanowi podstawę do implementacji technicznej
