"""
MinIO object storage service for managing datasets, models, and artifacts.
"""

import io
from typing import Optional, List
from pathlib import Path
from minio import Minio
from minio.error import S3Error
import logging

from app.core.config import settings


logger = logging.getLogger(__name__)


class MinIOService:
    """Service for interacting with MinIO object storage."""
    
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """Ensure all required buckets exist."""
        buckets = [
            settings.minio_bucket_raw,
            settings.minio_bucket_processed,
            settings.minio_bucket_models,
            settings.minio_bucket_logs
        ]
        
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Created MinIO bucket: {bucket}")
            except S3Error as e:
                logger.error(f"Error creating bucket {bucket}: {e}")
    
    def upload_file(
        self,
        file_path: str,
        object_name: str,
        bucket: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """Upload a file to MinIO."""
        try:
            self.client.fput_object(
                bucket,
                object_name,
                file_path,
                content_type=content_type
            )
            logger.info(f"Uploaded {file_path} to {bucket}/{object_name}")
            return f"{bucket}/{object_name}"
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    def upload_bytes(
        self,
        data: bytes,
        object_name: str,
        bucket: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """Upload bytes to MinIO."""
        try:
            data_stream = io.BytesIO(data)
            self.client.put_object(
                bucket,
                object_name,
                data_stream,
                length=len(data),
                content_type=content_type
            )
            logger.info(f"Uploaded bytes to {bucket}/{object_name}")
            return f"{bucket}/{object_name}"
        except S3Error as e:
            logger.error(f"Error uploading bytes: {e}")
            raise
    
    def download_file(
        self,
        object_name: str,
        bucket: str,
        file_path: str
    ) -> str:
        """Download a file from MinIO."""
        try:
            self.client.fget_object(bucket, object_name, file_path)
            logger.info(f"Downloaded {bucket}/{object_name} to {file_path}")
            return file_path
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    def download_bytes(
        self,
        object_name: str,
        bucket: str
    ) -> bytes:
        """Download object as bytes from MinIO."""
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            logger.info(f"Downloaded bytes from {bucket}/{object_name}")
            return data
        except S3Error as e:
            logger.error(f"Error downloading bytes: {e}")
            raise
    
    def delete_object(
        self,
        object_name: str,
        bucket: str
    ) -> bool:
        """Delete an object from MinIO."""
        try:
            self.client.remove_object(bucket, object_name)
            logger.info(f"Deleted {bucket}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting object: {e}")
            return False
    
    def list_objects(
        self,
        bucket: str,
        prefix: Optional[str] = None
    ) -> List[str]:
        """List objects in a bucket."""
        try:
            objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Error listing objects: {e}")
            return []
    
    def object_exists(
        self,
        object_name: str,
        bucket: str
    ) -> bool:
        """Check if an object exists."""
        try:
            self.client.stat_object(bucket, object_name)
            return True
        except S3Error:
            return False
    
    def get_object_url(
        self,
        object_name: str,
        bucket: str,
        expires_seconds: int = 3600
    ) -> str:
        """Get presigned URL for an object."""
        try:
            url = self.client.presigned_get_object(
                bucket,
                object_name,
                expires=expires_seconds
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise


# Global MinIO service instance
minio_service = MinIOService()
