# Specyfikacja wymagań

## 1. Wprowadzenie

Dokument opisuje wymagania funkcjonalne i ich priorytety dla systemu zarządzania dokumentacją praktyk studenckich (*ePraktyki*).

System wspiera proces od uzupełnienia dokumentów przez studenta, przez weryfikację opiekuna, aż do zatwierdzenia przez administrację.

---

## 2. Wymagania funkcjonalne

### F01 – Zarządzanie załącznikami

**Opis:**
System umożliwia każdemu użytkownikowi dostęp do odpowiednich formularzy (załączniki 1–9), zgodnie z jego rolą.

**Priorytet:** Must Have

---

### F02 – Formularz dziennika praktyk

**Opis:**
System umożliwia studentowi wypełnianie dziennika praktyk (załącznik 6) w formie dynamicznej tabeli.

**Priorytet:** Must Have

---

### F03 – Korekta przez opiekuna

**Opis:**
Opiekun ma możliwość edytowania i poprawiania wpisów studenta w celu usprawnienia procesu weryfikacji.

**Priorytet:** Should Have

---

### F04 – Blokada edycji po przesłaniu

**Opis:**
Po przesłaniu dokumentów do weryfikacji system blokuje możliwość dalszej edycji przez studenta.

**Priorytet:** Must Have

---

### F05 – Walidacja sprawozdania

**Opis:**
System ogranicza długość opisu w sprawozdaniu (załącznik 7) do jednego zdania na efekt uczenia się.

**Priorytet:** Could Have

---

### F06 – Generowanie dokumentów PDF

**Opis:**
System generuje oficjalne dokumenty w formacie PDF zgodne z wymaganym wzorem uczelnianym.

**Priorytet:** Must Have

---

### F07 – Widok protokołu zaliczenia

**Opis:**
System umożliwia wgląd w protokół zaliczenia (załącznik 8) dla studenta, opiekuna oraz administracji.

**Priorytet:** Must Have

---

### F08 – Dane przykładowe (placeholdery)

**Opis:**
System udostępnia przykładowe dane w formularzach, aby ułatwić studentowi ich poprawne wypełnianie.

**Priorytet:** Could Have

---

## 3. Priorytety (MoSCoW)

### Must Have

* F01 – Zarządzanie załącznikami
* F02 – Formularz dziennika praktyk
* F04 – Blokada edycji po przesłaniu
* F06 – Generowanie PDF
* F07 – Widok protokołu

### Should Have

* F03 – Korekta przez opiekuna

### Could Have

* F05 – Walidacja sprawozdania
* F08 – Dane przykładowe

### Won’t Have (na tym etapie)

* Ankieta (załącznik 5 – do przyszłego wdrożenia)

---

## 4. Uwagi końcowe

* System powinien być rozwijany iteracyjnie, zaczynając od funkcji oznaczonych jako *Must Have*.
* Funkcje *Should Have* i *Could Have* mogą zostać wdrożone w kolejnych etapach projektu.
* Dokument stanowi podstawę do dalszego projektowania architektury systemu.
