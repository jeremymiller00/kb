"""
Large Language Model management and interaction.
"""

import os
from typing import Dict, Any, List, Optional, Union
import asyncio
import json
from pathlib import Path
import httpx
import backoff
from functools import partial

from ..utils.logger import get_logger

logger = get_logger(__name__)

class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass

class RateLimitError(LLMError):
    """Error for rate limit issues."""
    pass

class ModelNotFoundError(LLMError):
    """Error for unavailable models."""
    pass

class LLMManager:
    """Manager for LLM interactions."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        local_model_path: Optional[Path] = None,
        max_retries: int = 3,
        timeout: int = 30,
        use_local_models: bool = False
    ):
        """Initialize LLM manager.
        
        Args:
            openai_api_key: OpenAI API key
            local_model_path: Path to local models
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
            use_local_models: Whether to prefer local models
        """
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.local_model_path = local_model_path
        self.max_retries = max_retries
        self.timeout = timeout
        self.use_local_models = use_local_models
        self._http_client = None
        self._ollama_client = None
        self._setup_clients()
        
        # Define prompts for different tasks
        self.prompts = {
            'arxiv': (
                'You are a scientific researcher. Please provide a concise summary '
                'of the following ArXiv paper\'s title and abstract, limit 100 words. '
                'Include only the aspects that are available:\n'
                '1. Main problem or research question\n'
                '2. Key methodology or approach\n'
                '3. Main results or findings\n'
                '4. Comparison to previous work\n'
                '5. Potential applications\n'
                '6. Limitations or future work'
            ),
            'github': (
                'You are a software developer. Please provide a concise summary '
                'of the following GitHub repository, limit 100 words. '
                'Include only the aspects that are available:\n'
                '1. Purpose of the project\n'
                '2. Key features and benefits\n'
                '3. Technology stack used\n'
                '4. Installation and setup\n'
                '5. Usage examples\n'
                '6. Project status and maintenance'
            ),
            'youtube': (
                'You are a content analyst. Please provide a concise summary '
                'of the following video transcript, limit 150 words. '
                'Include only the aspects that are available:\n'
                '1. Main topic and purpose\n'
                '2. Key points and arguments\n'
                '3. Examples or demonstrations\n'
                '4. Conclusions or takeaways\n'
                '5. Related resources or next steps'
            ),
            'web': (
                'You are a content curator. Please provide a concise summary '
                'of the following web content, limit 100 words. '
                'Include only the aspects that are available:\n'
                '1. Main topic or subject\n'
                '2. Key arguments or points\n'
                '3. Evidence or examples\n'
                '4. Conclusions or insights\n'
                '5. Practical applications'
            )
        }
    
    def _setup_clients(self) -> None:
        """Set up HTTP clients."""
        self._http_client = httpx.AsyncClient(timeout=self.timeout)
        if self.use_local_models:
            self._ollama_client = httpx.AsyncClient(
                base_url='http://localhost:11434',
                timeout=self.timeout
            )
    
    @backoff.on_exception(
        partial(backoff.expo, max_value=60),
        (httpx.RequestError, RateLimitError),
        max_tries=3
    )
    async def _call_openai(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4",
        temperature: float = 0.0,
        max_tokens: int = 500
    ) -> str:
        """Call OpenAI API.
        
        Args:
            messages: List of message dictionaries
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
            
        Raises:
            LLMError: If API call fails
        """
        try:
            response = await self._http_client.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': model,
                    'messages': messages,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError("OpenAI rate limit exceeded")
            raise LLMError(f"OpenAI API error: {e}")
            
        except Exception as e:
            raise LLMError(f"Error calling OpenAI API: {e}")
    
    async def _call_ollama(
        self,
        prompt: str,
        model: str = "llama2",
        temperature: float = 0.0,
        max_tokens: int = 500
    ) -> str:
        """Call Ollama API.
        
        Args:
            prompt: Text prompt
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
            
        Raises:
            LLMError: If API call fails
        """
        try:
            response = await self._ollama_client.post(
                '/api/generate',
                json={
                    'model': model,
                    'prompt': prompt,
                    'temperature': temperature,
                    'max_length': max_tokens
                }
            )
            response.raise_for_status()
            return response.json()['response']
            
        except Exception as e:
            raise LLMError(f"Error calling Ollama API: {e}")
    
    async def summarize(
        self,
        text: str,
        content_type: str = 'web'
    ) -> str:
        """Generate summary of text.
        
        Args:
            text: Text to summarize
            content_type: Type of content
            
        Returns:
            Generated summary
            
        Raises:
            LLMError: If summarization fails
        """
        prompt = self.prompts.get(content_type, self.prompts['web'])
        
        if self.use_local_models:
            return await self._call_ollama(
                f"{prompt}\n\nContent:\n{text}"
            )
        
        return await self._call_openai([
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': text}
        ])
    
    async def extract_keywords(
        self,
        text: str,
        max_keywords: int = 10
    ) -> List[str]:
        """Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            max_keywords: Maximum number of keywords
            
        Returns:
            List of keywords
            
        Raises:
            LLMError: If extraction fails
        """
        prompt = (
            f"Extract up to {max_keywords} important keywords or key phrases "
            f"from the following text. Return them as a comma-separated list.\n\n"
            f"Text: {text}\n\nKeywords:"
        )
        
        if self.use_local_models:
            response = await self._call_ollama(prompt)
        else:
            response = await self._call_openai([
                {'role': 'user', 'content': prompt}
            ])
        
        # Clean and split response
        keywords = [
            k.strip()
            for k in response.split(',')
            if k.strip()
        ]
        
        return keywords[:max_keywords]
    
    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores
            
        Raises:
            LLMError: If analysis fails
        """
        prompt = (
            "Analyze the sentiment of the following text. "
            "Return a JSON object with scores for 'positive', "
            "'negative', and 'neutral' that sum to 1.0\n\n"
            f"Text: {text}"
        )
        
        if self.use_local_models:
            response = await self._call_ollama(prompt)
        else:
            response = await self._call_openai([
                {'role': 'user', 'content': prompt}
            ])
        
        try:
            scores = json.loads(response)
            return {
                'positive': float(scores['positive']),
                'negative': float(scores['negative']),
                'neutral': float(scores['neutral'])
            }
        except Exception as e:
            raise LLMError(f"Error parsing sentiment scores: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models.
        
        Returns:
            Dictionary with model information
        """
        models = {
            'openai': {
                'available': bool(self.openai_api_key),
                'models': ['gpt-4', 'gpt-3.5-turbo']
            },
            'local': {
                'available': self.use_local_models,
                'models': ['llama2'] if self.use_local_models else []
            }
        }
        
        return {
            'preferred': 'local' if self.use_local_models else 'openai',
            'models': models,
            'max_retries': self.max_retries,
            'timeout': self.timeout
        }
    
    async def close(self) -> None:
        """Close HTTP clients."""
        if self._http_client:
            await self._http_client.aclose()
        if self._ollama_client:
            await self._ollama_client.aclose()