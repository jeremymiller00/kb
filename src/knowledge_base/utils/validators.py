"""
Validation utilities for the knowledge base application.

This module provides validators for:
- URLs
- Content types
- File formats
- Data structures
- Database entries
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urlparse
import json
import magic
from datetime import datetime

class ValidationError(Exception):
    """Base exception for validation errors."""
    pass

class URLValidator:
    """Validator for URLs."""
    
    # Known content source domains
    KNOWN_DOMAINS = {
        'arxiv.org',
        'github.com',
        'youtube.com',
        'youtu.be',
        'huggingface.co',
        'twitter.com',
        'linkedin.com'
    }
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if a URL is valid.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def get_source_type(url: str) -> str:
        """Determine the source type from a URL.
        
        Args:
            url: URL to check
            
        Returns:
            Source type (e.g., 'arxiv', 'github', 'youtube', etc.)
        
        Raises:
            ValidationError: If URL is invalid
        """
        if not URLValidator.is_valid_url(url):
            raise ValidationError(f"Invalid URL: {url}")
            
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
            
        if 'arxiv.org' in domain:
            return 'arxiv'
        elif 'github.com' in domain:
            if url.endswith('.ipynb'):
                return 'github_notebook'
            return 'github'
        elif any(yt in domain for yt in ['youtube.com', 'youtu.be']):
            return 'youtube'
        elif 'huggingface.co' in domain:
            return 'huggingface'
        
        return 'web'
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize a URL for consistent handling.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
            
        Raises:
            ValidationError: If URL is invalid
        """
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        if not URLValidator.is_valid_url(url):
            raise ValidationError(f"Invalid URL: {url}")
            
        return url.rstrip('/')

class ContentValidator:
    """Validator for content data structures."""
    
    REQUIRED_FIELDS = {
        'content',
        'type',
        'url',
        'timestamp'
    }
    
    KNOWN_TYPES = {
        'arxiv',
        'github',
        'github_notebook',
        'youtube',
        'huggingface',
        'web'
    }
    
    @staticmethod
    def validate_content(content: Dict[str, Any]) -> None:
        """Validate a content dictionary.
        
        Args:
            content: Content dictionary to validate
            
        Raises:
            ValidationError: If content is invalid
        """
        # Check required fields
        missing_fields = ContentValidator.REQUIRED_FIELDS - set(content.keys())
        if missing_fields:
            raise ValidationError(f"Missing required fields: {missing_fields}")
        
        # Validate content type
        if content['type'] not in ContentValidator.KNOWN_TYPES:
            raise ValidationError(f"Unknown content type: {content['type']}")
        
        # Validate URL
        if not URLValidator.is_valid_url(content['url']):
            raise ValidationError(f"Invalid URL: {content['url']}")
        
        # Validate timestamp
        try:
            timestamp = int(content['timestamp'])
            if timestamp < 0 or timestamp > int(datetime.now().timestamp()):
                raise ValidationError(f"Invalid timestamp: {timestamp}")
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid timestamp format: {content['timestamp']}")

class FileValidator:
    """Validator for files and file formats."""
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    ALLOWED_MIME_TYPES = {
        'text/plain',
        'text/markdown',
        'text/html',
        'application/json',
        'application/pdf',
        'application/x-ipynb+json'
    }
    
    @staticmethod
    def validate_file_size(file_path: Union[str, Path]) -> None:
        """Validate file size.
        
        Args:
            file_path: Path to file
            
        Raises:
            ValidationError: If file is too large
        """
        file_size = Path(file_path).stat().st_size
        if file_size > FileValidator.MAX_FILE_SIZE:
            raise ValidationError(
                f"File too large: {file_size} bytes "
                f"(max {FileValidator.MAX_FILE_SIZE} bytes)"
            )
    
    @staticmethod
    def validate_mime_type(file_path: Union[str, Path]) -> None:
        """Validate file MIME type.
        
        Args:
            file_path: Path to file
            
        Raises:
            ValidationError: If file type is not allowed
        """
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(str(file_path))
        
        if file_type not in FileValidator.ALLOWED_MIME_TYPES:
            raise ValidationError(f"Unsupported file type: {file_type}")
    
    @staticmethod
    def validate_json_format(file_path: Union[str, Path]) -> None:
        """Validate JSON file format.
        
        Args:
            file_path: Path to JSON file
            
        Raises:
            ValidationError: If JSON is invalid
        """
        try:
            with open(file_path) as f:
                json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format: {e}")
    
    @staticmethod
    def validate_notebook_format(file_path: Union[str, Path]) -> None:
        """Validate Jupyter notebook format.
        
        Args:
            file_path: Path to notebook file
            
        Raises:
            ValidationError: If notebook format is invalid
        """
        try:
            with open(file_path) as f:
                notebook = json.load(f)
            
            required_fields = {'cells', 'metadata', 'nbformat'}
            if not all(field in notebook for field in required_fields):
                raise ValidationError(
                    f"Invalid notebook format: missing required fields "
                    f"{required_fields - set(notebook.keys())}"
                )
        except Exception as e:
            raise ValidationError(f"Invalid notebook format: {e}")

def validate_embedding_dimensions(embedding: List[float], expected_dim: int = 384) -> None:
    """Validate embedding dimensions.
    
    Args:
        embedding: Embedding vector to validate
        expected_dim: Expected dimension size
        
    Raises:
        ValidationError: If dimensions don't match
    """
    if len(embedding) != expected_dim:
        raise ValidationError(
            f"Invalid embedding dimensions: got {len(embedding)}, "
            f"expected {expected_dim}"
        )