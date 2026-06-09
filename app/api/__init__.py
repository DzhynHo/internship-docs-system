"""
API Blueprint - REST API Endpoints
"""

from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import route modules
from app.api import internships, documents, diary, learning_outcomes, admin

# Register routes
api_bp.register_blueprint(internships.internships_bp)
api_bp.register_blueprint(documents.documents_bp)
api_bp.register_blueprint(diary.diary_bp)
api_bp.register_blueprint(learning_outcomes.learning_outcomes_bp)
api_bp.register_blueprint(admin.admin_bp)
