"""
File storage management for the knowledge base.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, BinaryIO
from datetime import datetime
import hashlib
import json
import mimetypes
from ..utils.logger import get_logger

logger = get_logger(__name__)

class FileStorageError(Exception):
    """Base exception for file storage errors."""
    pass

class FileStorage:
    """Manages file storage for the knowledge base."""
    
    def __init__(
        self,
        base_path: Path,
        max_file_size: int = 100 * 1024 * 1024  # 100MB
    ):
        """Initialize file storage.
        
        Args:
            base_path: Base directory for file storage
            max_file_size: Maximum allowed file size in bytes
        """
        self.base_path = Path(base_path)
        self.max_file_size = max_file_size
        self._setup_storage()
    
    def _setup_storage(self) -> None:
        """Set up storage directories."""
        try:
            # Create main directories
            self.base_path.mkdir(parents=True, exist_ok=True)
            (self.base_path / 'files').mkdir(exist_ok=True)
            (self.base_path / 'metadata').mkdir(exist_ok=True)
            (self.base_path / 'temp').mkdir(exist_ok=True)
            
        except Exception as e:
            raise FileStorageError(f"Failed to setup storage directories: {e}")
    
    def _get_file_hash(self, file_obj: BinaryIO) -> str:
        """Calculate SHA-256 hash of a file.
        
        Args:
            file_obj: File object to hash
            
        Returns:
            Hex string of file hash
        """
        hasher = hashlib.sha256()
        for chunk in iter(lambda: file_obj.read(8192), b''):
            hasher.update(chunk)
        file_obj.seek(0)
        return hasher.hexdigest()
    
    def _get_storage_path(self, file_hash: str) -> Path:
        """Get storage path for a file based on its hash.
        
        Args:
            file_hash: File hash
            
        Returns:
            Path where file should be stored
        """
        # Use hash to create directory structure
        return (self.base_path / 'files' / 
                file_hash[:2] / file_hash[2:4] / file_hash)
    
    def _get_metadata_path(self, file_hash: str) -> Path:
        """Get metadata path for a file.
        
        Args:
            file_hash: File hash
            
        Returns:
            Path where metadata should be stored
        """
        return (self.base_path / 'metadata' / 
                file_hash[:2] / file_hash[2:4] / f"{file_hash}.json")
    
    def _store_metadata(
        self,
        file_hash: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Store file metadata.
        
        Args:
            file_hash: File hash
            metadata: Metadata to store
        """
        metadata_path = self._get_metadata_path(file_hash)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _get_metadata(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get file metadata.
        
        Args:
            file_hash: File hash
            
        Returns:
            Metadata dictionary if found, None otherwise
        """
        metadata_path = self._get_metadata_path(file_hash)
        if metadata_path.exists():
            with open(metadata_path) as f:
                return json.load(f)
        return None
    
    def store_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a file.
        
        Args:
            file_obj: File object to store
            filename: Original filename
            metadata: Optional metadata
            
        Returns:
            File hash
            
        Raises:
            FileStorageError: If file cannot be stored
        """
        try:
            # Check file size
            file_obj.seek(0, os.SEEK_END)
            size = file_obj.tell()
            file_obj.seek(0)
            
            if size > self.max_file_size:
                raise FileStorageError(
                    f"File too large: {size} bytes "
                    f"(max {self.max_file_size} bytes)"
                )
            
            # Calculate hash
            file_hash = self._get_file_hash(file_obj)
            storage_path = self._get_storage_path(file_hash)
            
            # Store file if it doesn't exist
            if not storage_path.exists():
                storage_path.parent.mkdir(parents=True, exist_ok=True)
                with open(storage_path, 'wb') as f:
                    shutil.copyfileobj(file_obj, f)
            
            # Store metadata
            full_metadata = {
                'filename': filename,
                'size': size,
                'mime_type': (mimetypes.guess_type(filename)[0] or 
                             'application/octet-stream'),
                'stored_at': datetime.now().isoformat(),
                'hash': file_hash
            }
            if metadata:
                full_metadata.update(metadata)
            
            self._store_metadata(file_hash, full_metadata)
            
            return file_hash
            
        except Exception as e:
            raise FileStorageError(f"Failed to store file: {e}")
    
    def get_file(self, file_hash: str) -> Optional[Path]:
        """Get path to a stored file.
        
        Args:
            file_hash: Hash of file to retrieve
            
        Returns:
            Path to file if found, None otherwise
        """
        storage_path = self._get_storage_path(file_hash)
        return storage_path if storage_path.exists() else None
    
    def delete_file(self, file_hash: str) -> bool:
        """Delete a stored file.
        
        Args:
            file_hash: Hash of file to delete
            
        Returns:
            True if file was deleted, False if not found
        """
        storage_path = self._get_storage_path(file_hash)
        metadata_path = self._get_metadata_path(file_hash)
        
        deleted = False
        if storage_path.exists():
            storage_path.unlink()
            deleted = True
        
        if metadata_path.exists():
            metadata_path.unlink()
            deleted = True
        
        return deleted
    
    def list_files(self) -> Dict[str, Dict[str, Any]]:
        """List all stored files.
        
        Returns:
            Dictionary mapping file hashes to their metadata
        """
        files = {}
        for metadata_path in (self.base_path / 'metadata').rglob('*.json'):
            with open(metadata_path) as f:
                metadata = json.load(f)
                files[metadata['hash']] = metadata
        return files
    
    def cleanup_temp(self, max_age_hours: int = 24) -> None:
        """Clean up temporary files.
        
        Args:
            max_age_hours: Maximum age of temp files in hours
        """
        temp_dir = self.base_path / 'temp'
        if not temp_dir.exists():
            return
            
        now = datetime.now()
        for item in temp_dir.iterdir():
            if item.is_file():
                age = now - datetime.fromtimestamp(item.stat().st_mtime)
                if age.total_seconds() > max_age_hours * 3600:
                    item.unlink()
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Dictionary of storage statistics
        """
        total_size = 0
        total_files = 0
        mime_types = {}
        
        for file_path in (self.base_path / 'files').rglob('*'):
            if file_path.is_file():
                total_files += 1
                size = file_path.stat().st_size
                total_size += size
                
                metadata = self._get_metadata(file_path.name)
                if metadata and 'mime_type' in metadata:
                    mime_types[metadata['mime_type']] = \
                        mime_types.get(metadata['mime_type'], 0) + 1
        
        return {
            'total_size': total_size,
            'total_files': total_files,
            'mime_types': mime_types,
            'space_available': shutil.disk_usage(str(self.base_path)).free
        }