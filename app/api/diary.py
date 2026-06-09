"""
API endpoints for Diary Entries
"""

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models.internship import DiaryEntry, Internship
from datetime import datetime

diary_bp = Blueprint('diary', __name__)


@diary_bp.route('/diary-entries', methods=['GET'])
@login_required
def get_diary_entries():
    """
    GET /api/diary-entries
    
    Get diary entries for internships accessible by current user.
    """
    
    internship_id = request.args.get('internship_id', None, type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    if not internship_id:
        return jsonify({'success': False, 'error': 'internship_id required'}), 400
    
    internship = Internship.query.get(internship_id)
    
    if not internship:
        return jsonify({'success': False, 'error': 'Internship not found'}), 404
    
    # Check permissions
    if current_user.role == 'student' and internship.student_id != current_user.id:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    elif current_user.role == 'opiekun' and internship.mentor_id != current_user.id:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    elif current_user.role not in ['admin', 'staff', 'student', 'opiekun']:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    paginated = DiaryEntry.query.filter_by(internship_id=internship_id).order_by(
        DiaryEntry.date.desc()
    ).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'success': True,
        'data': [
            {
                'id': d.id,
                'date': d.date.isoformat(),
                'start_time': str(d.start_time),
                'end_time': str(d.end_time),
                'hours_worked': d.hours_worked,
                'description': d.description,
            }
            for d in paginated.items
        ],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': paginated.total,
            'pages': paginated.pages
        }
    })


@diary_bp.route('/diary-entry', methods=['POST'])
@login_required
def create_diary_entry():
    """
    POST /api/diary-entry
    
    Create a new diary entry.
    """
    
    data = request.get_json()
    internship_id = data.get('internship_id')
    
    internship = Internship.query.get(internship_id)
    
    if not internship:
        return jsonify({'success': False, 'error': 'Internship not found'}), 404
    
    # Check permissions - only student who owns the internship
    if current_user.role != 'student' or internship.student_id != current_user.id:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    # Parse date and time
    try:
        entry = DiaryEntry(
            internship_id=internship_id,
            date=datetime.fromisoformat(data.get('date')).date(),
            start_time=datetime.fromisoformat(data.get('start_time')).time(),
            end_time=datetime.fromisoformat(data.get('end_time')).time(),
            description=data.get('description', ''),
        )
        
        # Validate
        is_valid, errors = entry.validate()
        if not is_valid:
            return jsonify({'success': False, 'errors': errors}), 400
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Diary entry created',
            'data': {
                'id': entry.id,
                'date': entry.date.isoformat(),
                'hours_worked': entry.hours_worked,
            }
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@diary_bp.route('/diary-entry/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_diary_entry(entry_id):
    """
    DELETE /api/diary-entry/<id>
    
    Delete a diary entry (only if from today or future).
    """
    
    entry = DiaryEntry.query.get(entry_id)
    
    if not entry:
        return jsonify({'success': False, 'error': 'Entry not found'}), 404
    
    # Check permissions
    if current_user.role != 'student' or entry.internship.student_id != current_user.id:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    # Check if can delete (today or future only)
    if entry.date < datetime.now().date():
        return jsonify({'success': False, 'error': 'Cannot delete past entries'}), 400
    
    db.session.delete(entry)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Diary entry deleted'
    })
