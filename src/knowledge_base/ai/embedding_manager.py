"""
Embedding generation and management.
"""

import numpy as np
from typing import List, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
from pathlib import Path

from ..utils.logger import get_logger

logger = get_logger(__name__)

class EmbeddingDimensionError(Exception):
    """Error for mismatched embedding dimensions."""
    pass

class EmbeddingManager:
    """Manager for generating and handling embeddings."""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_dir: Optional[Path] = None,
        embedding_dim: int = 384
    ):
        """Initialize embedding manager.
        
        Args:
            model_name: Name of the sentence transformer model
            cache_dir: Directory for caching model files
            embedding_dim: Expected embedding dimension
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.embedding_dim = embedding_dim
        self._model = None
        self._setup_model()
    
    def _setup_model(self) -> None:
        """Set up the embedding model."""
        try:
            self._model = SentenceTransformer(
                self.model_name,
                cache_folder=str(self.cache_dir) if self.cache_dir else None
            )
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
    
    async def generate_embedding(
        self,
        text: str,
        normalize: bool = True
    ) -> np.ndarray:
        """Generate embedding for text.
        
        Args:
            text: Text to generate embedding for
            normalize: Whether to L2-normalize the embedding
            
        Returns:
            Embedding vector
            
        Raises:
            EmbeddingDimensionError: If embedding dimension is wrong
        """
        try:
            # Generate embedding
            embedding = self._model.encode(
                text,
                normalize_embeddings=normalize
            )
            
            # Validate dimension
            if len(embedding) != self.embedding_dim:
                raise EmbeddingDimensionError(
                    f"Expected dimension {self.embedding_dim}, "
                    f"got {len(embedding)}"
                )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_batch_embeddings(
        self,
        texts: List[str],
        batch_size: int = 32,
        normalize: bool = True
    ) -> np.ndarray:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts
            batch_size: Batch size for processing
            normalize: Whether to L2-normalize embeddings
            
        Returns:
            Array of embeddings
            
        Raises:
            EmbeddingDimensionError: If embedding dimensions are wrong
        """
        try:
            # Generate embeddings
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize
            )
            
            # Validate dimensions
            if embeddings.shape[1] != self.embedding_dim:
                raise EmbeddingDimensionError(
                    f"Expected dimension {self.embedding_dim}, "
                    f"got {embeddings.shape[1]}"
                )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """Compute cosine similarity between embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score
            
        Raises:
            EmbeddingDimensionError: If dimensions don't match
        """
        # Validate dimensions
        if len(embedding1) != self.embedding_dim:
            raise EmbeddingDimensionError(
                f"embedding1: Expected dimension {self.embedding_dim}, "
                f"got {len(embedding1)}"
            )
        if len(embedding2) != self.embedding_dim:
            raise EmbeddingDimensionError(
                f"embedding2: Expected dimension {self.embedding_dim}, "
                f"got {len(embedding2)}"
            )
        
        # Normalize if needed
        if not np.allclose(np.linalg.norm(embedding1), 1.0):
            embedding1 = embedding1 / np.linalg.norm(embedding1)
        if not np.allclose(np.linalg.norm(embedding2), 1.0):
            embedding2 = embedding2 / np.linalg.norm(embedding2)
        
        return float(np.dot(embedding1, embedding2))
    
    def compute_batch_similarities(
        self,
        embeddings1: np.ndarray,
        embeddings2: np.ndarray
    ) -> np.ndarray:
        """Compute similarities between batches of embeddings.
        
        Args:
            embeddings1: First batch of embeddings
            embeddings2: Second batch of embeddings
            
        Returns:
            Matrix of similarity scores
            
        Raises:
            EmbeddingDimensionError: If dimensions don't match
        """
        # Validate dimensions
        if embeddings1.shape[1] != self.embedding_dim:
            raise EmbeddingDimensionError(
                f"embeddings1: Expected dimension {self.embedding_dim}, "
                f"got {embeddings1.shape[1]}"
            )
        if embeddings2.shape[1] != self.embedding_dim:
            raise EmbeddingDimensionError(
                f"embeddings2: Expected dimension {self.embedding_dim}, "
                f"got {embeddings2.shape[1]}"
            )
        
        # Normalize if needed
        norms1 = np.linalg.norm(embeddings1, axis=1)
        norms2 = np.linalg.norm(embeddings2, axis=1)
        
        if not np.allclose(norms1, 1.0):
            embeddings1 = embeddings1 / norms1[:, np.newaxis]
        if not np.allclose(norms2, 1.0):
            embeddings2 = embeddings2 / norms2[:, np.newaxis]
        
        return embeddings1 @ embeddings2.T
    
    def find_nearest_neighbors(
        self,
        query_embedding: np.ndarray,
        embeddings: np.ndarray,
        k: int = 10
    ) -> Dict[str, np.ndarray]:
        """Find nearest neighbors for a query embedding.
        
        Args:
            query_embedding: Query embedding
            embeddings: Pool of embeddings to search
            k: Number of neighbors to return
            
        Returns:
            Dictionary with indices and scores
            
        Raises:
            EmbeddingDimensionError: If dimensions don't match
        """
        # Validate dimensions
        if len(query_embedding) != self.embedding_dim:
            raise EmbeddingDimensionError(
                f"query_embedding: Expected dimension {self.embedding_dim}, "
                f"got {len(query_embedding)}"
            )
        if embeddings.shape[1] != self.embedding_dim:
            raise EmbeddingDimensionError(
                f"embeddings: Expected dimension {self.embedding_dim}, "
                f"got {embeddings.shape[1]}"
            )
        
        # Compute similarities
        similarities = self.compute_batch_similarities(
            query_embedding.reshape(1, -1),
            embeddings
        )[0]
        
        # Get top k indices
        top_indices = np.argsort(similarities)[-k:][::-1]
        top_scores = similarities[top_indices]
        
        return {
            'indices': top_indices,
            'scores': top_scores
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'embedding_dim': self.embedding_dim,
            'model_size': self._get_model_size(),
            'supports_batching': True,
            'normalize_default': True,
            'cache_dir': str(self.cache_dir) if self.cache_dir else None
        }
    
    def _get_model_size(self) -> int:
        """Get size of model parameters in bytes.
        
        Returns:
            Size in bytes
        """
        total_size = 0
        for param in self._model.parameters():
            total_size += param.nelement() * param.element_size()
        return total_size