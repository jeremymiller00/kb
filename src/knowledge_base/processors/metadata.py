"""
Metadata extraction and processing for knowledge base content.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

from ..utils.logger import get_logger

logger = get_logger(__name__)

class MetadataProcessor:
    """Processor for extracting and enriching content metadata."""
    
    def __init__(self):
        """Initialize metadata processor."""
        self.metadata_extractors = {
            'arxiv': self._extract_arxiv_metadata,
            'github': self._extract_github_metadata,
            'youtube': self._extract_youtube_metadata,
            'web': self._extract_web_metadata,
        }
    
    async def extract_metadata(
        self,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract metadata from content.
        
        Args:
            content: Content dictionary
            
        Returns:
            Dictionary of extracted metadata
        """
        try:
            # Get base metadata
            metadata = self._extract_base_metadata(content)
            
            # Add content-type specific metadata
            content_type = content.get('type', 'web')
            if extractor := self.metadata_extractors.get(content_type):
                type_metadata = await extractor(content)
                metadata.update(type_metadata)
            
            # Add computed metadata
            metadata.update(self._compute_metadata(content))
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}
    
    def _extract_base_metadata(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic metadata common to all content types.
        
        Args:
            content: Content dictionary
            
        Returns:
            Base metadata dictionary
        """
        metadata = {
            'processed_at': datetime.now().isoformat(),
            'content_length': len(content.get('content', '')),
            'word_count': len(content.get('content', '').split()),
            'has_summary': bool(content.get('summary')),
            'keyword_count': len(content.get('keywords', [])),
            'url_domain': urlparse(content.get('url', '')).netloc
        }
        
        # Add language detection
        try:
            from langdetect import detect
            metadata['language'] = detect(content.get('content', ''))
        except:
            metadata['language'] = 'unknown'
            
        return metadata
    
    async def _extract_arxiv_metadata(
        self,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract ArXiv-specific metadata.
        
        Args:
            content: Content dictionary
            
        Returns:
            ArXiv metadata dictionary
        """
        metadata = {}
        
        try:
            # Extract paper ID
            if match := re.search(r'(\d{4}\.\d{4,5})', content['url']):
                metadata['arxiv_id'] = match.group(1)
            
            # Parse content for additional metadata
            text = content.get('content', '')
            
            # Extract authors
            if author_match := re.search(
                r'Authors?:(.*?)(?:\n\n|\Z)',
                text,
                re.DOTALL
            ):
                authors = [
                    author.strip()
                    for author in author_match.group(1).split(',')
                    if author.strip()
                ]
                metadata['authors'] = authors
            
            # Extract categories
            if cat_match := re.search(
                r'Categories?:(.*?)(?:\n\n|\Z)',
                text,
                re.DOTALL
            ):
                categories = [
                    cat.strip()
                    for cat in cat_match.group(1).split(',')
                    if cat.strip()
                ]
                metadata['categories'] = categories
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting ArXiv metadata: {e}")
            return metadata
    
    async def _extract_github_metadata(
        self,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract GitHub-specific metadata.
        
        Args:
            content: Content dictionary
            
        Returns:
            GitHub metadata dictionary
        """
        metadata = {}
        
        try:
            # Parse GitHub URL
            url_parts = content['url'].split('/')
            if len(url_parts) >= 5:
                metadata['github_user'] = url_parts[3]
                metadata['github_repo'] = url_parts[4]
            
            # Extract from content
            text = content.get('content', '')
            
            # Find programming languages
            language_patterns = [
                r'(?i)built with\s*(.*?)(?:\n|$)',
                r'(?i)written in\s*(.*?)(?:\n|$)',
                r'(?i)using\s*(.*?)(?:\n|$)'
            ]
            
            languages = set()
            for pattern in language_patterns:
                if matches := re.finditer(pattern, text):
                    for match in matches:
                        langs = [
                            lang.strip()
                            for lang in match.group(1).split(',')
                        ]
                        languages.update(langs)
            
            if languages:
                metadata['languages'] = list(languages)
            
            # Check for common sections
            sections = {
                'has_installation': bool(
                    re.search(r'(?i)(\#|\b)install(ation)?(\#|\b)', text)
                ),
                'has_usage': bool(
                    re.search(r'(?i)(\#|\b)usage(\#|\b)', text)
                ),
                'has_contributing': bool(
                    re.search(r'(?i)(\#|\b)contribut(e|ing)(\#|\b)', text)
                ),
                'has_license': bool(
                    re.search(r'(?i)(\#|\b)license(\#|\b)', text)
                )
            }
            metadata.update(sections)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting GitHub metadata: {e}")
            return metadata
    
    async def _extract_youtube_metadata(
        self,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract YouTube-specific metadata.
        
        Args:
            content: Content dictionary
            
        Returns:
            YouTube metadata dictionary
        """
        metadata = {}
        
        try:
            # Extract video ID
            if match := re.search(
                r'(?:v=|/)([a-zA-Z0-9_-]{11})(?:\?|&|/|$)',
                content['url']
            ):
                metadata['video_id'] = match.group(1)
            
            # Process transcript content
            text = content.get('content', '')
            
            # Calculate transcript statistics
            lines = text.split('\n')
            metadata['transcript_lines'] = len(lines)
            metadata['transcript_words'] = len(text.split())
            
            # Detect if transcript appears to be auto-generated
            metadata['likely_auto_generated'] = '[Music]' in text
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting YouTube metadata: {e}")
            return metadata
    
    async def _extract_web_metadata(
        self,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract web-specific metadata.
        
        Args:
            content: Content dictionary
            
        Returns:
            Web metadata dictionary
        """
        metadata = {}
        
        try:
            # Try to get page metadata
            response = requests.get(
                content['url'],
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=10
            )
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get meta tags
            meta_tags = {}
            for tag in soup.find_all('meta'):
                name = tag.get('name', tag.get('property', ''))
                if name and (content := tag.get('content')):
                    meta_tags[name] = content
            
            # Extract useful metadata
            if 'description' in meta_tags:
                metadata['page_description'] = meta_tags['description']
            
            if 'author' in meta_tags:
                metadata['page_author'] = meta_tags['author']
            
            if 'keywords' in meta_tags:
                metadata['page_keywords'] = [
                    k.strip()
                    for k in meta_tags['keywords'].split(',')
                ]
            
            if pub_date := (
                meta_tags.get('article:published_time') or
                meta_tags.get('date')
            ):
                metadata['published_date'] = pub_date
            
            # Get RSS/Atom feeds
            feeds = []
            for link in soup.find_all('link', type=re.compile(r'application/(rss|atom)\+xml')):
                feeds.append({
                    'title': link.get('title', ''),
                    'href': link['href']
                })
            if feeds:
                metadata['feeds'] = feeds
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting web metadata: {e}")
            return metadata
    
    def _compute_metadata(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Compute additional metadata from content.
        
        Args:
            content: Content dictionary
            
        Returns:
            Computed metadata dictionary
        """
        metadata = {}
        
        try:
            text = content.get('content', '')
            
            # Extract entities (URLs, emails, etc.)
            metadata['urls'] = re.findall(
                r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                text
            )
            
            metadata['emails'] = re.findall(
                r'[\w\.-]+@[\w\.-]+\.\w+',
                text
            )
            
            # Calculate reading time
            words_per_minute = 200
            word_count = len(text.split())
            metadata['reading_time_minutes'] = round(word_count / words_per_minute)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error computing metadata: {e}")
            return metadata