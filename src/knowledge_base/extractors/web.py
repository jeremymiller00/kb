"""
Web content extractor for general web pages.

This module handles extraction of content from general web pages, including:
- Article content
- Blog posts
- Documentation pages
- General web content

It attempts to extract meaningful content while filtering out navigation, ads, etc.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urlparse
import trafilatura
from readability import Document
import html2text

from .base import ContentExtractor, ExtractionError
from ..utils.logger import get_logger

logger = get_logger(__name__)

class WebExtractor(ContentExtractor):
    """Extractor for general web content."""
    
    def __init__(self):
        """Initialize the web extractor with configuration."""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/91.0.4472.114 Safari/537.36"
        }
        # Sites that need special handling
        self.special_domains = {
            'arxiv.org',
            'github.com',
            'youtube.com',
            'youtu.be',
            'huggingface.co',
            'twitter.com',
            'linkedin.com'
        }
        
    def can_handle(self, url: str) -> bool:
        """Check if this extractor should handle the given URL.
        
        Args:
            url: The URL to check
            
        Returns:
            True if this extractor should handle the URL, False if it should
            be handled by a more specific extractor
        """
        try:
            parsed = urlparse(self.clean_url(url))
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            # Return False if this should be handled by a specific extractor
            return domain not in self.special_domains
        except ValueError:
            return False
            
    def _get_main_content_readability(self, html: str) -> str:
        """Extract main content using readability-lxml.
        
        Args:
            html: The raw HTML content
            
        Returns:
            Extracted main content
        """
        doc = Document(html)
        return doc.summary()
        
    def _get_main_content_trafilatura(self, html: str) -> Optional[str]:
        """Extract main content using trafilatura.
        
        Args:
            html: The raw HTML content
            
        Returns:
            Extracted main content or None if extraction fails
        """
        return trafilatura.extract(html)
        
    def _extract_metadata_from_html(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from HTML using meta tags and other indicators.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # Try to get title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.text.strip()
            
        # Try to get meta description
        desc_tag = soup.find('meta', {'name': 'description'})
        if desc_tag:
            metadata['description'] = desc_tag.get('content', '').strip()
            
        # Try to get author
        author_tag = soup.find('meta', {'name': 'author'}) or \
                    soup.find('meta', {'property': 'article:author'})
        if author_tag:
            metadata['author'] = author_tag.get('content', '').strip()
            
        # Try to get publication date
        date_tag = soup.find('meta', {'property': 'article:published_time'}) or \
                  soup.find('meta', {'name': 'publish-date'})
        if date_tag:
            metadata['published_date'] = date_tag.get('content', '').strip()
            
        return metadata
        
    def _clean_extracted_content(self, content: str) -> str:
        """Clean up extracted content by removing excess whitespace, scripts, etc.
        
        Args:
            content: The content to clean
            
        Returns:
            Cleaned content
        """
        if not content:
            return ""
            
        # Convert HTML to markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_tables = False
        markdown_content = h.handle(content)
        
        # Clean up markdown
        lines = markdown_content.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.isspace():
                cleaned_lines.append(line)
                
        return '\n'.join(cleaned_lines)
        
    def _get_word_count(self, content: str) -> int:
        """Get the word count of the content.
        
        Args:
            content: The content to count words in
            
        Returns:
            Number of words
        """
        return len(re.findall(r'\w+', content))
        
    async def extract(self, url: str) -> Dict[str, Any]:
        """Extract content from a web page.
        
        Args:
            url: The URL to extract content from
            
        Returns:
            Dictionary containing:
                - content: The extracted content as markdown
                - type: 'web'
                - url: The original URL
                - metadata: Additional metadata about the page
                
        Raises:
            ExtractionError: If content cannot be extracted
        """
        url = self.clean_url(url)
        
        try:
            # Fetch the page
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            html = response.text
            
            # Try different content extraction methods
            content = self._get_main_content_trafilatura(html)
            if not content or self._get_word_count(content) < 100:
                content = self._get_main_content_readability(html)
                
            if not content:
                raise ExtractionError("No content could be extracted")
                
            # Clean the content
            content = self._clean_extracted_content(content)
            
            # Get metadata
            soup = BeautifulSoup(html, 'html.parser')
            metadata = self._extract_metadata_from_html(soup)
            
            # Add additional metadata
            metadata.update(self.extract_metadata(content))
            metadata['word_count'] = self._get_word_count(content)
            
            return {
                'content': content,
                'type': 'web',
                'url': url,
                'metadata': metadata
            }
            
        except requests.RequestException as e:
            raise ExtractionError(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            raise ExtractionError(f"Failed to extract content: {str(e)}")
            
    def is_paywall_content(self, html: str) -> bool:
        """Check if the content is behind a paywall.
        
        Args:
            html: The HTML content to check
            
        Returns:
            True if paywall indicators are found
        """
        paywall_indicators = {
            'paywall',
            'subscribe',
            'subscription',
            'become a member',
            'paid content'
        }
        
        text = html.lower()
        return any(indicator in text for indicator in paywall_indicators)