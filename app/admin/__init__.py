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

@admin_bp.route('/export/<int:user_id>')
@login_required
@role_required('administrator', 'admin', 'dziekanat', 'sekretariat', 'dyrekcja')
def export_user_files(user_id):
    import json
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
            att_name = att_names.get(s.attachment_id, f'dokument_{s.id}')
            safe_name = att_name.replace('/', '-').replace('\\', '-')[:60]
            filename = f'{s.id:03d}_{safe_name}_{s.status}.json'

            content = {
                'zalacznik': att_name,
                'status': s.status,
                'data_wyslania': s.created_at.strftime('%Y-%m-%d %H:%M') if s.created_at else None,
                'data_zmiany': s.updated_at.strftime('%Y-%m-%d %H:%M') if s.updated_at else None,
                'komentarz': s.comments,
                'dane': s.data or {},
            }
            z.writestr(filename, json.dumps(content, ensure_ascii=False, indent=2))
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