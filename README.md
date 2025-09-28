# DeepSea eDNA Dashboard

A comprehensive web application for analyzing environmental DNA (eDNA) sequences with machine learning-powered species classification and clustering.

## Features

### Frontend (React + Tailwind CSS)
- **Dashboard**: Overview of sequences, clusters, and analysis metrics
- **Sequences**: Upload, view, and manage DNA sequences with quality metrics
- **Clusters**: Visualize sequence clustering results and similarity groups
- **Metrics**: Real-time analysis performance and taxonomy confidence scores
- **Settings**: Configuration management for analysis parameters

### Backend (FastAPI + ML Pipeline)
- **Sequence Processing**: DNA sequence validation, cleaning, and quality assessment
- **ML Pipeline**: Pre-trained models for sequence embedding generation
- **Clustering**: HDBSCAN-based sequence clustering with customizable parameters
- **Taxonomy Assignment**: Local reference database and NCBI BLAST integration
- **Similarity Search**: FAISS-powered fast similarity search across sequences
- **Object Storage**: MinIO integration for storing sequences, models, and results

## Technology Stack

### Frontend
- **React 19.1.1** - Modern UI framework
- **Tailwind CSS 4.1.13** - Utility-first CSS framework
- **Vite 7.1.7** - Fast development build tool
- **React Router DOM** - Client-side routing
- **Recharts** - Data visualization components
- **Lucide React** - Beautiful icon library

### Backend
- **FastAPI 0.115.6** - High-performance Python web framework
- **SQLAlchemy 2.0.36** - SQL toolkit and ORM
- **PyTorch 2.5.1** - Deep learning framework
- **Transformers 4.48.0** - Pre-trained model library
- **HDBSCAN 0.8.41** - Density-based clustering algorithm
- **FAISS 1.9.0** - Fast similarity search library
- **MinIO 7.2.11** - Object storage client
- **Redis 5.2.1** - In-memory data structure store

### Infrastructure
- **Docker & Docker Compose** - Containerization and orchestration
- **MinIO** - S3-compatible object storage
- **Redis** - Caching and job queue management
- **SQLite/PostgreSQL** - Relational database storage

## Project Structure

```
M.A.R.L.IN-edna-species-classifier/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Main application pages
│   │   ├── hooks/          # Custom React hooks
│   │   └── data/           # Mock data and utilities
│   ├── public/             # Static assets
│   └── package.json        # Frontend dependencies
│
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API endpoints and models
│   │   ├── core/           # Core configuration and utilities
│   │   ├── services/       # ML pipeline and business logic
│   │   └── models/         # Database models
│   ├── main.py             # FastAPI application entry point
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend container image
│
└── docker-compose.yml      # Complete system orchestration
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Run with Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd M.A.R.L.IN-edna-species-classifier
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - MinIO Console: http://localhost:9001 (admin/minioadmin123)

### Local Development Setup

#### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

#### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## API Endpoints

### Sequences
- `GET /api/sequences` - List all sequences
- `POST /api/sequences` - Create new sequence
- `GET /api/sequences/{id}` - Get sequence by ID
- `POST /api/sequences/upload` - Upload FASTA file

### Clustering
- `GET /api/clusters` - List all clusters
- `POST /api/clusters/create` - Create clusters from sequences

### Analysis
- `POST /api/analysis/similarity` - Find similar sequences
- `POST /api/analysis/taxonomy` - Assign taxonomy to sequences
- `GET /api/metrics` - Get analysis metrics

### Jobs
- `GET /api/jobs/{id}` - Get job status

### System
- `GET /health` - Health check endpoint

## Machine Learning Pipeline

### 1. Sequence Preprocessing
- DNA sequence validation and cleaning
- Quality control and filtering
- GC content and length analysis
- Base composition statistics

### 2. Embedding Generation
- Pre-trained transformer models for DNA sequences
- K-mer tokenization approach (6-mer default)
- Batch processing for efficiency
- Vector embeddings stored in MinIO

### 3. Clustering Analysis
- HDBSCAN algorithm for density-based clustering
- Configurable minimum cluster size and samples
- Noise detection and outlier identification
- Cluster center calculation and storage

### 4. Similarity Search
- FAISS index for fast similarity queries
- Cosine similarity metric
- Configurable result limits
- Real-time search capabilities

### 5. Taxonomy Assignment
- Local reference database matching
- NCBI BLAST integration (placeholder)
- Confidence scoring and validation
- Multi-method taxonomy resolution

## Configuration

### Environment Variables

#### Backend Configuration
```bash
# Database
DATABASE_URL=sqlite:///./data/app.db

# MinIO Object Storage
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_SECURE=false

# Redis Cache
REDIS_URL=redis://redis:6379/0

# ML Pipeline
MODEL_CACHE_DIR=/app/models
BATCH_SIZE=32
```

#### Frontend Configuration
```bash
# API Backend URL
VITE_API_URL=http://localhost:8000
```

## Usage Examples

### Upload DNA Sequences
```bash
curl -X POST "http://localhost:8000/api/sequences/upload" \
  -F "file=@sequences.fasta"
```

### Create Clusters
```bash
curl -X POST "http://localhost:8000/api/clusters/create" \
  -H "Content-Type: application/json" \
  -d '{
    "min_cluster_size": 5,
    "min_samples": 3
  }'
```

### Find Similar Sequences
```bash
curl -X POST "http://localhost:8000/api/analysis/similarity" \
  -H "Content-Type: application/json" \
  -d '{
    "sequence_id": 1,
    "limit": 10
  }'
```

### Assign Taxonomy
```bash
curl -X POST "http://localhost:8000/api/analysis/taxonomy" \
  -H "Content-Type: application/json" \
  -d '{
    "sequence_ids": [1, 2, 3],
    "method": "local"
  }'
```

## Deployment

### Production Deployment

1. **Build frontend for production**
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Configure reverse proxy (nginx)**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:3000;
       }
       
       location /api {
           proxy_pass http://localhost:8000;
       }
   }
   ```

### Cloud Platforms
- **Frontend**: Deploy to Vercel, Netlify, or AWS S3 + CloudFront
- **Backend**: Deploy to AWS ECS, Google Cloud Run, or Azure Container Instances
- **Storage**: Use AWS S3, Google Cloud Storage, or Azure Blob Storage instead of MinIO
- **Database**: Use AWS RDS, Google Cloud SQL, or Azure Database for PostgreSQL

## Performance Optimization

### Backend Optimizations
- **Async Processing**: Background tasks for ML pipeline operations
- **Batch Processing**: Efficient handling of multiple sequences
- **Caching**: Redis caching for frequently accessed data
- **Connection Pooling**: SQLAlchemy connection management
- **Model Caching**: Pre-loaded ML models for faster inference

### Frontend Optimizations
- **Code Splitting**: Dynamic imports for route-based splitting
- **Memoization**: React.memo and useMemo for expensive computations
- **Virtual Scrolling**: Efficient rendering of large sequence lists
- **Progressive Loading**: Lazy loading of components and data

## Monitoring and Logging

### Health Checks
- Application health endpoints
- Container health checks in Docker Compose
- Database connectivity monitoring
- External service availability checks

### Logging
- Structured logging with JSON format
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Request/response logging for API calls
- ML pipeline operation logging

### Metrics
- API response times and error rates
- ML pipeline processing times
- Database query performance
- Storage usage and capacity

## Security Considerations

### API Security
- Input validation and sanitization
- Rate limiting and throttling
- CORS configuration
- Authentication and authorization (planned)

### Data Security
- Secure object storage configuration
- Database encryption at rest (planned)
- Network isolation with Docker networks
- Secrets management for production

## Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes with appropriate tests
4. Submit a pull request

### Code Standards
- **Frontend**: ESLint + Prettier configuration
- **Backend**: Black code formatting + isort imports
- **Git**: Conventional commit messages
- **Documentation**: Inline comments and README updates

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database file permissions
   ls -la backend/data/
   
   # Reset database
   rm backend/data/app.db
   docker-compose restart backend
   ```

2. **MinIO Connection Issues**
   ```bash
   # Check MinIO service status
   docker-compose logs minio
   
   # Restart MinIO service
   docker-compose restart minio
   ```

3. **ML Model Loading Errors**
   ```bash
   # Check available disk space
   df -h
   
   # Clear model cache
   rm -rf backend/models/*
   ```

4. **Frontend Build Failures**
   ```bash
   # Clear node modules and reinstall
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check the documentation at `/docs`
- Review API documentation at `http://localhost:8000/docs`

## Acknowledgments

- Built with modern web technologies and machine learning frameworks
- Inspired by the need for accessible eDNA analysis tools
- Designed for marine biodiversity research and conservation efforts