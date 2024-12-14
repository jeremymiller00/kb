"""
Content processing pipeline.
"""

import asyncio
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime

from ..ai.llm_manager import LLMManager
from ..ai.embedding_manager import EmbeddingManager
from .metadata import MetadataProcessor
from .text import TextProcessor
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ProcessingStep:
    """Single step in the processing pipeline."""
    
    def __init__(
        self,
        name: str,
        processor: Callable,
        required: bool = True
    ):
        """Initialize processing step.
        
        Args:
            name: Step name
            processor: Processing function
            required: Whether step is required
        """
        self.name = name
        self.processor = processor
        self.required = required
        
    async def execute(
        self,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute processing step.
        
        Args:
            content: Content to process
            
        Returns:
            Processed content
            
        Raises:
            ProcessingError: If required step fails
        """
        try:
            return await self.processor(content)
        except Exception as e:
            if self.required:
                raise ProcessingError(
                    f"Required step {self.name} failed: {e}"
                ) from e
            logger.warning(f"Optional step {self.name} failed: {e}")
            return content

class ProcessingError(Exception):
    """Error during content processing."""
    pass

class ProcessingPipeline:
    """Pipeline for processing content."""
    
    def __init__(
        self,
        llm_manager: LLMManager,
        embedding_manager: EmbeddingManager
    ):
        """Initialize processing pipeline.
        
        Args:
            llm_manager: LLM manager instance
            embedding_manager: Embedding manager instance
        """
        self.llm_manager = llm_manager
        self.embedding_manager = embedding_manager
        self.text_processor = TextProcessor()
        self.metadata_processor = MetadataProcessor()
        self.steps: List[ProcessingStep] = []
        self._setup_pipeline()
    
    def _setup_pipeline(self) -> None:
        """Set up processing steps."""
        self.steps = [
            ProcessingStep(
                "text_cleaning",
                self.text_processor.clean_text,
                required=True
            ),
            ProcessingStep(
                "text_normalization",
                self.text_processor.normalize_text,
                required=True
            ),
            ProcessingStep(
                "metadata_extraction",
                self.metadata_processor.extract_metadata,
                required=False
            ),
            ProcessingStep(
                "summarization",
                self._generate_summary,
                required=False
            ),
            ProcessingStep(
                "keyword_extraction",
                self._extract_keywords,
                required=False
            ),
            ProcessingStep(
                "embedding_generation",
                self._generate_embedding,
                required=True
            )
        ]
    
    async def _generate_summary(
        self,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate content summary.
        
        Args:
            content: Content to summarize
            
        Returns:
            Content with summary
        """
        content['summary'] = await self.llm_manager.summarize(
            content['content'],
            content.get('type', 'web')
        )
        return content
    
    async def _extract_keywords(
        self,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract keywords from content.
        
        Args:
            content: Content to extract keywords from
            
        Returns:
            Content with keywords
        """
        content['keywords'] = await self.llm_manager.extract_keywords(
            content['content']
        )
        return content
    
    async def _generate_embedding(
        self,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate content embedding.
        
        Args:
            content: Content to generate embedding for
            
        Returns:
            Content with embedding
        """
        content['embedding'] = await self.embedding_manager.generate_embedding(
            content['content']
        )
        return content
    
    async def process(
        self,
        content: Dict[str, Any],
        steps: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Process content through pipeline.
        
        Args:
            content: Content to process
            steps: Optional list of specific steps to run
            
        Returns:
            Processed content
            
        Raises:
            ProcessingError: If required step fails
        """
        processed = content.copy()
        
        try:
            # Add processing metadata
            processed['processing'] = {
                'started_at': datetime.now().isoformat(),
                'steps': []
            }
            
            # Run steps
            for step in self.steps:
                if not steps or step.name in steps:
                    start_time = datetime.now()
                    try:
                        processed = await step.execute(processed)
                        status = 'success'
                    except Exception as e:
                        status = 'error'
                        error_msg = str(e)
                        if step.required:
                            raise
                    finally:
                        processed['processing']['steps'].append({
                            'name': step.name,
                            'status': status,
                            'duration': (
                                datetime.now() - start_time
                            ).total_seconds(),
                            'error': error_msg if status == 'error' else None
                        })
            
            processed['processing']['completed_at'] = datetime.now().isoformat()
            return processed
            
        except Exception as e:
            logger.error(f"Error processing content: {e}")
            raise ProcessingError(f"Processing pipeline failed: {e}") from e
    
    async def process_batch(
        self,
        contents: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """Process multiple content items concurrently.
        
        Args:
            contents: List of content items to process
            max_concurrent: Maximum number of concurrent processes
            
        Returns:
            List of processed content items
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(content: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await self.process(content)
        
        return await asyncio.gather(
            *[process_with_semaphore(content) for content in contents],
            return_exceptions=True
        )