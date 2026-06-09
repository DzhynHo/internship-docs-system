"""
Test fixtures and configuration for pytest
"""

import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models.user import User
from app.models.internship import Internship, DiaryEntry, LearningOutcome
from app.models import DocumentSubmission, Attachment


@pytest.fixture(scope='session')
def app():
    """Create app for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def student_user(app):
    """Create test student user."""
    with app.app_context():
        existing = User.query.filter_by(email='student@test.com').first()
        if existing:
            return existing

        user = User(
            email='student@test.com',
            first_name='Jan',
            last_name='Kowalski',
            role='student',
            is_active=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return User.query.filter_by(email='student@test.com').first()


@pytest.fixture
def mentor_user(app):
    """Create test mentor user."""
    with app.app_context():
        existing = User.query.filter_by(email='mentor@test.com').first()
        if existing:
            return existing

        user = User(
            email='mentor@test.com',
            first_name='Maria',
            last_name='Nowak',
            role='opiekun',
            is_active=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return User.query.filter_by(email='mentor@test.com').first()


@pytest.fixture
def admin_user(app):
    """Create test admin user."""
    with app.app_context():
        existing = User.query.filter_by(email='admin@test.com').first()
        if existing:
            return existing

        user = User(
            email='admin@test.com',
            first_name='Admin',
            last_name='User',
            role='admin',
            is_active=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return User.query.filter_by(email='admin@test.com').first()


@pytest.fixture
def sample_internship(app, student_user, mentor_user):
    """Create sample internship."""
    with app.app_context():
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=60)
        
        existing = Internship.query.filter_by(student_id=student_user.id, mentor_id=mentor_user.id, company_name='Test Company').first()
        if existing:
            return existing

        internship = Internship(
            student_id=student_user.id,
            mentor_id=mentor_user.id,
            company_name='Test Company',
            start_date=start_date,
            end_date=end_date,
            total_hours=240,
            status='active'
        )
        db.session.add(internship)
        db.session.commit()
        return Internship.query.filter_by(student_id=student_user.id, mentor_id=mentor_user.id, company_name='Test Company').first()


@pytest.fixture
def sample_document(app, sample_internship, student_user):
    """Create sample document."""
    with app.app_context():
        # Ensure attachment exists
        attachment = Attachment.query.filter_by(name='Porozumienie').first()
        if not attachment:
            attachment = Attachment(
                name='Porozumienie',
                filename='01_Porozumienie.pdf',
                description='Umowa o praktykę',
                audience='all',
                required=True
            )
            db.session.add(attachment)
            db.session.commit()
        
        existing = DocumentSubmission.query.filter_by(user_id=student_user.id, internship_id=sample_internship.id, attachment_id=attachment.id).first()
        if existing:
            return existing

        document = DocumentSubmission(
            user_id=student_user.id,
            internship_id=sample_internship.id,
            attachment_id=attachment.id,
            status='draft',
            data={'company_name': 'Test Company'}
        )
        db.session.add(document)
        db.session.commit()
        return DocumentSubmission.query.filter_by(user_id=student_user.id, internship_id=sample_internship.id, attachment_id=attachment.id).first()


@pytest.fixture
def sample_diary_entry(app, sample_internship):
    """Create sample diary entry."""
    with app.app_context():
        from datetime import time
        
        existing = DiaryEntry.query.filter_by(internship_id=sample_internship.id, description='Test diary entry').first()
        if existing:
            return existing

        entry = DiaryEntry(
            internship_id=sample_internship.id,
            date=datetime.now().date(),
            start_time=time(9, 0),
            end_time=time(17, 0),
            description='Test diary entry'
        )
        db.session.add(entry)
        db.session.commit()
        return DiaryEntry.query.filter_by(internship_id=sample_internship.id, description='Test diary entry').first()


@pytest.fixture
def sample_learning_outcome(app, sample_internship):
    """Create sample learning outcome."""
    with app.app_context():
        existing = LearningOutcome.query.filter_by(internship_id=sample_internship.id, outcome_text='Student will be able to write Python code').first()
        if existing:
            return existing

        outcome = LearningOutcome(
            internship_id=sample_internship.id,
            outcome_text='Student will be able to write Python code',
            status='planned'
        )
        db.session.add(outcome)
        db.session.commit()
        return LearningOutcome.query.filter_by(internship_id=sample_internship.id, outcome_text='Student will be able to write Python code').first()
