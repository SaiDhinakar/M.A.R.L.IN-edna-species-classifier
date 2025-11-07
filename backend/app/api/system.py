"""
System monitoring API endpoints (Admin only).
Provides metrics for storage, CPU, GPU, and RAM usage.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import psutil
import os
import logging

from app.core.dependencies import get_current_active_user, require_admin
from app.database.session import get_db
from app.models.database_models import User
from app.services.minio_service import minio_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system", tags=["system"])


def get_minio_storage_usage() -> Dict[str, Any]:
    """Get MinIO storage usage statistics."""
    try:
        total_size = 0
        object_count = 0
        buckets = []
        
        # Get all buckets
        bucket_list = minio_service.client.list_buckets()
        
        for bucket in bucket_list:
            bucket_name = bucket.name
            bucket_size = 0
            bucket_objects = 0
            
            # List all objects in bucket
            objects = minio_service.client.list_objects(bucket_name, recursive=True)
            
            for obj in objects:
                bucket_size += obj.size
                bucket_objects += 1
            
            total_size += bucket_size
            object_count += bucket_objects
            
            buckets.append({
                "name": bucket_name,
                "size_bytes": bucket_size,
                "size_mb": round(bucket_size / (1024 * 1024), 2),
                "size_gb": round(bucket_size / (1024 * 1024 * 1024), 2),
                "object_count": bucket_objects,
                "created_date": bucket.creation_date
            })
        
        return {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2),
            "total_objects": object_count,
            "buckets": buckets,
            "status": "connected"
        }
    except Exception as e:
        logger.error(f"Error getting MinIO storage usage: {e}")
        return {
            "error": str(e),
            "status": "error"
        }


def get_cpu_usage() -> Dict[str, Any]:
    """Get CPU usage statistics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count()
        
        return {
            "usage_percent": round(sum(cpu_percent) / len(cpu_percent), 2),
            "usage_per_core": [round(p, 2) for p in cpu_percent],
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": cpu_count,
            "frequency_mhz": {
                "current": round(cpu_freq.current, 2) if cpu_freq else None,
                "min": round(cpu_freq.min, 2) if cpu_freq else None,
                "max": round(cpu_freq.max, 2) if cpu_freq else None
            },
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        }
    except Exception as e:
        logger.error(f"Error getting CPU usage: {e}")
        return {"error": str(e)}


def get_gpu_usage() -> Dict[str, Any]:
    """Get GPU usage statistics."""
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        
        if not gpus:
            return {
                "available": False,
                "message": "No GPU detected"
            }
        
        gpu_info = []
        for gpu in gpus:
            gpu_info.append({
                "id": gpu.id,
                "name": gpu.name,
                "load_percent": round(gpu.load * 100, 2),
                "memory_used_mb": round(gpu.memoryUsed, 2),
                "memory_total_mb": round(gpu.memoryTotal, 2),
                "memory_free_mb": round(gpu.memoryFree, 2),
                "memory_usage_percent": round((gpu.memoryUsed / gpu.memoryTotal) * 100, 2) if gpu.memoryTotal > 0 else 0,
                "temperature_c": gpu.temperature,
                "uuid": gpu.uuid
            })
        
        return {
            "available": True,
            "count": len(gpus),
            "gpus": gpu_info
        }
    except ImportError:
        return {
            "available": False,
            "message": "GPUtil package not installed. Install with: pip install gputil"
        }
    except Exception as e:
        logger.error(f"Error getting GPU usage: {e}")
        return {
            "available": False,
            "error": str(e)
        }


def get_ram_usage() -> Dict[str, Any]:
    """Get RAM usage statistics."""
    try:
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "total_gb": round(memory.total / (1024 ** 3), 2),
            "available_gb": round(memory.available / (1024 ** 3), 2),
            "used_gb": round(memory.used / (1024 ** 3), 2),
            "free_gb": round(memory.free / (1024 ** 3), 2),
            "usage_percent": round(memory.percent, 2),
            "buffers_gb": round(getattr(memory, 'buffers', 0) / (1024 ** 3), 2),
            "cached_gb": round(getattr(memory, 'cached', 0) / (1024 ** 3), 2),
            "swap": {
                "total_gb": round(swap.total / (1024 ** 3), 2),
                "used_gb": round(swap.used / (1024 ** 3), 2),
                "free_gb": round(swap.free / (1024 ** 3), 2),
                "usage_percent": round(swap.percent, 2)
            }
        }
    except Exception as e:
        logger.error(f"Error getting RAM usage: {e}")
        return {"error": str(e)}


def get_disk_usage() -> Dict[str, Any]:
    """Get disk usage statistics."""
    try:
        partitions = psutil.disk_partitions()
        disk_info = []
        
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / (1024 ** 3), 2),
                    "used_gb": round(usage.used / (1024 ** 3), 2),
                    "free_gb": round(usage.free / (1024 ** 3), 2),
                    "usage_percent": round(usage.percent, 2)
                })
            except PermissionError:
                continue
        
        return {
            "partitions": disk_info,
            "io_counters": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None
        }
    except Exception as e:
        logger.error(f"Error getting disk usage: {e}")
        return {"error": str(e)}


@router.get("/storage")
async def get_storage_metrics(
    current_user: User = Depends(require_admin)
):
    """
    Get MinIO storage usage metrics (Admin only).
    
    Returns:
    - Total storage used across all buckets
    - Per-bucket storage statistics
    - Object counts
    """
    return get_minio_storage_usage()


@router.get("/cpu")
async def get_cpu_metrics(
    current_user: User = Depends(require_admin)
):
    """
    Get CPU usage metrics (Admin only).
    
    Returns:
    - Overall CPU usage percentage
    - Per-core usage
    - CPU frequency
    - Load average
    """
    return get_cpu_usage()


@router.get("/gpu")
async def get_gpu_metrics(
    current_user: User = Depends(require_admin)
):
    """
    Get GPU usage metrics (Admin only).
    
    Returns:
    - GPU availability
    - Per-GPU load and memory usage
    - Temperature
    """
    return get_gpu_usage()


@router.get("/ram")
async def get_ram_metrics(
    current_user: User = Depends(require_admin)
):
    """
    Get RAM usage metrics (Admin only).
    
    Returns:
    - Total/used/free RAM
    - Usage percentage
    - Swap usage
    """
    return get_ram_usage()


@router.get("/disk")
async def get_disk_metrics(
    current_user: User = Depends(require_admin)
):
    """
    Get disk usage metrics (Admin only).
    
    Returns:
    - Per-partition disk usage
    - IO statistics
    """
    return get_disk_usage()


@router.get("/all")
async def get_all_metrics(
    current_user: User = Depends(require_admin)
):
    """
    Get all system metrics in one call (Admin only).
    
    Returns comprehensive system monitoring data including:
    - Storage (MinIO)
    - CPU
    - GPU
    - RAM
    - Disk
    """
    return {
        "storage": get_minio_storage_usage(),
        "cpu": get_cpu_usage(),
        "gpu": get_gpu_usage(),
        "ram": get_ram_usage(),
        "disk": get_disk_usage()
    }


@router.get("/health")
async def get_system_health(
    current_user: User = Depends(require_admin)
):
    """
    Get overall system health status (Admin only).
    
    Returns a summary of system health with warnings if any resource
    is running low or experiencing high usage.
    """
    cpu = get_cpu_usage()
    ram = get_ram_usage()
    disk = get_disk_usage()
    storage = get_minio_storage_usage()
    
    warnings = []
    status = "healthy"
    
    # Check CPU
    if cpu.get("usage_percent", 0) > 90:
        warnings.append("CPU usage critically high (>90%)")
        status = "critical"
    elif cpu.get("usage_percent", 0) > 75:
        warnings.append("CPU usage high (>75%)")
        status = "warning" if status == "healthy" else status
    
    # Check RAM
    if ram.get("usage_percent", 0) > 90:
        warnings.append("RAM usage critically high (>90%)")
        status = "critical"
    elif ram.get("usage_percent", 0) > 80:
        warnings.append("RAM usage high (>80%)")
        status = "warning" if status == "healthy" else status
    
    # Check Disk
    for partition in disk.get("partitions", []):
        if partition.get("usage_percent", 0) > 90:
            warnings.append(f"Disk {partition['mountpoint']} critically full (>90%)")
            status = "critical"
        elif partition.get("usage_percent", 0) > 85:
            warnings.append(f"Disk {partition['mountpoint']} almost full (>85%)")
            status = "warning" if status == "healthy" else status
    
    # Check Storage
    if storage.get("status") == "error":
        warnings.append("MinIO storage unavailable")
        status = "warning" if status == "healthy" else status
    
    return {
        "status": status,
        "warnings": warnings,
        "summary": {
            "cpu_usage_percent": cpu.get("usage_percent"),
            "ram_usage_percent": ram.get("usage_percent"),
            "storage_used_gb": storage.get("total_size_gb"),
            "disk_usage": [
                {
                    "mountpoint": p["mountpoint"],
                    "usage_percent": p["usage_percent"]
                }
                for p in disk.get("partitions", [])
            ]
        }
    }


@router.get("/services")
async def get_external_services_health(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get health status of external services (MinIO, MLflow, PostgreSQL, Redis).
    
    Admin only endpoint.
    
    Returns:
        Dictionary with status of each service
    """
    services = {}
    
    # Check MinIO
    try:
        minio_service.client.list_buckets()
        services["minio"] = {
            "status": "healthy",
            "message": "Connected",
            "endpoint": os.getenv("MINIO_ENDPOINT", "localhost:9000")
        }
    except Exception as e:
        logger.error(f"MinIO health check failed: {str(e)}")
        services["minio"] = {
            "status": "unhealthy",
            "message": str(e),
            "endpoint": os.getenv("MINIO_ENDPOINT", "localhost:9000")
        }
    
    # Check PostgreSQL
    try:
        from app.database.session import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        services["postgresql"] = {
            "status": "healthy",
            "message": "Connected",
            "database": os.getenv("POSTGRES_DB", "marlin")
        }
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {str(e)}")
        services["postgresql"] = {
            "status": "unhealthy",
            "message": str(e),
            "database": os.getenv("POSTGRES_DB", "marlin")
        }
    
    # Check Redis (if configured)
    redis_host = os.getenv("REDIS_HOST")
    if redis_host:
        try:
            import redis
            r = redis.Redis(
                host=redis_host,
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 0)),
                socket_connect_timeout=5
            )
            r.ping()
            services["redis"] = {
                "status": "healthy",
                "message": "Connected",
                "host": redis_host
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            services["redis"] = {
                "status": "unhealthy",
                "message": str(e),
                "host": redis_host
            }
    else:
        services["redis"] = {
            "status": "not_configured",
            "message": "Redis is not configured",
            "host": None
        }
    
    # Check MLflow
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI")
    if mlflow_uri:
        try:
            import mlflow
            mlflow.set_tracking_uri(mlflow_uri)
            # Try to get experiments
            mlflow.search_experiments(max_results=1)
            services["mlflow"] = {
                "status": "healthy",
                "message": "Connected",
                "tracking_uri": mlflow_uri
            }
        except Exception as e:
            logger.error(f"MLflow health check failed: {str(e)}")
            services["mlflow"] = {
                "status": "unhealthy",
                "message": str(e),
                "tracking_uri": mlflow_uri
            }
    else:
        services["mlflow"] = {
            "status": "not_configured",
            "message": "MLflow tracking URI is not configured",
            "tracking_uri": None
        }
    
    # Overall status
    all_critical = all(
        s["status"] in ["healthy", "not_configured"] 
        for s in services.values()
    )
    
    return {
        "overall_status": "healthy" if all_critical else "unhealthy",
        "services": services,
        "timestamp": psutil.time.time()
    }
