from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from schemas import JobResponse, JobCreate, JobStatusUpdate
from datetime import datetime, timezone, timedelta
import service
import jwt
import uuid

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = 'e8864a5995f27034ffeb39d99f682c65ca1d93f355a8cb908b36e15dba122f99'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()

# configure OpenAPI security scheme for Swagger UI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title='SEO Analyzer',
        version='1.0.0',
        routes=app.routes,
    )
    openapi_schema['components']['securitySchemes'] = {
        'Bearer': {
            'type': 'http',
            'scheme': 'bearer',
        }
    }
    
    # mark protected routes as requiring Bearer token
    for path in openapi_schema['paths']:
        # skip /jobs-all and /token (public routes)
        if path not in ['/jobs-all', '/token']:
            for method in openapi_schema['paths'][path]:
                if method != 'parameters':
                    openapi_schema['paths'][path][method]['security'] = [{'Bearer': []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# create tables on startup
Base.metadata.create_all(bind=engine)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode['exp'] = expire
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.middleware('http')
async def auth_middleware(request: Request, call_next):
    request.state.user_id = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get('sub')
            if user_id is not None:
                request.state.user_id = int(user_id)
        except jwt.PyJWTError:
            pass
    return await call_next(request)


@app.get('/jobs-all')
def get_all_jobs(db: Session = Depends(get_db)) -> list[JobResponse]:
    return service.get_all_jobs(db)


@app.get('/jobs')
def get_jobs(request: Request, db: Session = Depends(get_db)) -> list[JobResponse]:
    if request.state.user_id is None:
        raise HTTPException(status_code=401, detail='Invalid token')
    if not service.userExists(request.state.user_id, db):
        raise HTTPException(status_code=404, detail='User not found')
    return service.get_jobs(request.state.user_id, db)


@app.get('/jobs/{job_id}')
def get_job(job_id: int, request: Request, db: Session = Depends(get_db)) -> JobResponse:
    if request.state.user_id is None:
        raise HTTPException(status_code=401, detail='Invalid token')
    if not service.userExists(request.state.user_id, db):
        raise HTTPException(status_code=404, detail='User not found')
    job = service.get_job(request.state.user_id, job_id, db)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return job


@app.post('/jobs')
def create_job(job_data: JobCreate, request: Request, db: Session = Depends(get_db)) -> JobResponse:
    if request.state.user_id is None:
        raise HTTPException(status_code=401, detail='Invalid token')
    if not service.userExists(request.state.user_id, db):
        raise HTTPException(status_code=404, detail='User not found')
    return service.create_job(request.state.user_id, job_data, db)


@app.patch('/jobs/{job_id}')
def update_job_status(job_id: int, status_update: JobStatusUpdate, request: Request, db: Session = Depends(get_db)) -> JobResponse:
    if request.state.user_id is None:
        raise HTTPException(status_code=401, detail='Invalid token')
    if not service.userExists(request.state.user_id, db):
        raise HTTPException(status_code=404, detail='User not found')
    
    try:
        job = service.update_job_status(request.state.user_id, job_id, status_update, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return job


@app.delete('/jobs/{job_id}')
def delete_job(job_id: int, request: Request, db: Session = Depends(get_db)) -> JobResponse:
    if request.state.user_id is None:
        raise HTTPException(status_code=401, detail='Invalid token')
    if not service.userExists(request.state.user_id, db):
        raise HTTPException(status_code=404, detail='User not found')
    
    job = service.delete_job(request.state.user_id, job_id, db)

    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return job


@app.post('/token')
def get_access_token(db: Session = Depends(get_db)) -> dict:
    # generate unique uid: convert UUID to int then cap to 31-bit range (0-2147483647)
    user_id = int(uuid.uuid4().int % (2**31 - 1))
    
    if not service.userExists(user_id, db):
        service.create_user(user_id, db)

    access_token = create_access_token(data={'sub': str(user_id)})
    return {'access_token': access_token, 'token_type': 'bearer'}

