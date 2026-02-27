from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from schemas import JobResponse, JobCreate, JobStatusUpdate
from datetime import datetime, timezone, timedelta
import service
import jwt

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = 'e8864a5995f27034ffeb39d99f682c65ca1d93f355a8cb908b36e15dba122f99'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_from_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get('sub')
        if user_id is None:
            raise HTTPException(status_code=401, detail='Invalid token')
        return int(user_id)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail='Invalid token')


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
def get_jobs(user_id: int = Depends(get_user_from_token), db: Session = Depends(get_db)) -> list[JobResponse]:
    if not service.userExists(user_id, db):
        raise HTTPException(status_code=404, detail='User not found')
    return service.get_jobs(user_id, db)


@app.get('/jobs/{job_id}')
def get_job(job_id: int, user_id: int = Depends(get_user_from_token), db: Session = Depends(get_db)) -> JobResponse:
    if not service.userExists(user_id, db):
        raise HTTPException(status_code=404, detail='User not found')
    job = service.get_job(user_id, job_id, db)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return job


@app.post('/jobs')
def create_job(job_data: JobCreate, user_id: int = Depends(get_user_from_token), db: Session = Depends(get_db)) -> JobResponse:
    if not service.userExists(user_id, db):
        raise HTTPException(status_code=404, detail='User not found')
    return service.create_job(user_id, job_data, db)


@app.patch('/jobs/{job_id}')
def update_job_status(job_id: int, status_update: JobStatusUpdate, user_id: int = Depends(get_user_from_token), db: Session = Depends(get_db)) -> JobResponse:
    if not service.userExists(user_id, db):
        raise HTTPException(status_code=404, detail='User not found')
    
    try:
        job = service.update_job_status(user_id, job_id, status_update, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return job


@app.delete('/jobs/{job_id}')
def delete_job(job_id: int, user_id: int = Depends(get_user_from_token), db: Session = Depends(get_db)) -> JobResponse:
    if not service.userExists(user_id, db):
        raise HTTPException(status_code=404, detail='User not found')
    
    job = service.delete_job(user_id, job_id, db)

    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return job


@app.post('/token')
def login_for_access_token(user_id: int, db: Session = Depends(get_db)) -> dict:
    if not service.userExists(user_id, db):
        service.create_user(user_id, db)

    access_token = create_access_token(data={'sub': str(user_id)})
    return {'access_token': access_token, 'token_type': 'bearer'}

