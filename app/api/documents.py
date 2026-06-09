"""
API endpoints for Documents
"""

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import DocumentSubmission, Attachment
from app.models.internship import Internship
from datetime import datetime

documents_bp = Blueprint('documents', __name__)


@documents_bp.route('/documents', methods=['GET'])
@login_required
def get_documents():
    """
    GET /api/documents
    
    Get documents (filtered by user role and permissions)
    """
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', None)
    
    query = DocumentSubmission.query
    
    # Filter by role
    if current_user.role == 'student':
        query = query.filter_by(user_id=current_user.id)
    elif current_user.role == 'opiekun':
        # Get documents from internships where mentor is current_user
        internship_ids = db.session.query(Internship.id).filter_by(mentor_id=current_user.id).all()
        query = query.filter(DocumentSubmission.internship_id.in_([i[0] for i in internship_ids]))
    elif current_user.role not in ['admin', 'staff']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    # Filter by status if provided
    if status:
        query = query.filter_by(status=status)
    
    paginated = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'success': True,
        'data': [
            {
                'id': d.id,
                'attachment_name': d.attachment.name if d.attachment else 'Unknown',
                'status': d.status,
                'created_at': d.created_at.isoformat(),
                'updated_at': d.updated_at.isoformat(),
                'internship_id': d.internship_id,
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


@documents_bp.route('/document/<int:document_id>', methods=['GET'])
@login_required
def get_document(document_id):
    """
    GET /api/document/<id>
    
    Get details of a specific document.
    """
    
    document = DocumentSubmission.query.get(document_id)
    
    if not document:
        return jsonify({'success': False, 'error': 'Document not found'}), 404
    
    # Check permissions
    if current_user.role == 'student' and document.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    elif current_user.role == 'opiekun' and document.internship.mentor_id != current_user.id:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    elif current_user.role not in ['admin', 'staff', 'student', 'opiekun']:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    return jsonify({
        'success': True,
        'data': {
            'id': document.id,
            'attachment_name': document.attachment.name if document.attachment else 'Unknown',
            'status': document.status,
            'data': document.data,
            'comments': document.comments,
            'created_at': document.created_at.isoformat(),
            'updated_at': document.updated_at.isoformat(),
        }
    })


@documents_bp.route('/document/<int:document_id>/approve', methods=['PATCH'])
@login_required
def approve_document(document_id):
    """
    PATCH /api/document/<id>/approve
    
    Approve a document (mentor only)
    """
    
    document = DocumentSubmission.query.get(document_id)
    
    if not document:
        return jsonify({'success': False, 'error': 'Document not found'}), 404
    
    # Check permissions - only mentor or admin/staff
    if current_user.role == 'opiekun':
        if document.internship.mentor_id != current_user.id:
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
    elif current_user.role not in ['admin', 'staff']:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    document.status = 'approved'
    document.reviewer_id = current_user.id
    document.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Document approved',
        'data': {
            'id': document.id,
            'status': document.status
        }
    })


@documents_bp.route('/document/<int:document_id>/reject', methods=['PATCH'])
@login_required
def reject_document(document_id):
    """
    PATCH /api/document/<id>/reject
    
    Reject a document (mentor only)
    """
    
    document = DocumentSubmission.query.get(document_id)
    
    if not document:
        return jsonify({'success': False, 'error': 'Document not found'}), 404
    
    data = request.get_json()
    comments = data.get('comments', '')
    
    if not comments:
        return jsonify({'success': False, 'error': 'Comments are required'}), 400
    
    # Check permissions
    if current_user.role == 'opiekun':
        if document.internship.mentor_id != current_user.id:
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
    elif current_user.role not in ['admin', 'staff']:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    document.status = 'rejected'
    document.comments = comments
    document.reviewer_id = current_user.id
    document.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Document rejected',
        'data': {
            'id': document.id,
            'status': document.status
        }
    })
