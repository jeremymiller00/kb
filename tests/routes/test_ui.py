""" 
pytest tests/routes/test_ui.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os
from fasthtml.common import Html, Head, Body

# Import the module we're testing
from knowledge_base.routes.ui import (
    index, 
    article_view, 
    search_page,
    process_url_endpoint,
    ARTICLES
)


@pytest.fixture
def mock_content_manager():
    """Mock ContentManager for testing"""
    mock_cm = Mock()
    mock_cm.get_recent_content.return_value = [
        {
            "id": 1,
            "url": "https://example.com/test",
            "summary": "Test summary content",
            "content": "Test content",
            "type": "general",
            "timestamp": 1625097600
        }
    ]
    mock_cm.db.search_content.return_value = [
        {
            "id": 1,
            "url": "https://example.com/test",
            "summary": "Test summary",
            "content": "Test content",
            "type": "general",
            "timestamp": 1625097600
        }
    ]
    mock_cm.search_content.return_value = [
        {
            "id": 1,
            "url": "https://example.com/test",
            "summary": "Test summary",
            "content": "Test content",
            "type": "general",
            "timestamp": 1625097600
        }
    ]
    return mock_cm


@pytest.fixture
def mock_requests():
    """Mock requests for API calls"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "id": 1,
            "url": "https://example.com/test",
            "summary": "API test summary",
            "content": "API test content",
            "type": "general",
            "timestamp": 1625097600
        }
    ]
    
    with patch('knowledge_base.routes.ui.requests') as mock_req:
        mock_req.get.return_value = mock_response
        yield mock_req


class TestIndexRoute:
    """Test the index route functionality"""
    
    def test_index_with_content_manager_success(self, mock_content_manager):
        """Test index route when ContentManager is available and working"""
        with patch('knowledge_base.routes.ui.content_manager', mock_content_manager):
            result = index()
            
            # Check that result is a valid HTML response
            assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple
            
            # Verify ContentManager was called
            mock_content_manager.get_recent_content.assert_called_once_with(limit=5)
    
    def test_index_with_content_manager_error(self, mock_content_manager, mock_requests):
        """Test index route when ContentManager fails but API succeeds"""
        mock_content_manager.get_recent_content.side_effect = Exception("DB Error")
        
        with patch('knowledge_base.routes.ui.content_manager', mock_content_manager):
            with patch.dict(os.environ, {'API_BASE_URL': 'http://localhost:8000'}):
                result = index()
                
                # Check that result is Html object
                assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple
            
            # Verify API was called as fallback
            mock_requests.get.assert_called()
    
    def test_index_without_content_manager(self, mock_requests):
        """Test index route when ContentManager is not available"""
        with patch('knowledge_base.routes.ui.content_manager', None):
            with patch.dict(os.environ, {'API_BASE_URL': 'http://localhost:8000'}):
                result = index()
                
                # Check that result is Html object
                assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple
                
            # Verify API was called
            mock_requests.get.assert_called()
    
    def test_index_fallback_to_demo_data(self):
        """Test index route falls back to demo data when everything fails"""
        with patch('knowledge_base.routes.ui.content_manager', None):
            with patch('knowledge_base.routes.ui.requests') as mock_req:
                mock_req.get.side_effect = Exception("Network error")
                
                result = index()
                
                # Check that result is Html object
                assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple


class TestArticleViewRoute:
    """Test the article view route functionality"""
    
    def test_article_view_with_content_manager_success(self, mock_content_manager):
        """Test article view when ContentManager finds the article"""
        mock_content_manager.db.search_content.return_value = [
            {
                "id": 1,
                "url": "https://example.com/test",
                "summary": "Test article summary",
                "content": "Test article content",
                "type": "general",
                "timestamp": 1625097600,
                "keywords": ["test", "example"]
            }
        ]
        
        with patch('knowledge_base.routes.ui.content_manager', mock_content_manager):
            result = article_view(1)
            
            # Check that result is a valid HTML response
            assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple
            
            # Verify database search was called
            mock_content_manager.db.search_content.assert_called_once_with({}, limit=1000)
    
    def test_article_view_with_api_fallback(self, mock_requests):
        """Test article view when ContentManager fails but API succeeds"""
        with patch('knowledge_base.routes.ui.content_manager', None):
            with patch.dict(os.environ, {'API_BASE_URL': 'http://localhost:8000'}):
                mock_requests.get.return_value.json.return_value = {
                    "id": 1,
                    "url": "https://example.com/test",
                    "summary": "API article summary",
                    "content": "API article content",
                    "type": "general",
                    "timestamp": 1625097600
                }
                
                result = article_view(1)
                
                # Check that result is Html object
                assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple
                
                # Verify API was called
            mock_requests.get.assert_called_with('http://localhost:8000/content/1')
    
    def test_article_view_not_found(self):
        """Test article view when article is not found"""
        with patch('knowledge_base.routes.ui.content_manager', None):
            with patch('knowledge_base.routes.ui.requests') as mock_req:
                mock_response = Mock()
                mock_response.status_code = 404
                mock_req.get.return_value = mock_response
                
                result = article_view(999)
                
                # Check that result is Html object with error
                assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple


class TestSearchRoute:
    """Test the search route functionality"""
    
    def test_search_page_empty_query(self, mock_content_manager):
        """Test search page with empty query"""
        with patch('knowledge_base.routes.ui.content_manager', mock_content_manager):
            result = search_page()
            
            # Check that result is a valid HTML response
            assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple
            
            # Verify search was called with empty parameters
            mock_content_manager.search_content.assert_called_once()
    
    def test_search_page_with_text_query(self, mock_content_manager):
        """Test search page with text query"""
        with patch('knowledge_base.routes.ui.content_manager', mock_content_manager):
            result = search_page(query="test query")
            
            # Check that result is a valid HTML response
            assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple
            
            # Verify search was called with text query
            mock_content_manager.search_content.assert_called_once()
            call_kwargs = mock_content_manager.search_content.call_args[1]
            assert 'text_query' in call_kwargs
            assert call_kwargs['text_query'] == "test query"
    
    def test_search_page_with_filters(self, mock_content_manager):
        """Test search page with various filters"""
        with patch('knowledge_base.routes.ui.content_manager', mock_content_manager):
            result = search_page(
                query="test",
                content_type="general",
                keywords="keyword1,keyword2",
                date_from="2021-01-01",
                date_to="2021-12-31"
            )
            
            # Check that result is a valid HTML response
            assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple
            
            # Verify search was called with filters
            mock_content_manager.search_content.assert_called_once()
            call_kwargs = mock_content_manager.search_content.call_args[1]
            assert call_kwargs['text_query'] == "test"
            assert call_kwargs['content_type'] == "general"
            assert call_kwargs['keywords'] == ["keyword1", "keyword2"]
    
    def test_search_page_with_pagination(self, mock_content_manager):
        """Test search page with pagination"""
        # Mock many results to test pagination
        many_results = [
            {
                "id": i,
                "url": f"https://example.com/test{i}",
                "summary": f"Test summary {i}",
                "content": f"Test content {i}",
                "type": "general",
                "timestamp": 1625097600 + i
            }
            for i in range(25)  # More than one page (10 per page)
        ]
        mock_content_manager.search_content.return_value = many_results
        
        with patch('knowledge_base.routes.ui.content_manager', mock_content_manager):
            result = search_page(query="test", page=2)
            
            # Check that result is a valid HTML response
            assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple
            
            # Verify search was called
            mock_content_manager.search_content.assert_called_once()
    
    def test_search_page_api_fallback(self, mock_requests):
        """Test search page when ContentManager fails but API works"""
        with patch('knowledge_base.routes.ui.content_manager', None):
            with patch.dict(os.environ, {'API_BASE_URL': 'http://localhost:8000'}):
                result = search_page(query="test")
                
                # Check that result is Html object
                assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple
                
            # Verify API was called
            mock_requests.get.assert_called()
    
    def test_search_page_date_filter_validation(self, mock_content_manager):
        """Test search page with invalid date formats"""
        with patch('knowledge_base.routes.ui.content_manager', mock_content_manager):
            result = search_page(
                query="test",
                date_from="invalid-date",
                date_to="also-invalid"
            )
            
            # Should still return Html object despite invalid dates
            assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple
            
            # Search should still be called
            mock_content_manager.search_content.assert_called_once()
    
    def test_search_page_content_manager_error(self, mock_content_manager, mock_requests):
        """Test search page when ContentManager throws exception"""
        mock_content_manager.search_content.side_effect = Exception("Search error")
        
        with patch('knowledge_base.routes.ui.content_manager', mock_content_manager):
            with patch.dict(os.environ, {'API_BASE_URL': 'http://localhost:8000'}):
                result = search_page(query="test")
                
                # Check that result is Html object
                assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple
                
                # Verify API fallback was used
            mock_requests.get.assert_called()


class TestProcessUrlEndpoint:
    """Test the process URL endpoint functionality"""
    
    @patch('knowledge_base.routes.ui.LLMFactory')
    @patch('knowledge_base.routes.ui.ExtractorFactory')
    @patch('knowledge_base.routes.ui.Database')
    def test_process_url_success(self, mock_db_class, mock_extractor_factory, mock_llm_factory, mock_content_manager):
        """Test successful URL processing"""
        # Setup mocks
        mock_extractor = Mock()
        mock_extractor.normalize_url.return_value = "https://example.com"
        mock_extractor.extract.return_value = "extracted content"
        mock_extractor_factory.return_value.get_extractor.return_value = mock_extractor
        
        mock_llm = Mock()
        mock_llm.generate_summary.return_value = "test summary"
        mock_llm.extract_keywords_from_summary.return_value = ["test", "keyword"]
        mock_llm.generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_llm.summary_to_obsidian_markdown.return_value = "# Test\nContent"
        mock_llm_factory.return_value.create_llm.return_value = mock_llm
        
        mock_content_manager.clean_url.return_value = "https://example.com"
        mock_content_manager.get_file_path.return_value = ("general", "/path/file.json", "123456", "https://example.com")
        
        mock_db = Mock()
        mock_db.store_content.return_value = 1
        mock_db_class.return_value = mock_db
        
        with patch('knowledge_base.routes.ui.content_manager', mock_content_manager):
            with patch.dict(os.environ, {'DB_CONN_STRING': 'test_string'}):
                result = process_url_endpoint("https://example.com")
                
                # Check that result is Html object
                assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple
                
            # Verify content manager methods were called
            mock_content_manager.clean_url.assert_called_once_with("https://example.com")
            mock_content_manager.get_file_path.assert_called_once()
            mock_content_manager.save_content.assert_called_once()
    
    def test_process_url_no_content_manager(self):
        """Test URL processing when ContentManager is not available"""
        with patch('knowledge_base.routes.ui.content_manager', None):
            result = process_url_endpoint("https://example.com")
            
            # Should return error page
            assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple
    
    @patch('knowledge_base.routes.ui.LLMFactory')
    @patch('knowledge_base.routes.ui.ExtractorFactory')
    def test_process_url_with_debug_mode(self, mock_extractor_factory, mock_llm_factory, mock_content_manager):
        """Test URL processing in debug mode (no saving)"""
        # Setup mocks
        mock_extractor = Mock()
        mock_extractor.normalize_url.return_value = "https://example.com"
        mock_extractor.extract.return_value = "extracted content"
        mock_extractor_factory.return_value.get_extractor.return_value = mock_extractor
        
        mock_llm = Mock()
        mock_llm.generate_summary.return_value = "test summary"
        mock_llm.extract_keywords_from_summary.return_value = ["test", "keyword"]
        mock_llm.generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_llm.summary_to_obsidian_markdown.return_value = "# Test\nContent"
        mock_llm_factory.return_value.create_llm.return_value = mock_llm
        
        mock_content_manager.clean_url.return_value = "https://example.com"
        mock_content_manager.get_file_path.return_value = ("general", "/path/file.json", "123456", "https://example.com")
        
        with patch('knowledge_base.routes.ui.content_manager', mock_content_manager):
            result = process_url_endpoint("https://example.com", debug="true")
            
            # Check that result is a valid HTML response
            assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple
            
            # Verify save_content was NOT called in debug mode
            mock_content_manager.save_content.assert_not_called()
    
    def test_process_url_exception_handling(self, mock_content_manager):
        """Test URL processing when an exception occurs"""
        mock_content_manager.clean_url.side_effect = Exception("Processing error")
        
        with patch('knowledge_base.routes.ui.content_manager', mock_content_manager):
            result = process_url_endpoint("https://example.com")
            
            # Should return error page
            assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple


class TestSearchFilterLogic:
    """Test search and filter logic functionality"""
    
    def test_content_type_filter_all_types(self, mock_content_manager):
        """Test that 'All Types' is converted to empty string"""
        with patch('knowledge_base.routes.ui.content_manager', mock_content_manager):
            search_page(content_type="All Types")
            
            # Verify search was called without content_type filter
            call_kwargs = mock_content_manager.search_content.call_args[1]
            assert call_kwargs.get('content_type') == ""
    
    def test_keyword_parsing(self, mock_content_manager):
        """Test that comma-separated keywords are parsed correctly"""
        with patch('knowledge_base.routes.ui.content_manager', mock_content_manager):
            search_page(keywords="tag1, tag2 , tag3")
            
            # Verify keywords were parsed and stripped
            call_kwargs = mock_content_manager.search_content.call_args[1]
            assert call_kwargs['keywords'] == ["tag1", "tag2", "tag3"]
    
    def test_date_range_filtering(self, mock_content_manager):
        """Test date range filtering logic"""
        # Mock search results with different timestamps
        search_results = [
            {"id": 1, "timestamp": 1609459200, "content": "content1", "url": "url1"},  # 2021-01-01
            {"id": 2, "timestamp": 1640995200, "content": "content2", "url": "url2"},  # 2022-01-01
            {"id": 3, "timestamp": 1577836800, "content": "content3", "url": "url3"},  # 2020-01-01
        ]
        mock_content_manager.search_content.return_value = search_results
        
        with patch('knowledge_base.routes.ui.content_manager', mock_content_manager):
            result = search_page(
                date_from="2021-01-01",
                date_to="2021-12-31"
            )
            
            # Should return HTML with filtered results
            assert result is not None
            assert isinstance(result, tuple)  # FastHTML Html returns tuple