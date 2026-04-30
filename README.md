# SEO Analyzer

Full-stack application for SEO analysis of URLs with real-time updates.

- React frontend for job creation and monitoring
- REST API and WebSocket support
- Background worker analyzes pages: title, description, h1/h2/link counts
- Real-time job status and progress updates

## Tech stack

**Backend:**
- FastAPI, SQLAlchemy, SQLite
- RabbitMQ + aio-pika
- WebSocket support
- Python 3.14

**Frontend:**
- React 19 + Vite
- Bootstrap 5
- Axios for API calls

## Project structure

```
├── src/              # FastAPI backend
├── worker.py         # Background job processor
├── frontend/         # React application
├── main.py           # Backend entrypoint
└── requirements.txt  # Python dependencies
```

## Running

Requirements:

- Docker (for RabbitMQ, MinIO)
- Python venv with dependencies
- Node.js (for frontend)

```bash
# 1. Start Docker services
docker run -d --name rabbitmq -p 5672:5672 rabbitmq:3
docker run -d --name minio -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address :9001

# 2. Setup Python backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Setup frontend
cd frontend
npm install
cd ..

# 4. Run services (3 terminals)

# Terminal 1 - backend
source .venv/bin/activate
python main.py

# Terminal 2 - worker
source .venv/bin/activate
python worker.py

# Terminal 3 - frontend
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

## Usage

**Via Frontend (recommended):**
1. Open http://localhost:5173
2. Enter URL in the form
3. Watch job progress in real-time
4. View results when complete

**Via REST API:**
1. `POST /token` - get JWT token
2. `POST /jobs` with `{ "url": "https://example.com" }` - create job
3. `GET /jobs` - list all jobs
4. `GET /jobs/{id}` - check specific job status
5. `GET /jobs/{id}/result` - get presigned URL for result

**Via WebSocket:**
- `ws://localhost:8000/ws/jobs?token=<jwt_token>` - real-time job events

## Job lifecycle

```
QUEUED → PROCESSING → DONE → ERROR
```

Repeated `POST /jobs` with the same URL returns the existing active job (idempotency).
