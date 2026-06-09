"""
Tests for permission decorators and access control
"""

import pytest
from flask import url_for


class TestRoleBasedAccess:
    """Test role-based access control."""
    
    def test_student_can_view_own_internship(self, client, student_user, sample_internship):
        """Student can view their own internship."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get(f'/api/internship/{sample_internship.id}')
        assert response.status_code == 200
        assert response.json['success'] is True
    
    
    def test_student_cannot_view_other_internship(self, client, student_user, mentor_user, sample_internship, app):
        """Student cannot view other student's internship."""
        # Create another student
        with app.app_context():
            from app.models.user import User
            from app import db
            other_student = User(
                email='other@test.com',
                first_name='Other',
                last_name='Student',
                role='student',
                is_active=True
            )
            other_student.set_password('password123')
            db.session.add(other_student)
            db.session.commit()
        
        # Login as other student
        client.post(url_for('auth.login'), data={
            'email': 'other@test.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get(f'/api/internship/{sample_internship.id}')
        assert response.status_code == 403
    
    
    def test_mentor_can_view_assigned_internship(self, client, mentor_user, sample_internship):
        """Mentor can view assigned internship."""
        client.post(url_for('auth.login'), data={
            'email': mentor_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get(f'/api/internship/{sample_internship.id}')
        assert response.status_code == 200
        assert response.json['success'] is True
    
    
    def test_admin_can_view_any_internship(self, client, admin_user, sample_internship):
        """Admin can view any internship."""
        client.post(url_for('auth.login'), data={
            'email': admin_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get(f'/api/internship/{sample_internship.id}')
        assert response.status_code == 200
        assert response.json['success'] is True


class TestDocumentAccess:
    """Test document access control."""
    
    def test_student_can_view_own_documents(self, client, student_user, sample_document):
        """Student can view their own documents."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get(f'/api/document/{sample_document.id}')
        assert response.status_code == 200
        assert response.json['success'] is True
    
    
    def test_mentor_can_approve_assigned_document(self, client, mentor_user, sample_document):
        """Mentor can approve document from assigned student."""
        client.post(url_for('auth.login'), data={
            'email': mentor_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.patch(
            f'/api/document/{sample_document.id}/approve',
            json={}
        )
        assert response.status_code == 200
        assert response.json['data']['status'] == 'approved'


class TestPermissionDecorators:
    """Test permission decorator functions."""
    
    def test_mentor_required_decorator(self, client, student_user):
        """mentor_required decorator blocks non-mentors."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        # Try to access mentor-only endpoint
        response = client.get('/opiekun/dashboard')
        assert response.status_code == 403
    
    
    def test_admin_required_decorator(self, client, student_user):
        """admin_required decorator blocks non-admins."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        # Try to access admin-only endpoint
        response = client.get('/api/dashboard-stats')
        assert response.status_code == 403


class TestProtocolAccess:
    """Test special protocol (Attachment 8) access control."""
    
    def test_student_cannot_view_protocol(self, client, student_user, sample_internship, app):
        """Student cannot view Protocol (Attachment 8)."""
        with app.app_context():
            from app.models import Attachment, DocumentSubmission
            from app import db
            
            # Create protocol attachment and document
            protocol = Attachment.query.filter_by(name='Protokół').first()
            if not protocol:
                protocol = Attachment(
                    name='Protokół',
                    filename='08_Protokol.pdf',
                    description='Protokół egzaminu',
                    audience='staff',
                    required=False
                )
                db.session.add(protocol)
                db.session.commit()
            
            doc = DocumentSubmission(
                user_id=student_user.id,
                internship_id=sample_internship.id,
                attachment_id=protocol.id,
                status='approved',
                data={}
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id
        
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get(f'/api/document/{doc_id}')
        assert response.status_code == 403
