"""
API endpoints for Learning Outcomes
"""

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models.internship import LearningOutcome, Internship
from datetime import datetime

learning_outcomes_bp = Blueprint('learning_outcomes', __name__)


@learning_outcomes_bp.route('/learning-outcomes', methods=['GET'])
@login_required
def get_learning_outcomes():
    """
    GET /api/learning-outcomes
    
    Get learning outcomes for an internship.
    """
    
    internship_id = request.args.get('internship_id', None, type=int)
    
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
    
    outcomes = LearningOutcome.query.filter_by(internship_id=internship_id).all()
    
    return jsonify({
        'success': True,
        'data': [
            {
                'id': o.id,
                'outcome_text': o.outcome_text,
                'status': o.status,
                'achieved_date': o.achieved_date.isoformat() if o.achieved_date else None,
                'verified_date': o.verified_date.isoformat() if o.verified_date else None,
            }
            for o in outcomes
        ]
    })


@learning_outcomes_bp.route('/learning-outcome', methods=['POST'])
@login_required
def create_learning_outcome():
    """
    POST /api/learning-outcome
    
    Create a new learning outcome.
    """
    
    data = request.get_json()
    internship_id = data.get('internship_id')
    
    internship = Internship.query.get(internship_id)
    
    if not internship:
        return jsonify({'success': False, 'error': 'Internship not found'}), 404
    
    # Check permissions - only student who owns the internship
    if current_user.role != 'student' or internship.student_id != current_user.id:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    outcome_text = data.get('outcome_text', '').strip()
    
    if not outcome_text:
        return jsonify({'success': False, 'error': 'outcome_text required'}), 400
    
    if len(outcome_text) < 20 or len(outcome_text) > 500:
        return jsonify({'success': False, 'error': 'outcome_text must be 20-500 chars'}), 400
    
    try:
        outcome = LearningOutcome(
            internship_id=internship_id,
            outcome_text=outcome_text,
            status='planned'
        )
        
        db.session.add(outcome)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Learning outcome created',
            'data': {
                'id': outcome.id,
                'outcome_text': outcome.outcome_text,
                'status': outcome.status,
            }
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@learning_outcomes_bp.route('/learning-outcome/<int:outcome_id>/verify', methods=['PATCH'])
@login_required
def verify_learning_outcome(outcome_id):
    """
    PATCH /api/learning-outcome/<id>/verify
    
    Verify a learning outcome (mentor only).
    """
    
    outcome = LearningOutcome.query.get(outcome_id)
    
    if not outcome:
        return jsonify({'success': False, 'error': 'Outcome not found'}), 404
    
    # Check permissions - only mentor of this internship or admin
    if current_user.role == 'opiekun' and outcome.internship.mentor_id != current_user.id:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    elif current_user.role not in ['opiekun', 'admin', 'staff']:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    data = request.get_json()
    action = data.get('action', 'verify')  # 'verify' or 'unverify'
    
    if action == 'verify':
        outcome.status = 'verified'
        outcome.verified_by = current_user.id
        outcome.verified_date = datetime.now().date()
        message = 'Learning outcome verified'
    elif action == 'unverify':
        outcome.status = 'achieved'
        outcome.verified_by = None
        outcome.verified_date = None
        message = 'Learning outcome verification removed'
    else:
        return jsonify({'success': False, 'error': 'Invalid action'}), 400
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': message,
        'data': {
            'id': outcome.id,
            'status': outcome.status,
        }
    })


@learning_outcomes_bp.route('/learning-outcome/<int:outcome_id>/mark-achieved', methods=['PATCH'])
@login_required
def mark_outcome_achieved(outcome_id):
    """
    PATCH /api/learning-outcome/<id>/mark-achieved
    
    Mark learning outcome as achieved (student only).
    """
    
    outcome = LearningOutcome.query.get(outcome_id)
    
    if not outcome:
        return jsonify({'success': False, 'error': 'Outcome not found'}), 404
    
    # Check permissions - only student who owns this internship
    if current_user.role != 'student' or outcome.internship.student_id != current_user.id:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    outcome.status = 'achieved'
    outcome.achieved_date = datetime.now().date()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Learning outcome marked as achieved',
        'data': {
            'id': outcome.id,
            'status': outcome.status,
        }
    })
