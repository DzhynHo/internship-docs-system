"""
Email service - wysyłanie powiadomień do użytkowników.
"""

from flask import render_template, current_app, url_for
from flask_mail import Message
from app import mail
from threading import Thread


def send_async_email(app, msg):
    """Wysyłanie emaila w osobnym wątku (async)."""
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, text_body=None, html_body=None, attachments=None):
    """
    Ogólna funkcja wysyłająca email.
    
    Args:
        subject: Temat emaila
        recipients: Lista odbiorców
        text_body: Zawartość tekstowa
        html_body: Zawartość HTML (preferowana)
        attachments: Lista (filename, data, mimetype)
    """
    if not isinstance(recipients, list):
        recipients = [recipients]
    
    msg = Message(
        subject=subject,
        recipients=recipients,
        body=text_body,
        html=html_body
    )
    
    if attachments:
        for filename, data, mimetype in attachments:
            msg.attach(filename, mimetype, data)
    
    # Wysyłaj asynchronicznie
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()


def notify_student_document_submitted(student_email, student_name, internship_name, attachment_name):
    """Powiadomienie studenta: dokument wysłany do opiekuna."""
    
    subject = f"Dokument wysłany: {attachment_name}"
    
    html_body = render_template(
        "email/document_submitted.html",
        student_name=student_name,
        internship_name=internship_name,
        attachment_name=attachment_name,
        dashboard_url=url_for('student.dashboard', _external=True)
    )
    
    send_email(
        subject=subject,
        recipients=[student_email],
        html_body=html_body
    )


def notify_mentor_document_pending_review(mentor_email, mentor_name, student_name, attachment_name, review_url):
    """Powiadomienie opiekuna: dokument czeka na sprawdzenie."""
    
    subject = f"📋 Dokument do przeglądu: {student_name} - {attachment_name}"
    
    html_body = render_template(
        "email/mentor_review_pending.html",
        mentor_name=mentor_name,
        student_name=student_name,
        attachment_name=attachment_name,
        review_url=review_url
    )
    
    send_email(
        subject=subject,
        recipients=[mentor_email],
        html_body=html_body
    )


def notify_student_document_approved(student_email, student_name, attachment_name):
    """Powiadomienie studenta: dokument zatwierdzony."""
    
    subject = f"✅ Dokument zatwierdzone: {attachment_name}"
    
    html_body = render_template(
        "email/document_approved.html",
        student_name=student_name,
        attachment_name=attachment_name,
        dashboard_url=url_for('student.dashboard', _external=True)
    )
    
    send_email(
        subject=subject,
        recipients=[student_email],
        html_body=html_body
    )


def notify_student_document_rejected(student_email, student_name, attachment_name, comments):
    """Powiadomienie studenta: dokument odrzucony z uwagami."""
    
    subject = f"⚠️ Dokument wymaga poprawy: {attachment_name}"
    
    html_body = render_template(
        "email/document_rejected.html",
        student_name=student_name,
        attachment_name=attachment_name,
        comments=comments,
        dashboard_url=url_for('student.dashboard', _external=True)
    )
    
    send_email(
        subject=subject,
        recipients=[student_email],
        html_body=html_body
    )


def notify_director_final_approval_pending(director_email, director_name, student_name, internship_name):
    """Powiadomienie dyrekcji: dokumenty gotowe do ostatecznego zatwierdzenia."""
    
    subject = f"📊 Praktyka gotowa do zatwierdzenia: {student_name}"
    
    html_body = render_template(
        "email/director_final_approval.html",
        director_name=director_name,
        student_name=student_name,
        internship_name=internship_name,
        admin_url=url_for('admin.dashboard', _external=True)
    )
    
    send_email(
        subject=subject,
        recipients=[director_email],
        html_body=html_body
    )


def send_test_email(recipient_email):
    """Email testowy."""
    
    subject = "Test - System Praktyk Zawodowych"
    html_body = """
    <h2>Test konfiguracji emaila</h2>
    <p>Jeśli widzisz ten email, to znaczy że konfiguracja SMTP jest prawidłowa! 🎉</p>
    """
    
    send_email(
        subject=subject,
        recipients=[recipient_email],
        html_body=html_body
    )
