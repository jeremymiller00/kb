"""
Analytics and insights for knowledge base content.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from collections import defaultdict

from ..storage.database import Database
from ..ai.embedding_manager import EmbeddingManager
from ..utils.logger import get_logger

logger = get_logger(__name__)

class AnalyticsService:
    """Service for content analytics and insights."""
    
    def __init__(
        self,
        db: Database,
        embedding_manager: EmbeddingManager
    ):
        self.db = db
        self.embedding_manager = embedding_manager
    
    async def get_content_stats(self) -> Dict[str, Any]:
        """Get basic content statistics.
        
        Returns:
            Dictionary containing content statistics
        """
        content = await self.db.get_all_content()
        
        # Type distribution
        type_counts = defaultdict(int)
        for item in content:
            type_counts[item['type']] += 1
            
        # Time distribution
        time_ranges = {
            'last_24h': timedelta(days=1),
            'last_week': timedelta(days=7),
            'last_month': timedelta(days=30),
            'last_year': timedelta(days=365)
        }
        
        time_counts = {}
        now = datetime.now()
        for name, delta in time_ranges.items():
            cutoff = int((now - delta).timestamp())
            time_counts[name] = sum(
                1 for item in content
                if item['timestamp'] >= cutoff
            )
        
        return {
            'total_items': len(content),
            'type_distribution': dict(type_counts),
            'time_distribution': time_counts,
            'avg_keywords': np.mean([
                len(item['keywords']) for item in content
            ]),
            'avg_content_length': np.mean([
                len(item['content']) for item in content
            ])
        }
    
    async def get_keyword_analysis(self) -> Dict[str, Any]:
        """Analyze keyword usage and relationships.
        
        Returns:
            Dictionary containing keyword analytics
        """
        content = await self.db.get_all_content()
        
        # Keyword frequency
        keyword_counts = defaultdict(int)
        keyword_pairs = defaultdict(int)
        
        for item in content:
            keywords = item['keywords']
            for keyword in keywords:
                keyword_counts[keyword] += 1
                
            # Count co-occurrences
            for i, kw1 in enumerate(keywords):
                for kw2 in keywords[i+1:]:
                    if kw1 < kw2:
                        keyword_pairs[(kw1, kw2)] += 1
                    else:
                        keyword_pairs[(kw2, kw1)] += 1
        
        # Find top pairs
        top_pairs = sorted(
            [
                {'keywords': list(pair), 'count': count}
                for pair, count in keyword_pairs.items()
            ],
            key=lambda x: x['count'],
            reverse=True
        )[:20]
        
        return {
            'total_keywords': len(keyword_counts),
            'unique_keywords': len(set().union(*[
                set(item['keywords']) for item in content
            ])),
            'top_keywords': sorted(
                [
                    {'keyword': kw, 'count': count}
                    for kw, count in keyword_counts.items()
                ],
                key=lambda x: x['count'],
                reverse=True
            )[:50],
            'keyword_pairs': top_pairs
        }
    
    async def get_content_clusters(
        self,
        min_cluster_size: int = 3
    ) -> List[Dict[str, Any]]:
        """Analyze content clustering.
        
        Args:
            min_cluster_size: Minimum cluster size
            
        Returns:
            List of content clusters
        """
        content = await self.db.get_all_content()
        if not content:
            return []
            
        embeddings = np.array([item['embedding'] for item in content])
        
        from sklearn.cluster import DBSCAN
        clustering = DBSCAN(
            eps=0.3,
            min_samples=min_cluster_size,
            metric='cosine'
        ).fit(embeddings)
        
        clusters = defaultdict(list)
        for idx, label in enumerate(clustering.labels_):
            if label >= 0:
                clusters[label].append(content[idx])
        
        return [
            {
                'id': f'cluster_{label}',
                'size': len(items),
                'items': items,
                'keywords': self._get_cluster_keywords(items),
                'centroid': embeddings[clustering.labels_ == label].mean(axis=0)
            }
            for label, items in clusters.items()
        ]
    
    async def get_content_evolution(
        self,
        time_window: timedelta = timedelta(days=30),
        bucket_size: timedelta = timedelta(days=1)
    ) -> List[Dict[str, Any]]:
        """Analyze how content evolves over time.
        
        Args:
            time_window: Time window to analyze
            bucket_size: Size of time buckets
            
        Returns:
            List of time buckets with analytics
        """
        content = await self.db.get_all_content()
        
        # Create time buckets
        now = datetime.now()
        start_time = now - time_window
        bucket_count = int(time_window / bucket_size)
        buckets = [
            start_time + (bucket_size * i)
            for i in range(bucket_count + 1)
        ]
        
        # Group content into buckets
        bucketed_content = defaultdict(list)
        for item in content:
            item_time = datetime.fromtimestamp(item['timestamp'])
            if item_time >= start_time:
                bucket_idx = int((item_time - start_time) / bucket_size)
                if bucket_idx < len(buckets):
                    bucketed_content[bucket_idx].append(item)
        
        # Analyze each bucket
        results = []
        for idx, bucket_start in enumerate(buckets[:-1]):
            bucket_end = buckets[idx + 1]
            bucket_content = bucketed_content[idx]
            
            if bucket_content:
                results.append({
                    'start_time': bucket_start.isoformat(),
                    'end_time': bucket_end.isoformat(),
                    'count': len(bucket_content),
                    'types': self._count_types(bucket_content),
                    'keywords': self._get_trending_keywords(bucket_content),
                    'avg_similarity': self._calculate_avg_similarity(
                        [item['embedding'] for item in bucket_content]
                    )
                })
            else:
                results.append({
                    'start_time': bucket_start.isoformat(),
                    'end_time': bucket_end.isoformat(),
                    'count': 0,
                    'types': {},
                    'keywords': [],
                    'avg_similarity': 0.0
                })
        
        return results
    
    async def get_content_gaps(self) -> List[Dict[str, Any]]:
        """Identify potential gaps in content coverage.
        
        Returns:
            List of identified content gaps
        """
        content = await self.db.get_all_content()
        embeddings = np.array([item['embedding'] for item in content])
        
        # Calculate pairwise distances
        from sklearn.metrics.pairwise import cosine_distances
        distances = cosine_distances(embeddings)
        
        # Find areas with low coverage
        gaps = []
        threshold = np.percentile(distances, 95)  # Top 5% of distances
        
        for i in range(len(distances)):
            far_neighbors = np.where(distances[i] > threshold)[0]
            if len(far_neighbors) > 0:
                gaps.append({
                    'content_id': content[i]['id'],
                    'url': content[i]['url'],
                    'distance': float(distances[i][far_neighbors].mean()),
                    'far_neighbors': [
                        content[j]['id'] for j in far_neighbors
                    ]
                })
        
        return sorted(gaps, key=lambda x: x['distance'], reverse=True)
    
    def _get_cluster_keywords(
        self,
        items: List[Dict[str, Any]],
        min_count: int = 2
    ) -> List[str]:
        """Get representative keywords for a cluster.
        
        Args:
            items: List of content items
            min_count: Minimum keyword occurrence
            
        Returns:
            List of representative keywords
        """
        keyword_counts = defaultdict(int)
        for item in items:
            for keyword in item['keywords']:
                keyword_counts[keyword] += 1
        
        return [
            kw for kw, count in keyword_counts.items()
            if count >= min_count
        ]
    
    def _count_types(
        self,
        items: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Count content types in a list of items.
        
        Args:
            items: List of content items
            
        Returns:
            Dictionary of type counts
        """
        type_counts = defaultdict(int)
        for item in items:
            type_counts[item['type']] += 1
        return dict(type_counts)
    
    def _get_trending_keywords(
        self,
        items: List[Dict[str, Any]],
        top_n: int = 10
    ) -> List[str]:
        """Get trending keywords from a list of items.
        
        Args:
            items: List of content items
            top_n: Number of top keywords to return
            
        Returns:
            List of trending keywords
        """
        keyword_counts = defaultdict(int)
        for item in items:
            for keyword in item['keywords']:
                keyword_counts[keyword] += 1
        
        return [
            kw for kw, _ in sorted(
                keyword_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_n]
        ]
    
    def _calculate_avg_similarity(
        self,
        embeddings: List[np.ndarray]
    ) -> float:
        """Calculate average similarity between embeddings.
        
        Args:
            embeddings: List of embedding vectors
            
        Returns:
            Average similarity score
        """
        if len(embeddings) < 2:
            return 0.0
            
        embeddings = np.array(embeddings)
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(embeddings)
        
        # Exclude self-similarities
        np.fill_diagonal(similarities, 0)
        return float(similarities.mean())