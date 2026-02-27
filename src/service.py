from schemas import JobResponse, JobCreate, JobStatus, JobStatusUpdate
from database import Job, JobStatus as DBJobStatus
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


def get_jobs(db: Session) -> list[JobResponse]:
    stmt = select(Job)
    jobs = db.scalars(stmt).all()
    return [_job_to_response(job) for job in jobs]


def get_job(db: Session, job_id: int) -> JobResponse | None:
    stmt = select(Job).where(Job.id == job_id)
    job = db.scalar(stmt)
    return _job_to_response(job) if job else None


def create_job(db: Session, job_data: JobCreate) -> JobResponse:
    db_job = Job(url=job_data.url, status=DBJobStatus.CREATED.value)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return _job_to_response(db_job)


def update_job_status(db: Session, job_id: int, status_update: JobStatusUpdate) -> JobResponse:
    stmt = select(Job).where(Job.id == job_id)
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


def delete_job(db: Session, job_id: int) -> JobResponse | None:
    stmt = select(Job).where(Job.id == job_id)
    job = db.scalar(stmt)
    if job:
        db.delete(job)
        db.commit()
        return _job_to_response(job)