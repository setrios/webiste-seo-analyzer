from pydantic import BaseModel
from enum import Enum


class JobStatus(str, Enum):
    CREATED = 'CREATED'
    QUEUED = 'QUEUED'
    PROCESSING = 'PROCESSING'
    DONE = 'DONE'
    ERROR = 'ERROR'


class JobCreate(BaseModel):
    url: str

class JobStatusUpdate(BaseModel):
    status: JobStatus

class JobResponse(BaseModel):
    id: int
    url: str
    status: str
    s3_key: str | None
    progress: int
    created_at: str
    updated_at: str
    user_id: int


class UserResponse(BaseModel):
    id: int
    username: str