"""
MinIO Storage Service for eDNA Classifier
Handles data ingestion from MinIO object storage with MLflow integration
"""

import os
from pathlib import Path
from typing import Optional, List
from minio import Minio
from minio.error import S3Error
import tempfile
import shutil
import mlflow


class MinIOStorage:
    """Service for interacting with MinIO object storage with MLflow tracking"""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = False):
        """
        Initialize MinIO client
        
        Args:
            endpoint: MinIO server endpoint (e.g., 'localhost:9000')
            access_key: MinIO access key
            secret_key: MinIO secret key
            secure: Whether to use HTTPS
        """
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.endpoint = endpoint
    
    def list_buckets(self) -> List[str]:
        """List all available buckets"""
        try:
            buckets = self.client.list_buckets()
            return [bucket.name for bucket in buckets]
        except S3Error as e:
            print(f"Error listing buckets: {e}")
            return []
    
    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if a bucket exists"""
        try:
            return self.client.bucket_exists(bucket_name)
        except S3Error:
            return False
    
    def create_bucket(self, bucket_name: str) -> bool:
        """Create a new bucket"""
        try:
            if not self.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                print(f"Bucket '{bucket_name}' created successfully")
                mlflow.log_param("minio_bucket_created", bucket_name)
                return True
            return True
        except S3Error as e:
            print(f"Error creating bucket: {e}")
            return False
    
    def list_objects(self, bucket_name: str, prefix: str = "") -> List[str]:
        """
        List objects in a bucket with optional prefix
        
        Args:
            bucket_name: Name of the bucket
            prefix: Optional prefix to filter objects
            
        Returns:
            List of object names
        """
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"Error listing objects: {e}")
            return []
    
    def download_file(self, bucket_name: str, object_name: str, file_path: str) -> bool:
        """
        Download a file from MinIO
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object in MinIO
            file_path: Local path where file will be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Download file
            self.client.fget_object(bucket_name, object_name, file_path)
            file_size = os.path.getsize(file_path)
            print(f"Downloaded {object_name} to {file_path} ({file_size / 1024 / 1024:.2f} MB)")
            
            # Log to MLflow
            try:
                mlflow.log_param(f"downloaded_{Path(object_name).stem}", file_size)
            except:
                pass
            
            return True
        except S3Error as e:
            print(f"Error downloading file: {e}")
            return False
    
    def upload_file(self, bucket_name: str, object_name: str, file_path: str) -> bool:
        """
        Upload a file to MinIO
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name for the object in MinIO
            file_path: Local path of the file to upload
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure bucket exists
            if not self.bucket_exists(bucket_name):
                self.create_bucket(bucket_name)
            
            # Upload file
            self.client.fput_object(bucket_name, object_name, file_path)
            file_size = os.path.getsize(file_path)
            print(f"Uploaded {file_path} as {object_name} ({file_size / 1024 / 1024:.2f} MB)")
            
            # Log to MLflow
            try:
                mlflow.log_param(f"uploaded_{Path(object_name).stem}", file_size)
            except:
                pass
            
            return True
        except S3Error as e:
            print(f"Error uploading file: {e}")
            return False
    
    def download_archive(self, bucket_name: str, archive_name: str, extract_to: str) -> Optional[Path]:
        """
        Download and extract an archive from MinIO
        
        Args:
            bucket_name: Name of the bucket
            archive_name: Name of the archive file
            extract_to: Directory to extract files to
            
        Returns:
            Path to extracted directory or None if failed
        """
        import tarfile
        import gzip
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz') as temp_file:
                temp_path = temp_file.name
            
            # Download archive
            print(f"Downloading archive: {archive_name} from bucket: {bucket_name}")
            if not self.download_file(bucket_name, archive_name, temp_path):
                return None
            
            # Extract archive
            extract_path = Path(extract_to) / Path(archive_name).stem.replace('.tar', '')
            extract_path.mkdir(parents=True, exist_ok=True)
            
            print(f"Extracting archive to: {extract_path}")
            if archive_name.endswith('.tar.gz') or archive_name.endswith('.tgz'):
                with tarfile.open(temp_path, 'r:gz') as tar:
                    tar.extractall(path=extract_path)
            elif archive_name.endswith('.tar'):
                with tarfile.open(temp_path, 'r:') as tar:
                    tar.extractall(path=extract_path)
            else:
                print(f"Unsupported archive format: {archive_name}")
                os.unlink(temp_path)
                return None
            
            # Cleanup temporary file
            os.unlink(temp_path)
            
            # Log extraction to MLflow
            try:
                mlflow.log_param(f"archive_extracted", archive_name)
                mlflow.log_param(f"extraction_path", str(extract_path))
            except:
                pass
            
            print(f"Extracted {archive_name} to {extract_path}")
            return extract_path
            
        except Exception as e:
            print(f"Error downloading/extracting archive: {e}")
            return None
    
    def get_object_info(self, bucket_name: str, object_name: str) -> Optional[dict]:
        """Get information about an object"""
        try:
            stat = self.client.stat_object(bucket_name, object_name)
            return {
                'size': stat.size,
                'etag': stat.etag,
                'last_modified': stat.last_modified,
                'content_type': stat.content_type
            }
        except S3Error as e:
            print(f"Error getting object info: {e}")
            return None


def create_minio_client(endpoint: Optional[str] = None) -> MinIOStorage:
    """
    Create MinIO client from environment variables
    
    Args:
        endpoint: Optional MinIO endpoint (defaults to MINIO_API env var)
        
    Returns:
        MinIOStorage instance
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    endpoint = endpoint or os.getenv('MINIO_API', 'localhost:9000')
    access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
    
    print(f"Connecting to MinIO at: {endpoint}")
    return MinIOStorage(endpoint, access_key, secret_key, secure)

import os
import tarfile
from pathlib import Path
from typing import List, Optional
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MinIOStorageService:
    """Service for interacting with MinIO object storage."""
    
    def __init__(self):
        """Initialize MinIO client with credentials from environment."""
        minio_url = os.getenv("MINIO_API", "http://127.0.0.1:9000")
        
        # Parse MinIO URL
        minio_url = minio_url.replace("http://", "").replace("https://", "")
        
        # Default credentials (should be in .env in production)
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = os.getenv("MINIO_BUCKET", "edna-data")
        
        # Create MinIO client
        self.client = Minio(
            minio_url,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=False  # Set to True if using HTTPS
        )
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"✅ Created MinIO bucket: {self.bucket_name}")
            else:
                print(f"✅ MinIO bucket '{self.bucket_name}' already exists")
        except S3Error as e:
            print(f"⚠️ Error checking/creating bucket: {e}")
    
    def upload_file(self, file_path: str, object_name: Optional[str] = None) -> bool:
        """
        Upload a file to MinIO.
        
        Args:
            file_path: Local path to the file to upload
            object_name: Name to use in MinIO (defaults to filename)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if object_name is None:
                object_name = Path(file_path).name
            
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path
            )
            print(f"✅ Uploaded {file_path} as {object_name}")
            return True
        except S3Error as e:
            print(f"❌ Error uploading file: {e}")
            return False
    
    def download_file(self, object_name: str, file_path: str) -> bool:
        """
        Download a file from MinIO.
        
        Args:
            object_name: Name of the object in MinIO
            file_path: Local path where to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.client.fget_object(
                self.bucket_name,
                object_name,
                file_path
            )
            print(f"✅ Downloaded {object_name} to {file_path}")
            return True
        except S3Error as e:
            print(f"❌ Error downloading file: {e}")
            return False
    
    def list_objects(self, prefix: str = "") -> List[str]:
        """
        List objects in the bucket with optional prefix filter.
        
        Args:
            prefix: Filter objects by prefix (folder path)
            
        Returns:
            List of object names
        """
        try:
            objects = self.client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=True
            )
            object_names = [obj.object_name for obj in objects]
            print(f"✅ Found {len(object_names)} objects with prefix '{prefix}'")
            return object_names
        except S3Error as e:
            print(f"❌ Error listing objects: {e}")
            return []
    
    def delete_object(self, object_name: str) -> bool:
        """
        Delete an object from MinIO.
        
        Args:
            object_name: Name of the object to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            print(f"✅ Deleted {object_name}")
            return True
        except S3Error as e:
            print(f"❌ Error deleting object: {e}")
            return False
    
    def extract_archive(self, archive_path: str, extract_to: str) -> str:
        """
        Extract a tar.gz archive.
        
        Args:
            archive_path: Path to the archive file
            extract_to: Directory where to extract files
            
        Returns:
            Path to the extracted directory
        """
        try:
            Path(extract_to).mkdir(parents=True, exist_ok=True)
            
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(path=extract_to)
            
            print(f"✅ Extracted {archive_path} to {extract_to}")
            return extract_to
        except Exception as e:
            print(f"❌ Error extracting archive: {e}")
            raise
    
    def download_and_extract_archive(
        self, 
        object_name: str, 
        temp_dir: str = "./data/temp",
        extract_dir: str = "./data/raw"
    ) -> str:
        """
        Download an archive from MinIO and extract it.
        
        Args:
            object_name: Name of the archive in MinIO
            temp_dir: Temporary directory for download
            extract_dir: Directory where to extract files
            
        Returns:
            Path to the extracted directory
        """
        # Create temp directory
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        
        # Download archive
        archive_path = os.path.join(temp_dir, object_name)
        if not self.download_file(object_name, archive_path):
            raise Exception(f"Failed to download {object_name}")
        
        # Extract archive
        extracted_path = self.extract_archive(archive_path, extract_dir)
        
        # Clean up downloaded archive
        try:
            os.remove(archive_path)
            print(f"🗑️ Cleaned up temporary file: {archive_path}")
        except Exception as e:
            print(f"⚠️ Could not remove temporary file: {e}")
        
        return extracted_path


# Singleton instance
_storage_service = None


def get_storage_service() -> MinIOStorageService:
    """Get or create the MinIO storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = MinIOStorageService()
    return _storage_service
