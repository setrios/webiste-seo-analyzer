import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import Base, Job, User, JobStatus as DBJobStatus
from app import app, get_db

TEST_DATABASE_URL = 'sqlite:///:memory:'

@pytest.fixture()
def db_session():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={'check_same_thread': False}
    )

    Base.metadata.create_all(bind=engine)
    TestingSession =sessionmaker(bind=engine)
    session = TestingSession()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
            yield db_session

    app.dependency_overrides[get_db] = override_get_db

    mock_channel = MagicMock()
    mock_channel.default_exchange.publish = AsyncMock()
    mock_connection = MagicMock()
    mock_connection.close = AsyncMock()

    with patch('app.aio_pika.connect_robust', new=AsyncMock(return_value=mock_connection)), patch('app.asyncio.create_task'):
        mock_connection.channel = AsyncMock(return_value=mock_channel)
        mock_channel.declare_queue = AsyncMock()
        mock_channel.get_queue = AsyncMock()
        with TestClient(app) as c:
            c.app_state_channel = mock_channel  # зберігаємо для перевірки в тестах
            yield c

    app.dependency_overrides.clear()


@pytest.fixture()
def auth_token(client):
    response = client.post('/token')
    assert response.status_code == 200
    return response.json()['access_token']


@pytest.fixture()
def auth_headers(auth_token):
    return {'Authorization': f'Bearer {auth_token}'}


def make_user(db_session, user_id: int = 1) -> User:
    user = User(id=user_id, username=f'user_{user_id}')
    db_session.add(user)
    db_session.commit()
    return user


def make_job(db_session, user_id: int = 1, url: str = 'https://example.com',
             status: str = 'QUEUED', s3_key: str | None = None,
             progress: int = 0) -> Job:

    job = Job(url=url, status=status, user_id=user_id, s3_key=s3_key, progress=progress)

    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job