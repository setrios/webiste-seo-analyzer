import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import jwt
import pytest
from datetime import datetime, timezone, timedelta


SECRET = os.getenv('SECRET_KEY', 'secret')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')


def make_token(payload: dict, secret: str = SECRET) -> str:
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


class TestAuthMiddleware:
    def test_missing_token_returns_401(self, client):
        response = client.get('/jobs')
        assert response.status_code == 401

    def test_invalid_token_string_returns_401(self, client):
        response = client.get('/jobs', headers={'Authorization': 'Bearer garbage'})
        assert response.status_code == 401

    def test_expired_token_returns_401(self, client):
        # Assemble
        payload = {'sub': '1', 'exp': datetime.now(timezone.utc) - timedelta(seconds=1)}
        token = make_token(payload)
        # Act
        response = client.get('/jobs', headers={'Authorization': f'Bearer {token}'})
        # Assert
        assert response.status_code == 401

    def test_token_wrong_secret_returns_401(self, client):
        # Assemble
        payload = {'sub': '1', 'exp': datetime.now(timezone.utc) + timedelta(hours=1)}
        token = make_token(payload, secret='wrong-secret')
        # Act
        response = client.get('/jobs', headers={'Authorization': f'Bearer {token}'})
        # Assert
        assert response.status_code == 401

    def test_valid_token_grants_access(self, client, auth_headers):
        # Act
        response = client.get('/jobs', headers=auth_headers)
        # Assert
        assert response.status_code == 200

    def test_public_route_requires_no_token(self, client):
        response = client.get('/jobs-all')
        assert response.status_code == 200
