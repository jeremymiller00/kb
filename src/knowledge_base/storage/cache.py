"""
Cache management for the knowledge base.
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional, Union
import json
from datetime import datetime, timedelta
from collections import OrderedDict
import threading
import pickle
import hashlib
from ..utils.logger import get_logger

logger = get_logger(__name__)

class CacheError(Exception):
    """Base exception for cache errors."""
    pass

class Cache:
    """Memory and disk-based cache implementation."""
    
    def __init__(
        self,
        cache_dir: Path,
        memory_size: int = 1000,
        disk_size_bytes: int = 1_000_000_000,  # 1GB
        default_ttl: int = 3600  # 1 hour
    ):
        """Initialize cache.
        
        Args:
            cache_dir: Directory for disk cache
            memory_size: Maximum number of items in memory cache
            disk_size_bytes: Maximum disk cache size in bytes
            default_ttl: Default time-to-live in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.memory_size = memory_size
        self.disk_size_bytes = disk_size_bytes
        self.default_ttl = default_ttl
        
        # Memory cache using OrderedDict for LRU behavior
        self._memory_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.Lock()
        
        self._setup_cache()
    
    def _setup_cache(self) -> None:
        """Set up cache directories."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
        except Exception as e:
            raise CacheError(f"Failed to setup cache directory: {e}")
    
    def _get_cache_path(self, key: str) -> Path:
        """Get disk cache path for a key.
        
        Args:
            key: Cache key
            
        Returns:
            Path for disk cache file
        """
        # Use hash to avoid filesystem issues with long keys
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash[:2]}" / f"{key_hash[2:]}.cache"
    
    def _is_expired(self, metadata: Dict[str, Any]) -> bool:
        """Check if cache entry is expired.
        
        Args:
            metadata: Cache entry metadata
            
        Returns:
            True if expired, False otherwise
        """
        if 'expires_at' not in metadata:
            return False
        return datetime.fromisoformat(metadata['expires_at']) < datetime.now()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        # Try memory cache first
        with self._lock:
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                if not self._is_expired(entry['metadata']):
                    # Move to end for LRU
                    self._memory_cache.move_to_end(key)
                    return entry['value']
                else:
                    del self._memory_cache[key]
        
        # Try disk cache
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    entry = pickle.load(f)
                    
                if not self._is_expired(entry['metadata']):
                    # Store in memory cache
                    self.set(
                        key,
                        entry['value'],
                        ttl=entry['metadata'].get('ttl')
                    )
                    return entry['value']
                else:
                    # Clean up expired entry
                    cache_path.unlink()
                    
            except Exception as e:
                logger.error(f"Error reading cache file {cache_path}: {e}")
        
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Set cache value.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default_ttl if None)
        """
        ttl = ttl or self.default_ttl
        expires_at = (datetime.now() + timedelta(seconds=ttl)).isoformat()
        
        entry = {
            'value': value,
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at,
                'ttl': ttl
            }
        }
        
        # Update memory cache
        with self._lock:
            if len(self._memory_cache) >= self.memory_size:
                # Remove oldest item (first item in OrderedDict)
                self._memory_cache.popitem(last=False)
            self._memory_cache[key] = entry
        
        # Update disk cache
        try:
            cache_path = self._get_cache_path(key)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(cache_path, 'wb') as f:
                pickle.dump(entry, f)
                
            # Check disk cache size
            self._enforce_disk_limit()
            
        except Exception as e:
            logger.error(f"Error writing cache file {cache_path}: {e}")
    
    def delete(self, key: str) -> bool:
        """Delete cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was deleted, False if not found
        """
        deleted = False
        
        # Remove from memory cache
        with self._lock:
            if key in self._memory_cache:
                del self._memory_cache[key]
                deleted = True
        
        # Remove from disk cache
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                cache_path.unlink()
                deleted = True
            except Exception as e:
                logger.error(f"Error deleting cache file {cache_path}: {e}")
        
        return deleted
    
    def clear(self) -> None:
        """Clear all cache entries."""
        # Clear memory cache
        with self._lock:
            self._memory_cache.clear()
        
        # Clear disk cache
        try:
            for cache_file in self.cache_dir.rglob("*.cache"):
                cache_file.unlink()
        except Exception as e:
            logger.error(f"Error clearing disk cache: {e}")
    
    def _enforce_disk_limit(self) -> None:
        """Enforce disk cache size limit."""
        try:
            total_size = 0
            cache_files = []
            
            # Get all cache files with their sizes and timestamps
            for cache_file in self.cache_dir.rglob("*.cache"):
                stat = cache_file.stat()
                cache_files.append({
                    'path': cache_file,
                    'size': stat.st_size,
                    'mtime': stat.st_mtime
                })
                total_size += stat.st_size
            
            # Remove oldest files until under limit
            if total_size > self.disk_size_bytes:
                for file_info in sorted(
                    cache_files,
                    key=lambda x: x['mtime']
                ):
                    file_info['path'].unlink()
                    total_size -= file_info['size']
                    if total_size <= self.disk_size_bytes:
                        break
                        
        except Exception as e:
            logger.error(f"Error enforcing disk cache limit: {e}")
    
    def cleanup(self) -> None:
        """Clean up expired entries."""
        # Clean memory cache
        with self._lock:
            expired_keys = [
                key for key, entry in self._memory_cache.items()
                if self._is_expired(entry['metadata'])
            ]
            for key in expired_keys:
                del self._memory_cache[key]
        
        # Clean disk cache
        try:
            for cache_file in self.cache_dir.rglob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        entry = pickle.load(f)
                        
                    if self._is_expired(entry['metadata']):
                        cache_file.unlink()
                        
                except Exception as e:
                    logger.error(f"Error checking cache file {cache_file}: {e}")
                    # Delete corrupted cache file
                    cache_file.unlink()
                    
        except Exception as e:
            logger.error(f"Error cleaning up disk cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        memory_size = len(self._memory_cache)
        
        disk_size = 0
        disk_files = 0
        try:
            for cache_file in self.cache_dir.rglob("*.cache"):
                disk_size += cache_file.stat().st_size
                disk_files += 1
        except Exception as e:
            logger.error(f"Error calculating disk cache stats: {e}")
        
        return {
            'memory_entries': memory_size,
            'memory_limit': self.memory_size,
            'disk_bytes': disk_size,
            'disk_limit': self.disk_size_bytes,
            'disk_files': disk_files
        }