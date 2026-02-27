from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from schemas import JobResponse, JobCreate, JobStatusUpdate
import service

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


# create tables on startup
Base.metadata.create_all(bind=engine)


@app.get('/jobs')
def get_jobs(db: Session = Depends(get_db)) -> list[JobResponse]:
    return service.get_jobs(db)


@app.get('/jobs/{job_id}')
def get_job(job_id: int, db: Session = Depends(get_db)) -> JobResponse:
    job = service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return job


@app.post('/jobs')
def create_job(job_data: JobCreate, db: Session = Depends(get_db)) -> JobResponse:
    return service.create_job(db, job_data)


@app.patch('/jobs/{job_id}')
def update_job_status(job_id: int, status_update: JobStatusUpdate, db: Session = Depends(get_db)) -> JobResponse:
    try:
        job = service.update_job_status(db, job_id, status_update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return job


@app.delete('/jobs/{job_id}')
def delete_job(job_id: int, db: Session = Depends(get_db)) -> JobResponse:
    job = service.delete_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return job

