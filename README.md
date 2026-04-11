# SEO Analyzer

Backend service for SEO analysis of URLs.

- Accepts a URL via REST API
- Publishes a job to a RabbitMQ queue
- Background worker analyzes the page: title, description, h1/h2/link counts
- Job status and progress are updated in real time

## Tech stack

- FastAPI, SQLAlchemy, SQLite
- RabbitMQ + aio-pika
- Python 3.14

## Running

Requirements:

- Docker (for RabbitMQ)
- Python venv with dependencies

```bash
# RabbitMQ
docker run -d --name rabbitmq -p 5672:5672 rabbitmq:3

# venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# terminal 1 - backend
python main.py

# terminal 2 - worker
python worker.py
```

Swagger UI: http://localhost:8000/docs

## Usage

1. `POST /token` - get a token
2. `POST /jobs` with `{ "url": "https://example.com" }` - create a job
3. `GET /jobs/{id}` - check status and progress

## Job lifecycle

```
QUEUED → PROCESSING → DONE → ERROR
```

Repeated `POST /jobs` with the same URL returns the existing active job (idempotency).
