from flask import Blueprint, render_template_string, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.auth.decorators import role_required
from app import db
from app.models import DocumentSubmission

OPIEKUN_PAGE = '''
<!doctype html>
<html lang="pl">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Panel opiekuna – System Praktyk ANS</title>
    <link rel="stylesheet" href="/static/css/style.css">
    </head>
<body>
<nav class="ans-navbar navbar-logged">
    <a class="brand" href="/auth/dashboard">
        <img src="/static/img/logo.png" alt="ANS Logo" onerror="this.style.display='none'">
        <div class="brand-text">Akademia Nauk Stosowanych <span>w Elblągu – System Praktyk</span></div>
    </a>
    <nav>
        <a href="/auth/dashboard">Dashboard</a>
        <a href="/opiekun/">Panel opiekuna</a>
        <a href="/auth/logout" class="btn-logout">Wyloguj</a>
    </nav>
</nav>
<div class="ans-header-strip"></div>
{{ content|safe }}
<footer class="ans-footer">&copy; 2026 Akademia Nauk Stosowanych w Elblągu</footer>
</body>
</html>
'''

opiekun_bp = Blueprint('opiekun', __name__)


@opiekun_bp.route('/')
@login_required
@role_required('opiekun')
def index():
    submissions = DocumentSubmission.query.order_by(DocumentSubmission.created_at.desc()).all()
    content = '<main style="padding:18px;"><h1>Panel opiekuna</h1>'
    content += '<h2>Zgłoszenia</h2><ul>'
    for s in submissions:
        content += f'<li>#{s.id} załącznik {s.attachment_id} - {s.status} - <a href="{url_for("opiekun.review", submission_id=s.id)}">Oceń</a></li>'
    content += '</ul></main>'
    return render_template_string(OPIEKUN_PAGE, content=content)


@opiekun_bp.route('/review/<int:submission_id>', methods=['GET', 'POST'])
@login_required
@role_required('opiekun')
def review(submission_id):
    s = DocumentSubmission.query.get_or_404(submission_id)
    if request.method == 'POST':
        decision = request.form.get('decision')
        comment = request.form.get('comment')
        s.comments = comment
        s.reviewer_id = current_user.id
        if decision == 'approve':
            s.status = 'approved'
        elif decision == 'return':
            s.status = 'returned'
        # allow storing assessment in data
        assessment = request.form.get('assessment')
        if assessment:
            d = s.data or {}
            d['assessment'] = assessment
            s.data = d
        db.session.commit()
        flash('Decyzja zapisana.')
        return redirect(url_for('opiekun.index'))

    # GET -> show submission details
    content = f"<main style='padding:18px;'><h1>Przegląd zgłoszenia #{s.id}</h1>"
    content += f"<p>Załącznik: {s.attachment_id}</p>"
    if s.file_path:
        content += f"<p>Plik: <a href='{url_for('student.download_submission', submission_id=s.id)}'>Pobierz</a></p>"
    content += f"<form method='post'><div><label>Komentarz:</label><br><textarea name='comment' rows='4' cols='60'>{s.comments or ''}</textarea></div>"
    content += "<div><label>Ocena merytoryczna (4a):</label><br><textarea name='assessment' rows='3' cols='60'>" + (s.data.get('assessment') if s.data else '') + "</textarea></div>"
    content += "<div><button name='decision' value='approve' type='submit'>Zatwierdź</button> <button name='decision' value='return' type='submit'>Zwróć do poprawy</button></div></form></main>"
    return render_template_string(OPIEKUN_PAGE, content=content)
