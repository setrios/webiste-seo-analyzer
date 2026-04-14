import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
from schemas import JobCreate, JobStatusUpdate, JobStatus
import service


class TestCreateJob:
    def test_creates_new_job(self, db_session, make_user):
        # Assemble
        make_user(user_id=1)
        job_data = JobCreate(url='https://example.com')
        # Act
        result = service.create_job(1, job_data, db_session)
        # Assert
        assert result.url == 'https://example.com'
        assert result.status == 'QUEUED'
        assert result.user_id == 1

    def test_idempotent_same_url(self, db_session, make_user):
        # Assemble
        make_user(user_id=1)
        job_data = JobCreate(url='https://example.com')
        # Act
        first = service.create_job(1, job_data, db_session)
        second = service.create_job(1, job_data, db_session)
        # Assert
        assert first.id == second.id


class TestGetJob:
    def test_returns_job_for_owner(self, db_session, make_user, make_job):
        # Assemble
        make_user(user_id=1)
        job = make_job(user_id=1)
        # Act
        result = service.get_job(1, job.id, db_session)
        # Assert
        assert result is not None
        assert result.id == job.id

    def test_returns_none_for_wrong_user(self, db_session, make_user, make_job):
        # Assemble
        make_user(user_id=1)
        make_user(user_id=2)
        job = make_job(user_id=1)
        # Act
        result = service.get_job(2, job.id, db_session)
        # Assert
        assert result is None


class TestUpdateJobStatus:
    def test_valid_transition(self, db_session, make_user, make_job):
        # Assemble
        make_user(user_id=1)
        job = make_job(user_id=1, status='QUEUED')
        update = JobStatusUpdate(status=JobStatus.PROCESSING)
        # Act
        result = service.update_job_status(1, job.id, update, db_session)
        # Assert
        assert result.status == 'PROCESSING'

    def test_invalid_transition_raises_value_error(self, db_session, make_user, make_job):
        # Assemble
        make_user(user_id=1)
        job = make_job(user_id=1, status='DONE')
        update = JobStatusUpdate(status=JobStatus.QUEUED)
        # Act + Assert
        with pytest.raises(ValueError):
            service.update_job_status(1, job.id, update, db_session)


class TestDeleteJob:
    def test_deletes_and_returns_job(self, db_session, make_user, make_job):
        # Assemble
        make_user(user_id=1)
        job = make_job(user_id=1)
        # Act
        deleted = service.delete_job(1, job.id, db_session)
        # Assert
        assert deleted is not None
        assert service.get_job(1, job.id, db_session) is None


class TestUpdateJobFromEvent:
    def test_progress_event(self, db_session, make_user, make_job):
        # Assemble
        make_user(user_id=1)
        job = make_job(user_id=1, status='PROCESSING')
        # Act
        service.update_job_from_event(job.id, {'type': 'progress', 'progress': 50}, db_session)
        # Assert
        updated = service.get_job(1, job.id, db_session)
        assert updated.progress == 50

    def test_completed_event(self, db_session, make_user, make_job):
        # Assemble
        make_user(user_id=1)
        job = make_job(user_id=1, status='PROCESSING')
        # Act
        service.update_job_from_event(job.id, {'type': 'completed', 's3_key': 'jobs/1/result.json'}, db_session)
        # Assert
        updated = service.get_job(1, job.id, db_session)
        assert updated.status == 'DONE'
        assert updated.s3_key == 'jobs/1/result.json'
        assert updated.progress == 100

    def test_failed_event(self, db_session, make_user, make_job):
        # Assemble
        make_user(user_id=1)
        job = make_job(user_id=1, status='PROCESSING')
        # Act
        service.update_job_from_event(job.id, {'type': 'failed'}, db_session)
        # Assert
        updated = service.get_job(1, job.id, db_session)
        assert updated.status == 'ERROR'

    def test_unknown_job_id_does_nothing(self, db_session):
        # Act + Assert — не кидає виняток
        service.update_job_from_event(9999, {'type': 'completed', 's3_key': 'x'}, db_session)
