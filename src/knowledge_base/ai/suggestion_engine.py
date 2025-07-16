import os
import logging
from typing import List, Dict, Optional
from datetime import datetime

from .openai_llm import OpenAILLM
from ..core.models import DocumentResponse

logger = logging.getLogger(__name__)


class SuggestionEngine:
    """AI-powered suggestion engine for generating follow-up questions, related topics, 
    and practical AI solution ideas tailored for AI Product Managers in healthcare analytics.
    
    This engine generates fresh suggestions on every call with no caching mechanism,
    ensuring users always receive new and contextually relevant suggestions."""
    
    def __init__(self, model_name: str = "gpt-4.1-mini", max_suggestions: int = 5):
        """Initialize the suggestion engine.
        
        Args:
            model_name: OpenAI model to use (default: gpt-4o-mini)
            max_suggestions: Maximum number of suggestions to generate (default: 5)
        """
        self.llm = OpenAILLM(model_name=model_name)
        self.max_suggestions = min(max_suggestions, 100)  # Cap at 100
        self.persona_context = """
        You are generating suggestions for an AI Product Manager at a healthcare analytics company.
        Focus on practical AI solutions, product strategy, implementation challenges, 
        regulatory considerations, and business value in healthcare technology.
        """
    
    def generate_suggestions(
        self, 
        current_article: DocumentResponse,
        recent_articles: List[DocumentResponse] = None,
        similar_articles: List[DocumentResponse] = None,
        suggestion_count: int = 5
    ) -> List[Dict[str, str]]:
        """Generate AI-driven suggestions based on article context.
        
        Args:
            current_article: The current article being viewed
            recent_articles: Last N articles viewed by user (default: empty)
            similar_articles: Top N similar articles by cosine similarity (default: empty)
            suggestion_count: Number of suggestions to generate (default: 5)
            
        Returns:
            List of suggestion dictionaries with 'type', 'title', and 'description' keys
        """
        # Validate and cap suggestion count (1-100 range, respecting instance max)
        suggestion_count = min(max(suggestion_count, 1), min(self.max_suggestions, 100))
        recent_articles = recent_articles or []
        similar_articles = similar_articles or []
        
        logger.debug(f"SuggestionEngine generating {suggestion_count} suggestions (max: {self.max_suggestions})")
        
        # Build context from all sources
        context = self._build_context(current_article, recent_articles, similar_articles)
        
        # Generate suggestions using OpenAI
        suggestions = self._generate_ai_suggestions(context, suggestion_count)
        
        return suggestions
    
    def _build_context(
        self, 
        current_article: DocumentResponse,
        recent_articles: List[DocumentResponse],
        similar_articles: List[DocumentResponse]
    ) -> str:
        """Build comprehensive context for suggestion generation."""
        
        context_parts = [
            "=== CURRENT ARTICLE ===",
            f"Title: {current_article.url}",
            f"Content: {current_article.content}...",  # Truncate to avoid token limits [:2000]
            f"Summary: {current_article.summary or 'No summary available'}",
            f"Keywords: {', '.join(current_article.keywords or [])}"
        ]
        
        if recent_articles:
            context_parts.extend([
                "\n=== RECENTLY VIEWED ARTICLES ===",
                *[f"- {article.url}: {article.summary or 'No summary'}" 
                  for article in recent_articles[:5]]
            ])
        
        if similar_articles:
            context_parts.extend([
                "\n=== RELATED ARTICLES ===", 
                *[f"- {article.url}: {article.summary or 'No summary'}" 
                  for article in similar_articles[:5]]
            ])
        
        return "\n".join(context_parts)
    
    def _generate_ai_suggestions(self, context: str, count: int) -> List[Dict[str, str]]:
        """Generate suggestions using OpenAI based on context."""
        
        system_prompt = f"""
        {self.persona_context}
        
        Based on the provided article context, generate exactly {count} diverse suggestions.
        Each suggestion should be one of these types:
        1. Follow-up Questions: Specific questions to explore based on the content
        2. Related Topics: Adjacent areas worth investigating 
        3. Practical Applications: How to apply insights in healthcare AI products
        4. Implementation Ideas: Concrete steps for building solutions
        5. Strategic Considerations: Business, regulatory, or market factors
        
        Format your response as a JSON array where each suggestion has exactly these fields:
        - "type": one of ["question", "topic", "application", "implementation", "strategy"]
        - "title": a concise suggestion title (max 80 chars)
        - "description": detailed explanation (max 200 chars)
        
        IMPORTANT: Use "description" not "content" for the explanation field.
        
        Example format:
        [
            {{
                "type": "question",
                "title": "How can we measure AI model performance?",
                "description": "Explore metrics and evaluation frameworks for healthcare AI models to ensure clinical effectiveness."
            }}
        ]
        
        Focus on actionable, specific suggestions that help an AI Product Manager make decisions,
        identify opportunities, or solve problems in healthcare analytics.
        """
        
        user_prompt = f"""
        Article Context:
        {context}
        
        Generate {count} suggestions based on this context.
        """
        
        try:
            response = self.llm.gen_gpt_chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=3000,
                temperature=0.7
            )
            print(f"DEBUG: Raw AI response: {response}")  # Debugging line
            suggestions_text = response.choices[-1].message.content.strip()
            suggestions = self._parse_suggestions(suggestions_text)
            
            # Ensure we have the right number of suggestions
            if len(suggestions) < count:
                logger.warning(f"Generated {len(suggestions)} suggestions, expected {count}")
            
            return suggestions[:count]
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return self._fallback_suggestions(count)
    
    def _parse_suggestions(self, suggestions_text: str) -> List[Dict[str, str]]:
        """Parse AI-generated suggestions from JSON response."""
        try:
            import json
            # Try to extract JSON from response
            start_idx = suggestions_text.find('[')
            end_idx = suggestions_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_text = suggestions_text[start_idx:end_idx]
                suggestions = json.loads(json_text)
                
                # Validate structure and normalize fields
                valid_suggestions = []
                for suggestion in suggestions:
                    if 'type' in suggestion and 'title' in suggestion:
                        # Handle both 'description' and 'content' fields
                        if 'description' in suggestion:
                            suggestion['description'] = suggestion['description']
                        elif 'content' in suggestion:
                            suggestion['description'] = suggestion['content']
                        else:
                            suggestion['description'] = suggestion.get('title', 'No description available.')
                        
                        # Remove 'content' field if it exists to avoid confusion
                        if 'content' in suggestion:
                            del suggestion['content']
                            
                        valid_suggestions.append(suggestion)
                
                return valid_suggestions
            
        except Exception as e:
            logger.error(f"Error parsing suggestions JSON: {e}")
        
        # Fallback to text parsing if JSON fails
        return self._parse_text_suggestions(suggestions_text)
    
    def _parse_text_suggestions(self, text: str) -> List[Dict[str, str]]:
        """Fallback parser for non-JSON suggestion responses."""
        suggestions = []
        lines = text.split('\n')
        
        current_suggestion = {}
        for line in lines:
            line = line.strip()
            if line.startswith('Type:') or line.startswith('type:'):
                if current_suggestion:
                    suggestions.append(current_suggestion)
                current_suggestion = {'type': line.split(':', 1)[1].strip().lower()}
            elif line.startswith('Title:') or line.startswith('title:'):
                current_suggestion['title'] = line.split(':', 1)[1].strip()
            elif line.startswith('Description:') or line.startswith('description:'):
                current_suggestion['description'] = line.split(':', 1)[1].strip()
        
        if current_suggestion:
            suggestions.append(current_suggestion)
        
        return suggestions
    
    def _fallback_suggestions(self, count: int) -> List[Dict[str, str]]:
        """Generate fallback suggestions when AI generation fails."""
        fallback_suggestions = [
            {
                "type": "question",
                "title": "What are the key implementation challenges?",
                "description": "Explore potential technical and organizational hurdles for this solution."
            },
            {
                "type": "strategy", 
                "title": "How does this impact our product roadmap?",
                "description": "Consider strategic implications for current and future product development."
            },
            {
                "type": "application",
                "title": "What are potential use cases in healthcare?",
                "description": "Identify specific healthcare scenarios where this could add value."
            },
            {
                "type": "implementation",
                "title": "What data and infrastructure are needed?",
                "description": "Determine requirements for successful implementation."
            },
            {
                "type": "topic",
                "title": "Related regulatory considerations",
                "description": "Explore compliance requirements and regulatory implications."
            }
        ]
        
        return fallback_suggestions[:count]