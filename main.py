import uvicorn

# Lab 1

if __name__ == '__main__':
    uvicorn.run('src.app:app', reload=True)