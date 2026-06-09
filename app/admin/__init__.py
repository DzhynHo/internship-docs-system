from flask import Blueprint, render_template, send_file, request, redirect, url_for, flash
from flask_login import login_required
from app.auth.decorators import role_required
from app import db
from app.models.user import User
from app.models import DocumentSubmission
from app.forms import AdminCreateUserForm, AssignRoleForm
import io, zipfile

admin_bp = Blueprint("admin", __name__)

@admin_bp.route('/')
@login_required
@role_required('administrator', 'admin')
def index():
    return render_template('admin/index.html')

@admin_bp.route('/users')
@login_required
@role_required('administrator', 'admin')
def users_list():
    users = User.query.order_by(User.email).all()
    return render_template('admin/users_list.html', users=users)

def _doc_to_pdf_bytes(att_name, submission):
    """Generuje PDF z danych dokumentu bez zewnętrznych szablonów."""
    from weasyprint import HTML
    import html as _h

    data = submission.data or {}
    status_labels = {
        'draft': 'Szkic', 'submitted': 'Wysłany',
        'pending_review': 'W recenzji', 'approved': 'Zatwierdzony', 'rejected': 'Odrzucony'
    }
    status_pl = status_labels.get(submission.status, submission.status)
    created = submission.created_at.strftime('%d.%m.%Y %H:%M') if submission.created_at else '–'
    updated = submission.updated_at.strftime('%d.%m.%Y %H:%M') if submission.updated_at else '–'

    rows = ''
    for key, val in data.items():
        if key.startswith('_'):
            continue
        label = key.replace('_', ' ').capitalize()
        value = _h.escape(str(val)) if val is not None else '–'
        rows += f'<tr><td class="lbl">{_h.escape(label)}</td><td>{value}</td></tr>'

    html = f"""<!DOCTYPE html>
<html lang="pl"><head><meta charset="utf-8">
<style>
  body {{ font-family: Arial, sans-serif; font-size: 12px; color: #1a1a2e; margin: 40px; }}
  h1 {{ font-size: 16px; color: #1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom: 6px; }}
  .meta {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;
           padding: 10px 14px; margin: 12px 0; font-size: 11px; color: #475569; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 14px; }}
  th {{ background: #1e3a8a; color: white; padding: 7px 10px; text-align: left; font-size: 11px; }}
  td {{ padding: 6px 10px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }}
  td.lbl {{ font-weight: bold; width: 35%; color: #374151; }}
  .badge {{ display:inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold;
            background: {'#dcfce7' if submission.status=='approved' else '#fef9c3' if submission.status=='submitted' else '#fee2e2' if submission.status=='rejected' else '#f1f5f9'};
            color: {'#166534' if submission.status=='approved' else '#713f12' if submission.status=='submitted' else '#991b1b' if submission.status=='rejected' else '#475569'}; }}
  .comment {{ background: #fffbeb; border-left: 3px solid #f59e0b; padding: 8px 12px; margin-top: 14px; font-size: 11px; }}
  .footer {{ margin-top: 30px; font-size: 10px; color: #9ca3af; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 8px; }}
</style></head><body>
<h1>{_h.escape(att_name)}</h1>
<div class="meta">
  <strong>Status:</strong> <span class="badge">{_h.escape(status_pl)}</span> &nbsp;
  <strong>Wysłano:</strong> {created} &nbsp;
  <strong>Zmieniono:</strong> {updated}
</div>
<table>
  <tr><th colspan="2">Dane dokumentu</th></tr>
  {rows if rows else '<tr><td colspan="2" style="color:#9ca3af;font-style:italic;">Brak wypełnionych danych</td></tr>'}
</table>
{f'<div class="comment"><strong>Uwagi recenzenta:</strong> {_h.escape(submission.comments)}</div>' if submission.comments else ''}
<div class="footer">System Obsługi Praktyk Zawodowych — ANS Elbląg</div>
</body></html>"""

    try:
        return HTML(string=html).write_pdf()
    except Exception as e:
        print(f"[export PDF] WeasyPrint error: {e}")
        return None


@admin_bp.route('/export/<int:user_id>')
@login_required
@role_required('administrator', 'admin', 'dziekanat', 'sekretariat', 'dyrekcja')
def export_user_files(user_id):
    from app.models import Attachment

    user = User.query.get_or_404(user_id)
    subs = DocumentSubmission.query.filter_by(user_id=user_id).all()
    att_names = {a.id: a.name for a in Attachment.query.all()}

    mem = io.BytesIO()
    count = 0
    with zipfile.ZipFile(mem, mode='w', compression=zipfile.ZIP_DEFLATED) as z:
        for s in subs:
            if s.attachment_id is None:
                continue
            att_name = att_names.get(s.attachment_id, f'Dokument {s.id}')
            safe_name = att_name.replace('/', '-').replace('\\', '-')[:50]
            pdf_bytes = _doc_to_pdf_bytes(att_name, s)
            if pdf_bytes:
                filename = f'{s.id:03d}_{safe_name}_{s.status}.pdf'
                z.writestr(filename, pdf_bytes)
                count += 1

    mem.seek(0)
    if count == 0:
        flash('Ten użytkownik nie ma żadnych dokumentów do eksportu.', 'warning')
        return redirect(request.referrer or url_for('admin.users_list'))

    safe_email = (user.email or f'user_{user_id}').replace('@', '_').replace('.', '_')
    return send_file(mem, mimetype='application/zip', as_attachment=True,
                     download_name=f'dokumenty_{safe_email}.zip')

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@role_required('administrator', 'admin')
def create_user():
    form = AdminCreateUserForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data).first()
        if existing:
            flash('Uzytkownik o tym adresie email juz istnieje', 'warning')
            return redirect(url_for('admin.users_list'))
        user = User(
            email=form.email.data,
            full_name=form.full_name.data or None,
            role=form.role.data,
            is_active=True,
            auth_provider='local',
            student_index=form.student_index.data or None,
        )
        if form.password.data:
            user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Uzytkownik utworzony', 'success')
        return redirect(url_for('admin.users_list'))
    return render_template('admin/create_user.html', form=form)

@admin_bp.route('/users/<int:user_id>/role', methods=['GET', 'POST'])
@login_required
@role_required('administrator', 'admin')
def assign_role(user_id):
    user = User.query.get_or_404(user_id)
    form = AssignRoleForm(role=user.role)
    if form.validate_on_submit():
        old = user.role
        user.role = form.role.data
        db.session.commit()
        flash('Rola zaktualizowana', 'success')
        return redirect(url_for('admin.users_list'))
    return render_template('admin/assign_role.html', user=user, form=form)