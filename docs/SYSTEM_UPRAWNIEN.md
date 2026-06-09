# System Uprawnień Aplikacji Praktyk Zawodowych

## 1. Role w Systemie

### Student (role = "student")
- **Email domain**: `*.student@uczelnia.pl` (opcjonalnie)
- **Uprawnienia**:
  - ✅ Przeglądanie własnego profilu
  - ✅ Przeglądanie własnych praktyk
  - ✅ Wypełnianie formularzy (załączniki: 1, 2, 2a, 3, 4, 4b, 5, 6, 7, 7a, 9)
  - ✅ Przesyłanie dokumentów
  - ✅ Wgląd do komentarzy opiekuna
  - ✅ Pobieranie swoich dokumentów (PDF)
  - ❌ Przegląd innych studentów
  - ❌ Zatwierdzanie dokumentów
  - ❌ Wgląd do Protokołu (załącznik 8)

### Opiekun (role = "opiekun")
- **Email domain**: Pracownicy uczelni z rolą mentora
- **Uprawnienia**:
  - ✅ Przeglądanie profilu
  - ✅ Wgląd do swoich przypisanych studentów
  - ✅ Przeglądanie dokumentów swoich studentów
  - ✅ Dodawanie komentarzy do dokumentów
  - ✅ Zatwierdzanie dokumentów (draft → approved)
  - ✅ Oznaaczanie efektów nauczania jako "osiągnięte"
  - ✅ Generowanie raportu potwierdzenia efektów (załącznik 4a)
  - ❌ Przegląd studentów innych opiekunów
  - ❌ Finalne zatwierdzenie (robi to Dyrekcja)
  - ❌ Zamykanie praktyki
  - ❌ Generowanie Protokołu (załącznik 8)

### Sekretariat / Dziekanat (role = "staff")
- **Email domain**: Pracownicy uczelni
- **Uprawnienia**:
  - ✅ Wgląd do WSZYSTKICH praktyk
  - ✅ Filtrowanie i raportowanie
  - ✅ Wysyłanie powiadomień
  - ✅ Aktualizacja statusu
  - ✅ Pobieranie zbiorczych danych
  - ✅ Zarządzanie archiwum
  - ❌ Edycja danych studentów
  - ❌ Bezpośrednie zatwierdzanie (Dyrekcja)

### Dyrekcja / Admin (role = "admin")
- **Email domain**: Kierownictwo / Administratorzy
- **Uprawnienia**:
  - ✅ PEŁNY DOSTĘP do wszystkich danych
  - ✅ Zatwierdzanie/odrzucanie dokumentów
  - ✅ Zamykanie praktyk
  - ✅ Generowanie Protokołu (załącznik 8)
  - ✅ Zarządzanie użytkownikami (aktywacja, zmiana roli)
  - ✅ Generowanie raportów
  - ✅ Eksport danych do CSV/XLSX
  - ✅ Zarządzanie ustawieniami systemowymi

---

## 2. Macierz Uprawnień (RBAC)

| Operacja | Student | Opiekun | Sekretariat | Dyrekcja |
|----------|---------|---------|-------------|----------|
| **Wgląd do Internships** | Swoje | Swoich | Wszystkie | Wszystkie |
| **Edycja danych praktyki** | ❌ | ❌ | ❌ | ✅ |
| **Wypełnianie formularzy** | ✅ | ❌ | ❌ | ❌ |
| **Przesyłanie dokumentów** | ✅ | ❌ | ❌ | ❌ |
| **Komentowanie** | ❌ | ✅ | ✅ | ✅ |
| **Zatwierdzanie (level 1)** | ❌ | ✅ | ❌ | ❌ |
| **Zatwierdzanie (level 2)** | ❌ | ❌ | ❌ | ✅ |
| **Zamykanie praktyki** | ❌ | ❌ | ❌ | ✅ |
| **Generowanie Protokołu** | ❌ | ❌ | ❌ | ✅ |
| **Raportowanie** | ❌ | ❌ | ✅ | ✅ |
| **Zarządzanie użytkownikami** | ❌ | ❌ | ❌ | ✅ |

---

## 3. Uprawnienia do Dokumentów (por Załącznik)

| Załącznik | Student | Opiekun | Sekretariat | Dyrekcja | Notatki |
|-----------|---------|---------|-------------|----------|---------|
| Regulamin (Reg) | R | R | R | R | Czytaj tylko |
| Porozumienie (1) | RW | R | R | R | Student wypełnia |
| Program (2) | RW | R | R | R | Student wypełnia |
| Program & Harmonogram (2a) | RW | R | R | R | Student wypełnia |
| Karta Praktyki (3) | RW | R | R | R | Student wypełnia |
| Potwierdzenie Efektów (4) | RW | R | R | R | Student wypełnia |
| Potwierdzenie Uzyskania (4a) | R | RW | R | R | Opiekun generuje |
| Wniosek o Zaliczenie (4b) | RW | R | R | R | Student wypełnia |
| Ankieta (5) | RW | ❌ | R | R | Student wypełnia, brak przeglądu |
| Dziennik Praktyki (6) | RW | R | R | R | Student codziennie |
| Sprawozdanie (7) | RW | R | R | R | Student - 1 zdanie! |
| Sprawozdanie Niestacjonarne (7a) | RW | R | R | R | Jak (7) |
| Protokół Egzaminu (8) | ❌ | ❌ | R | RW | Tylko Dyrekcja & Sekretariat |
| Oświadczenie (9) | RW | ❌ | R | R | Student przesyła skan |

**Legenda**: 
- R = Odczyt
- RW = Odczyt + Zapis
- ❌ = Brak dostępu

---

## 4. Workflow Zatwierdzania

```
Status: draft
  ↓ (Student kliknie "Wyślij")
Status: submitted
  ↓ (Opiekun sprawdza)
  ├─→ Zatwierdzam (Level 1) → Status: approved_by_mentor
  │
  └─→ Mam uwagi → Status: pending_revision
      ↓ (Student poprawia)
      Status: submitted (znowu)

Status: approved_by_mentor
  ↓ (Czeka na Dyrekcję - tylko dla dokumentów wymagających 2-stopniowego zatwierdzenia)
Status: pending_director_approval
  ↓ (Dyrekcja zatwierdza)
  ├─→ Zatwierdzam (Final) → Status: approved
  │
  └─→ Mam uwagi → Status: pending_revision_admin
```

### Dokumenty z 1-stopniowym zatwierdzeniem (przez Opiekuna):
- Załącznik 1 (Porozumienie)
- Załącznik 3 (Karta Praktyki)
- Załącznik 4 (Potwierdzenie Efektów)
- Załącznik 6 (Dziennik)
- Załącznik 7 (Sprawozdanie)

### Dokumenty z 2-stopniowym zatwierdzeniem (Opiekun + Dyrekcja):
- Załącznik 4b (Wniosek o Zaliczenie)
- Załącznik 8 (Protokół - tworzy Dyrekcja)

---

## 5. Row-Level Security (RLS)

### Implementacja w Flask:

```python
# Decorator do sprawdzania dostępu na poziomie rekordu
@require_role("student", "opiekun", "staff", "admin")
@check_resource_access
def view_document(doc_id):
    doc = DocumentSubmission.query.get(doc_id)
    
    # Sprawdzenie uprawnień
    current_user = current_user
    
    if current_user.role == "student":
        # Student może przejrzeć TYLKO swoje dokumenty
        if doc.user_id != current_user.id:
            return abort(403)
    
    elif current_user.role == "opiekun":
        # Opiekun tylko swoich przypisanych studentów
        if doc.user.mentor_id != current_user.id:
            return abort(403)
    
    elif current_user.role == "staff":
        # Sekretariat widzi wszystko (R)
        pass
    
    elif current_user.role == "admin":
        # Admin pełny dostęp
        pass
    
    return render_template("view_doc.html", doc=doc)
```

---

## 6. Kontrola Dostępu w API

### GET /api/internships

```python
@api_bp.route('/internships', methods=['GET'])
@login_required
def get_internships():
    if current_user.role == "student":
        # Zwróć tylko swoje praktyki
        internships = Internship.query.filter_by(student_id=current_user.id).all()
    
    elif current_user.role == "opiekun":
        # Praktyki swoich studentów
        internships = Internship.query.filter_by(mentor_id=current_user.id).all()
    
    elif current_user.role in ["staff", "admin"]:
        # Wszystkie praktyki
        internships = Internship.query.all()
    
    return jsonify([i.to_dict() for i in internships])
```

---

## 7. Scenariusze Testowe

### Scenariusz 1: Student wypełnia praktykę
```
1. Student loguje się
2. Przeglądanie Dashboard: Moje praktyki
3. Klika na praktykę → Widok formularzy
4. Wypełnia Porozumienie (załącznik 1) → Status: draft
5. Kliknie "Wyślij" → Status: submitted
6. Opiekun widzi powiadomienie
7. Opiekun sprawdza → Zatwierdza → Status: approved_by_mentor
8. ✅ Student widzi: Zatwierdzono
```

### Scenariusz 2: Opiekun ma uwagi
```
1. Opiekun przeglądnie Sprawozdanie (załącznik 7)
2. Dodaje komentarz: "Za krótko, opisz bardziej"
3. Zmienia status na: pending_revision
4. Student widzi powiadomienie
5. Student edytuje dokument
6. Student wysyła znowu
7. Opiekun zatwierdza → approved_by_mentor
```

### Scenariusz 3: Protokół (Załącznik 8) - widoczność
```
1. Student loguje się
2. Przeglądanie Dashboard
3. ❌ NIE WIDZI Protokołu (załącznik 8)
4. Opiekun loguje się
5. ❌ NIE WIDZI Protokołu
6. Dyrekcja loguje się
7. ✅ WIDZI Protokół
8. Dyrekcja generuje Protokół PDF
9. Dyrekcja zatwierdza
10. Student & Opiekun nadal go nie widzą
```

---

## 8. Konfiguracja w `config.py`

```python
# Mapowanie domen email do ról
ROLE_DOMAIN_MAPPING = {
    "@student.uczelnia.pl": "student",
    "@uczelnia.pl": "staff",  # Default dla pracowników
    # Specjalni użytkownicy mogą mieć rolę ustawianą ręcznie
}

# Stały mapping dla administratorów
ADMIN_EMAILS = [
    "admin@uczelnia.pl",
    "rektor@uczelnia.pl",
]

MENTOR_EMAILS = {
    "prof.kowalski@uczelnia.pl": ["student123@uczelnia.pl", "student124@uczelnia.pl"],
    # Manualna konfiguracja przypisań
}
```

---

## 9. Audyt i Logging

Każda akcja powinna być logowana:

```python
def log_action(user_id, action, resource, details):
    """
    log_action(
        user_id=current_user.id,
        action="approve_document",
        resource="document_submission:123",
        details={"status": "approved_by_mentor", "comment": "OK"}
    )
    """
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details,
        timestamp=datetime.utcnow(),
        ip_address=request.remote_addr
    )
    db.session.add(audit_log)
    db.session.commit()
```

---

## 10. Testowanie Uprawnień

```bash
# Testy jednostkowe
pytest tests/test_permissions.py

# Testy integracyjne (Selenium/Cypress)
npm test
```

### Test Case:
```python
def test_student_cannot_view_other_student_internship():
    student1 = User(email="s1@student.uczelnia.pl", role="student")
    student2 = User(email="s2@student.uczelnia.pl", role="student")
    internship = Internship(student=student1)
    
    with app.test_client() as client:
        client.post('/auth/login', data={'user': student2})
        response = client.get(f'/student/internship/{internship.id}')
        assert response.status_code == 403
```

---

**Ostatnia aktualizacja**: 2026-05-24  
**Wersja**: 1.0 - System Uprawnień
