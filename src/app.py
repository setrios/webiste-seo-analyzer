from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from schemas import JobResponse, JobCreate, JobStatusUpdate
from datetime import datetime, timezone, timedelta
import asyncio
import json
import service
import jwt
import uuid

from contextlib import asynccontextmanager
import aio_pika
import os
from dotenv import load_dotenv

import boto3
from botocore.client import Config


load_dotenv()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def consume_events(queue: aio_pika.abc.AbstractQueue) -> None:
    async with queue.iterator() as it:
        async for message in it:
            async with message.process():
                event = json.loads(message.body)
                db = SessionLocal()
                try:
                    service.update_job_from_event(event['job_id'], event, db)
                finally:
                    db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: connect to RabbitMQ
    rabbitmq_url = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost/')
    connection = await aio_pika.connect_robust(rabbitmq_url)
    channel = await connection.channel()

    # create queue (if not exists)
    await channel.declare_queue('seo.request', durable=True)
    await channel.declare_queue('seo.events', durable=True)
    app.state.amqp_channel = channel
    app.state.amqp_connection = connection

    # start background consumer for worker events
    events_queue = await channel.get_queue('seo.events')
    consumer_task = asyncio.create_task(consume_events(events_queue))

    yield  # app itself starts here

    # shutdown
    consumer_task.cancel()
    await connection.close()


app = FastAPI(lifespan=lifespan)


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
    encoded_jwt = jwt.encode(to_encode, os.getenv('SECRET_KEY'), algorithm=os.getenv('ALGORITHM'))
    return encoded_jwt


@app.middleware('http')
async def auth_middleware(request: Request, call_next):
    request.state.user_id = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=[os.getenv('ALGORITHM')])
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


@app.get('/jobs/{job_id}/result')
def get_job_result(job_id: int, request: Request, db: Session = Depends(get_db)) -> dict:
    if request.state.user_id is None:
        raise HTTPException(status_code=401, detail='Invalid token')
    if not service.userExists(request.state.user_id, db):
        raise HTTPException(status_code=404, detail='Uset not found')

    job = service.get_job(request.state.user_id, job_id, db)

    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    if not job.s3_key:
        raise HTTPException(status_code=404, detail='Result not avaliable yet')

    s3 = boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY'),
        config=Config(signature_version='s3v4'),
    )
    presigned_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': os.getenv('MINIO_BUCKET'), 'Key': job.s3_key},
        ExpiresIn=3600,
    )
    return {'presigned_url': presigned_url}


@app.post('/jobs')
async def create_job(job_data: JobCreate, request: Request, db: Session = Depends(get_db)) -> JobResponse:
    if request.state.user_id is None:
        raise HTTPException(status_code=401, detail='Invalid token')
    if not service.userExists(request.state.user_id, db):
        raise HTTPException(status_code=404, detail='User not found')

    job = service.create_job(request.state.user_id, job_data, db)

    # publish to rabbitmq only if job just become QUEUED
    # (create only if not exist)
    if job.status == 'QUEUED':
        message_body = json.dumps({'job_id': job.id, 'url': job.url, 'user_id': job.user_id})
        await request.app.state.amqp_channel.default_exchange.publish(
            aio_pika.Message(
                body=message_body.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key='seo.request'
        )

    return job


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

