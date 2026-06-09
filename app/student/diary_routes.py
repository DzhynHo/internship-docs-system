"""
Trasy dziennika praktyki zawodowej – Załącznik nr 6.
Dołącz ten kod do app/student/routes.py (zastępuje istniejące
stub-funkcje diary lub dodaj jako nowe endpointy).
"""

from datetime import datetime, date, timedelta
import io

from flask import render_template, redirect, url_for, flash, request, send_file, jsonify, abort
from flask_login import current_user, login_required

# reportlab – pełny PDF dziennika
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm

from app import db
from app.models.internship import Internship, DiaryEntry
from app.auth.permissions import student_required, check_resource_access
from app.student import student_bp

# Rejestracja fontów z polskimi znakami
def _register_fonts():
    import os
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    _fonts = {
        'Arial':          r'C:\Windows\Fonts\arial.ttf',
        'Arial-Bold':     r'C:\Windows\Fonts\arialbd.ttf',
        'Arial-Italic':   r'C:\Windows\Fonts\ariali.ttf',
    }
    for name, path in _fonts.items():
        try:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont(name, path))
        except Exception:
            pass

_register_fonts()


# ---------------------------------------------------------------------------
# Pomocniczy stub – zastępuje WTForms gdy nie ma dedykowanego formularza
# ---------------------------------------------------------------------------
class _DiaryStub:
    """Minimalna klasa zastępująca WTForms Form, aby obsłużyć hidden_tag w szablonie."""
    def hidden_tag(self):
        return ''


# ---------------------------------------------------------------------------
# Widok główny dziennika (GET)
# ---------------------------------------------------------------------------
@student_bp.route('/internship/<int:internship_id>/diary')
@student_required
@check_resource_access("internship_id")
def diary_view(internship_id):
    internship = Internship.query.get_or_404(internship_id)
    entries = (DiaryEntry.query
               .filter_by(internship_id=internship_id)
               .order_by(DiaryEntry.date.asc())
               .all())

    # Oblicz godziny dla każdego wpisu (jeśli model nie ma trwałego pola `hours`)
    for e in entries:
        if not hasattr(e, 'hours') or e.hours is None:
            if e.start_time and e.end_time:
                start = datetime.combine(date.today(), e.start_time)
                end   = datetime.combine(date.today(), e.end_time)
                delta = (end - start).seconds / 3600
                e.hours = round(delta, 1)
            else:
                e.hours = 0

    return render_template(
        'student/attachment_6_diary.html',
        internship=internship,
        entries=entries,
        today=date.today().isoformat(),
        form=_DiaryStub()   # Poprawnie zainicjalizowana klasa pomocnicza
    )


# ---------------------------------------------------------------------------
# Dodaj wpis (POST) – wersja klasyczna (nie AJAX)
# ---------------------------------------------------------------------------
@student_bp.route('/internship/<int:internship_id>/diary/add-page', methods=['POST'])
@student_required
@check_resource_access("internship_id")
def add_diary_entry_page(internship_id):
    internship = Internship.query.get_or_404(internship_id)

    date_str   = request.form.get('date', '').strip()
    start_str  = request.form.get('start_time', '').strip()
    end_str    = request.form.get('end_time', '').strip()
    description = request.form.get('description', '').strip()
    outcomes   = request.form.get('learning_outcome_numbers', '').strip()

    # ── Walidacja ──
    errors = []
    if not date_str:
        errors.append("Data jest wymagana.")
    if not start_str:
        errors.append("Godzina rozpoczęcia jest wymagana.")
    if not end_str:
        errors.append("Godzina zakończenia jest wymagana.")
    if not description:
        errors.append("Opis wykonanych prac jest wymagany.")

    entry_date = None
    if date_str:
        try:
            entry_date = date.fromisoformat(date_str)
            if entry_date > date.today():
                errors.append("Nie można dodać wpisu z przyszłą datą.")
        except ValueError:
            errors.append("Nieprawidłowy format daty.")

    start_time = end_time = None
    if start_str and end_str:
        try:
            start_time = datetime.strptime(start_str, '%H:%M').time()
            end_time   = datetime.strptime(end_str, '%H:%M').time()
            if start_time >= end_time:
                errors.append("Godzina zakończenia musi być późniejsza niż godzina rozpoczęcia.")
        except ValueError:
            errors.append("Nieprawidłowy format godziny.")

    if errors:
        for err in errors:
            flash(err, 'error')
        return redirect(url_for('student.diary_view', internship_id=internship_id))

    # ── Zapisz wpis ──
    entry = DiaryEntry(
        internship_id=internship_id,
        date=entry_date,
        start_time=start_time,
        end_time=end_time,
        description=description,
    )

    entry.learning_outcome_numbers = outcomes or None

    db.session.add(entry)
    db.session.commit()

    flash('Wpis został dodany do dziennika.', 'success')
    return redirect(url_for('student.diary_view', internship_id=internship_id))


# ---------------------------------------------------------------------------
# Usuń wpis (DELETE / POST) – AJAX + fallback
# ---------------------------------------------------------------------------
@student_bp.route('/internship/<int:internship_id>/diary/<int:entry_id>/delete',
                 methods=['DELETE', 'POST'])
@student_required
@check_resource_access("internship_id")
def delete_diary_entry(internship_id, entry_id):
    entry = DiaryEntry.query.get_or_404(entry_id)

    if entry.internship_id != internship_id:
        if request.method == 'DELETE':
            return jsonify({'success': False, 'error': 'Wpis nie należy do tej praktyki.'}), 404
        flash('Wpis nie należy do tej praktyki.', 'error')
        return redirect(url_for('student.diary_view', internship_id=internship_id))

    if entry.date != date.today():
        if request.method == 'DELETE':
            return jsonify({'success': False, 'error': 'Możesz usunąć tylko wpis dodany dzisiaj.'}), 400
        flash('Możesz usunąć tylko wpis dodany dzisiaj.', 'error')
        return redirect(url_for('student.diary_view', internship_id=internship_id))

    db.session.delete(entry)
    db.session.commit()

    if request.method == 'DELETE':
        return jsonify({'success': True, 'message': 'Wpis usunięty.'})

    flash('Wpis został usunięty.', 'success')
    return redirect(url_for('student.diary_view', internship_id=internship_id))


# ---------------------------------------------------------------------------
# Generowanie PDF – pełny dziennik praktyki
# ---------------------------------------------------------------------------
@student_bp.route('/internship/<int:internship_id>/diary/pdf')
@student_required
@check_resource_access("internship_id")
def diary_pdf(internship_id):
    internship = Internship.query.get_or_404(internship_id)
    entries = (DiaryEntry.query
               .filter_by(internship_id=internship_id)
               .order_by(DiaryEntry.date.asc())
               .all())

    buffer = io.BytesIO()
    _build_diary_pdf(buffer, internship, entries)
    buffer.seek(0)

    student_name = (
        f"{getattr(current_user, 'first_name', '')} {getattr(current_user, 'last_name', '')}".strip()
        or current_user.email
    )
    safe_name = student_name.replace(' ', '_')
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Dziennik_Praktyki_{safe_name}.pdf"
    )


# ---------------------------------------------------------------------------
# PDF builder – ReportLab
# ---------------------------------------------------------------------------
def _build_diary_pdf(buffer, internship, entries):
    """Buduje PDF dziennika praktyki w orientacji poziomej (A4 landscape)."""
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=15 * mm,  bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    W, H = landscape(A4)
    content_w = W - 30 * mm  # 267 mm

    # ── Style ──
    title_style = ParagraphStyle(
        'Title', parent=styles['Normal'],
        fontSize=13, fontName='Arial-Bold',
        alignment=1, spaceAfter=2 * mm,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontSize=9, fontName='Arial',
        alignment=1, spaceAfter=1 * mm, textColor=colors.HexColor('#374151'),
    )
    header_meta_style = ParagraphStyle(
        'Meta', parent=styles['Normal'],
        fontSize=9, fontName='Arial',
        spaceAfter=1 * mm, textColor=colors.HexColor('#374151'),
    )
    cell_style = ParagraphStyle(
        'Cell', parent=styles['Normal'],
        fontSize=8, fontName='Arial',
        leading=11,
    )
    cell_center_style = ParagraphStyle(
        'CellCenter', parent=cell_style, alignment=1,
    )
    cell_mono_style = ParagraphStyle(
        'CellMono', parent=styles['Normal'],
        fontSize=8, fontName='Arial',
        leading=11, alignment=1,
    )
    instruct_style = ParagraphStyle(
        'Instruct', parent=styles['Normal'],
        fontSize=7.5, fontName='Arial-Italic',
        textColor=colors.HexColor('#6b7280'),
        leading=11,
    )

    # ── Dane studenta ──
    student_name = (
        f"{getattr(internship, 'student_name', '') or ''} "
        f"– nr albumu: {getattr(internship, 'album_number', '') or ''}"
    ).strip(" –")
    
    if not student_name.strip("–").strip():
        from flask_login import current_user as cu
        student_name = (
            f"{getattr(cu, 'first_name', '')} {getattr(cu, 'last_name', '')}".strip()
            or cu.email
        )

    company = getattr(internship, 'company_name', '') or '...................................'
    date_from = getattr(internship, 'start_date', None)
    date_to   = getattr(internship, 'end_date', None)
    date_from_str = date_from.strftime('%d.%m.%Y') if date_from else '..................'
    date_to_str   = date_to.strftime('%d.%m.%Y')   if date_to   else '..................'

    # ── Strona tytułowa (strona 1) ──
    story = []

    story.append(Paragraph("Akademia Nauk Stosowanych w Elblągu", subtitle_style))
    story.append(Paragraph(
        "Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego",
        subtitle_style
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("DZIENNIK PRAKTYKI ZAWODOWEJ", title_style))
    story.append(HRFlowable(width="100%", thickness=1,
                           color=colors.HexColor('#dde1ef'), spaceAfter=5 * mm))

    meta_rows = [
        [f"Student:  {student_name}",
         f"Nr albumu:  {getattr(internship, 'album_number', '') or '..........'}"],
        ["Kierunek:  informatyka",
         ""],
        [f"W zakresie:  {getattr(internship, 'specialization', '') or '....................'}",
         ""],
        ["Studia:  inżynierskie, stacjonarne",
         f"Rok ak.:  {date.today().year}/{date.today().year + 1}"],
        [f"Miejsce odbywania praktyki:  {company}", ""],
        [f"Data rozpoczęcia praktyki:  {date_from_str}",
         f"Data zakończenia praktyki:  {date_to_str}"],
    ]
    for row in meta_rows:
        story.append(Paragraph(row[0] + ("     " + row[1] if row[1] else ""), header_meta_style))

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("<b>WYKAZ ZAŁĄCZNIKÓW:</b>", header_meta_style))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("...................................................", header_meta_style))
    story.append(Paragraph("...................................................", header_meta_style))
    story.append(Spacer(1, 10 * mm))

    story.append(Paragraph(
        f"<i>Wygenerowano: {datetime.now().strftime('%d.%m.%Y %H:%M')}  |  "
        f"System Praktyk ANS Elbląg  |  Łącznie wpisów: {len(entries)}</i>",
        instruct_style
    ))

    # ── Strona z tabelą wpisów ──
    story.append(PageBreak())

    # Nagłówek powtarzający się na każdej stronie tabeli
    story.append(Paragraph(
        f"Akademia Nauk Stosowanych w Elblągu – Instytut Informatyki Stosowanej  "
        f"| <b>DZIENNIK PRAKTYKI ZAWODOWEJ</b>  |  {student_name}",
        subtitle_style
    ))
    story.append(Paragraph(f"Miejsce praktyki: {company}", subtitle_style))
    story.append(Spacer(1, 3 * mm))

    if not entries:
        story.append(Spacer(1, 10 * mm))
        story.append(Paragraph(
            "Brak wpisów w dzienniku.",
            ParagraphStyle('Empty', parent=styles['Normal'],
                           fontSize=10, alignment=1,
                           textColor=colors.HexColor('#6b7280'))
        ))
    else:
        col_w = [
            12 * mm,   # Dzień
            22 * mm,   # Data
            30 * mm,   # Godziny / h
            content_w - 12*mm - 22*mm - 30*mm - 28*mm - 28*mm,  # Opis
            28 * mm,   # Nr efektów
            28 * mm,   # Podpis
        ]

        header = [
            Paragraph("<b>Dzień</b>", cell_center_style),
            Paragraph("<b>Data</b>", cell_center_style),
            Paragraph("<b>Godziny</b>", cell_center_style),
            Paragraph("<b>Opis wykonanych prac</b>", cell_center_style),
            Paragraph("<b>Nr efektów<br/>uczenia się</b>", cell_center_style),
            Paragraph("<b>Podpis osoby<br/>nadzorującej</b>", cell_center_style),
        ]

        table_data = [header]

        instruct_text = (
            "Poz. 1. Wpis w pozycji „dzień\" oznacza kolejny dzień praktyki (jeden ze 120). "
            "Poz. 3. Wpisy powinny zawierać opis wykonywanych prac, z których powinno wynikać "
            "do nabycia jakich umiejętności prowadzą. Unikać skrótowych opisów. "
            "Poz. 4. Wpisać numer/numery efektów uczenia się. "
            "Każdą stronę dziennika potwierdza zakładowy opiekun praktyki (ZOPZ). "
            "(Powyższy tekst jest instrukcją, którą należy wykasować z dziennika.)"
        )
        instruct_para_style = ParagraphStyle(
            'Instruct2', parent=styles['Normal'],
            fontSize=7, fontName='Arial-Italic',
            textColor=colors.HexColor('#b91c1c'), leading=10,
        )
        table_data.append([
            Paragraph("", cell_center_style),
            Paragraph("", cell_center_style),
            Paragraph("", cell_center_style),
            Paragraph(instruct_text, instruct_para_style),
            Paragraph("", cell_center_style),
            Paragraph("", cell_center_style),
        ])

        for idx, e in enumerate(entries, start=1):
            date_str = e.date.strftime('%d.%m.%Y') if e.date else '–'

            if e.start_time and e.end_time:
                t_from = e.start_time.strftime('%H:%M')
                t_to   = e.end_time.strftime('%H:%M')
                start_dt = datetime.combine(date.today(), e.start_time)
                end_dt   = datetime.combine(date.today(), e.end_time)
                hrs = round((end_dt - start_dt).seconds / 3600, 1)
                hours_str = f"{t_from} – {t_to}\n({hrs}h)"
            else:
                hours_str = "–"

            outcomes = getattr(e, 'learning_outcome_numbers', '') or ''

            table_data.append([
                Paragraph(str(idx), cell_mono_style),
                Paragraph(date_str, cell_mono_style),
                Paragraph(hours_str.replace('\n', '<br/>'), cell_mono_style),
                Paragraph(e.description or '', cell_style),
                Paragraph(outcomes, cell_mono_style),
                Paragraph("", cell_style),
            ])

        tbl = Table(table_data, colWidths=col_w, repeatRows=1)

        navy  = colors.HexColor('#1a2744')
        light = colors.HexColor('#dde1ef')
        bg    = colors.HexColor('#f8f9fc')
        red_r = colors.HexColor('#fef2f2')

        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), navy),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTNAME',   (0, 0), (-1, 0), 'Arial-Bold'),
            ('FONTSIZE',   (0, 0), (-1, 0), 8),
            ('ALIGN',      (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN',     (0, 0), (-1, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 5),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('BACKGROUND', (0, 1), (-1, 1), red_r),
            *[('BACKGROUND', (0, i), (-1, i), bg)
              for i in range(2, len(table_data)) if i % 2 == 0],
            ('GRID',       (0, 0), (-1, -1), 0.5, light),
            ('BOX',        (0, 0), (-1, -1), 1, navy),
            ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING',  (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',   (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING',(0, 1), (-1, -1), 4),
        ]))

        story.append(tbl)

    doc.build(story)