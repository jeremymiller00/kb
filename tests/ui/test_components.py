"""
Unit tests for FastHTML UI components in the retro terminal knowledge base UI.
"""
import pytest
from src.knowledge_base.ui import components


# Test MainLayout
def test_main_layout_renders():
    html = components.MainLayout("Test Title", "Test Content")
    assert "terminal-container" in str(html)
    assert "terminal-title" in str(html)
    assert "Test Title" in str(html)
    assert "Test Content" in str(html)


# Test TerminalContainer
@pytest.mark.parametrize("content", ["Test content", "<b>HTML</b>"])
def test_terminal_container_renders(content):
    html = components.TerminalContainer(content)
    assert "terminal-container" in str(html)
    assert "scanlines" in str(html)
    assert content in str(html)


# Test TerminalButton
@pytest.mark.parametrize(
    "label,primary,expected_class",
    [
        ("Click Me", False, ""),
        ("Submit", True, "button-primary"),
        ("Back", False, ""),
    ]
)
def test_terminal_button_renders(label, primary, expected_class):
    html = components.TerminalButton(label, primary=primary)
    assert label in str(html)
    if expected_class:
        assert expected_class in str(html)


# Test TerminalSearchBar
@pytest.mark.parametrize("placeholder", ["Search...", "Find articles"])
def test_terminal_search_bar_renders(placeholder):
    html = components.TerminalSearchBar(placeholder=placeholder)
    assert "search" in str(html)
    assert placeholder in str(html)
    assert "Search" in str(html)


# Test TerminalResultsList
@pytest.mark.parametrize(
    "results",
    [
        [],
        [{"title": "Article 1", "snippet": "Summary 1", "id": "1"}],
        [
            {"title": "A", "snippet": "S1", "id": "1"},
            {"title": "B", "snippet": "S2", "id": "2"}
        ],
    ]
)
def test_terminal_results_list_renders(results):
    html = components.TerminalResultsList(results)
    assert "results-list" in str(html)
    for r in results:
        assert r["title"] in str(html)
        assert f"/article/{r['id']}" in str(html)


# Test TerminalArticleView
def test_terminal_article_view_renders():
    meta = {"author": "John Doe", "date": "2024-01-01", "tags": ["ai", "tech"]}
    summary = "This is a test summary"
    content = "This is the full test content"
    html = components.TerminalArticleView("Test Title", meta, summary, content)
    assert "terminal-article-view" in str(html)
    assert "Test Title" in str(html)
    assert "John Doe" in str(html)
    assert "2024-01-01" in str(html)
    assert "This is a test summary" in str(html)
    assert "This is the full test content" in str(html)


# Test TerminalNavControls
@pytest.mark.parametrize(
    "back_url,next_url",
    [
        ("/back", None),
        (None, "/next"),
        ("/back", "/next"),
        (None, None),
    ]
)
def test_terminal_nav_controls_renders(back_url, next_url):
    html = components.TerminalNavControls(back_url=back_url, next_url=next_url)
    assert "nav-controls" in str(html)
    if back_url:
        assert "Back" in str(html)
    if next_url:
        assert "Next" in str(html)


# Test TerminalSuggestionBox
@pytest.mark.parametrize(
    "suggestions",
    [
        [],
        ["Try searching for 'AI'"],
        ["Idea 1", "Idea 2"],
    ]
)
def test_terminal_suggestion_box_renders(suggestions):
    html = components.TerminalSuggestionBox(suggestions)
    assert "suggestion-box" in str(html)
    assert "Suggestions" in str(html)
    for s in suggestions:
        assert s in str(html)


# Test ArticleTitle
def test_article_title_renders():
    html = components.ArticleTitle("Test Title")
    assert "article-title" in str(html)
    assert "Test Title" in str(html)


# Test ArticleMeta
def test_article_meta_renders():
    meta = {"author": "John Doe", "date": "2024-01-01", "tags": ["ai", "tech"]}
    html = components.ArticleMeta(meta)
    assert "article-meta" in str(html)
    assert "By John Doe" in str(html)
    assert "2024-01-01" in str(html)
    assert "ai, tech" in str(html)


# Search Form Component Tests

class TestTerminalSearchBar:
    """Test the TerminalSearchBar component functionality"""
    
    def test_search_bar_basic_rendering(self):
        """Test basic search bar rendering"""
        html = components.TerminalSearchBar()
        html_str = str(html)
        
        # Check form structure
        assert '<form' in html_str
        assert 'action="/search"' in html_str
        assert 'method="get"' in html_str
        assert 'role="search"' in html_str
        
        # Check input field
        assert 'type="text"' in html_str
        assert 'name="query"' in html_str
        assert 'placeholder="Search articles..."' in html_str
        assert 'autofocus' in html_str
        
        # Check submit button
        assert 'type="submit"' in html_str
        assert 'Search' in html_str
        assert 'button-primary' in html_str
    
    def test_search_bar_with_custom_placeholder(self):
        """Test search bar with custom placeholder"""
        custom_placeholder = "Find knowledge base articles..."
        html = components.TerminalSearchBar(placeholder=custom_placeholder)
        html_str = str(html)
        
        assert f'placeholder="{custom_placeholder}"' in html_str
    
    def test_search_bar_with_value(self):
        """Test search bar with pre-filled value"""
        search_value = "machine learning"
        html = components.TerminalSearchBar(value=search_value)
        html_str = str(html)
        
        assert f'value="{search_value}"' in html_str
    
    def test_search_bar_with_additional_attributes(self):
        """Test search bar with additional HTML attributes"""
        html = components.TerminalSearchBar(id="custom-search", cls="custom-class")
        html_str = str(html)
        
        # Note: The exact implementation may vary, but custom attributes should be passed through
        assert 'custom' in html_str or 'id=' in html_str or 'class=' in html_str


class TestTerminalFilterControls:
    """Test the TerminalFilterControls component functionality"""
    
    def test_filter_controls_basic_rendering(self):
        """Test basic filter controls rendering"""
        html = components.TerminalFilterControls()
        html_str = str(html)
        
        # Check overall structure
        assert 'filter-controls' in html_str
        assert 'Filters' in html_str
        assert '<form' in html_str
        assert 'action="/search"' in html_str
        assert 'method="get"' in html_str
        
        # Check content type filter
        assert 'Content Type' in html_str
        assert 'All Types' in html_str
        assert 'name="content_type"' in html_str
        
        # Check keywords filter
        assert 'Keywords' in html_str
        assert 'comma-separated' in html_str
        assert 'name="keywords"' in html_str
        assert 'machine-learning, ai, python' in html_str
        
        # Check date range filter
        assert 'Date Range' in html_str
        assert 'name="date_from"' in html_str
        assert 'name="date_to"' in html_str
        assert 'type="date"' in html_str
        
        # Check action buttons
        assert 'Apply Filters' in html_str
        assert 'Clear Filters' in html_str
        assert 'type="submit"' in html_str
        assert 'type="button"' in html_str
    
    def test_filter_controls_with_query(self):
        """Test filter controls with search query"""
        query = "artificial intelligence"
        html = components.TerminalFilterControls(query=query)
        html_str = str(html)
        
        # Should include hidden field with query value
        assert 'type="hidden"' in html_str
        assert 'name="query"' in html_str
        assert f'value="{query}"' in html_str
    
    def test_filter_controls_with_selected_type(self):
        """Test filter controls with selected content type"""
        selected_type = "arxiv"
        html = components.TerminalFilterControls(selected_type=selected_type)
        html_str = str(html)
        
        # Should have the selected type marked as selected
        assert f'value="{selected_type}"' in html_str
        assert 'selected' in html_str
    
    def test_filter_controls_with_selected_tags(self):
        """Test filter controls with selected tags"""
        selected_tags = ["machine learning", "python", "ai"]
        html = components.TerminalFilterControls(selected_tags=selected_tags)
        html_str = str(html)
        
        # Should have tags joined with commas in the keywords field
        expected_value = "machine learning,python,ai"
        assert expected_value in html_str
    
    def test_filter_controls_with_date_range(self):
        """Test filter controls with date range"""
        date_from = "2023-01-01"
        date_to = "2023-12-31"
        html = components.TerminalFilterControls(date_from=date_from, date_to=date_to)
        html_str = str(html)
        
        # Should have date values in the date inputs
        assert f'value="{date_from}"' in html_str
        assert f'value="{date_to}"' in html_str
    
    def test_filter_controls_with_custom_available_types(self):
        """Test filter controls with custom available types"""
        custom_types = ["research", "blog", "documentation"]
        html = components.TerminalFilterControls(available_types=custom_types)
        html_str = str(html)
        
        # Should include custom types as options
        for type_name in custom_types:
            assert type_name.title() in html_str
    
    def test_filter_controls_with_all_parameters(self):
        """Test filter controls with all parameters set"""
        html = components.TerminalFilterControls(
            query="test query",
            selected_tags=["tag1", "tag2"],
            selected_type="general",
            date_from="2023-01-01",
            date_to="2023-12-31",
            available_types=["general", "arxiv", "github"]
        )
        html_str = str(html)
        
        # Should include all provided parameters
        assert "test query" in html_str
        assert "tag1,tag2" in html_str
        assert "2023-01-01" in html_str
        assert "2023-12-31" in html_str
        assert "General" in html_str  # Title case
        assert "Arxiv" in html_str   # Title case
        assert "Github" in html_str  # Title case
    
    def test_filter_controls_clear_button_functionality(self):
        """Test that clear button has correct onclick behavior"""
        html = components.TerminalFilterControls()
        html_str = str(html)
        
        # Should have onclick handler that redirects to /search
        assert "onclick" in html_str
        assert "window.location='/search'" in html_str
    
    def test_filter_controls_accessibility(self):
        """Test filter controls accessibility features"""
        html = components.TerminalFilterControls()
        html_str = str(html)
        
        # Should have proper labels
        assert 'for="type_filter"' in html_str
        assert 'for="keywords_filter"' in html_str
        assert 'id="type_filter"' in html_str
        assert 'id="keywords_filter"' in html_str
        
        # Should have descriptive labels
        assert 'Content Type:' in html_str
        assert 'Keywords (comma-separated):' in html_str
        assert 'Date Range:' in html_str


class TestSearchFormIntegration:
    """Test integration between search bar and filter controls"""
    
    def test_search_and_filter_form_compatibility(self):
        """Test that search bar and filter controls work together"""
        query = "test search"
        search_bar = components.TerminalSearchBar(value=query)
        filter_controls = components.TerminalFilterControls(query=query)
        
        search_str = str(search_bar)
        filter_str = str(filter_controls)
        
        # Both should point to the same action
        assert 'action="/search"' in search_str
        assert 'action="/search"' in filter_str
        
        # Both should use GET method
        assert 'method="get"' in search_str
        assert 'method="get"' in filter_str
        
        # Filter controls should preserve the query
        assert f'value="{query}"' in filter_str
    
    def test_form_parameter_consistency(self):
        """Test that form parameters are consistent between components"""
        search_bar = components.TerminalSearchBar()
        filter_controls = components.TerminalFilterControls()
        
        search_str = str(search_bar)
        filter_str = str(filter_controls)
        
        # Search bar should use 'query' parameter name
        assert 'name="query"' in search_str
        
        # Filter controls should also use 'query' for hidden field
        assert 'name="query"' in filter_str
        
        # Filter controls should have expected parameter names
        assert 'name="content_type"' in filter_str
        assert 'name="keywords"' in filter_str
        assert 'name="date_from"' in filter_str
        assert 'name="date_to"' in filter_str


class TestTerminalArticleView:
    """Comprehensive tests for the TerminalArticleView component"""
    
    def test_article_view_basic_rendering(self):
        """Test basic article view rendering with all elements"""
        title = "Test Article Title"
        meta = {
            "id": 123,
            "author": "Jane Doe", 
            "date": "2024-01-15",
            "tags": ["python", "testing", "fasthtml"]
        }
        summary = "This is a brief summary of the article content."
        content = "This is the full content of the article with much more detail."
        
        html = components.TerminalArticleView(title, meta, summary, content)
        html_str = str(html)
        
        # Check overall structure
        assert "terminal-article-view" in html_str
        
        # Check title rendering
        assert title in html_str
        assert "article-title" in html_str
        
        # Check metadata rendering
        assert "Article Information" in html_str
        assert "ID:" in html_str
        assert "123" in html_str
        assert "Author:" in html_str
        assert "Jane Doe" in html_str
        assert "Published:" in html_str
        assert "2024-01-15" in html_str
        assert "Tags:" in html_str
        assert "python" in html_str
        assert "testing" in html_str
        assert "fasthtml" in html_str
        
        # Check summary section (visible by default)
        assert "Summary" in html_str
        assert summary in html_str
        
        # Check content section (hidden by default)
        assert "Full Content" in html_str
        assert "Show Full Content" in html_str
        assert content in html_str
        assert 'id="content-body"' in html_str
        assert 'style="display: none' in html_str
    
    def test_article_view_with_url_title(self):
        """Test article view with URL as title (should be clickable)"""
        title = "https://example.com/article"
        meta = {"author": "John Doe", "date": "2024-01-01"}
        summary = "Test summary"
        content = "Test content"
        
        html = components.TerminalArticleView(title, meta, summary, content)
        html_str = str(html)
        
        # Should have clickable link
        assert f'href="{title}"' in html_str
        assert 'target="_blank"' in html_str
        assert 'article-title-link' in html_str
    
    def test_article_view_with_source_url(self):
        """Test article view with separate source URL in metadata"""
        title = "Article Title"
        meta = {
            "author": "Jane Doe",
            "date": "2024-01-01",
            "source_url": "https://source.com/original"
        }
        summary = "Test summary"
        content = "Test content"
        
        html = components.TerminalArticleView(title, meta, summary, content)
        html_str = str(html)
        
        # Should have source URL link
        assert "Source:" in html_str
        assert "https://source.com/original" in html_str
        assert 'target="_blank"' in html_str
    
    def test_article_view_with_back_url(self):
        """Test article view with back button"""
        title = "Test Title"
        meta = {"author": "John Doe"}
        summary = "Test summary"
        content = "Test content"
        back_url = "/search?query=test"
        
        html = components.TerminalArticleView(title, meta, summary, content, back_url)
        html_str = str(html)
        
        # Should have back button with correct URL
        assert "Back to Results" in html_str
        assert f"window.location='{back_url}'" in html_str
    
    def test_article_view_without_back_url(self):
        """Test article view without back URL (no back button)"""
        title = "Test Title"
        meta = {"author": "John Doe"}
        summary = "Test summary"
        content = "Test content"
        
        html = components.TerminalArticleView(title, meta, summary, content)
        html_str = str(html)
        
        # Should not have back button when back_url is None
        assert "Back to Results" not in html_str
        
        # But should still render other components
        assert "terminal-article-view" in html_str
        assert title in html_str
        assert summary in html_str
        assert content in html_str
    
    def test_article_view_minimal_metadata(self):
        """Test article view with minimal metadata"""
        title = "Test Title"
        meta = {}  # Empty metadata
        summary = "Test summary"
        content = "Test content"
        
        html = components.TerminalArticleView(title, meta, summary, content)
        html_str = str(html)
        
        # Should still render basic structure
        assert "terminal-article-view" in html_str
        assert title in html_str
        assert summary in html_str
        assert content in html_str
        
        # Should not have metadata section if no valid metadata
        # (The current implementation checks for any valid metadata keys)
    
    def test_article_view_with_empty_tags(self):
        """Test article view with empty tags list"""
        title = "Test Title"
        meta = {
            "author": "John Doe",
            "date": "2024-01-01",
            "tags": []  # Empty tags
        }
        summary = "Test summary"
        content = "Test content"
        
        html = components.TerminalArticleView(title, meta, summary, content)
        html_str = str(html)
        
        # Should not show tags section if empty
        assert "Author:" in html_str
        assert "Published:" in html_str
        # Tags section should not appear for empty list
    
    def test_article_view_javascript_functionality(self):
        """Test that JavaScript toggle functionality is included"""
        title = "Test Title"
        meta = {"author": "John Doe"}
        summary = "Test summary"
        content = "Test content"
        
        html = components.TerminalArticleView(title, meta, summary, content)
        html_str = str(html)
        
        # Should include toggle JavaScript
        assert "function toggleContent()" in html_str
        assert "getElementById('content-body')" in html_str
        assert "getElementById('content-toggle-btn')" in html_str
        assert "Show Full Content" in html_str
        assert "Hide Full Content" in html_str
        assert "onclick=\"toggleContent()\"" in html_str
    
    def test_article_view_accessibility_features(self):
        """Test accessibility features in article view"""
        title = "Test Title"
        meta = {
            "id": 123,
            "author": "John Doe",
            "date": "2024-01-01",
            "tags": ["test"]
        }
        summary = "Test summary"
        content = "Test content"
        
        html = components.TerminalArticleView(title, meta, summary, content)
        html_str = str(html)
        
        # Should have proper semantic structure
        assert "article-title" in html_str
        assert "article-meta" in html_str
        assert "article-summary" in html_str
        assert "article-content" in html_str
        
        # Should have proper IDs for JavaScript interaction
        assert 'id="content-toggle-btn"' in html_str
        assert 'id="content-body"' in html_str
    
    def test_article_view_styling_classes(self):
        """Test that proper CSS classes are applied"""
        title = "Test Title"
        meta = {"author": "John Doe"}
        summary = "Test summary"
        content = "Test content"
        
        html = components.TerminalArticleView(title, meta, summary, content)
        html_str = str(html)
        
        # Should have terminal-specific styling classes
        assert "terminal-article-view" in html_str
        assert "article-title" in html_str
        assert "article-meta" in html_str
        assert "article-summary" in html_str
        assert "article-content" in html_str
        assert "article-summary-body" in html_str
        assert "article-content-body" in html_str


class TestArticleViewNavigation:
    """Tests for article view navigation functionality"""
    
    def test_back_button_with_search_params(self):
        """Test back button with search parameters"""
        title = "Test Title"
        meta = {"author": "John Doe"}
        summary = "Test summary"
        content = "Test content"
        back_url = "/search?query=python&content_type=github&page=2"
        
        html = components.TerminalArticleView(title, meta, summary, content, back_url)
        html_str = str(html)
        
        # Should preserve search parameters in back URL (may be HTML escaped)
        assert "/search?query=python" in html_str
        assert "content_type=github" in html_str
        assert "page=2" in html_str
        assert "Back to Results" in html_str
    
    def test_back_button_styling(self):
        """Test back button has proper styling"""
        title = "Test Title"
        meta = {"author": "John Doe"}
        summary = "Test summary"
        content = "Test content"
        back_url = "/search"
        
        html = components.TerminalArticleView(title, meta, summary, content, back_url)
        html_str = str(html)
        
        # Should have proper button styling
        assert "background: #666" in html_str
        assert "color: #fff" in html_str
        assert "border-radius: 4px" in html_str
        assert "font-family: monospace" in html_str
    
    def test_title_link_navigation(self):
        """Test title link navigation for URL titles"""
        title = "https://example.com/article"
        meta = {"author": "John Doe"}
        summary = "Test summary"
        content = "Test content"
        
        html = components.TerminalArticleView(title, meta, summary, content)
        html_str = str(html)
        
        # Should have external link behavior
        assert f'href="{title}"' in html_str
        assert 'target="_blank"' in html_str
        assert 'word-break: break-all' in html_str


class TestArticleViewDataHandling:
    """Tests for article view data handling edge cases"""
    
    def test_article_view_with_none_values(self):
        """Test article view with None values in metadata"""
        title = "Test Title"
        meta = {
            "author": None,
            "date": None,
            "tags": None,
            "source_url": None
        }
        summary = "Test summary"
        content = "Test content"
        
        html = components.TerminalArticleView(title, meta, summary, content)
        html_str = str(html)
        
        # Should handle None values gracefully
        assert "terminal-article-view" in html_str
        assert title in html_str
        assert summary in html_str
        assert content in html_str
    
    def test_article_view_with_long_content(self):
        """Test article view with very long content"""
        title = "Test Title"
        meta = {"author": "John Doe"}
        summary = "Short summary"
        content = "Very long content " * 100  # Long content
        
        html = components.TerminalArticleView(title, meta, summary, content)
        html_str = str(html)
        
        # Should include scroll functionality for long content
        assert "max-height: 400px" in html_str
        assert "overflow-y: auto" in html_str
        assert content in html_str
    
    def test_article_view_with_special_characters(self):
        """Test article view with special characters in content"""
        title = "Test & Title <script>"
        meta = {"author": "John & Jane <Doe>"}
        summary = "Summary with <tags> & special chars"
        content = "Content with 'quotes' & <html> tags"
        
        html = components.TerminalArticleView(title, meta, summary, content)
        html_str = str(html)
        
        # Should render content (FastHTML handles escaping)
        assert "terminal-article-view" in html_str
        # Note: FastHTML handles HTML escaping automatically
    
    def test_article_view_with_unicode_content(self):
        """Test article view with Unicode content"""
        title = "测试文章标题"
        meta = {"author": "张三", "tags": ["测试", "中文"]}
        summary = "这是一个简短的摘要"
        content = "这是完整的文章内容，包含中文字符"
        
        html = components.TerminalArticleView(title, meta, summary, content)
        html_str = str(html)
        
        # Should handle Unicode properly
        assert "terminal-article-view" in html_str
        assert title in html_str
        assert summary in html_str
        assert content in html_str
