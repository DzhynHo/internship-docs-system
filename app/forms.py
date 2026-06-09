"""
Formularze dla zalacznikow praktyk zawodowych.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, IntegerField, DateField,
    SelectField, SubmitField, BooleanField, TimeField
)
from wtforms.validators import (
    DataRequired, Length, Email, Regexp, Optional,
    NumberRange, ValidationError
)
from datetime import datetime


class Attachment1Form(FlaskForm):
    """Porozumienie (Zalacznik 1) - formularz."""

    student_first_name = StringField(
        "Imie",
        validators=[
            DataRequired(message="Imie jest wymagane"),
            Length(min=2, max=100, message="Imie musi miec 2-100 znakow")
        ]
    )

    student_last_name = StringField(
        "Nazwisko",
        validators=[
            DataRequired(message="Nazwisko jest wymagane"),
            Length(min=2, max=100, message="Nazwisko musi miec 2-100 znakow")
        ]
    )

    index_number = StringField(
        "Nr indeksu",
        validators=[
            DataRequired(message="Nr indeksu jest wymagany"),
            Regexp(r'^\d{6,8}$', message="Nr indeksu: 6-8 cyfr")
        ]
    )

    email_student = StringField(
        "Email (konto studenckie)",
        validators=[
            DataRequired(message="Email jest wymagany"),
            Email(message="Podaj prawidlowy email")
        ]
    )

    year_of_study = SelectField(
        "Rok studiow",
        choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')],
        validators=[DataRequired(message="Rok studiow jest wymagany")]
    )

    field_of_study = StringField(
        "Kierunek studiow",
        validators=[
            DataRequired(message="Kierunek jest wymagany"),
            Length(min=3, max=100)
        ]
    )

    company_name = StringField(
        "Nazwa firmy",
        validators=[
            DataRequired(message="Nazwa firmy jest wymagana"),
            Length(min=3, max=255, message="Nazwa: 3-255 znakow")
        ]
    )

    company_address = TextAreaField(
        "Adres firmy",
        validators=[
            DataRequired(message="Adres firmy jest wymagany"),
            Length(min=10, max=500, message="Adres: 10-500 znakow")
        ],
        render_kw={"rows": 2}
    )

    mentor_name = StringField(
        "Osoba odpowiedzialna (opiekun w firmie)",
        validators=[
            DataRequired(message="Imie i nazwisko opiekuna jest wymagane"),
            Length(min=5, max=255, message="5-255 znakow")
        ]
    )

    mentor_phone = StringField(
        "Telefon kontaktowy",
        validators=[
            DataRequired(message="Numer telefonu jest wymagany"),
            Regexp(r'^[\d+\-\s()]+$', message="Podaj prawidlowy numer telefonu")
        ]
    )

    mentor_email = StringField(
        "Email opiekuna",
        validators=[
            DataRequired(message="Email opiekuna jest wymagany"),
            Email(message="Podaj prawidlowy email")
        ]
    )

    start_date = DateField(
        "Data rozpoczecia praktyki",
        format='%Y-%m-%d',
        validators=[DataRequired(message="Data rozpoczecia jest wymagana")]
    )

    end_date = DateField(
        "Data zakonczenia praktyki",
        format='%Y-%m-%d',
        validators=[DataRequired(message="Data zakonczenia jest wymagana")]
    )

    total_hours = IntegerField(
        "Wymagana liczba godzin",
        validators=[
            DataRequired(message="Liczba godzin jest wymagana"),
            NumberRange(min=100, max=600, message="Liczba godzin: 100-600")
        ]
    )

    job_description = TextAreaField(
        "Opis stanowiska pracy i glownych obowiazkow",
        validators=[
            DataRequired(message="Opis stanowiska jest wymagany"),
            Length(min=50, max=1000, message="Opis: 50-1000 znakow")
        ],
        render_kw={"rows": 4}
    )

    confirmation = BooleanField(
        "Potwierdzam, ze podane informacje sa prawidlowe",
        validators=[DataRequired(message="Musisz zatwierdzic")]
    )

    submit = SubmitField("Zapisz formularz")
    submit_and_send = SubmitField("Wyslij do opiekuna")

    def validate_end_date(self, field):
        if self.start_date.data and field.data <= self.start_date.data:
            raise ValidationError("Data zakonczenia musi byc po dacie rozpoczecia")

    def validate_start_date(self, field):
        today = datetime.now().date()
        if field.data and field.data < today:
            raise ValidationError("Data rozpoczecia nie moze byc w przeszlosci")

    def to_dict(self):
        return {
            "student_first_name": self.student_first_name.data,
            "student_last_name": self.student_last_name.data,
            "index_number": self.index_number.data,
            "email_student": self.email_student.data,
            "year_of_study": self.year_of_study.data,
            "field_of_study": self.field_of_study.data,
            "company_name": self.company_name.data,
            "company_address": self.company_address.data,
            "mentor_name": self.mentor_name.data,
            "mentor_phone": self.mentor_phone.data,
            "mentor_email": self.mentor_email.data,
            "start_date": self.start_date.data.isoformat() if self.start_date.data else None,
            "end_date": self.end_date.data.isoformat() if self.end_date.data else None,
            "total_hours": self.total_hours.data,
            "job_description": self.job_description.data,
        }


class DiaryEntryForm(FlaskForm):
    """Wpis do dziennika praktyki (Zalacznik 6)."""

    date = DateField(
        "Data",
        format='%Y-%m-%d',
        validators=[DataRequired(message="Data jest wymagana")]
    )

    start_time = TimeField(
        "Godzina poczatkowa",
        format='%H:%M',
        validators=[DataRequired(message="Godzina poczatkowa jest wymagana")]
    )

    end_time = TimeField(
        "Godzina koncowa",
        format='%H:%M',
        validators=[DataRequired(message="Godzina koncowa jest wymagana")]
    )

    description = TextAreaField(
        "Opis czynnosci",
        validators=[
            DataRequired(message="Opis jest wymagany"),
            Length(min=20, max=1000, message="Opis: 20-1000 znakow")
        ],
        render_kw={"rows": 4, "placeholder": "Opisz czym sie zajmowales dzisiaj..."}
    )

    submit = SubmitField("Dodaj wpis")

    def validate_end_time(self, field):
        if self.start_time.data and field.data <= self.start_time.data:
            raise ValidationError("Godzina koncowa musi byc po godzinie poczatkowej")

    @property
    def hours_worked(self):
        from datetime import datetime as dt
        if not self.start_time.data or not self.end_time.data:
            return 0
        base = self.date.data or datetime.now().date()
        start = dt.combine(base, self.start_time.data)
        end = dt.combine(base, self.end_time.data)
        return (end - start).total_seconds() / 3600

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        hours = self.hours_worked
        if hours < 1:
            self.end_time.errors.append("Minimum 1 godzina pracy")
            return False
        if hours > 10:
            self.end_time.errors.append("Maximum 10 godzin na dzien")
            return False
        return True


class ReportForm(FlaskForm):
    """Sprawozdanie z praktyki (Zalacznik 7)."""

    place_description = TextAreaField(
        "I. Charakterystyka miejsca odbywania praktyki",
        validators=[
            DataRequired(message="Opis miejsca praktyki jest wymagany"),
            Length(min=50, max=2000, message="Opis: 50-2000 znakow")
        ],
        render_kw={
            "rows": 6,
            "placeholder": "Krotki opis instytucji, w ktorej odbywala sie praktyka zawodowa..."
        }
    )

    work_description = TextAreaField(
        "II. Opis i analiza wykonywanych prac",
        validators=[
            DataRequired(message="Opis wykonywanych prac jest wymagany"),
            Length(min=50, max=3000, message="Opis: 50-3000 znakow")
        ],
        render_kw={
            "rows": 8,
            "placeholder": "Syntetyczny opis wykonanych prac. Opisz jakie zadania wykonywales w trakcie praktyki (jego zdaniem najwazniejsze)..."
        }
    )

    skills_acquired = TextAreaField(
        "III. Wiedza i umiejetnosci uzyskane w trakcie praktyki",
        validators=[
            DataRequired(message="Opis nabytych kompetencji jest wymagany"),
            Length(min=50, max=3000, message="Opis: 50-3000 znakow")
        ],
        render_kw={
            "rows": 8,
            "placeholder": "Samoocena w zakresie nabytych kompetencji oraz osiagnietych efektow uczenia sie. Opisz jakie kompetencje nabylas w trakcie praktyki zawodowej..."
        }
    )

    submit = SubmitField("Wyslij sprawozdanie")

    def to_dict(self):
        return {
            "place_description": self.place_description.data,
            "work_description": self.work_description.data,
            "skills_acquired": self.skills_acquired.data,
            "submitted_at": datetime.now().isoformat()
        }
from wtforms import PasswordField


class AdminCreateUserForm(FlaskForm):
    full_name = StringField("Imię i nazwisko", validators=[Optional(), Length(max=255)])
    email = StringField("Email", validators=[DataRequired(message="Email jest wymagany"), Email(message="Podaj prawidłowy email")])
    student_index = StringField("Nr albumu", validators=[Optional(), Length(max=20)])
    password = PasswordField("Hasło", validators=[Optional(), Length(min=6, message="Hasło: minimum 6 znaków")])
    password_confirm = PasswordField("Potwierdź hasło", validators=[Optional(), Length(min=6)])
    role = SelectField("Rola", choices=[
        ('student', 'Student'), ('opiekun', 'Opiekun'), ('dziekanat', 'Dziekanat'),
        ('sekretariat', 'Sekretariat'), ('dyrekcja', 'Dyrekcja'),
        ('administrator', 'Administrator'), ('pending', 'Oczekujący')
    ], validators=[DataRequired(message="Rola jest wymagana")])
    submit = SubmitField("Utwórz użytkownika")

    def validate(self, extra_validators=None):
        rv = super().validate(extra_validators=extra_validators)
        if not rv:
            return False
        if self.password.data:
            if not self.password_confirm.data:
                self.password_confirm.errors.append('Potwierdzenie hasła jest wymagane')
                return False
            if self.password.data != self.password_confirm.data:
                self.password_confirm.errors.append('Hasła muszą być takie same')
                return False
        return True


class AssignRoleForm(FlaskForm):
    role = SelectField("Rola", choices=[
        ('student', 'student'), ('opiekun', 'opiekun'), ('administrator', 'administrator'),
        ('admin', 'admin'), ('dziekanat', 'dziekanat'), ('sekretariat', 'sekretariat'),
        ('dyrekcja', 'dyrekcja'), ('pending', 'pending')
    ], validators=[DataRequired(message="Rola jest wymagana")])
    submit = SubmitField("Zapisz")


class LearningOutcomeForm(FlaskForm):
    """Efekt nauczania (do Zalacznika 4)."""

    outcome_text = TextAreaField(
        "Opis efektu nauczania",
        validators=[
            DataRequired(message="Opis efektu jest wymagany"),
            Length(min=20, max=500, message="Opis: 20-500 znakow")
        ],
        render_kw={"rows": 3}
    )

    evidence_source = TextAreaField(
        "Gdzie osiagnales ten efekt? (np. 'Dziennik dni 3-5')",
        validators=[
            Optional(),
            Length(max=300)
        ],
        render_kw={"rows": 2}
    )

    submit = SubmitField("Dodaj efekt")