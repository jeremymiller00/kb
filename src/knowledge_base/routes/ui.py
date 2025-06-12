# src/knowledge_base/routes/ui.py
# Main FastHTML route handlers for the Knowledge Base UI (retro terminal)

from fasthtml.common import fast_app
from fasthtml.components import Div, Html, Head, Title, Link, Body
from src.knowledge_base.ui.components import (
    TerminalContainer,
    TerminalSearchBar,
    TerminalResultsList,
    TerminalArticleView,
    TerminalNavControls,
    TerminalSuggestionBox,
)

app, rt = fast_app()

# Demo data for articles
ARTICLES = [
    {
        "id": 1,
        "title": "How to Use the Knowledge Base",
        "author": "Jane Doe",
        "date": "2025-06-10",
        "tags": ["guide", "intro"],
        "content": (
            "Welcome to the retro Knowledge Base! Use the search bar above to "
            "find articles."
        ),
    },
    {
        "id": 2,
        "title": "80s Terminal UI Design",
        "author": "John Smith",
        "date": "2025-06-09",
        "tags": ["design", "retro"],
        "content": (
            "This article explains how to create a retro terminal UI using "
            "FastHTML."
        ),
    },
]


@rt
def index():
    search_bar = TerminalSearchBar(placeholder="Search articles...")
    results = TerminalResultsList([
        {
            "id": a["id"],
            "title": a["title"],
            "snippet": a["content"][:60]
        }
        for a in ARTICLES
    ])
    container = TerminalContainer(
        Div(
            search_bar,
            results,
            TerminalSuggestionBox(["Try searching for 'retro' or 'guide'."]),
            cls="main-ui-inner"
        )
    )
    return Html(
        Head(
            Title("Knowledge Base - Retro Terminal UI"),
            Link(
                rel="stylesheet",
                href="/static/styles/retro_terminal.css"
            ),
        ),
        Body(
            container,
            cls="retro-bg"
        )
    )


@rt('/article/{article_id:int}')
def article_view(article_id: int):
    article = next((a for a in ARTICLES if a["id"] == article_id), None)
    if not article:
        return Html(Head(Title("Not found")), Body(Div("Article not found")))
    nav = TerminalNavControls(
        has_prev=article_id > 1,
        has_next=article_id < len(ARTICLES)
    )
    container = TerminalContainer(
        Div(
            TerminalArticleView(article),
            nav,
            TerminalSuggestionBox(["Related: 80s Terminal UI Design"]),
            cls="article-ui-inner"
        )
    )
    return Html(
        Head(
            Title(article["title"]),
            Link(
                rel="stylesheet",
                href="/static/styles/retro_terminal.css"
            ),
        ),
        Body(
            container,
            cls="retro-bg"
        )
    )


@rt('/ui')
def ui_index():
    return index()


router = app

# Remove direct serve() call; serving should be done in main.py
