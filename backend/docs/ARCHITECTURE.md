#   🏗️ M.A.R.L.IN Backend Architecture

## System Overview

┌─────────────────────────────────────────────────────────────────┐
│              					           Frontend (React)          							         │
│                   						 http://localhost:5173						                         │
└────────────────────────────┬────────────────────────────────────┘
                          						  │ HTTP/REST API
                          						  │ JWT Authentication
                                                                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                					    FastAPI Backend (main.py)               	                 				 │
│                						    http://localhost:8000   			        			                 │
│  ┌────────────────────────────────────────────────────────────┐       │
│  │                     API Layer                             											│	  |
│  │  • /auth      - Authentication & Authorization             									│	  |
│  │  • /dataset   - Dataset Upload & Management                									│	  |
│  │  • /admin     - Training Pipeline Control               										│	  |
│  │  • /model     - Inference & Prediction                     │ │
│  │  • /search    - Sequence Search                            │ │
│  │  • /visualize - Biodiversity Metrics                       │ │
│  └─────────────────────┬──────────────────────────────────────┘ │
│                        │                                          │
│  ┌─────────────────────┴──────────────────────────────────────┐ │
│  │                   Service Layer                             │ │
│  │  • MinioService     - Object Storage                       │ │
│  │  • RedisService     - Caching                              │ │
│  │  • MLflowService    - Experiment Tracking                  │ │
│  │  • EmbeddingService - DNA → Vector                         │ │
│  │  • FAISSIndexer     - Vector Search                        │ │
│  │  • TrainingPipeline - ML Orchestration (ZenML)             │ │
│  │  • InferenceService - Real-time Prediction                 │ │
│  └─────────────────────┬──────────────────────────────────────┘ │
│                        │                                          │
│  ┌─────────────────────┴──────────────────────────────────────┐ │
│  │                   Core Layer                                │ │
│  │  • Config  - Environment Variables                         │ │
│  │  • Security - JWT, Password Hashing                        │ │
│  │  • Dependencies - DI Container                             │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────┬─────────────────────────────────┬────────────────┘
               │                                 │
    ┌──────────┴──────────┐       ┌─────────────┴─────────────┐
    │   Storage Layer     │       │    ML/Data Layer          │
    └─────────────────────┘       └───────────────────────────┘
               │                                 │
    ┌──────────┼──────────┐       ┌─────────────┼─────────────┐
    │          │          │       │             │             │
    ▼          ▼          ▼       ▼             ▼             ▼
┌───────┐ ┌────────┐ ┌──────┐ ┌──────┐    ┌────────┐   ┌──────┐
│SQLite │ │ Redis  │ │MinIO │ │ZenML │    │ MLflow │   │FAISS │
│  DB   │ │ Cache  │ │  S3  │ │Pipe. │    │ Track  │   │Index │
└───────┘ └────────┘ └──────┘ └──────┘    └────────┘   └──────┘

---

## Data Flow Diagrams

### 1️⃣ User Registration & Authentication

```
User                FastAPI              Database
 │                     │                     │
 │──register────────>│                     │
 │                     │──hash_password───>│
 │                     │──save_user───────>│
 │                     │<─user_created─────│
 │<──201 Created──────│                     │
 │                     │                     │
 │──login───────────>│                     │
 │                     │──verify_password──>│
 │                     │<─user_validated───│
 │                     │──create_jwt───────>│
 │<──JWT Token────────│                     │
 │                     │                     │
 │──/me──────────────>│                     │
 │ (Authorization:     │──decode_jwt───────>│
 │  Bearer <token>)    │──get_user────────>│
 │                     │<─user_info────────│
 │<──User Info────────│                     │
```

### 2️⃣ Dataset Upload & Processing

```
User          FastAPI        MinIO       Database
 │                │             │            │
 │──upload file──>│             │            │
 │                │──hash───────>│            │
 │                │──check_dup──────────────>│
 │                │<─no duplicate─────────────│
 │                │──store_file──>│            │
 │                │<─s3_key───────│            │
 │                │──save_metadata───────────>│
 │                │<─dataset_id───────────────│
 │<─202 Accepted──│             │            │
```

### 3️⃣ Training Pipeline (Admin)

```
Admin     FastAPI      Database    ZenML       MLflow      MinIO      FAISS
  │          │            │          │            │          │          │
  │─approve─>│            │          │            │          │          │
  │          │─update────>│          │            │          │          │
  │<─200 OK──│            │          │            │          │          │
  │          │            │          │            │          │          │
  │─train───>│            │          │            │          │          │
  │          │─create_run─>│          │            │          │          │
  │<─202──────│            │          │            │          │          │
  │          │            │          │            │          │          │
  │      [Background Task]            │            │          │          │
  │          │─status:running────────>│            │          │          │
  │          │─start_pipeline────────>│            │          │          │
  │          │            │            │            │          │          │
  │          │            │      ┌─────┴─────┐      │          │          │
  │          │            │      │ Pipeline  │      │          │          │
  │          │            │      │  Steps:   │      │          │          │
  │          │            │      │           │      │          │          │
  │          │            │      │1. Load────────────────────>│          │
  │          │            │      │   ├─download_tar───────────>│          │
  │          │            │      │   └─parse_fasta            │          │
  │          │            │      │                            │          │
  │          │            │      │2. Preprocess               │          │
  │          │            │      │   ├─filter_length          │          │
  │          │            │      │   └─validate               │          │
  │          │            │      │                            │          │
  │          │            │      │3. Embed                    │          │
  │          │            │      │   ├─kmer_vectorize         │          │
  │          │            │      │   └─batch_process          │          │
  │          │            │      │                            │          │
  │          │            │      │4. Cluster                  │          │
  │          │            │      │   └─HDBSCAN                │          │
  │          │            │      │                            │          │
  │          │            │      │5. Index────────────────────────────────>│
  │          │            │      │   ├─create_faiss_index     │          │
  │          │            │      │   └─add_vectors            │          │
  │          │            │      │                            │          │
  │          │            │      │6. Metrics                  │          │
  │          │            │      │   ├─shannon_diversity      │          │
  │          │            │      │   └─simpson_diversity      │          │
  │          │            │      │                            │          │
  │          │            │      │7. Log──────────────────────>│          │
  │          │            │      │   ├─experiment             │          │
  │          │            │      │   ├─parameters             │          │
  │          │            │      │   ├─metrics                │          │
  │          │            │      │   └─artifacts──────────────────────────>│
  │          │            │      │                            │          │
  │          │            │      │8. Save─────────────────────────────────>│
  │          │            │      │   ├─embeddings.parquet     │          │
  │          │            │      │   ├─clusters.parquet       │          │
  │          │            │      │   └─faiss.index            │          │
  │          │            │      └───────────┘                │          │
  │          │            │            │                      │          │
  │          │─save_metadata──────────>│                      │          │
  │          │─status:completed───────>│                      │          │
```

### 4️⃣ Inference & Search

```
User      FastAPI    Redis     FAISS      Database
 │           │         │         │            │
 │─infer────>│         │         │            │
 │           │─hash────>│         │            │
 │           │─check───>│         │            │
 │           │<─miss────│         │            │
 │           │                   │            │
 │           │─embed_sequence───>│            │
 │           │─search───────────>│            │
 │           │<─top_k_results────│            │
 │           │                               │
 │           │─get_cluster_info─────────────>│
 │           │<─taxonomy+metadata────────────│
 │           │                               │
 │           │─cache_result────>│            │
 │           │                               │
 │<─results──│         │         │            │
 │           │         │         │            │
 │─infer────>│         │         │            │
 │  (same    │─check───>│         │            │
 │   seq)    │<─HIT!────│         │            │
 │<─cached───│         │         │            │
```

---

## Component Details

### API Layer (`app/api/`)

| Router                 | Endpoints | Purpose                                    |
| ---------------------- | --------- | ------------------------------------------ |
| **auth.py**      | 4         | User registration, login, token management |
| **data.py**      | 5         | Dataset upload, listing, deletion          |
| **admin.py**     | 5         | Dataset approval, training triggers        |
| **model.py**     | 4         | Model inference, version management        |
| **search.py**    | 3         | Sequence search by taxonomy/cluster        |
| **visualize.py** | 3         | Biodiversity metrics & statistics          |

### Service Layer (`app/services/`)

```
┌──────────────────────────────────────────────────────────────┐
│                       MinioService                           │
│  • upload_file()      - Store datasets/models/logs          │
│  • download_file()    - Retrieve stored objects             │
│  • get_presigned_url()- Generate temp download links        │
│  • list_objects()     - Browse bucket contents              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                       RedisService                           │
│  • set_cache()        - Store with TTL (1 hour default)     │
│  • get_cache()        - Retrieve cached data                │
│  • delete_cache()     - Invalidate cache                    │
│  • health_check()     - Verify connection                   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                       MLflowService                          │
│  • create_experiment()- Initialize tracking                 │
│  • start_run()        - Begin training run                  │
│  • log_params()       - Record hyperparameters              │
│  • log_metrics()      - Store accuracy/loss/diversity       │
│  • log_artifact()     - Save models/plots/data              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    EmbeddingService                          │
│  • embed_sequence()   - DNA → 768-dim vector (k-mer)       │
│  • embed_sequences()  - Batch processing                    │
│  • compute_similarity()- Cosine similarity                  │
│  • _sequence_to_kmers()- Sliding window tokenization        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                       FAISSIndexer                           │
│  • create_index()     - Initialize IndexFlatL2 + IDMap     │
│  • add_vectors()      - Insert embeddings with IDs          │
│  • search()           - k-NN similarity search              │
│  • save_index()       - Persist to MinIO                    │
│  • load_index()       - Restore from storage                │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    InferenceService                          │
│  • infer()            - Predict taxonomy (with caching)     │
│  • batch_infer()      - Multiple sequences at once          │
│  • load_model()       - Initialize from model ID            │
│  • _compute_hash()    - SHA256 for cache keys               │
└──────────────────────────────────────────────────────────────┘
```

### Training Pipeline (`app/services/training_pipeline.py`)

```
                    ZenML Pipeline Orchestration
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  @pipeline(name="edna_training_pipeline")              ┃
┃                                                         ┃
┃  Step 1: Load Data                                      ┃
┃  ├─ Download from MinIO (tar.gz)                       ┃
┃  ├─ Extract files                                       ┃
┃  ├─ Parse FASTA/FASTQ                                   ┃
┃  └─ Output: List[Dict] (sequence data)                 ┃
┃                                                         ┃
┃  Step 2: Preprocess                                     ┃
┃  ├─ Filter by length (min/max)                         ┃
┃  ├─ Remove invalid sequences                           ┃
┃  ├─ Deduplicate                                         ┃
┃  └─ Output: Cleaned sequences                          ┃
┃                                                         ┃
┃  Step 3: Embed                                          ┃
┃  ├─ K-mer extraction (6-mer)                           ┃
┃  ├─ Frequency vectorization (4^6 = 4096)               ┃
┃  ├─ Normalize & pad to 768 dims                        ┃
┃  └─ Output: np.ndarray (N × 768)                       ┃
┃                                                         ┃
┃  Step 4: Cluster                                        ┃
┃  ├─ HDBSCAN (min_cluster_size, min_samples)            ┃
┃  ├─ Automatic outlier detection                        ┃
┃  ├─ Cluster labels assignment                          ┃
┃  └─ Output: cluster_labels                             ┃
┃                                                         ┃
┃  Step 5: Index                                          ┃
┃  ├─ Create FAISS IndexFlatL2                           ┃
┃  ├─ Wrap with IndexIDMap                               ┃
┃  ├─ Add embeddings with sequence IDs                   ┃
┃  └─ Output: faiss_index                                ┃
┃                                                         ┃
┃  Step 6: Calculate Metrics                             ┃
┃  ├─ Shannon diversity: H' = -Σ(p_i × ln(p_i))         ┃
┃  ├─ Simpson diversity: D = 1 - Σ(p_i²)                ┃
┃  ├─ Cluster statistics                                 ┃
┃  └─ Output: metrics dict                               ┃
┃                                                         ┃
┃  Step 7: Log to MLflow                                  ┃
┃  ├─ Create experiment                                   ┃
┃  ├─ Log hyperparameters                                ┃
┃  ├─ Log metrics                                         ┃
┃  ├─ Save artifacts (index, embeddings, plots)          ┃
┃  └─ Register model                                      ┃
┃                                                         ┃
┃  Step 8: Save Results                                   ┃
┃  ├─ embeddings.parquet → MinIO                         ┃
┃  ├─ clusters.parquet → MinIO                           ┃
┃  ├─ faiss_index.bin → MinIO                            ┃
┃  ├─ metadata.json → MinIO                              ┃
┃  └─ Update database records                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## Database Schema

### SQLite Schema (`app.db`)

```sql
┌─────────────────────────────────────────────────────────────┐
│                           users                             │
├─────────────────────────────────────────────────────────────┤
│ id (PK)          INTEGER                                    │
│ username         VARCHAR(50) UNIQUE NOT NULL                │
│ email            VARCHAR(100) UNIQUE NOT NULL               │
│ hashed_password  VARCHAR(255) NOT NULL                      │
│ role             VARCHAR(10) DEFAULT 'user'                 │
│ is_active        BOOLEAN DEFAULT TRUE                       │
│ created_at       DATETIME DEFAULT CURRENT_TIMESTAMP         │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         datasets                            │
├─────────────────────────────────────────────────────────────┤
│ id (PK)             INTEGER                                 │
│ user_id (FK)        INTEGER → users.id                      │
│ filename            VARCHAR(255) NOT NULL                   │
│ original_filename   VARCHAR(255) NOT NULL                   │
│ file_hash           VARCHAR(64) UNIQUE NOT NULL             │
│ file_size           INTEGER NOT NULL                        │
│ upload_date         DATETIME DEFAULT CURRENT_TIMESTAMP      │
│ status              VARCHAR(20) DEFAULT 'uploaded'          │
│ description         TEXT                                    │
│ sample_location     VARCHAR(255)                            │
│ sample_date         DATETIME                                │
│ sample_depth        FLOAT                                   │
│ metadata_json       JSON                                    │
│ minio_key           VARCHAR(500) NOT NULL                   │
│ approved_by         INTEGER → users.id                      │
│ approved_at         DATETIME                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ N:M
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       training_runs                         │
├─────────────────────────────────────────────────────────────┤
│ id (PK)             INTEGER                                 │
│ user_id (FK)        INTEGER → users.id                      │
│ model_id (FK)       INTEGER → models.id                     │
│ run_name            VARCHAR(255) NOT NULL                   │
│ start_time          DATETIME DEFAULT CURRENT_TIMESTAMP      │
│ end_time            DATETIME                                │
│ status              VARCHAR(20) DEFAULT 'initiated'         │
│ hyperparameters     JSON                                    │
│ dataset_ids         JSON (array)                            │
│ error_log           TEXT                                    │
│ mlflow_run_id       VARCHAR(255)                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1:1
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                          models                             │
├─────────────────────────────────────────────────────────────┤
│ id (PK)             INTEGER                                 │
│ model_name          VARCHAR(255) UNIQUE NOT NULL            │
│ model_version       VARCHAR(50) NOT NULL                    │
│ created_at          DATETIME DEFAULT CURRENT_TIMESTAMP      │
│ mlflow_run_id       VARCHAR(255)                            │
│ faiss_index_path    VARCHAR(500)                            │
│ embedding_dim       INTEGER DEFAULT 768                     │
│ total_sequences     INTEGER                                 │
│ num_clusters        INTEGER                                 │
│ metrics             JSON                                    │
│ is_active           BOOLEAN DEFAULT TRUE                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        sequences                            │
├─────────────────────────────────────────────────────────────┤
│ id (PK)             INTEGER                                 │
│ model_id (FK)       INTEGER → models.id                     │
│ sequence_id         VARCHAR(255) NOT NULL                   │
│ sequence_data       TEXT NOT NULL                           │
│ sequence_length     INTEGER NOT NULL                        │
│ taxonomy            VARCHAR(500)                            │
│ cluster_id          INTEGER                                 │
│ confidence          FLOAT                                   │
│ embedding_json      JSON (optional)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ N:1
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    cluster_metadata                         │
├─────────────────────────────────────────────────────────────┤
│ id (PK)             INTEGER                                 │
│ model_id (FK)       INTEGER → models.id                     │
│ cluster_id          INTEGER NOT NULL                        │
│ num_sequences       INTEGER NOT NULL                        │
│ representative_seq  VARCHAR(255)                            │
│ avg_confidence      FLOAT                                   │
│ dominant_taxonomy   VARCHAR(500)                            │
│ metadata_json       JSON                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Authentication Flow

```
1. User Registration
   └─> Password → bcrypt hash (cost=12) → Database

2. User Login
   ├─> Verify password (bcrypt.checkpw)
   └─> Generate JWT token
       ├─ Header: {"alg": "HS256", "typ": "JWT"}
       ├─ Payload: {"sub": username, "role": "user", "exp": 24h}
       └─ Signature: HMAC-SHA256(header.payload, SECRET_KEY)

3. Protected Endpoints
   ├─> Extract token from Authorization: Bearer <token>
   ├─> Decode & verify JWT (jose.jwt.decode)
   ├─> Check expiration
   ├─> Verify user exists & is_active
   └─> Inject user into request context

4. Role-Based Access
   ├─> User role = "user"
   │   └─> Can: upload, view own data, inference
   └─> User role = "admin"
       └─> Can: approve datasets, trigger training, view all data
```

### Data Protection

```
┌────────────────────────────────────────────────────────────┐
│                   Security Layers                          │
├────────────────────────────────────────────────────────────┤
│ 1. Transport Layer                                         │
│    • HTTPS (production)                                    │
│    • CORS (restricted origins)                             │
│                                                            │
│ 2. Authentication Layer                                    │
│    • JWT tokens (24h expiry)                               │
│    • Bcrypt password hashing (cost=12)                     │
│    • Token refresh mechanism                               │
│                                                            │
│ 3. Authorization Layer                                     │
│    • Role-based access control                             │
│    • Resource ownership validation                         │
│    • Admin-only endpoints                                  │
│                                                            │
│ 4. Data Layer                                              │
│    • File hash verification (SHA-256)                      │
│    • Duplicate detection                                   │
│    • Input validation (Pydantic schemas)                   │
│                                                            │
│ 5. Storage Layer                                           │
│    • MinIO access keys                                     │
│    • Redis password                                        │
│    • Database encryption (at rest)                         │
└────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Development

```
┌──────────────────────────────────────────────────────────┐
│                    Development Setup                     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Backend (localhost:8000)                                │
│  ├─ Uvicorn --reload                                     │
│  └─ SQLite (./data/app.db)                               │
│                                                          │
│  Infrastructure (Docker Compose)                         │
│  ├─ PostgreSQL (localhost:5432)                          │
│  ├─ Redis (localhost:6379)                               │
│  ├─ MinIO (localhost:9000, console:9001)                 │
│  └─ Nginx (localhost:80)                                 │
│                                                          │
│  Frontend (localhost:5173)                               │
│  └─ Vite dev server                                      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Production

```
┌─────────────────────────────────────────────────────────────┐
│                         Cloud Load Balancer                 │
│                         (AWS ALB / GCP LB)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴────────────┐
         │                        │
    ┌────▼────┐             ┌─────▼────┐
    │Frontend │             │ Backend  │
    │ (CDN)   │             │ (K8s)    │
    │         │             │ 3 replicas│
    │ React   │             │ FastAPI  │
    │ Build   │             │ Uvicorn  │
    └─────────┘             └─────┬────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
         ┌────▼────┐         ┌────▼────┐        ┌────▼────┐
         │ RDS     │         │ Redis   │        │ S3      │
         │(Postgres│         │ElastiCache│      │(Storage)│
         └─────────┘         └─────────┘        └─────────┘
```

---

## Performance Optimization

### Caching Strategy

```
Level 1: Redis Cache (Hot Data)
├─ Inference results (1 hour TTL)
├─ User sessions (24 hour TTL)
└─ Frequently accessed metadata (15 min TTL)

Level 2: Application Cache
├─ FAISS index in memory
├─ Model artifacts loaded once
└─ Configuration singleton (lru_cache)

Level 3: Database Indexing
├─ users(username, email)
├─ datasets(file_hash, status, user_id)
├─ sequences(sequence_id, cluster_id, model_id)
└─ models(model_name, is_active)
```

### Async Operations

```
FastAPI Async Endpoints
├─ Database queries (async SQLAlchemy)
├─ Redis operations (async redis client)
├─ File uploads (streaming)
└─ Background tasks (training pipeline)

Non-blocking I/O
├─ MinIO operations (async)
├─ MLflow logging (batched)
└─ FAISS search (thread pool)
```

---

## Monitoring & Observability

### Metrics

```
Application Metrics
├─ Request rate (requests/sec)
├─ Response time (p50, p95, p99)
├─ Error rate (4xx, 5xx)
└─ Active users

ML Metrics (MLflow)
├─ Training duration
├─ Model accuracy
├─ Shannon diversity
├─ Simpson diversity
├─ Cluster count
└─ Sequence count

Infrastructure Metrics
├─ CPU usage
├─ Memory usage
├─ Disk I/O
├─ Network I/O
└─ Database connections
```

### Logging

```
Structured Logging (JSON)
{
  "timestamp": "2025-01-02T10:30:45Z",
  "level": "INFO",
  "service": "backend",
  "endpoint": "/api/v1/model/infer",
  "user_id": 123,
  "duration_ms": 45,
  "status_code": 200,
  "request_id": "abc-123",
  "trace_id": "xyz-789"
}
```

---

## Technology Stack Summary

| Category                 | Technology                | Purpose                 |
| ------------------------ | ------------------------- | ----------------------- |
| **Web Framework**  | FastAPI 0.115.6           | REST API, async support |
| **Server**         | Uvicorn 0.34.0            | ASGI server             |
| **Validation**     | Pydantic 2.9.2            | Data validation         |
| **Database**       | SQLAlchemy 2.0.36         | ORM                     |
| **Auth**           | python-jose 3.3.0         | JWT tokens              |
| **Password**       | bcrypt 4.2.1              | Password hashing        |
| **Cache**          | Redis 5.2.1               | In-memory cache         |
| **Storage**        | MinIO 7.2.10              | Object storage (S3)     |
| **ML Framework**   | PyTorch 2.5.1             | Deep learning           |
| **Vector Search**  | FAISS 1.9.0               | Similarity search       |
| **Clustering**     | HDBSCAN 0.8.38            | Density clustering      |
| **Pipeline**       | ZenML 0.70.0              | ML orchestration        |
| **Tracking**       | MLflow 2.17.2             | Experiment tracking     |
| **Bioinformatics** | BioPython 1.84            | Sequence parsing        |
| **Data Science**   | NumPy 2.1.3, Pandas 2.2.3 | Data processing         |

---

## API Endpoints Summary

### Authentication (`/api/v1/auth`)

- `POST /register` - Create new user
- `POST /login` - Get JWT token
- `GET /me` - Get current user
- `POST /logout` - Invalidate token

### Datasets (`/api/v1/dataset`)

- `POST /upload` - Upload dataset (.tar.gz)
- `GET /list` - List user's datasets
- `GET /{id}` - Get dataset details
- `GET /{id}/download` - Download dataset
- `DELETE /{id}` - Delete dataset

### Admin (`/api/v1/admin`)

- `POST /datasets/{id}/approve` - Approve dataset
- `POST /train` - Trigger training
- `GET /training-runs` - List training runs
- `GET /training-runs/{id}` - Get run details
- `GET /users` - List all users

### Models (`/api/v1/model`)

- `POST /infer` - Classify sequence
- `POST /batch-infer` - Batch classification
- `GET /versions` - List model versions
- `POST /load/{id}` - Load specific model

### Search (`/api/v1/search`)

- `POST /query` - Search sequences
- `GET /clusters` - List clusters
- `GET /taxonomies` - List taxonomies

### Visualization (`/api/v1/visualize`)

- `GET /summary` - Biodiversity summary
- `GET /cluster/{id}` - Cluster details
- `GET /dataset/{id}/stats` - Dataset statistics

---

## File Structure

```
backend/
├── main.py                     # FastAPI application entry
├── pyproject.toml              # Poetry dependencies
├── requirements.txt            # Pip dependencies
├── Dockerfile                  # Container image
├── .env                        # Environment config
├── .env.example                # Config template
├── create_admin.py             # Admin setup script
├── test_setup.py               # System verification
├── API_README.md               # API documentation
│
├── app/
│   ├── __init__.py
│   │
│   ├── api/                    # REST API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication (4 endpoints)
│   │   ├── data.py             # Datasets (5 endpoints)
│   │   ├── admin.py            # Admin ops (5 endpoints)
│   │   ├── model.py            # Inference (4 endpoints)
│   │   ├── search.py           # Search (3 endpoints)
│   │   └── visualize.py        # Metrics (3 endpoints)
│   │
│   ├── core/                   # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py           # Settings (40+ env vars)
│   │   ├── security.py         # JWT & bcrypt
│   │   └── dependencies.py     # Dependency injection
│   │
│   ├── database/               # Database layer
│   │   ├── __init__.py
│   │   └── session.py          # SQLAlchemy session
│   │
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   ├── database_models.py  # ORM models (6 tables)
│   │   └── schemas.py          # Pydantic schemas
│   │
│   └── services/               # Business logic
│       ├── __init__.py
│       ├── minio_service.py    # Object storage client
│       ├── redis_service.py    # Cache client
│       ├── mlflow_service.py   # Experiment tracking
│       ├── embedding_service.py# DNA → Vector (k-mer)
│       ├── faiss_indexer.py    # Vector search
│       ├── training_pipeline.py# ZenML pipeline (7 steps)
│       └── inference.py        # Real-time prediction
│
├── data/                       # Local data storage
│   ├── app.db                  # SQLite database
│   └── archives/               # Sample datasets
│       └── 16S_ribosomal_RNA.tar.gz
│
└── prompt/                     # Documentation
    ├── BACKEND_IMPLEMENTATION_SUMMARY.md
    ├── QUICK_START.md
    ├── PROJECT_STATUS.md
    ├── INSTALLATION_GUIDE.md
    └── ARCHITECTURE.md (this file)
```

---

## Key Design Decisions

### 1. K-mer Embeddings (MVP)

- **Decision**: Use 6-mer frequency vectors instead of DNABERT
- **Rationale**: Faster implementation, good baseline, simpler debugging
- **Tradeoff**: Lower accuracy than transformer models
- **Future**: Replace with DNABERT or DNA-BERT-2

### 2. FAISS IndexFlatL2

- **Decision**: Use flat (brute-force) index with L2 distance
- **Rationale**: Exact search, simple, works for <1M sequences
- **Tradeoff**: O(n) search time, not scalable to 100M+
- **Future**: Migrate to IVF or HNSW for large datasets

### 3. SQLite for Metadata

- **Decision**: SQLite instead of PostgreSQL for metadata
- **Rationale**: Simpler setup, file-based, sufficient for MVP
- **Tradeoff**: No concurrent writes, single-server only
- **Future**: Migrate to PostgreSQL for production

### 4. Background Tasks (FastAPI)

- **Decision**: Use FastAPI BackgroundTasks instead of Celery
- **Rationale**: No additional infrastructure, simpler for MVP
- **Tradeoff**: No distributed processing, limited to single server
- **Future**: Add Celery for multi-worker training

### 5. MinIO for Storage

- **Decision**: MinIO (S3-compatible) instead of local filesystem
- **Rationale**: Cloud-ready, versioning, scalable
- **Tradeoff**: Requires separate service
- **Future**: Migrate to AWS S3/GCS/Azure Blob

---

## Future Enhancements

### Phase 2 (Post-MVP)

- [ ] DNABERT embeddings
- [ ] BLAST taxonomy integration
- [ ] Unit tests (pytest)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Rate limiting
- [ ] API versioning

### Phase 3 (Production)

- [ ] PostgreSQL migration
- [ ] Celery for background tasks
- [ ] Kubernetes deployment
- [ ] Monitoring (Prometheus/Grafana)
- [ ] Distributed tracing
- [ ] A/B testing framework

---

**Last Updated**: January 2, 2025
**Version**: 1.0.0 (MVP)
