"""
Search API endpoints for querying sequences and clusters.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.database_models import User, Sequence
from app.models.schemas import SearchQuery, SearchResponse, SequenceResult
import logging


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


@router.post("/query", response_model=SearchResponse)
async def search_sequences(
    query: SearchQuery,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search sequences by taxonomy, cluster, or sequence ID."""
    
    # Build query based on search type
    base_query = db.query(Sequence)
    
    if query.search_type == "taxonomy":
        # Search in taxonomy field
        base_query = base_query.filter(
            Sequence.taxonomy.ilike(f"%{query.query}%")
        )
    
    elif query.search_type == "cluster":
        # Search by cluster ID
        try:
            cluster_id = int(query.query)
            base_query = base_query.filter(Sequence.cluster_id == cluster_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cluster ID must be an integer"
            )
    
    elif query.search_type == "sequence_id":
        # Search by sequence ID
        base_query = base_query.filter(
            Sequence.sequence_id.ilike(f"%{query.query}%")
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid search type: {query.search_type}"
        )
    
    # Get total count
    total = base_query.count()
    
    # Get results with pagination
    results = base_query.order_by(Sequence.created_at.desc())\
        .offset(query.offset)\
        .limit(query.limit)\
        .all()
    
    return SearchResponse(
        results=[SequenceResult.model_validate(r) for r in results],
        total=total,
        query=query.query,
        search_type=query.search_type
    )


@router.get("/clusters")
async def list_clusters(
    model_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all unique clusters."""
    
    query = db.query(Sequence.cluster_id).distinct()
    
    if model_id:
        # Filter by model (would need to add model_id to Sequence table)
        pass
    
    clusters = [row[0] for row in query.all() if row[0] is not None]
    clusters.sort()
    
    return {
        "clusters": clusters,
        "total": len(clusters)
    }


@router.get("/taxonomies")
async def list_taxonomies(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List unique taxonomies."""
    
    taxonomies = db.query(Sequence.taxonomy)\
        .distinct()\
        .filter(Sequence.taxonomy.isnot(None))\
        .limit(limit)\
        .all()
    
    taxonomy_list = [row[0] for row in taxonomies if row[0]]
    
    return {
        "taxonomies": taxonomy_list,
        "total": len(taxonomy_list)
    }
