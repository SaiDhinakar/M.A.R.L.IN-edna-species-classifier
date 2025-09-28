import io
import json
import pickle
from typing import Any, Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class MinIOClient:
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """Ensure all required buckets exist"""
        buckets = [
            settings.minio_bucket_raw,
            settings.minio_bucket_processed,
            settings.minio_bucket_models
        ]
        
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Created bucket: {bucket}")
            except S3Error as e:
                logger.error(f"Error creating bucket {bucket}: {e}")
    
    def upload_file(self, bucket: str, object_name: str, file_data: BinaryIO, 
                   content_type: str = "application/octet-stream") -> bool:
        """Upload a file to MinIO"""
        try:
            # Get file size
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            file_data.seek(0)  # Seek back to beginning
            
            self.client.put_object(
                bucket, object_name, file_data, file_size,
                content_type=content_type
            )
            logger.info(f"Uploaded {object_name} to bucket {bucket}")
            return True
        except S3Error as e:
            logger.error(f"Error uploading {object_name}: {e}")
            return False
    
    def download_file(self, bucket: str, object_name: str) -> Optional[bytes]:
        """Download a file from MinIO"""
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Error downloading {object_name}: {e}")
            return None
    
    def upload_json(self, bucket: str, object_name: str, data: Any) -> bool:
        """Upload JSON data to MinIO"""
        try:
            json_data = json.dumps(data, indent=2, default=str)
            json_bytes = json_data.encode('utf-8')
            return self.upload_file(
                bucket, object_name, io.BytesIO(json_bytes), 
                content_type="application/json"
            )
        except Exception as e:
            logger.error(f"Error uploading JSON {object_name}: {e}")
            return False
    
    def download_json(self, bucket: str, object_name: str) -> Optional[Any]:
        """Download JSON data from MinIO"""
        try:
            data = self.download_file(bucket, object_name)
            if data:
                return json.loads(data.decode('utf-8'))
            return None
        except Exception as e:
            logger.error(f"Error downloading JSON {object_name}: {e}")
            return None
    
    def upload_pickle(self, bucket: str, object_name: str, data: Any) -> bool:
        """Upload pickled data to MinIO"""
        try:
            pickle_data = pickle.dumps(data)
            return self.upload_file(
                bucket, object_name, io.BytesIO(pickle_data),
                content_type="application/octet-stream"
            )
        except Exception as e:
            logger.error(f"Error uploading pickle {object_name}: {e}")
            return False
    
    def download_pickle(self, bucket: str, object_name: str) -> Optional[Any]:
        """Download pickled data from MinIO"""
        try:
            data = self.download_file(bucket, object_name)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error downloading pickle {object_name}: {e}")
            return None
    
    def delete_file(self, bucket: str, object_name: str) -> bool:
        """Delete a file from MinIO"""
        try:
            self.client.remove_object(bucket, object_name)
            logger.info(f"Deleted {object_name} from bucket {bucket}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting {object_name}: {e}")
            return False
    
    def list_files(self, bucket: str, prefix: str = "") -> list:
        """List files in a bucket with optional prefix"""
        try:
            objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Error listing files in {bucket}: {e}")
            return []
    
    def file_exists(self, bucket: str, object_name: str) -> bool:
        """Check if a file exists in MinIO"""
        try:
            self.client.stat_object(bucket, object_name)
            return True
        except S3Error:
            return False


# Global MinIO client instance
minio_client = MinIOClient()


def get_minio_client() -> MinIOClient:
    """Get the global MinIO client instance"""
    return minio_client