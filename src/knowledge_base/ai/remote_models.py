"""
Remote model integrations (OpenAI, Anthropic, etc.).
"""

import os
import json
from typing import Dict, Any, List, Optional, Union
import httpx
import backoff
from functools import partial
from datetime import datetime, timedelta
from ..utils.logger import get_logger

logger = get_logger(__name__)

class RemoteModelError(Exception):
    """Base exception for remote model errors."""
    pass

class RemoteModelManager:
    """Manager for remote model interactions."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 30,
        rate_limit_minute: int = 50
    ):
        """Initialize remote model manager.
        
        Args:
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
            rate_limit_minute: Maximum requests per minute
        """
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.max_retries = max_retries
        self.timeout = timeout
        self.rate_limit_minute = rate_limit_minute
        
        self._client = httpx.AsyncClient(timeout=timeout)
        self._request_times: List[datetime] = []
    
    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limits."""
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        # Remove old requests
        self._request_times = [t for t in self._request_times if t > cutoff]
        
        # Check rate limit
        if len(self._request_times) >= self.rate_limit_minute:
            raise RemoteModelError("Rate limit exceeded")
        
        self._request_times.append(now)
    
    @backoff.on_exception(
        partial(backoff.expo, max_value=60),
        (httpx.RequestError, RemoteModelError),
        max_tries=3
    )
    async def call_openai(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4",
        temperature: float = 0.0,
        max_tokens: int = 500,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Call OpenAI API.
        
        Args:
            messages: List of message dictionaries
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream responses
            
        Returns:
            Generated text or async generator of text chunks
            
        Raises:
            RemoteModelError: If API call fails
        """
        if not self.openai_api_key:
            raise RemoteModelError("OpenAI API key not configured")
            
        await self._check_rate_limit()
        
        try:
            response = await self._client.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': model,
                    'messages': messages,
                    'temperature': temperature,
                    'max_tokens': max_tokens,
                    'stream': stream
                }
            )
            response.raise_for_status()
            
            if stream:
                async def generate():
                    async for line in response.aiter_lines():
                        if line.startswith('data: '):
                            data = json.loads(line[6:])
                            if content := data.get('choices', [{}])[0].get('delta', {}).get('content'):
                                yield content
                return generate()
            else:
                return response.json()['choices'][0]['message']['content']
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RemoteModelError("OpenAI rate limit exceeded")
            raise RemoteModelError(f"OpenAI API error: {e}")
            
        except Exception as e:
            raise RemoteModelError(f"Error calling OpenAI API: {e}")
    
    @backoff.on_exception(
        partial(backoff.expo, max_value=60),
        (httpx.RequestError, RemoteModelError),
        max_tries=3
    )
    async def call_anthropic(
        self,
        prompt: str,
        model: str = "claude-2",
        temperature: float = 0.0,
        max_tokens: int = 500,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Call Anthropic API.
        
        Args:
            prompt: Text prompt
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream responses
            
        Returns:
            Generated text or async generator of text chunks
            
        Raises:
            RemoteModelError: If API call fails
        """
        if not self.anthropic_api_key:
            raise RemoteModelError("Anthropic API key not configured")
            
        await self._check_rate_limit()
        
        try:
            response = await self._client.post(
                'https://api.anthropic.com/v1/complete',
                headers={
                    'X-API-Key': self.anthropic_api_key,
                    'Content-Type': 'application/json'
                },
                json={
                    'prompt': prompt,
                    'model': model,
                    'max_tokens_to_sample': max_tokens,
                    'temperature': temperature,
                    'stream': stream
                }
            )
            response.raise_for_status()
            
            if stream:
                async def generate():
                    async for line in response.aiter_lines():
                        if line.startswith('data: '):
                            data = json.loads(line[6:])
                            if completion := data.get('completion'):
                                yield completion
                return generate()
            else:
                return response.json()['completion']
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RemoteModelError("Anthropic rate limit exceeded")
            raise RemoteModelError(f"Anthropic API error: {e}")
            
        except Exception as e:
            raise RemoteModelError(f"Error calling Anthropic API: {e}")
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models from each provider.
        
        Returns:
            Dictionary mapping providers to their available models
        """
        models = {}
        
        if self.openai_api_key:
            models['openai'] = [
                'gpt-4',
                'gpt-3.5-turbo',
                'text-embedding-3-small'
            ]
            
        if self.anthropic_api_key:
            models['anthropic'] = [
                'claude-2',
                'claude-instant'
            ]
            
        return models
    
    def get_model_info(self, provider: str, model: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model.
        
        Args:
            provider: Model provider
            model: Model name
            
        Returns:
            Dictionary with model information or None if not found
        """
        model_info = {
            'openai': {
                'gpt-4': {
                    'context_length': 8192,
                    'input_cost': 0.03,
                    'output_cost': 0.06,
                    'streaming': True
                },
                'gpt-3.5-turbo': {
                    'context_length': 4096,
                    'input_cost': 0.001,
                    'output_cost': 0.002,
                    'streaming': True
                }
            },
            'anthropic': {
                'claude-2': {
                    'context_length': 100000,
                    'input_cost': 0.008,
                    'output_cost': 0.024,
                    'streaming': True
                },
                'claude-instant': {
                    'context_length': 100000,
                    'input_cost': 0.00163,
                    'output_cost': 0.00551,
                    'streaming': True
                }
            }
        }
        
        return model_info.get(provider, {}).get(model)
    
    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()