from schemas import JobResponse, JobCreate
from database import Job
from sqlalchemy import select
from sqlalchemy.orm import Session


def get_jobs(db: Session) -> list[JobResponse]:
    stmt = select(Job)
    jobs = db.scalars(stmt).all()
    return [JobResponse(
        id=job.id,
        url=job.url,
        status=job.status,
        result=job.result,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat()
    ) for job in jobs]


def create_job(db: Session, job_data: JobCreate) -> JobResponse:
    db_job = Job(**job_data.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return JobResponse(
        id=db_job.id,
        url=db_job.url,
        status=db_job.status,
        result=db_job.result,
        created_at=db_job.created_at.isoformat(),
        updated_at=db_job.updated_at.isoformat()
    )


def delete_job(db: Session, job_id: int) -> bool:
    stmt = select(Job).where(Job.id == job_id)
    job = db.scalar(stmt)
    if job:
        db.delete(job)
        db.commit()
        return True
    return False