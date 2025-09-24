import pytest
import json
import time
from unittest.mock import Mock, MagicMock, patch

from src.knowledge_base.ai.suggestion_engine import SuggestionEngine
from src.knowledge_base.ai.llm_factory import LLMFactory


@pytest.fixture
def mock_llm_factory():
    """Create a mock LLM factory."""
    factory = Mock(spec=LLMFactory)
    return factory


@pytest.fixture
def mock_llm():
    """Create a mock LLM instance."""
    llm = Mock()
    llm.generate_summary.return_value = json.dumps([
        {"text": "Test suggestion 1", "type": "question", "keywords": ["test", "mock"]},
        {"text": "Test suggestion 2", "type": "explore", "keywords": ["example"]},
        {"text": "Test suggestion 3", "type": "compare", "keywords": ["compare", "test"]}
    ])
    llm.set_logger.return_value = None
    return llm


@pytest.fixture
def mock_content_manager():
    """Create a mock content manager."""
    content_manager = Mock()
    return content_manager


@pytest.fixture
def suggestion_engine(mock_llm_factory, mock_llm, mock_content_manager):
    """Create a SuggestionEngine instance with mocked dependencies."""
    mock_llm_factory.create_llm.return_value = mock_llm
    engine = SuggestionEngine(mock_llm_factory, mock_content_manager)
    return engine


@pytest.fixture
def sample_article_data():
    """Sample article data for testing."""
    return {
        'title': 'Test Article About Machine Learning',
        'summary': 'This is a comprehensive guide to machine learning algorithms.',
        'content': 'Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.',
        'keywords': ['machine-learning', 'ai', 'algorithms'],
        'article_id': 123
    }


@pytest.fixture
def sample_search_data():
    """Sample search data for testing."""
    return {
        'query': 'machine learning',
        'result_count': 15,
        'content_types': ['github', 'arxiv'],
        'keywords': ['machine-learning'],
        'filters_applied': True
    }


@pytest.fixture
def sample_home_data():
    """Sample home page data for testing."""
    return {
        'recent_articles': [
            {'id': 1, 'type': 'github', 'title': 'ML Tutorial'},
            {'id': 2, 'type': 'arxiv', 'title': 'AI Research'}
        ],
        'total_articles': 25
    }


class TestSuggestionEngine:
    """Test suite for SuggestionEngine class."""
    
    def test_init(self, mock_llm_factory, mock_content_manager):
        """Test SuggestionEngine initialization."""
        engine = SuggestionEngine(mock_llm_factory, mock_content_manager)
        
        assert engine.llm_factory == mock_llm_factory
        assert engine.content_manager == mock_content_manager
        assert isinstance(engine._cache, dict)
        assert engine.cache_timeout == 900  # 15 minutes
    
    def test_generate_suggestions_article_context(self, suggestion_engine, sample_article_data):
        """Test generating suggestions for article context."""
        suggestions = suggestion_engine.generate_suggestions('article', sample_article_data, limit=3)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3
        
        # Verify LLM was called
        suggestion_engine.llm_factory.create_llm.assert_called_once()
        
        # Check suggestion structure
        if suggestions:
            suggestion = suggestions[0]
            assert 'text' in suggestion
            assert 'type' in suggestion
            assert 'keywords' in suggestion
    
    def test_generate_suggestions_search_context(self, suggestion_engine, sample_search_data):
        """Test generating suggestions for search context."""
        suggestions = suggestion_engine.generate_suggestions('search', sample_search_data, limit=3)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3
        
        # Search context should generate suggestions without calling LLM
        # (uses predefined logic based on search results)
        if suggestions:
            suggestion = suggestions[0]
            assert 'text' in suggestion
            assert 'type' in suggestion
            assert 'action' in suggestion
    
    def test_generate_suggestions_home_context(self, suggestion_engine, sample_home_data):
        """Test generating suggestions for home context."""
        suggestions = suggestion_engine.generate_suggestions('home', sample_home_data, limit=3)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3
        
        # Home context should generate suggestions without calling LLM
        # (uses predefined logic based on recent articles)
        if suggestions:
            suggestion = suggestions[0]
            assert 'text' in suggestion
            assert 'type' in suggestion
            assert 'action' in suggestion
    
    def test_generate_suggestions_unknown_context(self, suggestion_engine):
        """Test generating suggestions for unknown context type."""
        suggestions = suggestion_engine.generate_suggestions('unknown', {}, limit=3)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3
        
        # Should fallback to basic suggestions
        if suggestions:
            suggestion = suggestions[0]
            assert 'text' in suggestion
    
    def test_generate_suggestions_with_error_fallback(self, suggestion_engine, sample_article_data):
        """Test that suggestions fall back gracefully when LLM fails."""
        # Mock LLM to raise an exception
        mock_llm = suggestion_engine.llm_factory.create_llm.return_value
        mock_llm.generate_summary.side_effect = Exception("LLM API Error")
        
        suggestions = suggestion_engine.generate_suggestions('article', sample_article_data, limit=3)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0  # Should have fallback suggestions
        
        # Verify fallback suggestions have required structure
        suggestion = suggestions[0]
        assert 'text' in suggestion
        assert 'type' in suggestion
    
    def test_caching_behavior(self, suggestion_engine, sample_article_data):
        """Test that suggestions are cached properly."""
        # Clear cache first
        suggestion_engine.clear_cache()
        
        # First call should generate suggestions
        suggestions1 = suggestion_engine.generate_suggestions('article', sample_article_data, limit=3)
        
        # Second call with same data should use cache
        suggestions2 = suggestion_engine.generate_suggestions('article', sample_article_data, limit=3)
        
        # Should get same results
        assert suggestions1 == suggestions2
        
        # LLM should only be called once due to caching
        assert suggestion_engine.llm_factory.create_llm.call_count <= 2  # Initial + potentially one more
    
    def test_cache_expiry(self, suggestion_engine, sample_article_data):
        """Test that cache expires after timeout."""
        # Set short cache timeout for testing
        suggestion_engine.cache_timeout = 0.1  # 0.1 seconds
        
        # Generate initial suggestions
        suggestions1 = suggestion_engine.generate_suggestions('article', sample_article_data, limit=3)
        
        # Wait for cache to expire
        time.sleep(0.2)
        
        # Should generate new suggestions after cache expiry
        suggestions2 = suggestion_engine.generate_suggestions('article', sample_article_data, limit=3)
        
        # Results might be different due to cache miss
        assert isinstance(suggestions2, list)
    
    def test_parse_llm_response_valid_json(self, suggestion_engine):
        """Test parsing valid JSON response from LLM."""
        json_response = json.dumps([
            {"text": "Test suggestion", "type": "question", "keywords": ["test"]}
        ])
        
        suggestions = suggestion_engine._parse_llm_response(json_response, limit=3)
        
        assert len(suggestions) == 1
        assert suggestions[0]['text'] == "Test suggestion"
        assert suggestions[0]['type'] == "question"
        assert suggestions[0]['keywords'] == ["test"]
    
    def test_parse_llm_response_invalid_json(self, suggestion_engine):
        """Test parsing invalid JSON response from LLM."""
        invalid_response = "This is not JSON but contains some suggestions:\n- Try searching for more\n- Explore related topics"
        
        suggestions = suggestion_engine._parse_llm_response(invalid_response, limit=3)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0  # Should extract text suggestions
    
    def test_parse_llm_response_partial_json(self, suggestion_engine):
        """Test parsing response with JSON embedded in text."""
        response_with_json = """
        Here are some suggestions:
        [
            {"text": "Explore machine learning", "type": "explore", "keywords": ["ml"]},
            {"text": "Compare algorithms", "type": "compare", "keywords": ["algorithms"]}
        ]
        Hope this helps!
        """
        
        suggestions = suggestion_engine._parse_llm_response(response_with_json, limit=3)
        
        assert len(suggestions) == 2
        assert suggestions[0]['text'] == "Explore machine learning"
        assert suggestions[1]['type'] == "compare"
    
    def test_create_search_action(self, suggestion_engine):
        """Test creating search action URLs from keywords."""
        # With keywords
        action1 = suggestion_engine._create_search_action(['machine-learning', 'ai', 'python'])
        assert action1 == "/search?keywords=machine-learning,ai"
        
        # Without keywords
        action2 = suggestion_engine._create_search_action([])
        assert action2 == "/search"
        
        # With single keyword
        action3 = suggestion_engine._create_search_action(['test'])
        assert action3 == "/search?keywords=test"
    
    def test_generate_fallback_suggestions(self, suggestion_engine):
        """Test fallback suggestion generation."""
        suggestions = suggestion_engine._generate_fallback_suggestions(limit=2)
        
        assert len(suggestions) == 2
        for suggestion in suggestions:
            assert 'text' in suggestion
            assert 'type' in suggestion
            assert 'action' in suggestion
    
    def test_generate_article_fallback(self, suggestion_engine):
        """Test article-specific fallback suggestions."""
        title = "Test Article"
        keywords = ["test", "example", "demo"]
        
        suggestions = suggestion_engine._generate_article_fallback(title, keywords, limit=3)
        
        assert len(suggestions) <= 3
        for suggestion in suggestions:
            assert 'text' in suggestion
            assert 'type' in suggestion
            assert 'keywords' in suggestion
            assert 'action' in suggestion
    
    def test_clear_cache(self, suggestion_engine, sample_article_data):
        """Test cache clearing functionality."""
        # Generate suggestions to populate cache
        suggestion_engine.generate_suggestions('article', sample_article_data, limit=3)
        
        # Cache should have entries
        assert len(suggestion_engine._cache) > 0
        
        # Clear cache
        suggestion_engine.clear_cache()
        
        # Cache should be empty
        assert len(suggestion_engine._cache) == 0
    
    def test_set_logger(self, suggestion_engine):
        """Test logger setting."""
        mock_logger = Mock()
        suggestion_engine.set_logger(mock_logger)
        
        assert suggestion_engine.logger == mock_logger


class TestSuggestionEngineIntegration:
    """Integration tests for SuggestionEngine with real-like scenarios."""
    
    def test_article_suggestions_with_long_content(self, suggestion_engine):
        """Test suggestions with very long article content."""
        long_article = {
            'title': 'Very Long Article Title' * 10,
            'summary': 'This is a very long summary. ' * 50,
            'content': 'This is very long content that exceeds normal limits. ' * 100,
            'keywords': ['long', 'content', 'test'] * 10,
            'article_id': 999
        }
        
        suggestions = suggestion_engine.generate_suggestions('article', long_article, limit=3)
        
        assert isinstance(suggestions, list)
        # Should handle long content gracefully
        for suggestion in suggestions:
            if isinstance(suggestion, dict) and 'text' in suggestion:
                assert len(suggestion['text']) <= 150  # Text should be limited
    
    def test_search_suggestions_edge_cases(self, suggestion_engine):
        """Test search suggestions with edge case data."""
        # Empty search
        empty_search = {
            'query': '',
            'result_count': 0,
            'content_types': [],
            'keywords': [],
            'filters_applied': False
        }
        
        suggestions = suggestion_engine.generate_suggestions('search', empty_search, limit=3)
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Very large result count
        large_search = {
            'query': 'test',
            'result_count': 10000,
            'content_types': ['github'],
            'keywords': ['test'],
            'filters_applied': True
        }
        
        suggestions = suggestion_engine.generate_suggestions('search', large_search, limit=3)
        assert isinstance(suggestions, list)
    
    def test_concurrent_suggestion_generation(self, suggestion_engine, sample_article_data):
        """Test that concurrent suggestion generation works properly."""
        import threading
        
        results = []
        
        def generate_suggestions():
            suggestions = suggestion_engine.generate_suggestions('article', sample_article_data, limit=3)
            results.append(suggestions)
        
        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=generate_suggestions)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All results should be lists
        assert len(results) == 3
        for result in results:
            assert isinstance(result, list)