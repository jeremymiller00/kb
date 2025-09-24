"""
AI-driven suggestion engine for generating contextual ideas and questions.

This module provides intelligent suggestions based on the current user context,
including article content, search queries, and browsing patterns.
"""

import json
import time
import logging
from typing import List, Dict, Any, Optional
from ..ai.llm_factory import LLMFactory


class SuggestionEngine:
    """
    Generates AI-driven suggestions for enhancing user exploration and discovery
    in the knowledge base.
    """
    
    def __init__(self, llm_factory: LLMFactory, content_manager=None):
        """
        Initialize the suggestion engine.
        
        Args:
            llm_factory: Factory for creating LLM instances
            content_manager: Optional content manager for additional context
        """
        self.llm_factory = llm_factory
        self.content_manager = content_manager
        self.logger = logging.getLogger(__name__)
        self._cache = {}  # Simple in-memory cache
        self.cache_timeout = 900  # 15 minutes
    
    def generate_suggestions(
        self, 
        context_type: str, 
        context_data: Dict[str, Any], 
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate contextual suggestions based on the current page context.
        
        Args:
            context_type: Type of context ('article', 'search', 'home')
            context_data: Context-specific data dictionary
            limit: Maximum number of suggestions to return
            
        Returns:
            List of suggestion dictionaries with 'text', 'type', 'action', 'keywords'
        """
        cache_key = f"{context_type}_{hash(str(sorted(context_data.items())))}"
        
        # Check cache first
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_timeout:
                return cached_data['suggestions'][:limit]
        
        try:
            if context_type == 'article':
                suggestions = self._generate_article_suggestions(context_data, limit)
            elif context_type == 'search':
                suggestions = self._generate_search_suggestions(context_data, limit)
            elif context_type == 'home':
                suggestions = self._generate_home_suggestions(context_data, limit)
            else:
                self.logger.warning(f"Unknown context type: {context_type}")
                suggestions = self._generate_fallback_suggestions(limit)
            
            # Cache the results
            self._cache[cache_key] = {
                'suggestions': suggestions,
                'timestamp': time.time()
            }
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating suggestions: {e}")
            return self._generate_fallback_suggestions(limit)
    
    def _generate_article_suggestions(
        self, 
        article_data: Dict[str, Any], 
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate suggestions based on current article content.
        
        Args:
            article_data: Dictionary containing article title, summary, keywords, etc.
            limit: Maximum number of suggestions
            
        Returns:
            List of article-contextualized suggestions
        """
        title = article_data.get('title', 'Unknown Article')
        summary = article_data.get('summary', '')
        keywords = article_data.get('keywords', [])
        content_preview = article_data.get('content', '')[:500]  # First 500 chars
        
        # Create prompt for LLM
        prompt = f"""
Based on this article, generate {limit} engaging suggestions that would help a user explore this topic deeper.

Article Title: "{title}"
Keywords: {', '.join(keywords[:5])}
Summary: {summary[:300]}
Content Preview: {content_preview}

Generate suggestions that are:
1. Specific and actionable
2. Help users discover related concepts
3. Encourage deeper exploration
4. Mix questions and exploration ideas

Return as a JSON array where each suggestion has:
- "text": The suggestion text (engaging, under 100 chars)
- "type": Either "question", "explore", or "compare" 
- "keywords": Array of 1-3 relevant search keywords for this suggestion

Example format:
[
  {{"text": "How does this concept apply to real-world scenarios?", "type": "question", "keywords": ["applications", "examples"]}},
  {{"text": "Explore the historical development of this idea", "type": "explore", "keywords": ["history", "development"]}},
  {{"text": "Compare with alternative approaches to this problem", "type": "compare", "keywords": ["alternatives", "comparison"]}}
]
"""
        
        try:
            llm = self.llm_factory.create_llm()
            llm.set_logger(self.logger)
            
            # Get LLM response
            response = llm.generate_summary(prompt, summary_type='general')
            
            # Try to parse JSON response
            suggestions = self._parse_llm_response(response, limit)
            
            # Enhance suggestions with search actions
            for suggestion in suggestions:
                suggestion['action'] = self._create_search_action(suggestion.get('keywords', []))
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error in article suggestion generation: {e}")
            return self._generate_article_fallback(title, keywords, limit)
    
    def _generate_search_suggestions(
        self, 
        search_data: Dict[str, Any], 
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate suggestions based on current search context.
        
        Args:
            search_data: Dictionary with search query, results count, filters, etc.
            limit: Maximum number of suggestions
            
        Returns:
            List of search-contextualized suggestions
        """
        query = search_data.get('query', '')
        result_count = search_data.get('result_count', 0)
        content_types = search_data.get('content_types', [])
        
        if result_count == 0:
            # No results - suggest alternative searches
            suggestions = [
                {
                    "text": f"Try broader search terms related to '{query}'",
                    "type": "explore",
                    "keywords": [query.split()[0]] if query else ["general"],
                    "action": f"/search?query={query.split()[0]}" if query else "/search"
                },
                {
                    "text": "Remove filters to expand your search",
                    "type": "explore", 
                    "keywords": [],
                    "action": f"/search?query={query}"
                },
                {
                    "text": "Explore trending topics instead",
                    "type": "explore",
                    "keywords": ["trending"],
                    "action": "/"
                }
            ]
        elif result_count < 5:
            # Few results - suggest ways to expand
            suggestions = [
                {
                    "text": f"Find more articles similar to '{query}'",
                    "type": "explore",
                    "keywords": [query],
                    "action": f"/search?query={query}"
                },
                {
                    "text": "Discover related concepts and topics",
                    "type": "question",
                    "keywords": query.split()[:2],
                    "action": f"/search?keywords={','.join(query.split()[:2])}" if query else "/"
                }
            ]
        else:
            # Good results - suggest refinements
            suggestions = [
                {
                    "text": f"Narrow down '{query}' by content type",
                    "type": "explore", 
                    "keywords": [query],
                    "action": f"/search?query={query}"
                },
                {
                    "text": "Explore the most relevant articles first",
                    "type": "explore",
                    "keywords": [query],
                    "action": f"/search?query={query}"
                }
            ]
        
        return suggestions[:limit]
    
    def _generate_home_suggestions(
        self, 
        home_data: Dict[str, Any], 
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate suggestions for the home page based on recent content.
        
        Args:
            home_data: Dictionary with recent articles, popular topics, etc.
            limit: Maximum number of suggestions
            
        Returns:
            List of home-contextualized suggestions
        """
        recent_articles = home_data.get('recent_articles', [])
        
        suggestions = [
            {
                "text": "Discover connections between your recent reads",
                "type": "explore",
                "keywords": ["connections", "related"],
                "action": "/search"
            },
            {
                "text": "Explore trending topics in your knowledge base",
                "type": "explore", 
                "keywords": ["trending", "popular"],
                "action": "/search"
            },
            {
                "text": "Find articles you might have missed",
                "type": "question",
                "keywords": ["recent", "new"],
                "action": "/search"
            }
        ]
        
        # If we have recent articles, make suggestions more specific
        if recent_articles:
            recent_types = list(set([article.get('type', 'general') for article in recent_articles[:3]]))
            if recent_types:
                suggestions[0] = {
                    "text": f"Explore more {recent_types[0]} content",
                    "type": "explore",
                    "keywords": [recent_types[0]],
                    "action": f"/search?content_type={recent_types[0]}"
                }
        
        return suggestions[:limit]
    
    def _parse_llm_response(self, response: str, limit: int) -> List[Dict[str, Any]]:
        """
        Parse LLM JSON response into suggestion format.
        
        Args:
            response: Raw LLM response string
            limit: Maximum suggestions to return
            
        Returns:
            List of parsed suggestions
        """
        try:
            # Try to find JSON in the response
            response = response.strip()
            
            # Look for JSON array in the response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                suggestions = json.loads(json_str)
                
                # Validate and clean suggestions
                valid_suggestions = []
                for suggestion in suggestions:
                    if isinstance(suggestion, dict) and 'text' in suggestion:
                        # Ensure required fields
                        suggestion.setdefault('type', 'explore')
                        suggestion.setdefault('keywords', [])
                        
                        # Limit text length
                        if len(suggestion['text']) > 150:
                            suggestion['text'] = suggestion['text'][:147] + "..."
                        
                        valid_suggestions.append(suggestion)
                        
                        if len(valid_suggestions) >= limit:
                            break
                
                return valid_suggestions
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self.logger.warning(f"Could not parse LLM response as JSON: {e}")
        
        # Fallback - extract text suggestions
        return self._extract_text_suggestions(response, limit)
    
    def _extract_text_suggestions(self, response: str, limit: int) -> List[Dict[str, Any]]:
        """
        Extract suggestions from free-form text response.
        
        Args:
            response: Raw text response
            limit: Maximum suggestions to return
            
        Returns:
            List of extracted suggestions
        """
        suggestions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and len(line) > 10:
                # Clean up common prefixes
                for prefix in ['- ', '* ', '1. ', '2. ', '3. ', '• ']:
                    if line.startswith(prefix):
                        line = line[len(prefix):].strip()
                        break
                
                if line:
                    suggestion = {
                        "text": line[:147] + "..." if len(line) > 150 else line,
                        "type": "question" if line.endswith('?') else "explore",
                        "keywords": []
                    }
                    suggestions.append(suggestion)
                    
                    if len(suggestions) >= limit:
                        break
        
        return suggestions
    
    def _create_search_action(self, keywords: List[str]) -> str:
        """
        Create a search URL action from keywords.
        
        Args:
            keywords: List of keywords for the search
            
        Returns:
            Search URL string
        """
        if keywords:
            return f"/search?keywords={','.join(keywords[:2])}"
        return "/search"
    
    def _generate_fallback_suggestions(self, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Generate basic fallback suggestions when AI generation fails.
        
        Args:
            limit: Maximum number of suggestions
            
        Returns:
            List of fallback suggestions
        """
        fallback_suggestions = [
            {
                "text": "Search for related articles and topics",
                "type": "explore", 
                "keywords": [],
                "action": "/search"
            },
            {
                "text": "Discover connections between different concepts",
                "type": "question",
                "keywords": ["connections"],
                "action": "/search?keywords=connections"
            },
            {
                "text": "Explore different content types and sources",
                "type": "explore",
                "keywords": ["types"],
                "action": "/search"
            }
        ]
        
        return fallback_suggestions[:limit]
    
    def _generate_article_fallback(
        self, 
        title: str, 
        keywords: List[str], 
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate fallback suggestions specific to an article context.
        
        Args:
            title: Article title
            keywords: Article keywords
            limit: Maximum number of suggestions
            
        Returns:
            List of article-specific fallback suggestions
        """
        suggestions = []
        
        # Use article keywords if available
        if keywords:
            suggestions.append({
                "text": f"Explore more about {keywords[0]}",
                "type": "explore",
                "keywords": [keywords[0]],
                "action": f"/search?keywords={keywords[0]}"
            })
            
            if len(keywords) > 1:
                suggestions.append({
                    "text": f"Compare {keywords[0]} with {keywords[1]}",
                    "type": "compare", 
                    "keywords": keywords[:2],
                    "action": f"/search?keywords={','.join(keywords[:2])}"
                })
        
        # Add generic suggestion
        suggestions.append({
            "text": "Find articles with similar topics",
            "type": "explore",
            "keywords": keywords[:2] if keywords else [],
            "action": f"/search?keywords={','.join(keywords[:2])}" if keywords else "/search"
        })
        
        return suggestions[:limit]
    
    def clear_cache(self):
        """Clear the suggestion cache."""
        self._cache.clear()
        self.logger.info("Suggestion cache cleared")
    
    def set_logger(self, logger):
        """Set the logger for this instance."""
        self.logger = logger