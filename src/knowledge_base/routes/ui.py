# src/knowledge_base/routes/ui.py
# Main FastHTML route handlers for the Knowledge Base UI (retro terminal)

from fasthtml.common import fast_app, serve, Style, Div, Html, Head, Title, Link, Body
from src.knowledge_base.ui.components import (
    MainLayout,
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
    layout = MainLayout(
        "KNOWLEDGE BASE",
        search_bar,
        results,
        TerminalSuggestionBox(["Try searching for 'retro' or 'guide'."]),
    )
    return Html(
        Head(
            Title("Knowledge Base - Retro Terminal UI"),
            Style("""
                body { background: #101510; color: #39ff14; font-family: 'Fira Mono', 'Consolas', 'Menlo', 'Monaco', monospace; margin: 0; padding: 0; }
                .terminal-container { background: #181c18; border: 2px solid #39ff14; border-radius: 4px; padding: 2rem; margin: 2rem auto; max-width: 900px; box-shadow: 0 0 24px #39ff1433; }
                .terminal-title { font-size: 1.8rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1.5rem; text-align: center; border-bottom: 2px solid #39ff14; padding-bottom: 0.5rem; }
                .blink { animation: blink-cursor 1.1s steps(1) infinite; }
                @keyframes blink-cursor { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }
                a, .link { color: #ffe066; text-decoration: underline; cursor: pointer; }
                a:hover, .link:hover { color: #fff700; }
                input, button { background: #101510; color: #39ff14; border: 1.5px solid #39ff14; font-family: inherit; padding: 0.4em 0.7em; border-radius: 2px; margin-bottom: 1em; }
                .button-primary { background: #39ff14; color: #101510; font-weight: bold; text-transform: uppercase; }
                .highlight { color: #ffe066; background: #222a22; padding: 0.1em 0.3em; border-radius: 2px; }
                .result-item { border-left: 3px solid #39ff1444; padding-left: 1rem; margin-bottom: 1.5rem; }
            """),
        ),
        Body(
            layout,
            cls="retro-bg"
        )
    )


@rt('/article/{article_id:int}')
def article_view(article_id: int):
    article = next((a for a in ARTICLES if a["id"] == article_id), None)
    if not article:
        return Html(
            Head(Title("Not found")),
            Body(MainLayout("ERROR", Div("Article not found")))
        )
    article_content = TerminalArticleView(
        title=article["title"],
        meta={
            "author": article["author"],
            "date": article["date"],
            "tags": article["tags"]
        },
        content=article["content"],
        back_url="/"
    )
    layout = MainLayout(
        "ARTICLE VIEW",
        article_content,
        TerminalSuggestionBox(["Related: 80s Terminal UI Design"]),
    )
    return Html(
        Head(
            Title(article["title"]),
            Style("""
                body { background: #101510; color: #39ff14; font-family: 'Fira Mono', 'Consolas', 'Menlo', 'Monaco', monospace; margin: 0; padding: 0; }
                .terminal-container { background: #181c18; border: 2px solid #39ff14; border-radius: 4px; padding: 2rem; margin: 2rem auto; max-width: 900px; box-shadow: 0 0 24px #39ff1433; }
                .terminal-title { font-size: 1.8rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1.5rem; text-align: center; border-bottom: 2px solid #39ff14; padding-bottom: 0.5rem; }
                .blink { animation: blink-cursor 1.1s steps(1) infinite; }
                @keyframes blink-cursor { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }
                a, .link { color: #ffe066; text-decoration: underline; cursor: pointer; }
                a:hover, .link:hover { color: #fff700; }
                input, button { background: #101510; color: #39ff14; border: 1.5px solid #39ff14; font-family: inherit; padding: 0.4em 0.7em; border-radius: 2px; margin-bottom: 1em; }
                .button-primary { background: #39ff14; color: #101510; font-weight: bold; text-transform: uppercase; }
                .highlight { color: #ffe066; background: #222a22; padding: 0.1em 0.3em; border-radius: 2px; }
                .result-item { border-left: 3px solid #39ff1444; padding-left: 1rem; margin-bottom: 1.5rem; }
            """),
        ),
        Body(
            layout,
            cls="retro-bg"
        )
    )


@rt('/ui')
def ui_index():
    return index()


router = app

if __name__ == "__main__":
    serve()
