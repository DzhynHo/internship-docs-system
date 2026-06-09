"""
Tests for HTML routes and views
"""

import pytest
from flask import url_for


class TestAuthRoutes:
    """Test authentication routes."""
    
    def test_login_page(self, client):
        """GET /auth/login displays login page."""
        response = client.get('/auth/login')
        assert response.status_code == 200 or response.status_code == 302  # May redirect if already logged in
    
    
    def test_login_with_valid_credentials(self, client, student_user):
        """POST /auth/login with valid credentials logs in."""
        response = client.post(
            '/auth/login',
            data={
                'email': student_user.email,
                'password': 'password123'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Dashboard' in response.data or student_user.email.encode() in response.data


class TestStudentRoutes:
    """Test student routes."""
    
    def test_student_dashboard(self, client, student_user):
        """GET /student/dashboard displays student dashboard."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get('/student/dashboard')
        assert response.status_code == 200
        assert b'Praktyk' in response.data or b'Dashboard' in response.data
    
    
    def test_student_view_internship(self, client, student_user, sample_internship):
        """GET /student/internship/<id> displays internship details."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get(f'/student/internship/{sample_internship.id}')
        assert response.status_code == 200
        assert sample_internship.company_name.encode() in response.data
    
    
    def test_student_cannot_view_other_internship(self, client, student_user, sample_internship, app):
        """Student cannot view another student's internship."""
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
        
        client.post(url_for('auth.login'), data={
            'email': 'other@test.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get(f'/student/internship/{sample_internship.id}')
        assert response.status_code == 403


class TestMentorRoutes:
    """Test mentor routes."""
    
    def test_mentor_dashboard(self, client, mentor_user):
        """GET /opiekun/dashboard displays mentor dashboard."""
        client.post(url_for('auth.login'), data={
            'email': mentor_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get('/opiekun/dashboard')
        assert response.status_code == 200
        assert b'Panel' in response.data or b'Opiekun' in response.data
    
    
    def test_mentor_view_internship(self, client, mentor_user, sample_internship):
        """GET /opiekun/internship/<id> displays internship."""
        client.post(url_for('auth.login'), data={
            'email': mentor_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get(f'/opiekun/internship/{sample_internship.id}')
        assert response.status_code == 200
    
    
    def test_mentor_review_document(self, client, mentor_user, sample_document):
        """GET /opiekun/document/<id>/review displays review page."""
        client.post(url_for('auth.login'), data={
            'email': mentor_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get(f'/opiekun/document/{sample_document.id}/review')
        assert response.status_code == 200
        assert 'Przegląd'.encode('utf-8') in response.data or b'Review' in response.data
    
    
    def test_mentor_approve_document(self, client, mentor_user, sample_document):
        """POST /opiekun/document/<id>/review with approve action."""
        client.post(url_for('auth.login'), data={
            'email': mentor_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.post(
            f'/opiekun/document/{sample_document.id}/review',
            data={'action': 'approve'},
            follow_redirects=True
        )
        assert response.status_code == 200
    
    
    def test_mentor_reject_document(self, client, mentor_user, sample_document):
        """POST /opiekun/document/<id>/review with reject action."""
        client.post(url_for('auth.login'), data={
            'email': mentor_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.post(
            f'/opiekun/document/{sample_document.id}/review',
            data={
                'action': 'reject',
                'comment': 'Dokument wymaga poprawy.'
            },
            follow_redirects=True
        )
        assert response.status_code == 200


class TestUnauthenticatedAccess:
    """Test access control for unauthenticated users."""
    
    def test_unauthenticated_cannot_access_dashboard(self, client):
        """Unauthenticated user cannot access /student/dashboard."""
        response = client.get('/student/dashboard')
        # Should redirect to login or return 401
        assert response.status_code in [301, 302, 401, 403]
    
    
    def test_unauthenticated_cannot_access_mentor_dashboard(self, client):
        """Unauthenticated user cannot access /opiekun/dashboard."""
        response = client.get('/opiekun/dashboard')
        assert response.status_code in [301, 302, 401, 403]


class TestFlashMessages:
    """Test flash message handling."""
    
    def test_flash_message_on_document_approve(self, client, mentor_user, sample_document):
        """Flash message displayed after document approval."""
        client.post(url_for('auth.login'), data={
            'email': mentor_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.post(
            f'/opiekun/document/{sample_document.id}/review',
            data={'action': 'approve'},
            follow_redirects=True
        )
        assert response.status_code == 200
        # Check for success message (may vary by language)
        assert b'zatwierdz' in response.data.lower() or b'success' in response.data.lower() or b'ok' in response.data.lower()
