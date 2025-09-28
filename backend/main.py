from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import logging

from app.core.config import get_settings
from app.core.database import get_db, engine, Base, Sequence, Cluster, Job, Metrics
from app.api.models import (
    SequenceCreate, SequenceResponse, ClusterRequest, ClusterResponse, 
    MetricsResponse, SimilarityRequest, TaxonomyRequest
)
from app.services.ml_pipeline import get_dna_preprocessor, get_dna_embedder
from app.services.clustering import get_sequence_clusterer, get_similarity_searcher
from app.services.taxonomy import get_taxonomy_assigner
from app.core.utils import get_minio_client

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="DeepSea eDNA API",
    description="API for eDNA sequence analysis and species classification",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Get service instances
dna_preprocessor = get_dna_preprocessor()
dna_embedder = get_dna_embedder()
sequence_clusterer = get_sequence_clusterer()
similarity_searcher = get_similarity_searcher()
taxonomy_assigner = get_taxonomy_assigner()
minio_client = get_minio_client()


@app.get("/")
async def root():
    return {"message": "DeepSea eDNA API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


# Sequence endpoints
@app.get("/api/sequences", response_model=List[SequenceResponse])
async def get_sequences(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all sequences with pagination"""
    sequences = db.query(Sequence).offset(skip).limit(limit).all()
    return sequences


@app.post("/api/sequences", response_model=SequenceResponse)
async def create_sequence(sequence: SequenceCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create a new sequence and trigger analysis"""
    try:
        # Validate and preprocess sequence
        is_valid, message = dna_preprocessor.validate_sequence(sequence.sequence_data)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid sequence: {message}")
        
        # Clean sequence
        cleaned_sequence = dna_preprocessor.clean_sequence(sequence.sequence_data)
        
        # Get sequence statistics
        stats = dna_preprocessor.get_sequence_stats(cleaned_sequence)
        
        # Create sequence record
        db_sequence = Sequence(
            name=sequence.name,
            sequence_data=cleaned_sequence,
            length=stats["length"],
            gc_content=stats["gc_content"],
            quality_score=0.9 if stats["valid"] else 0.1,
            status="processing"
        )
        
        db.add(db_sequence)
        db.commit()
        db.refresh(db_sequence)
        
        # Schedule background processing
        background_tasks.add_task(process_sequence_background, db_sequence.id)
        
        return db_sequence
        
    except Exception as e:
        logger.error(f"Error creating sequence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sequences/{sequence_id}", response_model=SequenceResponse)
async def get_sequence(sequence_id: int, db: Session = Depends(get_db)):
    """Get a specific sequence by ID"""
    sequence = db.query(Sequence).filter(Sequence.id == sequence_id).first()
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    return sequence


@app.post("/api/sequences/upload")
async def upload_sequences(file: UploadFile = File(...), background_tasks: BackgroundTasks = None, db: Session = Depends(get_db)):
    """Upload sequences from FASTA file"""
    try:
        if not file.filename.endswith(('.fasta', '.fa', '.fas')):
            raise HTTPException(status_code=400, detail="Only FASTA files are supported")
        
        # Read file content
        content = await file.read()
        sequences = parse_fasta_content(content.decode('utf-8'))
        
        created_sequences = []
        for name, seq_data in sequences:
            # Validate sequence
            is_valid, message = dna_preprocessor.validate_sequence(seq_data)
            if not is_valid:
                logger.warning(f"Skipping invalid sequence {name}: {message}")
                continue
            
            # Clean and create sequence
            cleaned_sequence = dna_preprocessor.clean_sequence(seq_data)
            stats = dna_preprocessor.get_sequence_stats(cleaned_sequence)
            
            db_sequence = Sequence(
                name=name,
                sequence_data=cleaned_sequence,
                length=stats["length"],
                gc_content=stats["gc_content"],
                quality_score=0.9 if stats["valid"] else 0.1,
                status="processing"
            )
            
            db.add(db_sequence)
            created_sequences.append(db_sequence)
        
        db.commit()
        
        # Schedule background processing for all sequences
        if background_tasks:
            for seq in created_sequences:
                background_tasks.add_task(process_sequence_background, seq.id)
        
        return {
            "message": f"Uploaded {len(created_sequences)} sequences",
            "sequences": [{"id": seq.id, "name": seq.name} for seq in created_sequences]
        }
        
    except Exception as e:
        logger.error(f"Error uploading sequences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Clustering endpoints
@app.get("/api/clusters", response_model=List[ClusterResponse])
async def get_clusters(db: Session = Depends(get_db)):
    """Get all clusters"""
    clusters = db.query(Cluster).all()
    return clusters


@app.post("/api/clusters/create")
async def create_clusters(request: ClusterRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create clusters from sequences"""
    try:
        # Get sequences
        sequences = db.query(Sequence).filter(Sequence.status == "completed").all()
        if not sequences:
            raise HTTPException(status_code=400, detail="No completed sequences available for clustering")
        
        # Create clustering job
        job = Job(
            job_type="clustering",
            status="running",
            parameters={"min_cluster_size": request.min_cluster_size, "min_samples": request.min_samples}
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Schedule background clustering
        background_tasks.add_task(run_clustering_background, job.id, [seq.id for seq in sequences], request)
        
        return {"message": "Clustering job started", "job_id": job.id}
        
    except Exception as e:
        logger.error(f"Error creating clusters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analysis endpoints
@app.get("/api/metrics", response_model=List[MetricsResponse])
async def get_metrics(db: Session = Depends(get_db)):
    """Get analysis metrics"""
    metrics = db.query(Metrics).all()
    return metrics


@app.post("/api/analysis/similarity")
async def find_similar_sequences(request: SimilarityRequest, db: Session = Depends(get_db)):
    """Find similar sequences to a query sequence"""
    try:
        # Get query sequence
        query_sequence = db.query(Sequence).filter(Sequence.id == request.sequence_id).first()
        if not query_sequence:
            raise HTTPException(status_code=404, detail="Query sequence not found")
        
        if not query_sequence.embedding:
            raise HTTPException(status_code=400, detail="Query sequence has no embedding")
        
        # Perform similarity search
        results = similarity_searcher.search_similar(
            query_sequence.embedding, 
            k=request.limit or 10
        )
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Error finding similar sequences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analysis/taxonomy")
async def assign_taxonomy(request: TaxonomyRequest, db: Session = Depends(get_db)):
    """Assign taxonomy to sequences"""
    try:
        sequences = db.query(Sequence).filter(Sequence.id.in_(request.sequence_ids)).all()
        if not sequences:
            raise HTTPException(status_code=404, detail="No sequences found")
        
        # Assign taxonomy
        sequence_data = [seq.sequence_data for seq in sequences]
        taxonomy_results = taxonomy_assigner.assign_taxonomy_batch(
            sequence_data, 
            method=request.method or "local"
        )
        
        # Update sequences with taxonomy
        for seq, result in zip(sequences, taxonomy_results):
            seq.taxonomy = result.get("taxonomy", {})
            seq.taxonomy_confidence = result.get("confidence", 0.0)
        
        db.commit()
        
        return {"results": taxonomy_results}
        
    except Exception as e:
        logger.error(f"Error assigning taxonomy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Job management endpoints
@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Get job status"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# Background processing functions
async def process_sequence_background(sequence_id: int):
    """Background task for processing a single sequence"""
    try:
        db = next(get_db())
        sequence = db.query(Sequence).filter(Sequence.id == sequence_id).first()
        
        if not sequence:
            logger.error(f"Sequence {sequence_id} not found")
            return
        
        logger.info(f"Processing sequence {sequence_id}: {sequence.name}")
        
        # Generate embedding
        embedding = dna_embedder.generate_embedding(sequence.sequence_data)
        if embedding is not None:
            sequence.embedding = embedding.tolist()
        
        # Assign taxonomy
        taxonomy_result = taxonomy_assigner.assign_taxonomy_local(sequence.sequence_data)
        sequence.taxonomy = taxonomy_result.get("taxonomy", {})
        sequence.taxonomy_confidence = taxonomy_result.get("confidence", 0.0)
        
        # Update status
        sequence.status = "completed"
        
        db.commit()
        logger.info(f"Completed processing sequence {sequence_id}")
        
    except Exception as e:
        logger.error(f"Error processing sequence {sequence_id}: {e}")
        # Update sequence status to failed
        try:
            db = next(get_db())
            sequence = db.query(Sequence).filter(Sequence.id == sequence_id).first()
            if sequence:
                sequence.status = "failed"
                db.commit()
        except:
            pass


async def run_clustering_background(job_id: int, sequence_ids: List[int], request: ClusterRequest):
    """Background task for clustering sequences"""
    try:
        db = next(get_db())
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        logger.info(f"Running clustering job {job_id}")
        
        # Get sequences with embeddings
        sequences = db.query(Sequence).filter(
            Sequence.id.in_(sequence_ids),
            Sequence.embedding.isnot(None)
        ).all()
        
        if not sequences:
            job.status = "failed"
            job.error_message = "No sequences with embeddings found"
            db.commit()
            return
        
        # Extract embeddings
        embeddings = [seq.embedding for seq in sequences]
        
        # Perform clustering
        clustering_result = sequence_clusterer.cluster_sequences(
            embeddings,
            min_cluster_size=request.min_cluster_size,
            min_samples=request.min_samples
        )
        
        # Create cluster records
        cluster_map = {}
        for cluster_id, center in clustering_result["cluster_centers"].items():
            cluster = Cluster(
                name=f"Cluster {cluster_id}",
                center_embedding=center,
                size=0  # Will be updated below
            )
            db.add(cluster)
            db.flush()
            cluster_map[cluster_id] = cluster
        
        # Update sequence cluster assignments
        for assignment in clustering_result["cluster_assignments"]:
            seq_idx = assignment["sequence_index"]
            cluster_id = assignment["cluster_id"]
            
            if seq_idx < len(sequences):
                sequence = sequences[seq_idx]
                if cluster_id is not None and cluster_id in cluster_map:
                    sequence.cluster_id = cluster_map[cluster_id].id
                    cluster_map[cluster_id].size += 1
        
        # Update job status
        job.status = "completed"
        job.result = clustering_result
        
        db.commit()
        logger.info(f"Completed clustering job {job_id}")
        
    except Exception as e:
        logger.error(f"Error in clustering job {job_id}: {e}")
        try:
            db = next(get_db())
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                db.commit()
        except:
            pass


def parse_fasta_content(content: str) -> List[tuple]:
    """Parse FASTA file content"""
    sequences = []
    current_name = None
    current_seq = []
    
    for line in content.strip().split('\n'):
        line = line.strip()
        if line.startswith('>'):
            if current_name and current_seq:
                sequences.append((current_name, ''.join(current_seq)))
            current_name = line[1:].split()[0]  # Take first part of header
            current_seq = []
        elif line and current_name:
            current_seq.append(line)
    
    # Add last sequence
    if current_name and current_seq:
        sequences.append((current_name, ''.join(current_seq)))
    
    return sequences


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)