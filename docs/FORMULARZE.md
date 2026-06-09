# Formularze i Załączniki - Szczegółowa Specyfikacja

## Przegląd Załączników

Wszystkie załączniki są powiązane z praktyką zawodową studenta. Student ma JEDNĄ aktywną praktykę naraz, do której przypisane są wszystkie dokumenty.

---

## 1. Regulamin Praktyki Zawodowej (Reg)

**Typ**: Dokument PDF (read-only)  
**Kto widzi**: Wszyscy (student, opiekun, sekretariat, dyrekcja)  
**Funkcja**: Edukacyjna - zapoznanie z regulaminem

### Szczegóły:
- PDF statyczny, przechowywany w `app/static/docs/`
- Przycisk "Pobierz PDF"
- Przycisk "Drukuj"
- Brak interakcji, brak formularza

### Interfejs:
```
┌─────────────────────────────────────┐
│ Regulamin Praktyki Zawodowej        │
├─────────────────────────────────────┤
│                                     │
│  [Podgląd PDF]                      │
│                                     │
│  📥 Pobierz PDF                     │
│  🖨️  Drukuj                          │
│                                     │
└─────────────────────────────────────┘
```

---

## 2. Porozumienie (Załącznik 1)

**Typ**: Formularz  
**Kto wypełnia**: Student  
**Kto zatwierdza**: Opiekun  
**Status workflow**: draft → submitted → approved_by_mentor

### Pola formularza:

| Pole | Typ | Obowiązkowe | Walidacja |
|------|-----|------------|-----------|
| Imię studenta | Text | ✅ | Tylko litery |
| Nazwisko studenta | Text | ✅ | Tylko litery |
| Nr indeksu | Text | ✅ | 6-8 cyfr |
| Email studenta | Email | ✅ | Format email |
| Rok studiów | Select | ✅ | 1-6 |
| Kierunek | Select | ✅ | Lista kierunków |
| Nazwa firmy | Text | ✅ | Min 3 znaki |
| Adres firmy | Text | ✅ | Min 10 znaków |
| Osoba odpowiedzialna (mentor) | Text | ✅ | Imię Nazwisko |
| Tel kontaktowy | Tel | ✅ | Format tel |
| Email firmy | Email | ✅ | Format email |
| Data początkowa | Date | ✅ | >= dzisiaj |
| Data końcowa | Date | ✅ | > Data początkowa |
| Liczba godzin | Number | ✅ | 100-600 |
| Opis stanowiska | Textarea | ✅ | 50-500 znaków |
| Potwierdzenie | Checkbox | ✅ | Musi być zaznaczony |

### Logika:
```python
class Attachment1Form(FlaskForm):
    student_first_name = StringField(validators=[DataRequired(), Length(1, 100)])
    student_last_name = StringField(validators=[DataRequired(), Length(1, 100)])
    index_number = StringField(validators=[DataRequired(), Regexp(r'^\d{6,8}$')])
    # ... więcej pól
    
    def validate_end_date(self, field):
        if field.data <= self.start_date.data:
            raise ValidationError("Data końcowa musi być po dacie początkowej")
```

### Podgląd PDF:
- Formularz zostaje automatycznie preformatowany w PDF
- Student może pobrać PDF przed wysłaniem
- Po zatwierdzeniu przez opiekuna → PDF "zatwierdzone" (np. z pieczęcią)

---

## 3. Program i Harmonogram (Załącznik 2a)

**Typ**: Formularz  
**Kto wypełnia**: Student  
**Kto zatwierdza**: Opiekun  
**Status workflow**: draft → submitted → approved_by_mentor

### Pola:

| Pole | Typ | Obowiązkowe | Notatki |
|------|-----|------------|---------|
| Tygodnie | Table (7 wierszy) | ✅ | Każdy tydzień |
| Dzień | Select | ✅ | Mon-Fri |
| Zadania na dzień | Textarea | ✅ | 50-300 znaków |
| Godziny | Number | ✅ | 6-8 |

### Interfejs (Edytor Tabel):
```
┌─────────────────────────────────────────────────┐
│ Program i Harmonogram Praktyki                  │
├──────┬───────┬──────────────────┬────────────────┤
│ Dz.  │ Data  │ Zadania          │ Godziny        │
├──────┼───────┼──────────────────┼────────────────┤
│ Pon  │ 01.09 │ [textarea]       │ [spinner] 8    │
│ Wto  │ 02.09 │ [textarea]       │ [spinner] 8    │
│ ...  │       │                  │                │
└──────┴───────┴──────────────────┴────────────────┘
```

---

## 4. Karta Praktyki (Załącznik 3)

**Typ**: Formularz  
**Kto wypełnia**: Student  
**Kto zatwierdza**: Opiekun  
**Status workflow**: draft → submitted → approved_by_mentor

### Pola:

| Pole | Typ | Obowiązkowe |
|------|-----|------------|
| Data rozpoczęcia | Date | ✅ |
| Data zakończenia | Date | ✅ |
| Nazwa stanowiska | Text | ✅ |
| Obowiązki | Textarea | ✅ |
| Zastosowane umiejętności | Textarea | ✅ |
| Umiejętności nabyte | Textarea | ✅ |
| Opinia opiekuna (auto-filled po zatwierdzeniu) | Textarea | ❌ |

### Notatki:
- Pola "Data" automatycznie pobierają z Porozumienia (Załącznik 1)
- "Opinia opiekuna" pojawia się po zatwierdzeniu przez opiekuna

---

## 5. Potwierdzenie Efektów Nauczania (Załącznik 4)

**Typ**: Formularz  
**Kto wypełnia**: Student (lista efektów)  
**Kto zatwierdza**: Opiekun  
**Status workflow**: draft → submitted → approved_by_mentor

### Pola:

| Pole | Typ | Obowiązkowe | Notatki |
|------|-----|------------|---------|
| Efekt nr | Number | ✅ | Auto 1-10 |
| Opis efektu | Textarea | ✅ | 50-300 znaków |
| Gdzie go osiągnąłem (np. dz. praktyki nr) | Text | ✅ | Odniesienie do dziennika |
| Status osiągnięcia | Select | ✅ | "Planowany", "Osiągnięty", "Weryfikowany" |

### Interfejs (Multiwierszowy):
```
┌──────────────────────────────────────────────────────┐
│ Potwierdzenie Efektów Nauczania                      │
├─────┬──────────────┬─────────────┬──────────────────┤
│ Nr  │ Opis efektu  │ Gdzie?      │ Status           │
├─────┼──────────────┼─────────────┼──────────────────┤
│ 1   │ [textarea]   │ Dzień 1-5   │ [Osiągnięty] ✓   │
│ 2   │ [textarea]   │ Dzień 6-10  │ [Osiągnięty] ✓   │
│ [+] │ Dodaj efekt  │             │                  │
└─────┴──────────────┴─────────────┴──────────────────┘
```

---

## 6. Potwierdzenie Uzyskania Efektów (Załącznik 4a)

**Typ**: Raport (auto-generated)  
**Kto generuje**: System (na podstawie Załącznika 4 + oceny opiekuna)  
**Kto widzi**: Opiekun, Sekretariat, Dyrekcja

### Zawartość (auto):
- Imię/Nazwisko studenta
- Nr indeksu
- Lista efektów z Załącznika 4
- Ocena: "Osiągnięty" / "Nie osiągnięty" / "Weryfikowany"
- Notatki opiekuna
- Data wygenerowania
- Podpis opiekuna (cyfrowy)

### Interfejs:
```
Raport auto-generuje się, gdy opiekun zatwierdzi Załącznik 4.
```

---

## 7. Wniosek o Zaliczenie Efektów (Załącznik 4b)

**Typ**: Formularz  
**Kto wypełnia**: Student (opcjonalnie)  
**Kto zatwierdza**: Opiekun + Dyrekcja (2-stopniowe)  
**Status workflow**: draft → submitted → approved_by_mentor → approved_by_director

### Pola:

| Pole | Typ | Obowiązkowe | Notatki |
|------|-----|------------|---------|
| Podstawa wniosku | Select | ✅ | "Praca zawodowa", "Staż", "Działalność" |
| Opis pracy | Textarea | ✅ | 100-1000 znaków |
| Dokument uzasadniający | File | ✅ | PDF/DOC |
| Liczba miesięcy | Number | ✅ | 1-12 |
| Prośba o zaliczenie | Checkbox | ✅ | Zgoda |

### Logika:
- Wniosek wymaga zatwierdzenia przez OPIEKUNA
- Następnie DYREKCJA zatwierdza/odrzuca
- Jeśli zatwierdzone → Status: "zaliczono"

---

## 8. Kwestionariusz Ankiety (Załącznik 5)

**Typ**: Formularz (ewaluacja)  
**Kto wypełnia**: Student  
**Kto sprawdza**: NIE (brak przeglądu, bezpośrednio zbiera się statystyki)  
**Status workflow**: draft → submitted (brak zatwierdzania)

### Pola:

| Pytanie | Typ | Skala |
|---------|-----|-------|
| Czy środowisko pracy było przyjazne? | Radio | 1-5 |
| Czy nauczyłeś się nowych umiejętności? | Radio | 1-5 |
| Czy mentor wspierał Cię w pracy? | Radio | 1-5 |
| Czy polecasz tę firmę? | Radio | 1-5 |
| Uwagi ogólne | Textarea | Max 500 znaków |

### Notatki:
- Ankieta jest **anonimowa** (nie zbiera się danych studenta w wynikach)
- Student wysyła raz i nie może edytować
- Wyniki widzi TYLKO Dyrekcja (raportowanie)

---

## 9. Dziennik Praktyki (Załącznik 6)

**Typ**: Formularz (wielowpisowy - logi codzienne)  
**Kto wypełnia**: Student (codziennie)  
**Kto sprawdza**: Opiekun (podsumowanie tygodniowe)  
**Status workflow**: draft → submitted → approved_by_mentor

### Struktura wpisów:

| Pole | Typ | Obowiązkowe | Walidacja |
|------|-----|------------|-----------|
| Data | Date | ✅ | Auto dzisiaj |
| Godziny pracy | Time (range) | ✅ | np. 08:00-16:00 |
| Opis czynności | Textarea | ✅ | 50-500 znaków |
| Efekty uczenia | Select (multi) | ❌ | Odniesienie do efektów |

### Interfejs (Timeline):
```
┌──────────────────────────────────────────────────┐
│ Dziennik Praktyki (Załącznik 6)                  │
├──────────────────────────────────────────────────┤
│                                                  │
│ 📅 Monday, 01.09.2024                            │
│    ├─ 08:00-16:00 (8h)                           │
│    └─ Opis: Zapoznanie się z systemem...        │
│                                                  │
│ 📅 Tuesday, 02.09.2024                           │
│    ├─ 08:00-16:00 (8h)                           │
│    └─ Opis: Udział w spotkaniu zespołu...       │
│                                                  │
│ [+ Dodaj dzisiejszy wpis]                       │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Logika:
```python
class DiaryEntry(db.Model):
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    
    @property
    def hours_worked(self):
        delta = datetime.combine(date.today(), self.end_time) - \
                datetime.combine(date.today(), self.start_time)
        return delta.total_seconds() / 3600
    
    def validate_hours(self):
        if self.hours_worked < 1 or self.hours_worked > 10:
            raise ValueError("Dzień pracy: 1-10 godzin")
```

---

## 10. Sprawozdanie z Praktyki (Załącznik 7) ⭐ KLUCZOWE

**Typ**: Formularz (specjalny!)  
**Kto wypełnia**: Student  
**Kto zatwierdza**: Opiekun  
**Status workflow**: draft → submitted → approved_by_mentor

### 🔴 WYMAGANIE: MAX JEDNO ZDANIE (lub max 500 znaków)

### Pola:

| Pole | Typ | Obowiązkowe | Walidacja |
|------|-----|------------|-----------|
| Sprawozdanie | Textarea | ✅ | MAX 500 znaków, 1 zdanie! |
| Podpis cyfrowy (auto) | - | ✅ | Auto po zatwierdzeniu |

### Interfejs:
```
┌────────────────────────────────────────────────────┐
│ Sprawozdanie z Praktyki Zawodowej                  │
├────────────────────────────────────────────────────┤
│                                                    │
│ Wpisz sprawozdanie (MAX 1 ZDANIE, 500 znaków):   │
│                                                    │
│ ┌──────────────────────────────────────────────┐  │
│ │ [Textarea z licznikiem znaków]               │  │
│ │ 123 / 500 znaków                             │  │
│ │ ⚠️  BŁĄD: Więcej niż 1 zdanie!               │  │
│ └──────────────────────────────────────────────┘  │
│                                                    │
│ [Podgląd PDF] [Wyślij] [Zapisz]                   │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Logika walidacji:
```python
def validate_report(text: str) -> tuple[bool, str]:
    """
    Sprawdzenie:
    1. Min 50 znaków
    2. Max 500 znaków
    3. Dokładnie 1 zdanie (1 punkt, wykrzyknik, pytajnik)
    """
    if not text:
        return False, "Sprawozdanie jest wymagane"
    
    if len(text) < 50:
        return False, f"Min. 50 znaków ({len(text)}/50)"
    
    if len(text) > 500:
        return False, f"Max 500 znaków ({len(text)}/500)"
    
    # Liczba zdań
    sentences = re.split(r'[.!?]+', text.strip())
    sentence_count = len([s for s in sentences if s.strip()])
    
    if sentence_count > 1:
        return False, f"Tylko 1 zdanie! Znalezione: {sentence_count}"
    
    return True, "✓ Sprawozdanie poprawne"
```

---

## 11. Sprawozdanie - Studia Niestacjonarne (Załącznik 7a)

**Typ**: Identyczne jak Załącznik 7  
**Dla**: Studentów niestacjonarnych pracujących jednocześnie

---

## 12. Protokół Egzaminu (Załącznik 8) 🔒 OGRANICZONY DOSTĘP

**Typ**: Dokument (generowany przez Dyrekcję)  
**Kto generuje**: Dyrekcja  
**Kto widzi**: TYLKO Dyrekcja i Sekretariat  
**Student widzi**: ❌ NIE

### Pola (wypełnia Dyrekcja):

| Pole | Typ | Obowiązkowe |
|------|-----|------------|
| Data egzaminu | Date | ✅ |
| Ocena | Select | ✅ |
| Uwagi | Textarea | ❌ |
| Podpis egzaminatora | Digital Sig | ✅ |

### Logika dostępu:
```python
@app.route('/documents/<doc_id>')
@login_required
def view_document(doc_id):
    doc = Document.query.get(doc_id)
    
    # Sprawdź czy to Protokół (załącznik 8)
    if doc.attachment.name == "Protokół egzaminu praktyki zawodowej (załącznik 8)":
        if current_user.role not in ["admin", "staff"]:
            return abort(403, "Brak dostępu do Protokołu")
    
    return render_template("view_doc.html", doc=doc)
```

---

## 13. Oświadczenie Instytucji (Załącznik 9)

**Typ**: Skan dokumentu (PDF/JPG)  
**Kto przesyła**: Student  
**Kto sprawdza**: Brak przeglądu (upload + archiwizacja)  
**Status workflow**: draft → submitted

### Pola:

| Pole | Typ | Obowiązkowe | Format |
|------|-----|------------|--------|
| Plik dokumentu | File | ✅ | PDF, JPG, PNG (max 5MB) |

### Notatki:
- **ORYGINAŁ**, nie skan
- Musi zawierać pieczęć instytucji
- System sprawdza, czy zawiera pieczęć (OCR?)
- Przechowywanie w `uploads/attachment_9/`

---

## 14. Powiązania między Załącznikami

```
Załącznik 1 (Porozumienie)
  ├─ Data początkowa + końcowa → Automatycznie do Załącznika 2a
  ├─ Dane firmy → Załącznik 3
  └─ Nr indeksu → Wszystkie pozostałe

Załącznik 3 (Karta praktyki)
  └─ Stanowisko → Załącznik 4 (lista efektów)

Załącznik 4 (Efekty)
  ├─ Opiekun zatwierdza → Auto-generuje Załącznik 4a
  └─ Student odnosi do dziennika → Załącznik 6 (linking)

Załącznik 6 (Dziennik)
  └─ Podsumowanie → Załącznik 7 (sprawozdanie)

Załącznik 8 (Protokół)
  ├─ Generuje Dyrekcja po zatwierdzeniu Załącznika 7
  └─ Kto widzi: TYLKO Dyrekcja + Sekretariat
```

---

## 15. Procent Wypełnienia

System powinien pokazywać postęp:
```
Praktyka #1: 43% ukończona
├─ ✅ Załącznik 1 (Porozumienie) - approved
├─ ✅ Załącznik 3 (Karta praktyki) - approved
├─ 🔄 Załącznik 6 (Dziennik) - 18/30 dni wpisanych
├─ ⏳ Załącznik 7 (Sprawozdanie) - draft
└─ ❌ Załącznik 8 (Protokół) - brak dostępu
```

---

**Ostatnia aktualizacja**: 2026-05-24  
**Wersja**: 1.0 - Specyfikacja Formularzy
