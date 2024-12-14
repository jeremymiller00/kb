"""
Content discovery and recommendation functionality.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
import numpy as np
from collections import defaultdict

from ..storage.database import Database
from ..ai.embedding_manager import EmbeddingManager
from ..utils.logger import get_logger

logger = get_logger(__name__)

class DiscoveryService:
    """Service for content discovery and recommendations."""
    
    def __init__(
        self,
        db: Database,
        embedding_manager: EmbeddingManager,
        cache_timeout: int = 3600  # 1 hour
    ):
        self.db = db
        self.embedding_manager = embedding_manager
        self.cache_timeout = cache_timeout
        self.topic_cache: Dict[str, Any] = {}
        self.last_cache_update = datetime.min
    
    async def find_related_content(
        self,
        content_id: str,
        limit: int = 10,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find content related to a specific item.
        
        Args:
            content_id: ID of content to find related items for
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of related content items
        """
        content = await self.db.get_content(content_id)
        if not content:
            raise ValueError(f"Content not found: {content_id}")
        
        # Get similar content based on embeddings
        similar = await self.db.find_similar(
            content['embedding'],
            limit=limit * 2  # Get extra results for filtering
        )
        
        # Filter and enhance results
        results = []
        seen_urls = {content['url']}
        
        for item in similar:
            if (
                item['url'] not in seen_urls and
                item['similarity'] >= min_similarity
            ):
                # Add to results and track URL
                results.append(item)
                seen_urls.add(item['url'])
                
                if len(results) >= limit:
                    break
        
        return results
    
    async def discover_topics(self, min_docs: int = 3) -> List[Dict[str, Any]]:
        """Discover topics in the content collection.
        
        Args:
            min_docs: Minimum documents per topic
            
        Returns:
            List of discovered topics with representative content
        """
        # Check cache
        if (
            self.topic_cache and
            datetime.now() - self.last_cache_update < timedelta(seconds=self.cache_timeout)
        ):
            return self.topic_cache
        
        # Get all content
        content = await self.db.get_all_content()
        if not content:
            return []
        
        # Extract embeddings and cluster
        embeddings = np.array([item['embedding'] for item in content])
        
        from sklearn.cluster import DBSCAN
        clustering = DBSCAN(
            eps=0.3,
            min_samples=min_docs,
            metric='cosine'
        ).fit(embeddings)
        
        # Group content by cluster
        clusters = defaultdict(list)
        for idx, label in enumerate(clustering.labels_):
            if label >= 0:  # Ignore noise points (-1)
                clusters[label].append(content[idx])
        
        # Analyze each cluster
        topics = []
        for cluster_id, cluster_content in clusters.items():
            # Get common keywords
            keywords = self._get_common_keywords(cluster_content)
            
            # Get representative content
            representative = self._get_representative_content(
                cluster_content,
                embeddings[clustering.labels_ == cluster_id]
            )
            
            topics.append({
                'id': f'topic_{cluster_id}',
                'keywords': keywords,
                'size': len(cluster_content),
                'representative_content': representative,
                'recent_content': sorted(
                    cluster_content,
                    key=lambda x: x['timestamp'],
                    reverse=True
                )[:5]
            })
        
        # Update cache
        self.topic_cache = topics
        self.last_cache_update = datetime.now()
        
        return topics
    
    async def get_recommendations(
        self,
        content_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get content recommendations based on an item.
        
        Args:
            content_id: ID of content to base recommendations on
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended content items
        """
        # Get related content
        related = await self.find_related_content(
            content_id,
            limit=limit * 2
        )
        
        # Get content topics
        topics = await self.discover_topics()
        
        # Find topic for the given content
        content_topic = None
        for topic in topics:
            if any(
                item['id'] == content_id
                for item in topic['representative_content']
            ):
                content_topic = topic
                break
        
        # Combine recommendations
        recommendations = []
        seen_ids = {content_id}
        
        # Add some related content
        for item in related[:limit//2]:
            if item['id'] not in seen_ids:
                recommendations.append(item)
                seen_ids.add(item['id'])
        
        # Add some content from the same topic
        if content_topic:
            for item in content_topic['recent_content']:
                if (
                    item['id'] not in seen_ids and
                    len(recommendations) < limit
                ):
                    recommendations.append(item)
                    seen_ids.add(item['id'])
        
        # Fill remaining slots with other related content
        remaining_related = [
            item for item in related[limit//2:]
            if item['id'] not in seen_ids
        ]
        recommendations.extend(
            remaining_related[:limit - len(recommendations)]
        )
        
        return recommendations
    
    def _get_common_keywords(
        self,
        content: List[Dict[str, Any]],
        min_count: int = 2
    ) -> List[str]:
        """Get common keywords from a list of content.
        
        Args:
            content: List of content items
            min_count: Minimum number of occurrences
            
        Returns:
            List of common keywords
        """
        keyword_counts = defaultdict(int)
        for item in content:
            for keyword in item['keywords']:
                keyword_counts[keyword] += 1
        
        return [
            keyword for keyword, count in keyword_counts.items()
            if count >= min_count
        ]
    
    def _get_representative_content(
        self,
        content: List[Dict[str, Any]],
        embeddings: np.ndarray,
        n: int = 3
    ) -> List[Dict[str, Any]]:
        """Get representative content from a cluster.
        
        Args:
            content: List of content items
            embeddings: Numpy array of content embeddings
            n: Number of representative items to return
            
        Returns:
            List of representative content items
        """
        # Calculate centroid
        centroid = embeddings.mean(axis=0)
        
        # Calculate distances to centroid
        distances = np.linalg.norm(embeddings - centroid, axis=1)
        
        # Get indices of closest points
        closest_indices = np.argsort(distances)[:n]
        
        return [content[idx] for idx in closest_indices]