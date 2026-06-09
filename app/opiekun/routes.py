"""
Trasy (routes) dla widoków opiekuna.
"""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import current_user, login_required
from app import db
from app.models.user import User
from app.models.internship import Internship, LearningOutcome
from app.models import DocumentSubmission
from app.auth.permissions import (
    mentor_required, check_resource_access, role_required
)
from app.services.email_service import (
    notify_student_document_approved,
    notify_student_document_rejected,
    notify_mentor_document_pending_review
)
from datetime import datetime

opiekun_bp = Blueprint('opiekun', __name__, template_folder='templates')


@opiekun_bp.route('/dashboard')
@mentor_required
def dashboard():
    """Dashboard opiekuna - przegląd przypisanych studentów."""
    
    # Pobierz wszystkie praktyki gdzie current_user jest mentorem
    internships = Internship.query.filter_by(mentor_id=current_user.id).all()
    
    # Policz dokumenty do przeglądu
    pending_docs = DocumentSubmission.query.filter(
        DocumentSubmission.status.in_(['submitted', 'pending_review']),
        DocumentSubmission.internship_id.in_([i.id for i in internships])
    ).count()
    
    context = {
        'user': current_user,
        'internships': internships,
        'total_internships': len(internships),
        'pending_docs': pending_docs,
    }
    
    return render_template('opiekun/dashboard.html', **context)


@opiekun_bp.route('/internship/<int:internship_id>')
@mentor_required
@check_resource_access("internship_id")
def view_internship(internship_id):
    """Widok praktyki studenta dla opiekuna."""
    
    internship = Internship.query.get(internship_id)
    
    # Pobierz dokumenty dla tej praktyki
    documents = DocumentSubmission.query.filter_by(internship_id=internship_id).all()
    
    # Pogrupuj dokumenty po statusie
    documents_by_status = {
        'draft': [],
        'submitted': [],
        'pending_review': [],
        'approved': [],
        'rejected': []
    }
    
    for doc in documents:
        if doc.status in documents_by_status:
            documents_by_status[doc.status].append(doc)
    
    # Protokół egzaminu (Zał. 8, DB id=13) – widoczny opiekunowi gdy zatwierdzony
    protocol_doc = DocumentSubmission.query.filter_by(
        internship_id=internship_id,
        attachment_id=13,
        status='approved'
    ).first()

    context = {
        'internship': internship,
        'documents_by_status': documents_by_status,
        'learning_outcomes': internship.learning_outcomes,
        'total_hours_worked': internship.total_hours_worked,
        'protocol_doc': protocol_doc,
    }

    return render_template('opiekun/view_internship.html', **context)


@opiekun_bp.route('/document/<int:document_id>/edit', methods=['GET', 'POST'])
@mentor_required
def edit_document(document_id):
    """Opiekun poprawia błędy w formularzu studenta."""
    document = DocumentSubmission.query.get_or_404(document_id)

    if document.internship.mentor_id != current_user.id:
        flash("Brak dostępu do tego dokumentu.", "error")
        return redirect(url_for('opiekun.dashboard'))

    att = document.attachment
    att_name = att.name if att else f"Dokument #{document.id}"
    internship = document.internship
    saved = document.data or {}

    if request.method == 'POST':
        # Zbierz wszystkie pola formularza (generyczne – zapisz cały POST jako data)
        new_data = {k: v for k, v in request.form.items()
                    if k not in ('csrf_token', 'action')}
        document.data = new_data
        document.updated_at = datetime.utcnow()
        # Zmień status z rejected → draft żeby student widział poprawki
        if document.status == 'rejected':
            document.status = 'draft'
        db.session.commit()
        flash(f"Formularz poprawiony. Student może teraz go przejrzeć i wysłać ponownie.", "success")
        return redirect(url_for('opiekun.view_internship', internship_id=internship.id))

    # Buduj dynamiczny formularz na podstawie istniejących danych
    import html as _h

    def field_row(key, val):
        label = key.replace('_', ' ').capitalize()
        escaped_val = _h.escape(str(val or ''))
        if len(str(val or '')) > 100:
            return (f'<div class="form-row"><label>{label}</label>'
                    f'<textarea name="{key}" rows="4">{escaped_val}</textarea></div>')
        return (f'<div class="form-row"><label>{label}</label>'
                f'<input type="text" name="{key}" value="{escaped_val}"></div>')

    fields_html = ''.join(field_row(k, v) for k, v in saved.items()) if saved else (
        '<p style="color:#9ca3af;font-size:13px;">Ten dokument nie ma jeszcze zapisanych danych.</p>'
    )

    page_html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Edycja dokumentu – Panel Opiekuna</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/css/style.css">
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'IBM Plex Sans',sans-serif;background:#f0f2f7;color:#111827;min-height:100vh;display:flex;flex-direction:column}}
  nav{{background:#1a2744;display:flex;align-items:center;justify-content:space-between;padding:0 28px;height:68px}}
  nav a{{color:rgba(255,255,255,.8);text-decoration:none;padding:7px 14px;border-radius:6px;font-size:13.5px;font-weight:500}}
  nav a:hover{{background:rgba(255,255,255,.1);color:#fff}}
  nav a.logout{{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:#fff}}
  .strip{{height:4px;background:linear-gradient(90deg,#3b5bdb,#0d9488)}}
  .page-header{{background:#fff;border-bottom:1px solid #dde1ef;padding:18px 0;margin-bottom:28px}}
  .page-header-inner{{max-width:960px;margin:0 auto;padding:0 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
  h1{{font-size:20px;font-weight:700;color:#1a2744}}
  .breadcrumb{{font-size:12px;color:#6b7280;margin-top:4px}}
  .breadcrumb a{{color:#3b5bdb;text-decoration:none}}
  .container{{max-width:960px;margin:0 auto;padding:0 24px 48px;flex:1}}
  .form-row{{margin-bottom:14px}}
  .form-row label{{display:block;font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;color:#6b7280;margin-bottom:5px}}
  .form-row input,.form-row textarea,.form-row select{{width:100%;border:1px solid #dde1ef;border-radius:6px;padding:9px 12px;font-size:13.5px;font-family:inherit;outline:none;transition:border .15s}}
  .form-row input:focus,.form-row textarea:focus{{border-color:#3b5bdb;box-shadow:0 0 0 3px rgba(59,91,219,.1)}}
  .btn{{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:600;font-family:inherit;cursor:pointer;border:none;text-decoration:none;transition:all .15s}}
  .btn-primary{{background:#3b5bdb;color:#fff!important}}
  .btn-ghost{{background:transparent;color:#374151!important;border:1px solid #dde1ef}}
  footer{{padding:16px;text-align:center;color:#6b7280;font-size:12px;border-top:1px solid #dde1ef;background:#fff;margin-top:auto}}
</style>
</head>
<body>
<nav>
  <a href="/opiekun/dashboard" style="display:flex;align-items:center;gap:12px;text-decoration:none;">
    <img src="/static/img/logo.png" style="height:40px;background:#fff;padding:3px;border-radius:4px;" onerror="this.style.display='none'">
    <div><strong style="color:#fff;font-size:14px;display:block;">ANS Elbląg</strong>
    <span style="color:rgba(255,255,255,.6);font-size:11px;">Panel Opiekuna</span></div>
  </a>
  <div style="display:flex;gap:4px;">
    <a href="/opiekun/internship/{internship.id}">← Powrót do praktyki</a>
    <a href="/auth/logout" class="logout">Wyloguj</a>
  </div>
</nav>
<div class="strip"></div>
<div class="page-header">
  <div class="page-header-inner">
    <div>
      <h1>Edycja dokumentu studenta</h1>
      <div class="breadcrumb">
        <a href="/opiekun/dashboard">Dashboard</a> ›
        <a href="/opiekun/internship/{internship.id}">{_h.escape(internship.student.full_name)}</a> ›
        Edycja: {_h.escape(att_name)}
      </div>
    </div>
  </div>
</div>
<div class="container">
  <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:6px;
              padding:12px 16px;margin-bottom:20px;font-size:13px;color:#92400e;">
    <strong>Edycja w imieniu studenta</strong> — wprowadzone zmiany zostaną zapisane
    w dokumencie. Status dokumentu zostanie zmieniony na <strong>szkic</strong>
    – student będzie mógł go przejrzeć i wysłać ponownie.
  </div>

  <div style="background:#fff;border:1px solid #dde1ef;border-radius:10px;padding:28px 32px;max-width:800px;">
    <div style="margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid #e2e8f0;">
      <div style="font-size:11.5px;color:#6b7280;font-weight:600;margin-bottom:3px;">ZAŁĄCZNIK</div>
      <div style="font-size:14px;font-weight:700;color:#1a2744;">{_h.escape(att_name)}</div>
      <div style="font-size:12px;color:#9ca3af;margin-top:2px;">
        Student: {_h.escape(internship.student.full_name)} &nbsp;·&nbsp;
        Firma: {_h.escape(internship.company_name)}
      </div>
    </div>

    <form method="post">
      {fields_html}
      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;
                  border-top:1px solid #e2e8f0;padding-top:20px;margin-top:8px;">
        <button type="submit" class="btn btn-primary"
                onclick="return confirm('Zapisać poprawki w formularzu studenta?')">
          💾 Zapisz poprawki
        </button>
        <a href="/opiekun/internship/{internship.id}" class="btn btn-ghost">
          ✕ Anuluj
        </a>
      </div>
    </form>
  </div>
</div>
<footer>&copy; 2026 Akademia Nauk Stosowanych w Elblągu</footer>
</body></html>"""
    return page_html


@opiekun_bp.route('/document/<int:document_id>/review', methods=['GET', 'POST'])
@mentor_required
def review_document(document_id):
    """Przegląd i zatwierdzenie dokumentu."""
    
    document = DocumentSubmission.query.get(document_id)
    
    if not document:
        flash("Dokument nie znaleziony", "error")
        return redirect(url_for('opiekun.dashboard'))
    
    # Sprawdź czy ten dokument należy do naszych studentów
    if document.internship.mentor_id != current_user.id:
        flash("Brak dostępu do tego dokumentu", "error")
        return redirect(url_for('opiekun.dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action')  # 'approve' lub 'reject'
        comment = request.form.get('comment', '').strip()
        
        if action == 'approve':
            document.status = "approved"
            document.reviewer_id = current_user.id
            document.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Wyślij email do studenta
            try:
                notify_student_document_approved(
                    document.user.email,
                    document.user.full_name,
                    document.attachment.name if document.attachment else "Dokument"
                )
            except Exception as e:
                print(f"[Email] Error sending approval notification: {e}")
            
            flash(f"Dokument zatwierdzony", "success")
        
        elif action == 'reject':
            if not comment:
                flash("Musisz dodać komentarz przy odrzuceniu dokumentu", "error")
                return redirect(url_for('opiekun.review_document', document_id=document_id))
            
            document.status = "rejected"
            document.comments = comment
            document.reviewer_id = current_user.id
            document.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Wyślij email do studenta
            try:
                notify_student_document_rejected(
                    document.user.email,
                    document.user.full_name,
                    document.attachment.name if document.attachment else "Dokument",
                    comment
                )
            except Exception as e:
                print(f"[Email] Error sending rejection notification: {e}")
            
            flash("Dokument odrzucony, student otrzymał powiadomienie", "success")
        
        return redirect(url_for('opiekun.view_internship', internship_id=document.internship_id))
    
    context = {
        'document': document,
        'internship': document.internship,
        'attachment': document.attachment,
    }
    
    return render_template('opiekun/review_document.html', **context)


@opiekun_bp.route('/document/<int:document_id>/comment', methods=['POST'])
@mentor_required
def add_comment(document_id):
    """Dodaj komentarz do dokumentu (AJAX)."""
    
    document = DocumentSubmission.query.get(document_id)
    
    if not document or document.internship.mentor_id != current_user.id:
        return jsonify({'success': False, 'error': 'Brak dostępu'}), 403
    
    comment = request.form.get('comment', '').strip()
    
    if not comment:
        return jsonify({'success': False, 'error': 'Komentarz nie może być pusty'}), 400
    
    # Append comment to existing comments
    if document.comments:
        document.comments += f"\n\n[{datetime.now().strftime('%d.%m.%Y %H:%M')}]\n{comment}"
    else:
        document.comments = comment
    
    document.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Komentarz dodany',
        'comment': comment
    })


@opiekun_bp.route('/learning-outcome/<int:outcome_id>/verify', methods=['POST'])
@mentor_required
def verify_learning_outcome(outcome_id):
    """Weryfikacja efektu nauczania przez opiekuna."""
    
    outcome = LearningOutcome.query.get(outcome_id)
    
    if not outcome or outcome.internship.mentor_id != current_user.id:
        return jsonify({'success': False, 'error': 'Brak dostępu'}), 403
    
    action = request.form.get('action')  # 'verify' lub 'unverify'
    
    if action == 'verify':
        outcome.status = "verified"
        outcome.verified_by = current_user.id
        outcome.verified_date = datetime.now().date()
    elif action == 'unverify':
        outcome.status = "achieved"
        outcome.verified_by = None
        outcome.verified_date = None
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Efekt {action}owany',
        'outcome': outcome.to_dict()
    })


@opiekun_bp.route('/document/<int:document_id>/view')
@mentor_required
def view_document(document_id):
    """Podgląd zatwierdzonego/odrzuconego dokumentu w trybie read-only (jak dziekanat)."""
    import html as _h
    from flask import render_template_string

    document = DocumentSubmission.query.get_or_404(document_id)

    if document.internship.mentor_id != current_user.id:
        flash("Brak dostępu do tego dokumentu.", "error")
        return redirect(url_for('opiekun.dashboard'))

    internship = document.internship
    att = document.attachment
    att_name = att.name if att else f'Dokument #{document.id}'
    data = document.data or {}

    _LABELS = {
        'agreement_number': 'Numer porozumienia', 'agreement_date': 'Data porozumienia',
        'company_name': 'Nazwa zakładu pracy', 'company_address': 'Adres',
        'company_phone': 'Telefon', 'company_email': 'E-mail firmy',
        'company_nip': 'NIP firmy', 'company_contact': 'Osoba kontaktowa',
        'student_name': 'Student', 'album_number': 'Nr albumu',
        'study_type': 'Forma studiów', 'specialization': 'Specjalność',
        'internship_duration': 'Czas trwania', 'university_supervisor': 'Opiekun uczelniany',
        'date_from': 'Data od', 'date_to': 'Data do', 'internship_year': 'Rok',
        'company_supervisor': 'Opiekun zakładowy', 'supervisor_role': 'Stanowisko opiekuna',
        'bhp_confirmed': 'Szkolenie BHP',
        'place_description': 'I. Charakterystyka miejsca praktyki',
        'work_description': 'II. Opis i analiza wykonywanych prac',
        'skills_acquired': 'III. Wiedza i umiejętności',
        'cel_praktyki': 'Cel praktyki', 'zakres_zadan': 'Zakres zadań',
        'oczekiwane_efekty': 'Oczekiwane efekty', 'miejsce': 'Miejsce praktyki',
        'ocena_ogolna': 'Ocena ogólna', 'uwagi': 'Uwagi',
        'hours_total': 'Liczba godzin', 'student_index': 'Nr albumu',
    }
    _HIDE = {'type', 'submitted_at', '_dz_signed'}

    rows_html = ''
    for key, val in data.items():
        if key in _HIDE or not val or key.startswith('outcome_') or (key.startswith('q') and len(key) == 3):
            continue
        label = _LABELS.get(key, key.replace('_', ' ').capitalize())
        if key == 'bhp_confirmed':
            val_str = '✅ Tak – szkolenie BHP potwierdzone' if val == '1' else '✗ Nie'
        elif key == 'study_type':
            val_str = {'stacjonarne': 'Stacjonarne', 'niestacjonarne': 'Niestacjonarne'}.get(val, _h.escape(str(val)))
        else:
            val_str = _h.escape(str(val))
        rows_html += f"""<tr>
          <td style="width:38%;padding:9px 14px;font-weight:600;color:#374151;border:1px solid #e2e8f0;background:#f7fafc;font-size:13px;">{_h.escape(label)}</td>
          <td style="padding:9px 14px;border:1px solid #e2e8f0;font-size:13px;color:#111827;white-space:pre-wrap;line-height:1.55;">{val_str}</td>
        </tr>"""

    outcomes_html = ''
    outcome_items = sorted((k, v) for k, v in data.items() if k.startswith('outcome_'))
    if outcome_items:
        outcomes_html = '<div style="font-weight:700;font-size:13px;color:#1a2744;margin:16px 0 8px;">Efekty uczenia się</div>'
        outcomes_html += '<table style="width:100%;border-collapse:collapse;">'
        for k, v in outcome_items:
            num = k.replace('outcome_', '')
            color = '#16a34a' if v == 'uzyskal' else '#dc2626'
            label = 'uzyskał/a' if v == 'uzyskal' else 'nie uzyskał/a'
            outcomes_html += (f'<tr><td style="padding:6px 12px;border:1px solid #e2e8f0;width:44px;text-align:center;font-weight:700;font-size:12px;">{num}</td>'
                              f'<td style="padding:6px 12px;border:1px solid #e2e8f0;color:{color};font-weight:600;font-size:13px;">{label}</td></tr>')
        outcomes_html += '</table>'

    status_colors = {
        'approved': ('#16a34a', '#f0fdf4', '✅ Zatwierdzony'),
        'rejected': ('#dc2626', '#fef2f2', '✏️ Odesłany do poprawy'),
        'submitted': ('#d97706', '#fffbeb', '⏳ Oczekuje na decyzję'),
        'pending_review': ('#d97706', '#fffbeb', '🔍 W weryfikacji'),
        'draft': ('#6b7280', '#f3f4f6', '📝 Szkic'),
    }
    sc = status_colors.get(document.status, ('#6b7280', '#f3f4f6', document.status))

    reviewer_html = ''
    if document.reviewer:
        reviewer_html = f'<div style="margin-top:8px;padding:8px 10px;background:#f0fdf4;border-radius:6px;font-size:12px;color:#166534;"><strong>Zatwierdził/a:</strong> {_h.escape(document.reviewer.full_name or document.reviewer.email)}</div>'
    if document.comments:
        reviewer_html += f'<div style="margin-top:8px;padding:8px 10px;background:#fef2f2;border-radius:6px;font-size:12.5px;color:#c53030;"><strong>Uwagi:</strong> {_h.escape(document.comments)}</div>'

    student_name = _h.escape(internship.student.full_name or internship.student.email)
    company = _h.escape(internship.company_name)

    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{_h.escape(att_name)} – Panel Opiekuna</title>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'IBM Plex Sans',sans-serif;background:#f0f2f7;color:#111827;min-height:100vh;display:flex;flex-direction:column}}
    nav.ans-navbar{{background:#1a2744;display:flex;align-items:center;justify-content:space-between;padding:0 28px;height:68px;box-shadow:0 2px 12px rgba(0,0,0,.18)}}
    nav.ans-navbar a.brand{{display:flex;align-items:center;gap:14px;text-decoration:none}}
    nav.ans-navbar a.brand img{{height:44px;background:white;padding:4px;border-radius:4px}}
    nav.ans-navbar .brand-text{{color:#fff;line-height:1.2}}
    nav.ans-navbar .brand-text>strong{{font-size:15px;font-weight:700;display:block}}
    nav.ans-navbar .brand-text span{{font-size:12px;font-weight:300;color:rgba(255,255,255,.65)}}
    nav.ans-navbar>nav{{display:flex;align-items:center;gap:4px}}
    nav.ans-navbar>nav a{{color:rgba(255,255,255,.75);text-decoration:none;padding:7px 14px;border-radius:6px;font-size:13.5px;font-weight:500;transition:all .15s}}
    nav.ans-navbar>nav a:hover{{color:#fff;background:rgba(255,255,255,.1)}}
    nav.ans-navbar>nav a.btn-logout{{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2)}}
    .ans-header-strip{{height:4px;background:linear-gradient(90deg,#3b5bdb 0%,#0d9488 100%)}}
    .page-header{{background:#fff;border-bottom:1px solid #dde1ef;padding:18px 0}}
    .page-header-inner{{max-width:1200px;margin:0 auto;padding:0 28px;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}}
    .page-title-group h1{{font-size:20px;font-weight:700;color:#1a2744}}
    .breadcrumb{{display:flex;align-items:center;gap:6px;font-size:12.5px;color:#6b7280;margin-top:4px}}
    .breadcrumb a{{color:#3b5bdb;text-decoration:none}}
    .container{{max-width:1200px;margin:0 auto;padding:28px 28px 60px;flex:1}}
    .grid{{display:grid;grid-template-columns:1fr 280px;gap:24px;align-items:start}}
    .card{{background:#fff;border:1px solid #dde1ef;border-radius:10px;box-shadow:0 1px 3px rgba(26,39,68,.08);overflow:hidden;margin-bottom:20px}}
    .card-header{{padding:14px 20px;border-bottom:1px solid #eaecf5;display:flex;align-items:center;justify-content:space-between}}
    .card-header h2{{font-size:14px;font-weight:700;color:#1a2744}}
    .card-body{{padding:20px}}
    .btn{{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:600;font-family:inherit;cursor:pointer;border:none;text-decoration:none;transition:all .15s;white-space:nowrap}}
    .btn-ghost{{background:transparent;color:#374151;border:1px solid #dde1ef}}
    .btn-ghost:hover{{background:#f8f9fc}}
    .btn-sm{{padding:5px 12px;font-size:12px}}
    footer{{padding:16px;text-align:center;color:#6b7280;font-size:12px;border-top:1px solid #dde1ef;background:#fff;margin-top:auto}}
    @media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
  </style>
</head>
<body>
<nav class="ans-navbar">
  <a class="brand" href="/auth/dashboard">
    <img src="/static/img/logo.png" alt="ANS" onerror="this.style.display='none'">
    <div class="brand-text"><strong>Akademia Nauk Stosowanych</strong><span>w Elblągu – System Praktyk</span></div>
  </a>
  <nav>
    <a href="/auth/dashboard">Dashboard</a>
    <a href="/opiekun/dashboard">Panel opiekuna</a>
    <a href="/auth/logout" class="btn-logout">Wyloguj</a>
  </nav>
</nav>
<div class="ans-header-strip"></div>

<div class="page-header">
  <div class="page-header-inner">
    <div class="page-title-group">
      <h1>📄 {_h.escape(att_name)}</h1>
      <div class="breadcrumb">
        <a href="/opiekun/dashboard">Panel opiekuna</a> ›
        <a href="/opiekun/internship/{internship.id}">{student_name}</a> ›
        <span>Podgląd dokumentu</span>
      </div>
    </div>
    <a href="/opiekun/internship/{internship.id}" class="btn btn-ghost btn-sm">← Powrót</a>
  </div>
</div>

<div class="container">
  <div class="grid">
    <div>
      <div class="card">
        <div class="card-header">
          <h2>Treść dokumentu</h2>
          <span style="display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:20px;font-size:11.5px;font-weight:600;background:{sc[1]};color:{sc[0]};">{sc[2]}</span>
        </div>
        <div class="card-body">
          {f'<table style="width:100%;border-collapse:collapse;margin-bottom:16px;">{rows_html}</table>' if rows_html else '<p style="color:#9ca3af;font-size:13px;font-style:italic;">Brak danych formularza.</p>'}
          {outcomes_html}
        </div>
      </div>
    </div>
    <div>
      <div class="card">
        <div class="card-header"><h2>ℹ️ Szczegóły</h2></div>
        <div class="card-body" style="font-size:13px;">
          <div style="margin-bottom:8px;"><span style="color:#6b7280;">Student:</span><strong style="margin-left:6px;">{student_name}</strong></div>
          <div style="margin-bottom:8px;"><span style="color:#6b7280;">Firma:</span><span style="margin-left:6px;">{company}</span></div>
          <div style="margin-bottom:8px;"><span style="color:#6b7280;">Wysłano:</span><span style="margin-left:6px;font-family:'IBM Plex Mono',monospace;font-size:12px;">{document.created_at.strftime('%d.%m.%Y %H:%M')}</span></div>
          <div style="margin-bottom:8px;"><span style="color:#6b7280;">Zmieniono:</span><span style="margin-left:6px;font-family:'IBM Plex Mono',monospace;font-size:12px;">{document.updated_at.strftime('%d.%m.%Y %H:%M')}</span></div>
          <div style="margin-bottom:8px;"><span style="color:#6b7280;">Status:</span>
            <span style="margin-left:6px;display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:20px;font-size:11.5px;font-weight:600;background:{sc[1]};color:{sc[0]};">{sc[2]}</span>
          </div>
          {reviewer_html}
        </div>
      </div>
      <div class="card">
        <div class="card-header"><h2>🔗 Akcje</h2></div>
        <div class="card-body">
          <a href="/opiekun/internship/{internship.id}" class="btn btn-ghost" style="width:100%;justify-content:center;margin-bottom:8px;">← Wróć do praktyki</a>
          {'<a href="/opiekun/document/' + str(document.id) + '/review" class="btn btn-ghost" style="width:100%;justify-content:center;">✍️ Panel decyzji</a>' if document.status in ('submitted','pending_review') else ''}
        </div>
      </div>
    </div>
  </div>
</div>
<footer>&copy; 2026 <strong>Akademia Nauk Stosowanych w Elblągu</strong> – System Obsługi Praktyk</footer>
</body></html>"""
    return html


@opiekun_bp.route('/internship/<int:internship_id>/attachment-4a', methods=['GET', 'POST'])
@mentor_required
def attachment_4a(internship_id):
    """Zał. 4a – Potwierdzenie uzyskania efektów uczenia się (formularz opiekuna, DB id=7)."""
    internship = Internship.query.get_or_404(internship_id)
    if internship.mentor_id != current_user.id:
        flash("Brak dostępu.", "error")
        return redirect(url_for('opiekun.dashboard'))

    doc = DocumentSubmission.query.filter_by(
        internship_id=internship_id,
        attachment_id=7
    ).first()
    saved = doc.data if (doc and doc.data) else {}

    # Te same 13 efektów co w Zał. 4 studenta
    OUTCOMES = [
        (1,  "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących "
             "informatyki z zachowaniem standardów i norm technicznych"),
        (2,  "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce"),
        (3,  "Zna ekonomiczne, prawne skutki własnych działań podejmowanych w ramach praktyki "
             "oraz ograniczenia wynikające z prawa autorskiego i kodeksu pracy"),
        (4,  "Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka"),
        (5,  "Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu wymaganego "
             "do realizacji powierzonego zadania"),
        (6,  "W oparciu o kontakty ze środowiskiem inżynierskim zakładu potrafi podnieść "
             "swoje kompetencje co najmniej z dwóch zakresów (sprzęt, oprogramowanie, e-usługi)"),
        (7,  "Opracowuje dokumentację realizowanych zadań i referuje zagadnienia ustnie"),
        (8,  "Potrafi zidentyfikować problem informatyczny, opisać go i zrealizować rozwiązanie"),
        (9,  "Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu informatyki "
             "stosując normy i standardy oraz aspekty środowiskowe i etyczne"),
        (10, "Pracuje w zespole zajmującym się zawodowo branżą IT"),
        (11, "Przestrzega zasad etyki zawodowej i korzysta z wiedzy doświadczonych kolegów"),
        (12, "Potrafi komunikować się z osobami spoza branży – pozyskiwać i przekazywać informacje"),
        (13, "Dostrzega tempo deaktualizacji wiedzy informatycznej i skutki działalności "
             "informatyków ekonomiczne i społeczne"),
    ]

    if request.method == 'POST':
        action = request.form.get('action', 'save')
        assessments = {}
        for num, _ in OUTCOMES:
            assessments[f"out_{num:02d}"] = request.form.get(f"out_{num:02d}", "niepotwierdzone")

        data = {
            "ocena_ogolna": request.form.get('ocena_ogolna', '').strip(),
            "uwagi":        request.form.get('uwagi', '').strip(),
            **assessments,
        }

        if not doc:
            doc = DocumentSubmission(
                user_id=current_user.id,
                internship_id=internship_id,
                attachment_id=7,
                status='draft'
            )
            db.session.add(doc)

        doc.data = data
        doc.reviewer_id = current_user.id
        doc.updated_at = datetime.utcnow()
        doc.status = 'approved' if action == 'finalize' else 'draft'
        db.session.commit()

        msg = "Potwierdzenie efektów zatwierdzone." if action == 'finalize' else "Zapisano szkic."
        flash(msg, "success")
        return redirect(url_for('opiekun.view_internship', internship_id=internship_id))

    # Sprawdź co student zadeklarował (Zał. 4, DB id=6)
    student_doc = DocumentSubmission.query.filter_by(
        internship_id=internship_id,
        attachment_id=6
    ).first()
    student_claims = student_doc.data if (student_doc and student_doc.data) else {}

    from flask import render_template_string
    SCALE = [
        ('potwierdzone',      'Potwierdzone',      '#16a34a', '#f0fdf4'),
        ('czesciowe',         'Częściowe',          '#d97706', '#fffbeb'),
        ('niepotwierdzone',   'Niepotwierdzone',    '#dc2626', '#fef2f2'),
    ]

    rows_html = ''
    for num, text in OUTCOMES:
        key = f"out_{num:02d}"
        student_key = f"outcome_{num:02d}"
        saved_val = saved.get(key, 'niepotwierdzone')
        student_val = student_claims.get(student_key, '')
        student_cell = ''
        if student_val:
            s_color = '#16a34a' if student_val == 'uzyskal' else '#dc2626'
            s_label = 'uzyskał/a' if student_val == 'uzyskal' else 'nie uzyskał/a'
            student_cell = f'<span style="font-size:11px;color:{s_color};font-weight:600;">{s_label}</span>'

        radios = ''
        for val, label, color, bg in SCALE:
            checked = 'checked' if saved_val == val else ''
            radios += (
                f'<label style="display:flex;align-items:center;gap:5px;cursor:pointer;'
                f'font-size:12px;color:{color};">'
                f'<input type="radio" name="{key}" value="{val}" {checked} '
                f'style="accent-color:{color};"> {label}</label>'
            )

        rows_html += f"""<tr style="{'background:#f7fafc;' if num % 2 == 0 else ''}">
          <td style="width:32px;text-align:center;border:1px solid #cbd5e0;padding:10px 8px;
                     font-weight:700;color:#718096;font-size:12px;">{num:02d}</td>
          <td style="border:1px solid #cbd5e0;padding:10px 14px;font-size:12.5px;
                     line-height:1.5;color:#2d3748;">{text}
            {f'<div style="margin-top:4px;">Deklaracja studenta: {student_cell}</div>' if student_cell else ''}
          </td>
          <td style="border:1px solid #cbd5e0;padding:10px 12px;min-width:150px;">
            <div style="display:flex;flex-direction:column;gap:6px;">{radios}</div>
          </td>
        </tr>"""

    ocena_ogolna_val = saved.get('ocena_ogolna', '')
    uwagi_val = saved.get('uwagi', '')
    status_banner = ''
    if doc and doc.status == 'approved':
        status_banner = '<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:10px 16px;font-size:13px;color:#166534;margin-bottom:16px;">✅ Formularz zatwierdzony i widoczny dla studenta.</div>'

    page_html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Zał. 4a – Potwierdzenie efektów</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/css/style.css">
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'IBM Plex Sans',sans-serif;background:#f0f2f7;color:#111827;min-height:100vh;display:flex;flex-direction:column}}
  nav{{background:#1a2744;display:flex;align-items:center;justify-content:space-between;padding:0 28px;height:68px;box-shadow:0 2px 12px rgba(0,0,0,.18)}}
  nav a{{color:rgba(255,255,255,.8);text-decoration:none;padding:7px 14px;border-radius:6px;font-size:13.5px;font-weight:500}}
  nav a:hover{{background:rgba(255,255,255,.1);color:#fff}}
  nav a.logout{{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:#fff}}
  .strip{{height:4px;background:linear-gradient(90deg,#3b5bdb,#0d9488);flex-shrink:0}}
  .page-header{{background:#fff;border-bottom:1px solid #dde1ef;padding:18px 0;margin-bottom:24px}}
  .page-header-inner{{max-width:1100px;margin:0 auto;padding:0 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
  h1{{font-size:20px;font-weight:700;color:#1a2744}}
  .breadcrumb{{font-size:12px;color:#6b7280;margin-top:4px}}
  .breadcrumb a{{color:#3b5bdb;text-decoration:none}}
  .container{{max-width:1100px;margin:0 auto;padding:0 24px 48px;flex:1}}
  .btn{{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:600;font-family:inherit;cursor:pointer;border:none;text-decoration:none;transition:all .15s}}
  .btn-primary{{background:#3b5bdb;color:#fff!important}}
  .btn-ghost{{background:transparent;color:#374151!important;border:1px solid #dde1ef}}
  .btn-teal{{background:#0d9488;color:#fff!important}}
  .form-group{{margin-bottom:16px}}
  .form-group label{{display:block;font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;color:#6b7280;margin-bottom:5px}}
  .form-group input,.form-group select,.form-group textarea{{width:100%;border:1px solid #dde1ef;border-radius:6px;padding:9px 12px;font-size:13.5px;font-family:inherit;outline:none;transition:border .15s}}
  .form-group input:focus,.form-group textarea:focus{{border-color:#3b5bdb;box-shadow:0 0 0 3px rgba(59,91,219,.1)}}
  footer{{padding:16px;text-align:center;color:#6b7280;font-size:12px;border-top:1px solid #dde1ef;background:#fff;margin-top:auto}}
</style>
</head>
<body>
<nav>
  <a href="/opiekun/dashboard" style="display:flex;align-items:center;gap:12px;text-decoration:none;">
    <img src="/static/img/logo.png" style="height:40px;background:#fff;padding:3px;border-radius:4px;" onerror="this.style.display='none'">
    <div>
      <strong style="color:#fff;font-size:14px;display:block;">Akademia Nauk Stosowanych w Elblągu</strong>
      <span style="color:rgba(255,255,255,.6);font-size:11px;">Panel Opiekuna</span>
    </div>
  </a>
  <div style="display:flex;gap:4px;">
    <a href="/opiekun/dashboard">Dashboard</a>
    <a href="/opiekun/internship/{internship_id}">Praktyka studenta</a>
    <a href="/auth/logout" class="logout">Wyloguj</a>
  </div>
</nav>
<div class="strip"></div>

<div class="page-header">
  <div class="page-header-inner">
    <div>
      <h1>Potwierdzenie uzyskania efektów uczenia się</h1>
      <div class="breadcrumb">
        <a href="/opiekun/dashboard">Dashboard</a> ›
        <a href="/opiekun/internship/{internship_id}">{internship.student.full_name}</a> ›
        Załącznik nr 4a
      </div>
    </div>
    <span style="font-size:11px;color:#9ca3af;font-weight:600;">{'✅ ZATWIERDZONY' if (doc and doc.status == 'approved') else '⚪ SZKIC'}</span>
  </div>
</div>

<div class="container">
  {status_banner}

  <div style="background:#fff;border:1px solid #dde1ef;border-radius:10px;padding:32px 36px;max-width:900px;">
    <div style="text-align:right;font-size:11px;color:#9ca3af;margin-bottom:6px;">Załącznik nr 4a</div>
    <div style="font-size:12px;margin-bottom:16px;">
      <strong>Akademia Nauk Stosowanych w Elblągu</strong><br>
      <span style="font-style:italic;color:#6b7280;">Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego</span>
    </div>
    <div style="text-align:center;font-weight:700;font-size:14px;text-transform:uppercase;
                letter-spacing:.5px;margin-bottom:20px;line-height:1.5;color:#1a2744;">
      POTWIERDZENIE UZYSKANIA EFEKTÓW UCZENIA SIĘ<br>
      W RAMACH PRAKTYKI ZAWODOWEJ<br>
      <span style="font-size:12px;font-weight:500;font-style:italic;text-transform:none;">
        Merytoryczna ocena opiekuna zakładowego
      </span>
    </div>

    <div style="background:#f7fafc;border:1px solid #e2e8f0;border-radius:8px;
                padding:14px 20px;margin-bottom:22px;display:grid;
                grid-template-columns:1fr 1fr;gap:12px;font-size:13px;">
      <div><span style="color:#6b7280;">Student:</span>
        <strong style="margin-left:6px;">{internship.student.full_name}</strong></div>
      <div><span style="color:#6b7280;">Firma:</span>
        <strong style="margin-left:6px;">{internship.company_name}</strong></div>
      <div><span style="color:#6b7280;">Kierunek:</span>
        <strong style="margin-left:6px;">Informatyka</strong></div>
      <div><span style="color:#6b7280;">Termin:</span>
        <strong style="margin-left:6px;">{internship.start_date.strftime('%d.%m.%Y')} – {internship.end_date.strftime('%d.%m.%Y')}</strong></div>
    </div>

    <form method="post">
      <div style="overflow-x:auto;margin-bottom:22px;">
        <table style="width:100%;border-collapse:collapse;font-family:'IBM Plex Sans',sans-serif;">
          <thead>
            <tr style="background:#f7fafc;">
              <th style="width:32px;border:1px solid #cbd5e0;padding:8px;font-size:11px;color:#718096;text-align:center;">#</th>
              <th style="border:1px solid #cbd5e0;padding:8px 14px;font-size:11.5px;color:#718096;text-align:left;">Efekt uczenia się</th>
              <th style="width:170px;border:1px solid #cbd5e0;padding:8px;font-size:11.5px;color:#718096;text-align:center;">Ocena opiekuna</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>

      <div class="form-group">
        <label>Ocena ogólna praktyki</label>
        <input type="text" name="ocena_ogolna" value="{ocena_ogolna_val}"
               placeholder="np. 4.5, bardzo dobry, zaliczona z wyróżnieniem">
      </div>

      <div class="form-group">
        <label>Dodatkowe uwagi i komentarze</label>
        <textarea name="uwagi" rows="4"
                  placeholder="Uwagi do przebiegu praktyki, osiągnięć studenta...">{uwagi_val}</textarea>
      </div>

      <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:6px;
                  padding:10px 16px;font-size:12.5px;color:#92400e;margin-bottom:20px;">
        <strong>Uwaga:</strong> Po zatwierdzeniu formularz będzie widoczny dla studenta i dziekanatu.
        Możesz go edytować w dowolnym momencie.
      </div>

      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;
                  border-top:1px solid #e2e8f0;padding-top:20px;">
        <button type="submit" name="action" value="save" class="btn btn-ghost">
          💾 Zapisz szkic
        </button>
        <button type="submit" name="action" value="finalize" class="btn btn-teal"
                onclick="return confirm('Zatwierdzić ocenę efektów uczenia się?')">
          ✅ Zatwierdź ocenę
        </button>
        <a href="/opiekun/internship/{internship_id}" class="btn btn-ghost" style="margin-left:auto;">
          ← Powrót do praktyki
        </a>
      </div>
    </form>
  </div>
</div>
<footer>&copy; 2026 Akademia Nauk Stosowanych w Elblągu</footer>
</body></html>"""
    return page_html


@opiekun_bp.route('/list')
@mentor_required
def list_students():
    """Lista studentów przypisanych do opiekuna."""
    
    internships = Internship.query.filter_by(mentor_id=current_user.id).all()
    
    # Policz dokumenty do przeglądu dla każdej praktyki
    stats = {}
    for internship in internships:
        pending = DocumentSubmission.query.filter(
            DocumentSubmission.internship_id == internship.id,
            DocumentSubmission.status.in_(['submitted', 'pending_review'])
        ).count()
        stats[internship.id] = {
            'pending': pending,
            'approved': DocumentSubmission.query.filter_by(
                internship_id=internship.id,
                status='approved'
            ).count()
        }
    
    context = {
        'internships': internships,
        'stats': stats,
    }
    
    return render_template('opiekun/list_students.html', **context)


@opiekun_bp.route('/api/internships')
@mentor_required
def api_get_internships():
    """REST API: Pobierz praktyki gdzie mentor jest opiekunem."""
    
    internships = Internship.query.filter_by(mentor_id=current_user.id).all()
    
    return jsonify({
        'success': True,
        'data': [i.to_dict() for i in internships]
    })


@opiekun_bp.route('/api/documents/pending')
@mentor_required
def api_get_pending_documents():
    """REST API: Pobierz dokumenty czekające na przegląd."""
    
    # Pobierz praktyki gdzie mentor jest opiekunem
    my_internships = Internship.query.filter_by(mentor_id=current_user.id).with_entities(Internship.id).all()
    internship_ids = [i[0] for i in my_internships]
    
    # Pobierz dokumenty do przeglądu
    documents = DocumentSubmission.query.filter(
        DocumentSubmission.internship_id.in_(internship_ids),
        DocumentSubmission.status.in_(['submitted', 'pending_review'])
    ).all()
    
    return jsonify({
        'success': True,
        'count': len(documents),
        'data': [
            {
                'id': d.id,
                'student_name': d.user.full_name if d.user else 'Unknown',
                'attachment_name': d.attachment.name if d.attachment else 'Unknown',
                'status': d.status,
                'created_at': d.created_at.isoformat(),
            }
            for d in documents
        ]
    })


@opiekun_bp.route('/api/internship/<int:internship_id>/stats')
@mentor_required
def api_get_internship_stats(internship_id):
    """REST API: Statystyki praktyki."""
    
    internship = Internship.query.get(internship_id)
    
    if not internship or internship.mentor_id != current_user.id:
        return jsonify({'success': False, 'error': 'Brak dostępu'}), 403
    
    return jsonify({
        'success': True,
        'data': {
            'id': internship.id,
            'student_name': internship.student.full_name,
            'company_name': internship.company_name,
            'status': internship.status,
            'total_hours': internship.total_hours,
            'total_hours_worked': internship.total_hours_worked,
            'completion_percent': internship.completion_percent,
            'documents_count': len(internship.documents),
            'learning_outcomes_count': len(internship.learning_outcomes),
            'diary_entries_count': len(internship.diary_entries),
        }
    })
