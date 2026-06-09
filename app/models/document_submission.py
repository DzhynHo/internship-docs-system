"""
Model for DocumentSubmission
"""

from app import db
from datetime import datetime


class DocumentSubmission(db.Model):
    __tablename__ = 'document_submissions'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    internship_id = db.Column(
        db.Integer,
        db.ForeignKey('internships.id'),
        nullable=False
    )

    attachment_id = db.Column(
        db.Integer,
        db.ForeignKey('attachments.id'),
        nullable=True
    )

    reviewer_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=True
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default='pending'
    )

    # pending | approved | rejected
    data = db.Column(db.JSON, nullable=True)
    comments = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    user = db.relationship(
        'User',
        foreign_keys=[user_id],
        backref='document_submissions'
    )

    reviewer = db.relationship(
        'User',
        foreign_keys=[reviewer_id]
    )

    # UWAGA:
    # NIE definiujemy tutaj relacji internship,
    # ponieważ tworzy ją już backref w Internship.documents

    attachment = db.relationship(
        'Attachment',
        backref='document_submissions'
    )

    def __repr__(self):
        return f'<DocumentSubmission id={self.id} status={self.status}>'