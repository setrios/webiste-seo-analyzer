from fastapi import FastAPI, Depends
from database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', reload=True)