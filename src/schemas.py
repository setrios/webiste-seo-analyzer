from pydantic import BaseModel


class JobCreate(BaseModel):
    url: str
    status: str
    result: str

class JobResponse(BaseModel):
    id: int
    url: str
    status: str
    result: str
    created_at: str
    updated_at: str
