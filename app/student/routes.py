"""
Trasy (routes) dla widokow studenta.
"""

from flask import (
    render_template, render_template_string, redirect, url_for,
    request, jsonify, flash, current_app, get_flashed_messages,
    send_file, abort
)
from flask_login import current_user, login_required
from app import db
from app.models.user import User
from app.models.internship import Internship, LearningOutcome, DiaryEntry
from app.models import DocumentSubmission, Attachment, validate_one_sentence
from app.auth.decorators import role_required
from app.auth.permissions import student_required, check_resource_access
from app.forms import Attachment1Form, DiaryEntryForm, ReportForm, LearningOutcomeForm
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import os, uuid, io

from app.student import student_bp, STUDENT_PAGE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STUDENT_ATTACHMENT_IDS = [2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 14]

ATTACHMENT_META = {
    2:  {"title": "Porozumienie (Zał. 1)",            "desc": "Porozumienie o organizację praktyki zawodowej.", "icon": "🤝"},
    3:  {"title": "Program praktyki (Zał. 2)",         "desc": "Szczegółowy program i cele praktyki zawodowej.", "icon": "📅"},
    4:  {"title": "Program i harmonogram (Zał. 2a)",   "desc": "Tygodniowy harmonogram zadań praktyki.", "icon": "🗓️"},
    5:  {"title": "Karta praktyki (Zał. 3)",           "desc": "Skierowanie na praktykę – dane studenta, czas trwania, opiekun.", "icon": "📋"},
    6:  {"title": "Potwierdzenie efektów (Zał. 4)",    "desc": "Ocena uzyskania 13 efektów uczenia się.", "icon": "✅"},
    8:  {"title": "Wniosek o zaliczenie (Zał. 4b)",    "desc": "Wniosek o zaliczenie pracy zawodowej/stażu jako praktyki.", "icon": "📝"},
    9:  {"title": "Kwestionariusz ankiety (Zał. 5)",   "desc": "Anonimowa ankieta oceny przebiegu praktyki.", "icon": "📊"},
    10: {"title": "Dziennik praktyki (Zał. 6)",        "desc": "Codzienne wpisy z przebiegu praktyki zawodowej.", "icon": "📖"},
    11: {"title": "Sprawozdanie (Zał. 7)",             "desc": "Sprawozdanie studenta z praktyki (max 3 zdania na sekcję).", "icon": "🎓"},
    12: {"title": "Sprawozdanie niestacj. (Zał. 7a)", "desc": "Sprawozdanie dla studentów niestacjonarnych/pracujących.", "icon": "🎓"},
    14: {"title": "Oświadczenie instytucji (Zał. 9)", "desc": "Oświadczenie firmy o przyjęciu studenta na praktykę (skan).", "icon": "🏢"},
}

STATUS_LABELS = {
    "draft":          ("Szkic",           "badge-draft"),
    "submitted":      ("Wysłany",         "badge-submitted"),
    "pending_review": ("W weryfikacji",   "badge-pending"),
    "approved":       ("Zatwierdzony",    "badge-approved"),
    "rejected":       ("Odrzucony",       "badge-rejected"),
}


def _render(content: str) -> str:
    return render_template_string(STUDENT_PAGE, content=content)


def _timeline_html(internship, sub_by_att: dict, protocol_doc, diary_count: int = 0) -> str:
    """Poziomy stepper postępu studenta przez dokumenty praktyki."""

    STEPS = [
        {
            'key':   'internship',
            'icon':  '🏢',
            'label': 'Praktyka\naktywna',
            'short': 'Praktyka',
        },
        {
            'key':   5,   # Karta praktyki
            'icon':  '📋',
            'label': 'Karta\npraktyki',
            'short': 'Zał. 3',
        },
        {
            'key':   10,  # Dziennik
            'icon':  '📖',
            'label': f'Dziennik\n({diary_count} wpisów)',
            'short': 'Zał. 6',
        },
        {
            'key':   6,   # Efekty uczenia się
            'icon':  '✅',
            'label': 'Efekty\nuczenia się',
            'short': 'Zał. 4',
        },
        {
            'key':   11,  # Sprawozdanie
            'icon':  '📝',
            'label': 'Sprawozdanie',
            'short': 'Zał. 7',
        },
        {
            'key':   9,   # Ankieta
            'icon':  '📊',
            'label': 'Ankieta',
            'short': 'Zał. 5',
        },
        {
            'key':   'protocol',
            'icon':  '🎓',
            'label': 'Protokół\negzaminu',
            'short': 'Zał. 8',
        },
    ]

    def _step_state(step_key):
        if step_key == 'internship':
            if not internship:
                return 'pending', 'Brak praktyki'
            if internship.status == 'active':
                return 'active', 'Aktywna'
            if internship.status == 'completed':
                return 'done', 'Ukończona'
            if internship.status == 'pending':
                return 'waiting', 'Oczekuje'
            return 'pending', internship.status
        if step_key == 'protocol':
            if protocol_doc:
                return 'done', 'Zatwierdzony'
            return 'pending', 'Brak'
        sub = sub_by_att.get(step_key)
        if not sub:
            return 'pending', 'Nie wypełniony'
        status_labels = {
            'draft':          ('draft',    'Szkic'),
            'submitted':      ('submitted', 'Wysłany'),
            'pending_review': ('submitted', 'W weryfikacji'),
            'approved':       ('done',      'Zatwierdzony'),
            'rejected':       ('rejected',  'Odrzucony'),
        }
        return status_labels.get(sub.status, ('draft', sub.status))

    COLORS = {
        'pending':   ('--c-gray',   '#9ca3af', '#f3f4f6', ''),
        'waiting':   ('--c-amber',  '#d97706', '#fffbeb', ''),
        'draft':     ('--c-amber',  '#d97706', '#fffbeb', ''),
        'submitted': ('--c-blue',   '#3b5bdb', '#eff3ff', ''),
        'active':    ('--c-green',  '#16a34a', '#f0fdf4', ''),
        'done':      ('--c-green',  '#16a34a', '#f0fdf4', '✓'),
        'rejected':  ('--c-red',    '#dc2626', '#fef2f2', '✗'),
    }

    steps_html = ''
    done_count = 0
    total_steps = len(STEPS)

    for i, step in enumerate(STEPS):
        state, state_label = _step_state(step['key'])
        _, color, bg, check = COLORS[state]
        if state == 'done':
            done_count += 1

        label_lines = step['label'].split('\n')
        label_html = '<br>'.join(label_lines)

        # Connector line between steps
        connector = ''
        if i < total_steps - 1:
            line_color = '#16a34a' if state == 'done' else '#e2e8f0'
            connector = (f'<div style="flex:1;height:2px;background:{line_color};'
                         f'margin:0 4px;margin-top:-20px;"></div>')

        # Icon in circle
        circle_border = f'2px solid {color}'
        circle_bg = bg
        if state in ('pending',):
            circle_border = '2px dashed #d1d5db'
            circle_bg = '#fff'
            color = '#9ca3af'

        icon_inner = (f'<span style="font-size:13px;">{check}</span>'
                      if check else f'<span style="font-size:16px;">{step["icon"]}</span>')

        steps_html += f"""
        <div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;min-width:60px;">
          <div style="width:40px;height:40px;border-radius:50%;border:{circle_border};
                      background:{circle_bg};display:flex;align-items:center;justify-content:center;
                      box-shadow:{'0 0 0 3px ' + bg if state == 'active' else 'none'};
                      transition:all .2s;">
            {icon_inner}
          </div>
          <div style="margin-top:6px;text-align:center;font-size:11px;font-weight:600;
                      color:{color};line-height:1.3;">{label_html}</div>
          <div style="font-size:10px;color:#9ca3af;margin-top:1px;">{state_label}</div>
        </div>
        {connector}"""

    progress_pct = int((done_count / total_steps) * 100)
    progress_color = '#16a34a' if progress_pct == 100 else ('#3b5bdb' if progress_pct > 50 else '#d97706')

    return f"""
    <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;
                padding:20px 24px;margin-top:24px;margin-bottom:4px;">
      <div style="display:flex;align-items:center;justify-content:space-between;
                  margin-bottom:14px;">
        <div style="font-size:13px;font-weight:700;color:#1a2744;letter-spacing:-.2px;">
          Postęp realizacji praktyki
        </div>
        <div style="font-size:12px;font-weight:700;color:{progress_color};">
          {done_count}/{total_steps} ukończonych &nbsp;
          <span style="background:{progress_color}22;padding:2px 8px;border-radius:20px;">
            {progress_pct}%
          </span>
        </div>
      </div>
      <div style="display:flex;align-items:flex-start;overflow-x:auto;padding-bottom:4px;gap:0;">
        {steps_html}
      </div>
    </div>"""


def _pdf_dz_stamp(data: dict) -> str:
    """Pieczęć dziekanatu w widoku PDF – pokazuje kto i kiedy podpisał."""
    dz = data.get('_dz_signed', {}) if data else {}
    if not dz or not isinstance(dz, dict):
        return ''
    import html as _h
    note = _h.escape(dz.get('note', ''))
    return f"""
  <div style="margin-top:24px;border:2px solid #0d9488;border-radius:8px;
              padding:14px 18px;background:#f0fdfa;">
    <div style="font-weight:700;font-size:12px;text-transform:uppercase;
                letter-spacing:.5px;color:#0d9488;margin-bottom:6px;">
      🖊 Pieczęć Dziekanatu – ANS Elbląg
    </div>
    <div style="font-size:12.5px;color:#374151;line-height:1.7;">
      <div><strong>Podpisał/a:</strong> {_h.escape(dz.get('by_name','–'))}</div>
      <div><strong>Data:</strong> {_h.escape(dz.get('at','–'))}</div>
      {f'<div style="font-style:italic;margin-top:4px;">{note}</div>' if note else ''}
    </div>
  </div>"""


def _protocol_card_html(protocol_doc) -> str:
    """Karta protokołu egzaminu – widoczna gdy dziekanat zatwierdził."""
    if not protocol_doc:
        return ""
    d = protocol_doc.data or {}
    import html as _h
    ocena = _h.escape(str(d.get('ocena_koncowa', '–') or '–'))
    zaliczone = d.get('zaliczone', 'tak')
    badge_color = '#16a34a' if zaliczone == 'tak' else '#dc2626'
    badge_bg = '#f0fdf4' if zaliczone == 'tak' else '#fef2f2'
    badge_text = '✅ Zaliczona' if zaliczone == 'tak' else '❌ Niezaliczona'
    view_url = url_for('dziekanat.view_protocol', doc_id=protocol_doc.id)
    return f"""
      <div style="padding-top:28px;">
        <div style="font-size:13px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.6px;color:var(--text-muted);margin-bottom:14px;">
          Wyniki egzaminu
        </div>
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;
                    padding:20px 24px;display:flex;align-items:center;
                    justify-content:space-between;gap:16px;flex-wrap:wrap;">
          <div style="display:flex;align-items:center;gap:14px;">
            <div style="width:48px;height:48px;background:#f5f3ff;border-radius:10px;
                        display:flex;align-items:center;justify-content:center;
                        font-size:22px;">📋</div>
            <div>
              <div style="font-weight:700;font-size:14px;color:#1a2744;">
                Protokół egzaminu praktyki zawodowej
              </div>
              <div style="font-size:12.5px;color:#6b7280;margin-top:2px;">
                Załącznik nr 8 &nbsp;·&nbsp; Ocena końcowa: <strong>{ocena}</strong>
              </div>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:12px;">
            <span style="padding:4px 12px;border-radius:20px;font-size:12px;
                         font-weight:600;color:{badge_color};background:{badge_bg};">
              {badge_text}
            </span>
            <a href="{view_url}" class="btn btn-primary btn-sm">
              Pokaż protokół →
            </a>
          </div>
        </div>
      </div>"""


def _flash_html() -> str:
    msgs = get_flashed_messages(with_categories=True)
    if not msgs:
        return ""
    html = ""
    cat_map = {"success": "alert-success", "error": "alert-error",
               "warning": "alert-warning", "info": "alert-info", "message": "alert-info"}
    for cat, msg in msgs:
        cls = cat_map.get(cat, "alert-info")
        html += f'<div class="alert {cls}">{msg}</div>'
    return html


# ---------------------------------------------------------------------------
# Widoki stanu praktyki (brak / oczekuje / anulowana)
# ---------------------------------------------------------------------------

def _render_no_internship():
    import html as _h
    full_name = _h.escape(current_user.full_name or current_user.email)
    idx = _h.escape(getattr(current_user, 'student_index', '') or '')
    content = f"""
    <div class="page-header">
      <div class="page-header-inner">
        <div class="page-title-group">
          <h1>Zgłoszenie miejsca praktyki</h1>
          <div class="breadcrumb">
            <a href="{url_for('auth.dashboard')}">Dashboard</a> › <span>Wniosek o praktykę</span>
          </div>
        </div>
      </div>
    </div>
    <div class="student-container">
      {_flash_html()}

      <div style="background:#eff3ff;border:1px solid #c7d2fe;border-radius:10px;
                  padding:20px 24px;margin-bottom:24px;display:flex;gap:14px;align-items:flex-start;">
        <div style="font-size:28px;flex-shrink:0;">📋</div>
        <div>
          <div style="font-weight:700;font-size:14px;color:#1a2744;margin-bottom:4px;">
            Nie masz jeszcze przydzielonej praktyki
          </div>
          <div style="font-size:13px;color:#374151;line-height:1.6;">
            Wypełnij poniższy formularz podając miejsce, gdzie chcesz odbyć praktykę zawodową.
            Wniosek trafi do dziekanatu. Po zatwierdzeniu otrzymasz dostęp do wszystkich
            wymaganych dokumentów i formularzy.
          </div>
        </div>
      </div>

      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:28px 32px;">
        <div style="font-weight:700;font-size:15px;color:#1a2744;margin-bottom:20px;
                    padding-bottom:10px;border-bottom:1px solid #e2e8f0;">
          📝 Wniosek o praktykę zawodową
        </div>
        <form method="post" action="{url_for('student.submit_application')}">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px;">
            <div class="form-group">
              <label>Twoje imię i nazwisko <span class="required">*</span></label>
              <input type="text" name="student_name" value="{full_name}" required>
            </div>
            <div class="form-group">
              <label>Numer albumu <span class="required">*</span></label>
              <input type="text" name="student_index" value="{idx}"
                     required placeholder="np. 12345">
            </div>
          </div>

          <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;
                      color:#6b7280;margin:20px 0 12px;padding-top:8px;border-top:1px solid #f0f0f5;">
            Zakład pracy / firma
          </div>
          <div class="form-group" style="margin-bottom:14px;">
            <label>Pełna nazwa zakładu pracy <span class="required">*</span></label>
            <input type="text" name="company_name" required
                   placeholder="np. ABC Sp. z o.o.">
          </div>
          <div style="display:grid;grid-template-columns:2fr 1fr;gap:14px;margin-bottom:14px;">
            <div class="form-group">
              <label>Adres firmy</label>
              <input type="text" name="company_address" placeholder="ul. Przykładowa 1, Elbląg">
            </div>
            <div class="form-group">
              <label>Telefon kontaktowy</label>
              <input type="text" name="company_phone" placeholder="55 123 45 67">
            </div>
          </div>
          <div class="form-group" style="margin-bottom:14px;">
            <label>E-mail firmy</label>
            <input type="email" name="company_email" placeholder="kontakt@firma.pl">
          </div>
          <div class="form-group" style="margin-bottom:20px;">
            <label>Imię i nazwisko opiekuna zakładowego</label>
            <input type="text" name="company_supervisor"
                   placeholder="Osoba odpowiedzialna za Twoją praktykę w firmie">
          </div>

          <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;
                      color:#6b7280;margin:20px 0 12px;padding-top:8px;border-top:1px solid #f0f0f5;">
            Planowany termin praktyki
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:20px;">
            <div class="form-group">
              <label>Data rozpoczęcia <span class="required">*</span></label>
              <input type="date" name="start_date" required>
            </div>
            <div class="form-group">
              <label>Data zakończenia <span class="required">*</span></label>
              <input type="date" name="end_date" required>
            </div>
            <div class="form-group">
              <label>Forma studiów</label>
              <select name="study_type">
                <option value="stacjonarne">Stacjonarne</option>
                <option value="niestacjonarne">Niestacjonarne</option>
              </select>
            </div>
          </div>

          <div class="form-group" style="margin-bottom:24px;">
            <label>Dodatkowe informacje / uwagi</label>
            <textarea name="notes" rows="3"
                      placeholder="Opcjonalnie: opis planowanych zadań, specjalność itp."></textarea>
          </div>

          <div style="display:flex;gap:12px;align-items:center;
                      border-top:1px solid #e2e8f0;padding-top:18px;">
            <button type="submit" class="btn btn-primary">
              📤 Złóż wniosek do dziekanatu
            </button>
            <span style="font-size:12px;color:#9ca3af;">
              Po zatwierdzeniu wniosku dziekanat przydzieli Ci praktykę i opiekuna.
            </span>
          </div>
        </form>
      </div>
    </div>"""
    return _render(content)


def _render_pending_internship(internship):
    import html as _h
    content = f"""
    <div class="page-header">
      <div class="page-header-inner">
        <div class="page-title-group">
          <h1>Wniosek o praktykę – oczekuje</h1>
          <div class="breadcrumb">
            <a href="{url_for('auth.dashboard')}">Dashboard</a> › <span>Wniosek złożony</span>
          </div>
        </div>
        <span class="adm-badge badge-pending">
          <span class="adm-badge-dot"></span>Oczekuje na zatwierdzenie
        </span>
      </div>
    </div>
    <div class="student-container">
      {_flash_html()}

      <div style="background:#fffbeb;border:1px solid #fde68a;border-left:4px solid #d97706;
                  border-radius:8px;padding:18px 22px;margin-bottom:24px;">
        <div style="font-weight:700;font-size:14px;color:#92400e;margin-bottom:6px;">
          ⏳ Wniosek złożony – czeka na zatwierdzenie przez dziekanat
        </div>
        <div style="font-size:13px;color:#78350f;line-height:1.6;">
          Twój wniosek o praktykę w firmie <strong>{_h.escape(internship.company_name)}</strong>
          został przesłany do dziekanatu. Po zatwierdzeniu otrzymasz dostęp do wszystkich
          wymaganych formularzy i dokumentów. Zazwyczaj trwa to 1–3 dni robocze.
        </div>
      </div>

      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:24px 28px;">
        <div style="font-weight:700;font-size:14px;color:#1a2744;margin-bottom:16px;">
          Dane złożonego wniosku
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:13px;">
          <div><span style="color:#6b7280;">Firma:</span>
            <strong style="margin-left:6px;">{_h.escape(internship.company_name)}</strong></div>
          <div><span style="color:#6b7280;">Adres:</span>
            <span style="margin-left:6px;">{_h.escape(internship.company_address or '–')}</span></div>
          <div><span style="color:#6b7280;">Data od:</span>
            <span style="margin-left:6px;">{internship.start_date.strftime('%d.%m.%Y')}</span></div>
          <div><span style="color:#6b7280;">Data do:</span>
            <span style="margin-left:6px;">{internship.end_date.strftime('%d.%m.%Y')}</span></div>
        </div>
        <div style="margin-top:18px;padding-top:14px;border-top:1px solid #f0f0f5;">
          <a href="{url_for('auth.regulamin')}"
             style="font-size:13px;color:#3b5bdb;">
            📜 Przeczytaj Regulamin Praktyki Zawodowej →
          </a>
        </div>
      </div>
    </div>"""
    return _render(content)


def _render_cancelled_internship(internship):
    import html as _h
    reason = _h.escape(getattr(internship, 'rejection_reason', '') or '')
    content = f"""
    <div class="page-header">
      <div class="page-header-inner">
        <div class="page-title-group">
          <h1>Wniosek o praktykę – odrzucony</h1>
          <div class="breadcrumb">
            <a href="{url_for('auth.dashboard')}">Dashboard</a> › <span>Wniosek odrzucony</span>
          </div>
        </div>
      </div>
    </div>
    <div class="student-container">
      {_flash_html()}
      <div style="background:#fff3f3;border:1px solid #fed7d7;border-left:4px solid #e53e3e;
                  border-radius:8px;padding:18px 22px;margin-bottom:24px;">
        <div style="font-weight:700;font-size:14px;color:#c53030;margin-bottom:6px;">
          ❌ Wniosek odrzucony przez dziekanat
        </div>
        {f'<div style="font-size:13px;color:#742a2a;margin-top:4px;"><strong>Powód:</strong> {reason}</div>' if reason else ''}
        <div style="font-size:13px;color:#742a2a;margin-top:8px;">
          Złóż nowy wniosek z poprawionym miejscem praktyki lub skontaktuj się z dziekanatem.
        </div>
      </div>
      <div style="text-align:center;padding:20px;">
        <a href="{url_for('student.reapply')}" class="btn btn-primary">
          📝 Złóż nowy wniosek
        </a>
      </div>
    </div>"""
    return _render(content)


# ---------------------------------------------------------------------------
# Panel główny studenta – lista załączników
# ---------------------------------------------------------------------------

@student_bp.route("/")
@login_required
@role_required("student")
def index():
    # Sprawdź stan praktyki studenta
    internship = Internship.query.filter_by(student_id=current_user.id).first()

    # Brak praktyki → pokaż formularz wniosku
    if not internship:
        return _render_no_internship()

    # Oczekuje na zatwierdzenie przez dziekanat
    if internship.status == 'pending':
        return _render_pending_internship(internship)

    # Praktyka anulowana
    if internship.status == 'cancelled':
        return _render_cancelled_internship(internship)

    # Praktyka aktywna / ukończona → normalny panel
    attachments = (Attachment.query
                   .filter(Attachment.id.in_(STUDENT_ATTACHMENT_IDS))
                   .order_by(Attachment.id)
                   .all())

    submissions = DocumentSubmission.query.filter_by(user_id=current_user.id).all()
    sub_by_att = {}
    for s in submissions:
        sub_by_att[s.attachment_id] = s

    protocol_doc = DocumentSubmission.query.filter_by(
        internship_id=internship.id,
        attachment_id=13,
        status='approved'
    ).first()

    # Liczba wpisów w dzienniku (dla timeline)
    from app.models.internship import DiaryEntry
    diary_count = DiaryEntry.query.filter_by(internship_id=internship.id).count()

    cards_html = ""
    for a in attachments:
        meta = ATTACHMENT_META.get(a.id, {"title": a.name, "desc": a.description or "", "icon": "📄"})
        sub = sub_by_att.get(a.id)
        status_label, status_cls = STATUS_LABELS.get(
            sub.status if sub else "draft", ("Brak", "badge-draft")
        )
        badge = f'<span class="adm-badge {status_cls}"><span class="adm-badge-dot"></span>{status_label}</span>'
        feedback_html = ""
        if sub and sub.status == 'rejected' and sub.comments:
            import html as _html
            escaped_comment = _html.escape(sub.comments).replace('\n', '<br>')
            feedback_html = f"""
          <div style="margin:10px 0 0;padding:10px 14px;background:#fff3f3;border-left:3px solid #e53e3e;
                      border-radius:4px;font-size:12.5px;color:#c53030;">
            <strong style="display:block;margin-bottom:4px;">📝 Uwagi opiekuna:</strong>
            <span style="color:#742a2a;">{escaped_comment}</span>
          </div>"""
        cards_html += f"""
        <div class="attachment-card">
          <div style="display:flex;align-items:center;gap:10px;">
            <div class="attachment-num">{a.id}</div>
            <div>
              <div class="attachment-title">{meta['title']}</div>
            </div>
          </div>
          <div class="attachment-desc">{meta['desc']}</div>
          {feedback_html}
          <div class="attachment-footer">
            {badge}
            <a href="{url_for('student.attachment_form', attachment_id=a.id)}"
               class="btn btn-primary btn-sm">{'Popraw' if (sub and sub.status == 'rejected') else 'Wypełnij'}</a>
            {f'<a href="{url_for("student.document_pdf_view", doc_id=sub.id)}" class="btn btn-ghost btn-sm" target="_blank" title="Podgląd PDF">📄 PDF</a>' if (sub and sub.status not in ('draft',) and sub.data) else ''}
          </div>
        </div>
        """

    name = getattr(current_user, 'first_name', '') or current_user.email.split('@')[0]

    content = f"""
    <div class="page-header">
      <div class="page-header-inner">
        <div class="page-title-group">
          <h1>Panel studenta</h1>
          <div class="breadcrumb">
            <a href="{url_for('auth.dashboard')}">Dashboard</a>
            <span>›</span>
            <span>Panel studenta</span>
          </div>
        </div>
      </div>
    </div>

    <div class="student-container">
      {_flash_html()}

      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-icon blue">📋</div>
          <div>
            <div class="stat-val">{len(attachments)}</div>
            <div class="stat-label">Przypisane załączniki</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon green">✅</div>
          <div>
            <div class="stat-val">{sum(1 for s in sub_by_att.values() if s.status == 'approved')}</div>
            <div class="stat-label">Zatwierdzone</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon amber">⏳</div>
          <div>
            <div class="stat-val">{sum(1 for s in sub_by_att.values() if s.status in ('submitted','pending_review'))}</div>
            <div class="stat-label">Oczekujące</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon teal">📝</div>
          <div>
            <div class="stat-val">{sum(1 for s in sub_by_att.values() if s.status == 'draft')}</div>
            <div class="stat-label">Szkice</div>
          </div>
        </div>
      </div>

      <div style="padding-top:28px;">
        <div style="font-size:13px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.6px;color:var(--text-muted);margin-bottom:14px;">
          Twoje dokumenty
        </div>
        <div class="attachments-grid">
          {cards_html}
        </div>
      </div>

      {_timeline_html(internship, sub_by_att, protocol_doc, diary_count)}
      {_protocol_card_html(protocol_doc)}
    </div>
    """
    return _render(content)


# ---------------------------------------------------------------------------
# Formularz załącznika
# ---------------------------------------------------------------------------

@student_bp.route('/application', methods=['POST'])
@login_required
@role_required('student')
def submit_application():
    """Student składa wniosek o praktykę – tworzy Internship(status='pending')."""
    existing = Internship.query.filter_by(student_id=current_user.id).first()
    if existing and existing.status != 'cancelled':
        flash("Masz już złożony wniosek lub aktywną praktykę.", "error")
        return redirect(url_for('student.index'))

    company_name   = request.form.get('company_name', '').strip()
    start_date_str = request.form.get('start_date', '').strip()
    end_date_str   = request.form.get('end_date', '').strip()

    if not company_name or not start_date_str or not end_date_str:
        flash("Wypełnij wymagane pola: nazwa firmy i daty praktyki.", "error")
        return redirect(url_for('student.index'))

    from datetime import date as _date
    try:
        start_date = _date.fromisoformat(start_date_str)
        end_date   = _date.fromisoformat(end_date_str)
    except ValueError:
        flash("Nieprawidłowy format daty.", "error")
        return redirect(url_for('student.index'))

    if start_date >= end_date:
        flash("Data zakończenia musi być późniejsza niż data rozpoczęcia.", "error")
        return redirect(url_for('student.index'))

    student_idx = request.form.get('student_index', '').strip()
    if student_idx and not current_user.student_index:
        current_user.student_index = student_idx

    if existing and existing.status == 'cancelled':
        db.session.delete(existing)
        db.session.flush()

    internship = Internship(
        student_id      = current_user.id,
        mentor_id       = None,
        company_name    = company_name,
        company_address = request.form.get('company_address', '').strip() or None,
        company_phone   = request.form.get('company_phone', '').strip() or None,
        company_email   = request.form.get('company_email', '').strip() or None,
        start_date      = start_date,
        end_date        = end_date,
        status          = 'pending',
        total_hours     = 960,
    )
    db.session.add(internship)
    db.session.flush()

    req_doc = DocumentSubmission(
        user_id       = current_user.id,
        internship_id = internship.id,
        attachment_id = None,
        status        = 'submitted',
        data          = {
            'student_name':       request.form.get('student_name', ''),
            'student_index':      student_idx,
            'company_supervisor': request.form.get('company_supervisor', ''),
            'study_type':         request.form.get('study_type', 'stacjonarne'),
            'notes':              request.form.get('notes', ''),
            'type':               'internship_request',
        },
    )
    db.session.add(req_doc)
    db.session.commit()
    flash("Wniosek złożony! Dziekanat powiadomi Cię o decyzji.", "success")
    return redirect(url_for('student.index'))


@student_bp.route('/reapply')
@login_required
@role_required('student')
def reapply():
    internship = Internship.query.filter_by(
        student_id=current_user.id, status='cancelled'
    ).first()
    if internship:
        db.session.delete(internship)
        db.session.commit()
    return redirect(url_for('student.index'))


@student_bp.route('/attachment/<int:attachment_id>', methods=['GET', 'POST'])
@login_required
@role_required('student')
def attachment_form(attachment_id):
    if attachment_id not in STUDENT_ATTACHMENT_IDS:
        flash("Nie masz dostępu do tego załącznika.", "error")
        return redirect(url_for('student.index'))

    a = Attachment.query.get_or_404(attachment_id)

    # Zał. 1 – Porozumienie (DB id=2)
    if attachment_id == 2:
        return _attachment_generic_form(a, attachment_id, [
            ("company_name",    "Nazwa instytucji / zakładu pracy *", "text",     "Pełna nazwa zakładu pracy"),
            ("company_address", "Adres zakładu pracy *",              "text",     "ul. Przykładowa 1, 82-300 Elbląg"),
            ("company_nip",     "NIP zakładu",                        "text",     "000-000-00-00"),
            ("company_contact", "Osoba kontaktowa / opiekun zakładowy","text",    "imię i nazwisko, stanowisko"),
            ("student_name",    "Imię i nazwisko studenta *",          "text",     "Jan Kowalski"),
            ("album_number",    "Numer albumu *",                      "text",     "12345"),
            ("specialization",  "Specjalność",                         "text",     "np. Systemy informatyczne"),
            ("date_from",       "Termin od *",                         "date",     ""),
            ("date_to",         "Termin do *",                         "date",     ""),
        ])

    # Zał. 2 – Program praktyki (DB id=3)
    if attachment_id == 3:
        return _attachment_generic_form(a, attachment_id, [
            ("cel_praktyki",    "Cel praktyki *",                      "textarea",
             "Np. Zapoznanie się z praktycznym zastosowaniem wiedzy z zakresu informatyki, udział w projektach IT."),
            ("zakres_zadan",    "Zakres wykonywanych zadań *",         "textarea",
             "Np. Udział w tworzeniu oprogramowania, testowanie, dokumentowanie, wsparcie użytkowników."),
            ("oczekiwane_efekty","Oczekiwane efekty kształcenia",      "textarea",
             "Np. Uzyskanie kompetencji z zakresu pracy w środowisku zawodowym, znajomość narzędzi programistycznych."),
            ("miejsce",         "Miejsce odbywania praktyki",          "text",     "Nazwa firmy, miejscowość"),
        ])

    # Zał. 2a – Program i harmonogram (DB id=4)
    if attachment_id == 4:
        return _attachment_generic_form(a, attachment_id, [
            ("tydzien1", "Tydzień 1 – zakres zadań",  "textarea", "Np. Zapoznanie z firmą, BHP, strukturą organizacyjną"),
            ("tydzien2", "Tydzień 2 – zakres zadań",  "textarea", "Np. Obserwacja pracy działów IT"),
            ("tydzien3", "Tydzień 3 – zakres zadań",  "textarea", "Np. Samodzielna realizacja przydzielonych zadań"),
            ("tydzien4", "Tydzień 4 – zakres zadań",  "textarea", "Np. Kontynuacja projektu, raportowanie"),
            ("uwagi",    "Uwagi dodatkowe",           "textarea", ""),
        ])

    # Zał. 3 – dedykowany formularz Karta praktyki (DB id=5)
    if attachment_id == 5:
        return _attachment_karta(a)

    # Zał. 4 – Potwierdzenie efektów uczenia się (DB id=6)
    if attachment_id == 6:
        return _attachment_4_efekty(a)

    # Zał. 4b – Wniosek o zaliczenie (DB id=8)
    if attachment_id == 8:
        return _attachment_generic_form(a, attachment_id, [
            ("student_name",    "Imię i nazwisko studenta *",          "text",     ""),
            ("album_number",    "Numer albumu *",                      "text",     ""),
            ("typ_doswiadczenia","Typ doświadczenia zawodowego *",      "text",
             "praca zawodowa / staż / działalność gospodarcza"),
            ("pracodawca",      "Pracodawca / firma *",                "text",     ""),
            ("okres_od",        "Okres zatrudnienia – od",             "date",     ""),
            ("okres_do",        "Okres zatrudnienia – do",             "date",     ""),
            ("stanowisko",      "Stanowisko / zakres obowiązków *",    "textarea",
             "Opisz wykonywane obowiązki i ich związek z kierunkiem informatyka"),
            ("uzasadnienie",    "Uzasadnienie wniosku *",              "textarea",
             "Np. Praca zawodowa w firmie X obejmowała zadania z zakresu programowania, administracji, co odpowiada efektom uczenia się określonym w programie praktyki."),
        ])

    # Zał. 5 – Kwestionariusz ankiety (DB id=9)
    if attachment_id == 9:
        return _attachment_5_ankieta(a)

    # Przekieruj do dziennika – obsługiwany przez diary_routes.py (DB id=10)
    if attachment_id == 10:
        internship = Internship.query.filter_by(student_id=current_user.id).first()
        if not internship:
            flash("Nie masz przypisanej praktyki.", "error")
            return redirect(url_for('student.index'))
        return redirect(url_for('student.diary_view', internship_id=internship.id))

    # Zał. 7 – Sprawozdanie studenta (DB id=11)
    if attachment_id == 11:
        return _attachment_7_sprawozdanie(a)

    # Zał. 7a – Sprawozdanie niestacjonarne (DB id=12) – ten sam handler co Zał. 7
    if attachment_id == 12:
        return _attachment_7_sprawozdanie(a, db_id=12, label="Załącznik nr 7a",
                                          subtitle="studia niestacjonarne / praca zawodowa")

    # Zał. 9 – Oświadczenie instytucji (DB id=14) – upload skanu
    if attachment_id == 14:
        return _attachment_9_oswiadczenie(a)

    # ── Generyczny fallback dla pozostałych załączników ──
    if request.method == 'POST':
        action = request.form.get('action', 'save')
        text = request.form.get('text', '').strip()

        if action == 'pdf':
            return _generate_pdf(a, text)

        if 'Sprawozdanie' in a.name and not validate_one_sentence(text):
            flash('Sprawozdanie może zawierać maksymalnie jedno zdanie.', 'error')
            return redirect(url_for('student.attachment_form', attachment_id=attachment_id))

        file = request.files.get('file')
        saved_path = None
        if file and file.filename:
            uploads = os.path.join(current_app.instance_path, 'uploads')
            os.makedirs(uploads, exist_ok=True)
            fname = secure_filename(file.filename)
            dest_path = os.path.join(uploads, f"{uuid.uuid4().hex}_{fname}")
            file.save(dest_path)
            saved_path = dest_path

        internship = Internship.query.filter_by(student_id=current_user.id).first()
        if not internship:
            flash("Nie masz przypisanej praktyki.", "error")
            return redirect(url_for('student.index'))
        sub = DocumentSubmission(
            user_id=current_user.id,
            attachment_id=attachment_id,
            internship_id=internship.id,
            data={'text': text},
            file_path=saved_path,
            status='submitted'
        )
        db.session.add(sub)
        db.session.commit()
        flash('Dokument przesłany.', 'success')
        return redirect(url_for('student.index'))

    meta = ATTACHMENT_META.get(a.id, {"title": a.name, "desc": a.description or "", "icon": "📄"})
    content = f"""
    <div class="page-header">
      <div class="page-header-inner">
        <div class="page-title-group">
          <h1>{meta['title']}</h1>
          <div class="breadcrumb">
            <a href="{url_for('auth.dashboard')}">Dashboard</a>
            <span>›</span>
            <a href="{url_for('student.index')}">Panel studenta</a>
            <span>›</span>
            <span>{meta['title']}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="student-container">
      {_flash_html()}
      <div class="card" style="margin-top:20px;">
        <div class="card-header"><h2>{meta['title']}</h2></div>
        <div class="card-body">
          <p style="color:var(--text-muted);margin-bottom:20px;">{meta['desc']}</p>
          <form method="post" enctype="multipart/form-data">
            <div class="form-group" style="margin-bottom:16px;">
              <label>Tekst / komentarz</label>
              <textarea name="text" rows="6" id="text-input"></textarea>
            </div>
            <div class="form-group" style="margin-bottom:20px;">
              <label>Załącz plik (opcjonalnie)</label>
              <input type="file" name="file" style="padding:6px;">
            </div>
            <div style="display:flex;gap:10px;flex-wrap:wrap;">
              <button type="submit" name="action" value="save" class="btn btn-primary">Wyślij dokument</button>
              <button type="submit" name="action" value="pdf" class="btn btn-ghost" formtarget="_blank">Pobierz PDF</button>
              <a href="{url_for('student.index')}" class="btn btn-ghost">Powrót</a>
            </div>
          </form>
        </div>
      </div>
    </div>
    """
    return _render(content)


# ---------------------------------------------------------------------------
# _attachment_generic_form – reużywalny formularz dla prostych załączników
# ---------------------------------------------------------------------------

def _attachment_generic_form(attachment, db_id: int, fields: list):
    """
    fields: lista krotek (name, label, type, placeholder)
    type: 'text' | 'date' | 'textarea'
    """
    import html as _h

    doc = DocumentSubmission.query.filter_by(
        user_id=current_user.id,
        attachment_id=db_id
    ).order_by(DocumentSubmission.id.desc()).first()

    saved = doc.data if (doc and doc.data) else {}
    status = doc.status if doc else "draft"
    status_label, status_cls = STATUS_LABELS.get(status, ("Brak", "badge-draft"))

    if request.method == 'POST':
        action = request.form.get('action', 'save')
        data = {name: request.form.get(name, '').strip() for name, *_ in fields}

        if not doc:
            internship = Internship.query.filter_by(student_id=current_user.id).first()
            if not internship:
                flash("Nie masz przypisanej praktyki. Skontaktuj się z dziekanatem.", "error")
                return redirect(url_for('student.index'))
            doc = DocumentSubmission(
                user_id=current_user.id,
                attachment_id=db_id,
                internship_id=internship.id,
                status="draft"
            )
            db.session.add(doc)

        doc.data = data
        if action == 'submit':
            doc.status = "submitted"
            flash(f"{attachment.name} wysłany do opiekuna.", "success")
        else:
            doc.status = "draft"
            flash("Zapisano jako szkic.", "info")
        db.session.commit()
        return redirect(url_for('student.index'))

    # Feedback od opiekuna
    rejection_html = ""
    if doc and doc.status == "rejected" and doc.comments:
        rejection_html = (
            '<div style="background:#fff3f3;border:1px solid #fed7d7;border-left:4px solid #e53e3e;'
            'padding:14px 18px;border-radius:6px;margin-bottom:16px;">'
            '<strong style="color:#c53030;display:block;margin-bottom:6px;">❌ Uwagi opiekuna:</strong>'
            f'<p style="color:#742a2a;font-size:13px;white-space:pre-wrap;margin:0;">'
            f'{_h.escape(doc.comments)}</p></div>'
        )

    # Buduj pola formularza
    fields_html = ""
    for name, label, ftype, placeholder in fields:
        val = _h.escape(str(saved.get(name, '') or ''))
        req = " *" if "*" in label else ""
        clean_label = label.replace(" *", "").replace("*", "")
        if ftype == "textarea":
            fields_html += f"""<div class="form-group" style="margin-bottom:14px;">
              <label style="display:block;font-size:12px;font-weight:700;text-transform:uppercase;
                            letter-spacing:.4px;color:#6b7280;margin-bottom:5px;">
                {_h.escape(clean_label)}{req}
              </label>
              <textarea name="{name}" rows="4"
                        style="width:100%;border:1px solid #cbd5e0;border-radius:6px;
                               padding:9px 12px;font-size:13.5px;font-family:inherit;
                               resize:vertical;outline:none;"
                        placeholder="{_h.escape(placeholder)}">{val}</textarea>
            </div>"""
        else:
            fields_html += f"""<div class="form-group" style="margin-bottom:14px;">
              <label style="display:block;font-size:12px;font-weight:700;text-transform:uppercase;
                            letter-spacing:.4px;color:#6b7280;margin-bottom:5px;">
                {_h.escape(clean_label)}{req}
              </label>
              <input type="{ftype}" name="{name}" value="{val}"
                     placeholder="{_h.escape(placeholder)}"
                     style="width:100%;border:1px solid #cbd5e0;border-radius:6px;
                            padding:9px 12px;font-size:13.5px;font-family:inherit;outline:none;">
            </div>"""

    meta = ATTACHMENT_META.get(db_id, {"title": attachment.name, "icon": "📄"})

    content = f"""
    <div class="page-header">
      <div class="page-header-inner">
        <div class="page-title-group">
          <h1>{_h.escape(meta['title'])}</h1>
          <div class="breadcrumb">
            <a href="{url_for('auth.dashboard')}">Dashboard</a>
            <span>›</span>
            <a href="{url_for('student.index')}">Panel studenta</a>
            <span>›</span>
            <span>{_h.escape(meta['title'])}</span>
          </div>
        </div>
        <span class="adm-badge {status_cls}">
          <span class="adm-badge-dot"></span>{status_label}
        </span>
      </div>
    </div>

    <div class="student-container">
      {_flash_html()}

      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;
                  padding:28px 32px;margin-top:20px;max-width:820px;">

        <div style="font-size:11px;color:#9ca3af;text-align:right;margin-bottom:6px;">
          {_h.escape(attachment.name)}
        </div>
        <div style="font-size:12px;margin-bottom:20px;">
          <strong>Akademia Nauk Stosowanych w Elblągu</strong><br>
          <span style="font-style:italic;color:#6b7280;">
            Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego
          </span>
        </div>

        {rejection_html}

        <form method="post">
          {fields_html}
          <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;
                      border-top:1px solid #e2e8f0;padding-top:18px;margin-top:8px;">
            <button type="submit" name="action" value="save" class="btn btn-ghost">
              💾 Zapisz szkic
            </button>
            <button type="submit" name="action" value="submit" class="btn btn-primary"
                    onclick="return confirm('Wysłać do opiekuna?')">
              📤 Wyślij do opiekuna
            </button>
            <a href="{url_for('student.index')}" class="btn btn-ghost" style="margin-left:auto;">
              ← Powrót
            </a>
          </div>
        </form>
      </div>
    </div>"""
    return _render(content)


# ---------------------------------------------------------------------------
# Załącznik nr 9 – Oświadczenie instytucji (DB id=14) – upload skanu
# ---------------------------------------------------------------------------

def _attachment_9_oswiadczenie(_attachment):
    import html as _h

    doc = DocumentSubmission.query.filter_by(
        user_id=current_user.id,
        attachment_id=14
    ).order_by(DocumentSubmission.id.desc()).first()

    status = doc.status if doc else "draft"
    status_label, status_cls = STATUS_LABELS.get(status, ("Brak", "badge-draft"))

    if request.method == 'POST':
        action = request.form.get('action', 'save')
        company_name = request.form.get('company_name', '').strip()
        notes = request.form.get('notes', '').strip()

        file = request.files.get('file')
        saved_path = None
        if file and file.filename:
            uploads = os.path.join(current_app.instance_path, 'uploads')
            os.makedirs(uploads, exist_ok=True)
            fname = secure_filename(file.filename)
            dest = os.path.join(uploads, f"{uuid.uuid4().hex}_{fname}")
            file.save(dest)
            saved_path = dest

        if not doc:
            internship = Internship.query.filter_by(student_id=current_user.id).first()
            if not internship:
                flash("Nie masz przypisanej praktyki.", "error")
                return redirect(url_for('student.index'))
            doc = DocumentSubmission(
                user_id=current_user.id,
                attachment_id=14,
                internship_id=internship.id,
                status="draft"
            )
            db.session.add(doc)

        doc.data = {"company_name": company_name, "notes": notes}
        if saved_path:
            doc.file_path = saved_path
        if action == 'submit':
            if not doc.file_path:
                flash("Proszę załączyć skan oświadczenia.", "error")
                return redirect(url_for('student.attachment_form', attachment_id=14))
            doc.status = "submitted"
            flash("Oświadczenie instytucji wysłane.", "success")
        else:
            doc.status = "draft"
            flash("Zapisano.", "info")
        db.session.commit()
        return redirect(url_for('student.index'))

    company_val = _h.escape(str((doc.data or {}).get('company_name', '') if doc else ''))
    notes_val = _h.escape(str((doc.data or {}).get('notes', '') if doc else ''))
    has_file = bool(doc and doc.file_path)

    rejection_html = ""
    if doc and doc.status == "rejected" and doc.comments:
        rejection_html = (
            '<div style="background:#fff3f3;border:1px solid #fed7d7;border-left:4px solid #e53e3e;'
            'padding:14px 18px;border-radius:6px;margin-bottom:16px;">'
            '<strong style="color:#c53030;display:block;margin-bottom:6px;">❌ Uwagi opiekuna:</strong>'
            f'<p style="color:#742a2a;font-size:13px;white-space:pre-wrap;margin:0;">'
            f'{_h.escape(doc.comments)}</p></div>'
        )

    content = f"""
    <div class="page-header">
      <div class="page-header-inner">
        <div class="page-title-group">
          <h1>Oświadczenie instytucji (Zał. 9)</h1>
          <div class="breadcrumb">
            <a href="{url_for('auth.dashboard')}">Dashboard</a>
            <span>›</span>
            <a href="{url_for('student.index')}">Panel studenta</a>
            <span>›</span>
            <span>Załącznik nr 9</span>
          </div>
        </div>
        <span class="adm-badge {status_cls}">
          <span class="adm-badge-dot"></span>{status_label}
        </span>
      </div>
    </div>

    <div class="student-container">
      {_flash_html()}

      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;
                  padding:28px 32px;margin-top:20px;max-width:820px;">

        <div style="font-size:11px;color:#9ca3af;text-align:right;margin-bottom:6px;">
          Załącznik nr 9
        </div>
        <div style="font-size:12px;margin-bottom:16px;">
          <strong>Akademia Nauk Stosowanych w Elblągu</strong><br>
          <span style="font-style:italic;color:#6b7280;">
            Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego
          </span>
        </div>
        <div style="text-align:center;font-weight:700;font-size:14px;text-transform:uppercase;
                    letter-spacing:.5px;margin-bottom:24px;color:#1a2744;">
          OŚWIADCZENIE INSTYTUCJI<br>
          <span style="font-size:12px;font-weight:400;text-transform:none;">
            w sprawie przyjęcia studenta na praktykę zawodową
          </span>
        </div>

        {rejection_html}

        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:6px;
                    padding:12px 16px;margin-bottom:20px;font-size:12.5px;color:#92400e;">
          <strong>Wymagania:</strong> Pobierz formularz w dziekanacie lub ze strony uczelni,
          uzyskaj podpis i <strong>pieczęć zakładu pracy</strong>, następnie zeskanuj i wgraj tutaj.
          Wymagane są oryginały, a nie skany w przypadku dokumentów składanych w dziekanacie.
        </div>

        <form method="post" enctype="multipart/form-data">
          <div class="form-group" style="margin-bottom:14px;">
            <label style="display:block;font-size:12px;font-weight:700;text-transform:uppercase;
                          letter-spacing:.4px;color:#6b7280;margin-bottom:5px;">
              Nazwa instytucji *
            </label>
            <input type="text" name="company_name" value="{company_val}"
                   placeholder="Pełna nazwa zakładu pracy"
                   style="width:100%;border:1px solid #cbd5e0;border-radius:6px;
                          padding:9px 12px;font-size:13.5px;font-family:inherit;">
          </div>

          <div class="form-group" style="margin-bottom:14px;">
            <label style="display:block;font-size:12px;font-weight:700;text-transform:uppercase;
                          letter-spacing:.4px;color:#6b7280;margin-bottom:5px;">
              Uwagi (opcjonalnie)
            </label>
            <textarea name="notes" rows="3"
                      style="width:100%;border:1px solid #cbd5e0;border-radius:6px;
                             padding:9px 12px;font-size:13.5px;font-family:inherit;resize:vertical;"
                      placeholder="Dodatkowe informacje...">{notes_val}</textarea>
          </div>

          <div class="form-group" style="margin-bottom:20px;">
            <label style="display:block;font-size:12px;font-weight:700;text-transform:uppercase;
                          letter-spacing:.4px;color:#6b7280;margin-bottom:5px;">
              Skan oświadczenia (PDF / JPG / PNG) {'✅ plik załączony' if has_file else '⚠️ brak pliku'}
            </label>
            <input type="file" name="file" accept=".pdf,.jpg,.jpeg,.png"
                   style="width:100%;border:1px solid #cbd5e0;border-radius:6px;
                          padding:9px 12px;font-size:13px;">
            {'<div style="font-size:12px;color:#16a34a;margin-top:4px;">✅ Plik jest już załączony. Wgraj nowy tylko jeśli chcesz go zastąpić.</div>' if has_file else ''}
          </div>

          <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;
                      border-top:1px solid #e2e8f0;padding-top:18px;">
            <button type="submit" name="action" value="save" class="btn btn-ghost">
              💾 Zapisz
            </button>
            <button type="submit" name="action" value="submit" class="btn btn-primary"
                    onclick="return confirm('Wysłać oświadczenie do opiekuna?')">
              📤 Wyślij do opiekuna
            </button>
            <a href="{url_for('student.index')}" class="btn btn-ghost" style="margin-left:auto;">
              ← Powrót
            </a>
          </div>
        </form>
      </div>
    </div>"""
    return _render(content)


# ---------------------------------------------------------------------------
# Załącznik nr 3 – dedykowany widok (Karta Praktyki Zawodowej) – DB id=5
# ---------------------------------------------------------------------------

def _attachment_karta(attachment):
    doc = DocumentSubmission.query.filter_by(
        user_id=current_user.id,
        attachment_id=5
    ).order_by(DocumentSubmission.id.desc()).first()

    saved = doc.data if (doc and doc.data) else {}
    status = doc.status if doc else "draft"
    status_label, status_cls = STATUS_LABELS.get(status, ("Brak", "badge-draft"))

    def v(key, default=""):
        return saved.get(key, default)

    if request.method == 'POST':
        action = request.form.get('action', 'save')
        data = {
            "agreement_number":      request.form.get('agreement_number', '').strip(),
            "agreement_date":        request.form.get('agreement_date', '').strip(),
            "company_name":          request.form.get('company_name', '').strip(),
            "student_name":          request.form.get('student_name', '').strip(),
            "album_number":          request.form.get('album_number', '').strip(),
            "study_type":            request.form.get('study_type', 'stacjonarne'),
            "specialization":        request.form.get('specialization', '').strip(),
            "internship_duration":   request.form.get('internship_duration', '6 miesięcy  (120 dni roboczych)').strip(),
            "university_supervisor": request.form.get('university_supervisor', '').strip(),
            "date_from":             request.form.get('date_from', '').strip(),
            "date_to":               request.form.get('date_to', '').strip(),
            "internship_year":       request.form.get('internship_year', '').strip(),
            "company_supervisor":    request.form.get('company_supervisor', '').strip(),
            "supervisor_role":       request.form.get('supervisor_role', '').strip(),
            "bhp_confirmed":         request.form.get('bhp_confirmed', '0'),
        }

        if action == 'pdf':
            return _generate_attachment3_pdf(data)

        if not doc:
            internship = Internship.query.filter_by(student_id=current_user.id).first()
            if not internship:
                flash("Nie masz przypisanej praktyki. Skontaktuj się z dziekanatem.", "error")
                return redirect(url_for('student.index'))
            doc = DocumentSubmission(
                user_id=current_user.id,
                attachment_id=5,
                internship_id=internship.id,
                status="draft"
            )
            db.session.add(doc)

        doc.data = data
        if action == 'submit':
            doc.status = "submitted"
            flash("Karta praktyki zawodowej wysłana do opiekuna uczelnianenego.", "success")
        else:
            doc.status = "draft"
            flash("Karta zapisana jako szkic.", "info")
        db.session.commit()
        return redirect(url_for('student.index'))

    study_options = ""
    for val, label in [("stacjonarne", "inżynierskie stacjonarne"),
                        ("niestacjonarne", "inżynierskie niestacjonarne")]:
        sel = "selected" if v("study_type", "stacjonarne") == val else ""
        study_options += f'<option value="{val}" {sel}>{label}</option>'

    import html as _html
    rejection_feedback_html = ""
    if doc and doc.status == "rejected" and doc.comments:
        rejection_feedback_html = (
            '<div class="alert" style="background:#fff3f3;border:1px solid #fed7d7;'
            'border-left:4px solid #e53e3e;margin-top:16px;padding:14px 18px;border-radius:6px;">'
            '<strong style="color:#c53030;display:block;margin-bottom:6px;">❌ Dokument odrzucony – uwagi opiekuna:</strong>'
            f'<p style="color:#742a2a;font-size:13px;white-space:pre-wrap;margin:0;">{_html.escape(doc.comments)}</p>'
            '</div>'
        )

    content = f"""
    <div class="page-header">
      <div class="page-header-inner">
        <div class="page-title-group">
          <h1>Karta praktyki zawodowej</h1>
          <div class="breadcrumb">
            <a href="{url_for('auth.dashboard')}">Dashboard</a>
            <span>›</span>
            <a href="{url_for('student.index')}">Panel studenta</a>
            <span>›</span>
            <span>Załącznik nr 3</span>
          </div>
        </div>
        <span class="adm-badge {status_cls}">
          <span class="adm-badge-dot"></span>{status_label}
        </span>
      </div>
    </div>

    <div class="student-container">
      {_flash_html()}

      <div class="alert alert-info" style="margin-top:20px;">
        <span>📋</span>
        <div>
          <strong>Załącznik nr 3 – Karta praktyki zawodowej</strong><br>
          <span style="font-size:12.5px;">
            Wypełnij formularz skierowania na praktykę zawodową.
            Po zapisaniu możesz go w każdej chwili edytować.
            Kliknij <strong>Wyślij do opiekuna</strong>, gdy dokument jest gotowy.
          </span>
        </div>
      </div>

      {rejection_feedback_html}

      <form method="post" id="form3">

        <div class="card" style="margin-top:20px;">
          <div class="card-header"><h2>Skierowanie na praktykę</h2></div>
          <div class="card-body">
            <div class="form-section">
              <div class="form-grid">
                <div class="form-group">
                  <label>Numer porozumienia <span class="required">*</span></label>
                  <input type="text" name="agreement_number"
                         value="{v('agreement_number')}" placeholder="np. 12/2026">
                </div>
                <div class="form-group">
                  <label>Data porozumienia <span class="required">*</span></label>
                  <input type="date" name="agreement_date" value="{v('agreement_date')}">
                </div>
              </div>
            </div>
            <div class="form-section">
              <div class="form-group">
                <label>Nazwa instytucji / zakładu pracy <span class="required">*</span></label>
                <input type="text" name="company_name"
                       value="{v('company_name')}" placeholder="Pełna nazwa zakładu pracy">
                <div class="form-hint">Wpisz dokładną nazwę zakładu, do którego kierowany jest student.</div>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><h2>Dane studenta</h2></div>
          <div class="card-body">
            <div class="form-section">
              <div class="form-grid">
                <div class="form-group">
                  <label>Imię i nazwisko <span class="required">*</span></label>
                  <input type="text" name="student_name"
                         value="{v('student_name')}" placeholder="Jan Kowalski">
                </div>
                <div class="form-group">
                  <label>Numer albumu <span class="required">*</span></label>
                  <input type="text" name="album_number"
                         value="{v('album_number')}" placeholder="np. 12345">
                </div>
              </div>
            </div>
            <div class="form-section">
              <div class="form-grid">
                <div class="form-group">
                  <label>Studia <span class="required">*</span></label>
                  <select name="study_type">{study_options}</select>
                </div>
                <div class="form-group">
                  <label>Specjalność</label>
                  <input type="text" name="specialization"
                         value="{v('specialization')}" placeholder="np. Systemy informatyczne">
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><h2>Szczegóły praktyki</h2></div>
          <div class="card-body">
            <div class="form-section">
              <div class="form-grid">
                <div class="form-group">
                  <label>Czas trwania praktyki</label>
                  <input type="text" name="internship_duration"
                         value="{v('internship_duration', '6 miesięcy  (120 dni roboczych)')}" readonly>
                  <div class="form-hint">Wartość ustalona przez uczelnię.</div>
                </div>
                <div class="form-group">
                  <label>Uczelniany opiekun praktyki zawodowej</label>
                  <input type="text" name="university_supervisor"
                         value="{v('university_supervisor')}" placeholder="dr Jan Nowak">
                </div>
              </div>
            </div>
            <div class="form-section">
              <div class="form-section-title">Termin praktyki</div>
              <div class="form-grid-3">
                <div class="form-group">
                  <label>Od <span class="required">*</span></label>
                  <input type="date" name="date_from" value="{v('date_from')}">
                </div>
                <div class="form-group">
                  <label>Do <span class="required">*</span></label>
                  <input type="date" name="date_to" value="{v('date_to')}">
                </div>
                <div class="form-group">
                  <label>Rok (202…)</label>
                  <input type="text" name="internship_year"
                         value="{v('internship_year')}" placeholder="np. 2026"
                         maxlength="4" style="font-family:\'IBM Plex Mono\',monospace;">
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><h2>Zakładowy opiekun praktyki zawodowej</h2></div>
          <div class="card-body">
            <div class="form-section">
              <div class="form-grid">
                <div class="form-group">
                  <label>Imię i nazwisko opiekuna zakładowego</label>
                  <input type="text" name="company_supervisor"
                         value="{v('company_supervisor')}" placeholder="mgr Anna Wiśniewska">
                </div>
                <div class="form-group">
                  <label>Funkcja / zajmowane stanowisko</label>
                  <input type="text" name="supervisor_role"
                         value="{v('supervisor_role')}" placeholder="np. Kierownik działu IT">
                </div>
              </div>
            </div>
            <div class="form-section">
              <div style="display:flex;align-items:center;gap:10px;margin-top:4px;">
                <input type="checkbox" name="bhp_confirmed" value="1" id="bhp"
                       {'checked' if v('bhp_confirmed') == '1' else ''}
                       style="width:18px;height:18px;cursor:pointer;flex-shrink:0;">
                <label for="bhp" style="font-size:13.5px;font-weight:500;
                                         color:var(--text-mid);cursor:pointer;">
                  Potwierdzam odbycie szkolenia BHP przez studenta
                </label>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-body" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;">
            <button type="submit" name="action" value="save" class="btn btn-ghost">
              💾 Zapisz szkic
            </button>
            <button type="submit" name="action" value="submit" class="btn btn-primary"
                    onclick="return confirm('Wysłać kartę do opiekuna uczelnianenego?')">
              📤 Wyślij do opiekuna
            </button>
            <button type="submit" name="action" value="pdf" class="btn btn-teal" formtarget="_blank">
              📄 Pobierz PDF
            </button>
            <a href="{url_for('student.index')}" class="btn btn-ghost" style="margin-left:auto;">
              ← Powrót do panelu
            </a>
          </div>
        </div>

      </form>
    </div>

    <script>
    (function() {{
      const form = document.getElementById('form3');
      if (!form) return;
      form.addEventListener('submit', function(e) {{
        const action = e.submitter && e.submitter.value;
        if (action === 'pdf') return;
        const from = form.querySelector('[name=date_from]').value;
        const to   = form.querySelector('[name=date_to]').value;
        if (from && to && from > to) {{
          alert('Data końca praktyki nie może być wcześniejsza niż data początku.');
          e.preventDefault(); return;
        }}
      }});
    }})();
    </script>
    """
    return _render(content)


# ---------------------------------------------------------------------------
# Załącznik nr 4 – Potwierdzenie efektów uczenia się – DB id=6
# ---------------------------------------------------------------------------

LEARNING_OUTCOMES_4 = [
    (1,  "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących "
         "informatyki z zachowaniem standardów i norm technicznych"),
    (2,  "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce"),
    (3,  "Zna ekonomiczne, prawne skutki własnych działań podejmowanych w ramach praktyki "
         "oraz ograniczenia wynikające z prawa autorskiego i kodeksu pracy"),
    (4,  "Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka"),
    (5,  "Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu wymaganego "
         "do realizacji powierzonego zadania, posługując się rozmaitymi źródłami "
         "literaturowymi i zasobami publikowanymi w języku polskim jak i angielskim"),
    (6,  "W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść "
         "swoje kompetencje, wiedzę i umiejętności, co najmniej z dwóch zakresów: "
         "zadania dotyczące sprzętu i oprogramowania: np.: programowania, administrowanie "
         "siecią komputerową, konserwacja sprzętu i oprogramowania, bieżące usuwanie "
         "usterek, administrowanie zasobami informatycznymi, zakładu pracy / instytucji, "
         "(e)-usługami"),
    (7,  "Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań w ramach "
         "praktyki, a także referuje ustnie prezentowane w niej zagadnienia"),
    (8,  "Potrafi zidentyfikować problem informatyczny występujący w zakładzie pracy / "
         "instytucji, opisać go, przedstawić koncepcję rozwiązania i ją zrealizować"),
    (9,  "Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu działalności "
         "informatycznej zakładu pracy/instytucji stosując normy i standardy stosowane "
         "w informatyce oraz biorąc pod uwagę aspekty środowiskowe i etyczne"),
    (10, "Pracuje w zespole zajmującym się zawodowo branżą IT"),
    (11, "Przestrzega zasad etyki zawodowej i zgodnie z tymi zasadami korzysta z wiedzy "
         "i pomocy doświadczonych kolegów"),
    (12, "Kontaktując się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne "
         "informacje do realizacji planowanego zadania, jak i przekazać im w sposób "
         "zrozumiały informacje i opinie z zakresu informatyki"),
    (13, "Dostrzega w praktyce tempo deaktualizacji wiedzy informatycznej oraz skutki "
         "działalności informatyków w szczególności ekonomiczne i społeczne"),
]


def _attachment_4_efekty(_attachment):
    doc = DocumentSubmission.query.filter_by(
        user_id=current_user.id,
        attachment_id=6
    ).order_by(DocumentSubmission.id.desc()).first()

    saved = doc.data if (doc and doc.data) else {}
    status = doc.status if doc else "draft"
    status_label, status_cls = STATUS_LABELS.get(status, ("Brak", "badge-draft"))

    def v(key, default=""):
        return saved.get(key, default)

    if request.method == 'POST':
        action = request.form.get('action', 'save')
        outcomes = {}
        for num, _ in LEARNING_OUTCOMES_4:
            outcomes[f"outcome_{num:02d}"] = request.form.get(f"outcome_{num:02d}", "nie_uzyskal")

        data = {
            "student_name":   request.form.get('student_name', '').strip(),
            "album_number":   request.form.get('album_number', '').strip(),
            "specialization": request.form.get('specialization', '').strip(),
            "hours_total":    request.form.get('hours_total', '').strip(),
            **outcomes,
        }

        if not doc:
            internship = Internship.query.filter_by(student_id=current_user.id).first()
            if not internship:
                flash("Nie masz przypisanej praktyki. Skontaktuj się z dziekanatem.", "error")
                return redirect(url_for('student.index'))
            doc = DocumentSubmission(
                user_id=current_user.id,
                attachment_id=6,
                internship_id=internship.id,
                status="draft"
            )
            db.session.add(doc)

        doc.data = data
        if action == 'submit':
            doc.status = "submitted"
            flash("Potwierdzenie efektów uczenia się wysłane do opiekuna.", "success")
        else:
            doc.status = "draft"
            flash("Formularz zapisany jako szkic.", "info")
        db.session.commit()
        return redirect(url_for('student.index'))

    import html as _html

    rejection_feedback_4 = ""
    if doc and doc.status == "rejected" and doc.comments:
        rejection_feedback_4 = (
            '<div class="alert" style="background:#fff3f3;border:1px solid #fed7d7;'
            'border-left:4px solid #e53e3e;margin-top:16px;padding:14px 18px;border-radius:6px;">'
            '<strong style="color:#c53030;display:block;margin-bottom:6px;">❌ Dokument odrzucony – uwagi opiekuna:</strong>'
            f'<p style="color:#742a2a;font-size:13px;white-space:pre-wrap;margin:0;">{_html.escape(doc.comments)}</p>'
            '</div>'
        )

    rows_html = ""
    for num, text in LEARNING_OUTCOMES_4:
        key = f"outcome_{num:02d}"
        saved_val = v(key, "nie_uzyskal")
        checked_uzy = 'checked' if saved_val == "uzyskal" else ''
        checked_nie = 'checked' if saved_val != "uzyskal" else ''
        escaped_text = _html.escape(text)
        rows_html += f"""
        <tr>
          <td style="width:36px;text-align:center;font-weight:700;color:#4a5568;
                     border:1px solid #cbd5e0;padding:10px 8px;">{num:02d}</td>
          <td style="border:1px solid #cbd5e0;padding:10px 14px;font-size:13px;
                     line-height:1.55;color:#2d3748;">{escaped_text}</td>
          <td style="width:160px;text-align:center;border:1px solid #cbd5e0;
                     padding:10px 8px;vertical-align:middle;">
            <label style="display:flex;align-items:center;gap:6px;justify-content:center;
                          cursor:pointer;margin-bottom:6px;font-size:12.5px;color:#276749;">
              <input type="radio" name="{key}" value="uzyskal" {checked_uzy}
                     style="width:15px;height:15px;accent-color:#276749;">
              uzyskał/a
            </label>
            <label style="display:flex;align-items:center;gap:6px;justify-content:center;
                          cursor:pointer;font-size:12.5px;color:#c53030;">
              <input type="radio" name="{key}" value="nie_uzyskal" {checked_nie}
                     style="width:15px;height:15px;accent-color:#c53030;">
              nie uzyskał/a
            </label>
          </td>
        </tr>"""

    internship = Internship.query.filter_by(student_id=current_user.id).first()
    hours_worked = internship.total_hours_worked if internship else ""
    full_name = getattr(current_user, 'full_name', '') or current_user.email

    content = f"""
    <div class="page-header">
      <div class="page-header-inner">
        <div class="page-title-group">
          <h1>Potwierdzenie efektów uczenia się</h1>
          <div class="breadcrumb">
            <a href="{url_for('auth.dashboard')}">Dashboard</a>
            <span>›</span>
            <a href="{url_for('student.index')}">Panel studenta</a>
            <span>›</span>
            <span>Załącznik nr 4</span>
          </div>
        </div>
        <span class="adm-badge {status_cls}">
          <span class="adm-badge-dot"></span>{status_label}
        </span>
      </div>
    </div>

    <div class="student-container">
      {_flash_html()}
      {rejection_feedback_4}

      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;
                  padding:32px 36px;margin-top:20px;max-width:860px;">

        <div style="text-align:center;margin-bottom:28px;">
          <div style="font-size:10px;color:#718096;text-align:right;margin-bottom:4px;">
            Załącznik nr 4
          </div>
          <div style="font-weight:700;font-size:15px;text-transform:uppercase;
                      letter-spacing:.4px;line-height:1.5;color:#1a202c;">
            POTWIERDZENIE UZYSKANIA<br>
            EFEKTÓW UCZENIA SIĘ W RAMACH<br>
            PRAKTYKI ZAWODOWEJ
          </div>
        </div>

        <form method="post" id="form4">

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px;">
            <div class="form-group">
              <label>Student / ka <span class="required">*</span></label>
              <input type="text" name="student_name"
                     value="{_html.escape(v('student_name', full_name))}"
                     placeholder="Imię i nazwisko">
            </div>
            <div class="form-group">
              <label>Nr albumu <span class="required">*</span></label>
              <input type="text" name="album_number"
                     value="{_html.escape(v('album_number'))}"
                     placeholder="np. 12345">
            </div>
          </div>

          <div style="display:grid;grid-template-columns:2fr 1fr;gap:14px;margin-bottom:20px;">
            <div class="form-group">
              <label>Specjalność</label>
              <input type="text" name="specialization"
                     value="{_html.escape(v('specialization'))}"
                     placeholder="np. Systemy informatyczne">
            </div>
            <div class="form-group">
              <label>Liczba godzin praktyki</label>
              <input type="number" name="hours_total"
                     value="{v('hours_total', str(hours_worked))}"
                     placeholder="120" min="0">
            </div>
          </div>

          <div style="font-size:13px;color:#4a5568;margin-bottom:14px;
                      padding:10px 14px;background:#f7fafc;border-radius:6px;
                      border:1px solid #e2e8f0;">
            Kierunek studiów: <strong>Informatyka</strong><br>
            W ramach praktyki zawodowej zrealizowanej w wymiarze
            <strong><span id="hours-display">{v('hours_total', str(hours_worked))}</span> godzin</strong>
            uzyskał/a &nbsp;/&nbsp; nie uzyskał/a * zakładane dla praktyki zawodowej efekty uczenia się:
          </div>

          <div style="overflow-x:auto;margin-bottom:24px;">
            <table style="width:100%;border-collapse:collapse;font-family:'IBM Plex Sans',sans-serif;">
              <thead>
                <tr style="background:#f7fafc;">
                  <th style="width:36px;border:1px solid #cbd5e0;padding:10px 8px;
                             font-size:12px;color:#718096;text-align:center;">#</th>
                  <th style="border:1px solid #cbd5e0;padding:10px 14px;
                             font-size:12px;color:#718096;text-align:left;">
                    Efekty uczenia się
                  </th>
                  <th style="width:160px;border:1px solid #cbd5e0;padding:10px 8px;
                             font-size:12px;color:#718096;text-align:center;">
                    Potwierdzenie uzyskania efektów
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows_html}
              </tbody>
            </table>
          </div>

          <div style="background:#fffbf0;border:1px solid #f6e05e;border-radius:6px;
                      padding:12px 16px;font-size:12px;color:#744210;margin-bottom:24px;">
            <strong>Uwaga:</strong> Po wypełnieniu i wysłaniu formularza opiekun uczelniany
            zatwierdzi potwierdzenie. Podpis bezpośredniego opiekuna zakładowego oraz
            pieczęć zakładu pracy zostaną złożone na wydruku.
          </div>

          <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;">
            <button type="submit" name="action" value="save" class="btn btn-ghost">
              💾 Zapisz szkic
            </button>
            <button type="submit" name="action" value="submit" class="btn btn-primary"
                    onclick="return confirm('Wysłać potwierdzenie efektów do opiekuna?')">
              📤 Wyślij do opiekuna
            </button>
            <a href="{url_for('student.index')}" class="btn btn-ghost" style="margin-left:auto;">
              ← Powrót do panelu
            </a>
          </div>

        </form>
      </div>
    </div>

    <script>
    (function() {{
      const hi = document.getElementById('hours-display');
      const inp = document.querySelector('[name=hours_total]');
      if (inp && hi) {{
        inp.addEventListener('input', function() {{ hi.textContent = this.value || '...'; }});
      }}
    }})();
    </script>
    """
    return _render(content)


# ---------------------------------------------------------------------------
# Załącznik nr 5 – Kwestionariusz ankiety – DB id=9
# ---------------------------------------------------------------------------

SURVEY_QUESTIONS = [
    (1,  "Poznałam/poznałem zasady funkcjonowania instytucji, w której odbywałam/odbywałem praktyki zawodowe."),
    (2,  "Poznałam/poznałem strukturę oraz regulamin organizacyjny instytucji, w której odbywałam/odbywałem praktyki zawodowe."),
    (3,  "Praktyki zawodowe umożliwiły mi pełną realizację ramowego programu praktyk zawodowych przewidzianego w ramach mojego kierunku studiów."),
    (4,  "Podczas praktyk zawodowych zwracano uwagę na przestrzeganie zasad etyki i tajemnicy zawodowej."),
    (5,  "Podczas praktyk miałam/miałem możliwość praktycznego zastosowania wiedzy teoretycznej zdobytej na zajęciach."),
    (6,  "Praktyki zawodowe przyczyniły się do pogłębienia mojej wiedzy i umiejętności zdobytych w trakcie studiów."),
    (7,  "Mogłem liczyć na wsparcie merytoryczne Opiekuna zakładowego praktyk."),
    (8,  "Mogłem liczyć na wsparcie merytoryczne Opiekuna uczelnianego praktyk."),
    (9,  "Opiekun zakładowy odpowiedzialny za praktyki zawodowe w miejscu ich odbywania potrafił prawidłowo zorganizować ich przebieg."),
    (10, "Podczas praktyk zawodowych miałam/miałem możliwość pozyskiwania materiałów niezbędnych do przygotowania mojej pracy dyplomowej."),
    (11, "Praktyki zawodowe rozwinęły moje umiejętności skutecznego komunikowania się w sytuacjach zawodowych i pracy w zespole."),
    (12, "Praktyki zawodowe nauczyły mnie samodzielności i odpowiedzialności podczas wykonywania pracy."),
    (13, "Liczba godzin realizowana w ramach praktyk zawodowych jest wystarczająca."),
    (14, "Czy po zakończeniu praktyki zawodowej chciałaby/chciałby Pani/Pan współpracować z instytucją, w której Pani/Pan zrealizowała/zrealizował praktykę?"),
]

SURVEY_SCALE = [
    ("zdecydowanie_tak",  "zdecydowanie tak"),
    ("raczej_tak",        "raczej tak"),
    ("trudno_powiedziec", "trudno powiedzieć"),
    ("raczej_nie",        "raczej nie"),
    ("zdecydowanie_nie",  "zdecydowanie nie"),
]


def _attachment_5_ankieta(_attachment):
    doc = DocumentSubmission.query.filter_by(
        user_id=current_user.id,
        attachment_id=9
    ).order_by(DocumentSubmission.id.desc()).first()

    saved = doc.data if (doc and doc.data) else {}
    status = doc.status if doc else "draft"
    status_label, status_cls = STATUS_LABELS.get(status, ("Brak", "badge-draft"))

    def v(key, default=""):
        val = saved.get(key, default)
        return val if val is not None else default

    if request.method == 'POST':
        action = request.form.get('action', 'save')
        answers = {}
        for num, _ in SURVEY_QUESTIONS:
            answers[f"q{num:02d}"] = request.form.get(f"q{num:02d}", "")

        data = {
            "rok_akademicki":  request.form.get('rok_akademicki', '').strip(),
            "kierunek":        "Informatyka",
            "forma_studiow":   request.form.get('forma_studiow', 'stacjonarne'),
            "semestr":         request.form.get('semestr', '').strip(),
            "godziny_praktyk": request.form.get('godziny_praktyk', '').strip(),
            "uwagi_dodatkowe": request.form.get('uwagi_dodatkowe', '').strip(),
            **answers,
        }

        if not doc:
            internship = Internship.query.filter_by(student_id=current_user.id).first()
            if not internship:
                flash("Nie masz przypisanej praktyki. Skontaktuj się z dziekanatem.", "error")
                return redirect(url_for('student.index'))
            doc = DocumentSubmission(
                user_id=current_user.id,
                attachment_id=9,
                internship_id=internship.id,
                status="draft"
            )
            db.session.add(doc)

        doc.data = data
        if action == 'submit':
            doc.status = "submitted"
            flash("Kwestionariusz ankiety wysłany.", "success")
        else:
            doc.status = "draft"
            flash("Ankieta zapisana jako szkic.", "info")
        db.session.commit()
        return redirect(url_for('student.index'))

    import html as _html

    internship = Internship.query.filter_by(student_id=current_user.id).first()
    hours_worked = internship.total_hours_worked if internship else ""

    # Nagłówki kolumn
    scale_headers = "".join(
        f'<th style="width:90px;border:1px solid #cbd5e0;padding:8px 4px;font-size:11.5px;'
        f'font-weight:600;color:#4a5568;text-align:center;background:#f7fafc;">{label}</th>'
        for _, label in SURVEY_SCALE
    )

    # Wiersze pytań
    rows_html = ""
    for num, text in SURVEY_QUESTIONS:
        key = f"q{num:02d}"
        saved_val = v(key, "")
        cells = ""
        for val, _ in SURVEY_SCALE:
            checked = 'checked' if saved_val == val else ''
            cells += (
                f'<td style="border:1px solid #cbd5e0;padding:8px 4px;text-align:center;">'
                f'<input type="radio" name="{key}" value="{val}" {checked} '
                f'style="width:16px;height:16px;cursor:pointer;accent-color:#3b5bdb;">'
                f'</td>'
            )
        bg = '#f7fafc' if num % 2 == 0 else '#fff'
        rows_html += (
            f'<tr style="background:{bg};">'
            f'<td style="width:32px;border:1px solid #cbd5e0;padding:10px 8px;'
            f'text-align:center;font-weight:700;color:#718096;font-size:12px;">{num}.</td>'
            f'<td style="border:1px solid #cbd5e0;padding:10px 14px;font-size:13px;'
            f'line-height:1.55;color:#2d3748;">{_html.escape(text)}</td>'
            f'{cells}'
            f'</tr>'
        )

    # Metryczka – forma studiów
    form_st = v('forma_studiow', 'stacjonarne')
    radio_stac = 'checked' if form_st == 'stacjonarne' else ''
    radio_niest = 'checked' if form_st == 'niestacjonarne' else ''

    content = f"""
    <div class="page-header">
      <div class="page-header-inner">
        <div class="page-title-group">
          <h1>Kwestionariusz ankiety</h1>
          <div class="breadcrumb">
            <a href="{url_for('auth.dashboard')}">Dashboard</a>
            <span>›</span>
            <a href="{url_for('student.index')}">Panel studenta</a>
            <span>›</span>
            <span>Załącznik nr 5</span>
          </div>
        </div>
        <span class="adm-badge {status_cls}">
          <span class="adm-badge-dot"></span>{status_label}
        </span>
      </div>
    </div>

    <div class="student-container">
      {_flash_html()}

      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;
                  padding:32px 36px;margin-top:20px;max-width:1000px;">

        <div style="text-align:right;font-size:11px;color:#718096;margin-bottom:8px;">
          Załącznik nr 5
        </div>

        <div style="text-align:center;margin-bottom:24px;">
          <div style="font-weight:700;font-size:14px;line-height:1.6;color:#1a202c;
                      max-width:640px;margin:0 auto;">
            Kwestionariusz ankiety oceniający przebieg praktyk zawodowych<br>
            realizowanych w ramach programów studiów<br>
            w Instytucie Informatyki Stosowanej im. K. Brzeskiego w Elblągu
          </div>
        </div>

        <p style="font-size:13px;color:#4a5568;line-height:1.65;margin-bottom:10px;
                  text-align:justify;">
          W trosce o stałe podnoszenie jakości przebiegu praktyk zawodowych zwracamy się do
          Pani/Pana z prośbą o wypełnienie anonimowej ankiety dotyczącej praktyk zawodowych,
          w której należy określić w jakim stopniu zgadza się Pan/Pani z poniższymi stwierdzeniami.
        </p>
        <p style="font-size:13px;color:#4a5568;font-style:italic;margin-bottom:20px;">
          Prosimy zaznaczyć przy każdym pytaniu X w wybranym polu odpowiedzi.
        </p>

        <form method="post" id="form5">

          <div style="overflow-x:auto;margin-bottom:28px;">
            <table style="width:100%;border-collapse:collapse;font-family:'IBM Plex Sans',sans-serif;">
              <thead>
                <tr>
                  <th style="width:32px;border:1px solid #cbd5e0;padding:8px;
                             background:#f7fafc;"></th>
                  <th style="border:1px solid #cbd5e0;padding:8px 14px;
                             background:#f7fafc;font-size:12px;color:#718096;text-align:left;">
                    Stwierdzenie
                  </th>
                  {scale_headers}
                </tr>
              </thead>
              <tbody>
                {rows_html}
              </tbody>
            </table>
          </div>

          <div style="margin-bottom:28px;">
            <label style="font-weight:600;font-size:13px;color:#2d3748;display:block;margin-bottom:8px;">
              Dodatkowe uwagi dotyczące przebiegu praktyki zawodowej
            </label>
            <textarea name="uwagi_dodatkowe" rows="4"
                      style="width:100%;border:1px solid #cbd5e0;border-radius:6px;
                             padding:10px 14px;font-size:13px;resize:vertical;"
                      placeholder="Wpisz swoje uwagi (opcjonalnie)..."
            >{_html.escape(v('uwagi_dodatkowe'))}</textarea>
          </div>

          <div style="border:1px solid #cbd5e0;border-radius:8px;overflow:hidden;margin-bottom:28px;">
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
              <thead>
                <tr>
                  <th colspan="2" style="background:#f0f4f8;padding:10px 16px;font-size:13px;
                                         font-weight:700;color:#2d3748;text-align:center;
                                         border-bottom:1px solid #cbd5e0;">
                    Metryczka
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style="padding:10px 16px;font-weight:600;color:#4a5568;
                             border-bottom:1px solid #e2e8f0;width:240px;">Rok akademicki</td>
                  <td style="padding:8px 12px;border-bottom:1px solid #e2e8f0;">
                    <input type="text" name="rok_akademicki"
                           value="{_html.escape(v('rok_akademicki'))}"
                           placeholder="np. 2025/2026"
                           style="border:1px solid #cbd5e0;border-radius:4px;
                                  padding:6px 10px;font-size:13px;width:200px;">
                  </td>
                </tr>
                <tr>
                  <td style="padding:10px 16px;font-weight:600;color:#4a5568;
                             border-bottom:1px solid #e2e8f0;">Kierunek studiów</td>
                  <td style="padding:10px 16px;border-bottom:1px solid #e2e8f0;
                             font-weight:500;color:#2d3748;">Informatyka</td>
                </tr>
                <tr>
                  <td style="padding:10px 16px;font-weight:600;color:#4a5568;
                             border-bottom:1px solid #e2e8f0;">Forma studiów</td>
                  <td style="padding:8px 12px;border-bottom:1px solid #e2e8f0;">
                    <label style="display:inline-flex;align-items:center;gap:6px;
                                  font-size:13px;cursor:pointer;margin-right:20px;">
                      <input type="radio" name="forma_studiow" value="stacjonarne" {radio_stac}
                             style="accent-color:#3b5bdb;width:15px;height:15px;">
                      stacjonarne
                    </label>
                    <label style="display:inline-flex;align-items:center;gap:6px;
                                  font-size:13px;cursor:pointer;">
                      <input type="radio" name="forma_studiow" value="niestacjonarne" {radio_niest}
                             style="accent-color:#3b5bdb;width:15px;height:15px;">
                      niestacjonarne
                    </label>
                    <div style="font-size:11px;color:#a0aec0;margin-top:2px;">
                      *niewłaściwe skreślić
                    </div>
                  </td>
                </tr>
                <tr>
                  <td style="padding:10px 16px;font-weight:600;color:#4a5568;
                             border-bottom:1px solid #e2e8f0;">Semestr studiów</td>
                  <td style="padding:8px 12px;border-bottom:1px solid #e2e8f0;">
                    <input type="text" name="semestr"
                           value="{_html.escape(v('semestr'))}"
                           placeholder="np. VII"
                           style="border:1px solid #cbd5e0;border-radius:4px;
                                  padding:6px 10px;font-size:13px;width:120px;">
                  </td>
                </tr>
                <tr>
                  <td style="padding:10px 16px;font-weight:600;color:#4a5568;">
                    Liczba godzin zrealizowanej<br>praktyki zawodowej
                  </td>
                  <td style="padding:8px 12px;">
                    <input type="number" name="godziny_praktyk"
                           value="{v('godziny_praktyk', str(hours_worked))}"
                           placeholder="120" min="0"
                           style="border:1px solid #cbd5e0;border-radius:4px;
                                  padding:6px 10px;font-size:13px;width:120px;">
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div style="text-align:right;font-style:italic;font-weight:700;
                      font-size:14px;color:#2d3748;margin-bottom:24px;">
            Dziękujemy za udział w badaniu
          </div>

          <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;
                      border-top:1px solid #e2e8f0;padding-top:20px;">
            <button type="submit" name="action" value="save" class="btn btn-ghost">
              💾 Zapisz szkic
            </button>
            <button type="submit" name="action" value="submit" class="btn btn-primary"
                    onclick="return validateSurvey()">
              📤 Wyślij ankietę
            </button>
            <a href="{url_for('student.index')}" class="btn btn-ghost" style="margin-left:auto;">
              ← Powrót do panelu
            </a>
          </div>

        </form>
      </div>
    </div>

    <script>
    function validateSurvey() {{
      const total = {len(SURVEY_QUESTIONS)};
      let missing = [];
      for (let i = 1; i <= total; i++) {{
        const key = 'q' + String(i).padStart(2, '0');
        const checked = document.querySelector('[name="' + key + '"]:checked');
        if (!checked) missing.push(i);
      }}
      if (missing.length > 0) {{
        alert('Proszę odpowiedzieć na pytania: ' + missing.join(', '));
        return false;
      }}
      return confirm('Wysłać ankietę? Po wysłaniu nie będzie można jej edytować.');
    }}
    </script>
    """
    return _render(content)


# ---------------------------------------------------------------------------
# Załącznik nr 7 – Sprawozdanie z praktyki zawodowej – DB id=11
# ---------------------------------------------------------------------------

def _attachment_7_sprawozdanie(_attachment, db_id: int = 11,
                               label: str = "Załącznik nr 7",
                               subtitle: str = ""):
    doc = DocumentSubmission.query.filter_by(
        user_id=current_user.id,
        attachment_id=db_id
    ).order_by(DocumentSubmission.id.desc()).first()

    saved = doc.data if (doc and doc.data) else {}
    status = doc.status if doc else "draft"
    status_label, status_cls = STATUS_LABELS.get(status, ("Brak", "badge-draft"))

    def v(key, default=""):
        val = saved.get(key, default)
        return val if val is not None else default

    if request.method == 'POST':
        action = request.form.get('action', 'save')
        data = {
            "student_name":    request.form.get('student_name', '').strip(),
            "album_number":    request.form.get('album_number', '').strip(),
            "specialization":  request.form.get('specialization', '').strip(),
            "study_type":      request.form.get('study_type', 'stacjonarne'),
            "rok_akademicki":  request.form.get('rok_akademicki', '').strip(),
            "place_description": request.form.get('place_description', '').strip(),
            "work_description":  request.form.get('work_description', '').strip(),
            "skills_acquired":   request.form.get('skills_acquired', '').strip(),
        }

        if not doc:
            internship = Internship.query.filter_by(student_id=current_user.id).first()
            if not internship:
                flash("Nie masz przypisanej praktyki. Skontaktuj się z dziekanatem.", "error")
                return redirect(url_for('student.index'))
            doc = DocumentSubmission(
                user_id=current_user.id,
                attachment_id=db_id,
                internship_id=internship.id,
                status="draft"
            )
            db.session.add(doc)

        doc.data = data
        if action == 'submit':
            doc.status = "submitted"
            flash("Sprawozdanie wysłane do opiekuna.", "success")
        else:
            doc.status = "draft"
            flash("Sprawozdanie zapisane jako szkic.", "info")
        db.session.commit()
        return redirect(url_for('student.index'))

    import html as _html

    internship = Internship.query.filter_by(student_id=current_user.id).first()
    company_name = internship.company_name if internship else ""
    date_range = ""
    if internship:
        date_range = (f"{internship.start_date.strftime('%d.%m.%Y')} – "
                      f"{internship.end_date.strftime('%d.%m.%Y')}")

    full_name = getattr(current_user, 'full_name', '') or current_user.email

    study_opts = ""
    for val, label in [("stacjonarne", "inżynierskie stacjonarne"),
                       ("niestacjonarne", "inżynierskie niestacjonarne")]:
        sel = "selected" if v("study_type", "stacjonarne") == val else ""
        study_opts += f'<option value="{val}" {sel}>{label}</option>'

    rejection_html = ""
    if doc and doc.status == "rejected" and doc.comments:
        rejection_html = (
            '<div class="alert" style="background:#fff3f3;border:1px solid #fed7d7;'
            'border-left:4px solid #e53e3e;margin-bottom:20px;padding:14px 18px;border-radius:6px;">'
            '<strong style="color:#c53030;display:block;margin-bottom:6px;">❌ Dokument odrzucony – uwagi opiekuna:</strong>'
            f'<p style="color:#742a2a;font-size:13px;white-space:pre-wrap;margin:0;">{_html.escape(doc.comments)}</p>'
            '</div>'
        )

    content = f"""
    <div class="page-header">
      <div class="page-header-inner">
        <div class="page-title-group">
          <h1>Sprawozdanie z praktyki zawodowej</h1>
          <div class="breadcrumb">
            <a href="{url_for('auth.dashboard')}">Dashboard</a>
            <span>›</span>
            <a href="{url_for('student.index')}">Panel studenta</a>
            <span>›</span>
            <span>{label}</span>
          </div>
        </div>
        <span class="adm-badge {status_cls}">
          <span class="adm-badge-dot"></span>{status_label}
        </span>
      </div>
    </div>

    <div class="student-container">
      {_flash_html()}

      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;
                  padding:32px 36px;margin-top:20px;max-width:860px;">

        <div style="text-align:right;font-size:11px;color:#718096;margin-bottom:4px;">
          {label}{f' – {subtitle}' if subtitle else ''}
        </div>

        <div style="font-size:12px;margin-bottom:20px;line-height:1.5;">
          <div style="font-weight:700;font-size:13px;">Akademia Nauk Stosowanych w Elblągu</div>
          <div style="font-style:italic;color:#4a5568;">
            Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego
          </div>
        </div>

        <form method="post" id="form7">

          {rejection_html}

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px;">
            <div class="form-group">
              <label>Student / ka <span class="required">*</span></label>
              <input type="text" name="student_name"
                     value="{_html.escape(v('student_name', full_name))}"
                     placeholder="Imię i nazwisko">
            </div>
            <div class="form-group">
              <label>Nr albumu</label>
              <input type="text" name="album_number"
                     value="{_html.escape(v('album_number'))}"
                     placeholder="np. 12345">
            </div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:20px;">
            <div class="form-group">
              <label>Kierunek</label>
              <input type="text" value="Informatyka" readonly
                     style="background:#f7fafc;color:#4a5568;">
            </div>
            <div class="form-group">
              <label>Specjalność</label>
              <input type="text" name="specialization"
                     value="{_html.escape(v('specialization'))}"
                     placeholder="np. Systemy informatyczne">
            </div>
            <div class="form-group">
              <label>Studia</label>
              <select name="study_type">{study_opts}</select>
            </div>
          </div>

          <div style="margin-bottom:20px;">
            <div class="form-group">
              <label>Rok akademicki</label>
              <input type="text" name="rok_akademicki"
                     value="{_html.escape(v('rok_akademicki'))}"
                     placeholder="np. 2025/2026" style="max-width:200px;">
            </div>
          </div>

          <div style="background:#f7fafc;border:1px solid #e2e8f0;border-radius:6px;
                      padding:10px 16px;margin-bottom:24px;font-size:13px;color:#4a5568;">
            <strong>Praktyka:</strong> {_html.escape(company_name)}
            {f'&nbsp;&nbsp;({_html.escape(date_range)})' if date_range else ''}
          </div>

          <div style="text-align:center;margin-bottom:24px;">
            <div style="font-weight:700;font-size:14px;text-transform:uppercase;
                        letter-spacing:.6px;color:#1a202c;">
              Sprawozdanie studenta z praktyki zawodowej
              {f'<div style="font-size:12px;font-weight:400;text-transform:none;margin-top:2px;color:#6b7280;">({subtitle})</div>' if subtitle else ''}
            </div>
          </div>

          <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:6px;
                      padding:10px 16px;margin-bottom:20px;font-size:12.5px;color:#92400e;">
            <strong>Wskazówka:</strong> Każda sekcja – maksymalnie <strong>3 zdania</strong>
            (limit: 500 znaków). Pisz konkretnie i syntetycznie.
          </div>

          <div style="margin-bottom:20px;">
            <div style="font-weight:700;font-size:13px;text-transform:uppercase;
                        letter-spacing:.4px;color:#2d3748;margin-bottom:4px;">
              I.&nbsp;&nbsp;Charakterystyka miejsca odbywania praktyki
            </div>
            <div style="font-style:italic;font-size:12px;color:#718096;margin-bottom:6px;">
              (Krótki opis instytucji – max. 3 zdania)
            </div>
            <div style="font-size:12px;color:#3b5bdb;background:#eff3ff;border-radius:4px;
                        padding:6px 10px;margin-bottom:8px;">
              💡 Przykład: <em>„Praktykę odbywałem/am w firmie XYZ Sp. z o.o., specjalizującej się
              w tworzeniu oprogramowania dla sektora finansowego. Firma zatrudnia ok. 80 pracowników
              i działa na rynku od 2010 roku. Siedziba firmy znajduje się w Elblągu."</em>
            </div>
            <textarea name="place_description" id="place_desc" rows="4"
                      style="width:100%;border:1px solid #cbd5e0;border-radius:6px;
                             padding:10px 14px;font-size:13px;resize:vertical;
                             font-family:'IBM Plex Sans',sans-serif;"
                      placeholder="Np. Praktykę odbywałem/am w firmie [nazwa], specjalizującej się w [branża]. Firma zatrudnia [liczba] pracowników i działa od [rok]. Siedziba mieści się w [miejscowość]."
                      maxlength="500">{_html.escape(v('place_description'))}</textarea>
            <div id="place_count" style="font-size:11px;color:#a0aec0;text-align:right;margin-top:3px;"></div>
          </div>

          <div style="margin-bottom:20px;">
            <div style="font-weight:700;font-size:13px;text-transform:uppercase;
                        letter-spacing:.4px;color:#2d3748;margin-bottom:4px;">
              II.&nbsp;&nbsp;Opis i analiza wykonywanych prac
            </div>
            <div style="font-style:italic;font-size:12px;color:#718096;margin-bottom:6px;">
              (Najważniejsze zadania – max. 3 zdania)
            </div>
            <div style="font-size:12px;color:#3b5bdb;background:#eff3ff;border-radius:4px;
                        padding:6px 10px;margin-bottom:8px;">
              💡 Przykład: <em>„W trakcie praktyki zajmowałem/am się tworzeniem aplikacji webowej
              w technologii React i Node.js. Uczestniczyłem/am w code review i spotkaniach
              scrumowych. Samodzielnie zaimplementowałem/am moduł autoryzacji użytkowników."</em>
            </div>
            <textarea name="work_description" id="work_desc" rows="4"
                      style="width:100%;border:1px solid #cbd5e0;border-radius:6px;
                             padding:10px 14px;font-size:13px;resize:vertical;
                             font-family:'IBM Plex Sans',sans-serif;"
                      placeholder="Np. W trakcie praktyki zajmowałem/am się [zadania]. Uczestniczyłem/am w [aktywności]. Samodzielnie wykonałem/am [konkretne zadanie]."
                      maxlength="500">{_html.escape(v('work_description'))}</textarea>
            <div id="work_count" style="font-size:11px;color:#a0aec0;text-align:right;margin-top:3px;"></div>
          </div>

          <div style="margin-bottom:28px;">
            <div style="font-weight:700;font-size:13px;text-transform:uppercase;
                        letter-spacing:.4px;color:#2d3748;margin-bottom:4px;">
              III.&nbsp;&nbsp;Wiedza i umiejętności uzyskane w trakcie praktyki
            </div>
            <div style="font-style:italic;font-size:12px;color:#718096;margin-bottom:6px;">
              (Samoocena efektów uczenia się – max. 3 zdania; wypisz efekty wg Zał. 4)
            </div>
            <div style="font-size:12px;color:#3b5bdb;background:#eff3ff;border-radius:4px;
                        padding:6px 10px;margin-bottom:8px;">
              💡 Przykład: <em>„Nabyłem/am praktyczną znajomość technologii stosowanych
              w branży IT (efekt 01, 02 – wpisz w dzienniku: poz. 3, 5, 12). Rozwinąłem/am
              umiejętność pracy w zespole i stosowania metodyk zwinnych (efekt 10 – poz. 1-20).
              Samodzielnie rozwiązałem/am problem techniczny z zakresu bezpieczeństwa (efekt 08 – poz. 8)."</em>
            </div>
            <textarea name="skills_acquired" id="skills_acq" rows="4"
                      style="width:100%;border:1px solid #cbd5e0;border-radius:6px;
                             padding:10px 14px;font-size:13px;resize:vertical;
                             font-family:'IBM Plex Sans',sans-serif;"
                      placeholder="Np. Nabyłem/am [kompetencje] (efekt 01, 02 – dziennik poz. X). Rozwinąłem/am [umiejętności] (efekt 10 – poz. Y). Samodzielnie rozwiązałem/am [problem] (efekt 08 – poz. Z)."
                      maxlength="500">{_html.escape(v('skills_acquired'))}</textarea>
            <div id="skills_count" style="font-size:11px;color:#a0aec0;text-align:right;margin-top:3px;"></div>
          </div>

          <div style="text-align:right;margin-bottom:28px;">
            <div style="display:inline-block;text-align:center;width:260px;">
              <div style="border-top:1px solid #4a5568;padding-top:6px;font-size:12px;
                          color:#4a5568;">
                data i podpis studenta
              </div>
            </div>
          </div>

          <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;
                      border-top:1px solid #e2e8f0;padding-top:20px;">
            <button type="submit" name="action" value="save" class="btn btn-ghost">
              💾 Zapisz szkic
            </button>
            <button type="submit" name="action" value="submit" class="btn btn-primary"
                    onclick="return validateSprawozdanie()">
              📤 Wyślij do opiekuna
            </button>
            <a href="{url_for('student.index')}" class="btn btn-ghost" style="margin-left:auto;">
              ← Powrót do panelu
            </a>
          </div>

        </form>
      </div>
    </div>

    <script>
    function charCount(id, countId, max) {{
      const ta = document.getElementById(id);
      const ct = document.getElementById(countId);
      if (!ta || !ct) return;
      function upd() {{
        const n = ta.value.length;
        ct.textContent = n + ' / ' + max + ' znaków';
        ct.style.color = n > max ? '#e53e3e' : n > max * .85 ? '#d97706' : '#a0aec0';
      }}
      ta.addEventListener('input', upd); upd();
    }}
    charCount('place_desc',  'place_count',  500);
    charCount('work_desc',   'work_count',   500);
    charCount('skills_acq',  'skills_count', 500);

    function countSentences(text) {{
      return (text.match(/[.!?]+( |$)/g) || []).length;
    }}

    function validateSprawozdanie() {{
      const sections = [
        {{id:'place_desc', name:'I. Charakterystyka miejsca'}},
        {{id:'work_desc',  name:'II. Opis i analiza prac'}},
        {{id:'skills_acq', name:'III. Wiedza i umiejętności'}},
      ];
      for (const s of sections) {{
        const el = document.getElementById(s.id);
        if (!el) continue;
        const txt = el.value.trim();
        if (txt.length < 20) {{
          alert('Sekcja „' + s.name + '" jest za krótka (min. 20 znaków).');
          el.focus(); return false;
        }}
        if (txt.length > 500) {{
          alert('Sekcja „' + s.name + '" przekracza 500 znaków.');
          el.focus(); return false;
        }}
        const sc = countSentences(txt);
        if (sc > 3) {{
          alert('Sekcja „' + s.name + '" ma ' + sc + ' zdań. Proszę skrócić do max. 3 zdań.');
          el.focus(); return false;
        }}
      }}
      return confirm('Wysłać sprawozdanie do opiekuna?');
    }}
    </script>
    """
    return _render(content)


# ---------------------------------------------------------------------------
# Rejestracja fontów z polskimi znakami (raz przy pierwszym użyciu)
# ---------------------------------------------------------------------------

import os as _os

def _setup_fonts():
    """Rejestruje Arial TTF (obsługuje polskie znaki) w reportlab."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    fonts = {
        'Arial':      r'C:\Windows\Fonts\arial.ttf',
        'Arial-Bold': r'C:\Windows\Fonts\arialbd.ttf',
    }
    for name, path in fonts.items():
        try:
            if _os.path.exists(path):
                pdfmetrics.registerFont(TTFont(name, path))
        except Exception:
            pass  # już zarejestrowany


_setup_fonts()

_FONT       = 'Arial'
_FONT_BOLD  = 'Arial-Bold'


# ---------------------------------------------------------------------------
# Generowanie PDF – Załącznik nr 3
# ---------------------------------------------------------------------------

def _generate_attachment3_pdf(data: dict):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    m = 20 * mm

    def line(y, x1, x2):
        c.line(x1, y, x2, y)

    y = h - m
    c.setFont(_FONT_BOLD, 12)
    c.drawString(m, y, "Akademia Nauk Stosowanych w Elblagu")
    y -= 6 * mm
    c.setFont(_FONT, 10)
    c.drawString(m, y, "Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego")
    y -= 14 * mm

    c.setFont(_FONT_BOLD, 13)
    title = "KARTA PRAKTYKI ZAWODOWEJ"
    c.drawString((w - c.stringWidth(title, _FONT_BOLD, 13)) / 2, y, title)
    y -= 12 * mm

    c.setFont(_FONT_BOLD, 11)
    c.drawString(m, y, "SKIEROWANIE NA PRAKTYKĘ")
    y -= 8 * mm
    c.setFont(_FONT, 10)
    c.drawString(m, y,
        f"Na podstawie porozumienia nr {data.get('agreement_number','........')} "
        f"z dnia {data.get('agreement_date','............')} r., "
        "kieruję niżej wymienionego studenta")
    y -= 5 * mm
    c.drawString(m, y, "na praktykę zawodową do zakładu pracy:")
    y -= 8 * mm
    c.setFont(_FONT_BOLD, 10)
    c.drawString(m, y, data.get('company_name', ''))
    line(y - 2, m, w - m)
    y -= 10 * mm

    items = [
        ("1.  Imię i nazwisko:",       data.get('student_name', '')),
        ("2.  Numer albumu:",                data.get('album_number', '')),
        ("3.  Studia:",                      data.get('study_type', 'stacjonarne')
                                              .replace('stacjonarne', 'inżynierskie stacjonarne')
                                              .replace('niestacjonarne', 'inżynierskie niestacjonarne')),
        ("4.  Kierunek:",                    "informatyka"),
        ("    specjalność:",       data.get('specialization', '')),
        ("5.  Czas trwania praktyki:",       data.get('internship_duration', '6 miesięcy (120 dni roboczych)')),
        ("6.  Uczelniany opiekun:",          data.get('university_supervisor', '')),
        ("7.  Termin praktyki od",           f"{data.get('date_from','')} do {data.get('date_to','')} {data.get('internship_year','')} r."),
    ]
    for label, val in items:
        c.setFont(_FONT, 10)
        c.drawString(m, y, label)
        c.setFont(_FONT_BOLD, 10)
        c.drawString(m + 65 * mm, y, val)
        y -= 6.5 * mm

    y -= 8 * mm
    c.setFont(_FONT, 10)
    c.drawString(m, y, "Zakładowy opiekun praktyki:")
    c.setFont(_FONT_BOLD, 10)
    sup = f"{data.get('company_supervisor','')}  –  {data.get('supervisor_role','')}"
    c.drawString(m + 60 * mm, y, sup)
    y -= 8 * mm

    if data.get('bhp_confirmed') == '1':
        c.setFont(_FONT_BOLD, 10)
        c.drawString(m, y, "Potwierdzono odbycie szkolenia BHP")
        y -= 6 * mm

    c.setFont(_FONT, 8)
    c.setFillColorRGB(.5, .5, .5)
    c.drawString(m, m, "Strona 1 z 1  |  System Praktyk ANS Elbląg  |  Wygenerowano automatycznie")
    c.showPage()
    c.save()
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                     download_name='Zalacznik_3_Karta_Praktyki.pdf')


def _generate_pdf(attachment, text: str):
    """Generyczny PDF z polskimi znakami (Arial TTF)."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    y = height - margin
    c.setFont(_FONT_BOLD, 14)
    c.drawString(margin, y, attachment.name)
    y -= 12 * mm
    c.setFont(_FONT, 11)
    c.drawString(margin, y, f"Student: {getattr(current_user, 'full_name', '') or current_user.email}")
    y -= 8 * mm
    text_lines = []
    for paragraph in text.split('\n'):
        line_buf = ''
        for word in paragraph.split(' '):
            if c.stringWidth(line_buf + ' ' + word, _FONT, 11) < (width - 2 * margin):
                line_buf = (line_buf + ' ' + word).strip()
            else:
                text_lines.append(line_buf)
                line_buf = word
        if line_buf:
            text_lines.append(line_buf)
        text_lines.append('')
    for ln in text_lines:
        if y < margin + 20:
            c.showPage()
            y = height - margin
            c.setFont(_FONT, 11)
        c.drawString(margin, y, ln)
        y -= 6 * mm
    c.showPage()
    c.save()
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                     download_name=f"form_{attachment.id}.pdf")


# ---------------------------------------------------------------------------
# Pobierz plik zgłoszenia
# ---------------------------------------------------------------------------

@student_bp.route('/submission/<int:submission_id>/download')
@login_required
def download_submission(submission_id):
    sub = DocumentSubmission.query.get_or_404(submission_id)
    allowed_roles = ('opiekun', 'administrator', 'dziekanat', 'sekretariat', 'dyrekcja')
    if current_user.id != sub.user_id and current_user.role not in allowed_roles:
        abort(403)
    if not sub.file_path:
        abort(404)
    try:
        return send_file(sub.file_path, as_attachment=True)
    except Exception:
        abort(404)


# ---------------------------------------------------------------------------
# Widoki z render_template (szablony Jinja2)
# ---------------------------------------------------------------------------

@student_bp.route('/dashboard')
@student_required
def dashboard():
    internships = Internship.query.filter_by(student_id=current_user.id).all()
    return render_template('student/dashboard.html',
                           user=current_user,
                           internships=internships,
                           total_internships=len(internships))


@student_bp.route('/internship/<int:internship_id>')
@student_required
@check_resource_access("internship_id")
def view_internship(internship_id):
    internship = Internship.query.get(internship_id)
    documents = DocumentSubmission.query.filter_by(internship_id=internship_id).all()
    documents_by_status = {
        'draft': [], 'submitted': [], 'pending_review': [],
        'approved': [], 'rejected': []
    }
    for doc in documents:
        if doc.status in documents_by_status:
            documents_by_status[doc.status].append(doc)
    return render_template('student/view_internship.html',
                           internship=internship,
                           documents_by_status=documents_by_status,
                           completion_percent=internship.completion_percent,
                           total_hours_worked=internship.total_hours_worked)


@student_bp.route('/internship/<int:internship_id>/attachment/<int:attachment_id>/edit',
                  methods=['GET', 'POST'])
@student_required
@check_resource_access("internship_id")
def edit_attachment(internship_id, attachment_id):
    internship = Internship.query.get(internship_id)
    attachment = Attachment.query.get(attachment_id)

    if not attachment:
        flash("Załącznik nie znaleziony", "error")
        return redirect(url_for('student.view_internship', internship_id=internship_id))

    if attachment.audience not in ["student", "all"]:
        flash("Nie masz dostępu do tego załącznika", "error")
        return redirect(url_for('student.view_internship', internship_id=internship_id))

    doc = DocumentSubmission.query.filter_by(
        user_id=current_user.id,
        internship_id=internship_id,
        attachment_id=attachment_id
    ).first()

    form = None
    template = None
    student_index = ''

    if attachment_id == 1:
        form = Attachment1Form()
        template = 'student/attachment_1_form.html'
        if request.method == 'GET' and doc and doc.data:
            form.student_first_name.data = doc.data.get('student_first_name', '')
        if form.validate_on_submit():
            if not doc:
                doc = DocumentSubmission(
                    user_id=current_user.id,
                    internship_id=internship_id,
                    attachment_id=attachment_id,
                    status="draft"
                )
                db.session.add(doc)
            doc.data = form.to_dict()
            if 'submit_and_send' in request.form:
                doc.status = "submitted"
                flash("Formularz wysłany do opiekuna", "success")
            else:
                doc.status = "draft"
                flash("Formularz zapisany (draft)", "info")
            db.session.commit()
            return redirect(url_for('student.view_internship', internship_id=internship_id))

    elif attachment_id == 10:
        # Przekieruj do widoku dziennika z diary_routes.py
        return redirect(url_for('student.diary_view', internship_id=internship_id))

    elif attachment_id == 11:
        form = ReportForm()
        template = 'student/attachment_7_report.html'
        if request.method == 'GET' and doc and doc.data:
            form.place_description.data = doc.data.get('place_description', '')
            form.work_description.data = doc.data.get('work_description', '')
            form.skills_acquired.data = doc.data.get('skills_acquired', '')
        # Pobierz nr albumu z załącznika 1 (Porozumienie) jeśli dostępny
        att1_doc = DocumentSubmission.query.filter_by(
            internship_id=internship_id, attachment_id=1
        ).first()
        student_index = (att1_doc.data or {}).get('index_number', '') if att1_doc else ''
        if form.validate_on_submit():
            if not doc:
                doc = DocumentSubmission(
                    user_id=current_user.id,
                    internship_id=internship_id,
                    attachment_id=attachment_id,
                    status="draft"
                )
                db.session.add(doc)
            doc.data = form.to_dict()
            if 'submit' in request.form:
                doc.status = "submitted"
                flash("Sprawozdanie wysłane", "success")
            else:
                doc.status = "draft"
                flash("Sprawozdanie zapisane (draft)", "info")
            db.session.commit()
            return redirect(url_for('student.view_internship', internship_id=internship_id))

    else:
        flash("Ten załącznik nie jest jeszcze obsługiwany", "warning")
        return redirect(url_for('student.view_internship', internship_id=internship_id))

    return render_template(template, internship=internship,
                           attachment=attachment, form=form, document=doc,
                           student_index=student_index)


@student_bp.route('/internship/<int:internship_id>/learning-outcome/add', methods=['POST'])
@student_required
@check_resource_access("internship_id")
def add_learning_outcome(internship_id):
    form = LearningOutcomeForm()
    if form.validate_on_submit():
        outcome = LearningOutcome(
            internship_id=internship_id,
            outcome_text=form.outcome_text.data,
            evidence_source=form.evidence_source.data,
            status="planned"
        )
        db.session.add(outcome)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Efekt dodany', 'outcome': outcome.to_dict()})
    return jsonify({'success': False, 'errors': form.errors}), 400


@student_bp.route('/document/<int:document_id>/preview')
@student_required
def preview_document(document_id):
    document = DocumentSubmission.query.get(document_id)
    if not document or document.user_id != current_user.id:
        flash("Dokument nie znaleziony", "error")
        return redirect(url_for('student.dashboard'))
    return render_template('student/preview_pdf.html', document=document)


# ---------------------------------------------------------------------------
# Widok do druku / PDF – wszystkie dokumenty
# ---------------------------------------------------------------------------

# Mapowanie kluczy JSON na czytelne polskie etykiety
_FIELD_LABELS = {
    'agreement_number': 'Numer porozumienia', 'agreement_date': 'Data porozumienia',
    'company_name': 'Nazwa zakładu pracy', 'company_address': 'Adres',
    'company_phone': 'Telefon', 'company_email': 'E-mail firmy',
    'student_name': 'Student', 'album_number': 'Numer albumu',
    'study_type': 'Forma studiów', 'specialization': 'Specjalność',
    'internship_duration': 'Czas trwania', 'university_supervisor': 'Opiekun uczelniany',
    'date_from': 'Data od', 'date_to': 'Data do', 'internship_year': 'Rok',
    'company_supervisor': 'Opiekun zakładowy', 'supervisor_role': 'Stanowisko opiekuna',
    'bhp_confirmed': 'Szkolenie BHP',
    'place_description': 'I. Charakterystyka miejsca praktyki',
    'work_description': 'II. Opis i analiza wykonywanych prac',
    'skills_acquired': 'III. Wiedza i umiejętności',
    'rok_akademicki': 'Rok akademicki', 'kierunek': 'Kierunek', 'semestr': 'Semestr',
    'forma_studiow': 'Forma studiów', 'godziny_praktyk': 'Liczba godzin',
    'uwagi_dodatkowe': 'Dodatkowe uwagi', 'ocena_ogolna': 'Ocena ogólna', 'uwagi': 'Uwagi',
    'hours_total': 'Liczba godzin', 'student_index': 'Nr albumu',
}
# Klucze do ukrycia w widoku (wewnętrzne / techniczne)
_HIDE_KEYS = {'type', 'submitted_at', 'notes'}


@student_bp.route('/document/<int:doc_id>/pdf')
@login_required
def document_pdf_view(doc_id):
    """Widok dokumentu gotowy do druku / zapisania jako PDF przez przeglądarkę."""
    doc = DocumentSubmission.query.get_or_404(doc_id)

    # Kontrola dostępu
    allowed_roles = ('opiekun', 'dziekanat', 'sekretariat', 'dyrekcja', 'admin', 'administrator')
    if current_user.id != doc.user_id and current_user.role not in allowed_roles:
        abort(403)

    att = doc.attachment
    att_name = att.name if att else f'Dokument #{doc.id}'
    internship = doc.internship
    data = doc.data or {}

    import html as _h

    # Zbuduj wiersze tabeli z danych JSON
    rows_html = ''
    for key, val in data.items():
        if key in _HIDE_KEYS or key.startswith('outcome_') or key.startswith('q') or key.startswith('out_'):
            continue
        if not val:
            continue
        label = _FIELD_LABELS.get(key, key.replace('_', ' ').capitalize())
        val_str = _h.escape(str(val))
        if key == 'bhp_confirmed':
            val_str = 'Tak' if val == '1' else 'Nie'
        rows_html += f"""<tr>
          <td style="width:35%;padding:8px 12px;font-weight:600;color:#374151;
                     border:1px solid #e2e8f0;background:#f7fafc;font-size:12.5px;">
            {_h.escape(label)}
          </td>
          <td style="padding:8px 12px;border:1px solid #e2e8f0;font-size:13px;
                     color:#111827;white-space:pre-wrap;line-height:1.55;">
            {val_str}
          </td>
        </tr>"""

    # Sekcja efektów (dla Zał. 4)
    outcomes_html = ''
    outcome_rows = {k: v for k, v in data.items() if k.startswith('outcome_')}
    if outcome_rows:
        outcomes_html = '<h3 style="font-size:13px;font-weight:700;color:#1a2744;margin:16px 0 8px;">Efekty uczenia się</h3>'
        outcomes_html += '<table style="width:100%;border-collapse:collapse;">'
        for k, v in sorted(outcome_rows.items()):
            num = k.replace('outcome_', '')
            color = '#16a34a' if v == 'uzyskal' else '#dc2626'
            label = 'uzyskał/a' if v == 'uzyskal' else 'nie uzyskał/a'
            outcomes_html += f'<tr><td style="padding:5px 10px;border:1px solid #e2e8f0;font-size:12px;width:40px;text-align:center;font-weight:700;">{num}</td><td style="padding:5px 10px;border:1px solid #e2e8f0;font-size:12px;color:{color};font-weight:600;">{label}</td></tr>'
        outcomes_html += '</table>'

    # Sekcja ankiety (dla Zał. 5)
    survey_html = ''
    survey_rows = {k: v for k, v in data.items() if k.startswith('q') and len(k) == 3}
    scale_labels = {
        'zdecydowanie_tak': 'Zdecydowanie tak', 'raczej_tak': 'Raczej tak',
        'trudno_powiedziec': 'Trudno powiedzieć', 'raczej_nie': 'Raczej nie',
        'zdecydowanie_nie': 'Zdecydowanie nie',
    }
    if survey_rows:
        survey_html = '<h3 style="font-size:13px;font-weight:700;color:#1a2744;margin:16px 0 8px;">Odpowiedzi ankiety</h3>'
        survey_html += '<table style="width:100%;border-collapse:collapse;">'
        for k, v in sorted(survey_rows.items()):
            survey_html += f'<tr><td style="padding:5px 10px;border:1px solid #e2e8f0;font-size:12px;width:40px;font-weight:700;text-align:center;">{k[1:]}</td><td style="padding:5px 10px;border:1px solid #e2e8f0;font-size:12.5px;">{scale_labels.get(v, v)}</td></tr>'
        survey_html += '</table>'

    status_map = {
        'draft': 'Szkic', 'submitted': 'Wysłany', 'approved': 'Zatwierdzony',
        'rejected': 'Odrzucony', 'pending_review': 'W weryfikacji',
    }
    status_label = status_map.get(doc.status, doc.status)

    student_name = _h.escape(internship.student.full_name if internship else (current_user.full_name or current_user.email))
    company = _h.escape(internship.company_name if internship else '')
    created = doc.created_at.strftime('%d.%m.%Y') if doc.created_at else ''

    page = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<title>{_h.escape(att_name)} – PDF</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'IBM Plex Sans',sans-serif;background:#fff;color:#111827;font-size:13px;}}
  .no-print{{background:#1a2744;color:#fff;padding:10px 24px;display:flex;align-items:center;justify-content:space-between;gap:12px;}}
  .no-print button{{background:#3b5bdb;color:#fff;border:none;padding:8px 20px;border-radius:6px;font-size:13.5px;font-weight:600;cursor:pointer;font-family:inherit;}}
  .no-print button:hover{{background:#2f4ac0}}
  .no-print a{{color:rgba(255,255,255,.75);text-decoration:none;font-size:13px;}}
  .doc{{max-width:800px;margin:24px auto;padding:32px 36px;border:1px solid #e2e8f0;border-radius:8px;}}
  @media print{{
    .no-print{{display:none!important}}
    body{{background:#fff}}
    .doc{{margin:0;padding:20px;border:none;border-radius:0;max-width:100%;}}
    @page{{size:A4;margin:15mm 15mm 15mm 15mm}}
  }}
  .header-logo{{font-size:11.5px;color:#6b7280;margin-bottom:6px;}}
  .header-logo strong{{font-size:13px;color:#1a2744;display:block;}}
  .att-badge{{float:right;font-size:11px;color:#9ca3af;font-weight:600;letter-spacing:.3px;}}
  .doc-title{{font-size:16px;font-weight:700;color:#1a2744;text-align:center;text-transform:uppercase;letter-spacing:.5px;margin:20px 0 6px;}}
  .doc-meta{{text-align:center;font-size:12px;color:#6b7280;margin-bottom:16px;}}
  .status-badge{{display:inline-block;padding:2px 10px;border-radius:20px;font-size:11.5px;font-weight:600;margin-left:8px;}}
  .status-approved{{background:#f0fdf4;color:#16a34a;border:1px solid #bbf7d0;}}
  .status-submitted{{background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;}}
  .status-draft{{background:#f3f4f6;color:#6b7280;border:1px solid #e5e7eb;}}
  .status-rejected{{background:#fef2f2;color:#dc2626;border:1px solid #fecaca;}}
  .separator{{border:none;border-top:1px solid #e2e8f0;margin:16px 0;}}
  table{{width:100%;border-collapse:collapse;margin-bottom:8px;}}
  .sig-line{{margin-top:32px;display:flex;justify-content:space-between;}}
  .sig-block{{text-align:center;width:220px;}}
  .sig-block .line{{border-top:1px solid #374151;padding-top:5px;font-size:11.5px;color:#6b7280;}}
  .footer-note{{margin-top:24px;font-size:10.5px;color:#9ca3af;text-align:center;border-top:1px solid #f0f0f5;padding-top:10px;}}
</style>
</head>
<body>
<div class="no-print">
  <div>
    <span style="font-size:14px;font-weight:600;">📄 {_h.escape(att_name)}</span>
    <span style="font-size:12px;opacity:.7;margin-left:10px;">Podgląd do druku</span>
  </div>
  <div style="display:flex;gap:12px;align-items:center;">
    <a href="javascript:history.back()">← Wróć</a>
    <button onclick="window.print()">🖨️ Drukuj / Zapisz jako PDF</button>
  </div>
</div>

<div class="doc">
  <div class="att-badge">{_h.escape(att_name)}</div>
  <div class="header-logo">
    <strong>Akademia Nauk Stosowanych w Elblągu</strong>
    Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego
  </div>
  <hr class="separator">

  <div class="doc-title">{_h.escape(att_name)}</div>
  <div class="doc-meta">
    Student: <strong>{student_name}</strong>
    {f'&nbsp;·&nbsp; Firma: <strong>{company}</strong>' if company else ''}
    &nbsp;·&nbsp; Data: {created}
    &nbsp;·&nbsp; Status: <span class="status-badge status-{doc.status}">{status_label}</span>
  </div>
  <hr class="separator">

  {f'<table>{rows_html}</table>' if rows_html else '<p style="color:#9ca3af;font-style:italic;">Brak danych formularza.</p>'}
  {outcomes_html}
  {survey_html}

  <div class="sig-line">
    <div class="sig-block">
      <div style="min-height:36px;"></div>
      <div class="line">Data i podpis studenta</div>
    </div>
    <div class="sig-block">
      <div style="min-height:36px;"></div>
      <div class="line">Podpis opiekuna</div>
    </div>
  </div>

  {_pdf_dz_stamp(data)}

  <div class="footer-note">
    Wygenerowano: {doc.updated_at.strftime('%d.%m.%Y %H:%M') if doc.updated_at else created} &nbsp;·&nbsp;
    System Obsługi Praktyk – Akademia Nauk Stosowanych w Elblągu
  </div>
</div>
<script>
  // Automatyczny print jeśli w URL jest ?print=1
  if (new URLSearchParams(window.location.search).get('print') === '1') {{
    window.addEventListener('load', () => setTimeout(() => window.print(), 400));
  }}
</script>
</body></html>"""
    return page


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------

@student_bp.route('/api/internships')
@student_required
def api_get_internships():
    internships = Internship.query.filter_by(student_id=current_user.id).all()
    return jsonify({'success': True, 'data': [i.to_dict() for i in internships]})


@student_bp.route('/api/internship/<int:internship_id>')
@student_required
@check_resource_access("internship_id")
def api_get_internship(internship_id):
    internship = Internship.query.get(internship_id)
    return jsonify({
        'success': True,
        'data': internship.to_dict(),
        'documents_count': len(internship.documents),
        'diary_entries_count': len(internship.diary_entries),
    })