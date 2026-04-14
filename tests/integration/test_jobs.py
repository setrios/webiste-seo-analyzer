import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
from unittest.mock import AsyncMock


class TestJobEndpoints:
    def test_post_jobs_creates_job(self, client, auth_headers):
        # Act
        response = client.post('/jobs', json={'url': 'https://example.com'}, headers=auth_headers)
        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body['url'] == 'https://example.com'
        assert body['status'] == 'QUEUED'

    def test_post_jobs_idempotent(self, client, auth_headers):
        # Act
        r1 = client.post('/jobs', json={'url': 'https://example.com'}, headers=auth_headers)
        r2 = client.post('/jobs', json={'url': 'https://example.com'}, headers=auth_headers)
        # Assert
        assert r1.json()['id'] == r2.json()['id']

    def test_get_jobs_returns_list(self, client, auth_headers):
        client.post('/jobs', json={'url': 'https://a.com'}, headers=auth_headers)
        response = client.get('/jobs', headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

    def test_get_job_by_id(self, client, auth_headers):
        job_id = client.post('/jobs', json={'url': 'https://b.com'}, headers=auth_headers).json()['id']
        response = client.get(f'/jobs/{job_id}', headers=auth_headers)
        assert response.status_code == 200
        assert response.json()['id'] == job_id

    def test_get_job_not_found(self, client, auth_headers):
        response = client.get('/jobs/999999', headers=auth_headers)
        assert response.status_code == 404

    def test_patch_job_valid_transition(self, client, auth_headers):
        # Assemble: job створюється зі статусом QUEUED
        job_id = client.post('/jobs', json={'url': 'https://c.com'}, headers=auth_headers).json()['id']
        # Act
        response = client.patch(f'/jobs/{job_id}', json={'status': 'PROCESSING'}, headers=auth_headers)
        # Assert
        assert response.status_code == 200
        assert response.json()['status'] == 'PROCESSING'

    def test_patch_job_invalid_transition_returns_400(self, client, auth_headers):
        # Assemble: доводимо до DONE через PROCESSING
        job_id = client.post('/jobs', json={'url': 'https://d.com'}, headers=auth_headers).json()['id']
        client.patch(f'/jobs/{job_id}', json={'status': 'PROCESSING'}, headers=auth_headers)
        client.patch(f'/jobs/{job_id}', json={'status': 'DONE'}, headers=auth_headers)
        # Act: DONE → QUEUED — невалідний
        response = client.patch(f'/jobs/{job_id}', json={'status': 'QUEUED'}, headers=auth_headers)
        # Assert
        assert response.status_code == 400

    def test_delete_job(self, client, auth_headers):
        job_id = client.post('/jobs', json={'url': 'https://e.com'}, headers=auth_headers).json()['id']
        delete_response = client.delete(f'/jobs/{job_id}', headers=auth_headers)
        assert delete_response.status_code == 200
        get_response = client.get(f'/jobs/{job_id}', headers=auth_headers)
        assert get_response.status_code == 404

    def test_get_all_jobs_public(self, client):
        response = client.get('/jobs-all')
        assert response.status_code == 200
        assert isinstance(response.json(), list)
