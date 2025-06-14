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
    html = components.TerminalArticleView("Test Title", meta, "Test Content")
    assert "article-view" in str(html)
    assert "Test Title" in str(html)
    assert "John Doe" in str(html)
    assert "2024-01-01" in str(html)
    assert "Test Content" in str(html)


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
