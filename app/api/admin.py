"""
API endpoints for Admin/Staff
"""

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models.internship import Internship
from app.models.document_submission import DocumentSubmission
from app.auth.permissions import role_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard-stats', methods=['GET'])
@login_required
@role_required('admin', 'staff')
def get_dashboard_stats():
    """
    GET /api/dashboard-stats
    
    Get system statistics for admin dashboard.
    """
    
    total_internships = Internship.query.count()
    active_internships = Internship.query.filter_by(status='active').count()
    completed_internships = Internship.query.filter_by(status='completed').count()
    
    total_documents = DocumentSubmission.query.count()
    approved_documents = DocumentSubmission.query.filter_by(status='approved').count()
    pending_documents = DocumentSubmission.query.filter(
        DocumentSubmission.status.in_(['submitted', 'pending_review'])
    ).count()
    rejected_documents = DocumentSubmission.query.filter_by(status='rejected').count()
    
    return jsonify({
        'success': True,
        'data': {
            'internships': {
                'total': total_internships,
                'active': active_internships,
                'completed': completed_internships,
            },
            'documents': {
                'total': total_documents,
                'approved': approved_documents,
                'pending': pending_documents,
                'rejected': rejected_documents,
            }
        }
    })


@admin_bp.route('/internships/status/<status>', methods=['GET'])
@login_required
@role_required('admin', 'staff')
def get_internships_by_status(status):
    """
    GET /api/internships/status/<status>
    
    Get internships by status (admin/staff only).
    """
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    valid_statuses = ['active', 'completed', 'failed', 'cancelled']
    if status not in valid_statuses:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    
    paginated = Internship.query.filter_by(status=status).paginate(
        page=page, per_page=per_page
    )
    
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


@admin_bp.route('/documents/status/<status>', methods=['GET'])
@login_required
@role_required('admin', 'staff')
def get_documents_by_status(status):
    """
    GET /api/documents/status/<status>
    
    Get documents by status (admin/staff only).
    """
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    valid_statuses = ['draft', 'submitted', 'pending_review', 'approved', 'rejected']
    if status not in valid_statuses:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    
    paginated = DocumentSubmission.query.filter_by(status=status).paginate(
        page=page, per_page=per_page
    )
    
    return jsonify({
        'success': True,
        'data': [
            {
                'id': d.id,
                'student': d.user.full_name if d.user else 'Unknown',
                'attachment': d.attachment.name if d.attachment else 'Unknown',
                'status': d.status,
                'created_at': d.created_at.isoformat(),
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


@admin_bp.route('/reports/monthly', methods=['GET'])
@login_required
@role_required('admin', 'staff')
def get_monthly_report():
    """
    GET /api/reports/monthly
    
    Get monthly statistics for reporting.
    """
    
    from datetime import datetime, timedelta
    from sqlalchemy import func, extract
    
    # Get data for last 12 months
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)
    
    monthly_data = db.session.query(
        extract('year', Internship.start_date).label('year'),
        extract('month', Internship.start_date).label('month'),
        func.count(Internship.id).label('count')
    ).filter(
        Internship.start_date >= start_date
    ).group_by('year', 'month').all()
    
    return jsonify({
        'success': True,
        'data': {
            'monthly': [
                {
                    'year': int(m[0]),
                    'month': int(m[1]),
                    'count': m[2]
                }
                for m in monthly_data
            ]
        }
    })
