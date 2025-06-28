""" 
Simple test to verify UI route functionality
pytest tests/routes/test_ui_simple.py -v
"""

import pytest
from unittest.mock import Mock, patch
from knowledge_base.routes.ui import search_page


def test_search_page_basic():
    """Test that search_page returns a valid response"""
    with patch('knowledge_base.routes.ui.content_manager') as mock_cm:
        mock_cm.search_content.return_value = []
        result = search_page()
        
        # Check that result is not None (basic functionality test)
        assert result is not None
        assert isinstance(result, tuple)  # FastHTML returns tuple


def test_search_page_with_query():
    """Test search_page with query parameter"""
    with patch('knowledge_base.routes.ui.content_manager') as mock_cm:
        mock_cm.search_content.return_value = []
        result = search_page(query="test")
        
        # Check that search was called
        mock_cm.search_content.assert_called_once()
        
        # Check call arguments
        call_kwargs = mock_cm.search_content.call_args[1]
        assert call_kwargs['text_query'] == "test"


def test_keyword_parsing():
    """Test that keywords are parsed correctly"""
    with patch('knowledge_base.routes.ui.content_manager') as mock_cm:
        mock_cm.search_content.return_value = []
        search_page(keywords="tag1, tag2 , tag3")
        
        # Verify keywords were parsed and stripped
        call_kwargs = mock_cm.search_content.call_args[1]
        assert call_kwargs['keywords'] == ["tag1", "tag2", "tag3"]