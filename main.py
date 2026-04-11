import uvicorn
import sys
import os

# Lab 1
# Lab 2
# Lab 3
# Lab 4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == '__main__':
    uvicorn.run('src.app:app', reload=True)