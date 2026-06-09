"""
Modele dla praktyk zawodowych i efektów nauczania.
"""

from app import db
from datetime import datetime


class Internship(db.Model):
    """Model reprezentujący praktykę zawodową studenta."""
    
    __tablename__ = "internships"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    
    # Informacje o praktyce
    company_name = db.Column(db.String(255), nullable=False)
    company_address = db.Column(db.String(500), nullable=True)
    company_phone = db.Column(db.String(20), nullable=True)
    company_email = db.Column(db.String(255), nullable=True)
    
    # Daty
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # Status i godziny
    status = db.Column(
        db.String(50), 
        nullable=False, 
        default="active"
    )  # active, completed, failed, cancelled
    total_hours = db.Column(db.Integer, nullable=False, default=480)  # Wymagane godziny
    
    # Dane do audytu
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    
    # Relacje
    student = db.relationship("User", foreign_keys=[student_id], backref="internships_as_student")
    mentor = db.relationship("User", foreign_keys=[mentor_id], backref="internships_as_mentor")
    learning_outcomes = db.relationship("LearningOutcome", backref="internship", cascade="all, delete-orphan")
    diary_entries = db.relationship("DiaryEntry", backref="internship", cascade="all, delete-orphan")
    documents = db.relationship(
        "DocumentSubmission",
        backref="internship",
        cascade="all, delete-orphan",
        foreign_keys="DocumentSubmission.internship_id"
    )
    
    def __repr__(self):
        return f"<Internship {self.student.full_name} @ {self.company_name}>"
    
    @property
    def total_hours_worked(self):
        """Suma wszystkich godzin z wpisy dziennika."""
        return sum(entry.hours_worked for entry in self.diary_entries)
    
    @property
    def completion_percent(self):
        """Procent realizacji praktyki (godziny)."""
        if self.total_hours == 0:
            return 0
        return min(100, int(self.total_hours_worked / self.total_hours * 100))
    
    @property
    def days_passed(self):
        """Liczba dni od rozpoczęcia."""
        if self.status == "completed":
            delta = self.end_date - self.start_date
        else:
            delta = datetime.now().date() - self.start_date
        return delta.days + 1
    
    def to_dict(self):
        """Konwersja do słownika JSON."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.full_name,
            "mentor_id": self.mentor_id,
            "mentor_name": self.mentor.full_name if self.mentor else None,
            "company_name": self.company_name,
            "company_address": self.company_address,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "status": self.status,
            "total_hours": self.total_hours,
            "total_hours_worked": self.total_hours_worked,
            "completion_percent": self.completion_percent,
            "created_at": self.created_at.isoformat(),
        }


class LearningOutcome(db.Model):
    """Model reprezentujący efekt nauczania osiągnięty w praktyce."""
    
    __tablename__ = "learning_outcomes"
    
    id = db.Column(db.Integer, primary_key=True)
    internship_id = db.Column(db.Integer, db.ForeignKey("internships.id"), nullable=False)
    
    # Zawartość
    outcome_text = db.Column(db.String(500), nullable=False)  # Opis efektu
    evidence_source = db.Column(db.String(500), nullable=True)  # Gdzie osiągnąłem (np. "Dziennik dzień 3-5")
    
    # Status
    status = db.Column(
        db.String(50),
        nullable=False,
        default="planned"
    )  # planned, achieved, verified
    
    # Daty
    achieved_date = db.Column(db.Date, nullable=True)  # Kiedy osiągnięty
    verified_date = db.Column(db.Date, nullable=True)  # Kiedy zweryfikowany
    verified_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # Kto zweryfikował (opiekun)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<LearningOutcome {self.id}: {self.status}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "internship_id": self.internship_id,
            "outcome_text": self.outcome_text,
            "evidence_source": self.evidence_source,
            "status": self.status,
            "achieved_date": self.achieved_date.isoformat() if self.achieved_date else None,
            "verified_date": self.verified_date.isoformat() if self.verified_date else None,
        }


class DiaryEntry(db.Model):
    """Model reprezentujący wpis w dzienniku praktyki."""
    
    __tablename__ = "diary_entries"
    
    id = db.Column(db.Integer, primary_key=True)
    internship_id = db.Column(db.Integer, db.ForeignKey("internships.id"), nullable=False)
    
    # Data i czas
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)  # np. 08:00
    end_time = db.Column(db.Time, nullable=False)    # np. 16:00
    
    # Zawartość
    description = db.Column(db.String(1000), nullable=False)  # Opis czynności (max 1000 znaków)
    
    # Powiązanie z efektami nauczania (ID z tabeli learning_outcomes)
    learning_outcomes_ids = db.Column(db.JSON, nullable=True, default=[])
    # Numer/numery efektów wpisywane ręcznie przez studenta (np. "E1, E2, E5")
    learning_outcome_numbers = db.Column(db.String(200), nullable=True)
    
    # Audyt
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DiaryEntry {self.date} ({self.hours_worked}h)>"
    
    @property
    def hours_worked(self):
        """Liczba godzin przepracowanych tego dnia."""
        from datetime import datetime as dt
        start = dt.combine(self.date, self.start_time)
        end = dt.combine(self.date, self.end_time)
        delta = end - start
        return delta.total_seconds() / 3600
    
    def validate(self):
        """Walidacja wpisu dziennika."""
        errors = []
        
        # Sprawdzenie godzin
        if self.hours_worked < 1:
            errors.append("Minimum 1 godzina pracy")
        if self.hours_worked > 10:
            errors.append("Maximum 10 godzin na dzień")
        
        # Sprawdzenie opisu
        if len(self.description) < 20:
            errors.append("Opis musi zawierać min. 20 znaków")
        if len(self.description) > 1000:
            errors.append("Opis max 1000 znaków")
        
        # Sprawdzenie daty
        if self.date > datetime.now().date():
            errors.append("Data nie może być w przyszłości")
        
        return len(errors) == 0, errors
    
    def to_dict(self):
        return {
            "id": self.id,
            "internship_id": self.internship_id,
            "date": self.date.isoformat(),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "hours_worked": self.hours_worked,
            "description": self.description,
            "learning_outcomes_ids": self.learning_outcomes_ids,
            "created_at": self.created_at.isoformat(),
        }
