# 🚀 System Praktyk Zawodowych - Quick Start

## Zainstalowana infrastruktura

✅ **HTML Templates (Tailwind CSS)**
- `app/student/templates/base.html` - Layout z Tailwind CSS
- `app/student/templates/student/dashboard.html` - Dashboard studenta z podsumowaniem praktyk

✅ **Email Templates (Flask-Mail)**
- `app/templates/email/document_submitted.html`
- `app/templates/email/mentor_review_pending.html`
- `app/templates/email/document_approved.html`
- `app/templates/email/document_rejected.html`
- `app/templates/email/director_final_approval.html`

✅ **Email Service**
- `app/services/email_service.py` - Asynchroniczny dispatcher powiadomień
- Integracja: zaimplementuj w `app/student/routes.py` i `app/opiekun/routes.py`

✅ **PDF Generation**
- `app/services/pdf_service.py` - WeasyPrint integracja
- Funkcje dla wszystkich 8 załączników

✅ **Mentor Routes (Opiekun)**
- `app/opiekun/routes.py` - Kompletny blueprint z przeglądem, zatwierdzaniem, weryfikacją efektów
- `app/opiekun/templates/opiekun/dashboard.html` - Dashboard opiekuna
- `app/opiekun/templates/opiekun/review_document.html` - Przegląd dokumentu

✅ **REST API**
- `app/api/internships.py` - Endpointy praktyk (GET, PUT, stats)
- `app/api/documents.py` - Endpointy dokumentów (GET, PATCH approve/reject)
- `app/api/diary.py` - Endpointy dziennika praktyk (GET, POST, DELETE)
- `app/api/learning_outcomes.py` - Endpointy efektów nauczania (GET, POST, PATCH verify)
- `app/api/admin.py` - Endpointy administracyjne (statystyki, raporty)

✅ **Pytest Tests**
- `tests/conftest.py` - Fixtures (student, mentor, admin users, internships, documents)
- `tests/test_permissions.py` - Testy dostępu i RBAC
- `tests/test_api.py` - Testy REST API
- `tests/test_routes.py` - Testy HTML routes
- `pytest.ini` - Konfiguracja pytest

---

## Uruchomienie

### 1. Instalacja zależności
```bash
pip install -r requirements.txt
```

### 2. Inicjalizacja bazy danych
```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
>>>     db.create_all()
>>> exit()
```

### 3. Uruchomienie aplikacji
```bash
python run.py
```

Aplikacja dostępna: `http://localhost:5000`

### 4. Uruchomienie testów
```bash
# Wszystkie testy
pytest

# Tylko permission tests
pytest tests/test_permissions.py -v

# Tylko API tests
pytest tests/test_api.py -v

# Tylko routes tests
pytest tests/test_routes.py -v

# Pokrycie kodu
pytest --cov=app --cov-report=html
```

---

## API Endpoints (REST)

### Praktyki
```
GET    /api/internships              # List (role-filtered)
GET    /api/internship/<id>          # Details
PUT    /api/internship/<id>          # Update
GET    /api/internship/<id>/stats    # Statistics
```

### Dokumenty
```
GET    /api/documents                # List (filtered)
GET    /api/documents?status=draft   # Filter by status
GET    /api/document/<id>            # Details
PATCH  /api/document/<id>/approve    # Approve
PATCH  /api/document/<id>/reject     # Reject with comments
```

### Dziennik
```
GET    /api/diary-entries?internship_id=1  # List
POST   /api/diary-entry                    # Create
DELETE /api/diary-entry/<id>               # Delete
```

### Efekty Nauczania
```
GET    /api/learning-outcomes?internship_id=1  # List
POST   /api/learning-outcome                   # Create
PATCH  /api/learning-outcome/<id>/verify       # Verify (mentor)
PATCH  /api/learning-outcome/<id>/mark-achieved # Mark (student)
```

### Admin
```
GET    /api/dashboard-stats                # System statistics
GET    /api/internships/status/<status>    # Filter by status
GET    /api/documents/status/<status>      # Filter by status
GET    /api/reports/monthly                # Monthly report
```

---

## HTML Routes

### Student
```
GET  /student/dashboard                    # Dashboard
GET  /student/internship/<id>              # View details
POST /student/internship/<id>/attachment   # Submit document
GET  /student/internship/<id>/diary/add    # Add diary entry
```

### Mentor (Opiekun)
```
GET  /opiekun/dashboard                    # Dashboard
GET  /opiekun/internship/<id>              # View student
GET  /opiekun/document/<id>/review         # Review document
POST /opiekun/document/<id>/review         # Approve/Reject
POST /opiekun/learning-outcome/<id>/verify # Verify outcome
```

---

## Testy - Pokrycie

Zaimplementowane testy sprawdzają:

✅ **RBAC (Role-Based Access Control)**
- Student widzi tylko swoje praktyki
- Mentor widzi studentów, którym przydzielono
- Admin widzi wszystko
- Protokół (Attachment 8) dostępny tylko dla staff/admin

✅ **API Endpoints**
- GET/PUT internships z filtrowaniem po roli
- GET/POST/PATCH documents
- GET/POST diary entries
- GET/POST/PATCH learning outcomes
- Admin statistics i reports

✅ **HTML Routes**
- Student dashboard i szczegóły praktyki
- Mentor dashboard i przegląd dokumentów
- Zatwierdzanie/odrzucanie z komentarzami
- Weryfikacja efektów nauczania

✅ **Obsługa Błędów**
- 404 dla nieznanych zasobów
- 403 dla braku dostępu
- 400 dla nieprawidłowych danych
- Walidacja formularzy WTForms

---

## To zrobić (następne kroki)

1. **Integracja Email** - Podłączyć email_service do routes:
   - `app/student/routes.py` - wysłać emaile przy zmianie statusu dokumentu
   - `app/opiekun/routes.py` - wysłać potwierdzenie zatwierdzen

2. **PDF Generation** - Podłączyć pdf_service:
   - Create `/student/document/<id>/preview` route
   - Create `/student/document/<id>/download` route
   - Implement PDF templates w `app/templates/pdf/`

3. **Admin/Dyrekcja Routes** - Kompletna implementacja:
   - Dashboard z najnowszymi praktykami
   - Zarządzanie użytkownikami
   - Raporting i statystyki
   - Zatwierdzanie protokołów (Attachment 8)

4. **Frontend Enhancements**:
   - View internship template dla studenta
   - Attachment form templates (Attachment 1, 6, 7 itd.)
   - Admin dashboard z chartami
   - Mobile-responsive design

5. **Deployment**:
   - Konfiguracja producji (gunicorn, nginx)
   - Environment variables (.env production)
   - Database migration (SQLite → PostgreSQL)
   - CI/CD pipeline

---

## Struktura Plików

```
app/
├── api/                 # REST API blueprint
│   ├── __init__.py
│   ├── internships.py
│   ├── documents.py
│   ├── diary.py
│   ├── learning_outcomes.py
│   └── admin.py
├── opiekun/            # Mentor routes
│   ├── __init__.py
│   ├── routes.py
│   └── templates/
│       └── opiekun/
│           ├── dashboard.html
│           └── review_document.html
├── services/           # Business logic
│   ├── __init__.py
│   ├── email_service.py   # Email notifications
│   └── pdf_service.py     # PDF generation
├── student/
│   ├── routes.py
│   └── templates/
│       ├── base.html      # Tailwind CSS layout
│       └── student/
│           └── dashboard.html
├── templates/
│   └── email/           # Email templates
│       ├── document_submitted.html
│       ├── mentor_review_pending.html
│       ├── document_approved.html
│       ├── document_rejected.html
│       └── director_final_approval.html
tests/
├── conftest.py         # Pytest fixtures
├── test_permissions.py # RBAC tests
├── test_api.py        # API endpoint tests
└── test_routes.py     # HTML route tests
```

---

## Test Users (do testowania)

```
Student:
  Email: student@test.com
  Password: password123
  Role: student

Mentor:
  Email: mentor@test.com
  Password: password123
  Role: opiekun

Admin:
  Email: admin@test.com
  Password: password123
  Role: admin
```

---

**System gotowy do dalszego rozwijania! 🎉**
