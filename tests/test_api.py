"""
Tests for REST API endpoints
"""

import pytest
from flask import url_for
from datetime import datetime, time


class TestInternshipsAPI:
    """Test Internships API endpoints."""
    
    def test_student_get_internships(self, client, student_user, sample_internship):
        """GET /api/internships returns student's internships."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get('/api/internships')
        assert response.status_code == 200
        assert response.json['success'] is True
        assert len(response.json['data']) >= 1
    
    
    def test_mentor_get_internships(self, client, mentor_user, sample_internship):
        """GET /api/internships for mentor returns only their students."""
        client.post(url_for('auth.login'), data={
            'email': mentor_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get('/api/internships')
        assert response.status_code == 200
        assert response.json['success'] is True
        assert len(response.json['data']) >= 1
    
    
    def test_get_internship_stats(self, client, student_user, sample_internship):
        """GET /api/internship/<id>/stats returns statistics."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get(f'/api/internship/{sample_internship.id}/stats')
        assert response.status_code == 200
        assert response.json['success'] is True
        assert 'total_hours' in response.json['data']
        assert 'completion_percent' in response.json['data']


class TestDocumentsAPI:
    """Test Documents API endpoints."""
    
    def test_get_documents(self, client, student_user, sample_document):
        """GET /api/documents returns documents for current user."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get('/api/documents')
        assert response.status_code == 200
        assert response.json['success'] is True
        assert len(response.json['data']) >= 1
    
    
    def test_get_documents_by_status(self, client, student_user, sample_document):
        """GET /api/documents?status=draft filters by status."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get('/api/documents?status=draft')
        assert response.status_code == 200
        assert response.json['success'] is True
        assert all(d['status'] == 'draft' for d in response.json['data'])
    
    
    def test_approve_document(self, client, mentor_user, sample_document):
        """PATCH /api/document/<id>/approve marks document as approved."""
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
    
    
    def test_reject_document(self, client, mentor_user, sample_document):
        """PATCH /api/document/<id>/reject marks document as rejected."""
        client.post(url_for('auth.login'), data={
            'email': mentor_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.patch(
            f'/api/document/{sample_document.id}/reject',
            json={'comments': 'Wymagane poprawy'}
        )
        assert response.status_code == 200
        assert response.json['data']['status'] == 'rejected'


class TestDiaryAPI:
    """Test Diary API endpoints."""
    
    def test_get_diary_entries(self, client, student_user, sample_internship, sample_diary_entry):
        """GET /api/diary-entries returns diary entries."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get(f'/api/diary-entries?internship_id={sample_internship.id}')
        assert response.status_code == 200
        assert response.json['success'] is True
        assert len(response.json['data']) >= 1
    
    
    def test_create_diary_entry(self, client, student_user, sample_internship):
        """POST /api/diary-entry creates new diary entry."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        today = datetime.now().date().isoformat()
        response = client.post(
            '/api/diary-entry',
            json={
                'internship_id': sample_internship.id,
                'date': f'{today}T00:00:00',
                'start_time': '09:00:00',
                'end_time': '17:00:00',
                'description': 'Test entry description'
            }
        )
        assert response.status_code == 201
        assert response.json['success'] is True
        assert response.json['data']['hours_worked'] == 8.0


class TestLearningOutcomesAPI:
    """Test Learning Outcomes API endpoints."""
    
    def test_get_learning_outcomes(self, client, student_user, sample_internship, sample_learning_outcome):
        """GET /api/learning-outcomes returns learning outcomes."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get(f'/api/learning-outcomes?internship_id={sample_internship.id}')
        assert response.status_code == 200
        assert response.json['success'] is True
        assert len(response.json['data']) >= 1
    
    
    def test_create_learning_outcome(self, client, student_user, sample_internship):
        """POST /api/learning-outcome creates new outcome."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.post(
            '/api/learning-outcome',
            json={
                'internship_id': sample_internship.id,
                'outcome_text': 'This is a valid learning outcome for the student'
            }
        )
        assert response.status_code == 201
        assert response.json['success'] is True
        assert response.json['data']['status'] == 'planned'
    
    
    def test_verify_learning_outcome(self, client, mentor_user, sample_learning_outcome):
        """PATCH /api/learning-outcome/<id>/verify verifies outcome."""
        client.post(url_for('auth.login'), data={
            'email': mentor_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.patch(
            f'/api/learning-outcome/{sample_learning_outcome.id}/verify',
            json={'action': 'verify'}
        )
        assert response.status_code == 200
        assert response.json['data']['status'] == 'verified'


class TestAdminAPI:
    """Test Admin API endpoints."""
    
    def test_dashboard_stats(self, client, admin_user, sample_internship):
        """GET /api/dashboard-stats returns system statistics."""
        client.post(url_for('auth.login'), data={
            'email': admin_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get('/api/dashboard-stats')
        assert response.status_code == 200
        assert response.json['success'] is True
        assert 'internships' in response.json['data']
        assert 'documents' in response.json['data']
    
    
    def test_internships_by_status(self, client, admin_user, sample_internship):
        """GET /api/internships/status/<status> filters by status."""
        client.post(url_for('auth.login'), data={
            'email': admin_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get('/api/internships/status/active')
        assert response.status_code == 200
        assert response.json['success'] is True
        assert all(i['status'] == 'active' for i in response.json['data'])


class TestAPIErrorHandling:
    """Test API error handling."""
    
    def test_nonexistent_internship(self, client, student_user):
        """GET /api/internship/99999 returns 404."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get('/api/internship/99999')
        assert response.status_code == 404
    
    
    def test_invalid_diary_entry_missing_internship(self, client, student_user):
        """POST /api/diary-entries without internship_id returns error."""
        client.post(url_for('auth.login'), data={
            'email': student_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get('/api/diary-entries')
        assert response.status_code == 400
        assert response.json['success'] is False
