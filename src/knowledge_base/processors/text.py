"""
Text processing functionality.
"""

import re
from typing import Dict, Any, List
import html
import unicodedata
from bs4 import BeautifulSoup
from markdown import markdown

from ..utils.logger import get_logger

logger = get_logger(__name__)

class TextProcessor:
    """Processor for cleaning and normalizing text content."""
    
    def __init__(self):
        """Initialize text processor."""
        # Common patterns to clean
        self.noise_patterns = {
            'urls': r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            'emails': r'[\w\.-]+@[\w\.-]+\.\w+',
            'phone_numbers': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'extra_whitespace': r'\s+',
            'html_comments': r'<!--.*?-->',
            'markdown_links': r'\[([^\]]+)\]\(([^)]+)\)',
            'latex_commands': r'\\[a-zA-Z]+\{[^}]*\}'
        }
        
        # Words to preserve casing
        self.preserve_words = {
            'I', 'API', 'GPU', 'CPU', 'RAM', 'URL', 'HTTP', 
            'JSON', 'XML', 'HTML', 'CSS', 'UI', 'UX', 'CLI',
            'PhD', 'AI', 'ML', 'NLP', 'PDF'
        }
        
    async def clean_text(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Clean text content.
        
        Args:
            content: Content dictionary
            
        Returns:
            Content with cleaned text
        """
        text = content['content']
        
        # Convert HTML to text if present
        if bool(BeautifulSoup(text, "html.parser").find()):
            text = await self._html_to_text(text)
        
        # Convert markdown to text if present
        if any(marker in text for marker in ['##', '**', '__', '```']):
            text = await self._markdown_to_text(text)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Normalize unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Remove noise patterns
        for pattern in self.noise_patterns.values():
            text = re.sub(pattern, ' ', text)
        
        # Remove control characters
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        content['content'] = text
        return content
    
    async def normalize_text(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize text content.
        
        Args:
            content: Content dictionary
            
        Returns:
            Content with normalized text
        """
        text = content['content']
        
        # Split into sentences
        sentences = await self._split_sentences(text)
        
        # Process each sentence
        normalized_sentences = []
        for sentence in sentences:
            # Normalize case while preserving special words
            words = sentence.split()
            normalized_words = []
            
            for word in words:
                if word in self.preserve_words:
                    normalized_words.append(word)
                elif word.isupper() and len(word) > 1:
                    # Likely an acronym
                    normalized_words.append(word)
                else:
                    normalized_words.append(word.lower())
            
            normalized_sentences.append(' '.join(normalized_words))
        
        content['content'] = ' '.join(normalized_sentences)
        return content
    
    async def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text.
        
        Args:
            html_content: HTML content
            
        Returns:
            Plain text
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Break into lines and remove leading/trailing space
            lines = (line.strip() for line in text.splitlines())
            
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines
                     for phrase in line.split("  "))
            
            # Drop blank lines
            return ' '.join(chunk for chunk in chunks if chunk)
            
        except Exception as e:
            logger.error(f"Error converting HTML to text: {e}")
            return html_content
    
    async def _markdown_to_text(self, markdown_content: str) -> str:
        """Convert markdown to plain text.
        
        Args:
            markdown_content: Markdown content
            
        Returns:
            Plain text
        """
        try:
            # Convert markdown to HTML
            html_content = markdown(markdown_content)
            
            # Convert HTML to text
            return await self._html_to_text(html_content)
            
        except Exception as e:
            logger.error(f"Error converting markdown to text: {e}")
            return markdown_content
    
    async def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Handle common abbreviations
        abbreviations = r'(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|etc|vs|apt|dept|est|vol|viz|al)\.'
        
        # Pattern for sentence boundaries
        pattern = (
            f'(?<=[.!?])(?<!{abbreviations})'  # Positive lookbehind for sentence end
            r'\s+'                              # Whitespace
            r'(?=[A-Z])'                       # Positive lookahead for capital letter
        )
        
        # Split text
        sentences = re.split(pattern, text)
        
        # Clean up sentences
        return [s.strip() for s in sentences if s.strip()]
    
    def detect_language(self, text: str) -> str:
        """Detect text language.
        
        Args:
            text: Text to analyze
            
        Returns:
            ISO language code
        """
        try:
            from langdetect import detect
            return detect(text)
        except:
            return 'unknown'
    
    def get_text_stats(self, text: str) -> Dict[str, Any]:
        """Get text statistics.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of text statistics
        """
        words = text.split()
        sentences = self._split_sentences(text)
        
        return {
            'char_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0
        }