"""
Base extractor interface for all content extractors.

This module defines the base interface that all content extractors must implement.
Each extractor is responsible for handling a specific type of content source
(e.g., ArXiv, GitHub, YouTube, etc.).
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from urllib.parse import urlparse

class ContentExtractor(ABC):
    """Base class for all content extractors.
    
    This abstract class defines the interface that all content extractors must implement.
    Each extractor is responsible for:
    1. Determining if it can handle a given URL
    2. Extracting content from that URL
    3. Returning a standardized content dictionary
    """
    
    @abstractmethod
    def extract(self, url: str) -> Dict[str, Any]:
        """Extract content from the given URL.
        
        Args:
            url: The URL to extract content from.
            
        Returns:
            A dictionary containing:
                - content: The extracted content as text
                - type: The type of content (e.g., 'arxiv', 'github')
                - url: The original URL
                - metadata: Additional metadata specific to the content type
                
        Raises:
            ExtractionError: If content cannot be extracted
            ValueError: If the URL is invalid
        """
        pass

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL.
        
        Args:
            url: The URL to check
            
        Returns:
            True if this extractor can handle the URL, False otherwise
        """
        pass

    def clean_url(self, url: str) -> str:
        """Clean and normalize a URL.
        
        Args:
            url: The URL to clean
            
        Returns:
            A cleaned and normalized URL string
            
        Raises:
            ValueError: If the URL is invalid
        """
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Validate URL
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError("Invalid URL")
        except Exception as e:
            raise ValueError(f"Invalid URL: {e}")
            
        # Remove trailing slashes
        url = url.rstrip('/')
        
        return url

    def clean_text(self, text: str) -> str:
        """Clean extracted text content.
        
        Args:
            text: The text to clean
            
        Returns:
            Cleaned text with normalized whitespace and removed control characters
        """
        if not text:
            return ""
            
        # Remove control characters
        text = ''.join(char for char in text if char.isprintable())
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove empty lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(line for line in lines if line)
        
        return text.strip()

    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract basic metadata from content.
        
        Args:
            content: The content to extract metadata from
            
        Returns:
            Dictionary of basic metadata like length, language, etc.
        """
        return {
            'length': len(content),
            'lines': len(content.split('\n')),
            'words': len(content.split()),
            'extracted_at': self.get_timestamp()
        }
    
    def get_timestamp(self) -> int:
        """Get current timestamp.
        
        Returns:
            Current Unix timestamp in seconds
        """
        from datetime import datetime
        return int(datetime.now().timestamp())

class ExtractionError(Exception):
    """Base exception for content extraction errors."""
    pass