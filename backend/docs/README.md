# eDNA Species Classifier – Documentation Hub

Welcome to the documentation for the eDNA Species Classifier project. This backend powers AI-driven analysis of environmental DNA to identify taxa and assess biodiversity, while the frontend provides an interactive dashboard for admins and users.

- Tech stack (FARM): FastAPI (Backend), React + Vite + Tailwind (Frontend), MongoDB (Database), Redis (Caching/Jobs – planned)
- Containerization: Docker with separate frontend and backend services; optional MinIO object storage; Redis planned
- Pipelines: Training and Deployment pipelines orchestrate data ingestion to inference

Quick links:
- Overview: ./OVERVIEW.md
- Architecture: ./ARCH.md
- Pipelines and Workflow: ./WORKFLOW.md
- Model Summary: ./ML_MODEL.md
- API Reference: ./API.md
- Security and Auth: ./SECURITY.md
- Deployment Guide: ./DEPLOYMENT.md
- References: ./REFERENCE.md

Repository structure (relevant parts):
- backend/main.py – FastAPI app
- backend/src/ – API routes, services, models, and database client
- backend/pipelines/ – ML pipeline entry points (under construction)
- backend/notebooks/ – Data science notebooks (preprocessing → evaluation)
- frontend/ – React + Tailwind UI

If you’re new, read Overview and Architecture first, then Pipelines, then API/Deployment.

## Diagrams

Brief visuals to make the setup transparent to contributors.

Architecture (containers and data flow):

```mermaid
graph LR
	subgraph Client
		U[User/Admin]
	end

	subgraph Frontend
		FE[React + Vite + Tailwind]
	end

	subgraph Backend
		BE[FastAPI]
	end

	subgraph Infra
		DB[(MongoDB)]
		R[(Redis - planned)]
		S3[(MinIO/S3 - optional)]
	end

	U --> FE --> BE
	BE --> DB
	BE --> R
	BE --> S3
```

Sequence – inference (planned endpoints):

```mermaid
sequenceDiagram
	participant User
	participant FE as Frontend
	participant BE as Backend (FastAPI)
	participant R as Redis (planned)
	participant DB as MongoDB

	User->>FE: Submit sequences
	FE->>BE: POST /inference/classify
	BE->>R: Check cache (optional)
	R-->>BE: Hit/Miss
	BE->>BE: Preprocess + Embed + Classify
	BE->>DB: Log request/metrics
	BE-->>FE: Predictions + confidences
	FE-->>User: Show results
```

Sequence – admin training trigger (planned):

```mermaid
sequenceDiagram
	participant Admin
	participant FE as Frontend
	participant BE as Backend
	participant S3 as MinIO/S3
	participant R as Redis (queue)
	participant W as Worker (future)
	participant DB as MongoDB

	Admin->>FE: Upload dataset
	FE->>BE: POST /datasets (planned)
	BE->>S3: Store raw files
	BE->>R: Enqueue training job
	W->>S3: Read dataset
	W->>W: Preprocess → Embed → Cluster → Train → Eval → Package
	W->>S3: Write model bundle
	W->>DB: Update job & model metadata
	W-->>BE: Job complete (status)
```