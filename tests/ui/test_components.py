"""
Unit tests for FastHTML UI components in the retro terminal knowledge base UI.
"""
import pytest
from src.knowledge_base.ui import components


# Test TerminalContainer
@pytest.mark.parametrize("content", ["Test content", "<b>HTML</b>"])
def test_terminal_container_renders(content):
    html = components.TerminalContainer(content)
    assert "terminal-container" in str(html)
    assert content in str(html)


# Test TerminalButton
@pytest.mark.parametrize(
    "label,kwargs",
    [
        ("Click Me", {}),
        ("Submit", {"type": "submit"}),
        ("Back", {"cls": "back-btn"}),
    ]
)
def test_terminal_button_renders(label, kwargs):
    html = components.TerminalButton(label, **kwargs)
    assert "terminal-btn" in str(html)
    assert label in str(html)


# Test TerminalSearchBar
@pytest.mark.parametrize("placeholder", ["Search...", "Find articles"])
def test_terminal_search_bar_renders(placeholder):
    html = components.TerminalSearchBar(placeholder=placeholder)
    assert "terminal-search-bar" in str(html)
    assert placeholder in str(html)


# Test TerminalResultsList
@pytest.mark.parametrize(
    "results",
    [
        [],
        [{"title": "Article 1", "snippet": "Summary 1"}],
        [
            {"title": "A", "snippet": "S1"},
            {"title": "B", "snippet": "S2"}
        ],
    ]
)
def test_terminal_results_list_renders(results):
    html = components.TerminalResultsList(results)
    assert "terminal-results-list" in str(html)
    for r in results:
        assert r["title"] in str(html)


# Test TerminalArticleView
@pytest.mark.parametrize(
    "article",
    [
        {
            "title": "T",
            "author": "A",
            "date": "2024-01-01",
            "tags": ["x"],
            "content": "Body"
        },
        {
            "title": "Long Title",
            "author": "B",
            "date": "2023-12-31",
            "tags": [],
            "content": "<p>HTML</p>"
        },
    ]
)
def test_terminal_article_view_renders(article):
    html = components.TerminalArticleView(article)
    assert "terminal-article-view" in str(html)
    assert article["title"] in str(html)
    assert article["author"] in str(html)
    assert article["date"] in str(html)
    assert article["content"] in str(html)


# Test TerminalNavControls
@pytest.mark.parametrize(
    "has_prev,has_next",
    [
        (True, False),
        (False, True),
        (True, True),
        (False, False),
    ]
)
def test_terminal_nav_controls_renders(has_prev, has_next):
    html = components.TerminalNavControls(has_prev=has_prev, has_next=has_next)
    assert "terminal-nav-controls" in str(html)
    if has_prev:
        assert "Previous" in str(html)
    if has_next:
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
    assert "terminal-suggestion-box" in str(html)
    for s in suggestions:
        assert s in str(html)
