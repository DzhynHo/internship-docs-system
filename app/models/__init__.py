from datetime import datetime
import re

from app import db
from app.models.document_submission import DocumentSubmission


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(512), nullable=True)
    description = db.Column(db.Text, nullable=True)
    audience = db.Column(db.String(64), nullable=False, default="all")
    required = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Attachment {self.name} file={self.filename}>"


# Lista wzorcowa wymaganych załączników (używana przy inicjalizacji/seed)
REQUIRED_ATTACHMENTS = [
    "Regulamin Praktyki Zawodowej (PZ)",
    "Porozumienie (załącznik 1)",
    "Program praktyki zawodowej (załącznik 2)",
    "Program i harmonogram (załącznik 2a)",
    "Karta praktyki zawodowej (załącznik 3)",
    "Potwierdzenie efektów uczenia się (załącznik 4)",
    "Potwierdzenie uzyskania efektów (załącznik 4a)",
    "Wniosek o zaliczenie efektów (załącznik 4b)",
    "Kwestionariusz ankiety (załącznik 5)",
    "Dziennik praktyki zawodowej (załącznik 6)",
    "Sprawozdanie z praktyki zawodowej (załącznik 7)",
    "Sprawozdanie - studia niestacjonarne (załącznik 7a)",
    "Protokół egzaminu praktyki zawodowej (załącznik 8)",
    "Oświadczenie instytucji (załącznik 9)",
]


# Map specific attachments to audience (who should fill / see them)
ATTACHMENT_AUDIENCE = {
    "Regulamin Praktyki Zawodowej (PZ)": "all",
    "Porozumienie (załącznik 1)": "student",
    "Program praktyki zawodowej (załącznik 2)": "student",
    "Program i harmonogram (załącznik 2a)": "student",
    "Karta praktyki zawodowej (załącznik 3)": "student",
    "Potwierdzenie efektów uczenia się (załącznik 4)": "student",
    "Potwierdzenie uzyskania efektów (załącznik 4a)": "opiekun",
    "Wniosek o zaliczenie efektów (załącznik 4b)": "student",
    "Kwestionariusz ankiety (załącznik 5)": "student",
    "Dziennik praktyki zawodowej (załącznik 6)": "student",
    "Sprawozdanie z praktyki zawodowej (załącznik 7)": "student",
    "Sprawozdanie - studia niestacjonarne (załącznik 7a)": "student",
    "Protokół egzaminu praktyki zawodowej (załącznik 8)": "dziekanat",
    "Oświadczenie instytucji (załącznik 9)": "student",
}


def validate_one_sentence(text: str) -> bool:
    """Prosta walidacja: czy tekst zawiera nie więcej niż jedno zdanie.

    Liczymy wystąpienia znaków kończących zdania (.!?). Jeśli więcej niż 1, zwracamy False.
    """
    if not text:
        return True
    # usuń wielokropki i skróty prosto - prosta heurystyka
    # Count sentence terminators
    terminators = re.findall(r'[\.\!\?]+', text)
    return len(terminators) <= 1