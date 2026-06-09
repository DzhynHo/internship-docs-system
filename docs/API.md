# REST API - Endpointy i Dokumentacja

## 1. Autentykacja

### POST /auth/login
Logowanie poprzez Microsoft Azure AD

```
Request:
POST /auth/login
Content-Type: application/json

{
  "email": "student@uczelnia.pl",
  "password": "***" (lub OAuth redirect)
}

Response: 200 OK
{
  "user": {
    "id": 1,
    "email": "student@uczelnia.pl",
    "role": "student",
    "full_name": "Jan Kowalski"
  },
  "token": "eyJhbGciOiJIUzI1NiIs..." (JWT opcjonalnie)
}
```

### GET /auth/logout
```
Response: 302 Redirect → /auth/login
```

---

## 2. Internships (Praktyki)

### GET /api/internships
Pobranie listy praktyk (w zależności od roli)

```
Request:
GET /api/internships
Authorization: Bearer <token>

Response: 200 OK
{
  "internships": [
    {
      "id": 1,
      "student_id": 5,
      "student_name": "Jan Kowalski",
      "mentor_id": 10,
      "mentor_name": "Prof. Anna Nowak",
      "company_name": "TechCorp Sp. z o.o.",
      "start_date": "2024-09-01",
      "end_date": "2024-12-31",
      "status": "active",
      "total_hours": 480,
      "completion_percent": 43,
      "created_at": "2024-08-15"
    }
  ],
  "total": 1
}
```

**Role-based filtering:**
- `student`: Zwraca tylko swoje praktyki
- `opiekun`: Zwraca praktyki swoich przypisanych studentów
- `staff`, `admin`: Wszystkie praktyki

---

### POST /api/internships
Utworzenie nowej praktyki (Admin tylko)

```
Request:
POST /api/internships
Authorization: Bearer <token>
Content-Type: application/json

{
  "student_id": 5,
  "mentor_id": 10,
  "company_name": "TechCorp Sp. z o.o.",
  "start_date": "2024-09-01",
  "end_date": "2024-12-31",
  "total_hours": 480
}

Response: 201 Created
{
  "id": 1,
  "status": "active",
  "message": "Praktyka utworzona"
}
```

---

### GET /api/internships/{id}
Pobranie szczegółów praktyki

```
Response: 200 OK
{
  "id": 1,
  "student": {
    "id": 5,
    "name": "Jan Kowalski",
    "index_number": "123456"
  },
  "mentor": {
    "id": 10,
    "name": "Prof. Anna Nowak"
  },
  "company_name": "TechCorp",
  "start_date": "2024-09-01",
  "end_date": "2024-12-31",
  "status": "active",
  "documents": [
    {
      "attachment_id": 1,
      "name": "Porozumienie (załącznik 1)",
      "status": "approved",
      "completed_at": "2024-08-20"
    },
    {
      "attachment_id": 6,
      "name": "Dziennik praktyki (załącznik 6)",
      "status": "in_progress",
      "entries": 18
    }
  ]
}
```

---

## 3. Documents (Dokumenty/Formularze)

### POST /api/documents
Utworzenie/przesłanie dokumentu

```
Request:
POST /api/documents
Authorization: Bearer <token>
Content-Type: application/json

{
  "internship_id": 1,
  "attachment_id": 1,  // Załącznik 1 = Porozumienie
  "data": {
    "student_first_name": "Jan",
    "student_last_name": "Kowalski",
    "index_number": "123456",
    "email": "jan@student.uczelnia.pl",
    "year_of_study": 3,
    "field_of_study": "Informatyka",
    "company_name": "TechCorp",
    "company_address": "ul. Testowa 123, 00-000 Warszawa",
    "mentor_name": "Prof. Anna Nowak",
    "mentor_phone": "+48123456789",
    "mentor_email": "anna.nowak@uczelnia.pl",
    "start_date": "2024-09-01",
    "end_date": "2024-12-31",
    "total_hours": 480,
    "job_description": "Programowanie aplikacji webowych..."
  }
}

Response: 201 Created
{
  "id": 123,
  "attachment_id": 1,
  "status": "draft",
  "created_at": "2024-08-15T10:30:00Z",
  "message": "Dokument zapisany jako draft"
}
```

---

### GET /api/documents/{id}
Pobranie dokumentu

```
Response: 200 OK
{
  "id": 123,
  "attachment_id": 1,
  "internship_id": 1,
  "status": "draft",
  "data": { ... },
  "created_at": "2024-08-15",
  "updated_at": "2024-08-15",
  "created_by": 5,
  "reviewer": null,
  "comments": []
}
```

---

### PATCH /api/documents/{id}
Edycja dokumentu (Student)

```
Request:
PATCH /api/documents/123
Authorization: Bearer <token>
Content-Type: application/json

{
  "data": {
    "student_first_name": "Jan",
    "student_last_name": "Kowalski",
    // ... zmienione pola
  }
}

Response: 200 OK
{
  "id": 123,
  "status": "draft",
  "message": "Dokument zaktualizowany",
  "updated_at": "2024-08-15T11:00:00Z"
}
```

---

### POST /api/documents/{id}/submit
Przesłanie dokumentu (Student → Opiekun)

```
Request:
POST /api/documents/123/submit
Authorization: Bearer <token>

Response: 200 OK
{
  "id": 123,
  "status": "submitted",
  "message": "Dokument wysłany do przeglądu",
  "notification_sent_to": "prof.nowak@uczelnia.pl"
}
```

---

### PATCH /api/documents/{id}/comment
Dodanie komentarza (Opiekun/Admin)

```
Request:
PATCH /api/documents/123/comment
Authorization: Bearer <token>
Content-Type: application/json

{
  "comment": "Proszę poprawić opis stanowiska, bardziej szczegółowo",
  "status": "pending_revision"  // lub "approved_by_mentor"
}

Response: 200 OK
{
  "id": 123,
  "status": "pending_revision",
  "comments": [
    {
      "id": 1,
      "author": "Prof. Anna Nowak",
      "text": "Proszę poprawić...",
      "created_at": "2024-08-15T12:00:00Z"
    }
  ]
}
```

---

### PATCH /api/documents/{id}/approve
Zatwierdzenie dokumentu (Opiekun/Admin)

```
Request:
PATCH /api/documents/123/approve
Authorization: Bearer <token>
Content-Type: application/json

{
  "comment": "Zatwierdzone",
  "approval_level": "mentor"  // "mentor" lub "director"
}

Response: 200 OK
{
  "id": 123,
  "status": "approved_by_mentor",
  "approved_by": 10,
  "approved_at": "2024-08-15T12:30:00Z"
}
```

---

### DELETE /api/documents/{id}
Usunięcie dokumentu (tylko draft, student)

```
Request:
DELETE /api/documents/123
Authorization: Bearer <token>

Response: 204 No Content
```

---

## 4. Learning Outcomes (Efekty Nauczania)

### GET /api/internships/{internship_id}/learning-outcomes
Lista efektów praktyki

```
Response: 200 OK
{
  "learning_outcomes": [
    {
      "id": 1,
      "internship_id": 1,
      "outcome_text": "Umiejętność tworzenia aplikacji webowych w technologii X",
      "achieved_date": "2024-09-15",
      "status": "achieved",
      "evidence_source": "Dziennik praktyki, dni 3-5"
    },
    {
      "id": 2,
      "internship_id": 1,
      "outcome_text": "Umiejętność pracy w zespole",
      "achieved_date": null,
      "status": "planned",
      "evidence_source": null
    }
  ]
}
```

---

### POST /api/internships/{internship_id}/learning-outcomes
Dodanie efektu (Student)

```
Request:
POST /api/internships/1/learning-outcomes
Authorization: Bearer <token>
Content-Type: application/json

{
  "outcome_text": "Umiejętność tworzenia API REST",
  "status": "planned"
}

Response: 201 Created
{
  "id": 3,
  "outcome_text": "Umiejętność tworzenia API REST",
  "status": "planned"
}
```

---

### PATCH /api/learning-outcomes/{id}/verify
Weryfikacja efektu przez opiekuna

```
Request:
PATCH /api/learning-outcomes/1/verify
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "achieved",
  "achieved_date": "2024-09-15",
  "evidence_source": "Dziennik praktyki nr 3-5"
}

Response: 200 OK
{
  "id": 1,
  "status": "achieved",
  "verified_by": 10,
  "verified_at": "2024-09-15"
}
```

---

## 5. Diary Entries (Wpisy Dziennika)

### GET /api/internships/{internship_id}/diary-entries
Lista wpisów dziennika

```
Response: 200 OK
{
  "diary_entries": [
    {
      "id": 1,
      "date": "2024-09-01",
      "start_time": "08:00",
      "end_time": "16:00",
      "hours_worked": 8,
      "description": "Zapoznanie się z systemem...",
      "learning_outcomes": [1, 2]
    }
  ],
  "total_hours": 156,
  "expected_hours": 480,
  "completion_percent": 32.5
}
```

---

### POST /api/internships/{internship_id}/diary-entries
Dodanie wpisu do dziennika (Student)

```
Request:
POST /api/internships/1/diary-entries
Authorization: Bearer <token>
Content-Type: application/json

{
  "date": "2024-09-01",
  "start_time": "08:00",
  "end_time": "16:00",
  "description": "Zapoznanie się z systemem, training ...",
  "learning_outcomes": [1, 2]
}

Response: 201 Created
{
  "id": 1,
  "date": "2024-09-01",
  "hours_worked": 8,
  "message": "Wpis dodany"
}
```

---

### PATCH /api/diary-entries/{id}
Edycja wpisu (Student)

```
Response: 200 OK
{
  "id": 1,
  "message": "Wpis zaktualizowany"
}
```

---

### DELETE /api/diary-entries/{id}
Usunięcie wpisu (Student, tylko tego samego dnia)

```
Response: 204 No Content
```

---

## 6. Reports (Raporty)

### GET /api/reports/internship-summary
Raport podsumowujący praktykę (dla Admin/Staff)

```
Request:
GET /api/reports/internship-summary?internship_id=1

Response: 200 OK
{
  "student_name": "Jan Kowalski",
  "company_name": "TechCorp",
  "period": "2024-09-01 do 2024-12-31",
  "total_hours": 480,
  "documents_status": {
    "attachment_1": "approved",
    "attachment_3": "approved",
    "attachment_6": "in_progress (18/30 dni)",
    "attachment_7": "draft",
    "attachment_8": "generated"
  },
  "learning_outcomes_achieved": 7,
  "learning_outcomes_total": 10,
  "status": "active"
}
```

---

### GET /api/reports/generate-protocol
Generowanie Protokołu Egzaminu PDF (tylko Admin)

```
Request:
GET /api/reports/generate-protocol?internship_id=1

Response: 200 OK + PDF Binary
Content-Type: application/pdf
Content-Disposition: attachment; filename="Protokol_Jan_Kowalski_2024.pdf"

[Binary PDF Data]
```

---

## 7. Error Handling

### 400 Bad Request
```json
{
  "error": "Validation failed",
  "details": {
    "email": "Invalid email format",
    "index_number": "Must be 6-8 digits"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required",
  "message": "Please log in"
}
```

### 403 Forbidden
```json
{
  "error": "Access denied",
  "message": "Student cannot approve documents"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found",
  "resource": "Internship with id 999"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "Please contact support"
}
```

---

## 8. Status Codes Podsumowanie

| Kod | Znaczenie |
|-----|-----------|
| 200 | OK - operacja udana |
| 201 | Created - nowy zasób utworzony |
| 204 | No Content - usunięcie udane |
| 400 | Bad Request - błąd walidacji |
| 401 | Unauthorized - brak autentykacji |
| 403 | Forbidden - brak uprawnień |
| 404 | Not Found - zasób nie istnieje |
| 500 | Server Error - błąd serwera |

---

## 9. Pagination (opcjonalnie)

```
Request:
GET /api/internships?page=1&per_page=10&sort=created_at&order=desc

Response:
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 45,
    "pages": 5
  },
  "links": {
    "first": "/api/internships?page=1",
    "prev": null,
    "next": "/api/internships?page=2",
    "last": "/api/internships?page=5"
  }
}
```

---

## 10. Rate Limiting (opcjonalnie)

```
Response Headers:
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1692532800
```

---

**Ostatnia aktualizacja**: 2026-05-24  
**Wersja**: 1.0 - REST API
