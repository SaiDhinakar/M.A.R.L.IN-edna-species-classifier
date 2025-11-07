# M.A.R.L.IN eDNA Classifier - Backend API

AI-driven eDNA (environmental DNA) classification system with complete MLOps pipeline using ZenML, MLflow, FAISS, and FastAPI.

## 🚀 Features

- **User Authentication**: JWT-based auth with role-based access (user/admin)
- **Dataset Management**: Upload, validate, and track .tar.gz datasets
- **Training Pipeline**: Automated ZenML pipeline with:
  - Data extraction and preprocessing
  - DNA sequence embedding (k-mer based)
  - HDBSCAN clustering
  - FAISS vector indexing
  - MLflow experiment tracking
- **Model Inference**: Real-time DNA sequence classification with Redis caching
- **Search & Query**: FAISS-based similarity search and metadata filtering
- **Visualization**: Biodiversity metrics (Shannon/Simpson indices) and cluster analytics

## 🏗️ Architecture

```
Backend/
├── app/
│   ├── api/          # API endpoints (auth, data, admin, model, search, visualize)
│   ├── core/         # Config, security, dependencies
│   ├── database/     # SQLite session management
│   ├── models/       # Database models & Pydantic schemas
│   └── services/     # Business logic (MinIO, Redis, MLflow, FAISS, training, inference)
├── data/             # Local data storage
├── main.py           # FastAPI application
├── pyproject.toml    # Dependencies
└── Dockerfile        # Container image
```

## 📦 Tech Stack

- **Framework**: FastAPI 0.115+
- **ML/AI**: PyTorch, FAISS, HDBSCAN, BioPython
- **MLOps**: ZenML 0.70+, MLflow 2.17+
- **Storage**: MinIO (S3-compatible), Redis, SQLite, PostgreSQL
- **Authentication**: JWT (python-jose)

## 🔧 Setup & Installation

### Prerequisites

Ensure infrastructure services are running:
```bash
cd ../infra
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- MinIO (ports 9000, 9001)
- Nginx (ports 80, 443)

### Install Dependencies

```bash
cd backend
pip install -e .
```

### Configure Environment

Copy and edit the environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Initialize Database

The database will be automatically initialized on first run. Tables created:
- `users` - User accounts
- `datasets` - Uploaded datasets
- `models` - Trained model metadata
- `training_runs` - Pipeline execution records
- `sequences` - DNA sequence metadata
- `cluster_metadata` - Cluster statistics

### Run Development Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - Register new user
- `POST /login` - Login and get JWT token
- `GET /me` - Get current user info

### Datasets (`/api/v1/dataset`)
- `POST /upload` - Upload .tar.gz dataset
- `GET /list` - List user's datasets
- `GET /{dataset_id}` - Get dataset details
- `DELETE /{dataset_id}` - Delete dataset

### Admin (`/api/v1/admin`)
- `GET /datasets/pending` - List pending datasets
- `POST /datasets/{dataset_id}/approve` - Approve dataset
- `POST /train` - Trigger training pipeline
- `GET /training-runs` - List training runs
- `GET /training-runs/{run_id}` - Get training run details

### Model (`/api/v1/model`)
- `POST /infer` - Classify DNA sequence
- `GET /versions` - List model versions
- `GET /info` - Get loaded model info
- `POST /load/{model_id}` - Load specific model

### Search (`/api/v1/search`)
- `POST /query` - Search sequences by taxonomy/cluster/ID
- `GET /clusters` - List all clusters
- `GET /taxonomies` - List unique taxonomies

### Visualization (`/api/v1/visualize`)
- `GET /summary` - Get biodiversity metrics
- `GET /cluster/{cluster_id}` - Get cluster details
- `GET /dataset/{dataset_id}/stats` - Get dataset statistics

## 🔐 Authentication

All endpoints (except `/auth/register` and `/auth/login`) require JWT authentication.

1. Register or login to get token:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

2. Use token in subsequent requests:
```bash
curl http://localhost:8000/api/v1/dataset/list \
  -H "Authorization: Bearer <your_token>"
```

## 🧪 Example Workflow

### 1. Create Admin User (First Time)
```python
# Run in Python shell
from app.database.session import SessionLocal
from app.models.database_models import User
from app.core.security import get_password_hash

db = SessionLocal()
admin = User(
    username="admin",
    email="admin@example.com",
    hashed_password=get_password_hash("admin123"),
    role="admin",
    is_active=True
)
db.add(admin)
db.commit()
```

### 2. Upload Dataset
```bash
curl -X POST http://localhost:8000/api/v1/dataset/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@16S_ribosomal_RNA.tar.gz" \
  -F "description=Marine eDNA sample" \
  -F "sample_location=Pacific Ocean"
```

### 3. Approve Dataset (Admin)
```bash
curl -X POST http://localhost:8000/api/v1/admin/datasets/1/approve \
  -H "Authorization: Bearer <admin_token>"
```

### 4. Train Model (Admin)
```bash
curl -X POST http://localhost:8000/api/v1/admin/train \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_ids": [1],
    "model_name": "marine_classifier_v1",
    "hyperparameters": {
      "batch_size": 32,
      "min_cluster_size": 5
    }
  }'
```

### 5. Classify Sequence
```bash
curl -X POST http://localhost:8000/api/v1/model/infer \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": "ATGCTAGCTAGCTAGCTAG",
    "top_k": 5
  }'
```

## 🐳 Docker Deployment

Build and run with Docker:

```bash
# Build image
docker build -t marlin-backend .

# Run container
docker run -d \
  --name marlin-backend \
  --env-file .env \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  marlin-backend
```

Or use docker-compose from project root:
```bash
docker-compose up -d backend
```

## 🔍 Monitoring & Logging

- **Application Logs**: Check container logs `docker logs marlin-backend`
- **MLflow UI**: Access at http://localhost:5000 (if MLflow server running)
- **MinIO Console**: Access at http://localhost:9001 (credentials: minioadmin/minioadmin)
- **Health Check**: `curl http://localhost:8000/health`

## 📊 Data Storage

- **SQLite**: `./data/app.db` - Metadata and user data
- **MinIO Buckets**:
  - `raw-datasets/` - Uploaded .tar.gz files
  - `processed/` - Processed sequences
  - `models/` - Model artifacts and FAISS indices
  - `logs/` - Pipeline logs
- **Redis**: Cached inference results (TTL: 1 hour)

## 🧬 Training Pipeline

The ZenML pipeline includes these steps:

1. **Load Data**: Extract sequences from .tar.gz
2. **Preprocess**: Filter by length, remove invalid sequences
3. **Embed**: Generate k-mer based embeddings (6-mer frequency vectors)
4. **Cluster**: HDBSCAN clustering to find OTUs
5. **Index**: Build FAISS index for similarity search
6. **Metrics**: Calculate biodiversity indices
7. **Log**: Track metrics in MLflow
8. **Save**: Store results in MinIO

## 🛠️ Development

### Run Tests
```bash
pytest
```

### Code Formatting
```bash
black app/
ruff check app/
```

### Database Migrations
```bash
# If using Alembic
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## 🐛 Troubleshooting

### MinIO Connection Error
- Ensure MinIO container is running: `docker ps | grep minio`
- Check MinIO is accessible: `curl http://localhost:9000/minio/health/live`

### Redis Connection Error
- Ensure Redis container is running: `docker ps | grep redis`
- Test connection: `redis-cli ping`

### Database Locked Error
- SQLite doesn't handle concurrent writes well
- Consider upgrading to PostgreSQL for production

### Import Errors
- Reinstall dependencies: `pip install -e .`
- Check Python version: `python --version` (requires 3.12+)

## 📝 TODO

- [ ] Implement PostgreSQL vector extension for FAISS
- [ ] Add BLAST integration for taxonomy assignment
- [ ] Implement model versioning UI
- [ ] Add batch inference endpoint
- [ ] Implement ZenML server integration
- [ ] Add Celery for background tasks
- [ ] Implement data streaming for large files
- [ ] Add comprehensive test suite
- [ ] Add API rate limiting
- [ ] Implement audit logging

## 📄 License

[Your License Here]

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 📧 Contact

For questions and support, contact: [your-email@example.com]
