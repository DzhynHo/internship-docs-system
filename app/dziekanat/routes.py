"""
Panel dziekanatu / sekretariatu / dyrekcji.
Dostęp: dziekanat, sekretariat, dyrekcja, admin, administrator
"""
from flask import Blueprint, redirect, url_for, request, flash
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
import html as _html

from app import db
from app.models.user import User
from app.models.internship import Internship
from app.models import DocumentSubmission, Attachment
from app.auth.routes import _base, _navbar_logged

dziekanat_bp = Blueprint('dziekanat', __name__)

STAFF_ROLES = ('dziekanat', 'sekretariat', 'dyrekcja', 'admin', 'administrator')

GRADE_OPTIONS = [
    ('', '– wybierz –'),
    ('2.0', '2,0 – niedostateczny'),
    ('3.0', '3,0 – dostateczny'),
    ('3.5', '3,5 – dostateczny plus'),
    ('4.0', '4,0 – dobry'),
    ('4.5', '4,5 – dobry plus'),
    ('5.0', '5,0 – bardzo dobry'),
    ('zaliczone', 'zaliczone'),
    ('niezaliczone', 'niezaliczone'),
]

DOC_STATUS_LABELS = {
    'draft':          ('Szkic',         '#6b7280', '#f3f4f6'),
    'submitted':      ('Wysłany',       '#1d4ed8', '#eff6ff'),
    'pending_review': ('W weryfikacji', '#d97706', '#fffbeb'),
    'approved':       ('Zatwierdzony',  '#16a34a', '#f0fdf4'),
    'rejected':       ('Odrzucony',     '#dc2626', '#fef2f2'),
}


# ── Dekorator ─────────────────────────────────────────────────────────────────
def staff_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role not in STAFF_ROLES:
            flash("Brak dostępu.", "error")
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated


# ── Helpers ───────────────────────────────────────────────────────────────────
def _nav():
    role = getattr(current_user, 'role', '')
    label_map = {
        'dziekanat':   'Panel dziekanatu',
        'sekretariat': 'Panel sekretariatu',
        'dyrekcja':    'Panel dyrekcji',
        'admin':       'Panel admina',
        'administrator': 'Panel admina',
    }
    panel_label = label_map.get(role, 'Panel')
    return f"""
<nav style="background:#1a2744;display:flex;align-items:center;justify-content:space-between;
            padding:0 28px;height:68px;box-shadow:0 2px 12px rgba(0,0,0,.18);flex-shrink:0;">
  <a href="/dziekanat/" style="display:flex;align-items:center;gap:14px;text-decoration:none;">
    <img src="/static/img/logo.png" alt="ANS" style="height:44px;background:#fff;padding:4px;border-radius:4px;"
         onerror="this.style.display='none'">
    <div style="color:#fff;line-height:1.2;">
      <strong style="font-size:15px;font-weight:700;display:block;">Akademia Nauk Stosowanych</strong>
      <span style="font-size:12px;font-weight:300;color:rgba(255,255,255,.65);">w Elblągu – System Praktyk</span>
    </div>
  </a>
  <nav style="display:flex;align-items:center;gap:4px;">
    <a href="/auth/dashboard" style="color:rgba(255,255,255,.75);text-decoration:none;padding:7px 14px;
       border-radius:6px;font-size:13.5px;font-weight:500;">Dashboard</a>
    <a href="/dziekanat/" style="color:rgba(255,255,255,.75);text-decoration:none;padding:7px 14px;
       border-radius:6px;font-size:13.5px;font-weight:500;">{panel_label}</a>
    <a href="/dziekanat/students" style="color:rgba(255,255,255,.75);text-decoration:none;padding:7px 14px;
       border-radius:6px;font-size:13.5px;font-weight:500;">Studenci</a>
    <a href="/dziekanat/internships" style="color:rgba(255,255,255,.75);text-decoration:none;padding:7px 14px;
       border-radius:6px;font-size:13.5px;font-weight:500;">Praktyki</a>
    <a href="/auth/regulamin" style="color:rgba(255,255,255,.75);text-decoration:none;padding:7px 14px;
       border-radius:6px;font-size:13.5px;font-weight:500;">Regulamin PZ</a>
    <a href="/auth/logout" style="color:#fff;text-decoration:none;padding:7px 14px;border-radius:6px;
       font-size:13.5px;font-weight:500;background:rgba(255,255,255,.1);
       border:1px solid rgba(255,255,255,.2);">Wyloguj</a>
  </nav>
</nav>"""


def _page(title, content):
    role_badge_color = {
        'dziekanat': '#d97706', 'sekretariat': '#15803d',
        'dyrekcja': '#9333ea', 'admin': '#dc2626', 'administrator': '#dc2626',
    }
    color = role_badge_color.get(getattr(current_user, 'role', ''), '#6b7280')
    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{_html.escape(title)} – ANS System Praktyk</title>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'IBM Plex Sans',sans-serif;background:#f0f2f7;color:#111827;min-height:100vh;display:flex;flex-direction:column}}
    a{{color:#3b5bdb;text-decoration:none}}
    a:hover{{text-decoration:underline}}
    .strip{{height:4px;background:linear-gradient(90deg,#3b5bdb 0%,#0d9488 100%);flex-shrink:0}}
    .container{{max-width:1200px;margin:0 auto;padding:0 24px 48px;flex:1}}
    .page-header{{background:#fff;border-bottom:1px solid #dde1ef;padding:22px 0;margin-bottom:28px}}
    .page-header-inner{{max-width:1200px;margin:0 auto;padding:0 24px;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}}
    h1{{font-size:22px;font-weight:700;color:#1a2744}}
    .breadcrumb{{font-size:12.5px;color:#6b7280;margin-top:4px;display:flex;gap:6px;align-items:center}}
    .breadcrumb a{{color:#3b5bdb}}
    .stats-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:28px}}
    .stat-card{{background:#fff;border:1px solid #dde1ef;border-radius:10px;padding:18px 20px;
               display:flex;align-items:center;gap:14px;box-shadow:0 1px 3px rgba(26,39,68,.08)}}
    .stat-icon{{width:44px;height:44px;border-radius:10px;display:flex;align-items:center;
               justify-content:center;font-size:20px;flex-shrink:0}}
    .stat-val{{font-size:26px;font-weight:700;color:#1a2744;letter-spacing:-.5px;line-height:1}}
    .stat-label{{font-size:12px;color:#6b7280;margin-top:2px;font-weight:500}}
    .card{{background:#fff;border:1px solid #dde1ef;border-radius:10px;margin-bottom:20px;
          box-shadow:0 1px 3px rgba(26,39,68,.08)}}
    .card-header{{padding:16px 20px;border-bottom:1px solid #dde1ef;display:flex;
                 align-items:center;justify-content:space-between;gap:12px}}
    .card-header h2{{font-size:15px;font-weight:700;color:#1a2744}}
    .card-body{{padding:20px}}
    table{{width:100%;border-collapse:collapse;font-size:13px}}
    th{{padding:9px 14px;text-align:left;font-size:11.5px;font-weight:600;text-transform:uppercase;
       letter-spacing:.5px;color:#6b7280;border-bottom:2px solid #dde1ef;background:#f8f9fc}}
    td{{padding:11px 14px;border-bottom:1px solid #f0f0f5;color:#374151;vertical-align:middle}}
    tr:last-child td{{border-bottom:none}}
    tr:hover td{{background:#fafbff}}
    .badge{{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:20px;
           font-size:11.5px;font-weight:600;white-space:nowrap}}
    .btn{{display:inline-flex;align-items:center;gap:6px;padding:7px 14px;border-radius:6px;
         font-size:13px;font-weight:600;font-family:inherit;cursor:pointer;border:none;
         text-decoration:none;transition:all .15s;white-space:nowrap}}
    .btn-primary{{background:#3b5bdb;color:#fff!important}}
    .btn-primary:hover{{background:#2f4ac0;text-decoration:none}}
    .btn-ghost{{background:transparent;color:#374151!important;border:1px solid #dde1ef}}
    .btn-ghost:hover{{background:#f8f9fc;text-decoration:none}}
    .btn-teal{{background:#0d9488;color:#fff!important}}
    .btn-teal:hover{{background:#0a7c71;text-decoration:none}}
    .btn-amber{{background:#d97706;color:#fff!important}}
    .btn-amber:hover{{background:#b45309;text-decoration:none}}
    .form-group{{margin-bottom:16px}}
    .form-group label{{display:block;font-size:12px;font-weight:600;color:#374151;
                      text-transform:uppercase;letter-spacing:.4px;margin-bottom:5px}}
    .form-group input,.form-group select,.form-group textarea{{
      width:100%;border:1px solid #dde1ef;border-radius:6px;padding:9px 12px;
      font-size:13.5px;font-family:inherit;color:#111827;background:#fff;outline:none;
      transition:border .15s}}
    .form-group input:focus,.form-group select:focus,.form-group textarea:focus{{
      border-color:#3b5bdb;box-shadow:0 0 0 3px rgba(59,91,219,.1)}}
    .form-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
    .form-grid-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}}
    .alert{{padding:12px 16px;border-radius:6px;font-size:13px;margin-bottom:16px;border:1px solid}}
    .alert-info{{background:#eff6ff;border-color:#bfdbfe;color:#1d4ed8}}
    .alert-success{{background:#f0fdf4;border-color:#bbf7d0;color:#166534}}
    .alert-error{{background:#fef2f2;border-color:#fecaca;color:#991b1b}}
    .alert-warning{{background:#fffbeb;border-color:#fde68a;color:#92400e}}
    .role-tag{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;
              font-weight:700;background:{color}22;color:{color};border:1px solid {color}44}}
    footer{{padding:16px;text-align:center;color:#6b7280;font-size:12px;
           border-top:1px solid #dde1ef;background:#fff;margin-top:auto}}
    @media(max-width:900px){{.stats-row{{grid-template-columns:1fr 1fr}}.form-grid,.form-grid-3{{grid-template-columns:1fr}}}}
  </style>
</head>
<body>
{_nav()}
<div class="strip"></div>
{content}
<footer>&copy; 2026 <strong>Akademia Nauk Stosowanych w Elblągu</strong> – System Obsługi Praktyk</footer>
</body>
</html>"""


def _status_badge(status):
    label, color, bg = DOC_STATUS_LABELS.get(status, (status, '#6b7280', '#f3f4f6'))
    return f'<span class="badge" style="color:{color};background:{bg};">{label}</span>'


def _doc_status_summary(documents):
    """Mini-statystyki statusów dokumentów do nagłówka karty."""
    counts = {}
    for d in documents:
        if d.attachment_id is None:
            continue
        counts[d.status] = counts.get(d.status, 0) + 1
    parts = []
    for status, (label, color, bg) in DOC_STATUS_LABELS.items():
        n = counts.get(status, 0)
        if n:
            parts.append(
                f'<span style="font-size:12px;font-weight:600;color:{color};'
                f'background:{bg};padding:2px 8px;border-radius:20px;">'
                f'{n} {label}</span>'
            )
    return ' '.join(parts)


def _flashes():
    from flask import get_flashed_messages
    msgs = get_flashed_messages(with_categories=True)
    if not msgs:
        return ''
    cat_map = {'success': 'alert-success', 'error': 'alert-error',
               'warning': 'alert-warning', 'info': 'alert-info', 'message': 'alert-info'}
    return ''.join(
        f'<div class="alert {cat_map.get(c,"alert-info")}">{m}</div>'
        for c, m in msgs
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@dziekanat_bp.route('/')
@staff_required
def dashboard():
    internships = Internship.query.all()
    total = len(internships)
    active = sum(1 for i in internships if i.status == 'active')

    pending_docs = DocumentSubmission.query.filter(
        DocumentSubmission.status.in_(['submitted', 'pending_review'])
    ).count()

    protocols = DocumentSubmission.query.filter_by(attachment_id=13).count()

    # Wnioski oczekujące na rozpatrzenie
    pending_applications = Internship.query.filter_by(status='pending').all()
    students_without_internship = User.query.filter_by(role='student').filter(
        ~User.id.in_([i.student_id for i in Internship.query.all()])
    ).count()

    role = current_user.role
    role_labels = {
        'dziekanat': 'Dziekanat', 'sekretariat': 'Sekretariat',
        'dyrekcja': 'Dyrekcja', 'admin': 'Administrator', 'administrator': 'Administrator',
    }
    panel_title = f"Panel {role_labels.get(role, role)}"

    role_context = {
        'dziekanat': (
            '🏛️', '#d97706', '#fffbeb',
            'Dziekanat – obsługa administracyjna praktyk',
            'Zarządzasz dokumentacją, rozpatrujesz wnioski, wystawiasz protokoły egzaminacyjne (Zał. 8) '
            'i nadzujesz kompletność dokumentów wszystkich studentów.'
        ),
        'sekretariat': (
            '📋', '#15803d', '#f0fdf4',
            'Sekretariat Instytutu – obsługa kancelaryjno-administracyjna',
            'Obsługujesz dokumenty praktyk od strony kancelaryjnej: archiwizacja, korespondencja, '
            'koordynacja terminów. Masz wgląd we wszystkie praktyki i dokumenty.'
        ),
        'dyrekcja': (
            '🎓', '#9333ea', '#fdf4ff',
            'Dyrekcja Instytutu Informatyki Stosowanej im. K. Brzeskiego',
            'Jako dyrektor instytutu zatwierdzasz decyzje w sprawach praktyk, masz dostęp do pełnego '
            'przeglądu, wyników egzaminów i protokołów. To nie jest dyrekcja firmy przyjmującej studenta – '
            'to dyrekcja jednostki uczelnianej nadzorującej program praktyk zawodowych.'
        ),
    }
    ctx = role_context.get(role)
    role_banner = ''
    if ctx:
        icon, color, bg, ctx_title, ctx_desc = ctx
        role_banner = (
            f'<div style="background:{bg};border:1px solid {color}44;border-left:4px solid {color};'
            f'border-radius:8px;padding:14px 18px;margin-bottom:20px;">'
            f'<div style="font-weight:700;font-size:14px;color:{color};margin-bottom:4px;">{icon} {ctx_title}</div>'
            f'<div style="font-size:13px;color:#374151;line-height:1.6;">{ctx_desc}</div>'
            f'</div>'
        )

    rows = ''
    for i in Internship.query.order_by(Internship.id.desc()).limit(10).all():
        doc_count = len(i.documents)
        pending = sum(1 for d in i.documents if d.status in ('submitted', 'pending_review'))
        prot = DocumentSubmission.query.filter_by(internship_id=i.id, attachment_id=13).first()
        prot_badge = (_status_badge(prot.status) if prot
                      else '<span class="badge" style="color:#6b7280;background:#f3f4f6;">Brak</span>')
        intr_status_badge = {
            'active':    '<span class="badge" style="color:#16a34a;background:#f0fdf4;">Aktywna</span>',
            'completed': '<span class="badge" style="color:#1d4ed8;background:#eff6ff;">Ukończona</span>',
            'pending':   '<span class="badge" style="color:#d97706;background:#fffbeb;">Oczekuje</span>',
        }.get(i.status, f'<span class="badge" style="color:#6b7280;background:#f3f4f6;">{i.status}</span>')

        rows += f"""<tr>
          <td><a href="/dziekanat/internship/{i.id}"
               style="font-weight:600;color:#1a2744;">{_html.escape(i.student.full_name)}</a></td>
          <td>{_html.escape(i.company_name)}</td>
          <td style="white-space:nowrap;">{i.start_date.strftime('%d.%m.%Y')}<br>
            <span style="color:#9ca3af;font-size:11px;">{i.end_date.strftime('%d.%m.%Y')}</span></td>
          <td>{intr_status_badge}</td>
          <td style="text-align:center;">{doc_count}
            {f'<span style="color:#d97706;font-size:11px;"> ({pending} czeka)</span>' if pending else ''}
          </td>
          <td>{prot_badge}</td>
          <td style="white-space:nowrap;">
            <a href="/dziekanat/internship/{i.id}" class="btn btn-ghost" style="font-size:12px;padding:5px 10px;">
              Szczegóły →
            </a>
            <a href="/dziekanat/internship/{i.id}/protocol" class="btn btn-teal"
               style="font-size:12px;padding:5px 10px;margin-left:4px;">
              Protokół
            </a>
          </td>
        </tr>"""

    content = f"""
<div class="page-header">
  <div class="page-header-inner">
    <div>
      <h1>{panel_title}</h1>
      <div class="breadcrumb"><a href="/auth/dashboard">Dashboard</a> › <span>{panel_title}</span></div>
    </div>
    <span class="role-tag">{_html.escape(current_user.full_name or current_user.email)}</span>
  </div>
</div>
<div class="container">
  {_flashes()}
  {role_banner}

  {''.join(
    f'<div style="background:#fffbeb;border:1px solid #fde68a;border-left:4px solid #d97706;'
    f'border-radius:8px;padding:14px 18px;margin-bottom:12px;display:flex;align-items:center;'
    f'justify-content:space-between;gap:12px;">'
    f'<div><strong style="color:#92400e;font-size:13.5px;">⏳ Nowy wniosek: {_html.escape(a.student.full_name)}</strong>'
    f'<div style="font-size:12.5px;color:#78350f;margin-top:2px;">'
    f'Firma: <strong>{_html.escape(a.company_name)}</strong> · '
    f'{a.start_date.strftime("%d.%m.%Y")} – {a.end_date.strftime("%d.%m.%Y")}</div></div>'
    f'<a href="/dziekanat/application/{a.id}/review" class="btn btn-amber" '
    f'style="font-size:12px;padding:6px 14px;flex-shrink:0;background:#d97706;color:#fff;">Rozpatrz →</a></div>'
    for a in pending_applications
  )}

  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-icon" style="background:#eff3ff;">🎓</div>
      <div><div class="stat-val">{total}</div><div class="stat-label">Wszystkie praktyki</div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon" style="background:#fffbeb;">⏳</div>
      <div><div class="stat-val">{len(pending_applications)}</div><div class="stat-label">Wnioski do rozpatrzenia</div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon" style="background:#f0fdf4;">✅</div>
      <div><div class="stat-val">{active}</div><div class="stat-label">Aktywne</div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon" style="background:#f5f3ff;">📋</div>
      <div><div class="stat-val">{protocols}</div><div class="stat-label">Protokołów wystawionych</div></div>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <h2>📋 Wszystkie praktyki</h2>
      <div style="display:flex;gap:8px;">
        <a href="/dziekanat/internship/create" class="btn btn-primary" style="font-size:12px;">
          ＋ Nowa praktyka
        </a>
        <a href="/dziekanat/internships" class="btn btn-ghost" style="font-size:12px;">
          Pełna lista →
        </a>
      </div>
    </div>
    <div style="overflow-x:auto;">
      <table>
        <thead><tr>
          <th>Student</th><th>Firma</th><th>Termin</th>
          <th>Status</th><th style="text-align:center;">Dokumenty</th>
          <th>Protokół</th><th>Akcje</th>
        </tr></thead>
        <tbody>{rows if rows else '<tr><td colspan="7" style="text-align:center;color:#9ca3af;padding:24px;">Brak praktyk</td></tr>'}</tbody>
      </table>
    </div>
  </div>
</div>"""
    return _page(panel_title, content)


@dziekanat_bp.route('/internships')
@staff_required
def list_internships():
    search = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '')

    query = Internship.query
    if search:
        query = query.join(User, Internship.student_id == User.id).filter(
            User.full_name.ilike(f'%{search}%') | Internship.company_name.ilike(f'%{search}%')
        )
    if status_filter:
        query = query.filter(Internship.status == status_filter)

    internships = query.order_by(Internship.id.desc()).all()

    rows = ''
    for i in internships:
        doc_count = len(i.documents)
        approved = sum(1 for d in i.documents if d.status == 'approved')
        pending = sum(1 for d in i.documents if d.status in ('submitted', 'pending_review'))
        rejected = sum(1 for d in i.documents if d.status == 'rejected')
        prot = DocumentSubmission.query.filter_by(internship_id=i.id, attachment_id=13).first()
        rows += f"""<tr>
          <td><a href="/dziekanat/internship/{i.id}" style="font-weight:600;color:#1a2744;">
            {_html.escape(i.student.full_name)}</a><br>
            <span style="font-size:11px;color:#9ca3af;">{_html.escape(i.student.email)}</span>
          </td>
          <td>{_html.escape(i.company_name)}</td>
          <td>{i.start_date.strftime('%d.%m.%Y')} – {i.end_date.strftime('%d.%m.%Y')}</td>
          <td><span style="color:#{'16a34a' if i.status=='active' else '6b7280'};">{i.status}</span></td>
          <td style="text-align:center;">
            <span style="color:#16a34a;">{approved}✓</span> /
            <span style="color:#d97706;">{pending}⏳</span> /
            <span style="color:#dc2626;">{rejected}✗</span>
          </td>
          <td>{_status_badge(prot.status) if prot else '<span style="color:#9ca3af;font-size:12px;">brak</span>'}</td>
          <td>
            <a href="/dziekanat/internship/{i.id}" class="btn btn-ghost" style="font-size:12px;padding:5px 10px;">
              Otwórz
            </a>
            <a href="/dziekanat/internship/{i.id}/protocol" class="btn btn-teal"
               style="font-size:12px;padding:5px 10px;margin-left:4px;">
              Protokół
            </a>
          </td>
        </tr>"""

    search_val = _html.escape(search)
    content = f"""
<div class="page-header">
  <div class="page-header-inner">
    <div>
      <h1>Lista praktyk zawodowych</h1>
      <div class="breadcrumb">
        <a href="/dziekanat/">Panel</a> › <span>Wszystkie praktyki</span>
      </div>
    </div>
  </div>
</div>
<div class="container">
  {_flashes()}
  <div class="card" style="margin-bottom:20px;">
    <div class="card-body" style="padding:16px 20px;">
      <form method="get" style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;">
        <div style="flex:1;min-width:200px;">
          <label style="font-size:12px;font-weight:600;color:#6b7280;display:block;margin-bottom:4px;">
            SZUKAJ (student / firma)
          </label>
          <input type="text" name="q" value="{search_val}"
                 placeholder="Nazwisko studenta lub nazwa firmy..."
                 style="width:100%;border:1px solid #dde1ef;border-radius:6px;padding:8px 12px;font-size:13px;">
        </div>
        <div>
          <label style="font-size:12px;font-weight:600;color:#6b7280;display:block;margin-bottom:4px;">
            STATUS
          </label>
          <select name="status" style="border:1px solid #dde1ef;border-radius:6px;padding:8px 12px;font-size:13px;">
            <option value="">Wszystkie</option>
            <option value="active" {'selected' if status_filter=='active' else ''}>Aktywne</option>
            <option value="completed" {'selected' if status_filter=='completed' else ''}>Ukończone</option>
            <option value="pending" {'selected' if status_filter=='pending' else ''}>Oczekujące</option>
          </select>
        </div>
        <button type="submit" class="btn btn-primary">🔍 Szukaj</button>
        <a href="/dziekanat/internships" class="btn btn-ghost">Wyczyść</a>
      </form>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <h2>Praktyki ({len(internships)})</h2>
    </div>
    <div style="overflow-x:auto;">
      <table>
        <thead><tr>
          <th>Student</th><th>Firma</th><th>Termin</th><th>Status</th>
          <th style="text-align:center;">Dokumenty (zatw/czeka/odrzuc)</th>
          <th>Protokół</th><th>Akcje</th>
        </tr></thead>
        <tbody>{rows if rows else '<tr><td colspan="7" style="text-align:center;color:#9ca3af;padding:24px;">Brak wyników</td></tr>'}</tbody>
      </table>
    </div>
  </div>
</div>"""
    return _page("Lista praktyk", content)


@dziekanat_bp.route('/internship/<int:internship_id>')
@staff_required
def view_internship(internship_id):
    internship = Internship.query.get_or_404(internship_id)
    documents = DocumentSubmission.query.filter_by(internship_id=internship_id).all()

    att_names = {a.id: a.name for a in Attachment.query.all()}

    # Grupowanie dokumentów po statusie
    STATUS_ORDER = ['submitted', 'pending_review', 'rejected', 'draft', 'approved']
    docs_sorted = sorted(documents, key=lambda d: (
        STATUS_ORDER.index(d.status) if d.status in STATUS_ORDER else 99,
        d.attachment_id or 0
    ))

    doc_rows = ''
    for doc in docs_sorted:
        if doc.attachment_id is None:
            continue  # Pomijaj wnioski wewnętrzne
        att_name = att_names.get(doc.attachment_id, f'Dokument #{doc.id}')
        reviewer = doc.reviewer.full_name if doc.reviewer else '–'
        updated = doc.updated_at.strftime('%d.%m.%Y %H:%M') if doc.updated_at else '–'

        comment_cell = ''
        if doc.comments:
            escaped = _html.escape(doc.comments[:100]) + ('…' if len(doc.comments) > 100 else '')
            comment_cell = f'<div style="font-size:11.5px;color:#6b7280;margin-top:3px;font-style:italic;">{escaped}</div>'

        has_data = bool(doc.data)
        has_file = bool(getattr(doc, 'file_path', None))

        view_btn = (f'<a href="/dziekanat/document/{doc.id}" '
                    f'class="btn btn-primary" style="font-size:11.5px;padding:4px 10px;">'
                    f'👁 Otwórz</a>')
        if has_file:
            view_btn += (f'<a href="/student/submission/{doc.id}/download" '
                         f'class="btn btn-ghost" style="font-size:11.5px;padding:4px 10px;margin-left:4px;">'
                         f'📥 Plik</a>')

        # Czy dokument ma podpis dziekanatu
        dz_signed = (doc.data or {}).get('_dz_signed')
        sign_indicator = ''
        if dz_signed:
            sign_indicator = ('<span style="font-size:11px;color:#0d9488;font-weight:600;'
                              'margin-left:6px;">🖊 podpisano</span>')

        doc_rows += f"""<tr style="{'background:#f0fdf4;' if doc.status=='approved' else ''}">
          <td>
            <div style="font-weight:600;font-size:13px;">{_html.escape(att_name)}{sign_indicator}</div>
            {comment_cell}
          </td>
          <td>{_status_badge(doc.status)}</td>
          <td style="font-size:12.5px;color:#374151;">{_html.escape(reviewer)}</td>
          <td style="font-size:12px;color:#9ca3af;white-space:nowrap;">{updated}</td>
          <td style="white-space:nowrap;">{view_btn}</td>
        </tr>"""

    prot = DocumentSubmission.query.filter_by(internship_id=internship_id, attachment_id=13).first()
    prot_section = ''
    if prot:
        d = prot.data or {}
        prot_section = f"""
        <div class="alert alert-success" style="margin-top:0;">
          ✅ Protokół egzaminu wystawiony — ocena: <strong>{_html.escape(d.get('ocena_koncowa','–'))}</strong>
          &nbsp;&nbsp;
          <a href="/dziekanat/internship/{internship_id}/protocol" class="btn btn-ghost"
             style="font-size:12px;padding:4px 10px;margin-left:8px;">Edytuj</a>
        </div>"""
    else:
        prot_section = f"""
        <div class="alert alert-warning">
          ⚠️ Protokół egzaminu (Załącznik nr 8) nie został jeszcze wystawiony.
          <a href="/dziekanat/internship/{internship_id}/protocol" class="btn btn-primary"
             style="font-size:12px;padding:5px 12px;margin-left:12px;">Wystaw protokół →</a>
        </div>"""

    mentor_name = internship.mentor.full_name if internship.mentor else 'Nie przypisany'

    content = f"""
<div class="page-header">
  <div class="page-header-inner">
    <div>
      <h1>{_html.escape(internship.student.full_name)}</h1>
      <div class="breadcrumb">
        <a href="/dziekanat/">Panel</a> ›
        <a href="/dziekanat/internships">Praktyki</a> ›
        <span>{_html.escape(internship.company_name)}</span>
      </div>
    </div>
    <div style="display:flex;gap:8px;">
      <a href="/dziekanat/internship/{internship_id}/edit" class="btn btn-ghost">
        ✏️ Edytuj
      </a>
      <a href="/dziekanat/internship/{internship_id}/protocol" class="btn btn-teal">
        📋 Protokół
      </a>

    </div>
  </div>
</div>
<div class="container">
  {_flashes()}
  {prot_section}

  <div style="display:grid;grid-template-columns:2fr 1fr;gap:20px;">
    <div>
      <div class="card">
        <div class="card-header"><h2>Informacje o praktyce</h2></div>
        <div class="card-body">
          <div class="form-grid">
            <div><div style="font-size:11.5px;color:#6b7280;font-weight:600;margin-bottom:3px;">STUDENT</div>
              <div style="font-weight:600;">{_html.escape(internship.student.full_name)}</div>
              <div style="font-size:12px;color:#9ca3af;">{_html.escape(internship.student.email)}</div>
            </div>
            <div><div style="font-size:11.5px;color:#6b7280;font-weight:600;margin-bottom:3px;">FIRMA</div>
              <div style="font-weight:600;">{_html.escape(internship.company_name)}</div>
            </div>
            <div><div style="font-size:11.5px;color:#6b7280;font-weight:600;margin-bottom:3px;">TERMIN</div>
              <div>{internship.start_date.strftime('%d.%m.%Y')} – {internship.end_date.strftime('%d.%m.%Y')}</div>
            </div>
            <div><div style="font-size:11.5px;color:#6b7280;font-weight:600;margin-bottom:3px;">OPIEKUN</div>
              <div>{_html.escape(mentor_name)}</div>
            </div>
            <div><div style="font-size:11.5px;color:#6b7280;font-weight:600;margin-bottom:3px;">GODZINY</div>
              <div>{internship.total_hours_worked} / {internship.total_hours} h</div>
            </div>
            <div><div style="font-size:11.5px;color:#6b7280;font-weight:600;margin-bottom:3px;">STATUS</div>
              <div>{internship.status}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2>Dokumenty ({len([d for d in documents if d.attachment_id])})</h2>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            {_doc_status_summary(documents)}
          </div>
        </div>
        <div style="overflow-x:auto;">
          <table>
            <thead><tr>
              <th>Załącznik</th>
              <th>Status</th>
              <th>Recenzent</th>
              <th>Ostatnia zmiana</th>
              <th>Akcje</th>
            </tr></thead>
            <tbody>{doc_rows if doc_rows else '<tr><td colspan="5" style="text-align:center;color:#9ca3af;padding:20px;">Brak dokumentów</td></tr>'}</tbody>
          </table>
        </div>
      </div>
    </div>

    <div>
      <div class="card">
        <div class="card-header"><h2>Szybkie akcje</h2></div>
        <div class="card-body" style="display:flex;flex-direction:column;gap:10px;">
          <a href="/dziekanat/internship/{internship_id}/protocol" class="btn btn-teal" style="justify-content:center;">
            📋 Protokół egzaminu (Zał. 8)
          </a>
          <a href="/dziekanat/internship/{internship_id}/edit" class="btn btn-ghost" style="justify-content:center;">
            ✏️ Edytuj praktykę
          </a>
          <a href="/dziekanat/internship/create" class="btn btn-primary" style="justify-content:center;">
            ＋ Nowa praktyka
          </a>
          <a href="/dziekanat/internships" class="btn btn-ghost" style="justify-content:center;">
            ← Powrót do listy
          </a>
        </div>
      </div>

      <div class="card" style="margin-top:0;">
        <div class="card-header"><h2>Postęp dokumentów</h2></div>
        <div class="card-body">
          {''.join(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:6px 0;border-bottom:1px solid #f0f0f5;font-size:13px;">'
            f'<span style="color:#374151;">{_html.escape(att_names.get(d.attachment_id,f"#{d.id}"))}</span>'
            f'{_status_badge(d.status)}</div>'
            for d in sorted(documents, key=lambda x: x.attachment_id or 0)
          ) or '<div style="color:#9ca3af;font-size:13px;">Brak dokumentów</div>'}
        </div>
      </div>
    </div>
  </div>
</div>"""
    return _page(f"Praktyka – {internship.student.full_name}", content)


@dziekanat_bp.route('/internship/<int:internship_id>/protocol', methods=['GET', 'POST'])
@staff_required
def protocol(internship_id):
    """Protokół egzaminu praktyki zawodowej – Załącznik nr 8."""
    internship = Internship.query.get_or_404(internship_id)

    doc = DocumentSubmission.query.filter_by(
        internship_id=internship_id,
        attachment_id=13
    ).first()

    saved = doc.data if (doc and doc.data) else {}

    def v(key, default=''):
        val = saved.get(key, default)
        return val if val is not None else default

    if request.method == 'POST':
        action = request.form.get('action', 'save')
        data = {
            'data_egzaminu':    request.form.get('data_egzaminu', '').strip(),
            'przewodniczacy':   request.form.get('przewodniczacy', '').strip(),
            'czlonek1':         request.form.get('czlonek1', '').strip(),
            'czlonek2':         request.form.get('czlonek2', '').strip(),
            'ocena_dziennik':   request.form.get('ocena_dziennik', '').strip(),
            'ocena_sprawozdanie': request.form.get('ocena_sprawozdanie', '').strip(),
            'ocena_koncowa':    request.form.get('ocena_koncowa', '').strip(),
            'uwagi':            request.form.get('uwagi', '').strip(),
            'zaliczone':        request.form.get('zaliczone', 'tak'),
        }

        if not doc:
            doc = DocumentSubmission(
                user_id=current_user.id,
                internship_id=internship_id,
                attachment_id=13,
                status='draft'
            )
            db.session.add(doc)

        doc.data = data
        doc.reviewer_id = current_user.id
        doc.updated_at = datetime.utcnow()

        if action == 'finalize':
            doc.status = 'approved'
            flash("Protokół zatwierdzony i dostępny dla studenta.", "success")
        else:
            doc.status = 'draft'
            flash("Protokół zapisany jako szkic.", "info")

        db.session.commit()
        return redirect(url_for('dziekanat.view_internship', internship_id=internship_id))

    grade_opts_html = ''.join(
        f'<option value="{val}" {"selected" if v("ocena_dziennik") == val else ""}>{_html.escape(label)}</option>'
        for val, label in GRADE_OPTIONS
    )
    grade_opts_spr = ''.join(
        f'<option value="{val}" {"selected" if v("ocena_sprawozdanie") == val else ""}>{_html.escape(label)}</option>'
        for val, label in GRADE_OPTIONS
    )
    grade_opts_konc = ''.join(
        f'<option value="{val}" {"selected" if v("ocena_koncowa") == val else ""}>{_html.escape(label)}</option>'
        for val, label in GRADE_OPTIONS
    )

    status_banner = ''
    if doc and doc.status == 'approved':
        status_banner = '<div class="alert alert-success">✅ Protokół jest zatwierdzony i widoczny dla studenta i opiekuna.</div>'
    elif doc and doc.status == 'draft':
        status_banner = '<div class="alert alert-warning">⚠️ Protokół zapisany jako szkic – student i opiekun nie widzą go jeszcze.</div>'

    content = f"""
<div class="page-header">
  <div class="page-header-inner">
    <div>
      <h1>Protokół egzaminu praktyki zawodowej</h1>
      <div class="breadcrumb">
        <a href="/dziekanat/">Panel</a> ›
        <a href="/dziekanat/internship/{internship_id}">
          {_html.escape(internship.student.full_name)}
        </a> ›
        <span>Załącznik nr 8</span>
      </div>
    </div>
    {'<span class="badge" style="color:#16a34a;background:#f0fdf4;font-size:13px;padding:6px 14px;">ZATWIERDZONY</span>' if (doc and doc.status == 'approved') else '<span class="badge" style="color:#d97706;background:#fffbeb;font-size:13px;padding:6px 14px;">SZKIC</span>'}
  </div>
</div>
<div class="container">
  {_flashes()}
  {status_banner}

  <div style="background:#fff;border:1px solid #dde1ef;border-radius:10px;
              padding:32px 36px;max-width:860px;">

    <div style="text-align:right;font-size:11px;color:#9ca3af;margin-bottom:8px;">
      Załącznik nr 8
    </div>
    <div style="font-size:12px;margin-bottom:20px;">
      <strong style="font-size:13px;">Akademia Nauk Stosowanych w Elblągu</strong><br>
      <span style="font-style:italic;color:#6b7280;">
        Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego
      </span>
    </div>

    <div style="text-align:center;margin-bottom:28px;">
      <div style="font-weight:700;font-size:15px;text-transform:uppercase;
                  letter-spacing:.5px;color:#1a202c;line-height:1.5;">
        PROTOKÓŁ EGZAMINU<br>PRAKTYKI ZAWODOWEJ
      </div>
    </div>

    <div style="background:#f7fafc;border:1px solid #e2e8f0;border-radius:8px;
                padding:16px 20px;margin-bottom:24px;">
      <div class="form-grid">
        <div>
          <div style="font-size:11.5px;color:#6b7280;font-weight:600;margin-bottom:2px;">STUDENT</div>
          <div style="font-weight:600;font-size:14px;">{_html.escape(internship.student.full_name)}</div>
        </div>
        <div>
          <div style="font-size:11.5px;color:#6b7280;font-weight:600;margin-bottom:2px;">FIRMA</div>
          <div style="font-weight:600;">{_html.escape(internship.company_name)}</div>
        </div>
        <div>
          <div style="font-size:11.5px;color:#6b7280;font-weight:600;margin-bottom:2px;">KIERUNEK</div>
          <div>Informatyka</div>
        </div>
        <div>
          <div style="font-size:11.5px;color:#6b7280;font-weight:600;margin-bottom:2px;">TERMIN PRAKTYKI</div>
          <div>{internship.start_date.strftime('%d.%m.%Y')} – {internship.end_date.strftime('%d.%m.%Y')}</div>
        </div>
        <div>
          <div style="font-size:11.5px;color:#6b7280;font-weight:600;margin-bottom:2px;">ZREALIZOWANE GODZINY</div>
          <div><strong>{internship.total_hours_worked}</strong> / {internship.total_hours} h</div>
        </div>
        <div>
          <div style="font-size:11.5px;color:#6b7280;font-weight:600;margin-bottom:2px;">OPIEKUN ZAKŁADOWY</div>
          <div>{_html.escape(internship.mentor.full_name if internship.mentor else '–')}</div>
        </div>
      </div>
    </div>

    <form method="post">
      <div class="form-group">
        <label>Data egzaminu <span style="color:#dc2626;">*</span></label>
        <input type="date" name="data_egzaminu" value="{_html.escape(v('data_egzaminu'))}"
               style="max-width:200px;">
      </div>

      <div style="margin-bottom:20px;">
        <div style="font-weight:600;font-size:13px;color:#374151;margin-bottom:12px;
                    text-transform:uppercase;letter-spacing:.4px;">Skład komisji</div>
        <div class="form-group">
          <label>Przewodniczący komisji</label>
          <input type="text" name="przewodniczacy"
                 value="{_html.escape(v('przewodniczacy'))}"
                 placeholder="dr inż. Jan Kowalski">
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label>Członek komisji 1</label>
            <input type="text" name="czlonek1" value="{_html.escape(v('czlonek1'))}"
                   placeholder="mgr Anna Nowak">
          </div>
          <div class="form-group">
            <label>Członek komisji 2</label>
            <input type="text" name="czlonek2" value="{_html.escape(v('czlonek2'))}"
                   placeholder="opcjonalnie">
          </div>
        </div>
      </div>

      <div style="margin-bottom:20px;">
        <div style="font-weight:600;font-size:13px;color:#374151;margin-bottom:12px;
                    text-transform:uppercase;letter-spacing:.4px;">Oceny</div>
        <div class="form-grid-3">
          <div class="form-group">
            <label>Ocena dziennika</label>
            <select name="ocena_dziennik">{grade_opts_html}</select>
          </div>
          <div class="form-group">
            <label>Ocena sprawozdania</label>
            <select name="ocena_sprawozdanie">{grade_opts_spr}</select>
          </div>
          <div class="form-group">
            <label>Ocena końcowa <span style="color:#dc2626;">*</span></label>
            <select name="ocena_koncowa">{grade_opts_konc}</select>
          </div>
        </div>
      </div>

      <div class="form-group">
        <label>Uwagi komisji</label>
        <textarea name="uwagi" rows="4"
                  placeholder="Opcjonalne uwagi dotyczące przebiegu egzaminu...">{_html.escape(v('uwagi'))}</textarea>
      </div>

      <div style="background:#f7fafc;border:1px solid #e2e8f0;border-radius:6px;
                  padding:12px 16px;margin-bottom:24px;font-size:13px;">
        <strong>Praktyka:</strong>
        <label style="margin-left:16px;display:inline-flex;align-items:center;gap:6px;cursor:pointer;">
          <input type="radio" name="zaliczone" value="tak"
                 {'checked' if v('zaliczone','tak') == 'tak' else ''}
                 style="accent-color:#16a34a;">
          <span style="color:#16a34a;font-weight:600;">Zaliczona</span>
        </label>
        <label style="margin-left:16px;display:inline-flex;align-items:center;gap:6px;cursor:pointer;">
          <input type="radio" name="zaliczone" value="nie"
                 {'checked' if v('zaliczone','tak') == 'nie' else ''}
                 style="accent-color:#dc2626;">
          <span style="color:#dc2626;font-weight:600;">Niezaliczona</span>
        </label>
      </div>

      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;
                  border-top:1px solid #e2e8f0;padding-top:20px;">
        <button type="submit" name="action" value="save" class="btn btn-ghost">
          💾 Zapisz szkic
        </button>
        <button type="submit" name="action" value="finalize" class="btn btn-teal"
                onclick="return confirm('Zatwierdzić protokół? Stanie się widoczny dla studenta i opiekuna.')">
          ✅ Zatwierdź protokół
        </button>
        <a href="/dziekanat/internship/{internship_id}" class="btn btn-ghost" style="margin-left:auto;">
          ← Powrót
        </a>
      </div>
    </form>
  </div>
</div>"""
    return _page("Protokół egzaminu – Zał. 8", content)


@dziekanat_bp.route('/protocol/<int:doc_id>/view')
@login_required
def view_protocol(doc_id):
    """Widok protokołu dla studenta, opiekuna, dziekanatu, dyrekcji."""
    doc = DocumentSubmission.query.get_or_404(doc_id)
    internship = doc.internship

    # Kontrola dostępu
    user = current_user
    allowed = False
    if user.role in STAFF_ROLES:
        allowed = True
    elif user.role == 'student' and internship.student_id == user.id:
        allowed = doc.status == 'approved'
    elif user.role == 'opiekun' and internship.mentor_id == user.id:
        allowed = doc.status == 'approved'

    if not allowed:
        flash("Brak dostępu do tego protokołu.", "error")
        return redirect(url_for('auth.dashboard'))

    d = doc.data or {}

    def dv(key):
        return _html.escape(str(d.get(key, '–') or '–'))

    content = f"""
<div class="page-header">
  <div class="page-header-inner">
    <div>
      <h1>Protokół egzaminu praktyki zawodowej</h1>
      <div class="breadcrumb">
        <a href="/auth/dashboard">Dashboard</a> ›
        <span>Protokół – Załącznik nr 8</span>
      </div>
    </div>
    {'<span class="badge" style="color:#16a34a;background:#f0fdf4;font-size:13px;padding:6px 14px;">ZATWIERDZONY</span>' if doc.status == 'approved' else '<span class="badge" style="color:#d97706;background:#fffbeb;font-size:13px;padding:6px 14px;">SZKIC</span>'}
  </div>
</div>
<div class="container">
  <div style="background:#fff;border:1px solid #dde1ef;border-radius:10px;
              padding:32px 36px;max-width:760px;">
    <div style="text-align:right;font-size:11px;color:#9ca3af;margin-bottom:6px;">Załącznik nr 8</div>
    <div style="font-size:12px;margin-bottom:16px;">
      <strong>Akademia Nauk Stosowanych w Elblągu</strong><br>
      <span style="font-style:italic;color:#6b7280;">Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego</span>
    </div>
    <div style="text-align:center;font-weight:700;font-size:15px;text-transform:uppercase;
                letter-spacing:.5px;margin-bottom:24px;color:#1a2744;">
      PROTOKÓŁ EGZAMINU PRAKTYKI ZAWODOWEJ
    </div>

    <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:24px;">
      {''.join(f'<tr><td style="padding:8px 12px;font-weight:600;color:#6b7280;border:1px solid #e2e8f0;width:200px;">{k}</td><td style="padding:8px 12px;border:1px solid #e2e8f0;">{v_}</td></tr>' for k,v_ in [
        ('Student', _html.escape(internship.student.full_name)),
        ('Firma / instytucja', _html.escape(internship.company_name)),
        ('Kierunek', 'Informatyka'),
        ('Termin praktyki', f"{internship.start_date.strftime('%d.%m.%Y')} – {internship.end_date.strftime('%d.%m.%Y')}"),
        ('Zrealizowane godziny', f"{internship.total_hours_worked} h"),
        ('Data egzaminu', dv('data_egzaminu')),
        ('Przewodniczący komisji', dv('przewodniczacy')),
        ('Członek komisji 1', dv('czlonek1')),
        ('Członek komisji 2', dv('czlonek2')),
        ('Ocena dziennika', dv('ocena_dziennik')),
        ('Ocena sprawozdania', dv('ocena_sprawozdanie')),
        ('Ocena końcowa', dv('ocena_koncowa')),
        ('Praktyka', '✅ Zaliczona' if d.get('zaliczone') == 'tak' else '❌ Niezaliczona'),
        ('Uwagi', dv('uwagi')),
      ])}
    </table>

    <div style="display:flex;justify-content:space-between;margin-top:40px;">
      <div style="text-align:center;width:220px;">
        <div style="border-top:1px solid #374151;padding-top:6px;font-size:12px;color:#6b7280;">
          Podpis przewodniczącego komisji
        </div>
      </div>
      <div style="text-align:center;width:220px;">
        <div style="border-top:1px solid #374151;padding-top:6px;font-size:12px;color:#6b7280;">
          Data, pieczęć
        </div>
      </div>
    </div>

    <div style="margin-top:24px;padding-top:16px;border-top:1px solid #e2e8f0;">
      {'<a href="/dziekanat/internship/' + str(internship.id) + '/protocol" class="btn btn-ghost">← Edytuj protokół</a>' if current_user.role in STAFF_ROLES else '<a href="/auth/dashboard" class="btn btn-ghost">← Powrót</a>'}
    </div>
  </div>
</div>"""
    return _page("Protokół egzaminu", content)


# ── Tworzenie i edycja praktyk ────────────────────────────────────────────────

def _internship_form_html(students, opiekunowie, saved=None, errors=None,
                          title="Utwórz nową praktykę", action_url="#",
                          back_url="/dziekanat/internships"):
    """Wspólny HTML formularza tworzenia/edycji praktyki."""
    s = saved or {}

    def sel_students():
        opts = '<option value="">– wybierz studenta –</option>'
        for u in students:
            sel = "selected" if str(s.get("student_id", "")) == str(u.id) else ""
            opts += f'<option value="{u.id}" {sel}>{_html.escape(u.full_name or u.email or "")} ({_html.escape(u.email or "")})</option>'
        return opts

    def sel_opiekunowie():
        opts = '<option value="">– brak opiekuna –</option>'
        for u in opiekunowie:
            sel = "selected" if str(s.get("mentor_id", "")) == str(u.id) else ""
            opts += f'<option value="{u.id}" {sel}>{_html.escape(u.full_name or u.email or "")} ({_html.escape(u.email or "")})</option>'
        return opts

    def sel_status():
        opts = ""
        for val, label in [("active","Aktywna"),("pending","Oczekująca"),
                            ("completed","Ukończona"),("cancelled","Anulowana")]:
            sel = "selected" if s.get("status", "active") == val else ""
            opts += f'<option value="{val}" {sel}>{label}</option>'
        return opts

    def v(key, default=""):
        return _html.escape(str(s.get(key, default) or ""))

    errors_html = ""
    if errors:
        errors_html = ('<div class="alert alert-error" style="margin-bottom:16px;">'
                       + "<br>".join(_html.escape(e) for e in errors) + "</div>")

    return f"""
    <div style="background:#fff;border:1px solid #dde1ef;border-radius:10px;
                padding:28px 32px;max-width:820px;">
      <h2 style="font-size:17px;font-weight:700;color:#1a2744;margin-bottom:20px;">
        {_html.escape(title)}
      </h2>
      {errors_html}
      <form method="post" action="{action_url}">

        <div style="font-size:11.5px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.5px;color:#6b7280;margin:0 0 12px;
                    padding-bottom:6px;border-bottom:1px solid #e2e8f0;">
          Uczestnik
        </div>
        <div class="form-grid" style="margin-bottom:20px;">
          <div class="form-group">
            <label>Student <span style="color:#dc2626;">*</span></label>
            <select name="student_id" required>{sel_students()}</select>
          </div>
          <div class="form-group">
            <label>Opiekun zakładowy</label>
            <select name="mentor_id">{sel_opiekunowie()}</select>
          </div>
        </div>

        <div style="font-size:11.5px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.5px;color:#6b7280;margin:0 0 12px;
                    padding-bottom:6px;border-bottom:1px solid #e2e8f0;">
          Firma / instytucja
        </div>
        <div class="form-group" style="margin-bottom:14px;">
          <label>Nazwa zakładu pracy <span style="color:#dc2626;">*</span></label>
          <input type="text" name="company_name" value="{v('company_name')}"
                 required placeholder="Pełna nazwa firmy">
        </div>
        <div class="form-grid" style="margin-bottom:14px;">
          <div class="form-group">
            <label>Adres</label>
            <input type="text" name="company_address" value="{v('company_address')}"
                   placeholder="ul. Przykładowa 1, 82-300 Elbląg">
          </div>
          <div class="form-group">
            <label>Telefon</label>
            <input type="text" name="company_phone" value="{v('company_phone')}"
                   placeholder="55 123 45 67">
          </div>
        </div>
        <div class="form-group" style="margin-bottom:20px;">
          <label>E-mail firmy</label>
          <input type="email" name="company_email" value="{v('company_email')}"
                 placeholder="kontakt@firma.pl">
        </div>

        <div style="font-size:11.5px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.5px;color:#6b7280;margin:0 0 12px;
                    padding-bottom:6px;border-bottom:1px solid #e2e8f0;">
          Termin i warunki
        </div>
        <div class="form-grid" style="margin-bottom:14px;">
          <div class="form-group">
            <label>Data rozpoczęcia <span style="color:#dc2626;">*</span></label>
            <input type="date" name="start_date" value="{v('start_date')}" required>
          </div>
          <div class="form-group">
            <label>Data zakończenia <span style="color:#dc2626;">*</span></label>
            <input type="date" name="end_date" value="{v('end_date')}" required>
          </div>
        </div>
        <div class="form-grid" style="margin-bottom:20px;">
          <div class="form-group">
            <label>Wymagana liczba godzin</label>
            <input type="number" name="total_hours" value="{v('total_hours', '480')}"
                   min="1" placeholder="480">
          </div>
          <div class="form-group">
            <label>Status</label>
            <select name="status">{sel_status()}</select>
          </div>
        </div>

        <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;
                    border-top:1px solid #e2e8f0;padding-top:18px;">
          <button type="submit" class="btn btn-primary">
            💾 Zapisz praktykę
          </button>
          <a href="{back_url}" class="btn btn-ghost">Anuluj</a>
        </div>
      </form>
    </div>"""


@dziekanat_bp.route('/internship/create', methods=['GET', 'POST'])
@staff_required
def create_internship():
    students = User.query.filter_by(role='student').order_by(User.full_name).all()
    opiekunowie = User.query.filter_by(role='opiekun').order_by(User.full_name).all()
    errors = []

    if request.method == 'POST':
        student_id   = request.form.get('student_id', '').strip()
        mentor_id    = request.form.get('mentor_id', '').strip() or None
        company_name = request.form.get('company_name', '').strip()
        start_date   = request.form.get('start_date', '').strip()
        end_date     = request.form.get('end_date', '').strip()
        total_hours  = request.form.get('total_hours', '480').strip()
        status       = request.form.get('status', 'active')

        if not student_id:
            errors.append("Wybierz studenta.")
        if not company_name:
            errors.append("Podaj nazwę zakładu pracy.")
        if not start_date or not end_date:
            errors.append("Podaj daty praktyki.")
        elif start_date >= end_date:
            errors.append("Data zakończenia musi być późniejsza niż data rozpoczęcia.")

        if not errors:
            from datetime import date
            internship = Internship(
                student_id=int(student_id),
                mentor_id=int(mentor_id) if mentor_id else None,
                company_name=company_name,
                company_address=request.form.get('company_address', '').strip() or None,
                company_phone=request.form.get('company_phone', '').strip() or None,
                company_email=request.form.get('company_email', '').strip() or None,
                start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
                end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
                total_hours=int(total_hours) if total_hours.isdigit() else 480,
                status=status,
                created_by=current_user.id,
            )
            db.session.add(internship)
            db.session.commit()
            flash(f"Praktyka dla {internship.student.full_name} w {company_name} została utworzona.", "success")
            return redirect(url_for('dziekanat.view_internship', internship_id=internship.id))

        saved = dict(request.form)
    else:
        saved = {}

    form_html = _internship_form_html(
        students, opiekunowie, saved=saved, errors=errors,
        title="Utwórz nową praktykę",
        action_url="/dziekanat/internship/create",
        back_url="/dziekanat/internships"
    )

    content = f"""
<div class="page-header">
  <div class="page-header-inner">
    <div>
      <h1>Nowa praktyka zawodowa</h1>
      <div class="breadcrumb">
        <a href="/dziekanat/">Panel</a> ›
        <a href="/dziekanat/internships">Praktyki</a> ›
        <span>Utwórz nową</span>
      </div>
    </div>
  </div>
</div>
<div class="container">
  {_flashes()}
  {form_html}
</div>"""
    return _page("Nowa praktyka", content)


@dziekanat_bp.route('/internship/<int:internship_id>/edit', methods=['GET', 'POST'])
@staff_required
def edit_internship(internship_id):
    internship = Internship.query.get_or_404(internship_id)
    students = User.query.filter_by(role='student').order_by(User.full_name).all()
    opiekunowie = User.query.filter_by(role='opiekun').order_by(User.full_name).all()
    errors = []

    if request.method == 'POST':
        student_id   = request.form.get('student_id', '').strip()
        mentor_id    = request.form.get('mentor_id', '').strip() or None
        company_name = request.form.get('company_name', '').strip()
        start_date   = request.form.get('start_date', '').strip()
        end_date     = request.form.get('end_date', '').strip()
        total_hours  = request.form.get('total_hours', '480').strip()
        status       = request.form.get('status', 'active')

        if not company_name:
            errors.append("Podaj nazwę zakładu pracy.")
        if not start_date or not end_date:
            errors.append("Podaj daty praktyki.")
        elif start_date >= end_date:
            errors.append("Data zakończenia musi być późniejsza niż data rozpoczęcia.")

        if not errors:
            internship.student_id    = int(student_id) if student_id else internship.student_id
            internship.mentor_id     = int(mentor_id) if mentor_id else None
            internship.company_name  = company_name
            internship.company_address = request.form.get('company_address', '').strip() or None
            internship.company_phone   = request.form.get('company_phone', '').strip() or None
            internship.company_email   = request.form.get('company_email', '').strip() or None
            internship.start_date    = datetime.strptime(start_date, '%Y-%m-%d').date()
            internship.end_date      = datetime.strptime(end_date, '%Y-%m-%d').date()
            internship.total_hours   = int(total_hours) if total_hours.isdigit() else 480
            internship.status        = status
            internship.updated_at    = datetime.utcnow()
            db.session.commit()
            flash("Praktyka zaktualizowana.", "success")
            return redirect(url_for('dziekanat.view_internship', internship_id=internship_id))

        saved = dict(request.form)
    else:
        saved = {
            "student_id":      internship.student_id,
            "mentor_id":       internship.mentor_id,
            "company_name":    internship.company_name,
            "company_address": internship.company_address,
            "company_phone":   internship.company_phone,
            "company_email":   internship.company_email,
            "start_date":      internship.start_date.isoformat(),
            "end_date":        internship.end_date.isoformat(),
            "total_hours":     internship.total_hours,
            "status":          internship.status,
        }

    form_html = _internship_form_html(
        students, opiekunowie, saved=saved, errors=errors,
        title=f"Edytuj praktykę – {internship.student.full_name}",
        action_url=f"/dziekanat/internship/{internship_id}/edit",
        back_url=f"/dziekanat/internship/{internship_id}"
    )

    content = f"""
<div class="page-header">
  <div class="page-header-inner">
    <div>
      <h1>Edytuj praktykę</h1>
      <div class="breadcrumb">
        <a href="/dziekanat/">Panel</a> ›
        <a href="/dziekanat/internships">Praktyki</a> ›
        <a href="/dziekanat/internship/{internship_id}">
          {_html.escape(internship.student.full_name)}
        </a> ›
        <span>Edytuj</span>
      </div>
    </div>
  </div>
</div>
<div class="container">
  {_flashes()}
  {form_html}
</div>"""
    return _page("Edytuj praktykę", content)


# ── Podgląd dokumentu studenta ────────────────────────────────────────────────

@dziekanat_bp.route('/document/<int:doc_id>')
@staff_required
def view_document(doc_id):
    """Podgląd treści dokumentu studenta – dziekanat może zobaczyć każdy."""
    doc = DocumentSubmission.query.get_or_404(doc_id)
    internship = doc.internship
    att = doc.attachment
    att_name = att.name if att else f'Dokument #{doc.id}'
    data = doc.data or {}

    _LABELS = {
        'agreement_number': 'Numer porozumienia', 'agreement_date': 'Data porozumienia',
        'company_name': 'Nazwa zakładu pracy', 'company_address': 'Adres',
        'company_phone': 'Telefon', 'company_email': 'E-mail firmy',
        'student_name': 'Student', 'album_number': 'Nr albumu',
        'study_type': 'Forma studiów', 'specialization': 'Specjalność',
        'internship_duration': 'Czas trwania', 'university_supervisor': 'Opiekun uczelniany',
        'date_from': 'Data od', 'date_to': 'Data do', 'internship_year': 'Rok',
        'company_supervisor': 'Opiekun zakładowy', 'supervisor_role': 'Stanowisko opiekuna',
        'bhp_confirmed': 'Szkolenie BHP',
        'place_description': 'I. Charakterystyka miejsca praktyki',
        'work_description': 'II. Opis i analiza wykonywanych prac',
        'skills_acquired': 'III. Wiedza i umiejętności',
        'rok_akademicki': 'Rok akademicki', 'semestr': 'Semestr',
        'forma_studiow': 'Forma studiów', 'godziny_praktyk': 'Liczba godzin',
        'uwagi_dodatkowe': 'Dodatkowe uwagi', 'ocena_ogolna': 'Ocena ogólna',
        'hours_total': 'Liczba godzin', 'student_index': 'Nr albumu', 'uwagi': 'Uwagi',
    }
    _HIDE = {'type', 'submitted_at'}

    rows_html = ''
    for key, val in data.items():
        if key in _HIDE or not val:
            continue
        label = _LABELS.get(key, key.replace('_', ' ').capitalize())
        if key.startswith('outcome_'):
            continue
        if key.startswith('q') and len(key) == 3:
            continue
        val_str = _html.escape(str(val))
        if key == 'bhp_confirmed':
            val_str = 'Tak' if val == '1' else 'Nie'
        rows_html += f"""<tr>
          <td style="width:38%;padding:9px 14px;font-weight:600;color:#374151;
                     border:1px solid #e2e8f0;background:#f7fafc;font-size:13px;">
            {_html.escape(label)}
          </td>
          <td style="padding:9px 14px;border:1px solid #e2e8f0;font-size:13px;
                     color:#111827;white-space:pre-wrap;line-height:1.55;">
            {val_str}
          </td>
        </tr>"""

    # Efekty uczenia się
    outcomes_html = ''
    outcome_items = [(k, v) for k, v in data.items() if k.startswith('outcome_')]
    if outcome_items:
        outcomes_html = '<div style="font-weight:700;font-size:13px;color:#1a2744;margin:16px 0 8px;">Efekty uczenia się</div>'
        outcomes_html += '<table style="width:100%;border-collapse:collapse;">'
        scale_labels = {'uzyskal': 'uzyskał/a', 'nie_uzyskal': 'nie uzyskał/a'}
        for k, v in sorted(outcome_items):
            num = k.replace('outcome_', '')
            color = '#16a34a' if v == 'uzyskal' else '#dc2626'
            label = scale_labels.get(v, v)
            outcomes_html += (f'<tr><td style="padding:6px 12px;border:1px solid #e2e8f0;'
                               f'width:44px;text-align:center;font-weight:700;font-size:12px;">{num}</td>'
                               f'<td style="padding:6px 12px;border:1px solid #e2e8f0;'
                               f'color:{color};font-weight:600;font-size:13px;">{label}</td></tr>')
        outcomes_html += '</table>'

    # Pytania ankiety
    survey_items = [(k, v) for k, v in data.items() if k.startswith('q') and len(k) == 3]
    survey_html = ''
    if survey_items:
        scale_labels_s = {
            'zdecydowanie_tak': 'Zdecydowanie tak', 'raczej_tak': 'Raczej tak',
            'trudno_powiedziec': 'Trudno powiedzieć', 'raczej_nie': 'Raczej nie',
            'zdecydowanie_nie': 'Zdecydowanie nie',
        }
        survey_html = '<div style="font-weight:700;font-size:13px;color:#1a2744;margin:16px 0 8px;">Odpowiedzi ankiety</div>'
        survey_html += '<table style="width:100%;border-collapse:collapse;">'
        for k, v in sorted(survey_items):
            survey_html += (f'<tr><td style="padding:6px 12px;border:1px solid #e2e8f0;'
                            f'width:44px;font-weight:700;text-align:center;font-size:12px;">{k[1:]}</td>'
                            f'<td style="padding:6px 12px;border:1px solid #e2e8f0;font-size:13px;">'
                            f'{scale_labels_s.get(v, v)}</td></tr>')
        survey_html += '</table>'

    status_map = {'draft':'Szkic','submitted':'Wysłany','approved':'Zatwierdzony',
                  'rejected':'Odrzucony','pending_review':'W weryfikacji'}

    # Podpis dziekanatu – zapisany w data JSON pod kluczem _dz_signed
    dz_info = (doc.data or {}).get('_dz_signed', {})

    if dz_info and isinstance(dz_info, dict):
        sign_form_html = f"""
        <div style="border:2px solid #0d9488;border-radius:8px;padding:14px 18px;
                    background:#f0fdfa;margin-bottom:10px;">
          <div style="font-weight:700;font-size:13px;color:#0d9488;margin-bottom:8px;">
            🖊 Podpisano przez dziekanat
          </div>
          <div style="font-size:12.5px;color:#374151;line-height:1.8;">
            <div><span style="color:#6b7280;">Podpisał/a:</span>
              <strong style="margin-left:6px;">{_html.escape(dz_info.get('by_name','–'))}</strong>
            </div>
            <div><span style="color:#6b7280;">E-mail:</span>
              <span style="margin-left:6px;">{_html.escape(dz_info.get('by_email','–'))}</span>
            </div>
            <div><span style="color:#6b7280;">Data podpisu:</span>
              <strong style="margin-left:6px;">{_html.escape(dz_info.get('at','–'))}</strong>
            </div>
            {f'<div style="margin-top:6px;font-style:italic;color:#4a5568;">{_html.escape(dz_info.get("note",""))}</div>' if dz_info.get('note') else ''}
          </div>
        </div>
        <form method="post" action="/dziekanat/document/{doc_id}/sign">
          <input type="hidden" name="action" value="unsign">
          <button type="submit" class="btn btn-ghost" style="font-size:12px;width:100%;"
                  onclick="return confirm('Cofnąć podpis?')">
            Cofnij podpis
          </button>
        </form>"""
    elif doc.status == 'approved':
        sign_form_html = f"""
        <div style="background:#f0fdfa;border:1px solid #99f6e4;border-radius:8px;
                    padding:11px 14px;margin-bottom:12px;font-size:12.5px;color:#0f766e;
                    line-height:1.55;">
          ✅ Dokument został zatwierdzony przez opiekuna.<br>
          Podpisz, aby potwierdzić odbiór i przyjęcie do akt dziekanatu.
        </div>
        <form method="post" action="/dziekanat/document/{doc_id}/sign">
          <input type="hidden" name="action" value="sign">
          <div class="form-group" style="margin-bottom:10px;">
            <label>Uwaga do podpisu (opcjonalnie)</label>
            <textarea name="note" rows="2"
                      placeholder="np. Przyjęto do akt dziekanatu..."></textarea>
          </div>
          <button type="submit" class="btn btn-teal" style="width:100%;justify-content:center;"
                  onclick="return confirm('Podpisać ten dokument?')">
            🖊 Podpisz dokument
          </button>
        </form>"""
    else:
        status_label_map = {
            'draft': 'Szkic – student jeszcze nie wysłał dokumentu.',
            'submitted': 'Dokument wysłany przez studenta – czeka na decyzję opiekuna.',
            'pending_review': 'Dokument w trakcie weryfikacji przez opiekuna.',
            'rejected': 'Dokument odesłany do poprawy – student musi go poprawić.',
        }
        info = status_label_map.get(doc.status, f'Status: {doc.status}')
        sign_form_html = f"""
        <div style="background:#fffbeb;border:1px solid #fde68a;border-left:4px solid #d97706;
                    border-radius:8px;padding:12px 14px;font-size:12.5px;color:#78350f;
                    line-height:1.55;">
          ⚠️ <strong>Podpis niedostępny</strong><br>
          {_html.escape(info)}<br>
          Podpis dziekanatu jest możliwy wyłącznie po zatwierdzeniu dokumentu przez opiekuna.
        </div>"""

    student_name = _html.escape(internship.student.full_name if internship else '–')
    company = _html.escape(internship.company_name if internship else '–')
    created = doc.created_at.strftime('%d.%m.%Y %H:%M') if doc.created_at else '–'
    updated = doc.updated_at.strftime('%d.%m.%Y %H:%M') if doc.updated_at else '–'
    status_label = status_map.get(doc.status, doc.status)

    content = f"""
<div class="page-header">
  <div class="page-header-inner">
    <div>
      <h1>{_html.escape(att_name)}</h1>
      <div class="breadcrumb">
        <a href="/dziekanat/">Panel</a> ›
        <a href="/dziekanat/internship/{internship.id if internship else '#'}">
          {student_name}
        </a> ›
        <span>{_html.escape(att_name)}</span>
      </div>
    </div>
    <div style="display:flex;gap:8px;">
      <a href="/student/document/{doc_id}/pdf" target="_blank" class="btn btn-ghost">
        📄 Otwórz widok PDF
      </a>
      <a href="/dziekanat/internship/{internship.id if internship else '#'}" class="btn btn-ghost">
        ← Powrót
      </a>
    </div>
  </div>
</div>

<div class="container">
  {_flashes()}
  <div style="display:grid;grid-template-columns:1fr 280px;gap:20px;align-items:start;">

    <div class="card">
      <div class="card-header">
        <h2>Treść dokumentu</h2>
        {_status_badge(doc.status)}
      </div>
      <div class="card-body">
        {f'<table style="width:100%;border-collapse:collapse;margin-bottom:16px;">{rows_html}</table>' if rows_html else '<p style="color:#9ca3af;font-style:italic;font-size:13px;">Brak danych formularza.</p>'}
        {outcomes_html}
        {survey_html}
      </div>
    </div>

    <div>
      <div class="card">
        <div class="card-header"><h2>Szczegóły</h2></div>
        <div class="card-body" style="font-size:13px;">
          <div style="margin-bottom:8px;"><span style="color:#6b7280;">Student:</span>
            <strong style="margin-left:6px;">{student_name}</strong></div>
          <div style="margin-bottom:8px;"><span style="color:#6b7280;">Firma:</span>
            <span style="margin-left:6px;">{company}</span></div>
          <div style="margin-bottom:8px;"><span style="color:#6b7280;">Wysłano:</span>
            <span style="margin-left:6px;">{created}</span></div>
          <div style="margin-bottom:8px;"><span style="color:#6b7280;">Zmieniono:</span>
            <span style="margin-left:6px;">{updated}</span></div>
          <div style="margin-bottom:8px;"><span style="color:#6b7280;">Status:</span>
            <span style="margin-left:6px;">{_status_badge(doc.status)}</span></div>
          {f'<div style="margin-top:8px;padding:8px 10px;background:#fff3f3;border-radius:6px;font-size:12.5px;color:#c53030;"><strong>Uwagi:</strong> {_html.escape(doc.comments)}</div>' if doc.comments else ''}
        </div>
      </div>

      <div class="card">
        <div class="card-header"><h2>Podpis dziekanatu</h2></div>
        <div class="card-body">
          {sign_form_html}
        </div>
      </div>
    </div>
  </div>
</div>"""
    return _page(att_name, content)


# ── Podpis dziekanatu (nie zmienia statusu opiekuna) ─────────────────────────

@dziekanat_bp.route('/document/<int:doc_id>/sign', methods=['POST'])
@staff_required
def sign_document(doc_id):
    """Dziekanat podpisuje dokument – rejestruje kto i kiedy, nie zmienia statusu."""
    doc = DocumentSubmission.query.get_or_404(doc_id)
    action = request.form.get('action', 'sign')

    data = dict(doc.data) if doc.data else {}

    if action == 'sign':
        note = request.form.get('note', '').strip()
        data['_dz_signed'] = {
            'by_name':  current_user.full_name or current_user.email,
            'by_email': current_user.email,
            'at':       datetime.now().strftime('%d.%m.%Y %H:%M'),
            'note':     note,
        }
        doc.data = data
        db.session.commit()
        att_name = doc.attachment.name if doc.attachment else f'Dokument #{doc.id}'
        flash(f'Dokument „{att_name}" podpisany przez dziekanat.', 'success')

    elif action == 'unsign':
        data.pop('_dz_signed', None)
        doc.data = data
        db.session.commit()
        flash('Podpis dziekanatu cofnięty.', 'info')

    return redirect(url_for('dziekanat.view_document', doc_id=doc_id))


# ── Zarządzanie studentami ────────────────────────────────────────────────────

@dziekanat_bp.route('/students')
@staff_required
def list_students():
    """Lista wszystkich studentów z statusem praktyki."""
    students = User.query.filter_by(role='student').order_by(User.full_name).all()

    rows = ''
    for s in students:
        internship = Internship.query.filter_by(student_id=s.id).first()
        if not internship:
            status_cell = '<span style="color:#6b7280;font-size:12px;">Brak wniosku</span>'
            action = (f'<a href="/dziekanat/internship/create?student_id={s.id}" '
                      f'class="btn btn-primary" style="font-size:12px;padding:5px 10px;">＋ Przydziel praktykę</a>')
        elif internship.status == 'pending':
            status_cell = '<span style="color:#d97706;font-weight:600;font-size:12px;">⏳ Oczekuje na zatwierdzenie</span>'
            action = (f'<a href="/dziekanat/application/{internship.id}/review" '
                      f'class="btn btn-amber" style="font-size:12px;padding:5px 10px;">Rozpatrz wniosek</a>')
        elif internship.status == 'active':
            status_cell = '<span style="color:#16a34a;font-weight:600;font-size:12px;">✅ Aktywna</span>'
            action = (f'<a href="/dziekanat/internship/{internship.id}" '
                      f'class="btn btn-ghost" style="font-size:12px;padding:5px 10px;">Szczegóły</a>')
        elif internship.status == 'completed':
            status_cell = '<span style="color:#1d4ed8;font-size:12px;">Ukończona</span>'
            action = (f'<a href="/dziekanat/internship/{internship.id}" '
                      f'class="btn btn-ghost" style="font-size:12px;padding:5px 10px;">Szczegóły</a>')
        else:
            status_cell = f'<span style="color:#9ca3af;font-size:12px;">{internship.status}</span>'
            action = ''

        company = _html.escape(internship.company_name) if internship else '–'
        idx = _html.escape(s.student_index or '–') if hasattr(s, 'student_index') else '–'

        rows += f"""<tr>
          <td>
            <div style="font-weight:600;color:#1a2744;">{_html.escape(s.full_name or '?')}</div>
            <div style="font-size:11.5px;color:#9ca3af;">{_html.escape(s.email)}</div>
          </td>
          <td style="font-size:12.5px;">{idx}</td>
          <td style="font-size:12.5px;">{company}</td>
          <td>{status_cell}</td>
          <td>{action}</td>
        </tr>"""

    content = f"""
<div class="page-header">
  <div class="page-header-inner">
    <div>
      <h1>Studenci</h1>
      <div class="breadcrumb">
        <a href="/dziekanat/">Panel</a> › <span>Lista studentów</span>
      </div>
    </div>
    <a href="/dziekanat/student/create" class="btn btn-primary">＋ Dodaj studenta</a>
  </div>
</div>
<div class="container">
  {_flashes()}
  <div class="card">
    <div class="card-header">
      <h2>Studenci ({len(students)})</h2>
    </div>
    <div style="overflow-x:auto;">
      <table>
        <thead><tr>
          <th>Student</th><th>Nr albumu</th><th>Firma / miejsce praktyki</th>
          <th>Status praktyki</th><th>Akcje</th>
        </tr></thead>
        <tbody>{rows if rows else '<tr><td colspan="5" style="text-align:center;color:#9ca3af;padding:24px;">Brak studentów</td></tr>'}</tbody>
      </table>
    </div>
  </div>
</div>"""
    return _page("Lista studentów", content)


@dziekanat_bp.route('/student/create', methods=['GET', 'POST'])
@staff_required
def create_student():
    """Utwórz konto nowego studenta."""
    errors = []
    prefill_student_id = request.args.get('student_id', '')

    if request.method == 'POST':
        full_name     = request.form.get('full_name', '').strip()
        email         = request.form.get('email', '').strip().lower()
        password      = request.form.get('password', '').strip()
        student_index = request.form.get('student_index', '').strip()
        create_now    = request.form.get('create_internship') == '1'

        if not full_name:
            errors.append("Imię i nazwisko jest wymagane.")
        if not email or '@' not in email:
            errors.append("Podaj poprawny adres e-mail.")
        if not password or len(password) < 6:
            errors.append("Hasło musi mieć co najmniej 6 znaków.")
        if User.query.filter_by(email=email).first():
            errors.append(f"Użytkownik z adresem {email} już istnieje.")

        if not errors:
            user = User(
                email=email,
                full_name=full_name,
                role='student',
                is_active=True,
                auth_provider='local',
                student_index=student_index or None,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            if create_now:
                flash(f"Konto studenta {full_name} utworzone. Teraz utwórz praktykę.", "success")
                return redirect(url_for('dziekanat.create_internship') + f'?student_id={user.id}')

            flash(f"Konto studenta {full_name} ({email}) zostało utworzone. Hasło: {password}", "success")
            return redirect(url_for('dziekanat.list_students'))

        saved = dict(request.form)
    else:
        saved = {}

    def v(k, d=''):
        return _html.escape(str(saved.get(k, d) or d))

    errors_html = ''.join(
        f'<div class="alert alert-error" style="margin-bottom:8px;">{_html.escape(e)}</div>'
        for e in errors
    )

    content = f"""
<div class="page-header">
  <div class="page-header-inner">
    <div>
      <h1>Dodaj nowego studenta</h1>
      <div class="breadcrumb">
        <a href="/dziekanat/">Panel</a> ›
        <a href="/dziekanat/students">Studenci</a> ›
        <span>Nowy student</span>
      </div>
    </div>
  </div>
</div>
<div class="container">
  {_flashes()}
  <div style="background:#fff;border:1px solid #dde1ef;border-radius:10px;
              padding:28px 32px;max-width:700px;">
    <h2 style="font-size:16px;font-weight:700;color:#1a2744;margin-bottom:20px;">
      Dane konta studenta
    </h2>
    {errors_html}
    <form method="post">
      <div class="form-grid" style="margin-bottom:14px;">
        <div class="form-group">
          <label>Imię i nazwisko <span style="color:#dc2626;">*</span></label>
          <input type="text" name="full_name" value="{v('full_name')}"
                 required placeholder="Jan Kowalski">
        </div>
        <div class="form-group">
          <label>Nr albumu (indeks)</label>
          <input type="text" name="student_index" value="{v('student_index')}"
                 placeholder="np. 12345">
        </div>
      </div>
      <div class="form-grid" style="margin-bottom:14px;">
        <div class="form-group">
          <label>Adres e-mail <span style="color:#dc2626;">*</span></label>
          <input type="email" name="email" value="{v('email')}"
                 required placeholder="jan.kowalski@student.ans-elblag.pl">
        </div>
        <div class="form-group">
          <label>Hasło tymczasowe <span style="color:#dc2626;">*</span></label>
          <input type="text" name="password" value="{v('password')}"
                 required placeholder="min. 6 znaków" autocomplete="new-password">
          <div style="font-size:11.5px;color:#9ca3af;margin-top:4px;">
            Student powinien zmienić hasło po pierwszym logowaniu.
          </div>
        </div>
      </div>

      <div style="background:#f7fafc;border:1px solid #e2e8f0;border-radius:6px;
                  padding:12px 16px;margin-bottom:20px;">
        <label style="display:flex;align-items:center;gap:10px;cursor:pointer;font-size:13.5px;">
          <input type="checkbox" name="create_internship" value="1"
                 style="width:16px;height:16px;accent-color:#3b5bdb;"
                 {'checked' if prefill_student_id else ''}>
          <span>
            <strong>Po utworzeniu konta od razu przejdź do tworzenia praktyki</strong>
            <span style="display:block;font-size:12px;color:#6b7280;margin-top:1px;">
              Zalecane gdy znasz już miejsce praktyki studenta.
            </span>
          </span>
        </label>
      </div>

      <div style="display:flex;gap:12px;border-top:1px solid #e2e8f0;padding-top:18px;">
        <button type="submit" class="btn btn-primary">💾 Utwórz konto studenta</button>
        <a href="/dziekanat/students" class="btn btn-ghost">Anuluj</a>
      </div>
    </form>
  </div>
</div>"""
    return _page("Dodaj studenta", content)


@dziekanat_bp.route('/application/<int:internship_id>/review', methods=['GET', 'POST'])
@staff_required
def review_application(internship_id):
    """Dziekanat rozpatruje wniosek studenta o praktykę."""
    internship = Internship.query.get_or_404(internship_id)
    if internship.status != 'pending':
        flash("Ten wniosek nie oczekuje na rozpatrzenie.", "info")
        return redirect(url_for('dziekanat.list_students'))

    req_doc = DocumentSubmission.query.filter_by(
        internship_id=internship_id,
        attachment_id=None
    ).first()
    req_data = req_doc.data or {} if req_doc else {}

    opiekunowie = User.query.filter_by(role='opiekun').order_by(User.full_name).all()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'approve':
            mentor_id   = request.form.get('mentor_id', '').strip() or None
            total_hours = request.form.get('total_hours', '960').strip()
            new_start   = request.form.get('start_date', '').strip()
            new_end     = request.form.get('end_date', '').strip()

            internship.mentor_id   = int(mentor_id) if mentor_id else None
            internship.total_hours = int(total_hours) if total_hours.isdigit() else 960
            internship.status      = 'active'
            if new_start:
                internship.start_date = datetime.strptime(new_start, '%Y-%m-%d').date()
            if new_end:
                internship.end_date = datetime.strptime(new_end, '%Y-%m-%d').date()
            internship.updated_at = datetime.utcnow()

            if req_doc:
                req_doc.status = 'approved'
                req_doc.reviewer_id = current_user.id

            db.session.commit()
            flash(f"Wniosek studenta {internship.student.full_name} zatwierdzony. Praktyka aktywna.", "success")
            return redirect(url_for('dziekanat.list_students'))

        elif action == 'reject':
            reason = request.form.get('rejection_reason', '').strip()
            internship.status = 'cancelled'
            if hasattr(internship, 'rejection_reason'):
                internship.rejection_reason = reason
            if req_doc:
                req_doc.status = 'rejected'
                req_doc.comments = reason
                req_doc.reviewer_id = current_user.id
            db.session.commit()
            flash(f"Wniosek odrzucony. Student {internship.student.full_name} zostanie powiadomiony.", "warning")
            return redirect(url_for('dziekanat.list_students'))

    student = internship.student
    supervisor_opts = '<option value="">– brak –</option>' + ''.join(
        f'<option value="{o.id}">{_html.escape(o.full_name)} ({_html.escape(o.email)})</option>'
        for o in opiekunowie
    )

    def dv(k):
        return _html.escape(str(req_data.get(k, '') or ''))

    content = f"""
<div class="page-header">
  <div class="page-header-inner">
    <div>
      <h1>Rozpatrz wniosek o praktykę</h1>
      <div class="breadcrumb">
        <a href="/dziekanat/">Panel</a> ›
        <a href="/dziekanat/students">Studenci</a> ›
        <span>Wniosek – {_html.escape(student.full_name)}</span>
      </div>
    </div>
    <span style="padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;
                 background:#fffbeb;color:#d97706;">⏳ Oczekuje</span>
  </div>
</div>
<div class="container">
  {_flashes()}
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;">
    <div class="card">
      <div class="card-header"><h2>👤 Dane studenta</h2></div>
      <div class="card-body" style="font-size:13.5px;">
        <div style="margin-bottom:8px;"><strong>{_html.escape(student.full_name)}</strong></div>
        <div style="color:#6b7280;">{_html.escape(student.email)}</div>
        {f'<div style="margin-top:6px;color:#374151;">Nr albumu: <strong>{_html.escape(req_data.get("student_index","") or student.student_index or "–")}</strong></div>' if True else ''}
        {f'<div style="color:#374151;">Forma studiów: {dv("study_type")}</div>' if req_data.get("study_type") else ''}
      </div>
    </div>
    <div class="card">
      <div class="card-header"><h2>🏢 Proponowane miejsce praktyki</h2></div>
      <div class="card-body" style="font-size:13.5px;">
        <div style="font-weight:600;margin-bottom:6px;">{_html.escape(internship.company_name)}</div>
        {f'<div style="color:#6b7280;">{_html.escape(internship.company_address)}</div>' if internship.company_address else ''}
        {f'<div style="color:#6b7280;">{_html.escape(internship.company_phone)}</div>' if internship.company_phone else ''}
        {f'<div style="color:#6b7280;">{_html.escape(internship.company_email)}</div>' if internship.company_email else ''}
        {f'<div style="margin-top:6px;">Opiekun zakładowy: <strong>{dv("company_supervisor")}</strong></div>' if req_data.get("company_supervisor") else ''}
        <div style="margin-top:8px;">
          <strong>{internship.start_date.strftime('%d.%m.%Y')}</strong> –
          <strong>{internship.end_date.strftime('%d.%m.%Y')}</strong>
        </div>
        {f'<div style="margin-top:8px;color:#4a5568;font-style:italic;">{dv("notes")}</div>' if req_data.get("notes") else ''}
      </div>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
    <div class="card">
      <div class="card-header"><h2 style="color:#16a34a;">✅ Zatwierdź wniosek</h2></div>
      <div class="card-body">
        <form method="post">
          <input type="hidden" name="action" value="approve">
          <div class="form-group" style="margin-bottom:14px;">
            <label>Przydziel opiekuna uczelnianego</label>
            <select name="mentor_id">{supervisor_opts}</select>
          </div>
          <div class="form-grid" style="margin-bottom:14px;">
            <div class="form-group">
              <label>Data od (potwierdź)</label>
              <input type="date" name="start_date"
                     value="{internship.start_date.isoformat()}">
            </div>
            <div class="form-group">
              <label>Data do (potwierdź)</label>
              <input type="date" name="end_date"
                     value="{internship.end_date.isoformat()}">
            </div>
          </div>
          <div class="form-group" style="margin-bottom:18px;">
            <label>Wymagana liczba godzin</label>
            <input type="number" name="total_hours" value="960" min="1"
                   style="max-width:140px;">
          </div>
          <button type="submit" class="btn btn-teal"
                  onclick="return confirm('Zatwierdzić wniosek? Student uzyska dostęp do formularzy.')">
            ✅ Zatwierdź – aktywuj praktykę
          </button>
        </form>
      </div>
    </div>

    <div class="card">
      <div class="card-header"><h2 style="color:#dc2626;">❌ Odrzuć wniosek</h2></div>
      <div class="card-body">
        <form method="post">
          <input type="hidden" name="action" value="reject">
          <div class="form-group" style="margin-bottom:18px;">
            <label>Powód odrzucenia <span style="color:#dc2626;">*</span></label>
            <textarea name="rejection_reason" rows="4" required
                      placeholder="Np. Wybrana firma nie spełnia wymagań programu praktyk..."></textarea>
          </div>
          <button type="submit" class="btn btn-ghost"
                  style="border-color:#dc2626;color:#dc2626;"
                  onclick="return confirm('Odrzucić wniosek? Student zostanie powiadomiony.')">
            ❌ Odrzuć wniosek
          </button>
        </form>
      </div>
    </div>
  </div>
</div>"""
    return _page("Rozpatrz wniosek", content)
