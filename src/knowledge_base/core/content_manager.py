"""
Core content management functionality.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..storage.database import Database
from ..ai.llm_manager import LLMManager
from ..ai.embedding_manager import EmbeddingManager
from ..utils.validators import URLValidator, ContentValidator, ValidationError
from ..utils.logger import get_logger
# from ..extractors.arxiv import ArxivExtractor
# from ..extractors.github import GitHubExtractor
from ..extractors.web import WebExtractor
# from ..extractors.youtube import YouTubeExtractor
from ..extractors.base import ContentExtractor, ExtractionError

logger = get_logger(__name__)

class ContentManager:
    """Manages content processing and storage."""
    
    def __init__(
        self,
        db: Database,
        llm_manager: LLMManager,
        embedding_manager: EmbeddingManager
    ):
        self.db = db
        self.llm_manager = llm_manager
        self.embedding_manager = embedding_manager
        
        # Initialize extractors
        self.extractors: Dict[str, ContentExtractor] = {
            'arxiv': ArxivExtractor(),
            'github': GitHubExtractor(),
            'youtube': YouTubeExtractor(),
            'web': WebExtractor(),
        }
    
    def get_extractor(self, url: str) -> ContentExtractor:
        """Get appropriate extractor for a URL.
        
        Args:
            url: URL to get extractor for
            
        Returns:
            Appropriate ContentExtractor instance
            
        Raises:
            ValidationError: If URL is invalid
            ExtractionError: If no suitable extractor is found
        """
        url = URLValidator.normalize_url(url)
        
        # Try each extractor
        for extractor in self.extractors.values():
            if extractor.can_handle(url):
                return extractor
        
        # Default to web extractor
        return self.extractors['web']
    
    async def process_content(self, content: str, content_type: str) -> Dict[str, Any]:
        """Process raw content.
        
        Args:
            content: Raw content to process
            content_type: Type of content
            
        Returns:
            Processed content with summary, embeddings, etc.
            
        Raises:
            ValidationError: If content is invalid
        """
        # Process content in parallel
        summary_task = self.llm_manager.summarize(content, content_type)
        keywords_task = self.llm_manager.extract_keywords(content)
        embedding_task = self.embedding_manager.generate_embedding(content)
        
        summary, keywords, embedding = await asyncio.gather(
            summary_task, keywords_task, embedding_task
        )
        
        return {
            'content': content,
            'summary': summary,
            'keywords': keywords,
            'embedding': embedding
        }
    
    async def process_url(self, url: str) -> Dict[str, Any]:
        """Process content from a URL.
        
        Args:
            url: URL to process
            
        Returns:
            Processed content dictionary
            
        Raises:
            ValidationError: If URL is invalid
            ExtractionError: If content cannot be extracted
        """
        # Get appropriate extractor
        extractor = self.get_extractor(url)
        
        # Extract content
        extracted = await extractor.extract(url)
        
        # Process the content
        processed = await self.process_content(
            extracted['content'],
            extracted['type']
        )
        
        # Combine extraction and processing results
        result = {
            **extracted,
            **processed,
            'timestamp': int(datetime.now().timestamp())
        }
        
        # Validate final content
        ContentValidator.validate_content(result)
        
        return result
    
    async def save_content(self, content: Dict[str, Any]) -> str:
        """Save processed content.
        
        Args:
            content: Processed content to save
            
        Returns:
            ID of saved content
            
        Raises:
            ValidationError: If content is invalid
        """
        # Validate before saving
        ContentValidator.validate_content(content)
        
        # Save to database
        content_id = await self.db.store_content(content)
        
        logger.info(f"Saved content {content_id} from {content['url']}")
        return content_id
    
    async def find_similar(
        self,
        content_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find similar content.
        
        Args:
            content_id: ID of content to find similar items for
            limit: Maximum number of results
            
        Returns:
            List of similar content items
        """
        content = await self.db.get_content(content_id)
        if not content:
            raise ValueError(f"Content not found: {content_id}")
            
        return await self.db.find_similar(content['embedding'], limit)
    
    async def search(
        self,
        query: str,
        content_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search content.
        
        Args:
            query: Search query
            content_type: Optional type to filter by
            limit: Maximum number of results
            
        Returns:
            List of matching content items
        """
        # Generate query embedding
        embedding = await self.embedding_manager.generate_embedding(query)
        
        # Build search parameters
        search_params = {
            'embedding': embedding,
            'text_search': query
        }
        
        if content_type:
            search_params['type'] = content_type
            
        return await self.db.search_content(search_params, limit)
    
    async def update_all_embeddings(self) -> None:
        """Update embeddings for all content using current model."""
        content_items = await self.db.get_all_content()
        for item in content_items:
            try:
                new_embedding = await self.embedding_manager.generate_embedding(
                    item['content']
                )
                await self.db.update_content(
                    item['id'],
                    {'embedding': new_embedding}
                )
                logger.info(f"Updated embeddings for content {item['id']}")
            except Exception as e:
                logger.error(f"Error updating embeddings for {item['id']}: {e}")