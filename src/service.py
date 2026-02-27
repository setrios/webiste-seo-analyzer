from schemas import JobResponse, JobCreate, JobStatus, JobStatusUpdate, UserResponse
from database import Job, JobStatus as DBJobStatus
from database import User
from sqlalchemy import select
from sqlalchemy.orm import Session


# valid state transitions for the job
VALID_TRANSITIONS = {
    'CREATED': ['QUEUED'],
    'QUEUED': ['PROCESSING'],
    'PROCESSING': ['DONE', 'ERROR'],
    'DONE': [],
    'ERROR': []
}


def _job_to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        url=job.url,
        status=job.status,
        result=job.result,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat()
    )

def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username
    )


def create_user(user_id: int, db: Session) -> UserResponse:
    db_user = User(id=user_id, username=f'user_{user_id}')
    db.add(db_user)
    db.commit()
    db.refresh(db_user) 
    return _user_to_response(db_user)


def userExists(user_id: int, db: Session) -> bool:
    stmt = select(User).where(User.id == user_id)
    if db.scalars(stmt).first():
        return True
    return False


def get_jobs(user_id: int, db: Session) -> list[JobResponse]:
    stmt = select(Job).where(User.id == user_id)
    jobs = db.scalars(stmt).all()
    return [_job_to_response(job) for job in jobs]


def get_job(user_id: int, job_id: int, db: Session) -> JobResponse | None:
    stmt = select(Job).where(Job.user_id == user_id, Job.id == job_id)
    job = db.scalar(stmt)
    return _job_to_response(job) if job else None


def create_job(user_id: int, job_data: JobCreate, db: Session) -> JobResponse:
    db_job = Job(url=job_data.url, status=DBJobStatus.CREATED.value, user_id=user_id)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return _job_to_response(db_job)


def update_job_status(user_id: int, job_id: int, status_update: JobStatusUpdate, db: Session) -> JobResponse:
    stmt = select(Job).where(Job.user_id == user_id, Job.id == job_id)
    job = db.scalar(stmt)
    
    if not job:
        return None
    
    current_status = job.status
    new_status = status_update.status.value
    
    if new_status not in VALID_TRANSITIONS.get(current_status, []):
        raise ValueError(
            f'Invalid transition: {current_status} -> {new_status}. '
            f'Valid transitions: {VALID_TRANSITIONS[current_status]}'
        )
    
    job.status = new_status

    db.commit()
    db.refresh(job)
    return _job_to_response(job)


def delete_job(user_id: int, job_id: int, db: Session) -> JobResponse | None:
    stmt = select(Job).where(Job.user_id == user_id, Job.id == job_id)
    job = db.scalar(stmt)
    if job:
        db.delete(job)
        db.commit()
        return _job_to_response(job)