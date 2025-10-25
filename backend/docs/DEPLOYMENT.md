# Deployment Guide

This project is containerized. You can run backend and frontend together using the root `docker-compose.yml`, or the backend alone using `backend/docker-compose.yml`.

## Prerequisites
- Docker and Docker Compose
- A `.env` file for sensitive values (recommended)

## Services (root compose)
- MinIO (object storage): 9000 (S3) / 9001 (Console)
- Redis (cache/queues, planned usage): 6379
- Backend (FastAPI): 8000
- Frontend (Vite dev server): 3000

Environment variables (examples):
- Backend
  - SECRET_KEY=change-me
  - MONGO_DB_URI=mongodb+srv://<user>:<pass>@<host>/... (or mongodb://host:port)
  - MODEL_PATH=/app/model/dnabert_finetuned
  - MINIO_ENDPOINT=minio:9000
  - MINIO_ACCESS_KEY=minioadmin
  - MINIO_SECRET_KEY=minioadmin123
  - MINIO_SECURE=false
  - REDIS_URL=redis://redis:6379/0

Mounts and volumes:
- `./backend/data:/app/data`
- `./backend/model:/app/model` (for model bundles)

Health checks:
- Backend exposes `/health` for container health probes.

## Running (root)
- Start all: `docker compose up --build`
- Access API docs: http://localhost:8000/docs
- Access frontend (dev): http://localhost:3000

## Running backend only
From `backend/` use its compose file to run just the API:
- `docker compose up --build`

## Production notes
- Build a static frontend and serve via CDN or a reverse proxy rather than Vite dev server.
- Use managed MongoDB (e.g., Atlas) and secure secrets via environment or secret managers.
- Enable HTTPS and set appropriate CORS on the backend.
- Add Redis-backed workers for async pipelines and job orchestration.
- Persist artifacts in MinIO/S3 and version models via path naming or a simple registry collection in MongoDB.

## Diagram

docker-compose (root) topology:

```mermaid
graph LR
  FE[frontend:3000]\n(React dev) 
  BE[backend:8000]\n(FastAPI)
  MINIO[MinIO:9000/9001]
  REDIS[Redis:6379]
  VOL1[(./backend/data:/app/data)]
  VOL2[(./backend/model:/app/model)]

  FE -->|VITE_API_URL| BE
  BE --- VOL1
  BE --- VOL2
  BE --> MINIO
  BE --> REDIS
```