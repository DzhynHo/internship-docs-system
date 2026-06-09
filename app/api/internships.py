"""
API endpoints for Internships
"""

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models.internship import Internship
from app.auth.permissions import role_required, student_required, mentor_required

internships_bp = Blueprint('internships', __name__)


@internships_bp.route('/internships', methods=['GET'])
@login_required
def get_internships():
    """
    GET /api/internships
    
    Get internships for the current user.
    - Students see only their own
    - Mentors see students they supervise
    - Admin sees all
    """
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = None
    
    if current_user.role == 'student':
        query = Internship.query.filter_by(student_id=current_user.id)
    elif current_user.role == 'opiekun':
        query = Internship.query.filter_by(mentor_id=current_user.id)
    elif current_user.role in ['admin', 'staff']:
        query = Internship.query
    else:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    paginated = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'success': True,
        'data': [i.to_dict() for i in paginated.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': paginated.total,
            'pages': paginated.pages
        }
    })


@internships_bp.route('/internship/<int:internship_id>', methods=['GET'])
@login_required
def get_internship(internship_id):
    """
    GET /api/internship/<id>
    
    Get details of a specific internship.
    """
    
    internship = Internship.query.get(internship_id)
    
    if not internship:
        return jsonify({'success': False, 'error': 'Internship not found'}), 404
    
    # Check access permissions
    if current_user.role == 'student' and internship.student_id != current_user.id:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    elif current_user.role == 'opiekun' and internship.mentor_id != current_user.id:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    elif current_user.role not in ['admin', 'staff', 'student', 'opiekun']:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    return jsonify({
        'success': True,
        'data': internship.to_dict()
    })


@internships_bp.route('/internship/<int:internship_id>', methods=['PUT'])
@login_required
def update_internship(internship_id):
    """
    PUT /api/internship/<id>
    
    Update internship data (only student can update, or admin/staff)
    """
    
    internship = Internship.query.get(internship_id)
    
    if not internship:
        return jsonify({'success': False, 'error': 'Internship not found'}), 404
    
    # Check permissions
    if current_user.role == 'student' and internship.student_id != current_user.id:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    elif current_user.role not in ['admin', 'staff', 'student']:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    data = request.get_json()
    
    # Only allow certain fields to be updated
    updatable_fields = ['company_name', 'total_hours', 'job_description']
    
    for field in updatable_fields:
        if field in data:
            setattr(internship, field, data[field])
    
    if 'status' in data and current_user.role in ['admin', 'staff']:
        internship.status = data['status']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': internship.to_dict()
    })


@internships_bp.route('/internship/<int:internship_id>/stats', methods=['GET'])
@login_required
def get_internship_stats(internship_id):
    """
    GET /api/internship/<id>/stats
    
    Get statistics for internship.
    """
    
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
    
    return jsonify({
        'success': True,
        'data': {
            'total_hours': internship.total_hours,
            'total_hours_worked': internship.total_hours_worked,
            'completion_percent': internship.completion_percent,
            'days_passed': internship.days_passed,
            'diary_entries_count': len(internship.diary_entries),
            'learning_outcomes_count': len(internship.learning_outcomes),
            'documents_count': len(internship.documents),
        }
    })
