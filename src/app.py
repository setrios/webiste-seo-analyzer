from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from schemas import JobResponse
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

