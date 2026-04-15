import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock


SECRET = os.getenv('SECRET_KEY', 'secret')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')


class TestGetResultContract:
    def test_job_without_s3_key_returns_404(self, client, auth_headers):

        job_id = client.post('/jobs', json={'url': 'https://example.com'}, headers=auth_headers).json()['id']

        response = client.get(f'/jobs/{job_id}/result', headers=auth_headers)

        assert response.status_code == 404
        assert 'Result not avaliable yet' in response.json()['detail']

    def test_job_with_s3_key_returns_presigned_url(self, client, auth_headers, db_session):

        job_id = client.post('/jobs', json={'url': 'https://example.com'}, headers=auth_headers).json()['id']

        from database import Job
        job = db_session.get(Job, job_id)
        job.s3_key = 'jobs/1/result.json'
        job.status = 'DONE'
        db_session.commit()

        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = 'https://minio/presigned'


        with patch('app.boto3.client', return_value=mock_s3):
            response = client.get(f'/jobs/{job_id}/result', headers=auth_headers)


        assert response.status_code == 200
        body = response.json()
        assert 'presigned_url' in body
        assert isinstance(body['presigned_url'], str)
        assert body['presigned_url'].startswith('http')

    def test_response_structure_only_has_presigned_url_key(self, client, auth_headers, db_session):

        job_id = client.post('/jobs', json={'url': 'https://example.com'}, headers=auth_headers).json()['id']

        from database import Job
        job = db_session.get(Job, job_id)
        job.s3_key = 'jobs/1/result.json'
        job.status = 'DONE'
        db_session.commit()

        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = 'https://minio/presigned'

        with patch('app.boto3.client', return_value=mock_s3):
            response = client.get(f'/jobs/{job_id}/result', headers=auth_headers)


        assert set(response.json().keys()) == {'presigned_url'}
