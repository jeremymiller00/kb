import os
import logging
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime

from .suggestion_engine import SuggestionEngine
from ..core.models import DocumentResponse
from ..core.session_manager import SessionManager

logger = logging.getLogger(__name__)


class SuggestionService:
    """Service that integrates the suggestion engine with context gathering from multiple sources."""
    
    def __init__(
        self, 
        suggestion_engine: SuggestionEngine = None,
        session_manager: SessionManager = None,
        api_base_url: str = None
    ):
        """Initialize the suggestion service.
        
        Args:
            suggestion_engine: AI suggestion engine instance
            session_manager: Session manager for browsing history
            api_base_url: Base URL for content API calls
        """
        self.suggestion_engine = suggestion_engine or SuggestionEngine()
        self.session_manager = session_manager
        self.api_base_url = api_base_url or os.getenv('API_BASE_URL', 'http://localhost:8000')
    
    def generate_contextual_suggestions(
        self,
        current_article_id: str,
        session_id: str = None,
        suggestion_count: int = 5,
        include_recent_articles: bool = True,
        include_similar_articles: bool = True,
        force_fresh: bool = True
    ) -> Dict[str, Any]:
        """Generate AI suggestions using comprehensive context.
        
        Args:
            current_article_id: ID of the current article being viewed
            session_id: User session ID for browsing history
            suggestion_count: Number of suggestions to generate (default: 5)
            include_recent_articles: Whether to include recent browsing history (default: True)
            include_similar_articles: Whether to include similar articles (default: True)
            force_fresh: Always generate fresh suggestions, bypass any caching (default: True)
            
        Returns:
            Dictionary containing suggestions and context metadata
        """
        try:
            start_time = datetime.now()
            
            # Validate and cap suggestion count
            suggestion_count = min(max(suggestion_count, 1), 100)
            logger.info(f"Generating {suggestion_count} suggestions for article {current_article_id} (force_fresh: {force_fresh})")
            
            # Get current article
            current_article = self._get_article(current_article_id)
            if not current_article:
                logger.error(f"Failed to get current article: {current_article_id}")
                return self._empty_response("Current article not found")
            
            # # Get recent articles from session
            # recent_articles = []
            # if include_recent_articles and session_id and self.session_manager:
            #     recent_articles = self._get_recent_articles_from_session(session_id)
            
            # # Get similar articles via cosine similarity
            # similar_articles = []
            # if include_similar_articles:
            #     similar_articles = self._get_similar_articles(current_article_id)
            
            # Generate suggestions using all context
            # Note: force_fresh=True ensures no caching in the suggestion engine

            # BYPASSED FOR DEBUGGING

            suggestions = self.suggestion_engine.generate_suggestions(
                current_article=current_article,
                recent_articles=None,  # recent_articles,
                similar_articles=None,  # similar_articles,
                suggestion_count=suggestion_count
            )

            # # IGNORING CONTEXT FOR DEBUGGING
            # print("DEBUG: Bypassing context for debugging")
            # dubug_context = 'celiac disease is really bad'
            # suggestions = self.suggestion_engine._generate_ai_suggestions(
            #     context=dubug_context, 
            #     count=suggestion_count)
            # print(f"DEBUG: Suggestions generated: {suggestions}")  # Debugging line
            
            # Calculate generation time
            end_time = datetime.now()
            generation_time_ms = (end_time - start_time).total_seconds() * 1000
            
            logger.info(f"Generated {len(suggestions)} suggestions in {generation_time_ms:.1f}ms")
            
            # Return comprehensive response
            # INVOKED FOR DEBUGGING
            # return {'suggestions': suggestions, 'context': {}, 'success': True}

            return {
                'suggestions': suggestions,
                'context': {
                    'current_article': {
                        'id': current_article.id,
                        'url': current_article.url,
                        'summary_length': len(current_article.summary or ''),
                        'keywords_count': len(current_article.keywords or [])
                    },
                    # 'recent_articles_count': len(recent_articles),
                    # 'similar_articles_count': len(similar_articles),
                    'session_id': session_id,
                    'suggestion_count': len(suggestions),
                    'requested_count': suggestion_count,
                    'force_fresh': force_fresh,
                    'generation_time_ms': round(generation_time_ms, 1),
                    'generated_at': end_time.isoformat()
                },
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error generating contextual suggestions: {e}")
            return self._empty_response(f"Error: {str(e)}")
    
    def _get_article(self, article_id: str) -> Optional[DocumentResponse]:
        """Fetch article data from the content API."""
        try:
            response = requests.get(f"{self.api_base_url}/content/{article_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Convert API response to DocumentResponse model
                return DocumentResponse(
                    id=data.get('id'),
                    url=data.get('url', ''),
                    type=data.get('type', 'unknown'),
                    timestamp=data.get('timestamp', 0),
                    content=data.get('content', ''),
                    summary=data.get('summary'),
                    keywords=data.get('keywords', []),
                    embeddings=data.get('embeddings')
                )
            else:
                logger.warning(f"Article API returned {response.status_code} for article {article_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching article {article_id}: {e}")
            return None
    
    def _get_recent_articles_from_session(self, session_id: str) -> List[DocumentResponse]:
        """Get recent articles from user session and fetch their full data."""
        if not self.session_manager:
            return []
        
        try:
            # Get recent article IDs from session
            recent_views = self.session_manager.get_recent_articles(session_id, limit=5)
            recent_articles = []
            
            for view in recent_views:
                article_id = view.get('article_id')
                if article_id:
                    article = self._get_article(article_id)
                    if article:
                        recent_articles.append(article)
            
            logger.debug(f"Retrieved {len(recent_articles)} recent articles from session {session_id}")
            return recent_articles
            
        except Exception as e:
            logger.error(f"Error getting recent articles from session: {e}")
            return []
    
    def _get_similar_articles(self, article_id: str, limit: int = 5) -> List[DocumentResponse]:
        """Get similar articles using cosine similarity API."""
        try:
            response = requests.get(f"{self.api_base_url}/content/{article_id}/similar?n={limit}")
            
            if response.status_code == 200:
                similar_data = response.json()
                similar_articles = []
                
                for item in similar_data:
                    # Skip articles with very low similarity
                    if item.get('similarity_score', 0) <= 0.1:
                        continue
                    
                    article = DocumentResponse(
                        id=item.get('id'),
                        url=item.get('url', ''),
                        type=item.get('type', 'unknown'),
                        timestamp=item.get('timestamp', 0),
                        content=item.get('content', ''),
                        summary=item.get('summary'),
                        keywords=item.get('keywords', []),
                        embeddings=item.get('embeddings'),
                        similarity_score=item.get('similarity_score')
                    )
                    similar_articles.append(article)
                
                logger.debug(f"Retrieved {len(similar_articles)} similar articles for article {article_id}")
                return similar_articles
            
            else:
                logger.warning(f"Similar articles API returned {response.status_code} for article {article_id}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting similar articles: {e}")
            return []
    
    def _empty_response(self, error_message: str = "No suggestions available") -> Dict[str, Any]:
        """Return empty response structure for error cases."""
        return {
            'suggestions': [],
            'context': {
                'current_article': None,
                'recent_articles_count': 0,
                'similar_articles_count': 0,
                'session_id': None,
                'suggestion_count': 0,
                'generated_at': datetime.now().isoformat(),
                'error': error_message
            },
            'success': False
        }
    
    def get_suggestion_context_summary(
        self, 
        article_id: str, 
        session_id: str = None
    ) -> Dict[str, Any]:
        """Get a summary of available context for suggestion generation.
        
        Useful for debugging and understanding what data will be used.
        """
        try:
            context_summary = {
                'current_article': None,
                'recent_articles': [],
                'similar_articles': [],
                'session_info': None
            }
            
            # Get current article info
            current_article = self._get_article(article_id)
            if current_article:
                context_summary['current_article'] = {
                    'id': current_article.id,
                    'url': current_article.url,
                    'has_summary': bool(current_article.summary),
                    'keywords_count': len(current_article.keywords or []),
                    'content_length': len(current_article.content or '')
                }
            
            # Get session info
            if session_id and self.session_manager:
                session_context = self.session_manager.get_session_context(session_id)
                context_summary['session_info'] = session_context
                
                # Get recent articles summary
                recent_views = session_context.get('recent_articles', [])
                for view in recent_views:
                    context_summary['recent_articles'].append({
                        'id': view.get('article_id'),
                        'url': view.get('article_url'),
                        'viewed_at': view.get('viewed_at')
                    })
            
            # Get similar articles summary
            similar_articles = self._get_similar_articles(article_id)
            for article in similar_articles:
                context_summary['similar_articles'].append({
                    'id': article.id,
                    'url': article.url,
                    'similarity_score': getattr(article, 'similarity_score', None)
                })
            
            return context_summary
            
        except Exception as e:
            logger.error(f"Error getting context summary: {e}")
            return {'error': str(e)}